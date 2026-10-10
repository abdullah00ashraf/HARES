import json
import os
import random
import sys
import time

TARGET_TOTAL = 100_000
SPLIT_CONFIG = {
    "emirati_gulf": {"target": 40_000, "malicious_ratio": 0.70},
    "msa": {"target": 30_000, "malicious_ratio": 0.70},
    "expat_english": {"target": 20_000, "malicious_ratio": 0.70},
    "arabizi": {"target": 10_000, "malicious_ratio": 0.70},
}

SYSTEM_PROMPT = (
    "You are the Project Hares sovereign triage engine. Analyze the citizen text inside "
    "XML boundaries. Return strictly a JSON object conforming to TextTriageInferenceResult."
)

# =========================================================================
# Lure & Template Banks
# =========================================================================

# 1. Emirati & Gulf Arabic (40%)
EMIRATI_GREETINGS = [
    "مرحبا يا خوي",
    "هلا والله الشيخ",
    "السلام عليكم طال عمرك",
    "يا بو محمد",
    "صبحك الله بالخير",
    "مساك الله بالخير بو خالد",
    "يا الحبيب",
    "عزيزي العميل",
    "تنبيه عاجل",
    "إشعار هام",
]

EMIRATI_MALICIOUS_TEMPLATES = [
    (
        "{greeting}، حسابك في بنك دبي الإسلامي موقوف مؤقتاً لعدم تحديث الهوية الإماراتية. راجع الرابط فوراً قبل إغلاق الحساب: {link}",
        "Dubai Islamic Bank",
        ["banking_kyc_freeze"],
        "Deceptive DIB account suspension lure targeting UAE citizen with unverified domain.",
    ),
    (
        "{greeting}، مخالفة مرورية مشددة على موترك رقم {plate} بقيمة {amount} درهم. سدد خلال ساعتين عبر الرابط لتفادي الحجز القضائي: {link}",
        "Dubai Police",
        ["traffic_fine_extortion"],
        "Fake Dubai Police traffic fine and vehicle impound threat with coercive countdown.",
    ),
    (
        "{greeting}، رصيد سالك واصل الصفر وعليك غرامة تهرب بقيمة 500 درهم على موترك. اشحن الآن لتفادي التعميم: {link}",
        "Salik",
        ["traffic_fine_extortion"],
        "Salik account toll evasion fine lure demanding immediate unverified top-up.",
    ),
    (
        "{greeting}، تم تعليق شحنتك في مستودع بريد الإمارات بالقوز. ادفع رسوم التوصيل {fee} درهم عبر هذا الرابط لاستلام الطرد: {link}",
        "Emirates Post",
        ["delivery_fee_fraud"],
        "Emirates Post warehouse package detention scam demanding advance payment.",
    ),
    (
        "{greeting}، إنذار بقطع الكهرباء والمياه من ديوا اليوم لتأخر سداد الفاتورة بقيمة {amount} درهم. ادخل الرابط وسدد فوراً: {link}",
        "DEWA",
        ["utility_shutoff"],
        "DEWA utility disconnection threat with urgent unverified payment portal link.",
    ),
    (
        "{greeting}، مصرف أبوظبي الإسلامي: تم حظر بطاقة الخصم الخاصة بك لمحاولة دخول مشبوهة. يرجى تفعيلها بإدخال رقم البطاقة ورمز OTP هنا: {link}",
        "Abu Dhabi Islamic Bank",
        ["otp_harvesting", "banking_kyc_freeze"],
        "ADIB debit card freeze phishing attack harvesting card credentials and OTP.",
    ),
    (
        "{greeting}، تم قفل حساب تطبيق UAE Pass الخاص بك. يرجى توثيق البصمة والهوية فوراً عبر الرابط لتفادي إيقاف الخدمات الحكومية: {link}",
        "UAE Pass",
        ["credential_phishing"],
        "Spoofed UAE Pass national identity lock notification harvesting citizen credentials.",
    ),
    (
        "{greeting}، شريحة اتصالات (e&) الخاصة بك سيتم إيقافها نهائياً خلال 3 ساعات لعدم تجديد بيانات الهوية. حدث الآن: {link}",
        "e& (Etisalat)",
        ["sim_swap_threat"],
        "Telecom SIM card deactivation threat impersonating e& to harvest identity data.",
    ),
]

