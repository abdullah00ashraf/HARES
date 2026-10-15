"""
Project Hares: Dynamic PowerPoint Presentation Compiler
Generates a professional 16:9 widescreen PowerPoint deck (.pptx) based on Section 7 of project.md.
Features dynamic styling, card layouts, KPI stat callouts, embedded audit figures,
and verbatim speaker notes on every slide.
"""

import os
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

DOCS_DIR = Path("C:/HARES/docs")
FIGURES_DIR = DOCS_DIR / "figures"
OUTPUT_PPTX = DOCS_DIR / "Project_Hares_Executive_Presentation.pptx"

# Color Palette Constants
COLOR_DARK_BG = RGBColor(11, 19, 43)        # #0B132B - Deep Navy
COLOR_DARK_CARD = RGBColor(22, 33, 62)      # #16213E - Deep Slate
COLOR_WHITE = RGBColor(255, 255, 255)
COLOR_LIGHT_BG = RGBColor(248, 250, 252)    # #F8FAFC - Light Slate
COLOR_LIGHT_CARD = RGBColor(255, 255, 255)
COLOR_BORDER = RGBColor(226, 232, 240)      # #E2E8F0
COLOR_TEXT_PRIMARY = RGBColor(15, 23, 42)   # #0F172A - Slate 900
COLOR_TEXT_SECONDARY = RGBColor(71, 85, 105)# #475569 - Slate 600
COLOR_EMERALD = RGBColor(5, 150, 105)       # #059669 - Sovereign Green
COLOR_AMBER = RGBColor(217, 119, 6)         # #D97706 - Sovereign Gold/Amber
COLOR_CRIMSON = RGBColor(220, 38, 38)       # #DC2626 - High Threat Alert
COLOR_BLUE = RGBColor(37, 99, 235)          # #2563EB - Tech Blue
COLOR_NAVY = RGBColor(11, 27, 61)           # #0B1B3D - Deep Corporate Navy

def set_slide_background(slide, prs, rgb_color):
    """Fills slide background with a solid color."""
    background = slide.background
    fill = background.fill
    fill.solid()
    fill.fore_color.rgb = rgb_color

def add_header(slide, title_text: str, category_text: str = "PROJECT HARES (مشروع حارس)", is_dark: bool = False):
    """Adds a standardized clean header to content slides."""
    header_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.5), Inches(11.7), Inches(1.1))
    tf = header_box.text_frame
    tf.word_wrap = True
    tf.margin_top = Inches(0)
    tf.margin_left = Inches(0)

    # Category Tracker
    p_cat = tf.paragraphs[0]
    p_cat.text = category_text.upper()
    p_cat.font.name = "Calibri"
    p_cat.font.size = Pt(10)
    p_cat.font.bold = True
    p_cat.font.color.rgb = COLOR_EMERALD if is_dark else COLOR_BLUE
    p_cat.space_after = Pt(4)

    # Slide Title
    p_title = tf.add_paragraph()
    p_title.text = title_text
    p_title.font.name = "Calibri"
    p_title.font.size = Pt(24)
    p_title.font.bold = True
    p_title.font.color.rgb = COLOR_WHITE if is_dark else COLOR_TEXT_PRIMARY

def add_speaker_notes(slide, notes_text: str):
    """Attaches verbatim speaker notes to the slide."""
    notes_slide = slide.notes_slide
    text_frame = notes_slide.notes_text_frame
    text_frame.text = notes_text.strip()

