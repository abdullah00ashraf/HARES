"""
Project Hares: Official DOCX Technical Report Compiler
Parses project.md and compiles a professionally formatted Microsoft Word document (.docx)
with 1-inch margins, executive cover page, styled tables, color-coded headings,
and embedded 300-DPI empirical audit figures.
"""

import os
import re
from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

DOCS_DIR = Path("C:/HARES/docs")
FIGURES_DIR = DOCS_DIR / "figures"
OUTPUT_DOCX = DOCS_DIR / "Project_Hares_Master_Technical_Report.docx"
PROJECT_MD_PATH = Path("C:/HARES/project.md")

# Design Color Palette
COLOR_NAVY = RGBColor(11, 27, 61)       # #0B1B3D - Primary Headings
COLOR_SLATE = RGBColor(51, 65, 85)      # #334155 - Body Text
COLOR_EMERALD = RGBColor(5, 150, 105)   # #059669 - Accent / Verified
COLOR_AMBER = RGBColor(217, 119, 6)     # #D97706 - Warning / Advisory
COLOR_MUTED = RGBColor(100, 116, 139)   # #64748B - Metadata & Subtitles
HEX_TABLE_HEADER = "0B1B3D"             # Navy for Table Header
HEX_TABLE_ALT = "F8FAFC"                # Slate 50 for alternate rows
HEX_CALLOUT_BG = "F1F5F9"               # Slate 100 for callout boxes

