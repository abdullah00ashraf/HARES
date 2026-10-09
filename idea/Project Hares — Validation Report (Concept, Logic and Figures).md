# Project Hares — Validation Report

*Prepared 9 October 2026 · Inputs: Project Hares Problem Statement + SRS; UAE Cyber Fraud Statistics brief · Method: each figure checked against the originating publication or press release where reachable*

## 1. Verdict

**Concept:** the problem is real and well evidenced, and the architecture is credible. But six requirements are infeasible or contradict each other as written (Section 4). All are fixable without changing the idea.

**Figures:** 41 claims audited across both files.

| Result | Count | Share |
| --- | --- | --- |
| ✅ Verified as stated | 18 | 44% |
| ⚠️ Real, but needs correction (wrong date, base, attribution or wording) | 9 | 22% |
| ❌ Wrong or misread | 2 | 5% |
| 🔶 Could not verify | 12 | 29% |

‘Could not verify’ means I searched and found no primary source. It does not mean the claim is false. The SRS problem statement is the cleaner document; the statistics brief carries most of the errors.

**Top findings, ranked**

| # | Finding | Severity |
| --- | --- | --- |
| 1 | NFR-1.1 (‘no data through offshore APIs’) cannot be met on WhatsApp. The Cloud API is hosted by Meta, and Meta ended the self-hosted On-Premises API on 23 Oct 2025. | Critical |
| 2 | NFR-3.1 (FPR below 0.1%) is not supported by published detector performance, nor by the SRS’s own conformal method. Merely demonstrating it needs about 3,000 genuine test clips with zero false alarms. | Critical |
| 3 | FR-2.2’s strict .gov.ae allowlist would flag the official Dubai Police e-Crime portal (ecrime.ae). | High |
| 4 | FR-4.1 strips PII, while the statistics brief promises to harvest phone numbers, domains and wallets as threat indicators. The two documents contradict each other. | High |
| 5 | The audio module targets forwarded voice notes, but the documented voice-clone scams are mostly live calls. | High |
| 6 | The statistics brief misreads GASA’s 52% figure and misattributes the AED 3,250 and AED 11M figures. | High (credibility) |

## 2. Legend and method

✅ verified · ⚠️ verified with correction · ❌ wrong · 🔶 unverified · 🧪 my own calculation or illustrative model (not from a source)

**No UI mockups, placeholder data or invented figures were used.** Three items are my own calculations, marked 🧪 and listed in Section 7. Everything else comes from sources I retrieved. Limits: GASA’s full reports need registration, the CPX blog was unreachable, and Visa’s full PDFs were only partly readable. Where I relied on secondary coverage I say so.

## 3. Figure ledger

### 3.1 SRS (problem statement)

| ID | Claim | Status | Finding |
| --- | --- | --- | --- |
| S1 | Social engineering drives nearly 98% of cyberattacks (UAE Cyber Security Council) | ✅ | Council statement via WAM, 21 Sep 2025, from its Cyber Pulse awareness campaign. Coverage gives no methodology. Differs in scope from the Council’s own 75% figure (F3). |
| S2 | 56% face scam attempts monthly | ✅ | GASA/BioCatch 2024 State of Scams UAE with the Cybersecurity Council and TRENDS; n = 1,964; released 28 Nov 2024. |
| S3 | ‘Only 30% report them’ | ⚠️ | The source says 30% reported to law enforcement. It is not a measure of all reporting. GASA 2026 finds 79% of people who experienced a scam reported at least one incident to some entity (F20). |
| S4 | 18% don’t know where to report | ✅ | Same 2024 study. Reasons given: complexity, uncertainty, doubt that reporting works. |
| S5 | Agentic AI for Government Services Accelerator | ✅ | Launched 5 Oct 2026 by Dubai Future Foundation: 33 Dubai entities, 300+ use cases, run by DCAI with Digital Dubai and DESC. It is for government entities building agentic services. Hares as specified is a classifier pipeline, not an agent, so the fit is arguable. |
| S6 | ‘Dubai AI Infrastructure Empowerment Platform’ | ⚠️ | Real name is ‘AI Infrastructure Empowerment Platform’, approved Oct 2025 for Dubai government entities. It is not a public cloud; an open-source project would need a government sponsor to use it. |
| S7 | Call 901 / Dubai Police e-Crime | ✅ | 901 is the Dubai Police line. e-Crime covers only crimes within Dubai. Older Gulf News guidance calls 901 ‘inquiries only’; the app and e-Crime are the filing routes. |
| S8 | Federal Decree-Law No. 45 of 2021 (PDPL) | ✅ | Number and date correct (issued 20 Sep 2021). Applicability is a separate problem; see 4.8. |
| S9 | Single-purpose bot on the WhatsApp Business API | ✅ | Meta’s terms from 15 Jan 2026 prohibit general-purpose AI assistants on the API. Task-specific bots remain allowed. The single-purpose framing is the correct design choice. |

