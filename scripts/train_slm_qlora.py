"""
Project Hares: Sovereign Small Language Model (SLM) QLoRA Fine-Tuning Pipeline.

Fine-tunes Qwen-2.5-3B-Instruct (or Llama-3.2-3B) on the Project Hares localized
dialectal smishing corpus (100K or 25K curriculum core subset).

Hardware & Reliability Guards:
- T4 GPU float16 hardware compatibility (avoids broken BF16 emulation on Turing CC 7.5).
- Checkpoint streaming to Google Drive (/content/drive/MyDrive/hares_mlops/checkpoints/slm)
  every 500 steps with automatic resumption (resume_from_checkpoint=True).
- Paged 8-bit AdamW optimizer with cosine learning rate schedule.
- ChatML structured prompt boundary formatting with strict JSON schema compliance.
"""

from __future__ import annotations

import argparse
import json
import logging
import math
import os
import sys
import time
from pathlib import Path
from typing import Any

import torch
from datasets import load_dataset
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainerCallback,
    TrainingArguments,
)

try:
    from trl import SFTTrainer
except ImportError:
    SFTTrainer = None  # type: ignore



logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("hares.train_slm")

DEFAULT_MODEL_NAME = "Qwen/Qwen2.5-3B-Instruct"
DEFAULT_DRIVE_CHECKPOINT_DIR = "/content/drive/MyDrive/hares_mlops/checkpoints/slm"
DEFAULT_LOCAL_OUTPUT_DIR = "./output/hares_slm_lora"


def setup_bitsandbytes_config() -> BitsAndBytesConfig:
    """
    Configures 4-bit NormalFloat (nf4) quantization.
    Crucial Turing/T4 Hardware Guard:
    Checks torch.cuda.is_bf16_supported(). If False (e.g. on NVIDIA T4),
    forces torch.float16 to avoid software emulation slowdowns.
    """
    has_native_bf16 = torch.cuda.is_available() and torch.cuda.is_bf16_supported()
    compute_dtype = torch.bfloat16 if has_native_bf16 else torch.float16
    logger.info("CUDA Device: %s | Native BF16 Supported: %s | Compute Dtype: %s",
                torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU",
                has_native_bf16, compute_dtype)

    return BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=compute_dtype,
    )


def setup_lora_config() -> LoraConfig:
    """
    Configures LoRA adapter targeting all attention and MLP projection weights.
    Trainable parameters: ~0.8% of base model (~24M parameters).
    """
    return LoraConfig(
        r=16,
        lora_alpha=32,
        target_modules=[
            "q_proj",
            "k_proj",
            "v_proj",
            "o_proj",
            "gate_proj",
            "up_proj",
            "down_proj",
        ],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
    )


def format_chatml_prompts(data: dict[str, Any], tokenizer: Any) -> str | list[str]:
    """Applies the ChatML conversation template to messages list (supports both single sample and batch)."""
    messages = data.get("messages", [])
    if not messages:
        return ""
    # Case 1: Single sample (what SFTTrainer formatting_func expects)
    if isinstance(messages[0], dict):
        return tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=False,
        )
    # Case 2: Batched input (list of conversations)
    elif isinstance(messages[0], list):
        return [
            tokenizer.apply_chat_template(
                conv,
                tokenize=False,
                add_generation_prompt=False,
            )
            for conv in messages
        ]
    return ""


