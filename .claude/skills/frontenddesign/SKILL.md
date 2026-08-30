---
name: frontenddesign
description: "Frontend UI/UX design review and implementation for the WAI / morehelp.center design system"
---

# frontenddesign

Review and build frontend UI/UX consistent with the WAI / M.O.R.E. Help Center
design language: copper + ink palette, high-contrast surfaces, the AppShell +
BoundedAdmin layout, and the hybrid-NAM / provider console patterns already in
`frontend/src`.

## Steps

1. Load the design tokens from `frontend/src/index.css` (CSS vars: `--copper`,
   `--ink`, `.text-opaque-muted`, `.text-opaque-faint`) and the Tailwind config.
2. Inventory the page against the intended user flow — every control must have a
   visible label, a purpose, and a real wired handler (no cosmetic placeholders).
3. Check layout against the established shells: `AppShell.jsx` (nav), `BoundedAdmin`
   (role-gated admin pages), `ProviderGateway.jsx` (card-grid + toast pattern).
4. Verify responsive behavior and that new components reuse existing primitives
   rather than introducing divergent styling.
5. Report deviations and a minimal fix list (file:line) that restores consistency.

## Constraints

- Never claim a UI "works" without confirming the control triggers a real API call
  or state change (pair with `fra` / `frontendworkflowauditor`).
- Preserve WCAG 2.1 AA contrast — do not reintroduce `text-ink/40`-style
  low-contrast classes; use `.text-opaque-muted` / `.text-opaque-faint`.
- Cite `frontend/src` file:line for every finding.
