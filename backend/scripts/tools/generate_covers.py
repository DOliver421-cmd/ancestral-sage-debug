"""
Generate leather-bound style covers for all 4 Black On Black Love books.
"""
import os, sys, time, base64
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'), override=True)
key = os.environ.get('OPENAI_API_KEY', '')
if not key:
    print("ERROR: OPENAI_API_KEY not found")
    sys.exit(1)

client = OpenAI(api_key=key)

LEATHER_STYLE = "Antique imprinted leather-bound book cover, dark brown textured leather with ornate gold foil embossing, decorative gold border frame, ornamental corner flourishes, rich warm lighting, spine visible, professional publishing quality, 3D rendering, elegant and timeless academic book aesthetic"

COVERS = [
    {
        "file": "Book_I_Deep_Roots",
        "prompt": LEATHER_STYLE + ", volume I of a poetry series, deep ancestral theme, subtle root imagery woven into gold embossing",
    },
    {
        "file": "Book_II_Reclamation",
        "prompt": LEATHER_STYLE + ", volume II of a poetry series, healing reclamation theme, subtle sunrise or doorway imagery in gold embossing",
    },
    {
        "file": "Book_III_Ascension",
        "prompt": LEATHER_STYLE + ", volume III of a poetry series, ascension rising theme, subtle stairway or light imagery in gold embossing",
    },
    {
        "file": "Book_IV_Ascension_II",
        "prompt": LEATHER_STYLE + ", volume IV of a poetry series, final ascension culmination theme, subtle crown or circle imagery in gold embossing",
    },
]

outdir = os.path.expanduser('~/Downloads/Black_On_Black_Love_Covers')
os.makedirs(outdir, exist_ok=True)

for c in COVERS:
    print(f"Generating {c['file']}...")
    try:
        resp = client.images.generate(
            model="gpt-image-1.5",
            prompt=c["prompt"],
            size="1024x1024",
            n=1,
        )
        b64 = resp.data[0].b64_json
        path = os.path.join(outdir, c['file'] + '.png')
        with open(path, 'wb') as f:
            f.write(base64.b64decode(b64))
        print(f"  Saved: {path}")
    except Exception as e:
        print(f"  Error: {e}")
    time.sleep(5)

print(f"\nDone. Covers saved to {outdir}")
