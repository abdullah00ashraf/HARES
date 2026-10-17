"""
Dedicated downloader for ASVspoof Benchmark Datasets into c:\\HARES\\unseen\\asvspoof_benchmarks
"""

from __future__ import annotations

import logging
import sys
import time
from pathlib import Path
import datasets
from huggingface_hub import hf_hub_download

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("asvspoof_downloader")

TARGET_DIR = Path("c:/HARES/unseen/asvspoof_benchmarks")
TARGET_DIR.mkdir(parents=True, exist_ok=True)

def main() -> None:
    t0 = time.time()
    logger.info("=== Starting ASVspoof Benchmark Ingestion into %s ===", TARGET_DIR)

    # 1. DynamicSuperb ASVspoof 2017
    asv2017_dir = TARGET_DIR / "asvspoof_2017"
    asv2017_dir.mkdir(parents=True, exist_ok=True)
    logger.info("1. Downloading DynamicSuperb/SpoofDetection_ASVspoof2017...")
    ds_2017 = datasets.load_dataset("DynamicSuperb/SpoofDetection_ASVspoof2017", split="test")
    ds_2017 = ds_2017.cast_column("audio", datasets.Audio(decode=False))
    ds_2017.save_to_disk(str(asv2017_dir / "arrow_dataset"))
    hf_hub_download(
        repo_id="DynamicSuperb/SpoofDetection_ASVspoof2017",
        filename="data/test-00000-of-00001-e7ed034c56ededdd.parquet",
        repo_type="dataset",
        local_dir=str(asv2017_dir / "parquet"),
        local_dir_use_symlinks=False,
    )
    logger.info("ASVspoof 2017 successfully downloaded (%d rows).", len(ds_2017))

    # 2. DynamicSuperb ASVspoof 2015
    asv2015_dir = TARGET_DIR / "asvspoof_2015"
    asv2015_dir.mkdir(parents=True, exist_ok=True)
    logger.info("2. Downloading DynamicSuperb/SpoofDetection_ASVspoof2015...")
    ds_2015 = datasets.load_dataset("DynamicSuperb/SpoofDetection_ASVspoof2015", split="test")
    ds_2015 = ds_2015.cast_column("audio", datasets.Audio(decode=False))
    ds_2015.save_to_disk(str(asv2015_dir / "arrow_dataset"))
    hf_hub_download(
        repo_id="DynamicSuperb/SpoofDetection_ASVspoof2015",
        filename="data/test-00000-of-00001-4a252b1e92dc86af.parquet",
        repo_type="dataset",
        local_dir=str(asv2015_dir / "parquet"),
        local_dir_use_symlinks=False,
    )
    logger.info("ASVspoof 2015 successfully downloaded (%d rows).", len(ds_2015))

    # 3. SpeechAntiSpoofingBenchmarks ASVspoof 2021 DF
    asv2021_dir = TARGET_DIR / "asvspoof_2021_df"
    asv2021_dir.mkdir(parents=True, exist_ok=True)
    logger.info("3. Downloading SpeechAntiSpoofingBenchmarks/ASVspoof2021_DF labels & eval shard...")
    for fn in ["README.md", "LICENSE.txt", "build_parquet.py", "data/labels.parquet", "data/test-00000-of-00080.parquet"]:
        dest = hf_hub_download(
            repo_id="SpeechAntiSpoofingBenchmarks/ASVspoof2021_DF",
            filename=fn,
            repo_type="dataset",
            local_dir=str(asv2021_dir),
            local_dir_use_symlinks=False,
        )
        logger.info("Downloaded ASVspoof 2021 DF: %s", fn)

    # 4. SpeechAntiSpoofingBenchmarks ASVspoof 2019 LA
    asv2019_dir = TARGET_DIR / "asvspoof_2019_la"
    asv2019_dir.mkdir(parents=True, exist_ok=True)
    logger.info("4. Downloading SpeechAntiSpoofingBenchmarks/ASVspoof2019_LA labels & eval shard...")
    for fn in ["README.md", "LICENSE.txt", "build_parquet.py", "data/labels.parquet", "data/test-00000-of-00009.parquet"]:
        dest = hf_hub_download(
            repo_id="SpeechAntiSpoofingBenchmarks/ASVspoof2019_LA",
            filename=fn,
            repo_type="dataset",
            local_dir=str(asv2019_dir),
            local_dir_use_symlinks=False,
        )
        logger.info("Downloaded ASVspoof 2019 LA: %s", fn)

    logger.info("=== ASVspoof Benchmarks Ingestion Complete in %.2fs ===", time.time() - t0)

if __name__ == "__main__":
    main()
