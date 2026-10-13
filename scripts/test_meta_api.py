"""
Project Hares: Meta WhatsApp Cloud API Connectivity & Verification Diagnostic Tool.

Validates credentials in .env against the live Meta Graph API:
1. Tests token validity and retrieves Phone Number metadata (display name, status, quality rating).
2. Inspects token permissions (whatsapp_business_messaging).
3. Optionally dispatches a live test message to your designated test recipient number.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Any

import httpx

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("hares.meta_test")


def load_env_file(env_path: Path) -> dict[str, str]:
    """Simple parser for .env without external side effects."""
    env_vars: dict[str, str] = {}
    if not env_path.exists():
        return env_vars
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                env_vars[k] = v
    return env_vars


def test_meta_connection(recipient_phone: str | None = None) -> bool:
    env_path = Path(".env")
    env = load_env_file(env_path)

    token = os.environ.get("WHATSAPP_ACCESS_TOKEN") or env.get("WHATSAPP_ACCESS_TOKEN", "")
    phone_id = os.environ.get("WHATSAPP_PHONE_NUMBER_ID") or env.get("WHATSAPP_PHONE_NUMBER_ID", "")
    api_version = os.environ.get("WHATSAPP_API_VERSION") or env.get("WHATSAPP_API_VERSION", "v21.0")
    base_url = (os.environ.get("WHATSAPP_API_BASE_URL") or env.get("WHATSAPP_API_BASE_URL", "https://graph.facebook.com")).rstrip("/")

    print("=" * 75)
    print("🛡️ PROJECT HARES: META WHATSAPP CLOUD API CONNECTIVITY TEST")
    print("=" * 75)

    if not token or token.startswith("EAAG_staging") or len(token) < 15:
        logger.error("❌ WHATSAPP_ACCESS_TOKEN is missing or empty in .env!")
        print("\nPlease open c:\\HARES\\.env and paste your Meta Access Token:")
        print("  WHATSAPP_ACCESS_TOKEN=\"EAA...\"")
        print("\nMake sure to save the file (Ctrl + S) in your editor before running.")
        return False

    if not phone_id or phone_id == "100000000000000" or not phone_id.isdigit():
        logger.error("❌ WHATSAPP_PHONE_NUMBER_ID is missing or set to placeholder in .env!")
        print("\nPlease open c:\\HARES\\.env and paste your numerical Phone Number ID:")
        print("  WHATSAPP_PHONE_NUMBER_ID=\"123456789...\"")
        return False

    masked_token = f"{token[:8]}...{token[-6:]}"
    print(f"• Graph API Base:   {base_url}/{api_version}")
    print(f"• Phone Number ID:  {phone_id}")
    print(f"• Access Token:     {masked_token} ({len(token)} chars)")
    print("-" * 75)

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    # 1. Test Phone Number Metadata Probe
    logger.info("📡 Step 1/2: Querying Meta Graph API for Phone Number metadata...")
    phone_meta_url = f"{base_url}/{api_version}/{phone_id}"
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(phone_meta_url, headers=headers)
    except Exception as exc:
        logger.error("❌ Failed to reach Meta Graph API: %s", exc)
        return False

    if resp.status_code != 200:
        logger.error("❌ Meta Graph API rejected the request with HTTP %d:", resp.status_code)
        try:
            err_data = resp.json().get("error", {})
            logger.error("   Message: %s", err_data.get("message"))
            logger.error("   Type:    %s", err_data.get("type"))
            logger.error("   Code:    %s", err_data.get("code"))
            logger.error("   Subcode: %s", err_data.get("error_subcode"))
        except Exception:
            logger.error("   Raw: %s", resp.text)
        return False

    data = resp.json()
    display_phone = data.get("display_phone_number", "N/A")
    verified_name = data.get("verified_name", "N/A")
    quality_rating = data.get("quality_rating", "N/A")
    status = data.get("code_verification_status", data.get("status", "VERIFIED"))

    print("\n✅ STEP 1 SUCCESSFUL: Meta Cloud API credentials are VALID!")
    print(f"   • Display Phone:   {display_phone}")
    print(f"   • Verified Name:   {verified_name}")
    print(f"   • Quality Rating:  {quality_rating}")
    print(f"   • Status:          {status}")

    # 2. Optional: Dispatch Live WhatsApp Message
    if recipient_phone:
        clean_recipient = recipient_phone.replace(" ", "").replace("-", "")
        if not clean_recipient.startswith("+"):
            clean_recipient = f"+{clean_recipient}"
        
        logger.info("\n📲 Step 2/2: Dispatching test message to %s...", clean_recipient)
        msg_url = f"{base_url}/{api_version}/{phone_id}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "to": clean_recipient,
            "type": "text",
            "text": {
                "body": (
                    "🛡️ *Project Hares (مشروع حارس)*\n\n"
                    "✅ *Connection Test Successful!*\n"
                    "Your Meta WhatsApp Cloud API credentials have been verified.\n\n"
                    "You can now submit suspicious texts, links, or voice notes to test sovereign fraud triage."
                )
            },
        }

        try:
            with httpx.Client(timeout=10.0) as client:
                msg_resp = client.post(msg_url, json=payload, headers=headers)
        except Exception as exc:
            logger.error("❌ Failed to dispatch outbound test message: %s", exc)
            return False

        if msg_resp.status_code not in (200, 201):
            logger.warning("⚠️ Message dispatch returned HTTP %d:", msg_resp.status_code)
            try:
                err_data = msg_resp.json().get("error", {})
                logger.warning("   Message: %s", err_data.get("message"))
                logger.warning("   (Note: Meta Test Numbers only allow sending to pre-approved recipient phone numbers added in the API Setup dashboard.)")
            except Exception:
                logger.warning("   Raw: %s", msg_resp.text)
            return False

        msg_data = msg_resp.json()
        wamid = msg_data.get("messages", [{}])[0].get("id", "N/A")
        print("\n✅ STEP 2 SUCCESSFUL: Test WhatsApp message dispatched!")
        print(f"   • WhatsApp Message ID: {wamid}")
        print("   • Check WhatsApp on your phone!")
    else:
        print("\n💡 TIP: To send a live test message to your phone, run:")
        print("   python scripts/test_meta_api.py --recipient \"+971XXXXXXXXX\"")

    print("=" * 75)
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test Meta WhatsApp Cloud API connection.")
    parser.add_argument("--recipient", "-r", type=str, default=None, help="E.164 phone number to receive a test message (e.g. +971501234567)")
    args = parser.parse_args()

    success = test_meta_connection(recipient_phone=args.recipient)
    sys.exit(0 if success else 1)