### 3.2 Statistics brief

| ID | Claim | Status | Finding |
| --- | --- | --- | --- |
| F1 | 200,000+ attacks/day; 640,000 on a peak day | ⚠️ | 640,000 confirmed (Al Kuwaiti, Arab Media Summit); the brief cites a Facebook post instead. On 18 Feb 2026 the Council gave a range of 90,000–200,000 attempts/day, so ‘over 200,000’ is the top of a range, not a floor. |
| F2 | UAE is 6th most targeted (Microsoft) | ✅ | Digital Defence Report, H1 2026: 6th globally, 2nd in MEA among countries where Microsoft customers were most frequently impacted. This is a customer-telemetry ranking, not total attack volume. |
| F3 | 75% of breaches begin with phishing or fraudulent messages (CSC) | ✅ | Council figure carried by Khaleej Times, 16 Jul 2026. The brief alternates ‘breaches’, ‘attacks’ and ‘network attacks’; use ‘breaches’. |
| F4 | 90% of breaches bypass defences via AI social engineering | 🔶 | Sole source is a consultancy blog (conflictadvisory.com), not fetched. Extraordinary claim; conflicts with F3. Do not use as a headline. |
| F5 | 91% of attacks start with phishing; scammers make 57% of fake sites (Group-IB) | 🔶 | No dataset traced. The 91% claim is widely repeated by vendors; I found no primary methodology (background knowledge, not searched). |
| F6 | CPX: 48% medium / 28% high severity; phishing-spoofing-email 12%; drive-by, remote injection and direct install 11% each | 🔶 | CPX blog unreachable. The official CPX–CSC report release (25 Feb 2025) confirms other headline numbers (see F7). |
| F7 | 61% of incidents tied to improper usage and unlawful activity | ❌ | The official release says misconfiguration 32% and improper usage/unlawful activity 19%. That category is policy misuse, not social engineering, so the brief’s inference is also a leap. |
| F8 | UAE businesses lose $2.9M/yr (CPX) | ⚠️ | A matching figure (about AED 11M) exists, but in Adyen’s UAE Retail Report: retailers only, 2023 data, published 23 Apr 2024. $2.9M × 3.6725 = AED 10.65M. Likely misattributed. |
| F9 | GASA/Trend Micro: 70% encountered a scam, one per 3 days, 1 in 3 lost money, 10% multiple per day | ✅ | GASA release 27 Jan 2026; n = 1,000; self-reported. |
| F10 | About 111 encounters per person per year | ⚠️ | GASA states 111, but one per 3 days is 121.7/yr (365 ÷ 3). Source rounding. Cite as ‘about every three days (GASA: 111/yr)’. |
| F11 | Shopping 70%, investment 67%, unexpected money 66% | ✅ | Shares of victims, not mutually exclusive. |
| F12 | Visa: 49% fell for a scam, 15% repeatedly, 59% confident, 92% worry about others; n = 300 UAE | ✅ | Visa Stay Secure, Wakefield Research, fieldwork Dec 2024; 5,800 adults in 17 markets; published 18 Mar 2025. |
| F13 | ‘Highly knowledgeable’ users respond more: 79% vs 74%, 72% vs 61% | ⚠️ | UAE numbers are correct but come from Visa’s 2023 study (Nov/Dec 2023), not 2024/25. They measure self-reported likelihood to respond, not behaviour. |
| F14 | 62% of victims asked for a transfer; 69% bought via social media; 38% of scams on social platforms | 🔶 | Not found in the Visa releases I retrieved. |
| F15 | Responsibility: 36% banks / 36% government / 19% self (Visa, June 2026) | 🔶 | Not found. ‘June 2026’ conflicts with the study’s March 2025 release. GASA does say UAE residents see government and law enforcement as primarily responsible (qualitative). |
| F16 | 68% rank ‘data breach / password reset’ as the most believable lure | 🔶 | Not found. The brief describes the same figure three incompatible ways (‘believable’, ‘believable and suspicious’, ‘red flags recognized’). |
| F17 | Average loss AED 3,250, up 270% from AED 880 in 2022 (‘IBS Intelligence’) | ⚠️ | Maths right (+269.3%). Origin is Adyen’s UAE Retail Report (CEBR research), data year 2023; IBS Intelligence reprinted it. It covers payments-fraud victims, not all scam victims. |
| F18 | Norton: about $283 (AED about 1,038) | 🔶 | Conversion right ($283 × 3.6725 = AED 1,039). Edition unknown; Norton’s 2017 report gave AED 669, so this is old. |
| F19 | LexisNexis: each AED 1 lost costs firms AED 4.19 | ✅ | Release dated 17 Apr 2024 (URL and title confirm); body not re-read. Applies to firms, not citizens. |
| F20 | 79% of those who experienced a scam reported at least one incident | ✅ | GASA 2026; reporters averaged 4.6 encounters reported. |
| F21 | ‘52% of residents don’t report if no loss’ and ‘52% of the population will not report unless there is financial loss’ | ❌ | GASA says no financial loss was the most common reason for not reporting, cited by 52%. By the release’s wording that base is respondents who did not report. The brief turns a share-of-reasons into a share-of-population. |
| F22 | 50% of reporters saw no action or are unsure | ✅ | GASA 2026. |
| F23 | Dubai Police shut 103 fraudulent social accounts in Q2 2026 | ✅ | Reported 3 Aug 2026 (Khaleej Times, Emirates247, The National). |
| F24 | ‘31.2% drop in major crime categories’ | 🔶 | Six reports retrieved say ‘decline’ in fraud, cybercrime and economic crime, with no percentage. |
| F25 | Quote attributed to ‘Major General Jamal Salem Al Shamsi’ | ⚠️ | Coverage says ‘Major General Al Shamsi’; one outlet names Maj. Gen. Hareb Al Shamsi, Deputy Commander-in-Chief for Criminal Affairs. Verify the full name before attributing. |
| F26 | CBUAE Notice 3057 bans SMS/email OTP and static passwords as standalone authentication | ✅ | Issued 23 May 2025; full phase-out deadline 31 Mar 2026 (now passed, so the brief’s ‘ahead of March 2026’ is stale); refund liability for 3DS fraud from July 2025 per vendor summaries (primary text not read). |
| F27 | Kaspersky: 44% of UAE users met scams in the past year | 🔶 | The only 44% Kaspersky UAE figure I found is from 2016 and measures ‘affected by cyberthreats’. Date and definition likely wrong. |
| F28 | Microsoft 365 holds 77% of the regional market; device-code phishing | 🔶 | Not verified. |
| F29 | Classiscam: 384 groups; Craxs RAT in UAE/Singapore | 🔶 | Not verified (cited to a Scribd copy). |
| F30 | TDRA/Dubai Police warnings of a voice-clone surge | 🔶 | Cited to a law-firm blog and a news aggregator; no primary advisory retrieved. |
| F31 | e-Crime needs accused details and proof; too heavy for zero-loss cases | ⚠️ | Verified: e-Crime covers only crimes within Dubai. The documentation burden is unverified; 901, the Dubai Police app and police stations are alternatives. |
| F32 | 3.4 billion phishing messages sent daily | ✅ | Quoted by the CSC (Khaleej Times). It is a global industry estimate, not UAE telemetry. |

