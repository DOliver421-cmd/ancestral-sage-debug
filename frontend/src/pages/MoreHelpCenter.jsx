/**
 * MORE Help Center — unified entry point
 *
 * Three render modes, determined automatically:
 *   greeter — unauthenticated or student/instructor (public-facing welcome)
 *   exec    — admin / executive_admin (all greeter content + embedded Supervisor controls)
 *   decoy   — API unreachable (friendly offline page, static, no API calls)
 *
 * All section visibility is group-toggled by role, never per-user hard-coding.
 */

import { useEffect, useState, useCallback } from "react";
import { Link } from "react-router-dom";
import {
  Heart, BookOpen, MessageSquare, ArrowRight, Phone, Shield, Users, Globe,
  Activity, BadgeCheck, ShieldCheck, Sparkles, MapPin,
  Send, Eye, EyeOff, Crown,
} from "lucide-react";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";

// ── Brand tokens ───────────────────────────────────────────────────────────────
const GOLD      = "#e8b83e";
const TEAL      = "#0d7377";
const TEAL_DARK = "#095b5e";
const WARM      = "#f9f5f0";
const COPPER    = "#8d5a33";
const CREAM     = "#fff8f0";
const SUPPORT_EMAIL = "morehelpcenter@gmail.com";

// ── Role helpers ───────────────────────────────────────────────────────────────
const ROLE_RANK = { student: 1, instructor: 2, admin: 3, executive_admin: 4 };
function hasRank(user, min) { return (ROLE_RANK[user?.role] ?? 0) >= min; }
const isExec    = (u) => hasRank(u, 3);   // admin or executive_admin
const isSupExec = (u) => hasRank(u, 4);   // executive_admin only

// ── Static content (shared across modes) ──────────────────────────────────────
const FEATURES = [
  { icon: BookOpen,     title: "Free Learning",       desc: "Hands-on training, free modules, and certification pathways — no paywall at the door." },
  { icon: MessageSquare,title: "Community Support",   desc: "Ask questions, share knowledge, and get real answers from real people in your community." },
  { icon: Shield,       title: "Legal & Compliance",  desc: "Governance guidance, risk controls, and community-safe procedures built into every process." },
  { icon: Users,        title: "Community Market",    desc: "A virtual African market plaza where visitors discover services, training, and trusted allies." },
  { icon: Sparkles,     title: "Creative Production", desc: "Media, course-building, branding, and storytelling tools keep the hub vibrant and alive." },
  { icon: Activity,     title: "Autonomous Finance",  desc: "Self-managing finance operations run budgets, compliance, and expense flow for the center." },
];

const WAYPOINTS = [
  { icon: MapPin,     title: "Entrance Atrium",        desc: "Step in like a mall visitor and find the main path to finance, legal, and community services." },
  { icon: Users,      title: "Service Lanes",           desc: "Move through themed lanes for support, training, production, and marketplace discovery." },
  { icon: BadgeCheck, title: "Human Oversight Desk",   desc: "Every AI-driven direction is backed by human review, audit, and executive supervision." },
  { icon: Globe,      title: "WAI Infrastructure",     desc: "This hub is connected to the full WAI system, from course catalogs to executive controls." },
];

const ROLE_LANES = [
  { icon: Globe,      title: "Visitor lane",   desc: "Public guests are guided to support, community learning, and marketplace discovery." },
  { icon: Activity,   title: "Operator lane",  desc: "Platform operators manage service routing, compliance checks, and live response workflows." },
  { icon: BadgeCheck, title: "Supervisor lane",desc: "Supervisors review AI suggestions, coordinate escalations, and maintain executive visibility." },
  { icon: ShieldCheck,title: "Auditor lane",   desc: "Auditors verify governance, privacy, and finance decisions with transparent records." },
];

const NAV_LINKS = [
  { label: "Free Modules",  to: "/modules" },
  { label: "Community",     to: "/community" },
  { label: "Courses",       to: "/courses" },
  { label: "Help Center",   to: "/help-center" },
  { label: "Store",         to: "/store" },
  { label: "Plans",         to: "/plans" },
];

// ── Decoy Mode (API offline) ───────────────────────────────────────────────────
function DecoyMode() {
  return (
    <div style={{ minHeight: "100vh", background: TEAL_DARK, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: 32, textAlign: "center" }}>
      <div style={{ width: 64, height: 64, borderRadius: "50%", background: GOLD, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 28, fontWeight: 900, color: "#1a1a2e", marginBottom: 24 }}>M</div>
      <h1 style={{ color: "white", fontSize: 36, fontWeight: 900, marginBottom: 12 }}>MORE Help Center</h1>
      <p style={{ color: "#a0d4d6", fontSize: 18, maxWidth: 480, lineHeight: 1.6, marginBottom: 8 }}>
        We're temporarily offline for maintenance. Our team is working on it.
      </p>
      <p style={{ color: "#a0d4d6", fontSize: 14, marginBottom: 32 }}>
        All your data is safe. We'll be back shortly.
      </p>
      <a href={`mailto:${SUPPORT_EMAIL}`} style={{ background: GOLD, color: "#1a1a2e", padding: "12px 28px", borderRadius: 8, fontWeight: 700, fontSize: 14, textDecoration: "none", display: "inline-block" }}>
        Email Support
      </a>
      <p style={{ color: "rgba(255,255,255,0.3)", marginTop: 40, fontSize: 12 }}>WAI-Institute · MORE Help Center</p>
    </div>
  );
}

