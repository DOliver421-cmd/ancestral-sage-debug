"""
Convert WAI handbooks to styled HTML files.
"""
import os
from markdown_it import MarkdownIt

HANDOUT = r"C:\Users\lenovo\ancestral-sage-debug\backend\handbooks"
OUTDIR = r"C:\Users\lenovo\ancestral-sage-debug\backend\handbooks\html"
os.makedirs(OUTDIR, exist_ok=True)

md = MarkdownIt()

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;0,700;1,400&display=swap');
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: 'Cormorant Garamond', Georgia, 'Times New Roman', serif;
    color: #1a1a1a;
    line-height: 1.6;
    max-width: 800px;
    margin: 0 auto;
    padding: 60px 40px;
    background: #faf8f5;
  }}
  h1 {{
    font-size: 32px;
    font-weight: 700;
    color: #1a1a1a;
    border-bottom: 3px solid #D4AF37;
    padding-bottom: 12px;
    margin-bottom: 8px;
    text-align: center;
  }}
  .subtitle {{
    text-align: center;
    font-size: 15px;
    color: #666;
    margin-bottom: 40px;
    font-style: italic;
  }}
  h2 {{
    font-size: 22px;
    font-weight: 600;
    color: #1a1a1a;
    margin-top: 36px;
    margin-bottom: 12px;
    border-bottom: 1px solid #e0d5c0;
    padding-bottom: 4px;
  }}
  h3 {{
    font-size: 18px;
    font-weight: 600;
    color: #333;
    margin-top: 24px;
    margin-bottom: 8px;
  }}
  h4 {{
    font-size: 16px;
    font-weight: 600;
    color: #444;
    margin-top: 18px;
    margin-bottom: 6px;
  }}
  p {{ margin-bottom: 12px; font-size: 16px; }}
  ul, ol {{ margin: 8px 0 16px 24px; }}
  li {{ margin-bottom: 4px; font-size: 16px; }}
  strong {{ font-weight: 700; }}
  em {{ font-style: italic; }}
  blockquote {{
    border-left: 4px solid #D4AF37;
    margin: 16px 0;
    padding: 12px 20px;
    background: #f5f0e8;
    font-style: italic;
    color: #444;
    font-size: 16px;
  }}
  code {{
    font-family: 'Courier New', monospace;
    background: #f0ede8;
    padding: 1px 6px;
    border-radius: 3px;
    font-size: 14px;
  }}
  pre {{
    background: #f0ede8;
    padding: 16px 20px;
    border-radius: 4px;
    overflow-x: auto;
    font-size: 14px;
    margin: 12px 0 20px;
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
    margin: 16px 0 24px;
    font-size: 15px;
  }}
  th {{
    background: #1a1a1a;
    color: white;
    padding: 10px 14px;
    text-align: left;
    font-weight: 600;
  }}
  td {{
    padding: 8px 14px;
    border-bottom: 1px solid #ddd;
  }}
  tr:nth-child(even) td {{ background: #f5f2ed; }}
  hr {{
    border: none;
    border-top: 2px solid #D4AF37;
    margin: 32px 0;
  }}
  .footer {{
    text-align: center;
    margin-top: 48px;
    padding-top: 16px;
    border-top: 1px solid #e0d5c0;
    font-size: 14px;
    color: #888;
    font-style: italic;
  }}
</style>
</head>
<body>
{content}
<div class="footer">WAI Institute — NAM Oshun Mission</div>
</body>
</html>"""

files = [
    ("WAI_Admin_Handbook.md",           "WAI Institute — Admin Handbook"),
    ("WAI_Instructor_Handbook.md",      "WAI Institute — Instructor Handbook"),
    ("WAI_Student_Handbook.md",         "WAI Institute — Student Handbook"),
    ("AI_Persona_Creation_Manual.md",   "Building AI Personas — A Manual for Underserved Communities"),
]

for fname, title in files:
    src = os.path.join(HANDOUT, fname)
    if not os.path.exists(src):
        print(f"Not found: {src}")
        continue

    with open(src, "r", encoding="utf-8") as f:
        content = f.read()

    html_body = md.render(content)
    html = HTML_TEMPLATE.format(title=title, content=html_body)

    out = os.path.join(OUTDIR, fname.replace(".md", ".html"))
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"HTML: {out}")

print("\nDone.")