### 3.3 Contradictions inside and between the two files

1. **Three incompatible ‘share of attacks that are social engineering’ numbers:** 98% (SRS), 75% (brief, CSC) and 90% (brief, Conflict Advisory). They use different denominators (attacks, breaches, successful breaches). Lead with 75% of breaches (CSC) and name the denominator. Treat 98% as a campaign claim.
2. **30% vs 79% reporting.** The SRS says 30% report to law enforcement (2024, all respondents). The brief says 79% of those who experienced a scam reported to some entity (2026). Present both with their bases.
3. **‘Systemic under-reporting’ vs 79% reporting.** The narrative holds for law enforcement and for zero-loss cases, not for reporting in general.
4. **‘Most reports go to banks after loss’** (brief): no figure in any source I retrieved.
5. **Date drift:** Visa is dated March 2025, June 2026 and ‘2024/2025’ in different places, and one of its figures is from 2023.
6. **Blank sample sizes:** four table cells hold broken image placeholders instead of n-values. GASA n = 1,000; Visa 5,800 (17 markets), 300 (UAE).
7. **Source quality:** 4 of 30 citations are Facebook posts; others are vendor blogs and aggregators.

## 4. Concept and logic validation

### 4.1 What holds up

- **Problem evidence is real.** WhatsApp is the most popular scam-delivery platform in the UAE (GASA 2024). 18% do not know where to report. Half of those who reported saw no action or were unsure (GASA 2026).
- **Single-purpose bot** matches Meta’s January 2026 policy (S9).
- **Layered verification** (allowlist, blocklist, local LLM) and an explicit **abstain path** (NFR-3.2) are sound design instincts.
- **Async FastAPI + Docker** is an adequate stack for the stated load, subject to 4.9.

