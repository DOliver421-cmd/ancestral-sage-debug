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

let gates = {};      // { pageKey: enabled }
let loading = null;  // shared in-flight promise

export function getGates() {
  return gates;
}

/** Map a pathname to its gate key (matches the exec PAGE_ACCESS_REGISTRY). */
const PATH_POLICIES = [
  // Longest paths must be checked first so nested controls do not inherit the
  // wrong page key (for example /more/litigation must not become "more").
  ["/more/litigation", "legal-tools"],
  ["/admin/exec-control", "exec"],
  ["/admin/system", "exec"],
  ["/admin/control", "exec"],
  ["/admin/office", "exec"],
  ["/admin/director", "exec"],
  ["/admin/sage-audit", "exec"],
  ["/admin/staff-meetings", "exec"],
  ["/admin/exec-report", "exec"],
  ["/admin", "admin"],
  ["/app/helper", "helper"],
  ["/app/more", "more"],
  ["/partnership/discounts", "partnership"],
  ["/partnership", "partnership"],
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

/** True unless an exec gate explicitly disabled this page. */
export function isPageEnabled(pathname, user = null) {
  const k = pathKey(pathname);
  if (k === "home" || k === "login" || k === "register" || k === "forgot-password") return true;
  const policy = gates[k];
  if (policy === false) return false;
  if (!policy || typeof policy !== "object") return true;
  if (policy.enabled === false) return false;
  const allowedRoles = policy.allowed_roles;
  if (Array.isArray(allowedRoles) && allowedRoles.length > 0) {
    return Boolean(user && allowedRoles.includes(user.role));
  }
  return true;
}

/** Fetch the gate map once; safe to call from anywhere. */
export function loadGates() {
  if (loading) return loading;
  loading = api
    .get("/exec/control/access/public")
    .then((r) => {
      gates = r.data?.pages || {};
      return gates;
    })
    .catch(() => {
      gates = {};
      return gates;
    })
    .finally(() => {
      loading = null;
    });
  return loading;
}
