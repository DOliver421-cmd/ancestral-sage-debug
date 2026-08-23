# COMPLIANCE / TRUST AUDIT (Phase 20)

**Method:** source inspection this session. **No legal review has occurred** — this is a surface inventory, not legal advice.

## Present (SRC)

- Terms of Service — `/terms` (TermsOfService.jsx, 126 lines, public).
- Privacy Policy — `/privacy` (PrivacyPolicy.jsx, **45 lines**, public).
- Cookie consent — component mounted globally, posts choice to `/consent/cookie`.
- Age gate — registration requires `over_13` confirmation.
- Consent record — `terms_accepted_at` timestamp on registration (GDPR audit trail).
- Account deletion — `DELETE /auth/account`.
- Data export — `GET /auth/account/export`.
- Re-consent — `POST /auth/reconsent`.
- Erasure test exists (`tests/test_erasure.py`).

## Incomplete / thin (SRC)

- **Privacy policy is 45 lines** for a platform handling accounts, payments (email/order data), AI prompts, BYOK keys, and media uploads. **REQUIRES LEGAL REVIEW.**
- **Refund policy text: not found** on public pages (admin refund tooling exists in code, but no customer-facing refund/cancellation disclosure was located).
- Terms (126 lines) may be too thin to cover subscriptions, auto-renewal, cancellation, marketplace, and AI-generated content; requires legal review.

## Missing (not found this session — verify before launch)

- Acceptable-use / content-moderation policy text.
- Creator/publisher terms; marketplace seller terms.
- Copyright/IP language for user-uploaded content and AI-generated content disclosure.
- Data-retention description; children's-specific handling beyond the 13+ gate.
- Accessibility statement (if claimed anywhere).
- AI disclosure on public AI surfaces (helper teaser) — consider a simple "AI-assisted answer" note.

## Status per category

| Surface | Status |
|---|---|
| Terms | PRESENT / REQUIRES LEGAL REVIEW |
| Privacy | PRESENT but THIN / REQUIRES LEGAL REVIEW |
| Cookie consent | PRESENT |
| Account deletion / export | PRESENT |
| Refund policy | MISSING (text) / admin tooling exists |
| Acceptable use / moderation policy | MISSING |
| Creator/marketplace terms | MISSING |
| AI disclosure | MISSING |
| Accessibility statement | MISSING |

## Recommended before campaign (P1)

Publish refund/cancellation disclosure (align with LS policies), expand privacy to cover payments + AI + BYOK, and add AI disclosure to the public helper. All text requires legal review.
