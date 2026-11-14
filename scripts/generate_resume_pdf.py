#!/usr/bin/env python3
"""Render public RESUME.md to a PDF in the generated output branch."""
from pathlib import Path
import html
import re
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4

SOURCE = Path("RESUME.md")
DEST = Path("dist/Vikas_Sharma_Resume.pdf")
DEST.parent.mkdir(parents=True, exist_ok=True)
ink, purple = HexColor("#1E293B"), HexColor("#6D28D9")
styles = {
    "title": ParagraphStyle("Title", fontName="Helvetica-Bold", fontSize=19, leading=23, alignment=TA_CENTER, spaceAfter=4, textColor=ink),
    "h2": ParagraphStyle("Heading", fontName="Helvetica-Bold", fontSize=10, leading=12, spaceBefore=7, spaceAfter=2, textColor=purple),
    "body": ParagraphStyle("Body", fontName="Helvetica", fontSize=8.1, leading=10.1, spaceAfter=2, textColor=ink),
    "bul": ParagraphStyle("Bullet", fontName="Helvetica", fontSize=8.0, leading=10, leftIndent=10, firstLineIndent=-8, spaceAfter=1.5, textColor=ink),
}
def fmt(s):
    s = html.escape(s.strip().replace("  ", " "), quote=True)
    s = re.sub(r"\[([^\]]+)\]\((https?://[^)]+|mailto:[^)]+)\)", lambda m: '<link href="'+m.group(2)+'" color="#6D28D9">'+m.group(1)+'</link>', s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<i>\1</i>", s)
    return s.replace("📍", "").replace("✉️", "").replace("🔗", "").replace("⬅", "")

story=[]
for raw in SOURCE.read_text(encoding="utf-8").splitlines():
    line=raw.strip()
    if not line or line.startswith("---") or line.startswith("[⬅ Back to my GitHub profile]") or line.startswith("> "):
        continue
    if line.startswith("# "):
        story.append(Paragraph(fmt(line[2:]), styles["title"]))
    elif line.startswith("## "):
        story.append(Paragraph(fmt(line[3:].upper()), styles["h2"]))
    elif line.startswith("- "):
        story.append(Paragraph("&#8226; "+fmt(line[2:]), styles["bul"]))
    else:
        story.append(Paragraph(fmt(line), styles["body"]))

doc=SimpleDocTemplate(str(DEST), pagesize=A4, rightMargin=42, leftMargin=42, topMargin=28, bottomMargin=28, title="Vikas Sharma - Resume", author="Vikas Sharma", pageCompression=1)
doc.build(story)
print("Generated", DEST, DEST.stat().st_size, "bytes")