### 4.2 Critical: data sovereignty versus WhatsApp (NFR-1.1)

- Meta’s On-Premises API stopped delivering messages on 23 Oct 2025. The Cloud API is Meta-hosted; Meta manages the database and media data.
- Cloud API Local Storage offers UAE as a data-at-rest region. With it enabled, data-in-use is held up to 60 minutes, and one BSP’s documentation says content may sit in Meta data centres internationally during processing. Without it, defaults differ by source (US per Infobip; Germany per Clickatell).
- Every citizen message therefore transits Meta infrastructure outside Hares’ control. NFR-1.1 as written is false on day one.
- **Fix:** reword to ‘all processing performed by Hares (AI inference, storage, telemetry) occurs on UAE infrastructure; message transport is operated by Meta; UAE Local Storage is enabled; no Hares data is sent to any third-party AI API.’ Disclose this in the bot’s first message. Get a legal review of the Meta transit; I am not a lawyer.

### 4.3 Critical: audio deepfake module (FR-1.x, NFR-3.1)

**Threat-model mismatch (my analysis).** The brief’s voice-clone examples are live calls and ‘wrong number’ voice notes used to harvest samples. A citizen cannot forward a live call. Any recording is narrowband telephony audio, then re-compressed by WhatsApp. The module covers a slice of the threat, so the SRS should say which slice.

**Detector performance in the literature** (secondary summaries; I did not re-run these):

- Best single system on ASVspoof 5 test: 5.56% EER (reported in arXiv 2507.01750).
- Lab-trained models on the In-the-Wild set: 24.7% EER (ASSERT+LPS) and 34.8% EER (AASIST).
- Codec compression costs about 5.3 EER points on average (one summary).
- Models under 1% EER in the lab can reach 30–60% EER in the wild (aggregator summary, weaker source).

None of this approaches a 0.1% false-positive rate at useful recall without in-domain calibration.

**Conformal calibration (FR-1.4) does not improve the detector.** It sets thresholds, assuming calibration and deployment data are exchangeable. UAE traffic will not be: Gulf Arabic, Hindi, Urdu and other languages, WhatsApp Opus compression, new synthesis tools. Numbers (🧪, computed from standard conformal theory):

