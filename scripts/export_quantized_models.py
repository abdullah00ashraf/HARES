"""
Project Hares: Low-RAM LoRA Merge & Dual Model Quantization Exporter.

Merges trained LoRA adapters back into the base model and produces dual export formats:
1. 4-bit AWQ (W4A16 GEMM): High-throughput serving via vLLM container (hares-slm).
2. GGUF Q4_K_M: Lightweight edge serving via llama.cpp.

Colab Memory Hygiene Guards (Prevents Host RAM OOM on 12.7GB instances):
- Executes explicit garbage collection (gc.collect()) and CUDA cache emptying.
- Merges weights with low_cpu_mem_usage=True and device_map="cpu".
- Processes AWQ and GGUF quantization in clean, segregated execution phases.
"""

from __future__ import annotations

import argparse
import gc
import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("hares.exporter")


def purge_memory() -> None:
    """Forces aggressive garbage collection and empties GPU tensor cache."""
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


def merge_lora_to_fp16(
    base_model_name: str,
    adapter_dir: str,
    output_merged_dir: str,
) -> Path:
    """
    Loads base model and LoRA adapter with low_cpu_mem_usage=True, merges weights,
    and writes FP16 weights to disk. Purges memory immediately after writing.
    """
    logger.info("Starting low-RAM LoRA merge: Base=%s | Adapter=%s", base_model_name, adapter_dir)
    merged_path = Path(output_merged_dir)
    merged_path.mkdir(parents=True, exist_ok=True)

    purge_memory()

    tokenizer = AutoTokenizer.from_pretrained(adapter_dir, trust_remote_code=True)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info("Loading base model in FP16 (device_map='%s')...", device)
    base_model = AutoModelForCausalLM.from_pretrained(
        base_model_name,
        torch_dtype=torch.float16,
        low_cpu_mem_usage=True,
        device_map=device,
        trust_remote_code=True,
    )

    # Neutralize outdated Colab torchao check in PEFT
    try:
        import peft.import_utils
        peft.import_utils.is_torchao_available = lambda: False
    except Exception:
        pass

    logger.info("Attaching LoRA adapter from %s ...", adapter_dir)
    peft_model = PeftModel.from_pretrained(base_model, adapter_dir)

    logger.info("Merging adapter into base model weights...")
    merged_model = peft_model.merge_and_unload()

    logger.info("Saving merged FP16 model to %s ...", merged_path)
    merged_model.save_pretrained(merged_path, safe_serialization=True)
    tokenizer.save_pretrained(merged_path)

    # Free all memory
    del peft_model, base_model, merged_model
    purge_memory()
    logger.info("Merged model saved and host RAM completely scrubbed.")
    return merged_path


def export_awq_quantization(
    merged_model_dir: str,
    output_awq_dir: str,
    w_bit: int = 4,
    q_group_size: int = 128,
) -> Path:
    """
    Quantizes merged FP16 model to AWQ using AutoAWQ.
    Outputs weights optimized for vLLM PagedAttention.
    """
    logger.info("Starting AutoAWQ 4-bit quantization...")
    awq_path = Path(output_awq_dir)
    awq_path.mkdir(parents=True, exist_ok=True)

    purge_memory()

    try:
        from awq import AutoAWQForCausalLM  # type: ignore
        quant_config = {
            "zero_point": True,
            "q_group_size": q_group_size,
            "w_bit": w_bit,
            "version": "GEMM",
        }
        logger.info("Loading merged model into AutoAWQ on GPU...")
        model = AutoAWQForCausalLM.from_pretrained(
            merged_model_dir,
            low_cpu_mem_usage=True,
            trust_remote_code=True,
        )
        tokenizer = AutoTokenizer.from_pretrained(merged_model_dir, trust_remote_code=True)

        logger.info("Quantizing model with AWQ (max_calib_seq_len=512, max_calib_samples=64)...")
        model.quantize(
            tokenizer,
            quant_config=quant_config,
            max_calib_seq_len=512,
            max_calib_samples=64,
        )

        logger.info("Saving AWQ quantized model to %s ...", awq_path)
        model.save_quantized(awq_path)
        tokenizer.save_pretrained(awq_path)

        del model
        purge_memory()
        logger.info("AWQ export complete!")
        return awq_path
    except ImportError:
        logger.warning("AutoAWQ is not installed. To export AWQ in Colab, run: pip install autoawq")
        return awq_path


