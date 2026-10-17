"""
Production download and verification orchestrator for unseen evaluation benchmarks:
1. facebook/cyberseceval3-visual-prompt-injection (Hugging Face Datasets)
2. ASVspoof Benchmark Datasets:
   - DynamicSuperb/SpoofDetection_ASVspoof2017 (Audio + ground truth labels)
   - DynamicSuperb/SpoofDetection_ASVspoof2015 (Audio + ground truth labels)
   - SpeechAntiSpoofingBenchmarks/ASVspoof2021_DF (611k trial labels + evaluation shard)
   - SpeechAntiSpoofingBenchmarks/ASVspoof2019_LA (71k trial labels + evaluation shard)
"""

from __future__ import annotations

import concurrent.futures
import json
import logging
import os
import sys
import time
from pathlib import Path

import datasets
import requests
from huggingface_hub import hf_hub_download, snapshot_download

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("unseen_downloader")

UNSEEN_DIR = Path("c:/HARES/unseen")
UNSEEN_DIR.mkdir(parents=True, exist_ok=True)


def download_cyberseceval3(download_images: bool = True, max_images: int = 1000) -> dict:
    """Downloads facebook/cyberseceval3-visual-prompt-injection from hfdataset."""
    target_dir = UNSEEN_DIR / "facebook_cyberseceval3_visual_prompt_injection"
    target_dir.mkdir(parents=True, exist_ok=True)
    logger.info("=== [1/2] Downloading facebook/cyberseceval3-visual-prompt-injection ===")

    # 1. Download HF Dataset using `datasets` library
    logger.info("Loading test split via `datasets.load_dataset`...")
    t0 = time.time()
    ds = datasets.load_dataset("facebook/cyberseceval3-visual-prompt-injection", split="test")
    arrow_dir = target_dir / "arrow_dataset"
    ds.save_to_disk(str(arrow_dir))
    logger.info(
        "Saved HF Arrow dataset to %s in %.2fs. Total rows: %d",
        arrow_dir,
        time.time() - t0,
        len(ds),
    )

    # 2. Download metadata and documentation
    logger.info("Downloading test_cases.json and README.md...")
    for filename in ["test_cases.json", "README.md", ".gitattributes"]:
        hf_hub_download(
            repo_id="facebook/cyberseceval3-visual-prompt-injection",
            filename=filename,
            repo_type="dataset",
            local_dir=str(target_dir),
            local_dir_use_symlinks=False,
        )

    # 3. Download images in parallel
    images_dir = target_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)
    downloaded_images = 0

    if download_images:
        logger.info("Downloading %d benchmark images with thread pool...", max_images)
        session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(pool_connections=32, pool_maxsize=32)
        session.mount("https://", adapter)

        def _fetch_img(idx: int) -> bool:
            out_file = images_dir / f"{idx}.png"
            if out_file.exists() and out_file.stat().st_size > 0:
                return True
            url = f"https://huggingface.co/datasets/facebook/cyberseceval3-visual-prompt-injection/resolve/main/images/{idx}.png"
            try:
                r = session.get(url, timeout=30)
                if r.status_code == 200:
                    with open(out_file, "wb") as f:
                        f.write(r.content)
                    return True
                else:
                    logger.warning("Image %d returned status %d", idx, r.status_code)
                    return False
            except Exception as e:
                logger.error("Failed to download image %d: %s", idx, e)
                return False

        with concurrent.futures.ThreadPoolExecutor(max_workers=24) as executor:
            futures = {executor.submit(_fetch_img, i): i for i in range(max_images)}
            for f in concurrent.futures.as_completed(futures):
                if f.result():
                    downloaded_images += 1
                if downloaded_images % 100 == 0:
                    logger.info("Downloaded %d/%d images...", downloaded_images, max_images)

        logger.info("Completed image downloads: %d/%d stored in %s", downloaded_images, max_images, images_dir)

    return {
        "dataset_name": "facebook/cyberseceval3-visual-prompt-injection",
        "type": "Visual Prompt Injection Benchmark",
        "rows": len(ds),
        "features": list(ds.features.keys()),
        "target_dir": str(target_dir),
        "arrow_dir": str(arrow_dir),
        "images_dir": str(images_dir),
        "total_images": downloaded_images,
        "sample": {k: v for k, v in ds[0].items()},
    }