class MLOpsMetricsLoggerCallback(TrainerCallback):
    """
    Tracks, notes, and persists all training metrics across steps and epochs.
    Emits formatted ASCII telemetry dashboards per epoch and writes persistent
    metrics logs (JSONL, JSON, Markdown) to Google Drive.
    """

    def __init__(self, output_dir: str | Path) -> None:
        self.output_dir = Path(output_dir)
        self.metrics_file = self.output_dir / "training_metrics.jsonl"
        self.epoch_file = self.output_dir / "epoch_summary.json"
        self.report_file = self.output_dir / "TRAINING_RUN_REPORT.md"
        self.step_logs: list[dict[str, Any]] = []
        self.epoch_logs: list[dict[str, Any]] = []
        self.train_start_time: float = 0.0
        self.epoch_start_time: float = 0.0
        self.total_epochs: int = 1

    def on_train_begin(self, args: Any, state: Any, control: Any, **kwargs: Any) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.train_start_time = time.time()
        self.epoch_start_time = time.time()
        self.total_epochs = int(args.num_train_epochs)
        logger.info("[MLOps Callback] Initialized metric logger. Persisting to %s", self.output_dir)

    def on_epoch_begin(self, args: Any, state: Any, control: Any, **kwargs: Any) -> None:
        self.epoch_start_time = time.time()

    def on_log(self, args: Any, state: Any, control: Any, logs: dict[str, Any] | None = None, **kwargs: Any) -> None:
        if not logs:
            return
        entry = {
            "step": state.global_step,
            "epoch": round(state.epoch, 4) if state.epoch is not None else 0.0,
            "elapsed_seconds": round(time.time() - self.train_start_time, 2),
            **logs,
        }
        self.step_logs.append(entry)
        try:
            with open(self.metrics_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as exc:
            logger.debug("Failed to write incremental metric log: %s", exc)

    def on_epoch_end(self, args: Any, state: Any, control: Any, **kwargs: Any) -> None:
        epoch_idx = int(round(state.epoch)) if state.epoch is not None else len(self.epoch_logs) + 1
        now = time.time()
        epoch_duration = now - self.epoch_start_time
        total_elapsed = now - self.train_start_time

        epoch_step_losses = [
            x["loss"] for x in self.step_logs
            if "loss" in x and abs(x.get("epoch", 0.0) - epoch_idx) <= 1.05
        ]
        if not epoch_step_losses:
            epoch_step_losses = [x["loss"] for x in self.step_logs if "loss" in x]

        avg_loss = sum(epoch_step_losses) / len(epoch_step_losses) if epoch_step_losses else 0.0
        min_loss = min(epoch_step_losses) if epoch_step_losses else 0.0
        max_loss = max(epoch_step_losses) if epoch_step_losses else 0.0
        ppl = math.exp(avg_loss) if 0 < avg_loss < 20 else 1.0

        current_lr = 0.0
        for entry in reversed(self.step_logs):
            if "learning_rate" in entry:
                current_lr = entry["learning_rate"]
                break

        total_steps = state.max_steps if state.max_steps > 0 else 1
        current_step = state.global_step
        progress_pct = (current_step / total_steps) * 100.0
        remaining_steps = max(0, total_steps - current_step)
        steps_per_sec = current_step / max(1.0, total_elapsed)
        eta_seconds = remaining_steps / max(1e-4, steps_per_sec)

        epoch_summary = {
            "epoch": epoch_idx,
            "total_epochs": self.total_epochs,
            "step": current_step,
            "max_steps": total_steps,
            "progress_percent": round(progress_pct, 2),
            "average_loss": round(avg_loss, 4),
            "min_loss": round(min_loss, 4),
            "max_loss": round(max_loss, 4),
            "estimated_perplexity": round(ppl, 2),
            "learning_rate": current_lr,
            "epoch_duration_seconds": round(epoch_duration, 2),
            "total_elapsed_seconds": round(total_elapsed, 2),
            "eta_seconds": round(eta_seconds, 2),
        }
        self.epoch_logs.append(epoch_summary)

        try:
            with open(self.epoch_file, "w", encoding="utf-8") as f:
                json.dump(self.epoch_logs, f, indent=2)
        except Exception as exc:
            logger.debug("Failed to write epoch summary: %s", exc)

        banner = f"""
================================================================================
🚀 [PROJECT HARES MLOPS] EPOCH {epoch_idx} / {self.total_epochs} COMPLETE
--------------------------------------------------------------------------------
Current Step:           {current_step:,} / {total_steps:,} ({progress_pct:.1f}%)
Epoch Average Loss:     {avg_loss:.4f}  (Min: {min_loss:.4f} | Max: {max_loss:.4f})
Estimated Perplexity:   {ppl:.2f}
Current Learning Rate:  {current_lr:.3e}
Epoch Duration:         {self._format_duration(epoch_duration)}
Total Elapsed Time:     {self._format_duration(total_elapsed)}
Est. Time Remaining:    {self._format_duration(eta_seconds)}
Checkpoints Directory:  {self.output_dir}
================================================================================
"""
        print(banner)

    def on_train_end(self, args: Any, state: Any, control: Any, **kwargs: Any) -> None:
        total_time = time.time() - self.train_start_time
        losses = [x["loss"] for x in self.step_logs if "loss" in x]
        initial_loss = losses[0] if losses else 0.0
        final_loss = losses[-1] if losses else 0.0
        best_loss = min(losses) if losses else 0.0
        loss_reduction = ((initial_loss - final_loss) / initial_loss * 100.0) if initial_loss > 0 else 0.0

        report_md = f"""# Project Hares SLM Training Run Report

- **Run Timestamp:** {time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())}
- **Base Model:** Qwen-2.5-3B-Instruct (4-bit QLoRA)
- **Total Epochs:** {self.total_epochs}
- **Total Steps:** {state.global_step:,}
- **Total Duration:** {self._format_duration(total_time)}
- **Initial Loss:** {initial_loss:.4f}
- **Final Loss:** {final_loss:.4f}
- **Best Loss:** {best_loss:.4f}
- **Loss Reduction:** {loss_reduction:.2f}%

## Epoch Metrics Breakdown

| Epoch | Avg Loss | Perplexity | Min Loss | Max Loss | Duration |
| :---: | :---: | :---: | :---: | :---: | :---: |
"""
        for ep in self.epoch_logs:
            report_md += f"| {ep['epoch']} / {ep['total_epochs']} | {ep['average_loss']:.4f} | {ep['estimated_perplexity']:.2f} | {ep['min_loss']:.4f} | {ep['max_loss']:.4f} | {self._format_duration(ep['epoch_duration_seconds'])} |\n"

        try:
            with open(self.report_file, "w", encoding="utf-8") as f:
                f.write(report_md)
        except Exception as exc:
            logger.debug("Failed to write training run report: %s", exc)

        print(f"\n✅ Training Complete! Report written to {self.report_file}")

    @staticmethod
    def _format_duration(seconds: float) -> str:
        s = int(seconds)
        m, s = divmod(s, 60)
        h, m = divmod(m, 60)
        if h > 0:
            return f"{h}h {m:02d}m {s:02d}s"
        return f"{m:02d}m {s:02d}s"


def display_training_metrics(log_dir: str | Path) -> None:
    """Reads saved epoch summary and displays formatted table."""
    path = Path(log_dir)
    epoch_file = path / "epoch_summary.json"
    if not epoch_file.exists():
        print(f"No epoch summary found at {epoch_file}")
        return

    with open(epoch_file, "r", encoding="utf-8") as f:
        epoch_logs = json.load(f)

    print("\n" + "=" * 80)
    print("📊 PROJECT HARES — SLM TRAINING METRICS SUMMARY")
    print("=" * 80)
    print(f"{'Epoch':<8} {'Avg Loss':<12} {'Perplexity':<12} {'Min Loss':<12} {'Max Loss':<12} {'Duration':<12}")
    print("-" * 80)
    for ep in epoch_logs:
        dur = f"{int(ep['epoch_duration_seconds'] // 60)}m {int(ep['epoch_duration_seconds'] % 60)}s"
        print(f"{ep['epoch']:<8} {ep['average_loss']:<12.4f} {ep['estimated_perplexity']:<12.2f} {ep['min_loss']:<12.4f} {ep['max_loss']:<12.4f} {dur:<12}")
    print("=" * 80 + "\n")



def train_slm(
    dataset_path: str,
    output_dir: str,
    model_name: str = DEFAULT_MODEL_NAME,
    batch_size: int = 2,
    gradient_accumulation_steps: int = 8,
    epochs: int = 2,
    learning_rate: float = 2e-4,
    save_steps: int = 500,
    resume_from_checkpoint: bool = True,
    max_seq_length: int = 1024,
) -> None:
    """Executes the QLoRA training run."""
    logger.info("Initializing SLM QLoRA pipeline: Model=%s | Dataset=%s", model_name, dataset_path)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    bnb_config = setup_bitsandbytes_config()
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    has_native_bf16 = torch.cuda.is_available() and torch.cuda.is_bf16_supported()
    compute_dtype = torch.bfloat16 if has_native_bf16 else torch.float16

    logger.info("Loading base causal language model in 4-bit with torch_dtype=%s...", compute_dtype)
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        quantization_config=bnb_config,
        torch_dtype=compute_dtype,
        device_map="auto",
        trust_remote_code=True,
    )
    model.config.use_cache = False
    model = prepare_model_for_kbit_training(model)

    peft_config = setup_lora_config()
    model = get_peft_model(model, peft_config)
    model.print_trainable_parameters()

    logger.info("Loading training dataset from %s ...", dataset_path)
    raw_dataset = load_dataset("json", data_files=dataset_path, split="train")
    logger.info("Loaded %d training examples", len(raw_dataset))

    # Check for latest checkpoint in output_dir to resume
    checkpoint_to_resume: str | bool = False
    if resume_from_checkpoint and output_path.exists():
        checkpoints = sorted(
            [d for d in output_path.glob("checkpoint-*") if d.is_dir()],
            key=lambda d: int(d.name.split("-")[-1]) if d.name.split("-")[-1].isdigit() else 0,
        )
        if checkpoints:
            checkpoint_to_resume = str(checkpoints[-1])
            logger.info("Found existing checkpoint, will resume from: %s", checkpoint_to_resume)

    has_native_bf16 = torch.cuda.is_available() and torch.cuda.is_bf16_supported()

    config_kwargs = {
        "output_dir": output_dir,
        "num_train_epochs": epochs,
        "per_device_train_batch_size": batch_size,
        "gradient_accumulation_steps": gradient_accumulation_steps,
        "learning_rate": learning_rate,
        "lr_scheduler_type": "cosine",
        "warmup_steps": 100,
        "logging_steps": 25,
        "save_strategy": "steps",
        "save_steps": save_steps,
        "save_total_limit": 3,
        "fp16": not has_native_bf16,
        "bf16": has_native_bf16,
        "optim": "paged_adamw_8bit",
        "report_to": "none",
        "gradient_checkpointing": True,
    }

    try:
        from trl import SFTConfig
        try:
            training_args = SFTConfig(max_length=max_seq_length, **config_kwargs)
        except TypeError:
            training_args = SFTConfig(max_seq_length=max_seq_length, **config_kwargs)
    except (ImportError, TypeError):
        training_args = TrainingArguments(**config_kwargs)

    # Universal CUDA GEMM guard for Turing/Pascal (compute capability < 8.0)
    # Intercepts torch.addmm when out_dtype=torch.float32 is invoked on BF16/FP16 inputs
    _orig_torch_addmm = torch.addmm

    def safe_torch_addmm(input_tensor: Any, mat1: Any, mat2: Any, *addmm_args: Any, **addmm_kwargs: Any) -> Any:
        out_dtype = addmm_kwargs.pop("out_dtype", None)
        out = addmm_kwargs.get("out", None)
        if out_dtype is not None:
            res = _orig_torch_addmm(input_tensor.float(), mat1.float(), mat2.float(), *addmm_args, **addmm_kwargs)
            if out is not None:
                out.copy_(res)
                return out
            return res
        try:
            return _orig_torch_addmm(input_tensor, mat1, mat2, *addmm_args, **addmm_kwargs)
        except RuntimeError as err:
            if "compute capability 8.0" in str(err) or "gemm input type" in str(err):
                res = _orig_torch_addmm(input_tensor.float(), mat1.float(), mat2.float(), *addmm_args, **addmm_kwargs)
                if out is not None:
                    out.copy_(res)
                    return out
                return res
            raise err

    torch.addmm = safe_torch_addmm
    logger.info("Patched torch.addmm with safe_torch_addmm fallback for Turing T4 GEMM compatibility")

    metrics_callback = MLOpsMetricsLoggerCallback(output_dir=output_dir)

    trainer_kwargs = {
        "model": model,
        "train_dataset": raw_dataset,
        "peft_config": None if isinstance(model, PeftModel) else peft_config,
        "args": training_args,
        "formatting_func": lambda b: format_chatml_prompts(b, tokenizer),
        "callbacks": [metrics_callback],
    }

    try:
        trainer = SFTTrainer(processing_class=tokenizer, **trainer_kwargs)
    except TypeError:
        trainer = SFTTrainer(tokenizer=tokenizer, **trainer_kwargs)


    logger.info("Starting model training (Effective batch size = %d) ...", batch_size * gradient_accumulation_steps)
    if checkpoint_to_resume:
        trainer.train(resume_from_checkpoint=checkpoint_to_resume)
    else:
        trainer.train()

    # Save final LoRA adapter
    final_adapter_dir = output_path / "final_adapter"
    final_adapter_dir.mkdir(parents=True, exist_ok=True)
    logger.info("Saving final LoRA adapter to %s ...", final_adapter_dir)
    trainer.model.save_pretrained(final_adapter_dir)
    tokenizer.save_pretrained(final_adapter_dir)
    logger.info("Training complete and adapter successfully serialized!")