def set_cell_background(cell, hex_color: str):
    """Sets background shading of a docx table cell."""
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=120, bottom=120, left=180, right=180):
    """Sets internal padding (in twentieths of a point / dxa) for a table cell."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>'
        f'<w:top w:w="{top}" w:type="dxa"/>'
        f'<w:bottom w:w="{bottom}" w:type="dxa"/>'
        f'<w:left w:w="{left}" w:type="dxa"/>'
        f'<w:right w:w="{right}" w:type="dxa"/>'
        f'</w:tcMar>'
    )
    tcPr.append(tcMar)

def add_callout_box(doc, text: str, border_color: str = "059669", fill_color: str = "F0FDF4"):
    """Adds a stylish callout box with a colored left accent border."""
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    table.columns[0].width = Inches(6.5)

    cell = table.cell(0, 0)
    set_cell_background(cell, fill_color)
    set_cell_margins(cell, top=140, bottom=140, left=200, right=180)

    # Set left border thick, others none
    tcPr = cell._tc.get_or_add_tcPr()
    borders = parse_xml(
        f'<w:tcBorders {nsdecls("w")}>'
        f'<w:top w:val="none"/>'
        f'<w:left w:val="single" w:sz="36" w:space="0" w:color="{border_color}"/>'
        f'<w:bottom w:val="none"/>'
        f'<w:right w:val="none"/>'
        f'</w:tcBorders>'
    )
    tcPr.append(borders)

    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = 1.15
    run = p.add_run(text.strip())
    run.font.name = "Calibri"
    run.font.size = Pt(10)
    run.font.color.rgb = COLOR_SLATE

    # Add spacing after table
    post_p = doc.add_paragraph()
    post_p.paragraph_format.space_after = Pt(6)

def create_styled_document():
    doc = Document()

    # 1. Page Setup: 1.0 inch margins all around
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)
        section.different_first_page_header_footer = True

        # Header for internal pages
        header = section.header
        hp = header.paragraphs[0]
        hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        hrun = hp.add_run("Project Hares (مشروع حارس) • Sovereign Technical Dossier")
        hrun.font.name = "Calibri"
        hrun.font.size = Pt(8.5)
        hrun.font.color.rgb = COLOR_MUTED

        # Footer with page numbers and confidentiality notice
        footer = section.footer
        fp = footer.paragraphs[0]
        fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        frun = fp.add_run("Sovereign Research & Engineering Blueprint • Dubai Municipal Cybersecurity • FR-4.1 Zero-PII Standard")
        frun.font.name = "Calibri"
        frun.font.size = Pt(8)
        frun.font.color.rgb = COLOR_MUTED

    # 2. Configure Default Font
    style_normal = doc.styles["Normal"]
    style_normal.font.name = "Calibri"
    style_normal.font.size = Pt(10.5)
    style_normal.font.color.rgb = COLOR_SLATE

    # =========================================================================
    # COVER PAGE
    # =========================================================================
    p_spacing = doc.add_paragraph()
    p_spacing.paragraph_format.space_before = Pt(40)

    # Sovereign Crest Label
    p_crest = doc.add_paragraph()
    r_crest = p_crest.add_run("EMIRATE OF DUBAI • UNITED ARAB EMIRATES • MUNICIPAL CYBERSECURITY")
    r_crest.font.name = "Calibri"
    r_crest.font.size = Pt(9.5)
    r_crest.font.bold = True
    r_crest.font.color.rgb = COLOR_EMERALD
    p_crest.paragraph_format.space_after = Pt(12)

    # Main Title
    p_title = doc.add_paragraph()
    r_title = p_title.add_run("PROJECT HARES\nمشروع حارس")
    r_title.font.name = "Calibri"
    r_title.font.size = Pt(32)
    r_title.font.bold = True
    r_title.font.color.rgb = COLOR_NAVY
    p_title.paragraph_format.space_after = Pt(12)
    p_title.paragraph_format.line_spacing = 1.05

    # Subtitle
    p_sub = doc.add_paragraph()
    r_sub = p_sub.add_run("Autonomous Sovereign Multi-Modal Fraud Triage & Threat Intelligence System for Dubai")
    r_sub.font.name = "Calibri"
    r_sub.font.size = Pt(14)
    r_sub.font.color.rgb = COLOR_SLATE
    p_sub.paragraph_format.space_after = Pt(28)

    # Metadata Card Table
    meta_table = doc.add_table(rows=5, cols=2)
    meta_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    meta_table.columns[0].width = Inches(2.2)
    meta_table.columns[1].width = Inches(4.3)

    metadata_items = [
        ("Document Classification:", "Master Technical Architecture & Empirical Evaluation Report"),
        ("Document Version:", "1.0.0-PROD-MASTER (Production Verified)"),
        ("Publication Date:", "15 October 2026"),
        ("Jurisdiction & Mandate:", "Emirate of Dubai / UAE • DESC ISR v2.0 • Digital Dubai AI Ethics"),
        ("Live Production Portal:", "https://hares-wheat.vercel.app | API: https://hares-api.onrender.com"),
    ]

    for row_idx, (k, v) in enumerate(metadata_items):
        c0 = meta_table.cell(row_idx, 0)
        c1 = meta_table.cell(row_idx, 1)
        set_cell_background(c0, "F8FAFC")
        set_cell_background(c1, "FFFFFF")
        set_cell_margins(c0, top=80, bottom=80, left=120, right=120)
        set_cell_margins(c1, top=80, bottom=80, left=120, right=120)

        p0 = c0.paragraphs[0]
        r0 = p0.add_run(k)
        r0.font.bold = True
        r0.font.size = Pt(9.5)
        r0.font.color.rgb = COLOR_NAVY

        p1 = c1.paragraphs[0]
        r1 = p1.add_run(v)
        r1.font.size = Pt(9.5)
        r1.font.color.rgb = COLOR_SLATE

    p_spacer = doc.add_paragraph()
    p_spacer.paragraph_format.space_before = Pt(36)

    # Executive Legal Notice Box
    add_callout_box(
        doc,
        "LEGAL & OPEN-SOURCE PUBLIC ADVISORY NOTICE:\n"
        "Project Hares is an independent open-source cybersecurity research project developed for community fraud triage and is not an official government website, agency, or law enforcement division. While Project Hares employs Conformal Prediction statistical calibration to bound error rates (≤ 0.1%), automated models are advisory. Users must remain vigilant and apply sound judgment. The developers and operators disclaim any liability for direct, indirect, or consequential damages resulting from reliance on triage verdicts, third-party fraud, or actions taken prior to submitting content. All confirmed threats are synchronized with Dubai Police e-Crime (https://www.ecrime.ae) and hotline 901.",
        border_color="D97706",
        fill_color="FFFBEB"
    )

    doc.add_page_break()

    # =========================================================================
    # PARSE PROJECT.MD AND RENDER BODY
    # =========================================================================
    if not PROJECT_MD_PATH.exists():
        raise FileNotFoundError(f"Missing {PROJECT_MD_PATH}")

    with open(PROJECT_MD_PATH, "r", encoding="utf-8") as f:
        md_text = f.read()

    lines = md_text.splitlines()
    in_code_block = False
    code_block_lines = []
    in_table = False
    table_rows = []

    def flush_table():
        nonlocal in_table, table_rows
        if not table_rows:
            in_table = False
            return

        # Filter out markdown separator row (e.g. | --- | --- |)
        filtered_rows = [r for r in table_rows if not all(c.strip().replace("-", "").replace(":", "") == "" for c in r)]
        if not filtered_rows:
            in_table = False
            table_rows = []
            return

        num_cols = max(len(r) for r in filtered_rows)
        tbl = doc.add_table(rows=len(filtered_rows), cols=num_cols)
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER

        col_width = Inches(6.5 / max(1, num_cols))
        for col in tbl.columns:
            col.width = col_width

        for r_idx, row in enumerate(filtered_rows):
            is_header = (r_idx == 0)
            for c_idx in range(num_cols):
                val = row[c_idx] if c_idx < len(row) else ""
                cell = tbl.cell(r_idx, c_idx)
                cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER

                # Background & Margins
                if is_header:
                    set_cell_background(cell, HEX_TABLE_HEADER)
                else:
                    set_cell_background(cell, HEX_TABLE_ALT if r_idx % 2 == 1 else "FFFFFF")
                set_cell_margins(cell, top=100, bottom=100, left=140, right=140)

                p = cell.paragraphs[0]
                p.paragraph_format.space_before = Pt(0)
                p.paragraph_format.space_after = Pt(0)
                p.paragraph_format.line_spacing = 1.15
                run = p.add_run(val.strip())
                run.font.name = "Calibri"
                run.font.size = Pt(9 if not is_header else 9.5)
                if is_header:
                    run.font.bold = True
                    run.font.color.rgb = RGBColor(255, 255, 255)
                else:
                    run.font.color.rgb = COLOR_SLATE

        # Table post spacing
        p_post = doc.add_paragraph()
        p_post.paragraph_format.space_after = Pt(8)
        table_rows = []
        in_table = False

    def flush_code_block():
        nonlocal in_code_block, code_block_lines
        if not code_block_lines:
            in_code_block = False
            return

        code_text = "\n".join(code_block_lines)
        # If it's a slide or huge block, render cleanly in a styled table block
        tbl = doc.add_table(rows=1, cols=1)
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        tbl.columns[0].width = Inches(6.5)
        cell = tbl.cell(0, 0)
        set_cell_background(cell, "0F172A")
        set_cell_margins(cell, top=140, bottom=140, left=180, right=180)

        p = cell.paragraphs[0]
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        run = p.add_run(code_text)
        run.font.name = "Consolas"
        run.font.size = Pt(8.5)
        run.font.color.rgb = RGBColor(226, 232, 240) # Slate 200

        p_post = doc.add_paragraph()
        p_post.paragraph_format.space_after = Pt(6)

        code_block_lines = []
        in_code_block = False

    idx = 0
    total_lines = len(lines)

    while idx < total_lines:
        line = lines[idx]
        stripped = line.strip()

        # Handle Code Fences
        if stripped.startswith("```"):
            if in_code_block:
                flush_code_block()
            else:
                if in_table:
                    flush_table()
                in_code_block = True
                code_block_lines = []
            idx += 1
            continue

        if in_code_block:
            code_block_lines.append(line)
            idx += 1
            continue

        # Handle Markdown Tables
        if stripped.startswith("|") and stripped.endswith("|"):
            if not in_table:
                in_table = True
                table_rows = []
            parts = [c.strip() for c in stripped.split("|")[1:-1]]
            table_rows.append(parts)
            idx += 1
            continue
        else:
            if in_table:
                flush_table()

        # Handle Images (Figure embeds)
        img_match = re.match(r"!\[(.*?)\]\((.*?)\)", stripped)
        if img_match:
            caption = img_match.group(1)
            raw_path = img_match.group(2)

            # Resolve local file path
            img_path = None
            if "file:///" in raw_path:
                clean_p = raw_path.replace("file:///", "").replace("/", os.sep)
                img_path = Path(clean_p)
            elif raw_path.startswith("docs/figures/"):
                img_path = Path("C:/HARES") / raw_path

            if img_path and img_path.exists():
                p_img = doc.add_paragraph()
                p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p_img.paragraph_format.space_before = Pt(12)
                p_img.paragraph_format.space_after = Pt(4)
                doc.add_picture(str(img_path), width=Inches(5.8))

                # Image Caption
                p_cap = doc.add_paragraph()
                p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p_cap.paragraph_format.space_after = Pt(14)
                r_cap = p_cap.add_run(f"Figure: {caption}")
                r_cap.font.name = "Calibri"
                r_cap.font.size = Pt(9)
                r_cap.font.bold = True
                r_cap.font.color.rgb = COLOR_NAVY
            idx += 1
            continue

        # Handle Headings
        if stripped.startswith("# "):
            # Heading 1 (Section level)
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(20)
            p.paragraph_format.space_after = Pt(8)
            p.paragraph_format.keep_with_next = True
            run = p.add_run(stripped[2:].strip())
            run.font.name = "Calibri"
            run.font.size = Pt(18)
            run.font.bold = True
            run.font.color.rgb = COLOR_NAVY
            idx += 1
            continue

        if stripped.startswith("## "):
            # Heading 2
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(16)
            p.paragraph_format.space_after = Pt(6)
            p.paragraph_format.keep_with_next = True
            run = p.add_run(stripped[3:].strip())
            run.font.name = "Calibri"
            run.font.size = Pt(14)
            run.font.bold = True
            run.font.color.rgb = COLOR_NAVY
            idx += 1
            continue

        if stripped.startswith("### "):
            # Heading 3
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(12)
            p.paragraph_format.space_after = Pt(4)
            p.paragraph_format.keep_with_next = True
            run = p.add_run(stripped[4:].strip())
            run.font.name = "Calibri"
            run.font.size = Pt(11.5)
            run.font.bold = True
            run.font.color.rgb = COLOR_EMERALD
            idx += 1
            continue

        if stripped.startswith("#### "):
            # Heading 4
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(8)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.keep_with_next = True
            run = p.add_run(stripped[5:].strip())
            run.font.name = "Calibri"
            run.font.size = Pt(10.5)
            run.font.bold = True
            run.font.color.rgb = COLOR_SLATE
            idx += 1
            continue

        # Handle Bullet points
        if stripped.startswith("* ") or stripped.startswith("- "):
            p = doc.add_paragraph(style="List Bullet")
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(3)
            p.paragraph_format.line_spacing = 1.15
            content = stripped[2:].strip()

            # Inline bold parsing (**bold**)
            tokens = re.split(r"(\*\*.*?\*\*)", content)
            for tok in tokens:
                if tok.startswith("**") and tok.endswith("**"):
                    r = p.add_run(tok[2:-2])
                    r.font.bold = True
                    r.font.color.rgb = COLOR_NAVY
                else:
                    p.add_run(tok)
            idx += 1
            continue

        # Handle Horizontal Rules
        if stripped in ["---", "***", "___"]:
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(8)
            p.paragraph_format.space_after = Pt(8)
            # Add thin divider
            idx += 1
            continue

        # Normal Paragraphs
        if stripped:
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(6)
            p.paragraph_format.line_spacing = 1.15

            # Simple inline bold processing
            tokens = re.split(r"(\*\*.*?\*\*)", stripped)
            for tok in tokens:
                if tok.startswith("**") and tok.endswith("**"):
                    r = p.add_run(tok[2:-2])
                    r.font.bold = True
                    r.font.color.rgb = COLOR_NAVY
                else:
                    p.add_run(tok)

        idx += 1

    if in_table:
        flush_table()
    if in_code_block:
        flush_code_block()

    # Save output
    OUTPUT_DOCX.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(OUTPUT_DOCX))
    print(f"Generated Official Technical Report: {OUTPUT_DOCX}")

if __name__ == "__main__":
    create_styled_document()