EMIRATI_BENIGN_TEMPLATES = [
    (
        "{greeting}، شرطة دبي تذكرك: تجديد ملكية المركبة رقم {plate} متاح الآن عبر تطبيق شرطة دبي الرسمي: https://www.dubaipolice.gov.ae",
        "Dubai Police",
        "Official Dubai Police vehicle registration renewal reminder via verified .gov.ae portal.",
    ),
    (
        "{greeting}، سالك: تم خصم مبلغ {amount} درهم لمرور بوابة البرشاء. رصيدك الحالي {balance} درهم. للاستفسار زر: https://www.salik.ae",
        "Salik",
        "Legitimate Salik toll deduction alert with verified balance and official .ae domain.",
    ),
    (
        "{greeting}، ديوا: شكراً لسداد فاتورتك الشهرية بمبلغ {amount} درهم. تم استلام الدفعة بنجاح. يمكنك مراجعة الفاتورة الخضراء: https://www.dewa.gov.ae",
        "DEWA",
        "Official DEWA receipt acknowledgment confirming legitimate utility payment.",
    ),
    (
        "{greeting}، بنك الإمارات دبي الوطني: تم استلام حوالة مصرفية بمبلغ {amount} درهم في حسابك. لمعرفة التفاصيل استخدم التطبيق الرسمي.",
        "Emirates NBD",
        "Legitimate banking inbound transfer notification directing to official mobile banking app.",
    ),
    (
        "{greeting}، بريد الإمارات: طردك رقم {tracking} في طريقه للتسليم اليوم إلى عنوانك المسجل. لا يلزم أي إجراء منك.",
        "Emirates Post",
        "Standard Emirates Post out-for-delivery notification requiring zero citizen payment.",
    ),
]

# 2. Modern Standard Arabic (30%)
MSA_MALICIOUS_TEMPLATES = [
    (
        "إشعار قضائي عاجل من شرطة دبي: صدر بحقك أمر استدعاء في القضية الجنائية رقم {case_id}. للاطلاع على ملف القضية ومراجعة لائحة الاتهام اضغط هنا: {link}",
        "Dubai Police",
        ["legal_extortion", "credential_phishing"],
        "Fabricated Dubai Police criminal summons lure designed to instill panic and harvest credentials.",
    ),
    (
        "المصرف المركزي لدولة الإمارات العربية المتحدة: تطبيقاً لتعليمات الامتثال المصرفي، تم تعليق كافة العمليات المالية لحسابكم. لإعادة التنشيط ورفع التجميد يرجى المصادقة عبر البوابة الوطنية: {link}",
        "Central Bank of the UAE",
        ["banking_kyc_freeze"],
        "Spoofed Central Bank of the UAE regulatory account freeze phishing lure with unverified domain.",
    ),
    (
        "هيئة كهرباء ومياه دبي (ديوا): تنبيه أخير بفصل الخدمة. سيتم قطع التيار الكهربائي عن العقار رقم {account} خلال 60 دقيقة لعدم سداد المستحقات المتأخرة. لسداد المبلغ تفضل بالدخول: {link}",
        "DEWA",
        ["utility_shutoff"],
        "Deceptive DEWA final disconnection notice utilizing aggressive 60-minute coercion.",
    ),
    (
        "بريد الإمارات: تعذر تسليم الشحنة الجمركية رقم {tracking} لوجود رسوم جمركية مستحقة بقيمة {fee} درهم. في حال عدم السداد خلال 24 ساعة ستتم إعادة الطرد إلى بلد المنشأ. سدد الآن: {link}",
        "Emirates Post",
        ["delivery_fee_fraud"],
        "Fraudulent postal customs fee demand threatening return of parcel to sender.",
    ),
    (
        "مصرف الإمارات الإسلامي: عملية شراء جديدة بقيمة {amount} درهم على بطاقتك الائتمانية لدى متجر إلكتروني دولي. إذا لم تكن أنت من قام بالعملية، أوقف البطاقة فوراً عبر الرابط: {link}",
        "Emirates Islamic Bank",
        ["banking_kyc_freeze", "credential_phishing"],
        "Phishing lure simulating unauthorized credit card purchase to induce panic and credential theft.",
    ),
    (
        "الهيئة الاتحادية للهوية والجنسية والجمارك وأمن المنافذ: بطاقة الهوية الإماراتية الخاصة بكم منتهية الصلاحية. تفادياً للغرامة اليومية (20 درهم/يوم) يرجى تجديد البيانات ودفع الرسوم: {link}",
        "Federal Authority for Identity and Citizenship",
        ["credential_phishing", "government_fine_extortion"],
        "Spoofed ICP Emirates ID expiration penalty notice directing to fraudulent payment gateway.",
    ),
]

