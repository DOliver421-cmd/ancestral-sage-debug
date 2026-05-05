import axios from "axios";
import { toast } from "sonner";

// ---------------------------------------------------------------------------
// Domain-portable API base URL.
//
// We want the app to work in three places without a rebuild:
//   1. Local dev (http://localhost:3000 against http://localhost:8001)
//   2. Emergent preview URL (REACT_APP_BACKEND_URL points to preview)
//   3. Production domain — e.g. https://www.wai-institute.org (same-origin)
//
// Strategy: if a REACT_APP_BACKEND_URL was baked at build time AND its host
// matches the current browser host, use it (preserves today's behavior on
// preview). Otherwise, use the browser's current origin — so the deployed
// site at www.wai-institute.org will correctly hit
// https://www.wai-institute.org/api/... without cross-origin hops.
// ---------------------------------------------------------------------------
const ENV_URL = process.env.REACT_APP_BACKEND_URL;
const RUNTIME_ORIGIN = typeof window !== "undefined" ? window.location.origin : "";

function resolveBackendUrl() {
  if (!ENV_URL) return RUNTIME_ORIGIN; // no env var → fall back to same-origin
  if (!RUNTIME_ORIGIN) return ENV_URL; // SSR/node context
  try {
    const envHost = new URL(ENV_URL).host;
    const winHost = new URL(RUNTIME_ORIGIN).host;
    // If build-time URL matches the window, use it (keeps preview happy).
    // If they differ (custom production domain), prefer the live origin so
    // the app stays same-origin on whatever domain it's deployed to.
    return envHost === winHost ? ENV_URL : RUNTIME_ORIGIN;
  } catch {
    return ENV_URL;
  }
}

export const BACKEND_URL = resolveBackendUrl();
export const API = `${BACKEND_URL}/api`;

export const api = axios.create({ baseURL: API });

// Attach JWT on every request
api.interceptors.request.use((cfg) => {
  const t = localStorage.getItem("lce_token");
  if (t) cfg.headers.Authorization = `Bearer ${t}`;
  return cfg;
});

// Global response handling
//   401 anywhere but /auth/login → session expired → clear & redirect.
//   403 "deactivated" → same flow (admin locked this account mid-session).
//   5xx → user-friendly toast.
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
      if (!window.location.pathname.startsWith("/login")) {
        toast.error("Your account has been deactivated.");
        window.location.href = "/login";
      }
    } else if (status >= 500) {
      toast.error("Server error — please try again in a moment.");
    }
    return Promise.reject(err);
  }
);

export const getToken = () => localStorage.getItem("lce_token");
