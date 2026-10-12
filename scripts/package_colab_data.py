"""
Project Hares: Google Colab Data Packager & Curriculum Staging Tool.

Prepares compressed, integrity-verified dataset packages for Google Colab training:
1. Gzips the 100,000-record ChatML smishing corpus.
2. Extracts a stratified, balanced 25,000-sample curriculum core subset for fast T4 GPU verification:
   - 40% Emirati / Gulf Arabic (10,000)
   - 30% Modern Standard Arabic (7,500)
   - 20% UAE Expat English (5,000)
   - 10% Arabizi / Franco-Arabic (2,500)
   - Class balance: 70% Malicious (17,500) / 30% Benign (7,500)
3. Packages audio metadata catalog and creates directory archives.
4. Generates SHA-256 checksum manifests for Google Drive synchronization.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import logging
import os
import shutil
import sys
import tarfile
from pathlib import Path
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("hares.packager")

DEFAULT_SMISHING_100K = Path("opensource/datasets/localized_fraud_corpus/uae_smishing_100k.jsonl")
DEFAULT_AUDIO_DIR = Path("opensource/datasets/synthetic_voice_eval")
DEFAULT_OUTPUT_DIR = Path("colab_packages")


def compute_sha256(file_path: Path) -> str:
    """Computes the SHA-256 hexadecimal hash of a file."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def compress_file_gzip(source_file: Path, target_file: Path) -> int:
    """Compresses a file using gzip, returning output size in bytes."""
    logger.info("Compressing %s -> %s ...", source_file, target_file)
    with open(source_file, "rb") as f_in, gzip.open(target_file, "wb", compresslevel=6) as f_out:
        shutil.copyfileobj(f_in, f_out)
    size_bytes = target_file.stat().st_size
    logger.info("Compressed %s: %.2f MB", target_file.name, size_bytes / (1024 * 1024))
    return size_bytes