| Calibration clips (n) | Chance the realized FPR is ≤ 0.1% | 95th-percentile realized FPR |
| --- | --- | --- |
| 999 (minimum for α = 0.1%) | 63.2% | 0.299% |
| 2,999 | 57.7% | 0.210% |
| 9,999 | 54.2% | 0.157% |
| 29,999 | 52.4% | 0.132% |

The guarantee holds on average over calibration sets, not for your one deployed set. About half the time the realized FPR exceeds the target. To *demonstrate* FPR below 0.1%, you need 2,995 genuine test clips with zero false alarms (95% confidence) or 4,603 (99%) (🧪).

**Illustrative trade-off** (🧪, equal-variance Gaussian model; real ROC curves are not Gaussian): recall at 0.1% FPR for a detector with a given EER.

| Detector EER | Recall at 0.1% FPR |
| --- | --- |
| 1% | 94% |
| 5% | 58% |
| 10% | 30% |
| 20% | 8% |

**Fix:** state NFR-3.1 as a measured target with a confidence bound, reported per language and codec, and report *recall at 0.1% FPR*, not EER. Default audio to ‘inconclusive: verify by calling the official source’ unless the score clears a high-confidence threshold.

### 4.4 Text and link verification (FR-2.x)

- No published benchmark for Gulf-Arabic/English smishing intent classification at 0.1% FPR turned up in my searches (absence of evidence, not proof). Treat the target as unproven.
- Let deterministic checks (allowlist, blocklist, domain age, lookalike and IDN homograph detection) carry high-confidence verdicts. Use the LLM only for the ‘suspicious’ band.
- **Allowlist defect (FR-2.2).** A strict .gov.ae suffix rule would flag legitimate official or semi-official domains. Sources I retrieved list **ecrime.ae** (the Dubai Police e-Crime portal) and **salik.ae**. FR-3.2 itself sends users to e-Crime. Use a curated list of exact registrable domains with an owner and a review date.

### 4.5 Verdict semantics and abuse (FR-3.1, NFR-1.3)

- **‘Binary’ conflicts with abstention.** FR-3.1 requires two outcomes; NFR-3.2 requires an uncertain outcome. Define three states.
- **A green result will read as ‘safe’.** New scam templates are novel by design, so ‘no known threat’ is least reliable exactly when it matters. Default to amber wording (‘not found in known-threat lists; still verify by calling the official number’).
- **NFR-1.3 targets the wrong problem.** Rejecting ‘zero-entropy generations’ does not stop an attacker iterating a template until it turns green, which is the real risk. Controls that do: per-number rate limits, no feature-level explanations on green or amber, canary templates, delayed or merged verdicts on near-duplicate resubmissions.

### 4.6 PII versus indicators (FR-4.1)

The statistics brief promises to harvest scammer phone numbers, domains, wallets and IPs, while FR-4.1 strips PII before storage. Split the data into two classes:

- **Scammer-controlled identifiers** (sender number, URL, domain, wallet): this is the intelligence. Retain under a stated legal basis.
- **Citizen identifiers** (submitter number, names, Emirates ID, OTPs, IBANs): salted-hash or drop; redact before logs.
- Test redaction recall on mixed Arabic/English text. Pattern-based PII removal is error-prone there.

### 4.7 Problem framing

The claim that residents lack a frictionless tool is overstated. Existing channels: 901 and ecrime.ae (Dubai), Aman 800-2626 / SMS 2828 (Abu Dhabi), Najeed 800151 / SMS 7999 (Sharjah), the Dubai Police Anti-Fraud Centre, and private analyser sites (for example isthisascam.to). The defensible gap is **pre-loss triage with a feedback loop and aggregate intelligence**. Reframe the problem statement around that.

### 4.8 Legal basis (NFR-1.2)

- The PDPL excludes government data and government entities from its scope. If a Dubai government entity operates Hares, the PDPL may not be the governing instrument. Dubai’s Information Security Regulation and AI Security Policy (both named by Dubai Future Foundation in the accelerator launch) are the likely frameworks, with DESC as regulator. Confirm with counsel.
- Executive Regulations status is **contradictory in secondary sources** (some say still pending as of Feb 2026, others say issued in 2026). Unresolved; check the UAE Data Office directly.
- Do not state ‘complies with the PDPL’ as the sole compliance claim.

