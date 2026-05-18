import { createContext, useContext, useEffect, useState } from "react";
import { api } from "./api";

const AuthCtx = createContext(null);

function readCachedUser() {
  try {
    const raw = localStorage.getItem("lce_user");
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

function saveUser(u) {
  if (u) localStorage.setItem("lce_user", JSON.stringify(u));
  else localStorage.removeItem("lce_user");
}

export function AuthProvider({ children }) {
  // Restore from localStorage immediately so Protected routes never see a
  // null user while /auth/me is in-flight, which caused spurious /login redirects.
  const [user, setUser] = useState(() => {
    const token = localStorage.getItem("lce_token");
    return token ? readCachedUser() : null;
  });
  // loading=false when we have a cached user — no need to wait for network.
  // loading=true only when we have a token but no cached user (first login on a new device).
  const [loading, setLoading] = useState(() => {
    const token = localStorage.getItem("lce_token");
    return token ? !readCachedUser() : false;
  });

  useEffect(() => {
    const t = localStorage.getItem("lce_token");
    if (!t) { setLoading(false); return; }
    // Verify token and refresh user data from server in the background.
    api.get("/auth/me")
      .then((r) => { setUser(r.data); saveUser(r.data); })
      .catch(() => {
        localStorage.removeItem("lce_token");
        localStorage.removeItem("lce_user");
        setUser(null);
      })
      .finally(() => setLoading(false));
  }, []);

  const login = async (email, password) => {
    const r = await api.post("/auth/login", { email, password });
    localStorage.setItem("lce_token", r.data.access_token);
    saveUser(r.data.user);
    setUser(r.data.user);
    return r.data.user;
  };

  const register = async (payload) => {
    const r = await api.post("/auth/register", payload);
    localStorage.setItem("lce_token", r.data.access_token);
    saveUser(r.data.user);
    setUser(r.data.user);
    return r.data.user;
  };

  const logout = () => {
    localStorage.removeItem("lce_token");
    localStorage.removeItem("lce_user");
    setUser(null);
  };

  const refresh = async () => {
    try {
      const r = await api.get("/auth/me");
      setUser(r.data);
      saveUser(r.data);
      return r.data;
    } catch {
      return null;
    }
  };

  return <AuthCtx.Provider value={{ user, loading, login, register, logout, refresh }}>{children}</AuthCtx.Provider>;
}

export const useAuth = () => useContext(AuthCtx);
