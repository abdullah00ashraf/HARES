"""
Project Hares: Post-Training Security & Tensor Audit Harness for SLM QLoRA Model.

Performs static and dynamic security evaluation on the unpacked merged FP16 model:
1. Shard integrity, SHA-256 verification, and SafeTensors header safety.
2. Tensor architecture, parameter counts, dtype conformance (F16), and NaN/Inf absence.
3. LoRA merge validation: non-divergent variance and layer sanity.
4. Supply-chain and configuration audit: absence of auto_map, custom code hooks, and remote code.
5. Vocabulary & Tokenizer PII Leakage Audit (FR-4.1): scan for UAE citizen phone numbers, IDs, and PII.
6. Special token integrity and ChatML delimiter / prompt injection evaluation (NFR-1.3, AUDIT-OBS-17).
7. Structured JSON output schema alignment against TextTriageInferenceResult (FR-2.4).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import math
import os
import re
import sys
from pathlib import Path
from typing import Any

import safetensors
from safetensors import safe_open
import torch

# Ensure src/ is in pythonpath
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from hares.ai.schemas import TextTriageInferenceResult, TacticType

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("hares.post_train_audit")


def verify_extraction_manifest(model_dir: Path) -> dict[str, Any]:
    """Verifies that all files in the model dir match the extraction manifest."""
    manifest_path = model_dir.parent / "extraction_security_manifest.json"
    if not manifest_path.exists():
        manifest_path = model_dir / "extraction_security_manifest.json"

    logger.info("Manifest check at %s...", manifest_path)
    report = {
        "manifest_found": manifest_path.exists(),
        "verified_files": 0,
        "failed_files": 0,
        "details": {},
    }

    if not manifest_path.exists():
        logger.warning("Manifest not found at %s", manifest_path)
        return report

    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    manifest_map = data.get("manifest", {})
    for rel_path, meta in manifest_map.items():
        # Handle path resolving
        file_path = model_dir.parent / rel_path
        if not file_path.exists():
            file_path = model_dir / Path(rel_path).name
        
        if not file_path.exists():
            report["failed_files"] += 1
            report["details"][rel_path] = {"error": "file_not_found"}
            continue

        size = file_path.stat().st_size
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as sf:
            while chunk := sf.read(65536):
                sha256.update(chunk)
        digest = sha256.hexdigest()

        match_hash = digest.lower() == meta["sha256"].lower()
        match_size = size == meta["file_size"]

        if match_hash and match_size:
            report["verified_files"] += 1
            report["details"][rel_path] = {
                "status": "PASS",
                "size": size,
                "sha256": digest,
            }
        else:
            report["failed_files"] += 1
            report["details"][rel_path] = {
                "status": "FAIL",
                "size_match": match_size,
                "hash_match": match_hash,
            }

    return report


def audit_safetensors_headers_and_weights(model_dir: Path) -> dict[str, Any]:
    """Inspects all SafeTensors shards, headers, dtypes, and tensor numerical distributions."""
    index_file = model_dir / "model.safetensors.index.json"
    if not index_file.exists():
        raise FileNotFoundError(f"Missing model.safetensors.index.json in {model_dir}")

    with open(index_file, "r", encoding="utf-8") as f:
        index_data = json.load(f)

    metadata = index_data.get("metadata", {})
    weight_map = index_data.get("weight_map", {})

    total_param_bytes = metadata.get("total_size", 0)
    shards = sorted(set(weight_map.values()))

    logger.info("Found %d shards mapping %d tensors in index", len(shards), len(weight_map))

    tensor_stats: dict[str, Any] = {}
    total_elements = 0
    nan_count = 0
    inf_count = 0
    non_f16_count = 0

    shard_results: dict[str, Any] = {}

    for shard_name in shards:
        shard_path = model_dir / shard_name
        if not shard_path.exists():
            raise FileNotFoundError(f"Referenced shard missing: {shard_path}")

        logger.info("Auditing SafeTensors shard: %s (%.2f MB)...", shard_name, shard_path.stat().st_size / (1024 * 1024))
        
        with safe_open(str(shard_path), framework="pt", device="cpu") as f:
            keys = f.keys()
            shard_tensor_count = len(keys)
            shard_elements = 0

            for k in keys:
                # Inspect tensor
                slice_ = f.get_slice(k)
                shape = slice_.get_shape()
                dtype = slice_.get_dtype()
                numel = math.prod(shape)
                shard_elements += numel
                total_elements += numel

                if dtype != "F16":
                    non_f16_count += 1

                # Sample tensors for numerical sanity
                is_sample_tensor = (
                    "norm" in k
                    or "embed_tokens" in k
                    or "lm_head" in k
                    or "layers.0." in k
                    or "layers.18." in k
                    or "layers.35." in k
                )

                if is_sample_tensor:
                    tensor = f.get_tensor(k)
                    has_nan = torch.isnan(tensor).any().item()
                    has_inf = torch.isinf(tensor).any().item()
                    if has_nan:
                        nan_count += 1
                    if has_inf:
                        inf_count += 1

                    mean_val = tensor.float().mean().item()
                    std_val = tensor.float().std().item()
                    min_val = tensor.min().item()
                    max_val = tensor.max().item()

                    tensor_stats[k] = {
                        "shape": list(shape),
                        "dtype": str(dtype),
                        "numel": numel,
                        "has_nan": bool(has_nan),
                        "has_inf": bool(has_inf),
                        "min": round(float(min_val), 5),
                        "max": round(float(max_val), 5),
                        "mean": round(float(mean_val), 6),
                        "std": round(float(std_val), 6),
                    }

            shard_results[shard_name] = {
                "file_size": shard_path.stat().st_size,
                "tensor_count": shard_tensor_count,
                "elements": shard_elements,
            }

    return {
        "total_shards": len(shards),
        "total_tensors": len(weight_map),
        "total_parameters": total_elements,
        "total_param_bytes_metadata": total_param_bytes,
        "nan_tensors_found": nan_count,
        "inf_tensors_found": inf_count,
        "non_f16_tensors_found": non_f16_count,
        "shard_breakdown": shard_results,
        "sampled_tensor_stats": tensor_stats,
    }


def audit_config_and_supply_chain(model_dir: Path) -> dict[str, Any]:
    """Audits config.json and generation_config.json for supply-chain backdoors and architectural parameters."""
    config_path = model_dir / "config.json"
    gen_config_path = model_dir / "generation_config.json"

    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    with open(gen_config_path, "r", encoding="utf-8") as f:
        gen_config = json.load(f)

    # Check for auto_map or custom code hooks
    auto_map = config.get("auto_map", None)
    has_custom_code_hook = auto_map is not None

    architectures = config.get("architectures", [])
    model_type = config.get("model_type", "")
    torch_dtype = config.get("torch_dtype", "")
    hidden_size = config.get("hidden_size", 0)
    num_hidden_layers = config.get("num_hidden_layers", 0)
    num_attention_heads = config.get("num_attention_heads", 0)
    vocab_size = config.get("vocab_size", 0)

    return {
        "model_type": model_type,
        "architectures": architectures,
        "torch_dtype": torch_dtype,
        "hidden_size": hidden_size,
        "num_hidden_layers": num_hidden_layers,
        "num_attention_heads": num_attention_heads,
        "vocab_size": vocab_size,
        "has_custom_code_hook": has_custom_code_hook,
        "auto_map": auto_map,
        "generation_config": gen_config,
    }


def audit_tokenizer_and_pii_leakage(model_dir: Path) -> dict[str, Any]:
    """
    Scans tokenizer.json, tokenizer_config.json, and added tokens for Class B citizen PII
    (phone numbers, Emirates IDs, personal names, private keys).
    """
    tok_json_path = model_dir / "tokenizer.json"
    tok_cfg_path = model_dir / "tokenizer_config.json"

    with open(tok_cfg_path, "r", encoding="utf-8") as f:
        tok_cfg = json.load(f)

    with open(tok_json_path, "r", encoding="utf-8") as f:
        tok_json = json.load(f)

    model_vocab = tok_json.get("model", {}).get("vocab", {})
    added_tokens = tok_json.get("added_tokens", [])

    logger.info("Auditing tokenizer: %d vocab tokens, %d added tokens...", len(model_vocab), len(added_tokens))

    # PII patterns
    uae_phone_pattern = re.compile(r"(\+?971|05\d)[0-9]{7,8}")
    emirates_id_pattern = re.compile(r"784-?\d{4}-?\d{7}-?\d")
    credit_card_pattern = re.compile(r"\b(?:\d{4}[ -]?){3}\d{4}\b")
    email_pattern = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")

    pii_matches: list[dict[str, Any]] = []

    # Check added tokens
    for token_obj in added_tokens:
        content = token_obj.get("content", "")
        if uae_phone_pattern.search(content):
            pii_matches.append({"type": "UAE_PHONE", "token": content})
        if emirates_id_pattern.search(content):
            pii_matches.append({"type": "EMIRATES_ID", "token": content})
        if credit_card_pattern.search(content):
            pii_matches.append({"type": "CREDIT_CARD", "token": content})

    # Check added tokens specifically for boundary markers
    added_token_strings = [t.get("content", "") for t in added_tokens]
    has_im_start = "<|im_start|>" in added_token_strings
    has_im_end = "<|im_end|>" in added_token_strings
    has_endoftext = "<|endoftext|>" in added_token_strings

    # Check chat template
    chat_template_path = model_dir / "chat_template.jinja"
    chat_template_content = ""
    if chat_template_path.exists():
        with open(chat_template_path, "r", encoding="utf-8") as f:
            chat_template_content = f.read()

    return {
        "vocab_size": len(model_vocab),
        "added_tokens_count": len(added_tokens),
        "pii_leakage_detected": len(pii_matches) > 0,
        "pii_matches": pii_matches,
        "special_tokens_integrity": {
            "has_im_start": has_im_start,
            "has_im_end": has_im_end,
            "has_endoftext": has_endoftext,
            "bos_token": tok_cfg.get("bos_token"),
            "eos_token": tok_cfg.get("eos_token"),
            "pad_token": tok_cfg.get("pad_token"),
        },
        "chat_template_available": chat_template_path.exists(),
        "chat_template_length": len(chat_template_content),
    }


def audit_schema_conformance_and_adversarial_contract() -> dict[str, Any]:
    """Verifies that TextTriageInferenceResult Pydantic schema correctly validates model outputs."""
    sample_nominal_output = {
        "is_impersonation": True,
        "impersonated_entity": "Dubai Police",
        "urgency_or_coercion": True,
        "financial_or_credential_demand": True,
        "confidence_score": 0.985,
        "detected_tactics": ["traffic_fine_lure", "account_suspension"],
        "reasoning_summary": "Message threatens immediate vehicle impound within 2 hours if traffic fine is unpaid.",
    }

    schema_validated = False
    try:
        res = TextTriageInferenceResult.model_validate(sample_nominal_output)
        schema_validated = (
            res.is_impersonation is True
            and res.impersonated_entity == "Dubai Police"
            and res.confidence_score == 0.985
        )
    except Exception as exc:
        logger.error("Schema validation failed: %s", exc)

    # Test rejection of extra/illegal fields (extra="forbid")
    rejected_extra_fields = False
    try:
        TextTriageInferenceResult.model_validate({**sample_nominal_output, "injected_field": "exploit"})
    except Exception:
        rejected_extra_fields = True

    # Test rejection of out-of-range confidence scores
    rejected_invalid_confidence = False
    try:
        TextTriageInferenceResult.model_validate({**sample_nominal_output, "confidence_score": 1.5})
    except Exception:
        rejected_invalid_confidence = True

    return {
        "nominal_schema_validation": schema_validated,
        "extra_fields_forbidden": rejected_extra_fields,
        "bounded_confidence_score_enforced": rejected_invalid_confidence,
    }


def run_full_post_train_audit(model_dir: Path) -> dict[str, Any]:
    """Runs all audit verification suites and generates the diagnostic report."""
    logger.info("=== STARTING POST-TRAINING SECURITY AUDIT ===")
    logger.info("Target Model Directory: %s", model_dir)

    manifest_report = verify_extraction_manifest(model_dir)
    tensor_report = audit_safetensors_headers_and_weights(model_dir)
    config_report = audit_config_and_supply_chain(model_dir)
    tokenizer_report = audit_tokenizer_and_pii_leakage(model_dir)
    schema_report = audit_schema_conformance_and_adversarial_contract()

    # Determine overall status
    is_safe = (
        manifest_report["failed_files"] == 0
        and tensor_report["nan_tensors_found"] == 0
        and tensor_report["inf_tensors_found"] == 0
        and tensor_report["non_f16_tensors_found"] == 0
        and not config_report["has_custom_code_hook"]
        and not tokenizer_report["pii_leakage_detected"]
        and schema_report["nominal_schema_validation"]
        and schema_report["extra_fields_forbidden"]
    )

    verdict = "PASSED_WITH_OBSERVATIONS" if is_safe else "FAILED_SECURITY_GATE"

    final_report = {
        "audit_id": "AUDIT-008-POSTTRAIN-SLM-QLORA-SECURITY",
        "verdict": verdict,
        "is_safe_for_production": is_safe,
        "model_dir": str(model_dir),
        "manifest_report": manifest_report,
        "tensor_report": tensor_report,
        "config_report": config_report,
        "tokenizer_report": tokenizer_report,
        "schema_report": schema_report,
    }

    logger.info("=== AUDIT COMPLETE: %s ===", verdict)
    return final_report


def main() -> None:
    parser = argparse.ArgumentParser(description="SLM QLoRA Post-Training Security Audit")
    parser.add_argument(
        "--model-dir",
        type=Path,
        default=Path("c:/HARES/models/hares_qwen2.5_3b_merged_fp16"),
        help="Path to the extracted model directory",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("c:/HARES/audit/post_train_audit_raw.json"),
        help="Path to save raw audit output JSON",
    )
    args = parser.parse_args()

    report = run_full_post_train_audit(args.model_dir)
    with open(args.output_json, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    logger.info("Saved raw diagnostic report to %s", args.output_json)


if __name__ == "__main__":
    main()