MSA_BENIGN_TEMPLATES = [
    (
        "شرطة دبي: تم إصدار شهادة بحث الحالة الجنائية (بحث سوابق) الخاصة بكم بنجاح. يمكنكم تحميل الشهادة الرقمية عبر تطبيق شرطة دبي أو الرابط الرسمي: https://www.dubaipolice.gov.ae",
        "Dubai Police",
        "Legitimate Dubai Police digital certificate issuance notification with official government URL.",
    ),
    (
        "المصرف المركزي لدولة الإمارات: تحذير أمني عام: يرجى عدم مشاركة كلمة المرور لمرة واحدة (OTP) أو البيانات السرية للبطاقات المصرفية مع أي جهة تدعي تمثيل المصرف المركزي.",
        "Central Bank of the UAE",
        "Official CBUAE public fraud awareness bulletin warning citizens against sharing OTPs.",
    ),
    (
        "هيئة الطرق والمواصلات (RTA): تم تجديد ترخيص المركبة رقم {plate} بنجاح. شكراً لالتزامكم بمعايير السلامة المرورية في إمارة دبي: https://www.rta.ae",
        "RTA",
        "Legitimate RTA vehicle license renewal confirmation with official municipal domain.",
    ),
    (
        "بنك أبوظبي الأول (FAB): تم تحديث بيانات الهوية الإماراتية الخاصة بحسابكم المصرفي بنجاح. شكراً لتعاملكم مع مصرفنا.",
        "First Abu Dhabi Bank",
        "Legitimate banking identity confirmation acknowledging successful KYC completion.",
    ),
    (
        "بريد الإمارات: تم إيداع الشحنة رقم {tracking} في صندوق البريد الذكي الخاص بكم. رمز الاستلام هو {code}. https://www.emiratespost.ae",
        "Emirates Post",
        "Official Emirates Post smart locker package delivery notice with official .ae domain.",
    ),
]

# 3. UAE Expat English (20%)
ENGLISH_MALICIOUS_TEMPLATES = [
    (
        "Emirates Post Alert: Your package #{tracking} is held at our Dubai central depot due to incomplete address details. A customs clearance fee of AED {fee} is pending. Update your details and pay here: {link}",
        "Emirates Post",
        ["delivery_fee_fraud"],
        "Emirates Post customs fee lure targeting UAE expats with fake delivery rescheduling portal.",
    ),
    (
        "Salik Toll Violation: Vehicle plate {plate} has accrued {amount} AED in unpaid toll crossing violations. Judicial summons will be issued if payment is not cleared within 24h: {link}",
        "Salik",
        ["traffic_fine_extortion"],
        "Deceptive Salik violation extortion message threatening legal referral over unpaid tolls.",
    ),
    (
        "Emirates NBD Security Alert: A login attempt was detected from an unrecognized device in Frankfurt, Germany. Your online banking access is temporarily frozen. Verify your account immediately: {link}",
        "Emirates NBD",
        ["banking_kyc_freeze", "credential_phishing"],
        "Emirates NBD account freeze lure spoofing overseas login alert to harvest citizen credentials.",
    ),
    (
        "Aramex Express Delivery: Delivery attempt for parcel #{tracking} failed today. Please confirm your delivery address and pay AED 15 redelivery fee to avoid item return: {link}",
        "Aramex",
        ["delivery_fee_fraud"],
        "Fake Aramex failed delivery notification demanding unverified credit card fee payment.",
    ),
    (
        "DEWA Notice: Immediate disconnection scheduled today for electricity and water meter #{account} due to unpaid balance of AED {amount}. Settle outstanding bill now to maintain service: {link}",
        "DEWA",
        ["utility_shutoff"],
        "DEWA utility shutoff extortion threat demanding immediate payment via suspicious link.",
    ),
    (
        "Dubai Police Traffic Dept: Speed violation recorded on Sheikh Zayed Road (radar radar-SZ92). Fine amount: AED {amount} with 4 black points. Settle immediately to avoid vehicle impound: {link}",
        "Dubai Police",
        ["traffic_fine_extortion"],
        "Fraudulent Dubai Police speeding fine notification with black points extortion threat.",
    ),
    (
        "e& Customer Care: Your mobile line +97150xxxxxxx will be deactivated within 4 hours due to unverified Emirates ID residency record. Complete biometric identity verification here: {link}",
        "e& (Etisalat)",
        ["sim_swap_threat", "credential_phishing"],
        "Telecom SIM suspension phishing lure threatening line disconnection to steal identity details.",
    ),
    (
        "Dubai International Airport HR: Congratulations! Your CV was shortlisted for Senior Operations Executive at Terminal 3. Salary AED 24,500/month. Confirm interview by submitting AED 350 registration fee: {link}",
        "Dubai Airports",
        ["job_recruitment_scam"],
        "Employment advance fee scam impersonating Dubai Airports HR to extort application fees.",
    ),
]

