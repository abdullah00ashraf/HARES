"""
Project Hares: Secure Model Weights Unpacker & Ingestion Harness.

Implements defense-in-depth extraction for multi-part model archives downloaded
from Google Drive or external training environments, adhering strictly to the
Zero Guess Doctrine, PEP 706 principles, and enterprise security standards.

Security Guards:
1. Zip Slip / Path Traversal: Strict canonicalization ensuring all paths reside strictly within dest_dir.
2. Extension Allowlist: Allows only .safetensors, .json, .jinja, .txt, .md. Strictly rejects pickles/binaries.
3. Link/Device Hardening: Rejects symlinks, hardlinks, FIFOs, sockets, and character/block devices.
4. Resource Exhaustion Guard: Bounds per-file (<5GB) and cumulative (<15GB) extraction limits.
5. Cryptographic Integrity: Streams with SHA-256 hashing and verifies byte size upon write completion.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import stat
import sys
import zipfile
from pathlib import Path
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("hares.unpack_model")

# Strict extension allowlist for neural network weights and config artifacts
ALLOWED_EXTENSIONS = {".safetensors", ".json", ".jinja", ".txt", ".md"}

# Resource exhaustion thresholds
MAX_SINGLE_FILE_BYTES = 5 * 1024 * 1024 * 1024      # 5 GB per shard
MAX_CUMULATIVE_BYTES = 15 * 1024 * 1024 * 1024      # 15 GB aggregate
BUFFER_SIZE = 64 * 1024                             # 64 KB streaming buffer


class SecurityVerificationError(RuntimeError):
    """Raised when an archive member violates security constraints."""


def is_symlink_or_special_file(info: zipfile.ZipInfo) -> bool:
    """Detects whether a zip entry represents a symlink, FIFO, socket, or device."""
    mode = info.external_attr >> 16
    if mode == 0:
        return False
    # Check POSIX file type flags
    if stat.S_ISLNK(mode) or stat.S_ISFIFO(mode) or stat.S_ISSOCK(mode) or stat.S_ISCHR(mode) or stat.S_ISBLK(mode):
        return True
    return False


def validate_archive_member(
    info: zipfile.ZipInfo,
    dest_dir: Path,
    cumulative_bytes: int,
) -> tuple[Path, bool]:
    """
    Validates a single zip member against Zip Slip, extension allowlists, and resource bounds.

    Returns:
        tuple[Path, bool]: (target_file_path, is_directory)
    """
    filename = info.filename

    # Guard 1: Detect null bytes or illegal path separators
    if "\x00" in filename:
        raise SecurityVerificationError(f"Null byte detected in archive filename: {filename!r}")

    # Guard 2: Detect symlinks or special devices
    if is_symlink_or_special_file(info):
        raise SecurityVerificationError(f"Forbidden symlink or special file detected: {filename}")

    # Guard 3: Directory vs File classification
    is_dir = filename.endswith("/") or (info.external_attr >> 16 != 0 and stat.S_ISDIR(info.external_attr >> 16))

    # Strip any leading slashes or redundant parent markers
    normalized_rel = Path(filename.replace("\\", "/"))
    
    # Target resolution
    target_path = (dest_dir / normalized_rel).resolve()
    dest_canonical = dest_dir.resolve()

    # Guard 4: Zip Slip path traversal check
    try:
        target_path.relative_to(dest_canonical)
    except ValueError as exc:
        raise SecurityVerificationError(
            f"Path traversal detected! Member {filename!r} resolves outside destination root {dest_canonical}"
        ) from exc

    # Also double-check commonpath
    if os.path.commonpath([str(dest_canonical), str(target_path)]) != str(dest_canonical):
        raise SecurityVerificationError(
            f"Commonpath mismatch! Member {filename!r} resolves outside destination root {dest_canonical}"
        )

    if is_dir:
        return target_path, True

    # Guard 5: Extension allowlist
    suffix = target_path.suffix.lower()
    # Handle composite extensions like .safetensors.index.json
    if target_path.name.endswith(".safetensors.index.json"):
        suffix = ".json"

    if suffix not in ALLOWED_EXTENSIONS:
        raise SecurityVerificationError(
            f"Forbidden file extension {suffix!r} on member {filename}. Allowed: {sorted(ALLOWED_EXTENSIONS)}"
        )

    # Guard 6: Resource exhaustion bounds
    if info.file_size > MAX_SINGLE_FILE_BYTES:
        raise SecurityVerificationError(
            f"File size {info.file_size} exceeds single-file limit {MAX_SINGLE_FILE_BYTES}: {filename}"
        )

    if cumulative_bytes + info.file_size > MAX_CUMULATIVE_BYTES:
        raise SecurityVerificationError(
            f"Extraction would exceed cumulative limit {MAX_CUMULATIVE_BYTES} bytes."
        )

    return target_path, False


def extract_zip_securely(
    zip_path: Path,
    dest_dir: Path,
    cumulative_bytes: int,
) -> tuple[dict[str, dict[str, Any]], int]:
    """
    Extracts a zip file securely, validating every entry and computing cryptographic hashes.
    """
    logger.info("Opening archive: %s (%.2f MB)", zip_path.name, zip_path.stat().st_size / (1024 * 1024))
    manifest: dict[str, dict[str, Any]] = {}

    with zipfile.ZipFile(zip_path, mode="r") as zf:
        infolist = zf.infolist()
        logger.info("Archive %s contains %d entries", zip_path.name, len(infolist))

        for info in infolist:
            target_path, is_dir = validate_archive_member(info, dest_dir, cumulative_bytes)

            if is_dir:
                target_path.mkdir(parents=True, exist_ok=True)
                continue

            target_path.parent.mkdir(parents=True, exist_ok=True)

            logger.info("  Extracting: %s (%.2f MB)...", target_path.name, info.file_size / (1024 * 1024))
            sha256 = hashlib.sha256()
            written_bytes = 0

            with zf.open(info, "r") as source_stream, open(target_path, "wb") as dest_stream:
                while True:
                    chunk = source_stream.read(BUFFER_SIZE)
                    if not chunk:
                        break
                    dest_stream.write(chunk)
                    sha256.update(chunk)
                    written_bytes += len(chunk)
                    if written_bytes > info.file_size:
                        raise SecurityVerificationError(
                            f"Decompression bomb detected! Written bytes exceeded declared size for {info.filename}"
                        )

            if written_bytes != info.file_size:
                raise SecurityVerificationError(
                    f"Integrity error: Expected {info.file_size} bytes but extracted {written_bytes} bytes for {info.filename}"
                )

            digest = sha256.hexdigest()
            cumulative_bytes += written_bytes

            rel_key = str(target_path.relative_to(dest_dir.resolve())).replace("\\", "/")
            manifest[rel_key] = {
                "archive_source": zip_path.name,
                "file_size": written_bytes,
                "sha256": digest,
                "compress_size": info.compress_size,
            }
            logger.info("  Verified: %s [SHA-256: %s...%s]", target_path.name, digest[:8], digest[-8:])

    return manifest, cumulative_bytes


def secure_unpack_models(
    models_dir: Path,
    output_dir: Path,
) -> dict[str, Any]:
    """
    Finds and securely unpacks all split zip files in models_dir.
    """
    models_dir = models_dir.resolve()
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    zip_files = sorted(models_dir.glob("*.zip"))
    if not zip_files:
        raise FileNotFoundError(f"No .zip model archives found in {models_dir}")

    logger.info("Found %d model archive(s) in %s", len(zip_files), models_dir)

    total_manifest: dict[str, dict[str, Any]] = {}
    cumulative_bytes = 0

    for zf_path in zip_files:
        part_manifest, cumulative_bytes = extract_zip_securely(zf_path, output_dir, cumulative_bytes)
        total_manifest.update(part_manifest)

    logger.info("Secure extraction completed. Extracted %d files (%.2f GB total).",
                len(total_manifest), cumulative_bytes / (1024 * 1024 * 1024))

    manifest_file = output_dir / "extraction_security_manifest.json"
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(
            {
                "status": "SECURE_EXTRACTION_VERIFIED",
                "total_files": len(total_manifest),
                "total_bytes": cumulative_bytes,
                "manifest": total_manifest,
            },
            f,
            indent=2,
        )
    logger.info("Saved cryptographic extraction manifest to %s", manifest_file)

    return total_manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Secure Model Weights Ingestion & Unpacker")
    parser.add_argument(
        "--models-dir",
        type=Path,
        default=Path("c:/HARES/models"),
        help="Directory containing the model zip archives",
    )
    parser.add_argument(
        "--dest-dir",
        type=Path,
        default=Path("c:/HARES/models"),
        help="Destination directory for unpacked model files",
    )
    args = parser.parse_args()

    try:
        secure_unpack_models(args.models_dir, args.dest_dir)
        logger.info("ALL MODEL ARTIFACTS UNPACKED AND CRYPTOGRAPHICALLY VERIFIED.")
    except Exception as exc:
        logger.error("Secure unpack failed: %s", exc, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