def main() -> None:
    parser = argparse.ArgumentParser(description="Fine-tune Project Hares SLM via QLoRA")
    parser.add_argument("--dataset-path", type=str, required=True, help="Path to ChatML JSONL dataset")
    parser.add_argument("--output-dir", type=str, default=DEFAULT_DRIVE_CHECKPOINT_DIR, help="Checkpoint/Adapter output directory")
    parser.add_argument("--model-name", type=str, default=DEFAULT_MODEL_NAME, help="Base model identifier")
    parser.add_argument("--batch-size", type=int, default=2, help="Per device batch size")
    parser.add_argument("--grad-accum", type=int, default=8, help="Gradient accumulation steps")
    parser.add_argument("--epochs", type=int, default=2, help="Number of training epochs")
    parser.add_argument("--lr", type=float, default=2e-4, help="Learning rate")
    parser.add_argument("--save-steps", type=int, default=500, help="Checkpoint save step frequency")
    parser.add_argument("--no-resume", action="store_true", help="Do not resume from existing checkpoint")
    args = parser.parse_args()

    train_slm(
        dataset_path=args.dataset_path,
        output_dir=args.output_dir,
        model_name=args.model_name,
        batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum,
        epochs=args.epochs,
        learning_rate=args.lr,
        save_steps=args.save_steps,
        resume_from_checkpoint=not args.no_resume,
    )


if __name__ == "__main__":
    main()
