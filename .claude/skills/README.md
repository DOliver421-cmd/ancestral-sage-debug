# Agent skills — index and maintenance rules

`.claude/skills/` is the **single** agent-skill store for this repository
(Claude Code convention: one directory per skill, each containing `SKILL.md`).
Do not create a second skill store elsewhere (e.g. `.opencode/skills` or
`skills/`) — that is how drift and duplicates start.

## Ground rules (binding)

1. **Every skill must be repo-specific.** This checkout is MoreHelp Center:
   FastAPI + Motor/MongoDB backend (`backend/`), CRA React 18 frontend
   (`frontend/`), Railway deployment. A skill that does not cite `file:line`
   evidence from THIS repo and its execution environment does not belong here.
2. **Read `_shared/REPO-REALITY.md` first.** It is the evidence anchor every
   skill builds on: the five bug-generating patterns (P1–P5), the two-DB-layer
   split, the three auth mechanisms, container limits (no `mongod`, use
   `python3`), and the §9 reporting vocabulary.
3. **"Working" means executed.** Per `AGENTS.md` (Done Means Working / Working
   Means Executed): `source-confirmed` ≠ `route-registered` ≠ working. Never
   report `DONE`/`PASS` from source inspection. Mark what cannot be run
   `ENVIRONMENT BLOCKED`.
4. **No duplicates.** Before adding a skill, confirm no existing skill covers
   the purpose (table below). One purpose → one skill. Generic, repo-agnostic
   boilerplate skills are noise here and were removed in the 2026-09-06 audit.

## Inventory (13 skills)

| Skill | Purpose | Pair with |
|---|---|---|
| `aad` | Agent/AI architecture audit: `llm_gateway`, persona loader, keyvault/BYOK, scheduler jobs, failover watchdog, autonomy blast radius | `seca`, `databasepersistenceauditor` |
| `apicompleteness` | **DONE gate** for any API/endpoint/feature claim: route → auth → request → persistence → response → render, all proven | `fra`, `cea` |
| `apiendpointauditor` | Enumerate the registered 631-path surface; find phantom routes (router failed to import) and shadowed `(method,path)` duplicates | `frgk`, `cea` |
| `cea` | Code-execution audit: prove claims by importing the app and executing paths (`implemented != working`) | `apicompleteness` |
| `databasepersistenceauditor` | Mongo reality check: live vs near-dead DB layer, `bind()`/`None` handles, read-after-write shape contract | `aad` |
| `entitlementmembershipauditor` | 8-rank RBAC + feature-tier matrix: executed allows **and** denies across all four enforcement points | `seca` |
| `fra` | Functional reality audit: strictest "does it work for a human" gate — trace click → request → registration → auth → persistence → render | `apicompleteness`, `frgk` |
| `frgk` | Frontend↔backend gap: axios/`fetch`/`openAuthedUrl` call sites vs registered routes, shapes, status-code contracts | `apiendpointauditor` |
| `frontenddesign` | Frontend UI/UX design review & implementation in the copper/ink design system | `tailwindui`, `waiaccessibility` |
| `hybridnamsoulauditor` | Hybrid NAM (Assistant Director): 12-pillar behavior audit vs `docs/HYBRID_NAM_SPEC.md` and the live `/api/nam` surface | `cea`, `fra` |
| `seca` | Security audit: three competing auth mechanisms, gateway snapshot boundary, CORS, rate limits, secrets, SSO | `entitlementmembershipauditor` |
| `tailwindui` | Tailwind utility/component guidance against the repo's token system | `frontenddesign` |
| `waiaccessibility` | WCAG 2.1 AA audit + remediation for the frontend | `frontenddesign` |

## Removal log — 2026-09-06 duplicate audit

Seventeen skills were removed because they were generic cookie-cutter templates
(identical four-step structure, zero repo references, same boilerplate
constraints repeated across all of them) that duplicated each other or the
repo-specific skills above. Coverage was already provided by:

| Removed | Duplicated / replaced by |
|---|---|
| `arenaaiauditor` | `seca`, `hybridnamsoulauditor` (adversarial probing) |
| `completesitemap` | `apiendpointauditor` + `frgk` (registered routes vs frontend) |
| `csh` | `apiendpointauditor`, `aad` (structure/health leads) |
| `dependencyintegrationtracer` | `aad`, `databasepersistenceauditor`, anchor P1–P4 |
| `featureduplicatedetector` | `apiendpointauditor` §3 (shadowed duplicates) |
| `frontendworkflowauditor` | `fra` (render-chain audit) |
| `functionreality` | `cea` (single-function execution check) |
| `gapfiller` | `apicompleteness`/`fra` doctrine + `AGENTS.md` |
| `mvaud` | `fra`, `cea`, `apicompleteness` |
| `pad` | anchor §8 (docs must match reality) |
| `pca` | `csh`-family removal; no repo-specific replacement added |
| `pstest` | `aad` (prompt guard / live-path checks) |
| `rdaud` | `seca` |
| `repodiscovery` | `_shared/REPO-REALITY.md` (the orientation anchor) |
| `rgaud` | `cea`, `fra` (baseline re-execution) |
| `superagentprotocol` | not repo-specific; no in-repo consumer |
| `ura` | `seca`, `aad` |

`git log` preserves all removed files if a purpose genuinely re-emerges — in
that case reintroduce it as a **repo-specific** skill, not the old template.
