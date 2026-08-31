/**
 * accessGates — tiny shared store for exec-controlled page access.
 *
 * The executive control layer (`/exec/control/access`) toggles whether each
 * page is reachable. This store fetches the public gate map once and exposes:
 *   - loadGates()        — fetch (idempotent, shared promise)
 *   - isPageEnabled(path) — true unless exec explicitly disabled the page
 *
 * App.js blocks disabled routes; AppShell filters nav items with the same
 * matcher, so a disabled page disappears from navigation AND from the router.
 */
import { api } from "./api";
import { isNavItemVisible } from "./navAccess";

let gates = {};      // { pageKey: { enabled, allowed_roles, allowed_tiers, public_access, navigation_visible } }
let loading = null;  // shared in-flight promise
let gatesFailed = false;  // true when the gate fetch threw
let launchMode = false;   // mirrors backend db.platform_flags.flags.launch_mode.enabled

export function getGates() {
  return gates;
}

export function isGatesFailed() {
  return gatesFailed;
}

export function isLaunchMode() {
  return launchMode;
}

/** Map a pathname to its gate key (matches the exec PAGE_ACCESS_REGISTRY). */
const PATH_POLICIES = [
  // Longest paths must be checked first so nested controls do not inherit the
  // wrong page key (for example /more/litigation must not become "more").
  ["/more/litigation", "legal-tools"],
  ["/admin/exec-control", "exec-control"],
  ["/admin/system", "exec"],
  ["/admin/control", "site-control"],
  ["/admin/office", "exec-business-office"],
  ["/admin/director", "director"],
  ["/admin/sage-audit", "exec"],
  ["/admin/staff-meetings", "exec"],
  ["/admin/exec-report", "exec"],
  ["/admin/accounts", "account-controls"],
  ["/admin", "admin"],
  ["/app/helper", "helper"],
  ["/app/more", "more"],
  ["/partnership/discounts", "partnership-discounts"],
  ["/partnership", "partnership"],
  ["/creator/payouts", "creator-payouts"],
  ["/missing-kameron", "missing-kameron"],
];

export function pathKey(pathname) {
  const p = pathname || "/";
  const explicit = PATH_POLICIES.find(([prefix]) => p === prefix || p.startsWith(`${prefix}/`));
  if (explicit) return explicit[1];
  let segs = p.split("/").filter(Boolean);
  if (segs[0] === "app") segs = segs.slice(1); // /app/more → more, /app/helper → helper
  const seg = segs[0] || "";
  return seg || "home";
}

/**
 * isPageEnabled — one projection of the canonical Feature Registry gate map.
 *
 * Resolves the page key and delegates the decision to the pure shared module
 * (src/lib/navAccess.js) so the sidebar and the node integrity test run the
 * exact same logic. Navigation visibility is UX only — the backend is
 * authoritative.
 */
export function isPageEnabled(pathname, user = null) {
  return isNavItemVisible(pathKey(pathname), user, gates[pathKey(pathname)]);
}

/** Fetch the gate map once; safe to call from anywhere. */
export function loadGates() {
  if (loading) return loading;
  loading = api
    .get("/exec/control/access/public")
    .then((r) => {
      gates = r.data?.pages || {};
      launchMode = r.data?.launch_mode === true;
      gatesFailed = false;
      return gates;
    })
    .catch(() => {
      gatesFailed = true;
      return gates;
    })
    .finally(() => {
      loading = null;
    });
  return loading;
}
