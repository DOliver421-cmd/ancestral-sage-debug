"""
Overlay text on book covers with balanced spacing.
"""
import os
from PIL import Image, ImageDraw, ImageFont

INDIR = os.path.expanduser('~/Downloads/Black_On_Black_Love_Covers')
OUTDIR = os.path.expanduser('~/Downloads/Black_On_Black_Love_Covers_Titled')
os.makedirs(OUTDIR, exist_ok=True)

GOLD = (212, 175, 55)
WHITE = (255, 255, 255)

BOOKS = [
    {"file": "Book_I_Deep_Roots",     "number": "I",   "title": "Deep Roots",     "subtitle": "Where the Becoming Begins"},
    {"file": "Book_II_Reclamation",   "number": "II",  "title": "Reclamation",    "subtitle": "The Healing of a Man"},
    {"file": "Book_III_Ascension",    "number": "III", "title": "Ascension",      "subtitle": "The Return to the Inner Temple"},
    {"file": "Book_IV_Ascension_II",  "number": "IV",  "title": "Ascension II",   "subtitle": "We Ascend Again"},
]

def get_font(size, bold=False, italic=False):
    paths = [
        "C:\\Windows\\Fonts\\georgiab.ttf",
        "C:\\Windows\\Fonts\\georgiai.ttf",
        "C:\\Windows\\Fonts\\georgia.ttf",
        "C:\\Windows\\Fonts\\timesbd.ttf" if bold else "C:\\Windows\\Fonts\\times.ttf",
        "C:\\Windows\\Fonts\\arialbd.ttf" if bold else "C:\\Windows\\Fonts\\arial.ttf",
        "C:\\Windows\\Fonts\\CALIFR.ttf",
    ]
    for p in paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except:
                continue
    return ImageFont.load_default()

for book in BOOKS:
    src = os.path.join(INDIR, book["file"] + ".png")
    if not os.path.exists(src):
        print(f"Skipping {book['file']} — not found")
        continue

    img = Image.open(src).convert("RGB")
    W, H = img.size
    draw = ImageDraw.Draw(img)
    cx = W // 2
    line_w = 280

    # Font sizes scale with image width
    fs_series  = int(W * 0.050)
    fs_booknum = int(W * 0.036)
    fs_title   = int(W * 0.065)
    fs_sub     = int(W * 0.030)
    fs_author  = int(W * 0.040)
    fs_ances   = int(W * 0.032)
    fs_pub     = int(W * 0.028)

    f_series   = get_font(fs_series)
    f_booknum  = get_font(fs_booknum)
    f_title    = get_font(fs_title, bold=True)
    f_sub      = get_font(fs_sub)
    f_author   = get_font(fs_author)
    f_ances    = get_font(fs_ances)
    f_pub      = get_font(fs_pub)

    # ---- LAYOUT (all fractions of H) ----
    # Series + book number: top cluster
    y_top   = int(H * 0.10)
    # Title + subtitle: middle cluster
    y_tit_start = int(H * 0.30)
    # Author block: lower middle
    y_auth  = int(H * 0.60)
    # Publisher: near bottom
    y_pub   = int(H * 0.87)

    # --- Top cluster ---
    draw.text((cx, y_top), "BLACK ON BLACK LOVE", fill=GOLD, font=f_series, anchor="mt")
    draw.text((cx, y_top + int(H * 0.065)), f"Book {book['number']}", fill=GOLD, font=f_booknum, anchor="mt")

    # Decorative line above title
    y_line1 = y_tit_start - int(H * 0.025)
    draw.line([(cx - line_w // 2, y_line1), (cx + line_w // 2, y_line1)], fill=GOLD, width=2)

    # --- Title cluster ---
    draw.text((cx, y_tit_start), book['title'].upper(), fill=GOLD, font=f_title, anchor="mt")
    draw.text((cx, y_tit_start + int(H * 0.085)), book['subtitle'], fill=WHITE, font=f_sub, anchor="mt")

    # Decorative line below subtitle
    y_line2 = y_tit_start + int(H * 0.13)
    draw.line([(cx - line_w // 2, y_line2), (cx + line_w // 2, y_line2)], fill=GOLD, width=2)

    # --- Author block ---
    draw.text((cx, y_auth), "By NAM Oshun", fill=GOLD, font=f_author, anchor="mt")
    draw.text((cx, y_auth + int(H * 0.055)), "Ancestral PPoems", fill=GOLD, font=f_ances, anchor="mt")

    # --- Publisher ---
    draw.text((cx, y_pub), "Need $ome End$ Publication$", fill=GOLD, font=f_pub, anchor="mt")

    out = os.path.join(OUTDIR, book["file"] + ".png")
    img.save(out)
    print(f"Saved: {out}")

print("\nDone.")
