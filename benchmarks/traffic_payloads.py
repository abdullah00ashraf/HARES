import hashlib
import hmac
import random
import time
from typing import Any

TEXT_LURES: list[str] = [
    # Arabic Phishing & Impersonation lures
    "شرطة دبي: إشعار بمخالفة مرورية غير مسددة. يرجى سداد المبلغ فوراً لتجنب حجز المركبة: https://ecr1me-pay.top",
    "بريد الإمارات: شحنتك رقم EP98234 معلقة في المستودع. يرجى دفع رسوم تأكيد العنوان (15 درهم) لاستلام الطرد: https://emiratespost-tracking.online",
    "المصرف المركزي: تم تجميد حسابك المصرفي مؤقتاً لعدم تحديث الهوية. يرجى إدخال رمز التحقق OTP وكلمة المرور فوراً لتفادي الإغلاق الدائم.",
    "هيئة كهرباء ومياه دبي: إنذار بقطع الخدمة خلال ساعتين لتراكم الفواتير. اضغط للتحقق والسداد: https://dewa-bill-settle.cc",
    "تحديث بطاقة الهوية الإماراتية: تم تعليق صلاحية بطاقتك. اضغط لتحديث البيانات خلال 24 ساعة لتفادي الغرامات المالية.",
    # English Phishing & Impersonation lures
    "Salik Toll Alert: Outstanding violation detected on vehicle. Pay immediately within 24h to avoid judicial referral: https://salik-quickpay.vip",
    "Aramex UAE: Delivery attempt failed due to unpaid customs fee (AED 12.50). Reschedule and pay here: https://aramex-portal-pay.com",
    "Emirates NBD Security: Suspicious login detected from overseas IP. Verify your debit card credentials immediately: https://enbd-security-check.net",
    "e& Customer Care: Your mobile SIM card will be deactivated within 2 hours. Click to verify Emirates ID: https://etisalat-verify-portal.me",
    "Dubai Courts Notice: Legal summons issued against you. Download the official case dossier here: https://dubaicourts-cases.org",
    # Legitimate Official Messages
    "Dubai Police: Your traffic certificate has been issued successfully. Access via official portal: https://www.dubaipolice.gov.ae",
    "DEWA: Thank you for your payment of AED 450. Your official receipt is available at: https://www.dewa.gov.ae",
]


def create_meta_webhook_payload(
    msg_type: str,
    content: dict[str, Any],
    sender_phone: str | None = None,
    msg_id: str | None = None,
) -> dict[str, Any]:
    """Generates standard Meta WhatsApp Business Cloud API webhook event structure."""
    now_ts = int(time.time())
    phone = sender_phone or f"97150{random.randint(1000000, 9999999)}"
    mid = msg_id or f"wamid.HBgL{time.time_ns()}_{random.randint(1000, 9999)}"

    msg_obj: dict[str, Any] = {
        "from": phone,
        "id": mid,
        "timestamp": str(now_ts),
        "type": msg_type,
    }
    if msg_type == "text":
        msg_obj["text"] = content
    elif msg_type == "audio":
        msg_obj["audio"] = content

    return {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "1002349120934",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "97140000000",
                                "phone_number_id": "1002349120934",
                            },
                            "contacts": [
                                {
                                    "profile": {"name": "Citizen Submitter"},
                                    "wa_id": phone,
                                }
                            ],
                            "messages": [msg_obj],
                        },
                        "field": "messages",
                    }
                ],
            }
        ],
    }


def compute_meta_hub_signature(payload_bytes: bytes, app_secret: str) -> str:
    """Computes valid X-Hub-Signature-256 HMAC header."""
    digest = hmac.new(
        key=app_secret.encode("utf-8"),
        msg=payload_bytes,
        digestmod=hashlib.sha256,
    ).hexdigest()
    return f"sha256={digest}"