ENGLISH_BENIGN_TEMPLATES = [
    (
        "Emirates Post: Shipment #{tracking} has arrived at Dubai Central Post Office and is scheduled for out-for-delivery dispatch. Track online at https://www.emiratespost.ae",
        "Emirates Post",
        "Legitimate Emirates Post package tracking notification referencing official government domain.",
    ),
    (
        "Salik Notice: Your Salik account was successfully recharged with AED {amount} via Auto-Pay. Your current balance is AED {balance}. View trip history: https://www.salik.ae",
        "Salik",
        "Official Salik auto-recharge confirmation with verified balance and official website link.",
    ),
    (
        "Dubai Police: Traffic awareness advisory: Please maintain safe following distance on highways during foggy morning conditions. Safety first. https://www.dubaipolice.gov.ae",
        "Dubai Police",
        "Public safety awareness broadcast from official Dubai Police portal with zero demands.",
    ),
    (
        "DEWA: Thank you for your payment of AED {amount} for utility account #{account}. Transaction reference #{ref}. Official receipt: https://www.dewa.gov.ae",
        "DEWA",
        "Official DEWA payment receipt acknowledgment linking to verified municipal portal.",
    ),
    (
        "Emirates NBD: Your monthly e-Statement for account ending in {account_last4} is now available in Online Banking. Never share your password or OTP with anyone.",
        "Emirates NBD",
        "Legitimate banking account statement availability alert reinforcing anti-phishing hygiene.",
    ),
]

# 4. Arabizi / Franco-Arabic (10%)
ARABIZI_MALICIOUS_TEMPLATES = [
    (
        "3ajel: 7esabak el banky mafeesh update lel hawiyya el emarateya. Efta7 el link w 2aked el bayanat 2abl ma yet2afel: {link}",
        "Central Bank of the UAE",
        ["banking_kyc_freeze"],
        "Arabizi banking KYC freeze lure using Latinized Arabic numerals to bypass keyword filters.",
    ),
    (
        "Shor6at Dubai: 3endak mo5alafa morooreya gadeda 3ala el mowater {plate} be 2eemet {amount} AED. Sedad 7alan 3ashan ma yet7ajaz: {link}",
        "Dubai Police",
        ["traffic_fine_extortion"],
        "Arabizi Dubai Police traffic fine and impound threat bypassing naive keyword matching.",
    ),
    (
        "Mabrook! Raqm telephonak rabah' 200,000 AED ma3 Etisalat UAE. Etsel bel raqam aw od5ol el link 3ashan testalem el ja2eza: {link}",
        "e& (Etisalat)",
        ["lottery_prize_fraud"],
        "Arabizi telecommunications lottery scam claiming cash prize to harvest banking details.",
    ),
    (
        "Aramex UAE: El shahnatek raqm #{tracking} ma3ala2a fel mostawda3. Edfa3 12.50 AED rasoom ta2keed el 3enwan 3ashan توصل: {link}",
        "Aramex",
        ["delivery_fee_fraud"],
        "Arabizi courier package delivery fee fraud directing citizen to fraudulent link.",
    ),
    (
        "DEWA Dubai: Enzar be 2at3 el kahraba el naharda le 3adam sedad el fatoora #{account}. Edfa3 7alan 3ala el link: {link}",
        "DEWA",
        ["utility_shutoff"],
        "Arabizi DEWA utility disconnection threat urging immediate payment on unverified URL.",
    ),
    (
        "Ta2keed OTP: Ramz el ta2keed howa 9182. Talab ta7weel 4,500 AED. Eza mesh enta, e2fel el 7esab men hena: {link}",
        "Emirates NBD",
        ["otp_harvesting", "banking_kyc_freeze"],
        "Arabizi OTP harvesting phishing attack simulating unauthorized transfer panic.",
    ),
]

