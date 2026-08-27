import { useState, useEffect, useCallback } from "react";
import { api } from "../lib/api";
import AppShell from "../components/AppShell";
import PageBack from "../components/PageBack";
import {
  KeyRound, ShieldCheck, ExternalLink, Trash2, Plug, CheckCircle2,
  CircleDollarSign, Loader2, RefreshCw, AlertTriangle,
} from "lucide-react";

// ── Design tokens ─────────────────────────────────────────────────────────────
const COPPER = "#b5651d";
const INK = "#1a1a1a";
const BONE = "#f5f0e8";

const inputStyle = {
  width: "100%",
  border: "1.5px solid #ddd",
  borderRadius: 8,
  padding: "10px 12px",
  fontSize: 14,
  color: INK,
  background: "#fff",
  outline: "none",
};

function Card({ title, icon: Icon, children, right }) {
  return (
    <div style={{ background: "#fff", border: `1.5px solid ${BONE}`, borderRadius: 14, padding: 20, marginBottom: 16, boxShadow: "0 1px 3px rgba(0,0,0,0.04)" }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 14, gap: 12, flexWrap: "wrap" }}>
        <h2 style={{ margin: 0, fontSize: 15, fontWeight: 800, color: INK, display: "flex", alignItems: "center", gap: 8 }}>
          {Icon && <Icon color={COPPER} size={18} />} {title}
        </h2>
        {right}
      </div>
      {children}
    </div>
  );
}

