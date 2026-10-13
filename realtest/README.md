# Project Hares — Real-World Multi-Modal Test Suite (`c:\HARES\realtest`)

> [!IMPORTANT]
> **Purpose:** This directory contains real-world, production-representative test assets specifically curated to test every single aspect of the **Project Hares** sovereign citizen triage portal and backend API.

---

## 📁 Directory Structure & Test Assets

```
c:\HARES\realtest\
├── prompts/                      # Real-world text & SMS messages (Arabic, English, Arabizi)
│   ├── 01_fake_police_fine_urgent.txt       (🔴 RED: Urgent fine & vehicle impound threat)
│   ├── 02_enbd_kyc_suspension_bilingual.txt (🔴 RED: Fake bank security restriction & OTP request)
│   ├── 03_emirates_post_unpaid_customs.txt  (🔴 RED: Parcel delivery fee smishing)
│   ├── 04_official_dewa_bill_safe.txt       (🟢 GREEN: Legitimate DEWA billing notification)
│   ├── 05_official_dubai_police_901_safe.txt(🟢 GREEN: Official Dubai Police e-Crime advisory)
│   ├── 06_salik_homograph_spoof.txt         (🔴 RED: Salik recharge link with Unicode accent)
│   ├── 07_adversarial_prompt_injection.txt  (🔴 RED: ChatML <|im_start|> jailbreak attempt)
│   ├── 08_arabizi_lottery_prize_scam.txt    (🔴 RED: Chat Arabic / Arabizi 500k AED prize lure)
│   ├── 09_whatsapp_crypto_investment.txt    (🔴 RED: VIP Telegram desk & foreign phone)
│   └── 10_casual_benign_conversation_safe.txt (🟢 GREEN: Harmless social greeting)
│
├── urls/                         # Standalone URL test catalogs
│   ├── 01_official_verified_urls.txt        (🟢 GREEN: dewa.gov.ae, ecrime.ae, rta.ae, etc.)
│   ├── 02_homograph_spoofed_urls.txt        (🔴 RED: dеwa.gov.ae [Cyrillic], salík.ae, etc.)
│   └── 03_phishing_malicious_urls.txt       (🔴 RED: police-fine.cc, adcb-banking-auth.org)
│
├── audio/                        # Real WhatsApp Opus (.ogg) audio recordings
│   ├── 01_genuine_emirati_arabic_male.ogg   (🟢 GREEN: Authentic human male voice note)
│   ├── 02_genuine_emirati_arabic_female.ogg (🟢 GREEN: Authentic human female voice note)
│   ├── 03_deepfake_f5tts_urgent_police.ogg  (🔴 RED: Flow-Matching AI clone impersonating police)
│   ├── 04_deepfake_diffusion_bank_kyc.ogg   (🔴 RED: Diffusion neural TTS requesting KYC)
│   └── 05_deepfake_cosyvoice_lottery_lure.ogg(🔴 RED: Neural TTS voice claiming cash prize)
│
├── images/                       # Realistic screenshot images for Sovereign OCR testing
│   ├── screenshot_01_fake_police_fine_sms.png      (🔴 RED: SMS ticket with police-fine.cc)
│   ├── screenshot_02_emirates_post_unpaid_fee.png   (🔴 RED: Parcel fee with tracking link)
│   ├── screenshot_03_enbd_urgent_kyc_freeze.png    (🔴 RED: Bank freeze alert with portal link)
│   ├── screenshot_04_official_dewa_bill_verified.png(🟢 GREEN: Official DEWA statement)
│   └── screenshot_05_whatsapp_voice_scam_chat.png  (🔴 RED: WhatsApp audio scam + crypto link)
│
├── test_manifest.json            # Machine-readable test definitions & expected outcomes
├── generate_assets.py            # Regenerates or expands the test asset catalog
├── run_realtest_suite.py         # Automated test runner executing against http://localhost:8000
└── REALTEST_EXECUTION_REPORT.md  # Detailed pass/fail audit report generated after execution
```

---

## 🚀 How to Test the Web Interface (`http://localhost:3000`)

Open your browser to: **`http://localhost:3000`**

### Test 1: Testing Text / SMS Triage
1. Click the **`💬 Text / SMS`** tab in the Citizen Portal.
2. Open any file in `realtest/prompts/` (e.g. `01_fake_police_fine_urgent.txt` or `04_official_dewa_bill_safe.txt`).
3. Copy and paste the text into the text area.
4. Click **`🔍 Analyze Threat`**.
5. Observe the tri-state verdict card:
   - For `01_fake_police_fine_urgent.txt`: Observe **🔴 High Risk / Suspicious** with Dubai Police e-Crime escalation links (`ecrime.ae` / `901`).
   - For `04_official_dewa_bill_safe.txt`: Observe **🟢 Safe / Verified** with official government badge.

### Test 2: Testing URL Domain & Homograph Detection
1. Click the **`🔗 Link / URL`** tab.
2. Test a legitimate URL from `realtest/urls/01_official_verified_urls.txt`: `https://www.dewa.gov.ae`.
   - Result: **🟢 Verified Official Entity**.
3. Test a homograph spoof from `realtest/urls/02_homograph_spoofed_urls.txt`: `http://dеwa.gov.ae/pay` (contains Cyrillic `е`).
   - Result: **🔴 High Risk Homograph Spoof** identifying `dewa.gov.ae` as target.

### Test 3: Testing Screenshot OCR Extraction
1. Click the **`🖼️ Screenshot / OCR`** tab.
2. Drag and drop any image from `realtest/images/` into the upload box (e.g. `screenshot_01_fake_police_fine_sms.png`).
3. The image preview displays immediately.
4. Click **`🔍 Analyze Threat`**.
5. The local sovereign OCR engine extracts the text and URL (`police-fine.cc`) and flags the threat!

### Test 4: Testing Audio Voice Notes & Deepfake Spoof Detection
1. Click the **`🎙️ Voice Note / Audio`** tab.
2. Choose **Upload File** and select `realtest/audio/03_deepfake_f5tts_urgent_police.ogg` or record via microphone.
3. Click **`🔍 Analyze Threat`**.
4. The sovereign audio pipeline performs ASR transcription and runs the AASIST acoustic deepfake classifier.

---

## ⚡ Automated Command-Line Execution

To run the entire test asset suite automatically and generate an execution report:

```powershell
python c:\HARES\realtest\run_realtest_suite.py
```

The script will query the local API and emit `c:\HARES\realtest\REALTEST_EXECUTION_REPORT.md`.
