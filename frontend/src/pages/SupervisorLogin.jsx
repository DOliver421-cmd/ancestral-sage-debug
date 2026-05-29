import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../lib/auth";

const INK    = "#2e1065";
const SIGNAL = "#FFD100";
const BONE   = "#F7F7F5";

export default function SupervisorLogin() {
  const { login, user } = useAuth();
  const nav = useNavigate();
  const [email,    setEmail]    = useState("");
  const [password, setPassword] = useState("");
  const [loading,  setLoading]  = useState(false);
  const [error,    setError]    = useState("");

  // Already logged in as exec — go straight to supervisor
  if (user && user.role === "executive_admin") {
    nav("/supervisor", { replace: true });
    return null;
  }

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const u = await login(email, password);
      if (u.role !== "executive_admin") {
        setError("Access denied. Supervisor access requires executive authorization.");
        setLoading(false);
        return;
      }
      if (u.must_change_password) {
        nav("/settings?force=1");
        return;
      }
      nav("/supervisor", { replace: true });
    } catch (err) {
      setError(err?.response?.data?.detail || "Authentication failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ minHeight: "100vh", background: "#0b1225", display: "flex", alignItems: "center", justifyContent: "center", padding: 24 }}>
      <div style={{ background: "#fff", borderRadius: 14, padding: "40px 36px", width: "100%", maxWidth: 380, boxShadow: "0 8px 40px rgba(0,0,0,0.5)" }}>

        {/* Logo */}
        <div style={{ width: 56, height: 56, background: INK, borderRadius: "50%", margin: "0 auto 16px", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 22, fontWeight: 800, color: SIGNAL }}>S</div>

        <h2 style={{ textAlign: "center", fontSize: 22, fontWeight: 800, color: INK, marginBottom: 4 }}>Supervisor Access</h2>
        <p style={{ textAlign: "center", fontSize: 13, color: "#6b7280", marginBottom: 28 }}>WAI-Institute · Executive Portal</p>

        {error && (
          <div style={{ background: "#fee2e2", border: "1px solid #fca5a5", borderRadius: 8, padding: "10px 14px", marginBottom: 16, fontSize: 13, color: "#991b1b", textAlign: "center" }}>
            {error}
          </div>
        )}

        <form onSubmit={submit}>
          <label style={{ display: "block", fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: 1, color: "#6b7280", marginBottom: 6 }}>
            Executive Email
          </label>
          <input
            type="email"
            required
            value={email}
            onChange={e => setEmail(e.target.value)}
            placeholder="exec@wai-institute.org"
            style={{ width: "100%", padding: "11px 14px", border: "1.5px solid #e5e7eb", borderRadius: 7, fontSize: 14, outline: "none", marginBottom: 14, color: "#1a1a2e", boxSizing: "border-box" }}
          />

          <label style={{ display: "block", fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: 1, color: "#6b7280", marginBottom: 6 }}>
            Password
          </label>
          <input
            type="password"
            required
            value={password}
            onChange={e => setPassword(e.target.value)}
            placeholder="••••••••"
            style={{ width: "100%", padding: "11px 14px", border: "1.5px solid #e5e7eb", borderRadius: 7, fontSize: 14, outline: "none", marginBottom: 20, color: "#1a1a2e", boxSizing: "border-box" }}
          />

          <button
            type="submit"
            disabled={loading}
            style={{ width: "100%", padding: 12, background: loading ? "#6b7280" : INK, color: "#fff", border: "none", borderRadius: 7, fontSize: 14, fontWeight: 700, cursor: loading ? "not-allowed" : "pointer" }}
          >
            {loading ? "Authenticating…" : "Enter Supervisor Panel"}
          </button>
        </form>

        <p style={{ textAlign: "center", fontSize: 11, color: "#9ca3af", marginTop: 20 }}>
          Restricted access · Authorized personnel only
        </p>
        <p style={{ textAlign: "center", fontSize: 12, marginTop: 8 }}>
          <Link to="/login" style={{ color: INK, textDecoration: "underline" }}>← Main Platform Login</Link>
        </p>
      </div>
    </div>
  );
}