// ── Exec Supervisor Control Panel ──────────────────────────────────────────────
function ExecPanel({ apiOnline, visibility, setVisibility }) {
  const [tab, setTab]               = useState("health");
  const [health, setHealth]         = useState(null);
  const [users, setUsers]           = useState([]);
  const [incidents, setIncidents]   = useState([]);
  const [auditLog, setAuditLog]     = useState([]);
  const [broadcastMsg, setBroadcast]= useState("");
  const [sending, setSending]       = useState(false);
  const [gwStatus, setGwStatus]     = useState(null);
  const [apiKeys, setApiKeys]       = useState({});
  const [showKeys, setShowKeys]     = useState({});
  const [capLevel, setCapLevel]     = useState("");
  const [loading, setLoading]       = useState(false);
  const [notice, setNotice]         = useState("");

  const notify = (msg, isErr) => {
    setNotice(msg);
    setTimeout(() => setNotice(""), 3500);
  };

  const loadHealth = useCallback(async () => {
    setLoading(true);
    try { const r = await api.get("/health"); setHealth(r.data); } catch { setHealth(null); }
    finally { setLoading(false); }
  }, []);

  const loadGateway = useCallback(async () => {
    // GET /admin/gateway/status — returns gateway_status() from llm_gateway
    try { const r = await api.get("/admin/gateway/status"); setGwStatus(r.data); } catch {}
  }, []);

  const loadUsers = useCallback(async () => {
    // GET /admin/users — returns array directly
    try { const r = await api.get("/admin/users"); setUsers(Array.isArray(r.data) ? r.data : []); } catch {}
  }, []);

  const loadIncidents = useCallback(async () => {
    // GET /incidents?status=open — returns array directly; requires instructor+
    try {
      const r = await api.get("/incidents?status=open");
      setIncidents(Array.isArray(r.data) ? r.data.slice(0, 20) : []);
    } catch {}
  }, []);

  const loadAudit = useCallback(async () => {
    // GET /admin/audit?limit=20 — returns array directly
    try { const r = await api.get("/admin/audit?limit=20"); setAuditLog(Array.isArray(r.data) ? r.data : []); } catch {}
  }, []);

  const loadSageCap = useCallback(async () => {
    // GET /admin/sage/cap — returns { global_level, available_levels, overrides }
    try { const r = await api.get("/admin/sage/cap"); setCapLevel(r.data?.global_level || ""); } catch {}
  }, []);

  useEffect(() => {
    loadHealth();
    loadGateway();
  }, [loadHealth, loadGateway]);

  useEffect(() => {
    if (tab === "users")     loadUsers();
    if (tab === "incidents") loadIncidents();
    if (tab === "audit")     loadAudit();
    if (tab === "safety")    loadSageCap();
  }, [tab, loadUsers, loadIncidents, loadAudit, loadSageCap]);

  const sendBroadcast = async () => {
    if (!broadcastMsg.trim()) return;
    setSending(true);
    try {
      await api.post("/admin/broadcast", { message: broadcastMsg.trim() });
      notify("Broadcast sent");
      setBroadcast("");
    } catch { notify("Broadcast failed", true); }
    finally { setSending(false); }
  };

  const setSafetyCap = async (level) => {
    try {
      // PUT /admin/sage/cap/global — requires executive_admin
      await api.put("/admin/sage/cap/global", { level: level || null });
      setCapLevel(level);
      notify(`Safety cap set: ${level || "cleared"}`);
    } catch { notify("Failed to set cap", true); }
  };

  const pushApiKey = async (envKey, value) => {
    if (!value) return;
    try {
      await api.post("/admin/gateway/keys", { [envKey]: value });
      notify(`${envKey} pushed to gateway`);
    } catch { notify(`Failed to push ${envKey}`, true); }
  };

  const TABS = [
    { key: "health",     label: "Health" },
    { key: "gateway",    label: "Gateway" },
    { key: "users",      label: "Users" },
    { key: "broadcast",  label: "Broadcast" },
    { key: "incidents",  label: "Incidents" },
    { key: "safety",     label: "Safety Cap" },
    { key: "apikeys",    label: "API Keys" },
    { key: "audit",      label: "Audit Log" },
    { key: "visibility", label: "Visibility" },
  ];

  const INK = "#2e1065";
  const SIG = "#FFD100";

  return (
    <div style={{ background: INK, borderRadius: 16, overflow: "hidden", boxShadow: "0 8px 40px rgba(0,0,0,0.4)", marginBottom: 32 }}>
      {/* Panel header */}
      <div style={{ padding: "16px 24px", borderBottom: "1px solid rgba(255,255,255,0.1)", display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: 12 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <div style={{ width: 36, height: 36, borderRadius: "50%", background: SIG, display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 900, fontSize: 14, color: INK }}>S</div>
          <div>
            <div style={{ color: "white", fontWeight: 800, fontSize: 15 }}>Supervisor Panel</div>
            <div style={{ color: "rgba(255,255,255,0.45)", fontSize: 11 }}>Executive Control — MORE Help Center</div>
          </div>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <div style={{ width: 8, height: 8, borderRadius: "50%", background: apiOnline ? "#22c55e" : "#dc2626" }} />
          <span style={{ fontSize: 12, color: "rgba(255,255,255,0.6)" }}>{apiOnline ? "API online" : "API offline"}</span>
          <Link to="/admin/system" style={{ background: SIG, color: INK, padding: "5px 12px", borderRadius: 6, fontSize: 11, fontWeight: 700, textDecoration: "none", marginLeft: 8 }}>
            Full Dashboard →
          </Link>
        </div>
      </div>

      {/* Tab bar */}
      <div style={{ display: "flex", overflowX: "auto", borderBottom: "1px solid rgba(255,255,255,0.08)", padding: "0 16px" }}>
        {TABS.map(t => (
          <button key={t.key} onClick={() => setTab(t.key)}
            style={{ padding: "10px 14px", border: "none", background: "none", color: tab === t.key ? SIG : "rgba(255,255,255,0.55)", fontWeight: tab === t.key ? 700 : 500, fontSize: 12, cursor: "pointer", borderBottom: tab === t.key ? `2px solid ${SIG}` : "2px solid transparent", whiteSpace: "nowrap" }}>
            {t.label}
          </button>
        ))}
      </div>

      {/* Notice */}
      {notice && (
        <div style={{ margin: "12px 20px 0", background: "rgba(255,255,255,0.1)", borderRadius: 8, padding: "8px 14px", fontSize: 12, color: SIG }}>{notice}</div>
      )}

      {/* Panel body */}
      <div style={{ padding: 20, minHeight: 220 }}>

        {/* Health */}
        {tab === "health" && (
          <div>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
              <span style={{ color: "white", fontWeight: 700, fontSize: 14 }}>Platform Health</span>
              <button onClick={loadHealth} disabled={loading} style={{ background: "rgba(255,255,255,0.1)", border: "none", color: "white", padding: "5px 12px", borderRadius: 6, fontSize: 11, cursor: "pointer" }}>
                {loading ? "…" : "Refresh"}
              </button>
            </div>
            {health ? (
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(140px,1fr))", gap: 10 }}>
                {Object.entries(health).filter(([k]) => typeof health[k] !== "object").map(([k, v]) => (
                  <div key={k} style={{ background: "rgba(255,255,255,0.07)", borderRadius: 8, padding: "10px 14px" }}>
                    <div style={{ color: "rgba(255,255,255,0.45)", fontSize: 10, textTransform: "uppercase", letterSpacing: 1 }}>{k}</div>
                    <div style={{ color: v === "up" || v === true ? "#22c55e" : v === "down" || v === false ? "#dc2626" : SIG, fontWeight: 700, fontSize: 13, marginTop: 4 }}>{String(v)}</div>
                  </div>
                ))}
              </div>
            ) : (
              <p style={{ color: "rgba(255,255,255,0.4)", fontSize: 13 }}>Click Refresh to run health check.</p>
            )}
          </div>
        )}

        {/* Gateway */}
        {tab === "gateway" && (
          <div>
            <div style={{ color: "white", fontWeight: 700, fontSize: 14, marginBottom: 14 }}>LLM Gateway Status</div>
            {gwStatus ? (
              <div>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(160px,1fr))", gap: 10, marginBottom: 14 }}>
                  {Object.entries(gwStatus.providers || {}).map(([name, p]) => (
                    <div key={name} style={{ background: "rgba(255,255,255,0.07)", borderRadius: 8, padding: "10px 14px" }}>
                      <div style={{ color: "white", fontWeight: 700, fontSize: 13, textTransform: "capitalize" }}>{name}</div>
                      <div style={{ color: p.available ? "#22c55e" : "#dc2626", fontSize: 11, marginTop: 3 }}>
                        {p.available ? "✓ Active" : "✗ No key"}
                      </div>
                      <div style={{ color: SIG, fontSize: 10, marginTop: 2 }}>Tier {p.tier} · {p.cost}</div>
                    </div>
                  ))}
                </div>
                {gwStatus.budget && (
                  <div style={{ background: "rgba(255,255,255,0.06)", borderRadius: 8, padding: "10px 14px", fontSize: 12, color: "rgba(255,255,255,0.6)" }}>
                    Hourly budget: {gwStatus.budget.tokens_used?.toLocaleString()} / {gwStatus.budget.hourly_cap?.toLocaleString()} tokens ({gwStatus.budget.budget_pct}%)
                    {gwStatus.budget.over_budget && <span style={{ color: "#dc2626", marginLeft: 8, fontWeight: 700 }}>OVER BUDGET</span>}
                  </div>
                )}
              </div>
            ) : (
              <p style={{ color: "rgba(255,255,255,0.4)", fontSize: 13 }}>Loading gateway status…</p>
            )}
          </div>
        )}

        {/* Users */}
        {tab === "users" && (
          <div>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 14 }}>
              <span style={{ color: "white", fontWeight: 700, fontSize: 14 }}>Recent Users</span>
              <div style={{ display: "flex", gap: 8 }}>
                <button onClick={loadUsers} style={{ background: "rgba(255,255,255,0.1)", border: "none", color: "white", padding: "5px 10px", borderRadius: 6, fontSize: 11, cursor: "pointer" }}>Refresh</button>
                <Link to="/admin/system" style={{ background: SIG, color: INK, padding: "5px 10px", borderRadius: 6, fontSize: 11, fontWeight: 700, textDecoration: "none" }}>Full User DB</Link>
              </div>
            </div>
            <div style={{ overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
                <thead>
                  <tr>
                    {["Name", "Email", "Role", "Joined"].map(h => (
                      <th key={h} style={{ textAlign: "left", padding: "6px 10px", color: "rgba(255,255,255,0.4)", fontWeight: 700, borderBottom: "1px solid rgba(255,255,255,0.08)", textTransform: "uppercase", fontSize: 10 }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {users.slice(0, 15).map(u => (
                    <tr key={u.id || u.email} style={{ borderBottom: "1px solid rgba(255,255,255,0.06)" }}>
                      <td style={{ padding: "7px 10px", color: "white", fontWeight: 600 }}>{u.full_name || "—"}</td>
                      <td style={{ padding: "7px 10px", color: "rgba(255,255,255,0.6)" }}>{u.email}</td>
                      <td style={{ padding: "7px 10px" }}>
                        <span style={{ background: u.role === "executive_admin" ? SIG : u.role === "admin" ? "#7c3aed" : "rgba(255,255,255,0.15)", color: u.role === "executive_admin" ? INK : "white", padding: "2px 8px", borderRadius: 20, fontSize: 10, fontWeight: 700 }}>
                          {u.role}
                        </span>
                      </td>
                      <td style={{ padding: "7px 10px", color: "rgba(255,255,255,0.45)", fontSize: 11 }}>
                        {u.created_at ? new Date(u.created_at).toLocaleDateString() : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {users.length === 0 && <p style={{ color: "rgba(255,255,255,0.4)", fontSize: 13, marginTop: 12 }}>No users loaded.</p>}
            </div>
          </div>
        )}

        {/* Broadcast */}
        {tab === "broadcast" && (
          <div>
            <div style={{ color: "white", fontWeight: 700, fontSize: 14, marginBottom: 14 }}>Send Platform Broadcast</div>
            <textarea
              value={broadcastMsg}
              onChange={e => setBroadcast(e.target.value)}
              placeholder="Type a message to broadcast to all active users…"
              rows={4}
              style={{ width: "100%", background: "rgba(255,255,255,0.08)", border: "1px solid rgba(255,255,255,0.15)", borderRadius: 8, padding: "10px 14px", color: "white", fontSize: 13, resize: "vertical", outline: "none", boxSizing: "border-box" }}
            />
            <button onClick={sendBroadcast} disabled={sending || !broadcastMsg.trim()}
              style={{ marginTop: 10, background: SIG, border: "none", color: INK, padding: "9px 20px", borderRadius: 7, fontSize: 13, fontWeight: 700, cursor: "pointer", display: "flex", alignItems: "center", gap: 6 }}>
              <Send style={{ width: 14, height: 14 }} /> {sending ? "Sending…" : "Send Broadcast"}
            </button>
          </div>
        )}

        {/* Incidents */}
        {tab === "incidents" && (
          <div>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 14 }}>
              <span style={{ color: "white", fontWeight: 700, fontSize: 14 }}>Open Incidents</span>
              <button onClick={loadIncidents} style={{ background: "rgba(255,255,255,0.1)", border: "none", color: "white", padding: "5px 10px", borderRadius: 6, fontSize: 11, cursor: "pointer" }}>Refresh</button>
            </div>
            {incidents.length === 0
              ? <p style={{ color: "rgba(255,255,255,0.4)", fontSize: 13 }}>No open incidents.</p>
              : incidents.map(inc => (
                <div key={inc.id} style={{ background: "rgba(220,38,38,0.12)", border: "1px solid rgba(220,38,38,0.25)", borderRadius: 8, padding: "10px 14px", marginBottom: 8 }}>
                  <div style={{ color: "white", fontWeight: 700, fontSize: 13 }}>{inc.title || inc.description}</div>
                  <div style={{ color: "rgba(255,255,255,0.5)", fontSize: 11, marginTop: 3 }}>{inc.created_at ? new Date(inc.created_at).toLocaleString() : ""} · {inc.severity || ""}</div>
                </div>
              ))
            }
          </div>
        )}

        {/* Safety Cap */}
        {tab === "safety" && (
          <div>
            <div style={{ color: "white", fontWeight: 700, fontSize: 14, marginBottom: 6 }}>Global Sage Safety Cap</div>
            <div style={{ color: "rgba(255,255,255,0.5)", fontSize: 12, marginBottom: 16 }}>
              Current: <strong style={{ color: SIG }}>{capLevel || "No restriction"}</strong>
            </div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
              {["conservative", "standard", "exploratory"].map(lvl => (
                <button key={lvl} onClick={() => setSafetyCap(lvl)}
                  style={{ background: capLevel === lvl ? SIG : "rgba(255,255,255,0.1)", border: "none", color: capLevel === lvl ? INK : "white", padding: "8px 16px", borderRadius: 7, fontSize: 12, fontWeight: 700, cursor: "pointer", textTransform: "capitalize" }}>
                  {lvl}
                </button>
              ))}
              <button onClick={() => setSafetyCap("")}
                style={{ background: "rgba(220,38,38,0.2)", border: "1px solid rgba(220,38,38,0.4)", color: "#fca5a5", padding: "8px 16px", borderRadius: 7, fontSize: 12, fontWeight: 700, cursor: "pointer" }}>
                Clear Restriction
              </button>
            </div>
          </div>
        )}

        {/* API Keys */}
        {tab === "apikeys" && (
          <div>
            <div style={{ color: "white", fontWeight: 700, fontSize: 14, marginBottom: 16 }}>Push API Keys to Gateway</div>
            {[
              { label: "Groq (Primary Free)", env: "GROQ_API_KEY",        prefix: "gsk_" },
              { label: "Cerebras",             env: "CEREBRAS_API_KEY",    prefix: "csk-" },
              { label: "Gemini",               env: "GEMINI_API_KEY",      prefix: "AI" },
              { label: "xAI / Grok",           env: "XAI_API_KEY",         prefix: "xai-" },
              { label: "Cohere",               env: "COHERE_API_KEY",      prefix: "" },
              { label: "HuggingFace",          env: "HUGGINGFACE_API_KEY", prefix: "hf_" },
              { label: "Anthropic (paid)",     env: "ANTHROPIC_API_KEY",   prefix: "sk-ant" },
              { label: "ElevenLabs (exec TTS)",env: "ELEVENLABS_API_KEY",  prefix: "" },
            ].map(({ label, env, prefix }) => {
              const val = apiKeys[env] || "";
              const shown = showKeys[env];
              return (
                <div key={env} style={{ marginBottom: 10, display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
                  <div style={{ minWidth: 160, color: "rgba(255,255,255,0.7)", fontSize: 12, fontWeight: 600 }}>{label}</div>
                  <div style={{ flex: 1, display: "flex", gap: 6, minWidth: 220 }}>
                    <input
                      type={shown ? "text" : "password"}
                      placeholder={prefix ? `${prefix}…` : "paste key…"}
                      value={val}
                      onChange={e => setApiKeys(k => ({ ...k, [env]: e.target.value }))}
                      style={{ flex: 1, background: "rgba(255,255,255,0.08)", border: "1px solid rgba(255,255,255,0.15)", borderRadius: 6, padding: "6px 10px", color: "white", fontSize: 12, outline: "none" }}
                    />
                    <button onClick={() => setShowKeys(s => ({ ...s, [env]: !s[env] }))}
                      style={{ background: "rgba(255,255,255,0.1)", border: "none", color: "white", width: 30, borderRadius: 6, cursor: "pointer" }}>
                      {shown ? <EyeOff style={{ width: 13, height: 13 }} /> : <Eye style={{ width: 13, height: 13 }} />}
                    </button>
                    <button onClick={() => pushApiKey(env, val)} disabled={!val}
                      style={{ background: val ? SIG : "rgba(255,255,255,0.08)", border: "none", color: val ? INK : "rgba(255,255,255,0.3)", padding: "6px 12px", borderRadius: 6, fontSize: 11, fontWeight: 700, cursor: val ? "pointer" : "not-allowed" }}>
                      Push
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Visibility */}
        {tab === "visibility" && (
          <VisibilityTab visibility={visibility} setVisibility={setVisibility} />
        )}

        {/* Audit Log */}
        {tab === "audit" && (
          <div>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 14 }}>
              <span style={{ color: "white", fontWeight: 700, fontSize: 14 }}>Recent Audit Log</span>
              <button onClick={loadAudit} style={{ background: "rgba(255,255,255,0.1)", border: "none", color: "white", padding: "5px 10px", borderRadius: 6, fontSize: 11, cursor: "pointer" }}>Refresh</button>
            </div>
            {auditLog.length === 0
              ? <p style={{ color: "rgba(255,255,255,0.4)", fontSize: 13 }}>No audit entries loaded.</p>
              : auditLog.slice(0, 20).map((a, i) => (
                <div key={a.id || i} style={{ display: "flex", gap: 12, padding: "7px 0", borderBottom: "1px solid rgba(255,255,255,0.06)", alignItems: "flex-start" }}>
                  <div style={{ width: 6, height: 6, borderRadius: "50%", background: SIG, marginTop: 6, flexShrink: 0 }} />
                  <div style={{ flex: 1 }}>
                    <div style={{ color: "white", fontSize: 12, fontWeight: 600 }}>{a.actor?.full_name || a.actor?.email || a.actor_id || "system"}</div>
                    <div style={{ color: "rgba(255,209,0,0.7)", fontSize: 11, fontFamily: "monospace" }}>{a.action}</div>
                  </div>
                  <div style={{ color: "rgba(255,255,255,0.35)", fontSize: 10, whiteSpace: "nowrap" }}>{a.at ? new Date(a.at).toLocaleString() : ""}</div>
                </div>
              ))
            }
          </div>
        )}

      </div>
    </div>
  );
}

// ── Default section visibility (all on) ───────────────────────────────────────
const DEFAULT_VISIBILITY = {
  freeModules:  { label: "Free Modules",       minRank: 0 },
  features:     { label: "What We Do",         minRank: 0 },
  finance:      { label: "Finance Backbone",   minRank: 0 },
  roleLanes:    { label: "Role Lanes",         minRank: 0 },
  marketPulse:  { label: "Market Pulse",       minRank: 0 },
  governance:   { label: "Governance Pulse",   minRank: 0 },
  resources:    { label: "Resources",          minRank: 0 },
  support:      { label: "Support",            minRank: 0 },
};

// ── Visibility toggle panel (exec only) ───────────────────────────────────────
function VisibilityTab({ visibility, setVisibility }) {
  const RANK_LABELS = { 0: "Everyone", 1: "Students+", 2: "Instructors+", 3: "Admins+", 4: "Exec only" };
  const INK = "#2e1065"; const SIG = "#FFD100";
  return (
    <div>
      <div style={{ color: "white", fontWeight: 700, fontSize: 14, marginBottom: 6 }}>Section Visibility</div>
      <div style={{ color: "rgba(255,255,255,0.5)", fontSize: 11, marginBottom: 16 }}>
        Control which sections appear for each access level. Changes save instantly.
      </div>
      {Object.entries(visibility).map(([key, cfg]) => (
        <div key={key} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "8px 0", borderBottom: "1px solid rgba(255,255,255,0.07)" }}>
          <span style={{ color: "rgba(255,255,255,0.85)", fontSize: 13 }}>{cfg.label}</span>
          <div style={{ display: "flex", gap: 4 }}>
            {[0,1,2,3,4].map(rank => (
              <button key={rank} onClick={() => {
                const next = { ...visibility, [key]: { ...cfg, minRank: rank } };
                setVisibility(next);
                try { localStorage.setItem("mhc_visibility", JSON.stringify(next)); } catch {}
              }}
                style={{ padding: "3px 8px", borderRadius: 4, border: "none", fontSize: 10, fontWeight: 700, cursor: "pointer",
                  background: cfg.minRank === rank ? SIG : "rgba(255,255,255,0.12)",
                  color: cfg.minRank === rank ? INK : "rgba(255,255,255,0.6)" }}>
                {RANK_LABELS[rank]}
              </button>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

// ── Main component ─────────────────────────────────────────────────────────────
export default function MoreHelpCenter() {
  const { user } = useAuth();
  const [freeModules,  setFreeModules]  = useState([]);
  const [apiOnline,    setApiOnline]    = useState(null); // null = checking
  const [gwLabel,      setGwLabel]      = useState("Checking…");
  const [visibility,   setVisibility]   = useState(() => {
    try { const s = localStorage.getItem("mhc_visibility"); return s ? JSON.parse(s) : DEFAULT_VISIBILITY; } catch { return DEFAULT_VISIBILITY; }
  });

  useEffect(() => {
    api.get("/health")
      .then(() => { setApiOnline(true);  setGwLabel("Gateway online"); })
      .catch(() => { setApiOnline(false); setGwLabel("Gateway unavailable"); });
  }, []);

  useEffect(() => {
    if (apiOnline) {
      api.get("/modules").then(r => setFreeModules((r.data || []).filter(m => m.free))).catch(() => {});
    }
  }, [apiOnline]);

  // ── Mode resolution ──────────────────────────────────────────────────────────
  // Still checking API status — show nothing (avoids flash to decoy)
  if (apiOnline === null) {
    return (
      <div style={{ minHeight: "100vh", background: TEAL_DARK, display: "flex", alignItems: "center", justifyContent: "center" }}>
        <div style={{ color: "rgba(255,255,255,0.5)", fontSize: 14 }}>Loading MORE Help Center…</div>
      </div>
    );
  }

  // Decoy mode — API completely unreachable
  if (apiOnline === false && !isExec(user)) {
    return <DecoyMode />;
  }

  const execMode = isExec(user);
  const superExec = isSupExec(user);
  const userRank = ROLE_RANK[user?.role] ?? 0;
  const canSee = (key) => userRank >= (visibility[key]?.minRank ?? 0);

  const USER_DASHBOARD = {
    executive_admin: { label: "Executive Dashboard", to: "/admin/system", color: "#2e1065" },
    admin:           { label: "Admin Dashboard",      to: "/admin",        color: "#0d7377" },
    instructor:      { label: "Instructor Hub",       to: "/instructor",   color: COPPER },
    student:         { label: "My Dashboard",         to: "/dashboard",    color: TEAL },
  };

  return (
    <div style={{ minHeight: "100vh", background: WARM, color: "#1a1a2e" }}>
      {/* Accent bar */}
      <div style={{ height: 4, background: `linear-gradient(90deg, ${TEAL} 0%, ${GOLD} 50%, ${TEAL} 100%)` }} />

      {/* ── Header ── */}
      <header style={{ position: "sticky", top: 0, zIndex: 40, background: "#ffffff", borderBottom: "1px solid #e0d6cc" }}>
        <div style={{ maxWidth: 1200, margin: "0 auto", padding: "10px 24px", display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: 12 }}>
          <Link to="/more-help-center" style={{ display: "flex", alignItems: "center", gap: 10, textDecoration: "none" }}>
            <div style={{ width: 36, height: 36, borderRadius: 8, background: TEAL, display: "flex", alignItems: "center", justifyContent: "center", color: "white", fontWeight: 900, fontSize: 18 }}>M</div>
            <div>
              <div style={{ fontWeight: 800, fontSize: 14, color: TEAL, lineHeight: 1.2 }}>MORE Help Center</div>
              <div style={{ fontSize: 10, fontWeight: 700, textTransform: "uppercase", letterSpacing: 3, color: "#8a7e72" }}>
                {execMode ? (superExec ? "Exec · Supervisor Mode" : "Admin Mode") : "Goodwill Wing"}
              </div>
            </div>
          </Link>

          <nav style={{ display: "flex", alignItems: "center", gap: 16, flexWrap: "wrap" }}>
            {NAV_LINKS.map(({ label, to }) => (
              <Link key={to} to={to} style={{ fontSize: 12, fontWeight: 700, textTransform: "uppercase", letterSpacing: 2, color: "#5a4e42", textDecoration: "none" }}>{label}</Link>
            ))}
            {execMode && (
              <Link to="/admin/system" style={{ fontSize: 12, fontWeight: 700, textTransform: "uppercase", letterSpacing: 2, color: COPPER, textDecoration: "none", display: "flex", alignItems: "center", gap: 4 }}>
                <Crown style={{ width: 13, height: 13 }} /> Dashboard
              </Link>
            )}
            {!user
              ? <Link to="/login" style={{ background: GOLD, color: "#1a1a2e", padding: "7px 16px", borderRadius: 8, fontSize: 12, fontWeight: 700, textDecoration: "none" }}>Sign In →</Link>
              : null
            }
          </nav>
        </div>
      </header>

      <main style={{ maxWidth: 1200, margin: "0 auto", padding: "0 24px" }}>

        {/* ── Hero — always first, exec panel comes after ── */}
        <section style={{ borderRadius: 24, overflow: "hidden", marginTop: 32, marginBottom: 28, background: `linear-gradient(165deg, ${TEAL_DARK} 0%, #0a4e52 50%, ${TEAL} 100%)`, padding: "56px 40px", textAlign: "center", position: "relative" }}>
          <div style={{ position: "absolute", inset: 0, opacity: 0.08, backgroundImage: "radial-gradient(circle at 25px 25px, white 1px, transparent 0)", backgroundSize: "50px 50px" }} />
          <div style={{ position: "relative", zIndex: 1 }}>
            <div style={{ display: "inline-flex", alignItems: "center", gap: 6, padding: "6px 16px", borderRadius: 999, background: "rgba(255,255,255,0.15)", color: GOLD, fontSize: 11, fontWeight: 800, textTransform: "uppercase", letterSpacing: 3, marginBottom: 24 }}>
              <Heart style={{ width: 12, height: 12 }} /> 100% Free · Community-Powered
            </div>
            <h1 style={{ color: "white", fontSize: "clamp(32px, 6vw, 56px)", fontWeight: 900, lineHeight: 1.1, marginBottom: 16 }}>
              Help is here.<br /><span style={{ color: GOLD }}>Free, always.</span>
            </h1>
            <p style={{ color: "#c8e6e8", fontSize: 18, maxWidth: 560, margin: "0 auto 28px", lineHeight: 1.7 }}>
              No paywalls. No sign-ups for core help. Free training, community support, and real guidance — no strings attached.
            </p>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 12, justifyContent: "center" }}>
              <a href="#modules" style={{ background: GOLD, color: "#1a1a2e", padding: "12px 28px", borderRadius: 8, fontWeight: 800, fontSize: 13, textDecoration: "none", textTransform: "uppercase", letterSpacing: 2 }}>Start Learning Free</a>
              <a href="#support" style={{ border: `2px solid ${GOLD}`, color: "white", padding: "12px 28px", borderRadius: 8, fontWeight: 800, fontSize: 13, textDecoration: "none", textTransform: "uppercase", letterSpacing: 2 }}>Get Support</a>
              <Link to="/community" style={{ border: `2px solid rgba(255,255,255,0.4)`, color: "white", padding: "12px 28px", borderRadius: 8, fontWeight: 800, fontSize: 13, textDecoration: "none", textTransform: "uppercase", letterSpacing: 2 }}>Join Community</Link>
            </div>
          </div>
        </section>

        {/* ── Logged-in user: your space card (item 7) ── */}
        {user && USER_DASHBOARD[user.role] && (
          <div style={{ background: "white", borderRadius: 14, border: "1px solid #e0d6cc", padding: "14px 20px", marginBottom: 24, display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: 12 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <div style={{ width: 36, height: 36, borderRadius: "50%", background: USER_DASHBOARD[user.role].color, display: "flex", alignItems: "center", justifyContent: "center", color: "white", fontWeight: 900, fontSize: 14 }}>
                {(user.full_name || "U")[0].toUpperCase()}
              </div>
              <div>
                <div style={{ fontWeight: 700, fontSize: 14, color: "#2b1f15" }}>Welcome back, {user.full_name?.split(" ")[0] || "there"}.</div>
                <div style={{ fontSize: 11, color: "#8a7e72", textTransform: "capitalize" }}>{(user.role || "").replace("_", " ")} · WAI-Institute</div>
              </div>
            </div>
            <Link to={USER_DASHBOARD[user.role].to} style={{ background: USER_DASHBOARD[user.role].color, color: "white", padding: "8px 18px", borderRadius: 8, fontWeight: 700, fontSize: 12, textDecoration: "none", display: "flex", alignItems: "center", gap: 6 }}>
              {USER_DASHBOARD[user.role].label} <ArrowRight style={{ width: 13, height: 13 }} />
            </Link>
          </div>
        )}

        {/* ── Exec Supervisor Panel (admin + executive_admin only) ── */}
        {execMode && (
          <div style={{ marginBottom: 32 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 16 }}>
              <Crown style={{ width: 18, height: 18, color: GOLD }} />
              <span style={{ fontWeight: 800, fontSize: 16, color: "#2b1f15" }}>Supervisor Controls</span>
              <span style={{ fontSize: 11, color: "#8d5a33", background: "#fff3e0", padding: "2px 8px", borderRadius: 20, fontWeight: 700, textTransform: "uppercase", letterSpacing: 1 }}>
                {superExec ? "Executive Admin" : "Admin"}
              </span>
            </div>
            <ExecPanel apiOnline={apiOnline} visibility={visibility} setVisibility={setVisibility} />
          </div>
        )}

        {/* ── Gateway status strip ── */}
        <div style={{ background: "white", borderRadius: 12, padding: "12px 20px", marginBottom: 32, display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: 12, border: "1px solid #e0d6cc" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <div style={{ width: 8, height: 8, borderRadius: "50%", background: apiOnline ? "#22c55e" : "#dc2626" }} />
            <span style={{ fontSize: 13, fontWeight: 600, color: "#4b4038" }}>{gwLabel}</span>
          </div>
          <div style={{ display: "flex", gap: 16, flexWrap: "wrap" }}>
            {[
              { label: "WAI Help Center",    to: "/help-center" },
              { label: "Explore M.O.R.E.",   to: "/more" },
              { label: "Plans & Programs",   to: "/plans" },
              ...(execMode ? [{ label: "Executive Corridor", to: "/admin/system" }] : []),
            ].map(({ label, to }) => (
              <Link key={to} to={to} style={{ fontSize: 12, fontWeight: 700, color: TEAL, textDecoration: "underline" }}>{label}</Link>
            ))}
          </div>
        </div>

        {/* ── Waypoints ── */}
        <section style={{ marginBottom: 48 }}>
          <div style={{ marginBottom: 24 }}>
            <div style={{ fontSize: 11, fontWeight: 800, textTransform: "uppercase", letterSpacing: 3, color: COPPER, marginBottom: 6 }}>How the plaza works</div>
            <h2 style={{ fontSize: 28, fontWeight: 900, color: "#2b1f15" }}>Your path through the center</h2>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(220px,1fr))", gap: 16 }}>
            {WAYPOINTS.map(pt => {
              const Icon = pt.icon;
              return (
                <div key={pt.title} style={{ background: "white", borderRadius: 20, padding: 24, border: "1px solid #e2d3ba", boxShadow: "0 14px 35px rgba(96,62,28,0.08)" }}>
                  <div style={{ width: 48, height: 48, borderRadius: 16, background: "#f7ebdc", display: "flex", alignItems: "center", justifyContent: "center", color: COPPER, marginBottom: 16 }}>
                    <Icon style={{ width: 22, height: 22 }} />
                  </div>
                  <h3 style={{ fontWeight: 800, fontSize: 16, color: "#2b1f15", marginBottom: 8 }}>{pt.title}</h3>
                  <p style={{ fontSize: 13, color: "#5c4c41", lineHeight: 1.6 }}>{pt.desc}</p>
                </div>
              );
            })}
          </div>
        </section>

        {/* ── Free Modules ── */}
        {canSee("freeModules") && freeModules.length > 0 && (
          <section id="modules" style={{ marginBottom: 48 }}>
            <div style={{ textAlign: "center", marginBottom: 32 }}>
              <div style={{ fontSize: 11, fontWeight: 800, textTransform: "uppercase", letterSpacing: 3, color: TEAL, marginBottom: 6 }}>Free Curriculum</div>
              <h2 style={{ fontSize: 28, fontWeight: 900, color: "#1a1a2e" }}>Start Here — No Account Needed</h2>
              <p style={{ color: "#6b5e52", marginTop: 8 }}>Complete free modules and earn Partnership Points toward the full program.</p>
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(280px,1fr))", gap: 20 }}>
              {freeModules.map(m => (
                <Link to={`/modules/${m.slug}`} key={m.slug} style={{ display: "block", padding: 24, borderRadius: 16, background: WARM, border: "1px solid #e0d6cc", textDecoration: "none", transition: "transform 0.2s" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 12 }}>
                    <span style={{ background: GOLD, color: "#1a1a2e", padding: "3px 10px", borderRadius: 20, fontSize: 10, fontWeight: 900, textTransform: "uppercase" }}>FREE</span>
                    {m.points && <span style={{ fontSize: 12, fontWeight: 700, color: TEAL }}>+{m.points} pts</span>}
                  </div>
                  <h3 style={{ fontWeight: 800, fontSize: 18, color: "#1a1a2e", marginBottom: 8 }}>{m.title}</h3>
                  <p style={{ fontSize: 13, color: "#5a4e42", lineHeight: 1.6 }}>{m.summary}</p>
                  <div style={{ display: "flex", gap: 16, marginTop: 14, fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: 1, color: TEAL }}>
                    <span>{m.hours}h</span>
                    <ArrowRight style={{ width: 13, height: 13 }} />
                  </div>
                </Link>
              ))}
            </div>
            <div style={{ textAlign: "center", marginTop: 24 }}>
              <Link to="/register" style={{ display: "inline-flex", alignItems: "center", gap: 8, padding: "10px 24px", border: `2px solid ${TEAL}`, borderRadius: 8, color: TEAL, fontWeight: 700, fontSize: 13, textDecoration: "none", textTransform: "uppercase", letterSpacing: 1 }}>
                Create Account for Full Program <ArrowRight style={{ width: 15, height: 15 }} />
              </Link>
            </div>
          </section>
        )}

        {/* ── Features grid ── */}
        {canSee("features") && <section style={{ marginBottom: 48 }}>
          <div style={{ display: "flex", alignItems: "flex-end", justifyContent: "space-between", marginBottom: 24, flexWrap: "wrap", gap: 12 }}>
            <div>
              <div style={{ fontSize: 11, fontWeight: 800, textTransform: "uppercase", letterSpacing: 3, color: COPPER, marginBottom: 6 }}>Designed around the hub</div>
              <h2 style={{ fontSize: 28, fontWeight: 900, color: "#2b1f15" }}>What this center is built to do</h2>
            </div>
            <div style={{ background: CREAM, border: `1px solid #d7b290`, borderRadius: 999, padding: "8px 18px", fontSize: 13, fontWeight: 600, color: "#5c422c" }}>
              Finance-led autonomy + community guidance
            </div>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(260px,1fr))", gap: 20 }}>
            {FEATURES.map(f => {
              const Icon = f.icon;
              return (
                <div key={f.title} style={{ background: "white", borderRadius: 20, padding: 28, border: "1px solid #e4d1b4", boxShadow: "0 20px 45px rgba(102,70,33,0.08)" }}>
                  <div style={{ width: 52, height: 52, borderRadius: 16, background: "#f7ebdc", display: "flex", alignItems: "center", justifyContent: "center", color: COPPER, marginBottom: 16 }}>
                    <Icon style={{ width: 24, height: 24 }} />
                  </div>
                  <h3 style={{ fontWeight: 800, fontSize: 18, color: "#2b1f15", marginBottom: 8 }}>{f.title}</h3>
                  <p style={{ fontSize: 13, color: "#5c4e44", lineHeight: 1.7 }}>{f.desc}</p>
                </div>
              );
            })}
          </div>
        </section>}

        {/* ── Finance backbone (from SeshatsHub) ── */}
        {canSee("finance") && <section style={{ marginBottom: 48, background: CREAM, borderRadius: 24, border: `1px solid #d8b88e`, padding: "40px 36px", boxShadow: "0 24px 80px rgba(97,60,20,0.12)" }}>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(280px,1fr))", gap: 32, alignItems: "start" }}>
            <div>
              <div style={{ fontSize: 11, fontWeight: 800, textTransform: "uppercase", letterSpacing: 3, color: COPPER, marginBottom: 10 }}>Finance Backbone</div>
              <h2 style={{ fontSize: 30, fontWeight: 900, color: "#2b1f15", marginBottom: 16 }}>The finance department acts like its own autonomous staff.</h2>
              <p style={{ fontSize: 15, color: "#524236", lineHeight: 1.8, marginBottom: 20 }}>
                Every resource in the center is supported by finance, compliance, and revenue operations — making this not just a landing spot, but a living marketplace.
              </p>
              <ul style={{ listStyle: "none", padding: 0, space: 0 }}>
                {["Real-time budget visibility for help center initiatives.", "Compliance and approvals built into autonomous workflows.", "Finance staff personas coordinate with production, legal, and community teams."].map(item => (
                  <li key={item} style={{ display: "flex", gap: 10, marginBottom: 12, fontSize: 14, color: "#4c3f35" }}>
                    <BadgeCheck style={{ width: 18, height: 18, color: COPPER, marginTop: 2, flexShrink: 0 }} /> {item}
                  </li>
                ))}
              </ul>
            </div>
            <div style={{ background: "#fff5e5", borderRadius: 20, border: `1px solid #e3c6a6`, padding: 24 }}>
              <div style={{ fontSize: 11, fontWeight: 800, textTransform: "uppercase", letterSpacing: 3, color: COPPER, marginBottom: 14 }}>Supervisor briefing</div>
              <p style={{ fontSize: 13, color: "#4f4134", lineHeight: 1.7, marginBottom: 12 }}>
                The Supervisor is the landing greeter and navigator — the host offering a warm welcome and making the mission obvious from the first moment.
              </p>
              <p style={{ fontSize: 13, fontWeight: 700, color: "#6b4c2b", lineHeight: 1.7 }}>
                Human oversight is a must-have: executive review, audit checkpoints, and real people ensure every action is safe, compliant, and accountable.
              </p>
              <div style={{ marginTop: 16, background: "#fff1d2", borderRadius: 12, padding: 16 }}>
                <div style={{ fontWeight: 700, color: "#3e2f1f", fontSize: 13 }}>Gateway status</div>
                <div style={{ fontSize: 16, fontWeight: 800, color: apiOnline ? "#166534" : "#991b1b", marginTop: 6 }}>{gwLabel}</div>
              </div>
            </div>
          </div>
        </section>}

        {/* ── Role lanes ── */}
        {canSee("roleLanes") && <section style={{ marginBottom: 48 }}>
          <div style={{ marginBottom: 24 }}>
            <div style={{ fontSize: 11, fontWeight: 800, textTransform: "uppercase", letterSpacing: 3, color: COPPER, marginBottom: 6 }}>Role-based lanes</div>
            <h2 style={{ fontSize: 28, fontWeight: 900, color: "#2b1f15" }}>Choose your entry path</h2>
            <p style={{ marginTop: 8, fontSize: 14, color: "#5c4c41", maxWidth: 480 }}>
              The center supports different personas with specific corridors: visitors, operators, supervisors, and auditors all have distinct journeys.
            </p>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(200px,1fr))", gap: 16 }}>
            {ROLE_LANES.map(lane => {
              const Icon = lane.icon;
              return (
                <div key={lane.title} style={{ background: "white", borderRadius: 20, padding: 24, border: "1px solid #e4d1b4", boxShadow: "0 18px 45px rgba(96,62,28,0.08)" }}>
                  <div style={{ width: 44, height: 44, borderRadius: 14, background: "#f7ead9", display: "flex", alignItems: "center", justifyContent: "center", color: "#855a32", marginBottom: 14 }}>
                    <Icon style={{ width: 20, height: 20 }} />
                  </div>
                  <h3 style={{ fontWeight: 800, fontSize: 16, color: "#2b1f15", marginBottom: 8 }}>{lane.title}</h3>
                  <p style={{ fontSize: 13, color: "#5c4c41", lineHeight: 1.6 }}>{lane.desc}</p>
                </div>
              );
            })}
          </div>
        </section>}

        {/* ── Market Pulse — quick actions (from Seshat's Hub) ── */}
        {canSee("marketPulse") && <section style={{ marginBottom: 48 }}>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(280px,1fr))", gap: 32, alignItems: "start" }}>
            <div>
              <div style={{ fontSize: 11, fontWeight: 800, textTransform: "uppercase", letterSpacing: 3, color: COPPER, marginBottom: 6 }}>Meet the market</div>
              <h2 style={{ fontSize: 28, fontWeight: 900, color: "#2b1f15", marginBottom: 16 }}>What visitors do here</h2>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(200px,1fr))", gap: 16 }}>
                {[
                  { icon: MapPin,  title: "Receive a guided welcome",  desc: "The Supervisor points new visitors to platform support, finance tools, and the help center." },
                  { icon: Globe,   title: "Access the help center",     desc: "Find help across housing, legal, training, and community resources with a single click." },
                  { icon: Users,   title: "Join the market experience", desc: "Browse the community marketplace of services, courses, and production support." },
                ].map(item => {
                  const Icon = item.icon;
                  return (
                    <div key={item.title} style={{ background: "white", borderRadius: 20, padding: 24, border: "1px solid #e3ccb1", boxShadow: "0 18px 45px rgba(90,60,30,0.08)" }}>
                      <div style={{ width: 44, height: 44, borderRadius: 14, background: "#f7ead9", display: "flex", alignItems: "center", justifyContent: "center", color: "#855a32", marginBottom: 14 }}>
                        <Icon style={{ width: 20, height: 20 }} />
                      </div>
                      <h3 style={{ fontWeight: 800, fontSize: 16, color: "#2b1f15", marginBottom: 8 }}>{item.title}</h3>
                      <p style={{ fontSize: 13, color: "#5c4c41", lineHeight: 1.7 }}>{item.desc}</p>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Market Pulse sidebar */}
            <div style={{ background: "#fffdf7", borderRadius: 20, border: "1px solid #ebd8c6", padding: 24, boxShadow: "0 14px 50px rgba(97,70,42,0.08)" }}>
              <div style={{ fontSize: 10, fontWeight: 800, textTransform: "uppercase", letterSpacing: 3, color: "#7c593d", marginBottom: 8 }}>Market Pulse</div>
              <div style={{ fontSize: 20, fontWeight: 800, color: "#2e1f17", marginBottom: 20 }}>Live services in this plaza</div>
              <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                <Link to="/help-center" style={{ display: "block", borderRadius: 16, padding: "14px 18px", fontSize: 13, fontWeight: 700, textDecoration: "none", background: "#f6d06d", color: "#1a1a2e" }}>Visit the Help Center</Link>
                <Link to="/more"        style={{ display: "block", borderRadius: 16, padding: "14px 18px", fontSize: 13, fontWeight: 700, textDecoration: "none", background: TEAL, color: "white" }}>Explore M.O.R.E.</Link>
                <Link to="/community"   style={{ display: "block", borderRadius: 16, padding: "14px 18px", fontSize: 13, fontWeight: 700, textDecoration: "none", background: "#583c1d", color: "white" }}>Community Marketplace</Link>
                {execMode && (
                  <Link to="/admin/system" style={{ display: "block", borderRadius: 16, padding: "14px 18px", fontSize: 13, fontWeight: 700, textDecoration: "none", background: "#5a3d1a", color: "white" }}>Executive Oversight</Link>
                )}
              </div>
            </div>
          </div>
        </section>}

        {/* ── Process map + Service ownership (from Seshat's Hub) ── */}
        {canSee("governance") && <section style={{ marginBottom: 48, background: "#fff9ed", borderRadius: 24, border: "1px solid #d8b88e", padding: "36px 32px", boxShadow: "0 24px 60px rgba(97,60,20,0.12)" }}>
          <div style={{ display: "flex", alignItems: "flex-end", justifyContent: "space-between", flexWrap: "wrap", gap: 12, marginBottom: 24 }}>
            <div>
              <div style={{ fontSize: 11, fontWeight: 800, textTransform: "uppercase", letterSpacing: 3, color: COPPER, marginBottom: 6 }}>Governance pulse</div>
              <h2 style={{ fontSize: 26, fontWeight: 900, color: "#2b1f15" }}>Live oversight, analytics, and process flow</h2>
            </div>
            <div style={{ background: "#fff5e5", border: "1px solid #d7b290", borderRadius: 999, padding: "7px 16px", fontSize: 13, fontWeight: 600, color: "#5c422c" }}>
              Built for human review and executive visibility
            </div>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(280px,1fr))", gap: 20 }}>
            {/* Process map */}
            <div style={{ background: "white", borderRadius: 20, padding: 24, border: "1px solid #e4d1b4", boxShadow: "0 18px 50px rgba(96,62,28,0.08)" }}>
              <div style={{ fontSize: 10, fontWeight: 800, textTransform: "uppercase", letterSpacing: 2, color: COPPER, marginBottom: 16 }}>Process map</div>
              <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                {[
                  { step: "1. Request", desc: "A visitor enters the plaza and selects help, service, finance, or community support." },
                  { step: "2. Review",  desc: "The Supervisor and operator lane assess the need, apply compliance checks, and route the request." },
                  { step: "3. Approve", desc: "Human oversight verifies decisions, triggers executive visibility, or escalates to audit if needed." },
                  { step: "4. Execute", desc: "Workflows are completed and results are published to the help system for future reference." },
                ].map(s => (
                  <div key={s.step} style={{ background: "#f7ead9", borderRadius: 12, padding: "12px 16px" }}>
                    <div style={{ fontWeight: 700, color: "#2b1f15", fontSize: 13 }}>{s.step}</div>
                    <div style={{ fontSize: 12, color: "#4c3f35", marginTop: 4, lineHeight: 1.6 }}>{s.desc}</div>
                  </div>
                ))}
              </div>
            </div>
            {/* Service ownership */}
            <div style={{ background: "#fff7e3", borderRadius: 20, padding: 24, border: "1px solid #e4d1b4", boxShadow: "0 18px 50px rgba(96,62,28,0.08)" }}>
              <div style={{ fontSize: 10, fontWeight: 800, textTransform: "uppercase", letterSpacing: 2, color: COPPER, marginBottom: 16 }}>Service ownership</div>
              {[
                { owner: "Finance",    desc: "Manages budgets, approvals, and audit trails for every community and help service." },
                { owner: "Compliance", desc: "Verifies that recommendations follow policy, privacy, and safety standards." },
                { owner: "Community",  desc: "Operates the marketplace lanes and ensures each service has a visible help manual entry." },
              ].map(s => (
                <div key={s.owner} style={{ marginBottom: 16 }}>
                  <div style={{ fontWeight: 700, color: "#2b1f15", fontSize: 14 }}>{s.owner}</div>
                  <div style={{ fontSize: 12, color: "#4c3f35", marginTop: 4, lineHeight: 1.6 }}>{s.desc}</div>
                </div>
              ))}
            </div>
          </div>
        </section>}

        {/* ── Resources ── */}
        {canSee("resources") && <section id="resources" style={{ marginBottom: 48 }}>
          <div style={{ textAlign: "center", marginBottom: 32 }}>
            <div style={{ fontSize: 11, fontWeight: 800, textTransform: "uppercase", letterSpacing: 3, color: TEAL, marginBottom: 6 }}>Goodwill Resources</div>
            <h2 style={{ fontSize: 28, fontWeight: 900, color: "#1a1a2e" }}>Everything You Need, No Cost</h2>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(220px,1fr))", gap: 16 }}>
            {[
              { icon: BookOpen,     title: "Free Modules",    desc: "Hands-on training free forever.", to: "/modules",   internal: true },
              { icon: MessageSquare,title: "Community",       desc: "Real answers from real people.",  to: "/community", internal: true },
              { icon: Shield,       title: "Support Line",    desc: "Email us — no bots, no runaround.", to: `mailto:${SUPPORT_EMAIL}`, internal: false },
              { icon: Globe,        title: "Full Program",    desc: "Enroll in the complete WAI curriculum.", to: "/courses", internal: true },
              { icon: BadgeCheck,   title: "Help Center",     desc: "Core support and community navigation.", to: "/help-center", internal: true },
              { icon: Activity,     title: "Plans",           desc: "Training, services, and subscriptions.", to: "/plans",  internal: true },
            ].map(r => {
              const Icon = r.icon;
              const content = (
                <>
                  <div style={{ width: 40, height: 40, borderRadius: 12, background: TEAL, display: "flex", alignItems: "center", justifyContent: "center", marginBottom: 14 }}>
                    <Icon style={{ width: 18, height: 18, color: "white" }} />
                  </div>
                  <h3 style={{ fontWeight: 800, fontSize: 16, color: "#1a1a2e", marginBottom: 6 }}>{r.title}</h3>
                  <p style={{ fontSize: 13, color: "#5a4e42", lineHeight: 1.6 }}>{r.desc}</p>
                </>
              );
              const sharedStyle = { display: "block", background: "white", padding: 22, borderRadius: 16, border: "1px solid #e0d6cc", textDecoration: "none" };
              return r.internal
                ? <Link key={r.title} to={r.to} style={sharedStyle}>{content}</Link>
                : <a    key={r.title} href={r.to} style={sharedStyle}>{content}</a>;
            })}
          </div>
        </section>}

        {/* ── Support section ── */}
        {canSee("support") && <section id="support" style={{ textAlign: "center", background: "white", borderRadius: 24, padding: "48px 32px", marginBottom: 48, border: "1px solid #e0d6cc" }}>
          <div style={{ display: "inline-flex", alignItems: "center", gap: 8, padding: "6px 16px", borderRadius: 999, background: WARM, color: TEAL, fontSize: 11, fontWeight: 800, textTransform: "uppercase", letterSpacing: 2, marginBottom: 20 }}>
            <Phone style={{ width: 13, height: 13 }} /> Get In Touch
          </div>
          <h2 style={{ fontSize: 28, fontWeight: 900, color: "#1a1a2e", marginBottom: 12 }}>Need Help?</h2>
          <p style={{ fontSize: 16, color: "#5a4e42", maxWidth: 480, margin: "0 auto 28px" }}>
            Email us at{" "}
            <a href={`mailto:${SUPPORT_EMAIL}`} style={{ color: TEAL, fontWeight: 700 }}>{SUPPORT_EMAIL}</a>
            {" "}— we respond within 24 hours.
          </p>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 12, justifyContent: "center" }}>
            <a href={`mailto:${SUPPORT_EMAIL}`} style={{ background: TEAL, color: "white", padding: "11px 24px", borderRadius: 8, fontWeight: 700, fontSize: 13, textDecoration: "none" }}>Email Support</a>
            <Link to="/help-center" style={{ border: `2px solid ${TEAL}`, color: TEAL, padding: "11px 24px", borderRadius: 8, fontWeight: 700, fontSize: 13, textDecoration: "none" }}>Help Center</Link>
            <Link to="/community" style={{ border: `2px solid ${TEAL}`, color: TEAL, padding: "11px 24px", borderRadius: 8, fontWeight: 700, fontSize: 13, textDecoration: "none" }}>Community Forum</Link>
          </div>
        </section>}

        {/* ── Exec-only: Governance pulse (from SeshatsHub) ── */}
        {execMode && canSee("governance") && (
          <section style={{ marginBottom: 48, background: "#fff9ed", borderRadius: 24, border: `1px solid #d8b88e`, padding: "36px 32px" }}>
            <div style={{ marginBottom: 20 }}>
              <div style={{ fontSize: 11, fontWeight: 800, textTransform: "uppercase", letterSpacing: 3, color: COPPER, marginBottom: 6 }}>Governance pulse</div>
              <h2 style={{ fontSize: 24, fontWeight: 900, color: "#2b1f15" }}>Live oversight, analytics, and process flow</h2>
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(180px,1fr))", gap: 12, marginBottom: 24 }}>
              {["Audit readiness", "Observability", "Fallback mode"].map(label => (
                <div key={label} style={{ background: "white", borderRadius: 16, padding: 20, border: "1px solid #e2d2b7" }}>
                  <div style={{ fontWeight: 700, color: "#2b1f15", marginBottom: 8 }}>{label}</div>
                  <p style={{ fontSize: 12, color: "#5c4c41", lineHeight: 1.6 }}>
                    {label === "Audit readiness" && "Every task can be traced back to a supervisor review and compliance checklist."}
                    {label === "Observability" && "Usage trends, service demand, and escalation volume are visible in the dashboard."}
                    {label === "Fallback mode" && "When automation is unstable, the Supervisor switches to manual support and exec review routes."}
                  </p>
                </div>
              ))}
            </div>
            <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
              <Link to="/admin/system"      style={{ background: "#2e1065", color: "white", padding: "10px 20px", borderRadius: 8, fontWeight: 700, fontSize: 13, textDecoration: "none" }}>Executive Dashboard</Link>
              <Link to="/admin/audit"       style={{ border: "1px solid #d8b88e", color: COPPER, padding: "10px 20px", borderRadius: 8, fontWeight: 700, fontSize: 13, textDecoration: "none" }}>Audit Log</Link>
              <Link to="/admin/health"      style={{ border: "1px solid #d8b88e", color: COPPER, padding: "10px 20px", borderRadius: 8, fontWeight: 700, fontSize: 13, textDecoration: "none" }}>System Health</Link>
              <Link to="/admin/moderation"  style={{ border: "1px solid #d8b88e", color: COPPER, padding: "10px 20px", borderRadius: 8, fontWeight: 700, fontSize: 13, textDecoration: "none" }}>Moderation</Link>
            </div>
          </section>
        )}

      </main>

      {/* ── Footer ── */}
      <footer style={{ background: "#0d2b2d", color: "#7ab8bb", padding: "28px 24px" }}>
        <div style={{ maxWidth: 1200, margin: "0 auto", display: "flex", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between", gap: 16, fontSize: 12 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <Heart style={{ width: 13, height: 13 }} />
            <span>MORE Help Center — Goodwill Wing of WAI Institute</span>
          </div>
          <div style={{ display: "flex", gap: 20, flexWrap: "wrap" }}>
            <Link to="/privacy"    style={{ color: "#7ab8bb", textDecoration: "none" }}>Privacy</Link>
            <Link to="/terms"      style={{ color: "#7ab8bb", textDecoration: "none" }}>Terms</Link>
            <Link to="/modules"    style={{ color: "#7ab8bb", textDecoration: "none" }}>Modules</Link>
            <Link to="/community"  style={{ color: "#7ab8bb", textDecoration: "none" }}>Community</Link>
            <Link to="/register"   style={{ color: GOLD, fontWeight: 700, textDecoration: "none" }}>Join WAI →</Link>
            <a href={`mailto:${SUPPORT_EMAIL}`} style={{ color: "#7ab8bb", textDecoration: "none" }}>Contact</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