### 4.9 Performance and uptime (NFR-2.x)

- Cloud API throughput counts inbound and outbound together: 80 messages/second per number by default, up to 1,000 by automatic upgrade if eligible.
- 🧪 Little’s law: 1,000 concurrent queries × 5 s each = 200 queries/s = 400 messages/s (one inbound and one outbound each). The default cap of 80 mps supports about 40 queries/s, or roughly 200 concurrent at 5 s. The requirement needs the 1,000-mps tier, and the real bottleneck is GPU inference within the 5-second target, not FastAPI.
- 99.9% uptime means 8.76 hours of downtime per year. Meta’s availability is outside your control, so scope the SLO to Hares components.
- FR-3.1: acknowledge the webhook immediately and send the verdict as a separate message.

### 4.10 Model choice (🔶 background knowledge, not searched)

The SRS names ‘Llama 3 derivatives’. UAE-origin open-weight models (TII’s Falcon family, Jais from Inception/MBZUAI) are natural candidates for Gulf Arabic and for the sovereignty narrative. Benchmark them against Llama-based models on your own labelled Arabic/English smishing set rather than assuming either.

### 4.11 Reasoning leaps in the statistics brief

- 61% ‘improper usage’ is presented as proof of social engineering (F7).
- The 52% share-of-reasons is turned into a share-of-population (F21).
- ‘Humans are increasingly incapable of distinguishing AI audio’ has no source.
- The ‘knowledgeable users respond more’ finding is a self-reported hypothetical (F13).
- ‘Empirical necessity’ overreaches. The evidence supports the need for better triage, not this specific design.
- ‘Block at national ISP level’ requires TDRA integration that the SRS does not specify.

## 5. Figures safe to use in a pitch

| Claim | Source | Date | Sample / basis |
| --- | --- | --- | --- |
| 75% of UAE cyber breaches originate in phishing emails and fraudulent messages | UAE Cyber Security Council (via Khaleej Times) | 16 Jul 2026 | Official statement |
| 70% encountered a scam; about one every three days (GASA: 111/yr); 1 in 3 lost money | GASA / Trend Micro | 27 Jan 2026 | n = 1,000; self-reported |
| 79% of those who experienced a scam reported at least one incident; half of reporters saw no action or were unsure; no financial loss was the top reason for not reporting (52%, base per GASA wording) | GASA / Trend Micro | 27 Jan 2026 | n = 1,000 |
| 56% face scam attempts monthly; 30% reported to law enforcement; 18% don’t know where to report | GASA / BioCatch / CSC / TRENDS | 28 Nov 2024 | n = 1,964 |
| 49% say they have fallen for a scam (15% repeatedly) | Visa Stay Secure | Fieldwork Dec 2024; published 18 Mar 2025 | n = 300 UAE |
| UAE ranked 6th for customers most frequently impacted by cyber activity | Microsoft Digital Defence Report | H1 2026; reported 2 Oct 2026 | Microsoft customer telemetry |
| Average loss AED 3,250 per affected individual, up from AED 880 in 2022 | Adyen UAE Retail Report 2024 | 23 Apr 2024 | 2023 data; payments-fraud victims |
| 103 fraudulent social accounts shut in Q2 2026 | Dubai Police | 3 Aug 2026 | Official statement |
| CBUAE Notice 3057: SMS/email OTP phase-out by 31 Mar 2026 | Central Bank of the UAE | 23 May 2025 | Regulation |

## 6. Recommended SRS changes

