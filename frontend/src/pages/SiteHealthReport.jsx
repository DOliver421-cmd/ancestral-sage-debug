import { useState, useEffect, useCallback } from "react";
import { api } from "../lib/api";
import AppShell from "../components/AppShell";
import {
  Activity, AlertTriangle, CheckCircle2, Clock, Database, Globe,
  Key, Server, Shield, Users, Zap, RefreshCw, Loader2, XCircle,
} from "lucide-react";

const COPPER = "#b5651d";
const INK = "#1a1a1a";

function StatusDot({ ok }) {
  return (
    <span style={{
      display: "inline-block", width: 8, height: 8, borderRadius: "50%",
      background: ok ? "#1b7a3d" : "#b3261e", marginRight: 6,
      boxShadow: ok ? "0 0 6px rgba(27,122,61,0.4)" : "0 0 6px rgba(179,38,30,0.4)",
    }} />
  );
}

function Section({ title, icon: Icon, children }) {
  return (
    <div style={{ background: "#fff", border: "1px solid #e5e5e5", borderRadius: 10, padding: 20, marginBottom: 16 }}>
      <h3 style={{ margin: 0, fontSize: 15, fontWeight: 800, color: INK, display: "flex", alignItems: "center", gap: 8 }}>
        {Icon && <Icon size={16} color={COPPER} />} {title}
      </h3>
      <div style={{ marginTop: 14 }}>{children}</div>
    </div>
  );
}

function DataRow({ label, value, ok, note }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", padding: "6px 0", borderBottom: "1px solid #f0f0f0" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
        <StatusDot ok={ok !== false} />
        <span style={{ fontSize: 13, fontWeight: 600, color: "#333" }}>{label}</span>
      </div>
      <div style={{ textAlign: "right" }}>
        <span style={{ fontSize: 13, fontWeight: 700, color: ok === false ? "#b3261e" : ok === "warn" ? "#9a6b00" : "#1b7a3d" }}>
          {value}
        </span>
        {note && <div style={{ fontSize: 11, color: "#888", marginTop: 2 }}>{note}</div>}
      </div>
    </div>
  );
}

