# Project Hares Audio Track 2 Training Run Report

- **Run Date:** 2026-10-11 17:10:10 UTC
- **Accelerator:** 2x NVIDIA Tesla T4
- **Model:** WhisperDeepfakeMLPHead (768 -> 256 -> 64 -> 1)
- **Dataset:** 20,000 WhatsApp 16kHz Opus Audio Files (50% Genuine / 50% Synthetic)
- **Best Validation Loss:** 0.0000 (Epoch 10)
- **Conformal Thresholds:**
  - **Tau Red (Synthetic Spoof):** 0.0001 (FPR <= 0.1%)
  - **Tau Green (Bonafide Verified):** 0.0000

## Epoch Training History
| Epoch | Train Loss | Val Loss | Val Acc | FPR | FNR |
| :---: | :---: | :---: | :---: | :---: | :---: |
| 1 | 0.0519 | 0.0001 | 100.00% | 0.00% | 0.00% |
| 2 | 0.0002 | 0.0000 | 100.00% | 0.00% | 0.00% |
| 3 | 0.0001 | 0.0000 | 100.00% | 0.00% | 0.00% |
| 4 | 0.0000 | 0.0000 | 100.00% | 0.00% | 0.00% |
| 5 | 0.0000 | 0.0000 | 100.00% | 0.00% | 0.00% |
| 6 | 0.0000 | 0.0000 | 100.00% | 0.00% | 0.00% |
| 7 | 0.0000 | 0.0000 | 100.00% | 0.00% | 0.00% |
| 8 | 0.0000 | 0.0000 | 100.00% | 0.00% | 0.00% |
| 9 | 0.0000 | 0.0000 | 100.00% | 0.00% | 0.00% |
| 10 | 0.0000 | 0.0000 | 100.00% | 0.00% | 0.00% |
