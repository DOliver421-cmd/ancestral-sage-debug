"""
Convert WAI handbooks from markdown to proper PDF documents.
"""
import os, re
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem, HRFlowable, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

HANDOUT = r"C:\Users\lenovo\ancestral-sage-debug\backend\handbooks"
OUTDIR = r"C:\Users\lenovo\ancestral-sage-debug\backend\handbooks\pdf"
os.makedirs(OUTDIR, exist_ok=True)

PAPER = LETTER
MARGIN = 0.9 * inch

GOLD = HexColor("#D4AF37")
DARK = HexColor("#1A1A1A")
WHITE = HexColor("#FFFFFF")
BODY = HexColor("#2C2C2C")

styles = getSampleStyleSheet()

s_title = ParagraphStyle("CoverTitle", fontName="Times-Bold", fontSize=28, textColor=GOLD, alignment=TA_CENTER, spaceAfter=12)
s_sub = ParagraphStyle("CoverSub", fontName="Times-Roman", fontSize=16, textColor=GOLD, alignment=TA_CENTER, spaceAfter=4)
s_h1 = ParagraphStyle("H1", fontName="Times-Bold", fontSize=20, textColor=DARK, spaceBefore=24, spaceAfter=12)
s_h2 = ParagraphStyle("H2", fontName="Times-Bold", fontSize=15, textColor=DARK, spaceBefore=18, spaceAfter=8)
s_h3 = ParagraphStyle("H3", fontName="Times-Bold", fontSize=12, textColor=DARK, spaceBefore=12, spaceAfter=6)
s_body = ParagraphStyle("Body", fontName="Times-Roman", fontSize=11, textColor=BODY, leading=15, spaceAfter=6)
s_code = ParagraphStyle("Code", fontName="Courier", fontSize=9, textColor=HexColor("#333333"), leftIndent=20, spaceAfter=6, backColor=HexColor("#F5F5F5"))
s_bullet = ParagraphStyle("Bullet", fontName="Times-Roman", fontSize=11, textColor=BODY, leading=15, spaceAfter=3, leftIndent=24)
s_table_header = ParagraphStyle("TH", fontName="Times-Bold", fontSize=10, textColor=WHITE, alignment=TA_CENTER)
s_table_cell = ParagraphStyle("TC", fontName="Times-Roman", fontSize=10, textColor=BODY, alignment=TA_LEFT)

def build_pdf(md_path, pdf_path):
    with open(md_path, "r", encoding="utf-8") as f:
        text = f.read()

    doc = SimpleDocTemplate(pdf_path, pagesize=PAPER,
                            leftMargin=MARGIN, rightMargin=MARGIN,
                            topMargin=MARGIN, bottomMargin=MARGIN)
    elements = []
    in_table = False
    table_rows = []

    for line in text.split("\n"):
        if line.startswith("# ") and not in_table:
            elements.append(Spacer(1, 40))
            elements.append(Paragraph(line[2:].strip(), s_title))
            elements.append(HRFlowable(width="60%", thickness=2, color=GOLD, spaceAfter=20))
        elif line.startswith("## ") and not in_table:
            elements.append(Paragraph(line[3:].strip(), s_h1))
        elif line.startswith("### ") and not in_table:
            elements.append(Paragraph(line[4:].strip(), s_h2))
        elif line.startswith("#### ") and not in_table:
            elements.append(Paragraph(line[5:].strip(), s_h3))
        elif line.startswith("- **") and not in_table:
            line = re.sub(r"^\-\s\*\*(.+?)\*\*(.*)", r"\1\2", line)
            elements.append(ListItem(Paragraph(line.strip("- ").strip(), s_bullet), bulletColor=GOLD))
        elif line.startswith("- ") and not in_table:
            elements.append(ListItem(Paragraph(line[2:].strip(), s_bullet), bulletColor=GOLD))
        elif line.startswith("| ") and not in_table:
            cells = [c.strip() for c in line.split("|") if c.strip()]
            if not any("---" in c for c in cells):
                table_rows.append(cells)
        elif line.strip() == "" and not in_table:
            elements.append(Spacer(1, 6))
        elif line.strip().startswith("```"):
            in_table = not in_table
        elif in_table:
            elements.append(Paragraph(line.strip(), s_code))
        elif line.strip().startswith('"') and line.strip().endswith('"'):
            elements.append(Paragraph(line.strip(), ParagraphStyle("Quote", parent=s_body, leftIndent=30, rightIndent=30, textColor=HexColor("#555555"), fontName="Times-Italic")))
        elif line.strip().startswith("---"):
            elements.append(HRFlowable(width="100%", thickness=1, color=HexColor("#CCCCCC"), spaceAfter=12, spaceBefore=12))
        elif line.strip() == "":
            pass
        else:
            elements.append(Paragraph(line.strip(), s_body))

    # Render table if we have rows
    if table_rows:
        from reportlab.platypus import Table, TableStyle
        col_w = (PAPER[0] - 2 * MARGIN) / max(len(r) for r in table_rows)
        t = Table(table_rows, colWidths=[col_w] * len(table_rows[0]))
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), DARK),
            ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#CCCCCC")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HexColor("#F9F9F9"), HexColor("#FFFFFF")]),
        ]))
        elements.append(t)

    doc.build(elements)
    print(f"PDF: {pdf_path}")

files = [
    "WAI_Instructor_Handbook.md",
    "WAI_Student_Handbook.md",
    "WAI_Admin_Handbook.md",
    "AI_Persona_Creation_Manual.md",
]

for fname in files:
    md = os.path.join(HANDOUT, fname)
    pdf = os.path.join(OUTDIR, fname.replace(".md", ".pdf"))
    if os.path.exists(md):
        build_pdf(md, pdf)
    else:
        print(f"Not found: {md}")

print("\nDone.")
