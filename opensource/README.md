# Project Hares: Sovereign Open-Source Asset Registry

**Registry Version:** 1.0.0-phase5-complete  
**Root Path:** `c:/HARES/opensource/`  
**Compliance Context:** NFR-1.1 (UAE Sovereign On-Premise Execution, Zero External APIs), FR-3.3 (Sub-5.0s SLA), FR-1.x (Unified Whisper Dual-Head Speech & Spoof Triage), FR-2.x (Dialectal Fraud & Deterministic Engines)

---

## 1. Directory Structure & Organization

```
c:/HARES/opensource/
├── relevants.md                          # Technical procurement evaluation matrix
├── README.md                             # Comprehensive asset documentation (this file)
├── CATALOG.json                          # Machine-readable registry of all assets
├── repositories/                         # Synchronized upstream git repositories
│   ├── audio_deepfake/
│   │   ├── deepfake-whisper-features/    # piotrkawa Unified Whisper acoustic head (Interspeech 2023)
│   │   ├── aasist/                       # clovaai spectro-temporal graph attention networks
│   │   └── asvspoof2021_air/             # Acoustic impairment robustness & Opus degradation simulator
│   ├── asr/
│   │   └── faster-whisper/               # SYSTRAN CTranslate2 INT8 Whisper inference engine
│   ├── nlp_arabic/
│   │   ├── marbert/                      # UBC-NLP dialectal Arabic transformer
│   │   ├── arabert/                      # AUB MIND Lab MSA BERT & Farasa preprocessor
│   │   └── camel_tools/                  # NYU Abu Dhabi morphological & dialect identification toolkit
│   ├── structured_generation/
│   │   └── outlines/                     # outlines-dev FSM logit masking for guided JSON decoding
│   └── conformal/
│       ├── nonconformist/                # donlnz distribution-free split-conformal framework
│       ├── conformal_classification/     # aangelopoulos conformal prediction set predictors
│       └── MAPIE/                        # Scikit-learn contrib model-agnostic prediction interval estimator
├── datasets/                             # Reference evaluation datasets and calibration distributions
│   ├── uae_regional_opus_suite/          # 3,000 empirical calibration scores from genuine UAE voice notes
│   ├── synthetic_voice_eval/             # Benchmark taxonomy across Diffusion, Codec, VC, and Commercial engines
│   ├── localized_fraud_corpus/           # 1,000 scam lures & 1,000 verified municipal alert templates
│   ├── adversarial_injection_suite/      # 500 prompt injection test payloads
│   └── official_domains_allowlist/       # Curated TDRA/DESC verified official registrable domains
└── models/                               # Local architectures, state dicts, and token constraints
    ├── whisper_dual_head/                # PyTorch MLP head definition & config (piotrkawa)
    ├── slm_guided/                       # Strict JSON schemas & Outlines regex grammars
    └── conformal_profiles/               # Serialized empirical non-conformity calibration profiles
```

---

## 2. Upstream Repositories Inventory

| Repository | Category | Architecture & Role | Local Directory |
| :--- | :--- | :--- | :--- |
| **[piotrkawa/deepfake-whisper-features](https://github.com/piotrkawa/deepfake-whisper-features)** | Audio Deepfake | Unified Whisper single-forward acoustic representation extractor + MLP spoof head. | `repositories/audio_deepfake/deepfake-whisper-features` |
| **[clovaai/aasist](https://github.com/clovaai/aasist)** | Audio Deepfake | SOTA spectral/temporal graph attention networks on raw waveforms. | `repositories/audio_deepfake/aasist` |
| **[yzyouzhang/ASVspoof2021_AIR](https://github.com/yzyouzhang/ASVspoof2021_AIR)** | Audio Deepfake | Channel-robust acoustic impairment training to counter lossy Opus compression. | `repositories/audio_deepfake/asvspoof2021_air` |
| **[SYSTRAN/faster-whisper](https://github.com/SYSTRAN/faster-whisper)** | Local ASR | High-throughput CTranslate2 INT8 Whisper serving (sub-280ms latency for 30s audio). | `repositories/asr/faster-whisper` |
| **[UBC-NLP/marbert](https://github.com/UBC-NLP/marbert)** | Dialectal NLP | Pretrained on 1B dialectal Arabic tweets; excels on informal Gulf Arabic smishing. | `repositories/nlp_arabic/marbert` |
| **[aub-mind/arabert](https://github.com/aub-mind/arabert)** | Dialectal NLP | MSA BERT and Farasa segmentation for formal UAE authority impersonation lures. | `repositories/nlp_arabic/arabert` |
| **[CAMeL-Lab/camel_tools](https://github.com/CAMeL-Lab/camel_tools)** | Dialectal NLP | NYU Abu Dhabi morphological analysis and dialect identification (DID). | `repositories/nlp_arabic/camel_tools` |
| **[outlines-dev/outlines](https://github.com/outlines-dev/outlines)** | Structured Decoding | FSM logit masking guaranteeing 100% prompt injection containment. | `repositories/structured_generation/outlines` |
| **[donlnz/nonconformist](https://github.com/donlnz/nonconformist)** | Conformal Prediction | Python distribution-free conformal prediction framework. | `repositories/conformal/nonconformist` |
| **[aangelopoulos/conformal_classification](https://github.com/aangelopoulos/conformal_classification)** | Conformal Prediction | PyTorch classification set prediction with formal coverage guarantees. | `repositories/conformal/conformal_classification` |
| **[scikit-learn-contrib/MAPIE](https://github.com/scikit-learn-contrib/MAPIE)** | Conformal Prediction | Model-agnostic prediction interval and risk control estimators. | `repositories/conformal/MAPIE` |

---

## 3. Systematic Verification & Integrity

All repositories were cloned using shallow mirrors (`--depth 1`) to optimize storage efficiency while retaining the complete source code, configuration files, and evaluation scripts. All benchmark suites and model configurations are locally inspectable and execute within hermetic, air-gapped test environments.