def generate_curriculum_25k_subset(
    source_jsonl: Path,
    output_jsonl: Path,
    target_count: int = 25_000,
) -> dict[str, Any]:
    """
    Extracts a balanced, stratified 25,000 sample subset from the 100,000 ChatML corpus.
    Preserves dialect breakdown and malicious/benign distribution.
    """
    logger.info("Generating %d-sample curriculum core subset from %s ...", target_count, source_jsonl)

    # Stratified target counts (proportional to 100k)
    quota = {
        "emirati_gulf_malicious": int(target_count * 0.40 * 0.70),  # 7,000
        "emirati_gulf_benign": int(target_count * 0.40 * 0.30),     # 3,000
        "msa_malicious": int(target_count * 0.30 * 0.70),          # 5,250
        "msa_benign": int(target_count * 0.30 * 0.30),             # 2,250
        "expat_english_malicious": int(target_count * 0.20 * 0.70),# 3,500
        "expat_english_benign": int(target_count * 0.20 * 0.30),   # 1,500
        "arabizi_malicious": int(target_count * 0.10 * 0.70),      # 1,750
        "arabizi_benign": int(target_count * 0.10 * 0.30),         # 750
    }

    counts: dict[str, int] = {k: 0 for k in quota}
    collected_records: list[str] = []

    with open(source_jsonl, "r", encoding="utf-8") as f_in:
        for line in f_in:
            if not line.strip():
                continue
            try:
                record = json.loads(line)
                messages = record.get("messages", [])
                user_msg = next((m["content"] for m in messages if m["role"] == "user"), "")
                assistant_msg = next((m["content"] for m in messages if m["role"] == "assistant"), "")
                asst_data = json.loads(assistant_msg)
                is_malicious = asst_data.get("is_impersonation", False) or asst_data.get("urgency_or_coercion", False) or asst_data.get("financial_or_credential_demand", False)
            except Exception:
                continue

            # Identify dialect group
            is_arabic = any("\u0600" <= c <= "\u06FF" for c in user_msg)
            has_arabizi = any(kw in user_msg.lower() for kw in ["habibi", "mabrook", "police", "dirhams", "urgent", "el-"]) and not is_arabic
            
            if is_arabic:
                emirati_cues = ["يا خوي", "طال عمرك", "موترك", "الحبيب", "بو محمد", "سدد", "درهم", "الشيخ", "رصيد سالك"]
                if any(cue in user_msg for cue in emirati_cues):
                    key = "emirati_gulf_malicious" if is_malicious else "emirati_gulf_benign"
                else:
                    key = "msa_malicious" if is_malicious else "msa_benign"
            elif has_arabizi:
                key = "arabizi_malicious" if is_malicious else "arabizi_benign"
            else:
                key = "expat_english_malicious" if is_malicious else "expat_english_benign"

            if counts.get(key, 0) < quota.get(key, 0):
                counts[key] += 1
                collected_records.append(line)

            if len(collected_records) >= target_count:
                break

    # If any slot is slightly short due to heuristic matching, fill remainder
    if len(collected_records) < target_count:
        with open(source_jsonl, "r", encoding="utf-8") as f_in:
            for line in f_in:
                if line.strip():
                    collected_records.append(line)
                    if len(collected_records) >= target_count:
                        break

    output_jsonl.parent.mkdir(parents=True, exist_ok=True)
    with open(output_jsonl, "w", encoding="utf-8") as f_out:
        f_out.writelines(collected_records)

    manifest = {
        "dataset_name": f"Project Hares Curriculum Core Subset ({target_count // 1000}K)",
        "source_dataset": str(source_jsonl),
        "total_records": len(collected_records),
        "target_file": str(output_jsonl),
        "file_size_bytes": output_jsonl.stat().st_size,
        "counts_by_stratum": counts,
    }
    manifest_path = output_jsonl.with_suffix(".manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f_m:
        json.dump(manifest, f_m, indent=2)

    logger.info("Generated curriculum subset with %d records (%.2f MB)", len(collected_records), output_jsonl.stat().st_size / (1024 * 1024))
    return manifest


def package_all_datasets(output_dir: Path = DEFAULT_OUTPUT_DIR) -> dict[str, Any]:
    """Packages all datasets, generates curriculum subset, and produces checksum manifests."""
    output_dir.mkdir(parents=True, exist_ok=True)
    results: dict[str, Any] = {"files": {}, "checksums": {}}

    # 1. 100K Smishing Dataset
    if DEFAULT_SMISHING_100K.exists():
        gz_100k = output_dir / "uae_smishing_100k.jsonl.gz"
        compress_file_gzip(DEFAULT_SMISHING_100K, gz_100k)
        results["files"]["smishing_100k_gz"] = str(gz_100k)
        results["checksums"]["smishing_100k_gz"] = compute_sha256(gz_100k)

        # 2. 25K Curriculum Core Subset
        subset_25k = output_dir / "uae_smishing_25k_core.jsonl"
        manifest_25k = generate_curriculum_25k_subset(DEFAULT_SMISHING_100K, subset_25k, target_count=25_000)
        gz_25k = output_dir / "uae_smishing_25k_core.jsonl.gz"
        compress_file_gzip(subset_25k, gz_25k)
        results["files"]["smishing_25k_gz"] = str(gz_25k)
        results["checksums"]["smishing_25k_gz"] = compute_sha256(gz_25k)
        results["manifest_25k"] = manifest_25k
    else:
        logger.warning("100K Smishing dataset not found at %s", DEFAULT_SMISHING_100K)

    # 3. Audio Metadata & Manifest Copy
    audio_meta = DEFAULT_AUDIO_DIR / "audio_metadata.jsonl"
    audio_manifest = DEFAULT_AUDIO_DIR / "audio_corpus_manifest.json"
    if audio_meta.exists():
        dest_meta = output_dir / "audio_metadata.jsonl"
        shutil.copy2(audio_meta, dest_meta)
        results["files"]["audio_metadata"] = str(dest_meta)
        results["checksums"]["audio_metadata"] = compute_sha256(dest_meta)

    if audio_manifest.exists():
        dest_manifest = output_dir / "audio_corpus_manifest.json"
        shutil.copy2(audio_manifest, dest_manifest)
        results["files"]["audio_manifest"] = str(dest_manifest)

    # 4. Save Comprehensive Packaging Manifest
    manifest_file = output_dir / "colab_package_manifest.json"
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    logger.info("Packaging complete! Manifest written to %s", manifest_file)
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Package Project Hares datasets for Google Colab")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR, help="Destination directory for packages")
    parser.add_argument("--subset-only", action="store_true", help="Only generate the 25k curriculum subset")
    args = parser.parse_args()

    if args.subset_only:
        subset_path = args.output_dir / "uae_smishing_25k_core.jsonl"
        generate_curriculum_25k_subset(DEFAULT_SMISHING_100K, subset_path)
    else:
        package_all_datasets(args.output_dir)


if __name__ == "__main__":
    main()
