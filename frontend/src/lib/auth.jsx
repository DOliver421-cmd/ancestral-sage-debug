import { createContext, useContext, useEffect, useState } from "react";
import { api } from "./api";

const AuthCtx = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const t = localStorage.getItem("lce_token");
    if (!t) { setLoading(false); return; }
    api.get("/auth/me").then((r) => setUser(r.data)).catch(() => localStorage.removeItem("lce_token")).finally(() => setLoading(false));
  }, []);

  const login = async (email, password) => {
    const r = await api.post("/auth/login", { email, password });
    localStorage.setItem("lce_token", r.data.access_token);
    setUser(r.data.user);
    return r.data.user;
  };

  const register = async (payload) => {
    const r = await api.post("/auth/register", payload);
    localStorage.setItem("lce_token", r.data.access_token);
    setUser(r.data.user);
    return r.data.user;
  };

  const logout = () => {
    localStorage.removeItem("lce_token");
    setUser(null);
  };

  const refresh = async () => {
    try {
      const r = await api.get("/auth/me");
      setUser(r.data);
      return r.data;
    } catch {
      return null;
    }
  };

  return <AuthCtx.Provider value={{ user, loading, login, register, logout, refresh }}>{children}</AuthCtx.Provider>;
}

export const useAuth = () => useContext(AuthCtx);
