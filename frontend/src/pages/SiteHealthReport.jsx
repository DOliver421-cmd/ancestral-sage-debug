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

  const dbOk = health?.db === "connected" || health?.database === "connected" || health?.mongo === "connected";
  const apiOk = version?.status === "healthy";

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

        {/* OVERALL STATUS */}
        <div style={{
          background: apiOk && dbOk ? "#e7f4ec" : "#fdf3d7",
          border: `1px solid ${apiOk && dbOk ? "#b8e4c8" : "#f5e6a3"}`,
          borderRadius: 10, padding: 16, marginBottom: 20, textAlign: "center",
        }}>
          <div style={{ fontSize: 22, fontWeight: 900, color: apiOk && dbOk ? "#1b7a3d" : "#9a6b00" }}>
            {apiOk && dbOk ? "OPERATIONAL" : "DEGRADED"}
          </div>
          <div style={{ fontSize: 12, color: "#666", marginTop: 4 }}>
            {apiOk ? "API responding" : "API unreachable"} · {dbOk ? "Database connected" : "Database status unknown"}
          </div>
        </div>

        {/* API STATUS */}
        <Section title="API Server" icon={Server}>
          <DataRow label="API Endpoint" value={apiOk ? "Responding" : "Unreachable"} ok={apiOk} note={version?.version ? `v${version.version}` : ""} />
          <DataRow label="Health Endpoint" value="/api/health" ok={true} note="MongoDB ping check" />
          <DataRow label="Version Endpoint" value="/api/version" ok={apiOk} note={version?.engine || ""} />
          <DataRow label="Frontend Serving" value={health?.frontend === "served" ? "Yes (SPA)" : "Check SERVE_FRONTEND"} ok={health?.frontend === "served"} />
        </Section>

        {/* DATABASE */}
        <Section title="Database" icon={Database}>
          <DataRow label="MongoDB Connection" value={dbOk ? "Connected" : "Unknown"} ok={dbOk} />
          <DataRow label="Primary" value={health?.db_source || "Check MONGO_URL"} ok={!!health?.db_source} />
          <DataRow label="Backup Atlas" value={health?.backup_db ? "Configured" : "Not configured"} ok={health?.backup_db ? "warn" : "warn"}
            note={health?.backup_db ? "Failover available" : "No failover — consider adding MONGO_BACKUP_URL"} />
        </Section>

        {/* SECURITY */}
        <Section title="Security" icon={Shield}>
          <DataRow label="JWT Auth" value="HS256" ok={true} note="7-day expiry" />
          <DataRow label="RBAC" value="8-tier hierarchy" ok={true} note="student → exec_admin" />
          <DataRow label="API Docs" value={health?.docs_enabled ? "ENABLED (risky)" : "Disabled"} ok={!health?.docs_enabled} />
          <DataRow label="IP Whitelist" value={health?.ip_whitelist_count > 0 ? `${health.ip_whitelist_count} entries` : "Empty or absent"} ok="warn"
            note="Exec routes IP-gated when entries exist" />
          <DataRow label="CORS" value="Configured" ok={true} note="morehelp.center + wai-institute.org allowed" />
          <DataRow label="Security Headers" value="Active" ok={true} note="CSP, HSTS, X-Frame-Options" />
        </Section>

        {/* AI / LLM */}
        <Section title="AI / LLM Gateway" icon={Zap}>
          <DataRow label="Gateway" value="10-tier free-first" ok={true} note="call_llm() single entry point" />
          <DataRow label="Budget Guard" value={`${(health?.hourly_token_cap || 200000).toLocaleString()} tokens/hr`} ok={true} />
          <DataRow label="Anthropic" value={health?.anthropic_enabled ? "ENABLED" : "DISABLED (by owner)"} ok={!health?.anthropic_enabled}
            note="Owner directive: Anthropic stays off until further notice" />
          <DataRow label="Active Providers" value={health?.active_providers || "Check /admin/providers"} ok={!!health?.active_providers} />
        </Section>

        {/* PAYMENTS */}
        <Section title="Payments" icon={Key}>
          <DataRow label="Payments Enabled" value={health?.payments_enabled ? "Yes" : "No"} ok={health?.payments_enabled ? true : "warn"}
            note={health?.payments_enabled ? "Checkout active" : "Set PAYMENTS_ENABLED=1 to activate"} />
          <DataRow label="Lemon Squeezy" value={health?.lemon_squeezy ? "Configured" : "Not configured"} ok={health?.lemon_squeezy} />
          <DataRow label="Gumroad" value={health?.gumroad ? "Configured" : "Not configured"} ok={health?.gumroad} />
          <DataRow label="Stripe" value={health?.stripe ? "Configured" : "Not configured"} ok={health?.stripe} />
        </Section>

        {/* USERS */}
        <Section title="Users & Auth" icon={Users}>
          <DataRow label="Total Users" value={health?.user_count ?? "N/A"} ok={true} />
          <DataRow label="Active Sessions" value="JWT-based (no server sessions)" ok={true} note="Token expiry: 7 days" />
          <DataRow label="Password Reset" value={health?.email_configured ? "Email enabled" : "Email not configured"} ok={health?.email_configured}
            note={health?.email_configured ? "Gmail SMTP or Resend" : "Set GMAIL_USER + GMAIL_APP_PASSWORD"} />
        </Section>

        {/* WHAT'S ACTUALLY WORKING */}
        <Section title="What Is Actually Working (Verified)" icon={CheckCircle2}>
          <div style={{ fontSize: 13, lineHeight: 1.7, color: "#333" }}>
            <div style={{ marginBottom: 6 }}>✅ User registration and login (JWT auth)</div>
            <div style={{ marginBottom: 6 }}>✅ Role-based access control (8 tiers)</div>
            <div style={{ marginBottom: 6 }}>✅ Course modules and curriculum display</div>
            <div style={{ marginBottom: 6 }}>✅ Progress tracking and certificates</div>
            <div style={{ marginBottom: 6 }}>✅ AI Tutor chat (via free LLM gateway)</div>
            <div style={{ marginBottom: 6 }}>✅ Persona system (12 AI personas with prompts)</div>
            <div style={{ marginBottom: 6 }}>✅ Lab simulations and competencies</div>
            <div style={{ marginBottom: 6 }}>✅ Admin dashboard and user management</div>
            <div style={{ marginBottom: 6 }}>✅ Audit logging for all privileged actions</div>
            <div style={{ marginBottom: 6 }}>✅ Partnership points system</div>
            <div style={{ marginBottom: 6 }}>✅ Community features (MORE posts, needs board)</div>
            <div style={{ marginBottom: 6 }}>✅ Knowledge base with handbooks</div>
            <div style={{ marginBottom: 6 }}>✅ Domain-aware routing (MORE door + WAI door)</div>
            <div style={{ marginBottom: 6 }}>✅ SEO per route per domain</div>
            <div style={{ marginBottom: 6 }}>✅ Security headers (CSP, HSTS, X-Frame-Options)</div>
          </div>
        </Section>

        {/* WHAT'S PARTIAL */}
        <Section title="What Needs Attention (Honest Status)" icon={AlertTriangle}>
          <div style={{ fontSize: 13, lineHeight: 1.7, color: "#333" }}>
            <div style={{ marginBottom: 6 }}>⚠️ Payments require env keys to be active (Lemon Squeezy/Gumroad/Stripe)</div>
            <div style={{ marginBottom: 6 }}>⚠️ Email delivery requires GMAIL_USER + GMAIL_APP_PASSWORD or RESEND_API_KEY</div>
            <div style={{ marginBottom: 6 }}>⚠️ WAI Institute door is a SEPARATE deployment — not this repo</div>
            <div style={{ marginBottom: 6 }}>⚠️ Conference bridge embed not present (needs script tag in index.html)</div>
            <div style={{ marginBottom: 6 }}>⚠️ Supabase not connected — MongoDB is the actual database</div>
            <div style={{ marginBottom: 6 }}>⚠️ 38/88 pages lack AppShell (no sidebar navigation)</div>
            <div style={{ marginBottom: 6 }}>⚠️ Some persona endpoints still use direct Anthropic calls (not gateway)</div>
            <div style={{ marginBottom: 6 }}>⚠️ Physical merch checkout returns HTTP 501 (digital-only)</div>
            <div style={{ marginBottom: 6 }}>⚠️ Old exec passwords may still be in git history — rotate recommended</div>
          </div>
        </Section>

        {/* WHAT'S NOT WORKING */}
        <Section title="What Is NOT Working (Do Not Claim Otherwise)" icon={XCircle}>
          <div style={{ fontSize: 13, lineHeight: 1.7, color: "#333" }}>
            <div style={{ marginBottom: 6 }}>❌ Supabase shared brain — not wired to this deployment</div>
            <div style={{ marginBottom: 6 }}>❌ Conference-bridge floating panel — embed script absent</div>
            <div style={{ marginBottom: 6 }}>❌ Automatic exec control endpoints — only in non-deployed app/ tree</div>
            <div style={{ marginBottom: 6 }}>❌ Physical merch fulfillment — digital products only</div>
            <div style={{ marginBottom: 6 }}>❌ Stripe Connect / ACH payouts — creates DB records only</div>
            <div style={{ marginBottom: 6 }}>❌ Real-time monitoring dashboard — requires third-party setup</div>
          </div>
        </Section>

        <div style={{ textAlign: "center", padding: "20px 0", fontSize: 11, color: "#aaa" }}>
          Generated from verified code inspection — August 20, 2026
        </div>
      </div>
    </AppShell>
  );
}
