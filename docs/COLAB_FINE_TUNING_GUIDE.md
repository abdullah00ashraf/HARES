# Project Hares (مشروع حارس) — Google Colab Model Fine-Tuning & Training Guide

**Document Version:** 1.0.0-production-guide  
**Classification:** MLOps Operator Manual & Cloud-to-Sovereign Deployment Protocol  
**Compliance Context:** NFR-1.1 (100% Local Inference within UAE), FR-2.4 (Dialectal Smishing SLM), FR-1.1 to FR-1.4 (Whisper Dual-Head Deepfake Classifier & Conformal Calibration), FR-3.3 (Sub-5.0s SLA)

---

## 1. Architectural Overview & Compute Topology

Project Hares trains its sovereign AI models using cloud GPU acceleration (Google Colab Free Tier NVIDIA T4 16GB or Colab Pro A100/L4) and exports the resulting quantized weights and calibration profiles back into local sovereign UAE infrastructure (`hares-slm` and `hares-worker-media`).

```mermaid
graph TD
    subgraph Local_Machine [Developer Workstation - c:/HARES]
        Packager[python scripts/package_colab_data.py]
        Packager --> LocalArchives[colab_packages/<br/>- uae_smishing_100k.jsonl.gz<br/>- uae_smishing_25k_core.jsonl.gz<br/>- audio_metadata.jsonl]
    end

    subgraph Google_Drive [Google Drive Storage: /MyDrive/hares_mlops/]
        LocalArchives --> DriveMount[Drive Staging Layer]
        DriveMount --> CheckpointDir[checkpoints/slm/ (Streaming save_steps=500)]
        DriveMount --> AudioModelDir[audio_models/]
        DriveMount --> ExportModelDir[exported_models/]
    end

    subgraph Colab_Runtimes [Google Colab GPU Sessions]
        DriveMount --> NB1[notebooks/colab_slm_qlora_tuning.ipynb<br/>Track 1: QLoRA SFT on Qwen-2.5-3B]
        DriveMount --> NB2[notebooks/colab_whisper_dual_head_training.ipynb<br/>Track 2: 2-Phase Whisper Head & Conformal]
        NB1 --> ExportModelDir
        NB2 --> AudioModelDir
    end

    subgraph Sovereign_Deployment [Local Sovereign UAE Containers - NFR-1.1]
        ExportModelDir --> SLM_Container[hares-slm Container (vLLM AWQ / llama.cpp GGUF)]
        AudioModelDir --> Media_Worker[hares-worker-media Container (PyTorch Whisper Head)]
        Verifier[python scripts/verify_colab_artifacts.py]
        SLM_Container & Media_Worker --> Verifier
    end
```

---

## 2. Prerequisites & Cloud Setup

1. **Google Account & Drive Space:** Ensure at least **15 GB** of available Google Drive space for staging datasets and model weights.
2. **Google Colab Environment:** Standard free-tier Google Colab (with GPU accelerator enabled) or Colab Pro.
3. **Local Python Environment:** Python 3.11+ / 3.12+ with project dependencies installed (`pip install .` or `pip install -e .`).

---

## 3. Step 1: Package Datasets Locally

Run the packaging script to generate compressed archives and the 25k curriculum subset:

```powershell
python scripts/package_colab_data.py --output-dir colab_packages
```

This generates:
- `colab_packages/uae_smishing_100k.jsonl.gz` (~18 MB compressed)
- `colab_packages/uae_smishing_25k_core.jsonl.gz` (~4.5 MB compressed, balanced 25k curriculum core)
- `colab_packages/audio_metadata.jsonl`
- `colab_packages/audio_corpus_manifest.json`
- `colab_packages/colab_package_manifest.json` (SHA-256 checksums)

### Upload to Google Drive:
In Google Drive, create a folder named **`hares_mlops`** in `My Drive` (`MyDrive/hares_mlops/`) and copy the contents of `colab_packages/` into it:
- `MyDrive/hares_mlops/uae_smishing_100k.jsonl.gz`
- `MyDrive/hares_mlops/uae_smishing_25k_core.jsonl.gz`
- `MyDrive/hares_mlops/audio_metadata.jsonl`

---

## 4. Step 2: Track 1 — SLM Instruction Fine-Tuning (`colab_slm_qlora_tuning.ipynb`)

