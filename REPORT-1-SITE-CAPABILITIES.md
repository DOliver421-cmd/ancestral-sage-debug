# REPORT 1 — What This Site Actually Does For A Real Person Right Now

**Date:** August 24, 2026 · **Basis:** every claim below was checked against the running code during this session. Where something could not be proven, it says so.

---

## What a visitor can do without an account

- **Browse the public site** — landing pages, help center, knowledge base, site guide, and community boards load and display content.
- **Read the community boards** — public posts and a public "needs" board are readable.
- **See membership prices** — the plans page shows all five levels plus the $3 trial.
- **Register an account** — sign-up and sign-in pages exist and are wired to the sign-in system.
- **Listen to music** — two music players are embedded on the gateway page. *The owner reports these players are broken. The embed code is the standard, current format, so the break is most likely on the music platform's side (deleted or changed tracks) — this is unresolved and listed in the Defect Log.*

## What a signed-in member can do

- **Take courses** — course catalog, lessons, progress tracking, completion certificates, and a personal portfolio.
- **Earn recognition** — a points system, levels, leaderboards, and skill competencies that unlock as labs are completed.
- **Use AI help** — an AI tutor and a set of AI assistants. When no AI provider key is active, these quietly answer from the built-in knowledge base instead of saying "AI is down" — the user is never told the difference.
- **Create and sell** — a creator studio to write lyrics/scripts with AI help, build beats with a step sequencer, and publish digital products for sale.
- **Join the community** — post, comment, chat, request collaborations, and book bands.
- **Play** — an arcade with playable games and daily puzzles that award points.
- **Manage their account** — profile, avatar, password, email preferences, download their data, or delete their account.

## What administrators can do

- **Run the member list** — search, edit, promote, deactivate, and delete accounts.
- **See the business office** — an executive dashboard hub with projects, tools, and operations panels.
- **Watch system health** — live status pages showing whether the server and database are up.
- **Control access** — role and tier gating, feature controls, promo codes, scholarship management.
- **See the audit trail** — privileged actions are logged.

## What works vs. what is hollow

**Works (proven by running it):**
- Every one of the 45 main pages loads without crashing — including when the data behind them is missing or malformed.
- Every link in the sidebar and every route on the site points to a real page. Zero dead links (checked automatically across 167 routes).
- The sign-in system, courses, community, creator studio, arcade, and admin tools all load and respond.

**Hollow or limited (be honest):**
- **The store is not really "ours."** The store page shows an external storefront inside a window frame. Buying there happens on the external site, not on this one. Our own product catalog exists behind the scenes, but the store page does not display or sell it.
- **Physical merchandise cannot be bought** — the system deliberately refuses these orders.
- **62 of 140 pages have no sidebar** — they open as bare pages without site navigation.
- **Money features were broken until today** — clicking a plan sent buyers to a dead end (see Report 3 and Report 4 for the fix and its limits).
