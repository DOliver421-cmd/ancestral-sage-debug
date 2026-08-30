---
name: tailwindui
description: "Tailwind CSS utility and component-pattern guidance for this project"
---

# tailwindui

Apply Tailwind utilities and component patterns consistent with this repo's
Tailwind setup (see `tailwind.config.js` and `frontend/src/index.css`). Avoid
arbitrary one-off values that break the design system.

## Steps

1. Read `tailwind.config.js` theme extension and `frontend/src/index.css` to learn
   the available tokens (colors, spacing, the copper/ink semantic classes).
2. Prefer semantic classes already defined (`.btn-copper`, `.text-opaque-muted`,
   card/panel wrappers) over inline `style=` or raw hex values.
3. When adding a component, mirror an existing one (e.g. `ProviderGateway.jsx`
   card grid, `AdminPage` wrapper) for spacing/radius/shadow consistency.
4. Check dark/light surfaces use the token vars so they track theme changes.
5. Report any new utility that should be promoted to a shared class.

## Constraints

- Do not hardcode colors that already exist as tokens.
- Keep utility usage readable; extract repeated patterns into a component or
  shared class rather than copy-pasting long class strings.
- Cite file:line for examples and proposed extractions.