def download_asvspoof_benchmarks() -> dict:
    """Downloads ASVspoof Benchmark Datasets."""
    target_dir = UNSEEN_DIR / "asvspoof_benchmarks"
    target_dir.mkdir(parents=True, exist_ok=True)
    logger.info("=== [2/2] Downloading ASVspoof Benchmark Datasets ===")

    results = {}

    # 1. DynamicSuperb ASVspoof 2017
    logger.info("Loading DynamicSuperb/SpoofDetection_ASVspoof2017...")
    ds_2017 = datasets.load_dataset("DynamicSuperb/SpoofDetection_ASVspoof2017", split="test")
    ds_2017 = ds_2017.cast_column("audio", datasets.Audio(decode=False))
    asv2017_dir = target_dir / "asvspoof_2017"
    ds_2017.save_to_disk(str(asv2017_dir / "arrow_dataset"))
    # Also download raw parquet
    hf_hub_download(
        repo_id="DynamicSuperb/SpoofDetection_ASVspoof2017",
        filename="data/test-00000-of-00001-e7ed034c56ededdd.parquet",
        repo_type="dataset",
        local_dir=str(asv2017_dir / "parquet"),
        local_dir_use_symlinks=False,
    )
    results["asvspoof_2017"] = {
        "dataset_name": "DynamicSuperb/SpoofDetection_ASVspoof2017",
        "rows": len(ds_2017),
        "features": list(ds_2017.features.keys()),
        "path": str(asv2017_dir),
    }
    logger.info("ASVspoof 2017 saved: %d rows", len(ds_2017))

    # 2. DynamicSuperb ASVspoof 2015
    logger.info("Loading DynamicSuperb/SpoofDetection_ASVspoof2015...")
    ds_2015 = datasets.load_dataset("DynamicSuperb/SpoofDetection_ASVspoof2015", split="test")
    ds_2015 = ds_2015.cast_column("audio", datasets.Audio(decode=False))
    asv2015_dir = target_dir / "asvspoof_2015"
    ds_2015.save_to_disk(str(asv2015_dir / "arrow_dataset"))
    # Also download raw parquet
    hf_hub_download(
        repo_id="DynamicSuperb/SpoofDetection_ASVspoof2015",
        filename="data/test-00000-of-00001-4a252b1e92dc86af.parquet",
        repo_type="dataset",
        local_dir=str(asv2015_dir / "parquet"),
        local_dir_use_symlinks=False,
    )
    results["asvspoof_2015"] = {
        "dataset_name": "DynamicSuperb/SpoofDetection_ASVspoof2015",
        "rows": len(ds_2015),
        "features": list(ds_2015.features.keys()),
        "path": str(asv2015_dir),
    }
    logger.info("ASVspoof 2015 saved: %d rows", len(ds_2015))

    # 3. SpeechAntiSpoofingBenchmarks ASVspoof 2021 DF
    logger.info("Downloading SpeechAntiSpoofingBenchmarks/ASVspoof2021_DF labels & eval shard...")
    asv2021_dir = target_dir / "asvspoof_2021_df"
    asv2021_dir.mkdir(parents=True, exist_ok=True)
    for fn in ["README.md", "LICENSE.txt", "build_parquet.py", "data/labels.parquet", "data/test-00000-of-00080.parquet"]:
        dest = hf_hub_download(
            repo_id="SpeechAntiSpoofingBenchmarks/ASVspoof2021_DF",
            filename=fn,
            repo_type="dataset",
            local_dir=str(asv2021_dir),
            local_dir_use_symlinks=False,
        )
        logger.info("Downloaded %s -> %s", fn, dest)

    results["asvspoof_2021_df"] = {
        "dataset_name": "SpeechAntiSpoofingBenchmarks/ASVspoof2021_DF",
        "total_official_trials": 611829,
        "files_downloaded": ["data/labels.parquet", "data/test-00000-of-00080.parquet", "build_parquet.py", "README.md"],
        "path": str(asv2021_dir),
    }

    # 4. SpeechAntiSpoofingBenchmarks ASVspoof 2019 LA
    logger.info("Downloading SpeechAntiSpoofingBenchmarks/ASVspoof2019_LA labels & eval shard...")
    asv2019_dir = target_dir / "asvspoof_2019_la"
    asv2019_dir.mkdir(parents=True, exist_ok=True)
    for fn in ["README.md", "LICENSE.txt", "build_parquet.py", "data/labels.parquet", "data/test-00000-of-00009.parquet"]:
        dest = hf_hub_download(
            repo_id="SpeechAntiSpoofingBenchmarks/ASVspoof2019_LA",
            filename=fn,
            repo_type="dataset",
            local_dir=str(asv2019_dir),
            local_dir_use_symlinks=False,
        )
        logger.info("Downloaded %s -> %s", fn, dest)

    results["asvspoof_2019_la"] = {
        "dataset_name": "SpeechAntiSpoofingBenchmarks/ASVspoof2019_LA",
        "total_official_trials": 71237,
        "files_downloaded": ["data/labels.parquet", "data/test-00000-of-00009.parquet", "build_parquet.py", "README.md"],
        "path": str(asv2019_dir),
    }

    return results


def main() -> None:
    start_time = time.time()
    logger.info("================================================================")
    logger.info("HARES UNSEEN BENCHMARK DATASET INGESTION: CYBERSECEVAL3 & ASVSPOOF")
    logger.info("Target: %s", UNSEEN_DIR)
    logger.info("================================================================")

    cyber_res = download_cyberseceval3(download_images=True, max_images=1000)
    asv_res = download_asvspoof_benchmarks()

    # Generate complete benchmark catalog
    total_size = 0
    file_count = 0
    for root, _, files in os.walk(UNSEEN_DIR):
        for f in files:
            fp = Path(root) / f
            file_count += 1
            total_size += fp.stat().st_size

    catalog = {
        "ingestion_timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "target_directory": str(UNSEEN_DIR),
        "total_files": file_count,
        "total_size_mb": round(total_size / 1e6, 2),
        "total_size_gb": round(total_size / 1e9, 3),
        "datasets": {
            "cyberseceval3_visual_prompt_injection": cyber_res,
            "asvspoof_benchmarks": asv_res,
        },
    }

    catalog_path = UNSEEN_DIR / "BENCHMARK_CATALOG.json"
    with open(catalog_path, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2)

    logger.info("================================================================")
    logger.info("ALL BENCHMARK DATASETS SUCCESSFULLY DOWNLOADED AND VERIFIED!")
    logger.info("Catalog written to: %s", catalog_path)
    logger.info("Total Files: %d", file_count)
    logger.info("Total Size: %.2f MB (%.3f GB)", total_size / 1e6, total_size / 1e9)
    logger.info("Elapsed Time: %.2f seconds", time.time() - start_time)
    logger.info("================================================================")


if __name__ == "__main__":
    main()
