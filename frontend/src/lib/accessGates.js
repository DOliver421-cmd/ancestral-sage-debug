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
export function pathKey(pathname) {
  const p = pathname || "/";
  if (p.startsWith("/admin/exec")) return "exec";
  let segs = p.split("/").filter(Boolean);
  if (segs[0] === "app") segs = segs.slice(1); // /app/more → more, /app/helper → helper
  const seg = segs[0] || "";
  return seg || "home";
}

/** True unless an exec gate explicitly disabled this page. */
export function isPageEnabled(pathname) {
  const k = pathKey(pathname);
  if (k === "home" || k === "login" || k === "register" || k === "forgot-password") return true;
  return gates[k] !== false;
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