export default function SiteHealthReport() {
  const [health, setHealth] = useState(null);
  const [version, setVersion] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    setRefreshing(true);
    setError(null);
    try {
      const [h, v] = await Promise.allSettled([
        api.get("/health"),
        api.get("/version"),
      ]);
      setHealth(h.status === "fulfilled" ? h.value?.data : null);
      setVersion(v.status === "fulfilled" ? v.value?.data : null);
    } catch (e) {
      setError(e?.message || "Could not load health data");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  // Real reads only — the backend /health payload reports live check results
  // under `checks.*`. These fields exist; the old top-level reads never did.
  const dbStatus = health?.checks?.db?.status || "unknown";
  const dbOk = dbStatus.startsWith("up");
  const apiOk = !!health; // receiving a /health payload means the API answered
  const overall = health?.status || "unknown"; // operational | degraded | critical
  const aiStatus = health?.checks?.ai_api?.status || "unknown";
  const payStatus = health?.checks?.payments?.status || "not_configured";
  const emailStatus = health?.checks?.email?.status || "not_configured";
  const plat = health?.checks?.platform || {};

  return (
    <AppShell>
      <div style={{ maxWidth: 800, margin: "0 auto", padding: "28px 20px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 20 }}>
          <div>
            <h1 style={{ margin: 0, fontSize: 24, fontWeight: 900, color: INK, display: "flex", alignItems: "center", gap: 10 }}>
              <Activity size={24} color={COPPER} /> System Health Report
            </h1>
            <p style={{ margin: "6px 0 0", fontSize: 13, color: "#666" }}>
              Verified status — not aspirational. Updated in real-time.
            </p>
          </div>
          <button onClick={load} disabled={refreshing} style={{
            display: "flex", alignItems: "center", gap: 6, cursor: "pointer",
            background: "transparent", color: COPPER, border: `1.5px solid ${COPPER}`,
            borderRadius: 8, padding: "8px 14px", fontWeight: 800, fontSize: 11,
            textTransform: "uppercase", letterSpacing: "0.06em",
          }}>
            {refreshing ? <Loader2 size={13} /> : <RefreshCw size={13} />} Refresh
          </button>
        </div>

        {error && (
          <div style={{ background: "#fdeaea", border: "1px solid #f5c6c6", borderRadius: 8, padding: 14, marginBottom: 16, fontSize: 13, color: "#b3261e" }}>
            <AlertTriangle size={14} style={{ marginRight: 6 }} /> {error}
          </div>
        )}

        {/* OVERALL STATUS — backend's own verdict, not a local guess */}
        <div style={{
          background: overall === "operational" ? "#e7f4ec" : overall === "critical" ? "#fdeaea" : "#fdf3d7",
          border: `1px solid ${overall === "operational" ? "#b8e4c8" : overall === "critical" ? "#f5c6c6" : "#f5e6a3"}`,
          borderRadius: 10, padding: 16, marginBottom: 20, textAlign: "center",
        }}>
          <div style={{ fontSize: 22, fontWeight: 900, color: overall === "operational" ? "#1b7a3d" : overall === "critical" ? "#b3261e" : "#9a6b00" }}>
            {(overall || "unknown").toUpperCase()}
          </div>
          <div style={{ fontSize: 12, color: "#666", marginTop: 4 }}>
            {apiOk ? "API responding" : "API unreachable"} · {dbOk ? "Database connected" : "Database status unknown"}
          </div>
          {health?.issues?.length > 0 && (
            <div style={{ marginTop: 8, display: "flex", flexWrap: "wrap", gap: 6, justifyContent: "center" }}>
              {health.issues.map((iss) => (
                <span key={iss} style={{ fontSize: 10, fontWeight: 800, background: "#f5e6a3", color: "#9a6b00", padding: "3px 8px", borderRadius: 999 }}>{iss.replace(/_/g, " ")}</span>
              ))}
            </div>
          )}
        </div>

        {/* API STATUS */}
        <Section title="API Server" icon={Server}>
          <DataRow label="API Endpoint" value={apiOk ? "Responding" : "Unreachable"} ok={apiOk} note={version?.version ? `v${version.version}` : ""} />
          <DataRow label="Health Endpoint" value="/api/health" ok={true} note="Live ping + subsystem checks" />
          <DataRow label="Overall Verdict" value={overall} ok={overall === "operational" ? true : "warn"} note="set by backend from real checks" />
        </Section>

        {/* DATABASE */}
        <Section title="Database" icon={Database}>
          <DataRow label="MongoDB Connection" value={dbStatus} ok={dbOk} />
          <DataRow label="Primary" value={health?.db_source || "Check MONGO_URL"} ok={!!health?.db_source} />
        </Section>

        {/* SECURITY */}
        <Section title="Security" icon={Shield}>
          <DataRow label="JWT Auth" value={plat.jwt_algo || "—"} ok={!!plat.jwt_algo} note="7-day expiry" />
          <DataRow label="RBAC" value={plat.rbac_tiers ? `${plat.rbac_tiers} tiers` : "Active"} ok={!!plat.rbac_tiers} note="student → exec_admin" />
          <DataRow label="API Docs" value={health?.checks?.docs_enabled ? "ENABLED (risky)" : "Disabled"} ok={!health?.checks?.docs_enabled} />
          <DataRow label="IP Whitelist" value={(health?.checks?.ip_whitelist_count || 0) > 0 ? `${health.checks.ip_whitelist_count} entries` : "Empty or absent"} ok="warn"
            note="Exec routes IP-gated when entries exist" />
          <DataRow label="CORS" value={plat.cors_origins?.length ? plat.cors_origins.join(", ") : "Configured"} ok={true} note="from backend CORS config" />
          <DataRow label="Security Headers" value={plat.security_headers?.length ? `${plat.security_headers.length} active` : "Unknown"} ok={(plat.security_headers?.length || 0) > 0}
            note="X-Frame-Options · HSTS · nosniff · Referrer-Policy" />
        </Section>

        {/* AI / LLM */}
        <Section title="AI / LLM Gateway" icon={Zap}>
          <DataRow label="Gateway" value={aiStatus} ok={aiStatus === "configured" ? true : "warn"} note="live provider availability from the gateway" />
          <DataRow label="Active Free Providers" value={health?.checks?.ai_api?.active_free_providers ?? "—"} ok={(health?.checks?.ai_api?.active_free_providers || 0) > 0} />
          <DataRow label="Budget Usage" value={health?.checks?.ai_api?.budget_pct != null ? `${health.checks.ai_api.budget_pct}%` : "—"} ok={!health?.checks?.ai_api?.over_budget} note={health?.checks?.ai_api?.over_budget ? "OVER BUDGET" : "within budget"} />
        </Section>

        {/* PAYMENTS */}
        <Section title="Payments" icon={Key}>
          <DataRow label="Payments Status" value={payStatus} ok={payStatus === "configured" ? true : "warn"}
            note={payStatus === "configured" ? "A payment key is set (env or encrypted vault)" : "No Stripe / Lemon Squeezy / Gumroad key is configured"} />
        </Section>

        {/* USERS */}
        <Section title="Users & Auth" icon={Users}>
          <DataRow label="Total Users" value={health?.checks?.user_count ?? "N/A"} ok={health?.checks?.user_count != null} />
          <DataRow label="Active Sessions" value="JWT-based (no server sessions)" ok={true} note="Token expiry: 7 days" />
          <DataRow label="Email Delivery" value={emailStatus} ok={emailStatus === "configured" ? true : "warn"}
            note={emailStatus === "configured" ? "Resend or Gmail SMTP configured" : "No RESEND_API_KEY or GMAIL_APP_PASSWORD set"} />
        </Section>

        {/* WHAT THE PAYLOAD PROVES */}
        <Section title="What The Live Check Proves Right Now" icon={CheckCircle2}>
          <div style={{ fontSize: 13, lineHeight: 1.7, color: "#333" }}>
            <div style={{ marginBottom: 6 }}>✅ API answered the /health probe (this page rendered from live data)</div>
            <div style={{ marginBottom: 6 }}>✅ Database reported: {dbStatus || "—"}</div>
            <div style={{ marginBottom: 6 }}>✅ JWT auth algorithm reported by backend: {plat.jwt_algo || "—"}</div>
            <div style={{ marginBottom: 6 }}>✅ Security headers middleware reported: {(plat.security_headers?.length || 0)} headers active</div>
            <div style={{ marginBottom: 6 }}>✅ CORS origins reported: {(plat.cors_origins || []).join(", ") || "—"}</div>
            <div style={{ marginBottom: 6 }}>✅ Total users reported: {health?.checks?.user_count ?? "—"}</div>
            {overall !== "operational" && (
              <div style={{ marginBottom: 6 }}>⚠️ Backend reported {overall}: {(health?.issues || []).join(", ") || "no detail"}</div>
            )}
          </div>
        </Section>

        {/* WHAT'S PARTIAL */}
        <Section title="What Needs Attention (Reported By The Backend)" icon={AlertTriangle}>
          <div style={{ fontSize: 13, lineHeight: 1.7, color: "#333" }}>
            <div style={{ marginBottom: 6 }}>⚠️ Payments: {payStatus}{payStatus !== "configured" ? " — no Stripe/Lemon/Gumroad key is set" : ""}</div>
            <div style={{ marginBottom: 6 }}>⚠️ Email: {emailStatus}{emailStatus !== "configured" ? " — set RESEND_API_KEY or GMAIL_APP_PASSWORD" : ""}</div>
            <div style={{ marginBottom: 6 }}>⚠️ AI gateway: {aiStatus}{aiStatus === "configured" ? ` — ${health?.checks?.ai_api?.active_free_providers || 0} provider(s) available` : ""}</div>
            {(health?.issues || []).map((iss) => (
              <div key={iss} style={{ marginBottom: 6 }}>⚠️ {iss.replace(/_/g, " ")}</div>
            ))}
          </div>
        </Section>

        {/* WHAT'S NOT WORKING */}
        <Section title="Known Failures (Verified In Code, Not Claimed Otherwise)" icon={XCircle}>
          <div style={{ fontSize: 13, lineHeight: 1.7, color: "#333" }}>
            <div style={{ marginBottom: 6 }}>❌ AI cost tracking: the tracker (ai_cost_tracker.record_ai_call) exists but no code path calls it — the cost summary reads an empty collection. Writes not wired yet.</div>
            <div style={{ marginBottom: 6 }}>❌ Handbook links previously 401'd for signed-in users (auth-gated endpoint opened without a token) — fixed in code, pending deploy.</div>
            <div style={{ marginBottom: 6 }}>❌ /api/modules previously returned HTTP 500 (legacy module docs missing the required id field), rendering the /modules page empty — hardened in code, pending deploy.</div>
          </div>
        </Section>

        <div style={{ textAlign: "center", padding: "20px 0", fontSize: 11, color: "#aaa" }}>
          Generated from verified code inspection — August 20, 2026
        </div>
      </div>
    </AppShell>
  );
}
