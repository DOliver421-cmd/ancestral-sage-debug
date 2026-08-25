# Morehelp.center Starter Library

This directory contains the four original ebook manuscripts for the **Morehelp.center Starter Library**. Each manuscript is intentionally plain Markdown so it can be reviewed, converted, and uploaded through the existing media-store upload flow without introducing a second publishing system.

## Products

- **The Small Start** — A Practical Guide to Turning One Good Idea Into Something Real
- **From Creator to Product** — How to Turn Your Writing, Music, Knowledge, and Ideas Into Things People Can Use
- **AI Without the Intimidation** — A Human-First Guide to Using AI Without Losing Your Judgment
- **The Community Funding Starter** — A Practical Guide to Turning a Good Community Idea Into a Fundable Plan

## Required store setup

The existing `/store` page already reads published records from `GET /api/media/products` and sends paid products to `POST /api/media/products/{id}/checkout`. Upload each Markdown manuscript (or a reviewed PDF/EPUB conversion) through the existing seller flow, set `price_cents` to `400`, `type` to `pdf` or `other`, add the matching cover, and publish it. No new checkout, payment provider, database collection, or storefront is introduced here.

The manuscripts are not represented as sellable products until an authorized owner uploads and publishes them through that existing flow. This prevents a product card from appearing without a real downloadable file and avoids claiming that checkout works before a real purchase verifies it.
