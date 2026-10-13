from dataclasses import dataclass, field
from enum import Enum


class TriageVerdict(str, Enum):
    RED = "RED"
    AMBER = "AMBER"
    GREEN = "GREEN"


@dataclass
class VerdictResult:
    verdict: TriageVerdict
    rule_triggered: str
    explanation_en: str
    explanation_ar: str
    escalation_url: str | None = None
    police_contact: str | None = None
    indicators: list[str] = field(default_factory=list)
    response_template_en: str = ""
    response_template_ar: str = ""

    @property
    def reason(self) -> str:
        return self.explanation_en

    @property
    def escalation_hotline(self) -> str | None:
        return self.police_contact


class VerdictSynthesizer:
    """
    Tri-State Verdict Synthesizer & Escalation Template Formatter (FR-3.1, FR-3.2).
    Classifies submissions into 🔴 RED, 🟡 AMBER, or 🟢 GREEN states and formats
    bilingual WhatsApp responses with official Dubai Police escalation pathways.
    """

    DUBAI_POLICE_ECRIME_URL: str = "https://www.ecrime.ae"
    DUBAI_POLICE_NON_EMERGENCY_LINE: str = "901"

    def build_red_verdict(
        self,
        rule_triggered: str,
        reason: str,
        indicators: list[str] | None = None,
    ) -> VerdictResult:
        """Constructs a 🔴 High Risk verdict with Dubai Police escalation handoff."""
        ind_list = indicators or []
        explanation_en = f"High Risk: Detected malicious or spoofed indicators ({reason})."
        explanation_ar = f"عالي الخطورة: تم رصد مؤشرات احتيال أو انتحال ({reason})."

        template_en = (
            "🔴 *HIGH RISK / CONFIRMED FRAUD DETECTED*\n\n"
            f"• *Reason:* {explanation_en}\n"
            "• *Action:* Do NOT click links, send money, or provide credentials.\n\n"
            f"🚨 *Official Police Escalation:* Report this incident directly to Dubai Police e-Crime: {self.DUBAI_POLICE_ECRIME_URL}\n"
            f"📞 For non-emergency municipal fraud assistance, call: {self.DUBAI_POLICE_NON_EMERGENCY_LINE}"
        )

        template_ar = (
            "🔴 *تحذير: تم رصد احتيال مؤكد أو عالي الخطورة*\n\n"
            f"• *السبب:* {explanation_ar}\n"
            "• *الإجراء المطلوب:* لا تفتح الروابط ولا تقم بتحويل الأموال أو مشاركة بياناتك.\n\n"
            f"🚨 *الإبلاغ الرسمي:* قم بالإبلاغ الفوري عبر منصة الجرائم الإلكترونية بشرطة دبي: {self.DUBAI_POLICE_ECRIME_URL}\n"
            f"📞 للاستفسارات غير الطارئة، اتصل بشرطة دبي على الرقم: {self.DUBAI_POLICE_NON_EMERGENCY_LINE}"
        )

        return VerdictResult(
            verdict=TriageVerdict.RED,
            rule_triggered=rule_triggered,
            explanation_en=explanation_en,
            explanation_ar=explanation_ar,
            escalation_url=self.DUBAI_POLICE_ECRIME_URL,
            police_contact=self.DUBAI_POLICE_NON_EMERGENCY_LINE,
            indicators=ind_list,
            response_template_en=template_en,
            response_template_ar=template_ar,
        )

    def build_green_verdict(
        self,
        entity_name: str,
        verified_domain: str | None = None,
        indicators: list[str] | None = None,
        reason: str | None = None,
        rule_triggered: str = "allowlist_exact_match",
    ) -> VerdictResult:
        """Constructs a 🟢 Verified Official or Benign verdict."""
        ind_list = indicators or []
        domain_str = verified_domain or "Official / Authenticated Source"
        if reason:
            explanation_en = f"Verified Legitimate: {reason}"
            explanation_ar = f"موثق وسليم: {reason}"
        else:
            explanation_en = f"Verified Official: Matched legitimate domain '{domain_str}' owned by {entity_name}."
            explanation_ar = f"رسمي موثق: النطاق '{domain_str}' مسجل ومعتمد رسميًا لصالح {entity_name}."

        domain_line_en = f"• *Verified Domain:* {domain_str}\n" if verified_domain else ""
        domain_line_ar = f"• *النطاق المعتمد:* {domain_str}\n" if verified_domain else ""

        template_en = (
            "🟢 *VERIFIED SAFE / OFFICIAL*\n\n"
            f"• *Entity:* {entity_name}\n"
            f"{domain_line_en}"
            f"• *Status:* {explanation_en}"
        )

        template_ar = (
            "🟢 *وجهة آمنة وموثقة*\n\n"
            f"• *الجهة:* {entity_name}\n"
            f"{domain_line_ar}"
            f"• *الحالة:* {explanation_ar}"
        )

        return VerdictResult(
            verdict=TriageVerdict.GREEN,
            rule_triggered=rule_triggered,
            explanation_en=explanation_en,
            explanation_ar=explanation_ar,
            indicators=ind_list,
            response_template_en=template_en,
            response_template_ar=template_ar,
        )


    def build_amber_verdict(
        self,
        reason: str = "Unverified source or novel link",
        indicators: list[str] | None = None,
        rule_triggered: str = "unverified_default_caution",
    ) -> VerdictResult:
        """Constructs a 🟡 Amber / Unverified verdict for unlisted or ambiguous inputs."""
        ind_list = indicators or []
        explanation_en = f"Unverified: Authenticity cannot be confirmed ({reason})."
        explanation_ar = f"غير موثق: لا يمكن إثبات صحة الوجهة أو المصدر ({reason})."

        template_en = (
            "🟡 *UNVERIFIED / PROCEED WITH CAUTION*\n\n"
            f"• *Notice:* {explanation_en}\n"
            "• *Precaution:* Do not share OTPs, credit card numbers, or passwords. Verify directly through official app or hotline."
        )

        template_ar = (
            "🟡 *تنبيه: غير موثق / يرجى توخي الحذر*\n\n"
            f"• *ملاحظة:* {explanation_ar}\n"
            "• *الإجراء الوقائي:* تجنب إدخال كلمات المرور أو أرقام البطاقات المصرفية، وتأكد دائمًا عبر القنوات الرسمية."
        )

        return VerdictResult(
            verdict=TriageVerdict.AMBER,
            rule_triggered=rule_triggered,
            explanation_en=explanation_en,
            explanation_ar=explanation_ar,
            indicators=ind_list,
            response_template_en=template_en,
            response_template_ar=template_ar,
        )