ARABIZI_BENIGN_TEMPLATES = [
    (
        "Salik UAE: Tam 5asm {amount} AED le bawabit el Barsha. Raseedak el 7aly {balance} AED. Lel ma3loomat zor: https://www.salik.ae",
        "Salik",
        "Legitimate Arabizi Salik toll notification linking to official government portal.",
    ),
    (
        "DEWA: Shokran le sedad fatoorat el kahraba be mablagh {amount} AED. Tam estelam el daf3a be naja7: https://www.dewa.gov.ae",
        "DEWA",
        "Legitimate Arabizi DEWA receipt notification linking to official portal.",
    ),
    (
        "Dubai Police: Neshabhat 3aleik bel 5eir. Tzakkar teftah asharet el moroor fel ghabash le salametak. https://www.dubaipolice.gov.ae",
        "Dubai Police",
        "Official Arabizi traffic safety awareness reminder from Dubai Police.",
    ),
    (
        "Emirates Post: El shahna raqm {tracking} وصلt markaz el tawzee3 w gayya fel tareeq. https://www.emiratespost.ae",
        "Emirates Post",
        "Legitimate Arabizi postal out-for-delivery status update with official domain.",
    ),
]

# Deceptive vs Official link pools
MALICIOUS_DOMAINS = [
    "http://ecr1me-pay.top",
    "https://dubaipolice-fines.click",
    "http://salik-quickpay.vip",
    "https://salik-recharge.cc",
    "http://emiratespost-tracking.online",
    "https://epost-delivery-fee.club",
    "http://cbuae-update.ae.security-hub.net",
    "https://centralbank-kyc-uae.com",
    "http://dewa-bill-settle.cc",
    "https://dewa-pay-portal.info",
    "http://enbd-security-check.net",
    "https://adcb-banking-auth.org",
    "http://aramex-portal-pay.com",
    "https://aramex-customs-clearance.top",
    "http://etisalat-verify-portal.me",
    "https://du-sim-activation.xyz",
    "http://uaepass-auth-portal.com",
    "https://uae-identity-renewal.tech",
]

MALICIOUS_SHORTENERS = [
    "https://bit.ly/uae-pay-91",
    "https://tinyurl.com/salik-fines",
    "https://is.gd/dubai-police-traffic",
    "https://cutt.ly/dewa-urgent-settle",
    "https://rb.gy/emirates-post-track",
]

def generate_random_link(is_shortened: bool = False) -> str:
    if is_shortened:
        return random.choice(MALICIOUS_SHORTENERS) + f"?id={random.randint(10000, 99999)}"
    domain = random.choice(MALICIOUS_DOMAINS)
    path = random.choice(["/pay", "/verify", "/kyc", "/settle", "/tracking", "/portal", "/auth"])
    return f"{domain}{path}?ref={random.randint(100000, 999999)}"