def create_presentation():
    prs = Presentation()
    # 16:9 Widescreen standard
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    # =========================================================================
    # SLIDE 1: TITLE SLIDE (SOVEREIGN SENTINEL)
    # =========================================================================
    s1 = prs.slides.add_slide(blank_layout)
    set_slide_background(s1, prs, COLOR_DARK_BG)

    # Sovereign Accent Banner
    banner = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.2), Inches(11.733), Inches(0.4))
    banner.fill.solid()
    banner.fill.fore_color.rgb = COLOR_EMERALD
    banner.line.color.rgb = COLOR_EMERALD
    tb = banner.text_frame
    tb.text = "EMIRATE OF DUBAI • MUNICIPAL CYBERSECURITY • SOVEREIGN DEFENSE PLATFORM"
    tb.paragraphs[0].font.size = Pt(10)
    tb.paragraphs[0].font.bold = True
    tb.paragraphs[0].font.color.rgb = COLOR_WHITE
    tb.paragraphs[0].alignment = PP_ALIGN.CENTER

    # Main Title Box
    tbox = s1.shapes.add_textbox(Inches(0.8), Inches(2.0), Inches(11.733), Inches(3.0))
    tf1 = tbox.text_frame
    tf1.word_wrap = True

    p1 = tf1.paragraphs[0]
    p1.text = "PROJECT HARES (مشروع حارس)"
    p1.font.name = "Calibri"
    p1.font.size = Pt(44)
    p1.font.bold = True
    p1.font.color.rgb = COLOR_WHITE
    p1.space_after = Pt(12)

    p2 = tf1.add_paragraph()
    p2.text = "Autonomous Sovereign Multi-Modal Fraud Triage & Threat Intelligence System"
    p2.font.name = "Calibri"
    p2.font.size = Pt(20)
    p2.font.color.rgb = COLOR_AMBER
    p2.space_after = Pt(18)

    p3 = tf1.add_paragraph()
    p3.text = "Production Verified • DESC ISR v2.0 • Digital Dubai AI Ethics • Conformal Error Bounded (≤ 0.1%)"
    p3.font.name = "Calibri"
    p3.font.size = Pt(12)
    p3.font.color.rgb = RGBColor(148, 163, 184) # Slate 400

    # Live Badge Card
    badge = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(5.8), Inches(11.733), Inches(0.8))
    badge.fill.solid()
    badge.fill.fore_color.rgb = COLOR_DARK_CARD
    badge.line.color.rgb = COLOR_BORDER
    btf = badge.text_frame
    btf.text = "Live Deployments: Vercel Edge Portal (hares-wheat.vercel.app) | API Gateway (hares-api.onrender.com) | HF ZeroGPU A10G"
    btf.paragraphs[0].font.size = Pt(11)
    btf.paragraphs[0].font.color.rgb = COLOR_WHITE
    btf.paragraphs[0].alignment = PP_ALIGN.CENTER

    add_speaker_notes(
        s1,
        "Good morning, esteemed colleagues and leadership. Today, I am proud to present Project Hares—"
        "Dubai's sovereign, automated fraud triage and threat intelligence system. In an era where social "
        "engineering and deepfake scams weaponize local trust, Project Hares provides an instantaneous, "
        "privacy-preserving defense shield for every citizen and resident."
    )

    # =========================================================================
    # SLIDE 2: THE THREAT LANDSCAPE
    # =========================================================================
    s2 = prs.slides.add_slide(blank_layout)
    set_slide_background(s2, prs, COLOR_LIGHT_BG)
    add_header(s2, "The Dubai Cyber Threat Landscape: The Urgency in Numbers")

    cards_data_s2 = [
        ("60% of Reported Lures", "MUNICIPAL IMPERSONATION", "Attackers weaponize trust via fake Salik toll alerts and Dubai Police legal summonses demanding immediate fines.", COLOR_CRIMSON),
        ("Sub-180ms Exploits", "AI VOICE CLONING", "WhatsApp voice notes generated by neural vocoders impersonate family members and executives in high-panic scenarios.", COLOR_AMBER),
        ("15-Min Response Gap", "CITIZEN VULNERABILITY", "Victims comply within 15 minutes of receiving a threat, while traditional manual reporting takes 24 to 48 hours.", COLOR_BLUE),
    ]

    for i, (stat, title, desc, col) in enumerate(cards_data_s2):
        left = Inches(0.8 + i * 4.0)
        card = s2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, Inches(2.0), Inches(3.7), Inches(4.7))
        card.fill.solid()
        card.fill.fore_color.rgb = COLOR_LIGHT_CARD
        card.line.color.rgb = col
        card.line.width = Pt(2)

        ctf = card.text_frame
        ctf.word_wrap = True
        ctf.margin_left = Inches(0.3)
        ctf.margin_right = Inches(0.3)
        ctf.margin_top = Inches(0.4)

        cp1 = ctf.paragraphs[0]
        cp1.text = stat
        cp1.font.size = Pt(22)
        cp1.font.bold = True
        cp1.font.color.rgb = col
        cp1.space_after = Pt(12)

        cp2 = ctf.add_paragraph()
        cp2.text = title
        cp2.font.size = Pt(12)
        cp2.font.bold = True
        cp2.font.color.rgb = COLOR_TEXT_PRIMARY
        cp2.space_after = Pt(14)

        cp3 = ctf.add_paragraph()
        cp3.text = desc
        cp3.font.size = Pt(11)
        cp3.font.color.rgb = COLOR_TEXT_SECONDARY
        cp3.line_spacing = 1.2

    add_speaker_notes(
        s2,
        "Threat actors in the UAE are no longer sending generic spam. They send hyper-targeted, Arabic and "
        "English lures impersonating Salik, Dubai Police, and the Central Bank. A victim panics and clicks within "
        "minutes. Traditional municipal reporting queues that take days are fundamentally obsolete."
    )

    # =========================================================================
    # SLIDE 3: OUR CORE MANDATES (THE 5 INVARIANTS)
    # =========================================================================
    s3 = prs.slides.add_slide(blank_layout)
    set_slide_background(s3, prs, COLOR_LIGHT_BG)
    add_header(s3, "Sovereign System Architecture: The Five Core Invariants")

    invariants = [
        ("1. SUB-SECOND INGRESS", "3.5ms Webhook ACK & immediate HTTP 200; <3s full multi-modal neural verdict.", COLOR_BLUE),
        ("2. 100% DATA SOVEREIGNTY", "100% on-premise execution; zero resident telemetry dispatched to offshore commercial APIs.", COLOR_EMERALD),
        ("3. ZERO CITIZEN PII RETENTION", "Class B phone numbers hashed via HMAC-SHA256 (32B salt); raw strings purged from RAM.", COLOR_AMBER),
        ("4. BOUNDED ERROR RATE (≤ 0.1%)", "Non-parametric Conformal Prediction guarantees False Positive Rate ≤ 0.1% at 95% confidence.", COLOR_CRIMSON),
        ("5. DUBAI POLICE ESCALATION", "Automated synchronization of verified Class A threat indicators with Dubai Police e-Crime & 901.", COLOR_NAVY),
    ]

    for i, (title, detail, col) in enumerate(invariants):
        top = Inches(1.8 + i * 1.0)
        box = s3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), top, Inches(11.733), Inches(0.85))
        box.fill.solid()
        box.fill.fore_color.rgb = COLOR_WHITE
        box.line.color.rgb = col
        box.line.width = Pt(1.5)

        btf = box.text_frame
        btf.word_wrap = True
        btf.margin_left = Inches(0.3)
        btf.margin_top = Inches(0.15)

        p1 = btf.paragraphs[0]
        p1.text = title
        p1.font.size = Pt(13)
        p1.font.bold = True
        p1.font.color.rgb = col

        p2 = btf.add_paragraph()
        p2.text = detail
        p2.font.size = Pt(10.5)
        p2.font.color.rgb = COLOR_TEXT_SECONDARY

    add_speaker_notes(
        s3,
        "We engineered Project Hares on five uncompromised engineering pillars. We guarantee that no resident "
        "data ever leaves UAE sovereignty, no citizen phone numbers are stored in plain text, and our mathematical "
        "error rate is bounded strictly to 0.1%."
    )

    # =========================================================================
    # SLIDE 4: END-TO-END MULTI-MODAL INTAKE
    # =========================================================================
    s4 = prs.slides.add_slide(blank_layout)
    set_slide_background(s4, prs, COLOR_LIGHT_BG)
    add_header(s4, "Multi-Modal Citizen Verification: 4 Unified Ingress Vectors")

    modes = [
        ("Forwarded Text & SMS", "Bilingual text processing handling Emirati Gulf Arabic, Modern Standard Arabic (MSA), Expat English, and Arabizi SMS slang.", "Qwen2.5-3B + Colang 2.0"),
        ("Link & Domain Inspector", "Deep domain extraction, exact allowlist matching, IDN homoglyph punycode decoding, and lookalike detection.", "uts46 / tldextract"),
        ("Voice Note / Audio", "WhatsApp 16kHz mono Opus decoding, feature extraction, and neural deepfake classification for synthetic voice cloning.", "Whisper Dual-Head"),
        ("Screenshot Image OCR", "Optical Character Recognition extracting bilingual Arabic/English text from captured SMS notifications and spoofed portals.", "TrOCR / Tesseract"),
    ]

    for i, (m_title, m_desc, m_engine) in enumerate(modes):
        col_idx = i % 2
        row_idx = i // 2
        left = Inches(0.8 + col_idx * 6.0)
        top = Inches(1.8 + row_idx * 2.6)

        card = s4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, Inches(5.7), Inches(2.3))
        card.fill.solid()
        card.fill.fore_color.rgb = COLOR_WHITE
        card.line.color.rgb = COLOR_BORDER

        ctf = card.text_frame
        ctf.word_wrap = True
        ctf.margin_left = Inches(0.3)
        ctf.margin_top = Inches(0.25)

        p1 = ctf.paragraphs[0]
        p1.text = m_title
        p1.font.size = Pt(16)
        p1.font.bold = True
        p1.font.color.rgb = COLOR_NAVY
        p1.space_after = Pt(6)

        p2 = ctf.add_paragraph()
        p2.text = m_desc
        p2.font.size = Pt(10.5)
        p2.font.color.rgb = COLOR_TEXT_SECONDARY
        p2.space_after = Pt(8)

        p3 = ctf.add_paragraph()
        p3.text = f"Engine: {m_engine}"
        p3.font.size = Pt(9.5)
        p3.font.bold = True
        p3.font.color.rgb = COLOR_EMERALD

    add_speaker_notes(
        s4,
        "Citizens interact with fraud across multiple mediums. Hares accepts forwarded text messages, URLs, raw voice "
        "notes, and screenshots, unifying them into a single automated pipeline with sub-second execution guarantees."
    )

    # =========================================================================
    # SLIDE 5: DETERMINISTIC VERIFICATION ENGINE
    # =========================================================================
    s5 = prs.slides.add_slide(blank_layout)
    set_slide_background(s5, prs, COLOR_LIGHT_BG)
    add_header(s5, "The First Line of Defense: Deterministic Verification (<15ms)")

    # Left Card: Allowlist
    left_card = s5.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.8), Inches(5.6), Inches(5.0))
    left_card.fill.solid()
    left_card.fill.fore_color.rgb = COLOR_WHITE
    left_card.line.color.rgb = COLOR_EMERALD
    left_card.line.width = Pt(2)
    ltf = left_card.text_frame
    ltf.word_wrap = True
    ltf.margin_left = Inches(0.4)
    ltf.margin_top = Inches(0.3)

    lp1 = ltf.paragraphs[0]
    lp1.text = "OFFICIAL GOVERNMENT ALLOWLIST"
    lp1.font.size = Pt(16)
    lp1.font.bold = True
    lp1.font.color.rgb = COLOR_EMERALD
    lp1.space_after = Pt(12)

    lp2 = ltf.add_paragraph()
    lp2.text = "• Instant GREEN Verdict (<15ms Execution)\n• Authenticates against Sovereign UAE Registry\n• Covers .gov.ae, .police.gov.ae, dewa.gov.ae, salik.ae\n• Zero neural inference required on known authentic portals\n• Delivers instant peace of mind to citizens"
    lp2.font.size = Pt(11)
    lp2.font.color.rgb = COLOR_TEXT_SECONDARY
    lp2.line_spacing = 1.3

    # Right Card: Homoglyph Radar
    right_card = s5.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.9), Inches(1.8), Inches(5.6), Inches(5.0))
    right_card.fill.solid()
    right_card.fill.fore_color.rgb = COLOR_WHITE
    right_card.line.color.rgb = COLOR_CRIMSON
    right_card.line.width = Pt(2)
    rtf = right_card.text_frame
    rtf.word_wrap = True
    rtf.margin_left = Inches(0.4)
    rtf.margin_top = Inches(0.3)

    rp1 = rtf.paragraphs[0]
    rp1.text = "HOMOGLYPH & PUNYCODE RADAR"
    rp1.font.size = Pt(16)
    rp1.font.bold = True
    rp1.font.color.rgb = COLOR_CRIMSON
    rp1.space_after = Pt(12)

    rp2 = rtf.add_paragraph()
    rp2.text = "• Instant RED Verdict (<32ms Execution)\n• Inspects Unicode IDN cross-script mixing\n• Detects Cyrillic 'а' replacing Latin 'a' in 'dewa.gov.ae'\n• Decodes deceptive 'xn--' Punycode strings\n• Intercepts malicious .cc, .top, .xyz phishing domains\n• One-click dispatch to TDRA ISP DNS sinkholing"
    rp2.font.size = Pt(11)
    rp2.font.color.rgb = COLOR_TEXT_SECONDARY
    rp2.line_spacing = 1.3

    add_speaker_notes(
        s5,
        "Before waking up heavy neural models, our deterministic engine inspects URLs. Official government sites "
        "are verified instantly in 15 milliseconds. Deceptive Cyrillic lookalikes and fake .cc domains are "
        "intercepted and neutralized on the spot."
    )

    # =========================================================================
    # SLIDE 6: SOVEREIGN NEURAL ENGINE (LOCAL SLM & ZEROGPU)
    # =========================================================================
    s6 = prs.slides.add_slide(blank_layout)
    set_slide_background(s6, prs, COLOR_LIGHT_BG)
    add_header(s6, "Sovereign Neural Engine: Qwen2.5-3B + Colang 2.0 Guardrails")

    s6_cards = [
        ("Fine-Tuned Qwen2.5-3B-Instruct", "Trained via QLoRA (Rank=16, Alpha=32) on localized UAE smishing lures, traffic fine notifications, and Arabizi dialects. Merged to FP16 SafeTensors (3.09B params).", COLOR_BLUE),
        ("NVIDIA NeMo Guardrails", "Colang 2.0 policy execution screening against ChatML breakouts, system overrides, and citizen PII leaks before model generation.", COLOR_EMERALD),
        ("Pydantic v2 Contract Output", "Guided decoding locks JSON structure into strict closed contracts (is_impersonation, urgency, financial_demand, detected_tactics).", COLOR_AMBER),
    ]

    for i, (title, desc, col) in enumerate(s6_cards):
        top = Inches(1.8 + i * 1.7)
        card = s6.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), top, Inches(11.733), Inches(1.4))
        card.fill.solid()
        card.fill.fore_color.rgb = COLOR_WHITE
        card.line.color.rgb = col
        card.line.width = Pt(1.5)

        ctf = card.text_frame
        ctf.word_wrap = True
        ctf.margin_left = Inches(0.3)
        ctf.margin_top = Inches(0.2)

        p1 = ctf.paragraphs[0]
        p1.text = title
        p1.font.size = Pt(15)
        p1.font.bold = True
        p1.font.color.rgb = col
        p1.space_after = Pt(4)

        p2 = ctf.add_paragraph()
        p2.text = desc
        p2.font.size = Pt(11)
        p2.font.color.rgb = COLOR_TEXT_SECONDARY

    add_speaker_notes(
        s6,
        "When complex semantic analysis is required, our fine-tuned Qwen2.5-3B engine on ZeroGPU A10G "
        "analyzes the lure. Wrapped in Colang 2.0 guardrails, it strips citizen PII and enforces a strict JSON "
        "output format, preventing model hallucination."
    )

    # =========================================================================
    # SLIDE 7: ACOUSTIC DEEPFAKE CLASSIFIER (WITH EMBEDDED FIGURE)
    # =========================================================================
    s7 = prs.slides.add_slide(blank_layout)
    set_slide_background(s7, prs, COLOR_LIGHT_BG)
    add_header(s7, "Acoustic Deepfake Classifier: ASVspoof 2021 DF Evaluation")

    # Left text box
    tbox_s7 = s7.shapes.add_textbox(Inches(0.8), Inches(1.8), Inches(6.0), Inches(5.0))
    stf = tbox_s7.text_frame
    stf.word_wrap = True

    sp1 = stf.paragraphs[0]
    sp1.text = "Whisper Dual-Head Feature Extractor"
    sp1.font.size = Pt(16)
    sp1.font.bold = True
    sp1.font.color.rgb = COLOR_NAVY
    sp1.space_after = Pt(10)

    sp2 = stf.add_paragraph()
    sp2.text = (
        "• 100.0% Detection Rate on 250 synthetic voice clones\n"
        "• 0.00% Equal Error Rate (EER) across WhatsApp Opus audio\n"
        "• 0.0000% False Positive Rate on bonafide human voices\n"
        "• < 180 ms Latency: Single forward-pass Whisper encoder\n"
        "• Detects vocoder phase continuity and spectral roll-off anomalies\n"
        "• Zero degradation under lossy WhatsApp 16kHz compression"
    )
    sp2.font.size = Pt(11.5)
    sp2.font.color.rgb = COLOR_TEXT_SECONDARY
    sp2.line_spacing = 1.3

    # Right: Embed Figure 3
    fig3_path = FIGURES_DIR / "figure3_audio_deepfake_confusion_matrix.png"
    if fig3_path.exists():
        s7.shapes.add_picture(str(fig3_path), Inches(7.2), Inches(1.8), width=Inches(5.3))

    add_speaker_notes(
        s7,
        "Voice cloning is the newest frontier in fraud. Our Whisper Dual-Head architecture inspects the "
        "micro-spectral continuity of the audio signal, detecting synthetic vocoder artifacts in under 180 milliseconds "
        "with zero false alarms."
    )

    # =========================================================================
    # SLIDE 8: DATA SOVEREIGNTY & FR-4.1 PRIVACY
    # =========================================================================
    s8 = prs.slides.add_slide(blank_layout)
    set_slide_background(s8, prs, COLOR_LIGHT_BG)
    add_header(s8, "Cryptographic Data Sovereignty: Class A vs. Class B Separation")

    # Left Box: Class B
    c_b = s8.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.8), Inches(5.6), Inches(4.8))
    c_b.fill.solid()
    c_b.fill.fore_color.rgb = COLOR_WHITE
    c_b.line.color.rgb = COLOR_EMERALD
    c_b.line.width = Pt(2)
    cbtf = c_b.text_frame
    cbtf.word_wrap = True
    cbtf.margin_left = Inches(0.4)
    cbtf.margin_top = Inches(0.3)

    cp1 = cbtf.paragraphs[0]
    cp1.text = "CLASS B: CITIZEN IDENTIFIERS"
    cp1.font.size = Pt(16)
    cp1.font.bold = True
    cp1.font.color.rgb = COLOR_EMERALD
    cp1.space_after = Pt(10)

    cp2 = cbtf.add_paragraph()
    cp2.text = (
        "• Submitter phone numbers, Emirates IDs, personal names\n"
        "• Keyed HMAC-SHA256 with 32-byte secret salt\n"
        "• Cryptographically irreversible pseudonymization\n"
        "• Raw telephone numbers wiped from RAM via try...finally\n"
        "• Compliant with UAE PDPL Federal Decree-Law No. 45"
    )
    cp2.font.size = Pt(11)
    cp2.font.color.rgb = COLOR_TEXT_SECONDARY
    cp2.line_spacing = 1.3

    # Right Box: Class A
    c_a = s8.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.9), Inches(1.8), Inches(5.6), Inches(4.8))
    c_a.fill.solid()
    c_a.fill.fore_color.rgb = COLOR_WHITE
    c_a.line.color.rgb = COLOR_CRIMSON
    c_a.line.width = Pt(2)
    catf = c_a.text_frame
    catf.word_wrap = True
    catf.margin_left = Inches(0.4)
    catf.margin_top = Inches(0.3)

    cap1 = catf.paragraphs[0]
    cap1.text = "CLASS A: THREAT INDICATORS (IoCs)"
    cap1.font.size = Pt(16)
    cap1.font.bold = True
    cap1.font.color.rgb = COLOR_CRIMSON
    cap1.space_after = Pt(10)

    cap2 = catf.add_paragraph()
    cap2.text = (
        "• Scammer URLs, phishing domains, foreign numbers\n"
        "• Persisted in plain text to PostgreSQL threat intelligence\n"
        "• Clustered into STIX 2.1 Threat Campaigns\n"
        "• Synchronized automatically with Dubai Police e-Crime\n"
        "• Exportable for TDRA ISP DNS firewall blocking"
    )
    cap2.font.size = Pt(11)
    cap2.font.color.rgb = COLOR_TEXT_SECONDARY
    cap2.line_spacing = 1.3

    add_speaker_notes(
        s8,
        "Privacy is not an afterthought; it is our architecture. Citizen phone numbers are hashed immediately "
        "and permanently wiped from volatile RAM. Only the scammer's threat indicators are preserved in the "
        "threat intelligence repository."
    )

    # =========================================================================
    # SLIDE 9: EMPIRICAL BENCHMARKS (WITH EMBEDDED FIGURE 1)
    # =========================================================================
    s9 = prs.slides.add_slide(blank_layout)
    set_slide_background(s9, prs, COLOR_LIGHT_BG)
    add_header(s9, "SLM Benchmark Results: 97.16% Recall across 500 UAE Lures")

    tbox_s9 = s9.shapes.add_textbox(Inches(0.8), Inches(1.8), Inches(6.0), Inches(5.0))
    s9tf = tbox_s9.text_frame
    s9tf.word_wrap = True

    p_s9_1 = s9tf.paragraphs[0]
    p_s9_1.text = "Held-Out Evaluation Suite (n=500)"
    p_s9_1.font.size = Pt(16)
    p_s9_1.font.bold = True
    p_s9_1.font.color.rgb = COLOR_NAVY
    p_s9_1.space_after = Pt(10)

    p_s9_2 = s9tf.add_paragraph()
    p_s9_2.text = (
        "• 342 True Positives: Accurately caught criminal scams\n"
        "• 10 False Negatives: High-subtlety novel lures\n"
        "• 97.16% Catch Rate (Recall) on malicious communications\n"
        "• 87.69% F1-Score across localized Arabic/English datasets\n"
        "• 100.0% Prompt Injection Resistance (Meta CyberSecEval)\n"
        "• Zero citizen PII leaked during token generation"
    )
    p_s9_2.font.size = Pt(11.5)
    p_s9_2.font.color.rgb = COLOR_TEXT_SECONDARY
    p_s9_2.line_spacing = 1.3

    fig1_path = FIGURES_DIR / "figure1_slm_confusion_matrix.png"
    if fig1_path.exists():
        s9.shapes.add_picture(str(fig1_path), Inches(7.2), Inches(1.8), width=Inches(5.3))

    add_speaker_notes(
        s9,
        "We do not guess; we measure. Across 500 dialectal tests and 500 acoustic deepfakes, Project Hares "
        "achieved 97.16% text recall, 100% audio spoof detection, and complete immunity against adversarial prompt injection."
    )

    # =========================================================================
    # SLIDE 10: ETHICAL DIALECT EQUITY (WITH EMBEDDED FIGURE 2)
    # =========================================================================
    s10 = prs.slides.add_slide(blank_layout)
    set_slide_background(s10, prs, COLOR_LIGHT_BG)
    add_header(s10, "Digital Dubai Ethical AI Alignment: Dialect Equity Parity (0.91)")

    tbox_s10 = s10.shapes.add_textbox(Inches(0.8), Inches(1.8), Inches(5.8), Inches(5.0))
    s10tf = tbox_s10.text_frame
    s10tf.word_wrap = True

    p_s10_1 = s10tf.paragraphs[0]
    p_s10_1.text = "Multilingual Protection Across Cohorts"
    p_s10_1.font.size = Pt(16)
    p_s10_1.font.bold = True
    p_s10_1.font.color.rgb = COLOR_NAVY
    p_s10_1.space_after = Pt(10)

    p_s10_2 = s10tf.add_paragraph()
    p_s10_2.text = (
        "• Emirati Gulf Arabic: 100.0% Recall (93.6% Accuracy)\n"
        "• Modern Standard Arabic: 100.0% Recall (85.6% Accuracy)\n"
        "• Expat English: 97.7% Recall (74.4% Accuracy)\n"
        "• Arabizi / Social Slang: 90.9% Recall (69.6% Accuracy)\n"
        "• Demographic Disparity Ratio = 0.91 (Mandate ≥ 0.80)\n"
        "• Guarantees equal protection across all resident demographics"
    )
    p_s10_2.font.size = Pt(11)
    p_s10_2.font.color.rgb = COLOR_TEXT_SECONDARY
    p_s10_2.line_spacing = 1.3

    fig2_path = FIGURES_DIR / "figure2_dialect_performance_breakdown.png"
    if fig2_path.exists():
        s10.shapes.add_picture(str(fig2_path), Inches(6.8), Inches(1.8), width=Inches(5.7))

    add_speaker_notes(
        s10,
        "Dubai is a global melting pot. In compliance with Digital Dubai AI Ethics guidelines, our dialect parity "
        "ratio is 0.91, ensuring equal protection across Emirati citizens, Arab residents, and the international expatriate community."
    )

    # =========================================================================
    # SLIDE 11: SYSTEM LATENCY & SLA COMPLIANCE (WITH EMBEDDED FIGURE 4)
    # =========================================================================
    s11 = prs.slides.add_slide(blank_layout)
    set_slide_background(s11, prs, COLOR_LIGHT_BG)
    add_header(s11, "Subsystem Latency Profile: Fast Webhooks & Sub-3s Triage")

    tbox_s11 = s11.shapes.add_textbox(Inches(0.8), Inches(1.8), Inches(5.8), Inches(5.0))
    s11tf = tbox_s11.text_frame
    s11tf.word_wrap = True

    p_s11_1 = s11tf.paragraphs[0]
    p_s11_1.text = "SLA Compliance Breakdown"
    p_s11_1.font.size = Pt(16)
    p_s11_1.font.bold = True
    p_s11_1.font.color.rgb = COLOR_NAVY
    p_s11_1.space_after = Pt(10)

    p_s11_2 = s11tf.add_paragraph()
    p_s11_2.text = (
        "• Webhook Ingress (FR-3.3): 3.5ms P99 (Budget: 500ms)\n"
        "• Allowlist / Homoglyph Radar: 32ms P99 (Budget: 50ms)\n"
        "• Client Offline Fallback: 120ms (Instant Resilience)\n"
        "• Acoustic Inference: 178ms (Budget: 180ms)\n"
        "• ZeroGPU Neural Triage: 2.86s P99 (Budget: 5.0s)\n"
        "• End-to-End Citizen Triage: 3.1s P50 (Budget: 6.0s)"
    )
    p_s11_2.font.size = Pt(11)
    p_s11_2.font.color.rgb = COLOR_TEXT_SECONDARY
    p_s11_2.line_spacing = 1.3

    fig4_path = FIGURES_DIR / "figure4_system_latency_distribution.png"
    if fig4_path.exists():
        s11.shapes.add_picture(str(fig4_path), Inches(6.8), Inches(1.8), width=Inches(5.7))

    add_speaker_notes(
        s11,
        "Speed saves victims. Our webhook acknowledges incoming queries in 3.5 milliseconds, while our complete "
        "multi-modal neural verdict is returned in approximately 3 seconds."
    )

    # =========================================================================
    # SLIDE 12: MUNICIPAL SOC HUB & STIX 2.1 ATTACK GRAPH
    # =========================================================================
    s12 = prs.slides.add_slide(blank_layout)
    set_slide_background(s12, prs, COLOR_LIGHT_BG)
    add_header(s12, "Municipal SOC Analyst Hub: Real-Time STIX 2.1 Attack Graph")

    soc_cards = [
        ("Workbench 1: Overview & Heatmap", "SVG Threat Arrival Curve + 7-Day x 24-Hour UAE Municipal Threat Velocity Heatmap illustrating diurnal attack volume.", COLOR_BLUE),
        ("Workbench 2: STIX 2.1 Campaign Graph", "Stationary 60 FPS HTML5 Canvas engine mapping relationships between Threat Actors, Phishing Domains, and Municipal Victims.", COLOR_EMERALD),
        ("Workbench 3 & 4: IoC & Homoglyph Radar", "Searchable Class A IoC repository with TDRA ISP block push button and glyph-by-glyph Unicode Punycode decoder.", COLOR_AMBER),
        ("Workbench 5 & 6: Audio Lab & Telemetry", "Acoustic biometric inspection (Jitter, Shimmer, Formants) + Neon DB live persistence status and Qwen2.5-3B specs.", COLOR_CRIMSON),
    ]

    for i, (title, desc, col) in enumerate(soc_cards):
        col_idx = i % 2
        row_idx = i // 2
        left = Inches(0.8 + col_idx * 6.0)
        top = Inches(1.8 + row_idx * 2.6)

        card = s12.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, Inches(5.7), Inches(2.3))
        card.fill.solid()
        card.fill.fore_color.rgb = COLOR_WHITE
        card.line.color.rgb = col
        card.line.width = Pt(1.5)

        ctf = card.text_frame
        ctf.word_wrap = True
        ctf.margin_left = Inches(0.3)
        ctf.margin_top = Inches(0.2)

        p1 = ctf.paragraphs[0]
        p1.text = title
        p1.font.size = Pt(14)
        p1.font.bold = True
        p1.font.color.rgb = col
        p1.space_after = Pt(6)

        p2 = ctf.add_paragraph()
        p2.text = desc
        p2.font.size = Pt(10.5)
        p2.font.color.rgb = COLOR_TEXT_SECONDARY

    add_speaker_notes(
        s12,
        "For municipal security analysts, Project Hares features a dedicated SOC hub with an interactive STIX 2.1 "
        "graph, mapping live relationships between threat actors, phishing domains, and targeted government services in real time."
    )

    # =========================================================================
    # SLIDE 13: OFFICIAL DUBAI POLICE ESCALATION PATHWAYS
    # =========================================================================
    s13 = prs.slides.add_slide(blank_layout)
    set_slide_background(s13, prs, COLOR_LIGHT_BG)
    add_header(s13, "Automated Escalation: Dubai Police e-Crime Binding")

    esc_box = s13.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.8), Inches(11.733), Inches(5.0))
    esc_box.fill.solid()
    esc_box.fill.fore_color.rgb = COLOR_WHITE
    esc_box.line.color.rgb = COLOR_CRIMSON
    esc_box.line.width = Pt(2)

    etf = esc_box.text_frame
    etf.word_wrap = True
    etf.margin_left = Inches(0.5)
    etf.margin_top = Inches(0.4)

    ep1 = etf.paragraphs[0]
    ep1.text = "ONE-TAP INCIDENT ESCALATION CHANNELS"
    ep1.font.size = Pt(18)
    ep1.font.bold = True
    ep1.font.color.rgb = COLOR_CRIMSON
    ep1.space_after = Pt(14)

    ep2 = etf.add_paragraph()
    ep2.text = (
        "1. Dubai Police e-Crime Portal Direct Link (https://www.ecrime.ae):\n"
        "   When a RED verdict is emitted, the citizen is provided with an immediate one-click pathway to lodge\n"
        "   an official cybercrime report with Dubai Police General Headquarters.\n\n"
        "2. Municipal Non-Emergency Police Hotline (Call 901):\n"
        "   Direct phone link embedded for immediate phone advisory regarding financial scams and extortion.\n\n"
        "3. Clear Bilingual Public Protective Advisory:\n"
        "   '🔴 HIGH RISK: Do NOT click links or transfer funds. Report immediately to Dubai Police e-Crime.'\n"
        "   '🔴 تحذير: تم رصد احتيال مؤكد. لا تقم بالتحويل أو مشاركة البيانات، وأبلغ شرطة دبي فوراً.'"
    )
    ep2.font.size = Pt(11.5)
    ep2.font.color.rgb = COLOR_TEXT_SECONDARY
    ep2.line_spacing = 1.3

    add_speaker_notes(
        s13,
        "When a RED threat is confirmed, the citizen is immediately provided with one-tap escalation channels to "
        "Dubai Police e-Crime and the 901 hotline, closing the loop between detection and legal enforcement."
    )

    # =========================================================================
    # SLIDE 14: OPEN-SOURCE INTEGRITY & PUBLIC TRANSPARENCY
    # =========================================================================
    s14 = prs.slides.add_slide(blank_layout)
    set_slide_background(s14, prs, COLOR_LIGHT_BG)
    add_header(s14, "Public Transparency: Independent Open-Source Governance")

    banner_card = s14.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.8), Inches(11.733), Inches(1.4))
    banner_card.fill.solid()
    banner_card.fill.fore_color.rgb = RGBColor(254, 243, 199) # Amber 100
    banner_card.line.color.rgb = COLOR_AMBER
    banner_card.line.width = Pt(1.5)

    btf14 = banner_card.text_frame
    btf14.word_wrap = True
    btf14.margin_left = Inches(0.3)
    btf14.margin_top = Inches(0.2)

    bp1 = btf14.paragraphs[0]
    bp1.text = "INDEPENDENT OPEN-SOURCE ADVISORY RIBBON BANNER"
    bp1.font.size = Pt(14)
    bp1.font.bold = True
    bp1.font.color.rgb = COLOR_AMBER
    bp1.space_after = Pt(4)

    bp2 = btf14.add_paragraph()
    bp2.text = "Rendered across every page: 'Project Hares is an independent open-source cybersecurity project — not an official government agency or official state website.'"
    bp2.font.size = Pt(10.5)
    bp2.font.color.rgb = RGBColor(120, 53, 15) # Amber 900

    # Compliance card below
    comp_card = s14.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(3.4), Inches(11.733), Inches(3.4))
    comp_card.fill.solid()
    comp_card.fill.fore_color.rgb = COLOR_WHITE
    comp_card.line.color.rgb = COLOR_BORDER

    ctf14 = comp_card.text_frame
    ctf14.word_wrap = True
    ctf14.margin_left = Inches(0.4)
    ctf14.margin_top = Inches(0.3)

    cp1 = ctf14.paragraphs[0]
    cp1.text = "Complete Legal & Privacy Suite Live in Production"
    cp1.font.size = Pt(15)
    cp1.font.bold = True
    cp1.font.color.rgb = COLOR_NAVY
    cp1.space_after = Pt(8)

    cp2 = ctf14.add_paragraph()
    cp2.text = (
        "• Static Next.js 15 Routes: /terms and /privacy live, indexable, and certified.\n"
        "• Interactive Glassmorphic Legal Modal accessible from any portal view.\n"
        "• Mathematical Conformal Calibration Bound accurately stated: (≤ 0.1%).\n"
        "• Open-Source Foundation: Faster-Whisper, NeMo Guardrails, AraBERT, Outlines, Nonconformist.\n"
        "• 100% Free Public Verification: Zero advertising, zero data monetization, zero tracking."
    )
    cp2.font.size = Pt(11)
    cp2.font.color.rgb = COLOR_TEXT_SECONDARY
    cp2.line_spacing = 1.3

    add_speaker_notes(
        s14,
        "Transparency builds trust. Project Hares proudly displays an independent open-source advisory ribbon "
        "across every page, providing full legal terms and mathematical disclaimers."
    )

    # =========================================================================
    # SLIDE 15: CONCLUSION & OPERATIONAL ROADMAP
    # =========================================================================
    s15 = prs.slides.add_slide(blank_layout)
    set_slide_background(s15, prs, COLOR_DARK_BG)

    tbox_s15 = s15.shapes.add_textbox(Inches(0.8), Inches(1.5), Inches(11.733), Inches(4.5))
    tf15 = tbox_s15.text_frame
    tf15.word_wrap = True

    p15_1 = tf15.paragraphs[0]
    p15_1.text = "PROJECT HARES IS PRODUCTION VERIFIED & LIVE"
    p15_1.font.size = Pt(32)
    p15_1.font.bold = True
    p15_1.font.color.rgb = COLOR_WHITE
    p15_1.space_after = Pt(16)

    p15_2 = tf15.add_paragraph()
    p15_2.text = (
        "✔ Citizen Verification Portal: https://hares-wheat.vercel.app (100% Uptime)\n"
        "✔ Backend API Gateway: https://hares-api.onrender.com (FastAPI / Render)\n"
        "✔ Sovereign Neural Engine: Hugging Face ZeroGPU A10G Space (Active)\n"
        "✔ Relational Persistence: Neon Serverless PostgreSQL 16 (TLS Connection Pooling)\n"
        "✔ Automated E2E Verification: 17/17 Playwright Test Cases Passing (100% Suite Pass)\n"
        "✔ Complete Master Blueprint: project.md & Technical Word Dossier Generated"
    )
    p15_2.font.size = Pt(14)
    p15_2.font.color.rgb = COLOR_EMERALD
    p15_2.line_spacing = 1.4
    p15_2.space_after = Pt(20)

    p15_3 = tf15.add_paragraph()
    p15_3.text = "Autonomous Sovereign Intelligence Protecting Dubai's Digital Horizon."
    p15_3.font.size = Pt(16)
    p15_3.font.bold = True
    p15_3.font.color.rgb = COLOR_AMBER

    add_speaker_notes(
        s15,
        "Project Hares is fully operational, verified across 17 automated end-to-end test suites, and deployed live. "
        "Thank you for your time, and we invite you to explore the live portal and system ledger."
    )

    OUTPUT_PPTX.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(OUTPUT_PPTX))
    print(f"Generated Official Presentation: {OUTPUT_PPTX}")

if __name__ == "__main__":
    create_presentation()