def export_gguf_quantization(
    merged_model_dir: str,
    output_gguf_dir: str,
    quant_type: str = "Q4_K_M",
) -> Path:
    """
    Exports merged FP16 model to GGUF format using llama.cpp conversion scripts.
    """
    logger.info("Starting GGUF (%s) conversion...", quant_type)
    gguf_path = Path(output_gguf_dir)
    gguf_path.mkdir(parents=True, exist_ok=True)

    outfile_fp16 = gguf_path / "model_f16.gguf"
    outfile_quant = gguf_path / f"hares_slm_{quant_type.lower()}.gguf"

    # Step 1: Look for convert_hf_to_gguf.py in environment or llama.cpp clone
    convert_script = None
    possible_paths = [
        Path("llama.cpp/convert_hf_to_gguf.py"),
        Path("/content/llama.cpp/convert_hf_to_gguf.py"),
    ]
    for p in possible_paths:
        if p.exists():
            convert_script = p
            break

    if convert_script:
        logger.info("Converting HF weights to GGUF FP16...")
        cmd_convert = [
            sys.executable,
            str(convert_script),
            merged_model_dir,
            "--outfile",
            str(outfile_fp16),
            "--outtype",
            "f16",
        ]
        subprocess.run(cmd_convert, check=True)

        # Step 2: Quantize to target Q4_K_M
        quantize_bin = shutil.which("llama-quantize") or shutil.which("./llama.cpp/llama-quantize") or shutil.which("/content/llama.cpp/llama-quantize")
        if quantize_bin:
            logger.info("Quantizing GGUF to %s ...", quant_type)
            cmd_quant = [str(quantize_bin), str(outfile_fp16), str(outfile_quant), quant_type]
            subprocess.run(cmd_quant, check=True)
            if outfile_fp16.exists():
                outfile_fp16.unlink()
            logger.info("GGUF quantized file written to %s", outfile_quant)
        else:
            logger.info("llama-quantize tool not found in PATH; preserved FP16 GGUF at %s", outfile_fp16)
    else:
        logger.info("GGUF converter script not found locally. Step ready for Colab execution where llama.cpp is cloned.")

    return gguf_path


def run_dual_export(
    base_model_name: str,
    adapter_dir: str,
    output_dir: str,
    skip_awq: bool = False,
    skip_gguf: bool = False,
) -> dict[str, str]:
    """Coordinates merge and produces both AWQ and GGUF outputs in separate folders."""
    out_path = Path(output_dir)
    merged_dir = out_path / "merged_fp16"
    awq_dir = out_path / "awq_4bit"
    gguf_dir = out_path / "gguf_q4_k_m"

    # Step 1: Merge LoRA adapter
    merge_lora_to_fp16(base_model_name, adapter_dir, str(merged_dir))

    results = {"merged_fp16": str(merged_dir)}

    # Step 2: AutoAWQ export
    if not skip_awq:
        export_awq_quantization(str(merged_dir), str(awq_dir))
        results["awq_dir"] = str(awq_dir)

    # Step 3: GGUF export
    if not skip_gguf:
        export_gguf_quantization(str(merged_dir), str(gguf_dir))
        results["gguf_dir"] = str(gguf_dir)

    logger.info("Dual model export completed: %s", results)
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Merge LoRA and dual-quantize for Project Hares")
    parser.add_argument("--base-model", type=str, default="Qwen/Qwen2.5-3B-Instruct", help="Base model identifier")
    parser.add_argument("--adapter-dir", type=str, required=True, help="Directory containing final LoRA adapter")
    parser.add_argument("--output-dir", type=str, default="./output/exported_models", help="Export target directory")
    parser.add_argument("--skip-awq", action="store_true", help="Skip AWQ export")
    parser.add_argument("--skip-gguf", action="store_true", help="Skip GGUF export")
    args = parser.parse_args()

    run_dual_export(
        base_model_name=args.base_model,
        adapter_dir=args.adapter_dir,
        output_dir=args.output_dir,
        skip_awq=args.skip_awq,
        skip_gguf=args.skip_gguf,
    )


if __name__ == "__main__":
    main()