export default function BYOK() {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState(null);
  const [busyProvider, setBusyProvider] = useState(null);
  const [keyInputs, setKeyInputs] = useState({});
  const [adminStats, setAdminStats] = useState(null);

  // Instructor tier and above get BYOK free; everyone below pays $3 one-time.
  const byokPrice = status?.price_usd ?? 3;
  const byokFree = status?.free_for_role || byokPrice === 0;

  const flash = (msg) => {
    setToast(msg);
    setTimeout(() => setToast(null), 4000);
  };

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await api.get("/byok/status");
      setStatus(data);
    } catch (e) {
      flash(e?.response?.data?.detail || "Could not load BYOK status.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    // Admin aggregate view (ignored if the user lacks access).
    const u = JSON.parse(localStorage.getItem("lce_user") || "{}");
    if (u?.role === "admin" || u?.role === "executive_admin") {
      api.get("/byok/admin").then(({ data }) => setAdminStats(data)).catch(() => {});
    }
  }, [load]);

  const activate = async () => {
    setBusyProvider("activate");
    try {
      // Checkout first: instructors activate free; below-instructor users get
      // a $3 payment session (the webhook flips byok_enabled once paid).
      const { data } = await api.post("/byok/checkout");
      if (data?.url) {
        window.location.href = data.url;
        return;
      }
      setStatus((s) => ({ ...s, enabled: true, activated_at: data.activated_at, price_usd: data.price_usd, free_for_role: data.free_for_role }));
      flash(data?.free_for_role
        ? "BYOK activated — included free with your instructor account."
        : data?.grace
        ? "BYOK activated — $3 unlock recorded (payments pending setup)."
        : `BYOK activated — $${data.price_usd} entitlement enabled.`);
    } catch (e) {
      flash(e?.response?.data?.detail || "Activation failed.");
    } finally {
      setBusyProvider(null);
    }
  };

  const saveAndTest = async (provider) => {
    const key = (keyInputs[provider] || "").trim();
    if (!key) {
      flash("Paste your API key first.");
      return;
    }
    setBusyProvider(provider);
    try {
      await api.post("/byok/key", { provider, key });
      const { data } = await api.post(`/byok/key/${provider}/test`, { provider, key });
      await load();
      flash(data?.ok
        ? `${provider} key saved & verified (${data.latency_ms}ms). Your AI requests now route through your key.`
        : `Key saved, but the test failed: ${data?.error || "unknown error"}`);
      setKeyInputs((s) => ({ ...s, [provider]: "" }));
    } catch (e) {
      flash(e?.response?.data?.detail || "Could not save that key.");
    } finally {
      setBusyProvider(null);
    }
  };

  const removeKey = async (provider) => {
    setBusyProvider(provider);
    try {
      await api.delete(`/byok/key/${provider}`);
      await load();
      flash(`${provider} key removed.`);
    } catch (e) {
      flash(e?.response?.data?.detail || "Could not remove that key.");
    } finally {
      setBusyProvider(null);
    }
  };

  const isBusy = (p) => busyProvider === p;

  return (
    <AppShell>
      <div style={{ maxWidth: 880, margin: "0 auto", padding: "28px 20px" }}>
        <PageBack to="/dashboard" label="Dashboard" />
        {/* Header */}
        <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 16, flexWrap: "wrap", marginBottom: 8 }}>
          <div>
            <h1 style={{ margin: 0, fontSize: 28, fontWeight: 900, color: INK, letterSpacing: "-0.02em", display: "flex", alignItems: "center", gap: 12 }}>
              <KeyRound color={COPPER} size={28} /> Bring Your Own Key
            </h1>
            <p style={{ margin: "6px 0 0", color: "#666", fontSize: 14, maxWidth: 620 }}>
              {byokFree ? (
                <>
                  <strong style={{ color: INK }}>Included free</strong> with your instructor account — attach a key from one of
                  three free providers and your AI runs on your own key. The platform never pays for your generation.
                </>
              ) : (
                <>
                  A one-time <strong style={{ color: INK }}>$3</strong> unlock that gives your profile real AI. Bring a key from one of
                  three free providers — the platform never pays for your generation, and you never hand over a credit card.
                  <span style={{ color: "#888" }}> Instructors and above get BYOK free.</span>
                </>
              )}
            </p>
          </div>
          <div style={{
            background: status?.enabled ? "#e7f4ec" : "#fdf1e3",
            color: status?.enabled ? "#1b7a3d" : COPPER,
            fontSize: 12, fontWeight: 800, textTransform: "uppercase", letterSpacing: "0.08em",
            padding: "6px 12px", borderRadius: 999, whiteSpace: "nowrap",
          }}>
            {status?.enabled ? "● BYOK active" : "○ BYOK not activated"}
          </div>
        </div>

        {toast && (
          <div style={{ background: INK, color: "#fff", fontSize: 13, padding: "10px 16px", borderRadius: 8, margin: "12px 0", lineHeight: 1.5 }}>
            {toast}
          </div>
        )}

        {loading ? (
          <div style={{ textAlign: "center", padding: 48, color: "#888" }}>
            <Loader2 size={24} className="animate-spin" /> Loading…
          </div>
        ) : (
          <>
            {/* Activation */}
            {!status?.enabled && (
              <Card title={byokFree ? "Unlock BYOK — Free (instructor account)" : `Unlock BYOK — $${byokPrice}`} icon={CircleDollarSign}>
                {byokFree ? (
                  <p style={{ margin: "0 0 4px", color: "#555", fontSize: 14 }}>
                    Your instructor account includes BYOK at no charge — no payment needed.
                  </p>
                ) : (
                  <p style={{ margin: "0 0 4px", color: "#555", fontSize: 14 }}>
                    Activation is a one-time ${byokPrice} entitlement. You keep it for the life of your profile.
                  </p>
                )}
                <p style={{ margin: "0 0 16px", color: "#888", fontSize: 13 }}>
                  {byokFree
                    ? "After activation, attach a free provider key below."
                    : "Online payments are coming soon — the $3 unlock can't be purchased yet. Instructors activate free. After activation, attach a free provider key below."}
                </p>
                <button
                  onClick={activate}
                  disabled={isBusy("activate") || !byokFree}
                  title={byokFree ? undefined : "Online payments are coming soon"}
                  style={{
                    background: COPPER, color: "#fff", border: "none", borderRadius: 10, padding: "12px 22px",
                    fontWeight: 800, fontSize: 14, cursor: !byokFree ? "not-allowed" : isBusy("activate") ? "wait" : "pointer",
                    opacity: !byokFree ? 0.55 : 1,
                    display: "inline-flex", alignItems: "center", gap: 8,
                  }}
                >
                  {isBusy("activate") ? <Loader2 size={16} className="animate-spin" /> : <Plug size={16} />}
                  {byokFree ? "Activate BYOK — Free" : "Coming Soon — online checkout"}
                </button>
              </Card>
            )}

            {/* Provider cards */}
            {(status?.providers || []).map((p) => (
              <Card
                key={p.key}
                title={p.label}
                icon={p.configured ? CheckCircle2 : ShieldCheck}
                right={p.configured ? (
                  <span style={{ fontSize: 12, color: "#1b7a3d", fontWeight: 800 }}>
                    ● {p.masked || "configured"}
                  </span>
                ) : (
                  <a href={p.signup_url} target="_blank" rel="noreferrer"
                     style={{ fontSize: 12, color: COPPER, fontWeight: 700, display: "inline-flex", alignItems: "center", gap: 4 }}>
                    Get a free key <ExternalLink size={12} />
                  </a>
                )}
              >
                <p style={{ margin: "0 0 4px", color: "#555", fontSize: 13 }}>
                  {p.free_tier} · Model: <code style={{ background: BONE, padding: "1px 6px", borderRadius: 4 }}>{p.model}</code>
                </p>

                {!status?.enabled ? (
                  <p style={{ margin: 0, color: "#b3261e", fontSize: 13, display: "flex", gap: 6, alignItems: "center" }}>
                    <AlertTriangle size={14} /> Activate BYOK first, then save your key.
                  </p>
                ) : (
                  <div style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
                    <input
                      type="password"
                      placeholder={p.configured ? `Replace ${p.masked || ""}…` : `Paste your ${p.label} API key`}
                      value={keyInputs[p.key] || ""}
                      onChange={(e) => setKeyInputs((s) => ({ ...s, [p.key]: e.target.value }))}
                      style={{ ...inputStyle, flex: "1 1 320px", fontFamily: "ui-monospace, monospace" }}
                    />
                    <button
                      onClick={() => saveAndTest(p.key)}
                      disabled={isBusy(p.key)}
                      style={{
                        background: INK, color: "#fff", border: "none", borderRadius: 8, padding: "10px 16px",
                        fontWeight: 800, fontSize: 13, cursor: isBusy(p.key) ? "wait" : "pointer",
                        display: "inline-flex", alignItems: "center", gap: 6,
                      }}
                    >
                      {isBusy(p.key) ? <Loader2 size={14} className="animate-spin" /> : <CheckCircle2 size={14} />}
                      Save &amp; Test
                    </button>
                    {p.configured && (
                      <button
                        onClick={() => removeKey(p.key)}
                        disabled={isBusy(p.key)}
                        style={{
                          background: "#fdeaea", color: "#b3261e", border: "none", borderRadius: 8, padding: "10px 14px",
                          fontWeight: 800, fontSize: 13, cursor: isBusy(p.key) ? "wait" : "pointer",
                          display: "inline-flex", alignItems: "center", gap: 6,
                        }}
                      >
                        <Trash2 size={14} /> Remove
                      </button>
                    )}
                  </div>
                )}
              </Card>
            ))}

            {/* Admin aggregate */}
            {adminStats && (
              <Card title="BYOK adoption (admin)" icon={RefreshCw}>
                <div style={{ display: "flex", gap: 24, flexWrap: "wrap", color: "#555", fontSize: 14 }}>
                  <span><strong style={{ color: INK }}>{adminStats.activated_users}</strong> activated profiles</span>
                  <span><strong style={{ color: INK }}>{adminStats.configured_keys}</strong> active keys</span>
                  <span>Price point: <strong style={{ color: INK }}>${adminStats.price_usd}</strong></span>
                </div>
              </Card>
            )}
          </>
        )}
      </div>
    </AppShell>
  );
}
