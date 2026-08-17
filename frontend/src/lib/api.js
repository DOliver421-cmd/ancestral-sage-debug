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

// Attach JWT on every request
api.interceptors.request.use((cfg) => {
  const t = localStorage.getItem("lce_token");
  if (t) cfg.headers.Authorization = `Bearer ${t}`;
  return cfg;
});

api.interceptors.response.use(
  (r) => r,
  (err) => {
    const status = err?.response?.status;
    const url = err?.config?.url || "";
    if (status === 401 && !url.includes("/auth/login")) {
      localStorage.removeItem("lce_token");
      localStorage.removeItem("lce_user");
      if (!window.location.pathname.startsWith("/login")) {
        toast.error("Session expired — please sign in again.");
        window.location.href = "/login";
      }
    } else if (status === 403 && err?.response?.data?.detail?.includes("deactivated")) {
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
    } else if (status >= 500) {
      toast.error("Server error — please try again in a moment.");
    }
    return Promise.reject(err);
  }
);

export const getToken = () => localStorage.getItem("lce_token");