def build_record(category: str, is_malicious: bool) -> dict:
    amount = str(random.choice([150, 250, 320, 450, 600, 850, 1000, 1500, 2000, 3000]))
    fee = str(random.choice([12.50, 15.00, 18.00, 25.00, 30.00, 35.50]))
    plate = f"{random.choice(['A', 'B', 'C', 'D', 'E', 'H', 'K', 'L', 'M', 'N', 'R', 'S', 'T'])} {random.randint(1000, 99999)}"
    tracking = f"EP{random.randint(10000000, 99999999)}AE"
    account = str(random.randint(100000000, 999999999))
    balance = str(random.choice([25, 40, 60, 85, 120, 150]))
    ref = f"TXN{random.randint(1000000, 9999999)}"
    code = str(random.randint(1000, 9999))
    case_id = f"{random.randint(100, 999)}/2026"
    link = generate_random_link(is_shortened=random.random() < 0.25)
    greeting = random.choice(EMIRATI_GREETINGS)

    if category == "emirati_gulf":
        if is_malicious:
            tmpl, entity, tactics, reason = random.choice(EMIRATI_MALICIOUS_TEMPLATES)
            text = tmpl.format(greeting=greeting, link=link, amount=amount, plate=plate, fee=fee)
            assistant_obj = {
                "is_impersonation": True,
                "impersonated_entity": entity,
                "urgency_or_coercion": True,
                "financial_or_credential_demand": True,
                "confidence_score": round(random.uniform(0.92, 0.99), 2),
                "detected_tactics": tactics,
                "reasoning_summary": reason,
            }
        else:
            tmpl, entity, reason = random.choice(EMIRATI_BENIGN_TEMPLATES)
            text = tmpl.format(greeting=greeting, plate=plate, amount=amount, balance=balance, tracking=tracking)
            assistant_obj = {
                "is_impersonation": False,
                "impersonated_entity": None,
                "urgency_or_coercion": False,
                "financial_or_credential_demand": False,
                "confidence_score": round(random.uniform(0.01, 0.08), 2),
                "detected_tactics": [],
                "reasoning_summary": reason,
            }

    elif category == "msa":
        if is_malicious:
            tmpl, entity, tactics, reason = random.choice(MSA_MALICIOUS_TEMPLATES)
            text = tmpl.format(case_id=case_id, link=link, account=account, tracking=tracking, fee=fee, amount=amount)
            assistant_obj = {
                "is_impersonation": True,
                "impersonated_entity": entity,
                "urgency_or_coercion": True,
                "financial_or_credential_demand": True,
                "confidence_score": round(random.uniform(0.94, 0.99), 2),
                "detected_tactics": tactics,
                "reasoning_summary": reason,
            }
        else:
            tmpl, entity, reason = random.choice(MSA_BENIGN_TEMPLATES)
            text = tmpl.format(plate=plate, tracking=tracking, code=code)
            assistant_obj = {
                "is_impersonation": False,
                "impersonated_entity": None,
                "urgency_or_coercion": False,
                "financial_or_credential_demand": False,
                "confidence_score": round(random.uniform(0.01, 0.06), 2),
                "detected_tactics": [],
                "reasoning_summary": reason,
            }

    elif category == "expat_english":
        if is_malicious:
            tmpl, entity, tactics, reason = random.choice(ENGLISH_MALICIOUS_TEMPLATES)
            text = tmpl.format(tracking=tracking, fee=fee, link=link, plate=plate, amount=amount, account=account)
            assistant_obj = {
                "is_impersonation": True,
                "impersonated_entity": entity,
                "urgency_or_coercion": True,
                "financial_or_credential_demand": True,
                "confidence_score": round(random.uniform(0.93, 0.99), 2),
                "detected_tactics": tactics,
                "reasoning_summary": reason,
            }
        else:
            tmpl, entity, reason = random.choice(ENGLISH_BENIGN_TEMPLATES)
            text = tmpl.format(tracking=tracking, amount=amount, balance=balance, account=account, ref=ref, account_last4=str(random.randint(1000, 9999)))
            assistant_obj = {
                "is_impersonation": False,
                "impersonated_entity": None,
                "urgency_or_coercion": False,
                "financial_or_credential_demand": False,
                "confidence_score": round(random.uniform(0.01, 0.05), 2),
                "detected_tactics": [],
                "reasoning_summary": reason,
            }

    else:  # arabizi
        if is_malicious:
            tmpl, entity, tactics, reason = random.choice(ARABIZI_MALICIOUS_TEMPLATES)
            text = tmpl.format(link=link, plate=plate, amount=amount, tracking=tracking, account=account)
            assistant_obj = {
                "is_impersonation": True,
                "impersonated_entity": entity,
                "urgency_or_coercion": True,
                "financial_or_credential_demand": True,
                "confidence_score": round(random.uniform(0.91, 0.98), 2),
                "detected_tactics": tactics,
                "reasoning_summary": reason,
            }
        else:
            tmpl, entity, reason = random.choice(ARABIZI_BENIGN_TEMPLATES)
            text = tmpl.format(amount=amount, balance=balance, tracking=tracking)
            assistant_obj = {
                "is_impersonation": False,
                "impersonated_entity": None,
                "urgency_or_coercion": False,
                "financial_or_credential_demand": False,
                "confidence_score": round(random.uniform(0.02, 0.09), 2),
                "detected_tactics": [],
                "reasoning_summary": reason,
            }

    # Format ChatML message structure
    user_content = f"<citizen_forwarded_text>{text}</citizen_forwarded_text>"
    assistant_content = json.dumps(assistant_obj, ensure_ascii=False)

    return {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
            {"role": "assistant", "content": assistant_content},
        ]
    }


