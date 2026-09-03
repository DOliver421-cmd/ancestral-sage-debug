import axios from "axios";
import { toast } from "sonner";

// ── Backend URL resolution ──────────────────────────────────────────────────
// Priority order (highest wins):
//   1. window.__WAI_BACKEND__  — runtime-injected by the deployment (nginx
//      entrypoint or hosting config), no rebuild needed.
//   2. REACT_APP_BACKEND_URL   — build-time env var (split frontend/backend
//      deployments bake the API origin here).
//   3. Same-origin ("")       — the single-service deployment: the backend
//      serves the built React SPA and the API lives at /api on this origin.
//      This is the default so a backend that serves the frontend "just works"
//      with zero configuration and zero CORS.
//
// There is deliberately NO hardcoded fallback host: a dead baked URL silently
// broke every API call on the live site. Same-origin is always the safe floor.
const ENV_URL = process.env.REACT_APP_BACKEND_URL;
const RUNTIME_URL = (typeof window !== "undefined" && window.__WAI_BACKEND__) || "";

export const BACKEND_URL = RUNTIME_URL || ENV_URL || "";
export const API = `${BACKEND_URL}/api`;

export const api = axios.create({ baseURL: API });

/**
 * openAuthedUrl — fetch a backend URL with the session token and open it in a
 * new tab as a blob. Used for the handbooks (GET /api/handbooks/{name} is
 * auth-gated): a plain <a href> opens a tab with no Authorization header and
 * gets a 401, which is exactly why the handbook links appeared broken.
 */
export async function openAuthedUrl(path) {
  const t = localStorage.getItem("lce_token");
  try {
    const res = await fetch(`${API}${path}`, {
      headers: t ? { Authorization: `Bearer ${t}` } : {},
    });
    if (!res.ok) {
      toast.error(`Could not open the document (HTTP ${res.status}).`);
      return;
    }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    window.open(url, "_blank", "noopener,noreferrer");
    setTimeout(() => URL.revokeObjectURL(url), 60_000);
  } catch {
    toast.error("Could not open the document. Try again in a moment.");
  }
}

// Attach JWT on every request
api.interceptors.request.use((cfg) => {
  const t = localStorage.getItem("lce_token");
  if (t) cfg.headers.Authorization = `Bearer ${t}`;
  return cfg;
});

// A 401 only means "your session is dead" when it comes from an auth endpoint
// (token validation) or explicitly names an invalid/expired/revoked token.
// Many endpoints 401 for their own reasons (a resource, a role, a stale
// cross-site token) — wiping the session on those logs the owner out while
// simply navigating, which is exactly the bug we are defending against here.
const AUTH_PATHS = ["/auth/me", "/auth/login", "/auth/register", "/auth/refresh", "/auth/cross-site-login", "/auth/cross-site-token"];

// Admin-scoped endpoints return 403 (not 401) for an authenticated user who
// lacks the role — a 401 here can ONLY mean the token itself is dead (missing,
// expired, or invalid). Without this, an expired session silently 401s every
// panel in the admin/exec surfaces and the page looks like a complete failure
// with no sign-in prompt.
const ADMIN_SCOPE = ["/admin/", "/exec/", "/executive/", "/abo/", "/member-projects/"];

function sessionRejected(status, url) {
  // Canonical auth endpoints, plus admin-scoped endpoints where 401 is
  // unambiguous. Everything else keeps the old behavior: a protected feature
  // may 401 for its own policy or a legacy auth adapter, and treating that as
  // a global logout would trap the owner in a login loop.
  if (status !== 401) return false;
  if (AUTH_PATHS.some((p) => url.includes(p))) return true;
  return ADMIN_SCOPE.some((p) => url.includes(p));
}

api.interceptors.response.use(
  (r) => r,
  (err) => {
    const status = err?.response?.status;
    const url = err?.config?.url || "";
    const detail = err?.response?.data?.detail;
    if (sessionRejected(status, url, detail) && !url.includes("/auth/login")) {
      localStorage.removeItem("lce_token");
      localStorage.removeItem("lce_user");
      if (!window.location.pathname.startsWith("/login")) {
        toast.error("Session expired — please sign in again.");
        const returnTo = `${window.location.pathname}${window.location.search}${window.location.hash}`;
        window.location.href = `/login?returnTo=${encodeURIComponent(returnTo)}`;
      }
    } else if (status === 403 && detail?.includes("deactivated")) {
      localStorage.removeItem("lce_token");
      localStorage.removeItem("lce_user");
      // Avoid redirect loop — only redirect if we're not already on an auth page
      const onAuthPage = ["/login", "/register", "/forgot-password"].some(p => window.location.pathname.startsWith(p));
      if (!onAuthPage) {
        toast.error("This account has been deactivated. Contact support at morehelpcenter@gmail.com to restore access.");
        setTimeout(() => { window.location.href = "/login"; }, 2500);
      }
    } else if (status === 429) {
      toast.error("Too many requests — please slow down and try again shortly.");
    } else if (status >= 500 && !err?.config?.skipGenericErrorToast) {
      toast.error("Server error — please try again in a moment.");
    }
    return Promise.reject(err);
  }
);

export const getToken = () => localStorage.getItem("lce_token");
