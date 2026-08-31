---
name: completesitemap
description: "Full site-map generation/audit"
---

# completesitemap

Produce or verify a complete map of every route, page, and nav entry — including dead links.

## Steps

1. Crawl the router/page registry and the frontend route table.
2. Diff declared routes vs reachable pages vs nav links.
3. Flag orphan pages and nav links with no destination.
4. Report a complete sitemap plus the gap list.

## Constraints

- Verify by execution where possible; never report working on source inspection alone.
- Cite file:line evidence for every finding.
- Report DONE/PASS only when the live behavior matches the intended purpose.