def main():
    out_dir = os.path.abspath("opensource/datasets/localized_fraud_corpus")
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "uae_smishing_100k.jsonl")
    manifest_file = os.path.join(out_dir, "uae_smishing_manifest.json")

    print(f"Generating {TARGET_TOTAL:,} ChatML paired instruction-response records...")
    t0 = time.time()

    split_counts = {"emirati_gulf": 0, "msa": 0, "expat_english": 0, "arabizi": 0}
    class_counts = {"malicious": 0, "benign": 0}

    with open(out_file, "w", encoding="utf-8") as f:
        for split_key, cfg in SPLIT_CONFIG.items():
            target_n = cfg["target"]
            malicious_target = int(target_n * cfg["malicious_ratio"])
            benign_target = target_n - malicious_target

            # Generate malicious
            for _ in range(malicious_target):
                rec = build_record(split_key, is_malicious=True)
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                split_counts[split_key] += 1
                class_counts["malicious"] += 1

            # Generate benign
            for _ in range(benign_target):
                rec = build_record(split_key, is_malicious=False)
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                split_counts[split_key] += 1
                class_counts["benign"] += 1

    dt = time.time() - t0
    file_size_mb = os.path.getsize(out_file) / (1024 * 1024)
    print(f"Generation completed in {dt:.2f}s ({TARGET_TOTAL/dt:.0f} rec/s)!")
    print(f"Output File: {out_file} ({file_size_mb:.2f} MB)")
    print(f"Split distribution: {split_counts}")
    print(f"Class distribution: {class_counts}")

    # Generate Manifest
    manifest = {
        "dataset_name": "Project Hares Localized UAE Text Smishing & Social Engineering Corpus (100K)",
        "version": "1.0.0",
        "format": "ChatML JSONL",
        "total_records": TARGET_TOTAL,
        "splits": {
            "emirati_gulf_arabic": {"count": split_counts["emirati_gulf"], "percentage": 40.0},
            "modern_standard_arabic": {"count": split_counts["msa"], "percentage": 30.0},
            "uae_expat_english": {"count": split_counts["expat_english"], "percentage": 20.0},
            "arabizi_franco_arabic": {"count": split_counts["arabizi"], "percentage": 10.0},
        },
        "class_balance": {
            "malicious_fraud_lures": {"count": class_counts["malicious"], "percentage": 70.0},
            "benign_verified_notifications": {"count": class_counts["benign"], "percentage": 30.0},
        },
        "file_path": "opensource/datasets/localized_fraud_corpus/uae_smishing_100k.jsonl",
        "file_size_bytes": os.path.getsize(out_file),
        "target_task": "Local Sovereign SLM Instruction-Tuning (TextTriageInferenceResult FSM Decoding)",
    }
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    print(f"Manifest written to {manifest_file}")


if __name__ == "__main__":
    main()
