import logging
from typing import Any
import httpx
from hares.core.config import get_settings
from hares.engine.verdict import TriageVerdict, VerdictResult

logger = logging.getLogger("hares.services.whatsapp_client")


class WhatsAppClient:
    """
    Outbound WhatsApp Business Cloud API Message Dispatcher (FR-3.1, FR-3.2).
    Sends formatted tri-state triage assessments to citizens with UAE Local Storage compliance.
    """

    def __init__(
        self,
        access_token: str | None = None,
        phone_number_id: str | None = None,
        api_base_url: str | None = None,
        api_version: str | None = None,
        timeout_seconds: float = 3.0,
    ) -> None:
        settings = get_settings()
        self.access_token = access_token or settings.WHATSAPP_ACCESS_TOKEN
        self.phone_number_id = phone_number_id or settings.WHATSAPP_PHONE_NUMBER_ID
        self.api_base_url = (api_base_url or settings.WHATSAPP_API_BASE_URL).rstrip("/")
        self.api_version = api_version or settings.WHATSAPP_API_VERSION
        self.timeout = timeout_seconds

    def send_verdict_reply(self, recipient_phone: str, verdict_result: VerdictResult) -> dict[str, Any]:
        """
        Dispatches standardized tri-state verdict message to citizen submitter.
        For RED verdicts: embeds official Dubai Police e-Crime (https://www.ecrime.ae) and 901 hotline.
        """
        if not recipient_phone or not recipient_phone.strip():
            raise ValueError("Recipient phone number is required.")

        body_text = self._format_message_body(verdict_result)

        # Mock / Development dry-run mode for testing and air-gapped CI
        settings = get_settings()
        if (
            settings.ENVIRONMENT in ["development", "staging"]
            or self.access_token.startswith("mock_")
            or self.access_token.startswith("test_")
        ):
            logger.debug(
                "Dry-run dispatch: reply to recipient=%s... verdict=%s",
                recipient_phone[:4],
                verdict_result.verdict.value,
            )
            return {
                "status": "delivered_mock",
                "recipient": recipient_phone[:4] + "****",
                "verdict": verdict_result.verdict.value,
            }

        url = f"{self.api_base_url}/{self.api_version}/{self.phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient_phone.strip(),
            "type": "text",
            "text": {
                "preview_url": True,
                "body": body_text,
            },
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(url, headers=headers, json=payload)
                resp.raise_for_status()
                return resp.json()
        except httpx.HTTPError as exc:
            logger.error("Outbound WhatsApp message dispatch failed: %s", str(exc))
            raise ValueError(f"Failed to dispatch WhatsApp message via Meta Cloud API: {exc}")

    @staticmethod
    def _format_message_body(verdict: VerdictResult) -> str:
        """Constructs bilingual, clear citizen assessment text."""
        if verdict.verdict == TriageVerdict.RED:
            return (
                f"🚨 *مشروع حارس - تقرير التقييم الأمني*\n"
                f"النتيجة: *عالي الخطورة (احتيال مؤكد)* 🔴\n\n"
                f"السبب: {verdict.reason}\n\n"
                f"⚠️ *إرشادات فورية:*\n"
                f"• لا تفتح الروابط ولا تقم بسداد أي مبالغ أو مشاركة رموز OTP.\n"
                f"• للإبلاغ الرسمي: منصة الجرائم الإلكترونية بشرطة دبي (e-Crime):\n"
                f"{verdict.escalation_url}\n"
                f"• مركز الاتصال لشرطة دبي (غير الطوارئ): {verdict.escalation_hotline}\n\n"
                f"------------------------------------\n"
                f"🚨 *Project Hares - Security Triage Report*\n"
                f"Verdict: *HIGH RISK (Confirmed Threat)* 🔴\n\n"
                f"Reason: {verdict.reason}\n\n"
                f"Report to Dubai Police e-Crime: {verdict.escalation_url}\n"
                f"Non-emergency hotline: {verdict.escalation_hotline}"
            )
        elif verdict.verdict == TriageVerdict.GREEN:
            return (
                f"✅ *مشروع حارس - تقرير التقييم الأمني*\n"
                f"النتيجة: *جهة رسمية موثقة* 🟢\n\n"
                f"الجهة: {verdict.reason}\n\n"
                f"------------------------------------\n"
                f"✅ *Project Hares - Security Triage Report*\n"
                f"Verdict: *VERIFIED OFFICIAL DESTINATION* 🟢\n\n"
                f"{verdict.reason}"
            )
        else:
            return (
                f"⚠️ *مشروع حارس - تقرير التقييم الأمني*\n"
                f"النتيجة: *غير مؤكد - يرجى توخي الحذر* 🟡\n\n"
                f"التفاصيل: {verdict.reason}\n\n"
                f"تنبيه: لم يتم العثور على مؤشرات رسمية موثقة. لا تشارك بياناتك البنكية أو الشخصية.\n\n"
                f"------------------------------------\n"
                f"⚠️ *Project Hares - Security Triage Report*\n"
                f"Verdict: *UNVERIFIED / PROCEED WITH CAUTION* 🟡\n\n"
                f"{verdict.reason}\n"
                f"Caution: Never share OTPs or banking credentials with unverified contacts."
            )
