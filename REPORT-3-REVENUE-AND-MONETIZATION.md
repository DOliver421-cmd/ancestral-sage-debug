# REPORT 3 — How This Platform Makes Money (Plain Business Terms)

**Date:** August 24, 2026 · **Method:** every money path below was traced through the actual code this session. Where a path was proven only with simulated responses, it says so.

---

## The ways the platform earns

1. **Monthly memberships** — five levels: free, member ($9/mo), plus ($15/mo), pro ($29/mo), patron ($59/mo).
2. **$3 all-access trial** — a one-time 3-day taste of everything through the pro level.
3. **$3 AI unlock** — a one-time purchase that lets members run AI through their own provider key (the platform never pays for customers' AI usage).
4. **Creator product sales** — creators sell digital products (prompt packs, templates, beats, media). **The platform keeps 30% of every sale; the creator keeps 70%.** This split is built into the payout tracking.
5. **Donations** — free-will support in any amount.
6. **Promo codes** — discount and access codes with validation and one-time-use reservation built in.
7. **Scholarship sponsorships** — sponsors pledge money; funds are released to approved applicants as they hit progress milestones.

## Are the money paths actually wired to real processing?

| Path | Price calculation | Payment routing | Money reaching the right hands |
|---|---|---|---|
| Memberships | Built in, correct | **Fixed today** — buyers now reach a real payment page | Wired: payment confirmation automatically upgrades the account. **Never proven with a real payment.** |
| $3 trial / $3 AI unlock | Built in | Same checkout path | Same wiring, same proof gap |
| Creator sales (70/30) | Built in | Same checkout path | The 70/30 split is tracked per sale and payouts accumulate monthly. Payouts are **recorded, not automatically sent** — someone must actually pay creators out. |
| Donations | Buyer chooses the amount | Same checkout path | Recorded on payment |
| Promo codes | Validation built in | Applies before checkout | Working logic, not proven with a live purchase |
| Physical merchandise | — | **Deliberately blocked** — the system refuses these orders | Not available |
| Scholarship pledges | Built in | Same checkout path | Funds release on milestones; pledge payment wired to the same checkout |

## What was broken and what changed today

Until today, **every one of these money paths hit the same dead end**: the system prepared the payment correctly and then sent the buyer to a page where buying is impossible. That single flaw made the entire monetization model unusable, regardless of whether payment keys were configured.

Today's fix sends buyers to the payment provider's real checkout page, with their account email pre-filled so the purchase reliably connects back to their account and the upgrade (or creator credit) actually lands.

## The honest bottom line

- The **structure** to earn — tiers, splits, trials, codes, payouts — is genuinely built, not faked.
- The **critical broken link** (buyers reaching a real payment page) was found and fixed today.
- What is still missing: **one real completed purchase** proving money actually moves and the account upgrade actually lands. Until that happens, the revenue model is correctly wired but unproven.
- Creator payouts require a human to actually send money monthly — the system tracks it; it does not pay it.

## August 26, 2026 — deploy-status correction

Nothing here changes the "one real completed purchase" gate, which remains the single open proof for monetization. For accuracy: the store catalog ship (two $29 AI-authored books with covers, membership cards on `/store`) is now **committed to `main` and deploying** (commit `98c79cd`), not merely in the working tree. Also newly shipped in `98c79cd`: per-tier daily AI budgets scale free→patron (more feature access = more API allowance) and OpenAI/DeepSeek are wired as text tiers so members on those keys get live AI instead of keyword KB. The revenue-relevant consequence: a real purchase must still be watched end to end on the deployed site before "revenue works" can be signed off.
