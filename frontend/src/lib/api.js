import axios from "axios";
import { toast } from "sonner";

// Always use REACT_APP_BACKEND_URL if set (Render production).
// Fall back to the known production backend host when deployed as static
// assets where a runtime proxy may not be available.
const ENV_URL = process.env.REACT_APP_BACKEND_URL;
const RUNTIME_ORIGIN = typeof window !== "undefined" ? window.location.origin : "";

// Fallback backend URL (production deployed backend). This ensures the
// frontend will contact the real API even when the static host does not
// provide a runtime proxy for /api/ paths.
const FALLBACK_BACKEND = "https://ancestral-sage-debug-production.up.railway.app";

export const BACKEND_URL = ENV_URL || RUNTIME_ORIGIN || FALLBACK_BACKEND;
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
      if (!window.location.pathname.startsWith("/login")) {
        toast.error("Your account has been deactivated.");
        window.location.href = "/login";
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
