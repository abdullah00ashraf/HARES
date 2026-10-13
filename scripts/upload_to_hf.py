"""
Project Hares: Hugging Face Model Hub & Space Deployment Automation.
Uploads model SafeTensors shards to abdullahashraf122/hares-qwen2.5-3b.
"""

import os
import sys
from pathlib import Path
from huggingface_hub import HfApi

def upload_model():
    api = HfApi()
    repo_id = "abdullahashraf122/hares-qwen2.5-3b"
    model_dir = Path("models/qwen/hares_qwen2.5_3b_merged_fp16")
    
    if not model_dir.exists():
        print(f"Error: {model_dir} does not exist!")
        sys.exit(1)

    print(f"Uploading model shards from {model_dir} to {repo_id}...")
    api.upload_folder(
        folder_path=str(model_dir),
        repo_id=repo_id,
        repo_type="model",
        commit_message="feat(model): upload Qwen2.5-3B fine-tuned SafeTensors shards and tokenizer",
    )
    print(f"✅ Model weights uploaded successfully to https://huggingface.co/{repo_id}")

if __name__ == "__main__":
    upload_model()
