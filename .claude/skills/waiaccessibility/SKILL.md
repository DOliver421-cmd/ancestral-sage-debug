---
name: waiaccessibility
description: "WCAG 2.1 AA accessibility audit and fixes for the WAI / morehelp.center frontend"
---

# waiaccessibility

Audit and remediate frontend accessibility to WCAG 2.1 AA: contrast, labels,
keyboard/focus, and ARIA. This repo already carries the `.text-opaque-muted`
(`#4a4238`) and `.text-opaque-faint` (`#5e4b8d`) high-contrast utilities as the
replacement for low-contrast `text-ink/55` / `text-ink/40` classes.

## Steps

1. Scan `frontend/src` for low-contrast utility usage (`text-ink/40`, `text-ink/55`,
   `opacity-40` text) and replace with `.text-opaque-muted` / `.text-opaque-faint`.
2. Flag every form control (input, select, textarea) missing an associated
   `<label>` or `aria-label`; add one per control.
3. Verify focus-visible states exist for interactive elements and that the tab
   order follows the visual order.
4. Check `role`/`aria-*` usage is correct (no redundant or conflicting ARIA).
5. Run a keyboard-only pass (Tab / Shift+Tab / Enter) on the target flow.
6. Report PASS only when contrast ≥ 4.5:1 for body text, all controls labeled,
   and the flow is keyboard-operable.

## Constraints

- Contrast must meet 4.5:1 (3:1 for large text) — verify with a contrast tool,
  do not eyeball.
- The fix applied in `BusinessOffice.jsx` (42 replacements + aria-labels) is the
  reference pattern; reuse it.
- Cite file:line for each violation and its remediation.