| Requirement | Problem | Proposed change |
| --- | --- | --- |
| NFR-1.1 | Impossible on WhatsApp | Scope to Hares-controlled processing; enable UAE Local Storage; disclose Meta transit (4.2) |
| FR-1.4 / NFR-3.1 | Unsupported FPR target; the conformal guarantee is average-case | Measured target with a confidence bound; at least 3,000 genuine test clips per language and codec; report recall at 0.1% FPR (4.3) |
| FR-3.1 vs NFR-3.2 | Binary vs abstain | Three states; amber default (4.5) |
| FR-2.2 | The .gov.ae suffix rule flags ecrime.ae | Curated exact-domain allowlist with owner and review date (4.4) |
| FR-4.1 | Contradicts IOC harvesting | Two data classes: scammer identifiers kept, citizen identifiers hashed or dropped (4.6) |
| NFR-1.3 | Wrong control | Rate limits, opaque green/amber, near-duplicate handling (4.5) |
| NFR-1.2 | PDPL may not apply to government operators | Name the governing framework with counsel (4.8) |
| NFR-2.1 | Ignores the 80-mps cap | Specify the 1,000-mps tier and the GPU capacity plan (4.9) |
| NFR-2.2 | Depends on Meta’s uptime | Scope the SLO to Hares components |
| Problem statement | Overstates the lack of tools | Reframe around pre-loss triage and feedback (4.7) |
| *New* | No evaluation protocol | Add test sets (genuine UAE audio and text, adversarial set, per-language, per-codec) and abuse handling |

## 7. My calculations (🧪)

1. **Arithmetic checks:** 365 ÷ 3 = 121.7; 3,250 ÷ 880 − 1 = +269.3%; $283 × 3.6725 = AED 1,039; $2.9M × 3.6725 = AED 10.65M; 99.9% uptime = 8.76 h/year (43.2 min/month).
2. **Conformal realized-FPR table (4.3):** realized false-positive rate modelled as Beta(l, n + 1 − l) with l = floor((n + 1) × 0.001), the standard split-conformal result. Zero-failure sample sizes: n ≥ ln(0.05) / ln(0.999) = 2,995 (95%) and 4,603 (99%).
3. **Recall at 0.1% FPR (4.3):** equal-variance Gaussian model, d′ = 2 × z(1 − EER), recall = Φ(d′ − z(0.999)). Illustrative only.
4. **Throughput (4.9):** Little’s law, concurrency ÷ latency.

For reference, at an FPR of 0.1% / 1% / 5%, every 1,000,000 genuine queries produce 1,000 / 10,000 / 50,000 false alarms. The 1,000,000 is an illustrative volume, not a forecast.

## 8. Sources retrieved

- GASA, ‘Scams Hit UAE Residents Every Three Days’ (27 Jan 2026); GASA UAE report page
- WAM, ‘2024 State of Scams in UAE’ (28 Nov 2024); GASA/BioCatch 2024 report page
- WAM, ‘98% of attacks exploit human error’ (21 Sep 2025); Khaleej Times (16 Jul 2026); menastartupdigest (75% CSC)
- The National and Gulf News (Microsoft Digital Defence Report, 2 Oct 2026); TechRepublic (640,000); meatechwatch (Feb 2026 CSC range)
- Visa Middle East press releases (18 Mar 2025; 27 Nov 2023)
- WAM (CPX–CSC report, 25 Feb 2025); Adyen via Arabian Business, TradeArabia, IBS Intelligence (23 Apr 2024)
- Khaleej Times, Gulf News, Emirates247, The National, TRT (Dubai Police, Aug 2026)
- Descope, Onlayer, FacePhi, Sardine (CBUAE Notice 3057)
- WAM, The National, Gulf News (Agentic AI accelerator, 5 Oct 2026); WAM and Dubai Media Office (AI Infrastructure Empowerment Platform, Oct 2025)
- Meta Cloud API documentation as mirrored by Infobip, Clickatell, 360dialog, chatarchitect (throughput, Local Storage, On-Premises sunset); respond.io, Dataslayer, The Daily Star (WhatsApp AI policy)
- arXiv 2507.01750, ISCA ASVspoof 2024 (Schäfer et al.), ResearchGate and emergentmind summaries (detector performance)
- Simmons & Simmons, CookieYes, Modulos, Primerus, Kayrouz & Associates, CyberSigma (PDPL)
- Gulf News, Bayut, Al Ansari Exchange, NBF (reporting channels)
