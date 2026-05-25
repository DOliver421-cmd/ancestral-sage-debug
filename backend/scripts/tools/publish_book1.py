"""
Publish Book I: Deep Roots to Gumroad directly (circumvents server needing restart).
Run:  python scripts/tools/publish_book1.py
"""

import os, sys, json, requests, httpx, asyncio
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'), override=True)
GUMROAD_KEY = os.environ.get("GUMROAD_API_KEY", "")

if not GUMROAD_KEY:
    print("ERROR: GUMROAD_API_KEY not found in .env")
    sys.exit(1)

NAME = "Black On Black Love \u2014 Book I: Deep Roots"
DESC = (
    "Black On Black Love: Deep Roots \u2014 Where the Becoming Begins\n\n"
    "Book I of the Black On Black Love series by NAM Oshun.\n\n"
    "A poetic memoir spanning 52 chapters, Deep Roots traces the spiritual and "
    "ancestral foundations of a young Black man coming into his voice. From the "
    "fractured garden of Mama Sylvia to the birth of NAM Oshun himself, this book "
    "is a journey through lineage, love, survival, and the drum that never stopped speaking.\n\n"
    '\u201cBefore my story, before my breath, before my first cry split the air, '
    "there was a woman standing in a fractured garden with her hands in the dirt "
    "and her eyes on the sky.\u201d\n\n"
    "NAM Oshun is the poetic identity of Delon Oliver \u2014 poet, builder, "
    "community architect, and carrier of the Oliver family legacy. His monikers "
    '\u201cPoets Got to Eat Too\u201d and \u201cSlanging Poetry\u201d reflect '
    "his mission: to ensure artists survive, thrive, and are valued.\n\n"
    "This is not just poetry. This is inheritance. This is testimony. "
    "This is architecture for the soul."
)

async def main():
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.post(
            "https://api.gumroad.com/v2/products",
            data={
                "access_token": GUMROAD_KEY,
                "name": NAME,
                "description": DESC,
                "price": 999,
                "published": "true",
            },
        )
    resp = r.json()
    print("Gumroad status:", r.status_code)
    print("Success:", resp.get("success"))
    if resp.get("success"):
        p = resp.get("product", {})
        print("Product ID:", p.get("id"))
        print("URL:", p.get("short_url"))
        print("Name:", p.get("name"))
    else:
        print("Error message:", resp.get("message", resp))

asyncio.run(main())
