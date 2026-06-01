"""
Create "Coming Soon" listings on Gumroad for Books II, III, IV.
Run:  python scripts/tools/publish_coming_soon.py
"""

import os, httpx, asyncio
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'), override=True)
KEY = os.environ.get("GUMROAD_API_KEY", "")

BOOKS = [
    {
        "name": "Black On Black Love \u2014 Book II: Reclamation (Coming Soon)",
        "desc": (
            "Black On Black Love: Reclamation \u2014 The Healing of a Man\n\n"
            "Book II of the Black On Black Love series by NAM Oshun.\n\n"
            "Picking up where Deep Roots left off, Reclamation follows the journey "
            "of healing, self-confrontation, and the return to the door of unfinished feelings. "
            "This is the story of a man learning to reclaim what was lost, buried, and forgotten.\n\n"
            "Coming soon. Sign up to be notified at launch."
        ),
        "price": 999,
    },
    {
        "name": "Black On Black Love \u2014 Book III: Ascension (Coming Soon)",
        "desc": (
            "Black On Black Love: Ascension \u2014 The Return to the Inner Temple\n\n"
            "Book III of the Black On Black Love series by NAM Oshun.\n\n"
            "The ascent continues. Ascension is the return to the inner temple, "
            "the conversation with the shadow, and the integration of all that came before. "
            "A man who rises must return. A man who returns must live.\n\n"
            "Coming soon. Sign up to be notified at launch."
        ),
        "price": 999,
    },
    {
        "name": "Black On Black Love \u2014 Book IV: Ascension II (Coming Soon)",
        "desc": (
            "Black On Black Love: Ascension II \u2014 We Ascend Again\n\n"
            "Book IV of the Black On Black Love series by NAM Oshun.\n\n"
            "The final chapter of the Black On Black Love series. Ascension II is the moment "
            "the universe opens again, the boy who chose love returns as the man who remembers, "
            "and the crown is claimed. Love is the crown. And we \u2014 Black, sovereign, ascended \u2014 wear it.\n\n"
            "Coming soon. Sign up to be notified at launch."
        ),
        "price": 999,
    },
]

async def main():
    async with httpx.AsyncClient(timeout=20) as client:
        for book in BOOKS:
            r = await client.post(
                "https://api.gumroad.com/v2/products",
                data={
                    "access_token": KEY,
                    "name": book["name"],
                    "description": book["desc"],
                    "price": book["price"],
                    "published": "true",
                },
            )
            resp = r.json()
            if resp.get("success"):
                p = resp.get("product", {})
                print(f"OK  {book['name']}")
                print(f"    URL: {p.get('short_url')}")
            else:
                print(f"ERR {book['name']}: {resp.get('message', resp)}")
            print()

asyncio.run(main())