1. Open [Google Colab](https://colab.research.google.com/) and upload `notebooks/colab_slm_qlora_tuning.ipynb`.
2. Navigate to **Runtime > Change runtime type**, select **T4 GPU**, and click Save.
3. **Hardware Guard (Automatic):** The notebook automatically detects if native BF16 is supported:
   - On NVIDIA T4 (Turing CC 7.5), it forces `torch.float16` to prevent software emulation slowdowns.
4. **Choose Dataset Staging:**
   - **Recommended Initial Run:** Start with `uae_smishing_25k_core.jsonl.gz` (~1.2 hours on T4) to verify loss convergence and JSON compliance.
   - **Full Run:** Set `DATASET_ARCHIVE = f"{DRIVE_DIR}/uae_smishing_100k.jsonl.gz"` (~4.5 hours on T4).
5. **Checkpoint Streaming:**
   - The training arguments stream checkpoints directly to `MyDrive/hares_mlops/checkpoints/slm/` every 500 steps (`save_steps=500, save_total_limit=3`).
   - If Google Colab disconnects, re-running the cell automatically invokes `trainer.train(resume_from_checkpoint=...)` to resume from the last saved step.
6. **Low-RAM LoRA Merge:**
   - Step 7 scrubs training variables (`del model, trainer; gc.collect(); torch.cuda.empty_cache()`) and merges weights with `low_cpu_mem_usage=True` to prevent Colab 12.7 GB host RAM kernel crashes.
7. **Dual Quantization Export:**
   - **AWQ 4-bit:** Saved to `MyDrive/hares_mlops/exported_models/hares_qwen2.5_3b_awq/` (for high-throughput `vLLM` serving).
   - **GGUF Q4_K_M:** Saved to `MyDrive/hares_mlops/exported_models/hares_qwen2.5_3b_gguf/` (for lightweight `llama.cpp` serving).

---

## 5. Step 3: Track 2 — Whisper Dual-Head Spoof Classifier (`colab_whisper_dual_head_training.ipynb`)

1. Upload `notebooks/colab_whisper_dual_head_training.ipynb` to Google Colab with GPU runtime enabled.
2. **Phase 1 (One-Time Feature Extraction):**
   - Forwards audio files once through the frozen `openai/whisper-small` encoder and saves the $(20000, 768)$ feature tensor (~61 MB) directly to `MyDrive/hares_mlops/audio_models/whisper_pooled_features_20k.pt`.
   - If this file already exists in Drive, the notebook skips extraction automatically.
3. **Phase 2 (Ultra-Fast Head Training):**
   - Trains `WhisperDeepfakeMLPHead` ($768 \to 256 \to 64 \to 1$) on the pre-extracted tensor matrix.
   - 10 epochs complete in **less than 60 seconds** on a T4 GPU.
4. **Phase 3 (Non-Parametric Conformal Calibration):**
   - Evaluates empirical non-conformity scores on $n \ge 3{,}000$ authentic UAE clips.
   - Computes $(1 - \alpha)$ quantiles at $\alpha = 0.001$, mathematically bounding False Positive Rate $\le 0.1\%$ at 95% confidence (NFR-3.1).
   - Generates `MyDrive/hares_mlops/audio_models/calibration_scores_n3000.json`.
5. **Exported Artifacts:**
   - PyTorch Head State Dict: `MyDrive/hares_mlops/audio_models/whisper_deepfake_head_calibrated.pt`
   - Conformal Profile: `MyDrive/hares_mlops/audio_models/calibration_scores_n3000.json`

---

## 6. Step 4: Download Artifacts to Local Sovereign Repository

Once the Colab sessions finish, download the exported artifacts from Google Drive to your local repository directory structure:

| Colab Google Drive Path | Destination in Local Repository | Purpose |
| :--- | :--- | :--- |
| `audio_models/whisper_deepfake_head_calibrated.pt` | `opensource/models/whisper_dual_head/head_weights.pt` | Loaded by `src/hares/ai/audio_pipeline.py` with `weights_only=True` |
| `audio_models/calibration_scores_n3000.json` | `opensource/datasets/uae_regional_opus_suite/calibration_scores_n3000.json` | Loaded by `src/hares/ai/conformal.py` |
| `exported_models/hares_qwen2.5_3b_awq/` | `models/slm/qwen2.5-3b-awq/` | Production vLLM model container (`hares-slm`) |
| `exported_models/hares_qwen2.5_3b_gguf/` | `models/slm/qwen2.5-3b-gguf/` | Edge llama.cpp model |

---

## 7. Step 5: Local Verification & Integration Testing

Run the automated verification harness to certify model weights and calibration quantiles:

```powershell
python scripts/verify_colab_artifacts.py --weights-path opensource/models/whisper_dual_head/head_weights.pt --calib-path opensource/datasets/uae_regional_opus_suite/calibration_scores_n3000.json
```

Run the hermetic test suite:

```powershell
pytest tests/ -v
```

All 89+ unit and integration tests must pass with 100% compliance, certifying the system as production-ready.
