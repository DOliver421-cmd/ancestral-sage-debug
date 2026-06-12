/**
 * SeshatsHub.jsx — Supervisor Control Panel + Backup System Panel
 * Route:       /supervisor  (SupervisorProtected — executive_admin only)
 * Purpose:     Standalone supervisor interface. NOT a redirect to or wrapper
 *              of the Executive Panel. Has its own controls, its own backend
 *              routes, and doubles as the primary Backup System Control Panel.
 *
 * Tabs:
 *   overview      — supervisor dashboard summary, continuity check
 *   moderation    — content queue (posts, needs, appeals, flags)
 *   escalations   — escalation chain management
 *   greeter       — visitor flow + greeter/persona config
 *   sage          — sage session review, flagging, cap status
 *   backup        — backup system: provider switching, gateway reset,
 *                   breaker panel, free matrix, emergency broadcast
 *   rbac          — permission matrix, MFA config, IP whitelist
 *   audit         — full audit log with export
 *
 * Backend routes (all require executive_admin):
 *   GET  /supervisor/dashboard
 *   GET  /supervisor/escalations
 *   POST /supervisor/escalations
 *   POST /supervisor/escalations/{id}/resolve
 *   GET  /supervisor/greeter/config
 *   PATCH /supervisor/greeter/config
 *   GET  /supervisor/visitor-flow
 *   PATCH /supervisor/visitor-flow
 *   POST /supervisor/content/{type}/{id}/approve
 *   POST /supervisor/content/{type}/{id}/reject
 *   GET  /supervisor/backup/status
 *   POST /supervisor/backup/switch-provider
 *   POST /supervisor/backup/reset-gateway
 *   GET  /supervisor/backup/free-matrix
 *   POST /supervisor/backup/emergency-broadcast
 *   GET  /supervisor/sage/sessions
 *   POST /supervisor/sage/sessions/{id}/flag
 *   GET  /supervisor/system/continuity-check
 *   GET  /more/admin/queue
 *   GET  /more/admin/flags
 *   GET  /admin/rbac/matrix
 *   PATCH /admin/rbac/matrix
 *   GET  /admin/mfa/config
 *   PATCH /admin/mfa/config
 *   GET  /admin/access/ipwhitelist
 *   POST /admin/access/ipwhitelist
 *   DELETE /admin/access/ipwhitelist/{id}
 *   GET  /admin/audit
 *   GET  /admin/audit/export
 *   GET  /exec/panel
 *   POST /exec/panel/toggle
 *   POST /exec/panel/reset
 *   GET  /exec/panel/health
 *   POST /exec/failover
 *   GET  /exec/free-backup-matrix
 *   GET  /admin/sage/cap
 *   GET  /admin/sage/status
 */

import { useState, useEffect, useCallback } from "react";
import { useNavigate, Link } from "react-router-dom";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";

// ── Palette (African marketplace, supervisor dark theme) ──────────────────────
const BG     = "#0d0f1a";
const PANEL  = "#131620";
const BORDER = "rgba(74,242,197,0.15)";
const SIG    = "#4af2c5";
const WARN   = "#f59e0b";
const ERR    = "#f87171";
const OK     = "#4ade80";
const MUTED  = "rgba(200,210,230,0.45)";
const WHITE  = "#f0f4ff";
const BARK   = "#8d5a33";
const AMBER  = "#f6d06d";

const TABS = [
  { key: "overview",    label: "Overview" },
  { key: "moderation",  label: "Moderation" },
  { key: "escalations", label: "Escalations" },
  { key: "greeter",     label: "Greeter / Flow" },
  { key: "sage",        label: "Sage Sessions" },
  { key: "backup",      label: "Backup System" },
  { key: "rbac",        label: "RBAC" },
  { key: "audit",       label: "Audit Log" },
];

const ALL_ROLES  = ["student","instructor","admin","executive_admin"];
const ROLE_LABEL = { student:"Student", instructor:"Instructor", admin:"Admin", executive_admin:"Executive Admin" };
const PROVIDERS  = ["groq","cerebras","gemini","xai","cohere","openrouter","huggingface","anthropic"];
const PERM_KEYS  = ["content_read","content_create","content_edit_own","content_delete_own","user_warn","user_mute","user_ban","api_access","billing_view","export_data"];

// ── Shared styles ─────────────────────────────────────────────────────────────
const card  = { background: PANEL, border: `1px solid ${BORDER}`, borderRadius: 10, padding: "14px 18px", marginBottom: 14 };
const label = { fontSize: 10, textTransform: "uppercase", letterSpacing: "0.1em", color: MUTED, marginBottom: 6, display: "block" };
const inp   = { background: "rgba(255,255,255,0.05)", border: `1px solid ${BORDER}`, borderRadius: 6, padding: "7px 12px", fontSize: 12, color: WHITE, outline: "none", width: "100%" };
const btn   = (color = SIG) => ({ border: `1px solid ${color}`, background: "transparent", color, borderRadius: 6, padding: "5px 14px", fontSize: 11, fontWeight: 700, cursor: "pointer" });
const chip  = (on) => ({ fontSize: 10, padding: "3px 10px", borderRadius: 999, cursor: "pointer", border: `1px solid ${on ? SIG : BORDER}`, color: on ? SIG : MUTED, background: "transparent" });
const section_head = { color: SIG, fontWeight: 700, fontSize: 11, textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: 12 };

// ── Utility ───────────────────────────────────────────────────────────────────
function StatusDot({ v }) {
  const c = v === "ok" || v === true ? OK : v === "error" || v === false ? ERR : WARN;
  return <span style={{ display:"inline-block", width:8, height:8, borderRadius:"50%", background:c, boxShadow:`0 0 6px ${c}`, marginRight:6 }} />;
}

function SectionLabel({ children }) {
  return <div style={section_head}>{children}</div>;
}

function InfoGrid({ items }) {
  return (
    <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fit,minmax(130px,1fr))", gap:8 }}>
      {items.map(([k,v,color]) => (
        <div key={k} style={{ background:"rgba(255,255,255,0.04)", borderRadius:6, padding:"7px 12px" }}>
          <div style={{ color:MUTED, fontSize:9, textTransform:"uppercase", letterSpacing:1 }}>{k}</div>
          <div style={{ color:color||WHITE, fontWeight:700, fontSize:13, marginTop:3 }}>{String(v ?? "—")}</div>
        </div>
      ))}
    </div>
  );
}

// ── Tab: Overview ─────────────────────────────────────────────────────────────
// Routes: GET /supervisor/dashboard, GET /supervisor/system/continuity-check
function OverviewTab({ notify }) {
  const [dash,  setDash]  = useState(null);
  const [check, setCheck] = useState(null);
  const [runningCheck, setRunningCheck] = useState(false);

  const load = useCallback(async () => {
    try { const r = await api.get("/supervisor/dashboard"); setDash(r.data); } catch {}
  }, []);

  useEffect(() => { load(); }, [load]);

  async function runContinuityCheck() {
    setRunningCheck(true);
    try {
      const r = await api.get("/supervisor/system/continuity-check");
      setCheck(r.data);
    } catch (e) {
      notify("Continuity check failed: " + (e?.response?.data?.detail || e.message), true);
    } finally { setRunningCheck(false); }
  }

  return (
    <div>
      <SectionLabel>Supervisor Dashboard</SectionLabel>

      {dash && (
        <>
          <div style={card}>
            <div style={{ color:MUTED, fontSize:10, textTransform:"uppercase", letterSpacing:1, marginBottom:10 }}>Moderation Queue</div>
            <InfoGrid items={[
              ["Posts Pending",   dash.moderation?.posts_pending,   dash.moderation?.posts_pending > 0 ? WARN : OK],
              ["Needs Pending",   dash.moderation?.needs_pending,   dash.moderation?.needs_pending > 0 ? WARN : OK],
              ["Flags Pending",   dash.moderation?.flags_pending,   dash.moderation?.flags_pending > 0 ? ERR  : OK],
              ["Appeals Pending", dash.moderation?.appeals_pending, dash.moderation?.appeals_pending > 0 ? WARN : OK],
            ]} />
          </div>
          <div style={card}>
            <div style={{ color:MUTED, fontSize:10, textTransform:"uppercase", letterSpacing:1, marginBottom:10 }}>Platform</div>
            <InfoGrid items={[
              ["Open Incidents", dash.incidents?.open, dash.incidents?.open > 0 ? ERR : OK],
              ["Total Users",    dash.users?.total],
              ["Active Users",   dash.users?.active],
            ]} />
          </div>
        </>
      )}

      <div style={card}>
        <SectionLabel>System Continuity Check</SectionLabel>
        <button onClick={runContinuityCheck} disabled={runningCheck} style={btn(SIG)}>
          {runningCheck ? "Running…" : "Run Full Check"}
        </button>
        {check && (
          <div style={{ marginTop:14 }}>
            <div style={{ marginBottom:8 }}>
              <StatusDot v={check.all_ok ? "ok" : "error"} />
              <span style={{ color:check.all_ok ? OK : ERR, fontWeight:700, fontSize:12 }}>
                {check.all_ok ? "All systems operational" : "Issues detected"}
              </span>
              <span style={{ color:MUTED, fontSize:10, marginLeft:10 }}>{check.checked_at ? new Date(check.checked_at).toLocaleString() : ""}</span>
            </div>
            {check.checks && Object.entries(check.checks).map(([k, v]) => (
              <div key={k} style={{ display:"flex", alignItems:"center", gap:8, padding:"5px 0", borderBottom:`1px solid ${BORDER}` }}>
                <StatusDot v={v.status} />
                <span style={{ color:WHITE, fontSize:11, fontWeight:600, width:160 }}>{k.replace(/_/g," ")}</span>
                <span style={{ color:MUTED, fontSize:10 }}>
                  {Object.entries(v).filter(([kk]) => kk !== "status").map(([kk,vv]) => `${kk}: ${vv}`).join(" · ")}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      <div style={{ ...card, display:"flex", gap:10, flexWrap:"wrap" }}>
        <SectionLabel>Quick Nav</SectionLabel>
        {[
          ["/admin/users","User Management (Admin Panel)"],
          ["/more-help-center","Public Help Center"],
          ["/more","M.O.R.E. Hub"],
        ].map(([to, label]) => (
          <Link key={to} to={to} style={{ ...btn(AMBER), color:"#1a1a2e", background:AMBER, border:"none", textDecoration:"none", display:"inline-block" }}>
            {label}
          </Link>
        ))}
      </div>
    </div>
  );
}

// ── Tab: Moderation ───────────────────────────────────────────────────────────
// Routes: GET /more/admin/queue, GET /more/admin/flags, GET /more/admin/moderation-stats
//         POST /supervisor/content/{type}/{id}/approve
//         POST /supervisor/content/{type}/{id}/reject
function ModerationTab({ notify }) {
  const [queue,  setQueue]  = useState(null);
  const [flags,  setFlags]  = useState([]);
  const [stats,  setStats]  = useState(null);
  const [view,   setView]   = useState("posts");
  const [rejectReason, setRejectReason] = useState({});

  const load = useCallback(async () => {
    try { const r = await api.get("/more/admin/queue"); setQueue(r.data); } catch {}
    try { const r = await api.get("/more/admin/flags"); setFlags(r.data.flags || []); } catch {}
    try { const r = await api.get("/more/admin/moderation-stats"); setStats(r.data); } catch {}
  }, []);

  useEffect(() => { load(); }, [load]);

  async function approve(type, id) {
    try {
      await api.post(`/supervisor/content/${type}/${id}/approve`);
      notify(`${type} approved`);
      load();
    } catch (e) { notify(e?.response?.data?.detail || "Approve failed", true); }
  }

  async function reject(type, id) {
    const reason = rejectReason[id] || "";
    try {
      await api.post(`/supervisor/content/${type}/${id}/reject`, { reason });
      notify(`${type} rejected`);
      setRejectReason(prev => { const n={...prev}; delete n[id]; return n; });
      load();
    } catch (e) { notify(e?.response?.data?.detail || "Reject failed", true); }
  }

  const items = view === "posts" ? (queue?.posts || []) :
                view === "needs" ? (queue?.needs || []) :
                view === "appeals" ? (queue?.appeals || []) : flags;

  return (
    <div>
      <SectionLabel>Content Moderation</SectionLabel>

      {stats && (
        <div style={card}>
          <InfoGrid items={[
            ["Total Moderated", stats.total_moderated],
            ["Approved", stats.approved, OK],
            ["Blocked",  stats.blocked,  ERR],
            ["Warned",   stats.warned,   WARN],
            ["Flagged",  stats.flagged,  WARN],
            ["Pending",  stats.pending_count, stats.pending_count > 0 ? WARN : MUTED],
          ]} />
        </div>
      )}

      <div style={{ display:"flex", gap:6, marginBottom:14, flexWrap:"wrap" }}>
        {[
          ["posts",   `Posts (${queue?.posts_total ?? 0})`],
          ["needs",   `Needs (${queue?.needs_total ?? 0})`],
          ["appeals", `Appeals (${queue?.appeals_total ?? 0})`],
          ["flags",   `Flags (${flags.length})`],
        ].map(([k,l]) => (
          <button key={k} onClick={() => setView(k)} style={chip(view===k)}>{l}</button>
        ))}
      </div>

      {items.length === 0 ? (
        <div style={{ ...card, color:MUTED, fontSize:12, textAlign:"center" }}>Queue empty for this category.</div>
      ) : items.map(item => (
        <div key={item.id || item._id} style={{ ...card, borderLeft:`3px solid ${view==="flags"?ERR:WARN}` }}>
          <div style={{ display:"flex", justifyContent:"space-between", alignItems:"flex-start", gap:10 }}>
            <div style={{ flex:1 }}>
              <div style={{ color:WHITE, fontWeight:700, fontSize:12, marginBottom:4 }}>
                {item.title || item.content_type || item.reason || item.type || "(no title)"}
              </div>
              <div style={{ color:MUTED, fontSize:11, marginBottom:4, lineHeight:1.5 }}>
                {(item.content || item.description || item.body || "").slice(0,200)}
              </div>
              <div style={{ color:MUTED, fontSize:10 }}>
                {item.created_at ? new Date(item.created_at).toLocaleString() : ""}
                {item.author_id && <span style={{ marginLeft:8 }}>by {item.author_id}</span>}
                {item.flagged_by && <span style={{ marginLeft:8 }}>flagged by {item.flagged_by}</span>}
              </div>
            </div>
            <div style={{ display:"flex", flexDirection:"column", gap:6, flexShrink:0 }}>
              {view !== "flags" && (
                <button onClick={() => approve(view==="appeals"?"appeal":view.replace(/s$/,""), item.id)}
                  style={btn(OK)}>Approve</button>
              )}
              <button onClick={() => reject(
                view==="flags"?"flag":view==="appeals"?"appeal":view.replace(/s$/,""),
                item.id
              )} style={btn(ERR)}>Reject</button>
            </div>
          </div>
          <div style={{ marginTop:8 }}>
            <input
              value={rejectReason[item.id] || ""}
              onChange={e => setRejectReason(prev => ({...prev, [item.id]: e.target.value}))}
              placeholder="Rejection reason (optional)…"
              style={{ ...inp, fontSize:11 }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}

// ── Tab: Escalations ──────────────────────────────────────────────────────────
// Routes: GET /supervisor/escalations
//         POST /supervisor/escalations
//         POST /supervisor/escalations/{id}/resolve
function EscalationsTab({ notify }) {
  const [escalations, setEscalations] = useState([]);
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState({ title:"", description:"", severity:"medium", target_id:"", target_type:"user" });
  const [resolveForm, setResolveForm] = useState({});

  const load = useCallback(async () => {
    try { const r = await api.get("/supervisor/escalations"); setEscalations(r.data.escalations || []); } catch {}
  }, []);

  useEffect(() => { load(); }, [load]);

  async function createEscalation() {
    try {
      await api.post("/supervisor/escalations", form);
      notify("Escalation created");
      setCreating(false);
      setForm({ title:"", description:"", severity:"medium", target_id:"", target_type:"user" });
      load();
    } catch (e) { notify(e?.response?.data?.detail || "Create failed", true); }
  }

  async function resolveEscalation(id) {
    const rf = resolveForm[id] || {};
    try {
      await api.post(`/supervisor/escalations/${id}/resolve`, {
        decision: rf.decision || "resolved",
        note: rf.note || "",
      });
      notify("Escalation resolved");
      setResolveForm(prev => { const n={...prev}; delete n[id]; return n; });
      load();
    } catch (e) { notify(e?.response?.data?.detail || "Resolve failed", true); }
  }

  const SEVERITY_COLOR = { low: MUTED, medium: WARN, high: ERR, critical: "#dc2626" };

  return (
    <div>
      <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:14 }}>
        <SectionLabel>Escalation Management</SectionLabel>
        <button onClick={() => setCreating(c => !c)} style={btn(SIG)}>
          {creating ? "Cancel" : "+ New Escalation"}
        </button>
      </div>

      {creating && (
        <div style={{ ...card, borderColor:`${SIG}44` }}>
          <SectionLabel>Create Escalation</SectionLabel>
          <div style={{ display:"grid", gap:10 }}>
            <div>
              <span style={label}>Title</span>
              <input value={form.title} onChange={e => setForm(p=>({...p,title:e.target.value}))} style={inp} placeholder="Escalation title" />
            </div>
            <div>
              <span style={label}>Description</span>
              <textarea value={form.description} onChange={e => setForm(p=>({...p,description:e.target.value}))}
                rows={3} style={{ ...inp, resize:"vertical" }} placeholder="What is the issue?" />
            </div>
            <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr 1fr", gap:10 }}>
              <div>
                <span style={label}>Severity</span>
                <select value={form.severity} onChange={e => setForm(p=>({...p,severity:e.target.value}))}
                  style={{ ...inp, background:"rgba(0,0,0,0.4)" }}>
                  {["low","medium","high","critical"].map(s => <option key={s} value={s}>{s}</option>)}
                </select>
              </div>
              <div>
                <span style={label}>Target Type</span>
                <select value={form.target_type} onChange={e => setForm(p=>({...p,target_type:e.target.value}))}
                  style={{ ...inp, background:"rgba(0,0,0,0.4)" }}>
                  {["user","content","system","gateway"].map(t => <option key={t} value={t}>{t}</option>)}
                </select>
              </div>
              <div>
                <span style={label}>Target ID (optional)</span>
                <input value={form.target_id} onChange={e => setForm(p=>({...p,target_id:e.target.value}))} style={inp} placeholder="ID…" />
              </div>
            </div>
            <button onClick={createEscalation} style={{ ...btn(SIG), alignSelf:"flex-start" }}>Create Escalation</button>
          </div>
        </div>
      )}

      {escalations.length === 0 ? (
        <div style={{ ...card, color:MUTED, fontSize:12, textAlign:"center" }}>No open escalations.</div>
      ) : escalations.map(esc => {
        const rf = resolveForm[esc.id] || {};
        return (
          <div key={esc.id} style={{ ...card, borderLeft:`3px solid ${SEVERITY_COLOR[esc.severity]||MUTED}` }}>
            <div style={{ display:"flex", justifyContent:"space-between", gap:10 }}>
              <div style={{ flex:1 }}>
                <div style={{ color:WHITE, fontWeight:700, fontSize:12, marginBottom:2 }}>{esc.title}</div>
                <div style={{ color:MUTED, fontSize:11, marginBottom:6 }}>{esc.description}</div>
                <div style={{ display:"flex", gap:8, flexWrap:"wrap" }}>
                  <span style={{ fontSize:10, color:SEVERITY_COLOR[esc.severity]||MUTED }}>{esc.severity?.toUpperCase()}</span>
                  <span style={{ fontSize:10, color:MUTED }}>{esc.target_type}: {esc.target_id || "—"}</span>
                  <span style={{ fontSize:10, color:MUTED }}>{esc.created_at ? new Date(esc.created_at).toLocaleString() : ""}</span>
                </div>
              </div>
              <div style={{ display:"flex", flexDirection:"column", gap:6, flexShrink:0 }}>
                <select value={rf.decision||"resolved"} onChange={e => setResolveForm(p=>({...p,[esc.id]:{...rf,decision:e.target.value}}))}
                  style={{ ...inp, width:130, background:"rgba(0,0,0,0.4)", fontSize:11 }}>
                  {["resolved","dismissed","escalated_to_exec","monitoring"].map(d=><option key={d} value={d}>{d.replace(/_/g," ")}</option>)}
                </select>
                <input value={rf.note||""} onChange={e => setResolveForm(p=>({...p,[esc.id]:{...rf,note:e.target.value}}))}
                  placeholder="Resolution note…" style={{ ...inp, fontSize:11 }} />
                <button onClick={() => resolveEscalation(esc.id)} style={btn(OK)}>Resolve</button>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ── Tab: Greeter / Visitor Flow ───────────────────────────────────────────────
// Routes: GET /supervisor/greeter/config, PATCH /supervisor/greeter/config
//         GET /supervisor/visitor-flow, PATCH /supervisor/visitor-flow
function GreeterTab({ notify }) {
  const [greeterCfg, setGreeterCfg] = useState(null);
  const [flowCfg,    setFlowCfg]    = useState(null);
  const [saving,     setSaving]     = useState(false);

  const load = useCallback(async () => {
    try { const r = await api.get("/supervisor/greeter/config"); setGreeterCfg(r.data.config); } catch {}
    try { const r = await api.get("/supervisor/visitor-flow");   setFlowCfg(r.data.flow);     } catch {}
  }, []);

  useEffect(() => { load(); }, [load]);

  async function saveGreeter() {
    setSaving(true);
    try {
      await api.patch("/supervisor/greeter/config", { config: greeterCfg });
      notify("Greeter config saved");
    } catch (e) { notify(e?.response?.data?.detail || "Save failed", true); }
    finally { setSaving(false); }
  }

  async function saveFlow() {
    setSaving(true);
    try {
      await api.patch("/supervisor/visitor-flow", { flow: flowCfg });
      notify("Visitor flow saved");
    } catch (e) { notify(e?.response?.data?.detail || e.message, true); }
    finally { setSaving(false); }
  }

  if (!greeterCfg || !flowCfg) return <div style={{ color:MUTED, fontSize:12 }}>Loading config…</div>;

  return (
    <div>
      <div style={card}>
        <SectionLabel>Greeter Persona Config</SectionLabel>
        <div style={{ display:"grid", gap:10 }}>
          <div>
            <span style={label}>Greeter Name</span>
            <input value={greeterCfg.greeter_name||""} onChange={e => setGreeterCfg(p=>({...p,greeter_name:e.target.value}))} style={inp} />
          </div>
          <div>
            <span style={label}>Welcome Message</span>
            <textarea value={greeterCfg.welcome_message||""} onChange={e => setGreeterCfg(p=>({...p,welcome_message:e.target.value}))}
              rows={3} style={{ ...inp, resize:"vertical" }} />
          </div>
          <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:10 }}>
            <div>
              <span style={label}>Greeter Mode</span>
              <select value={greeterCfg.mode||"greeter"} onChange={e => setGreeterCfg(p=>({...p,mode:e.target.value}))}
                style={{ ...inp, background:"rgba(0,0,0,0.4)" }}>
                {["greeter","exec","decoy"].map(m => <option key={m} value={m}>{m}</option>)}
              </select>
            </div>
            <div>
              <span style={label}>Route Unauthenticated To</span>
              <input value={greeterCfg.route_unauthenticated_to||""} onChange={e => setGreeterCfg(p=>({...p,route_unauthenticated_to:e.target.value}))} style={inp} />
            </div>
          </div>
          <div style={{ display:"flex", gap:16, flexWrap:"wrap" }}>
            {[["show_help_link","Show Help Link"],["show_community_link","Show Community Link"]].map(([k,lbl])=>(
              <label key={k} style={{ display:"flex", alignItems:"center", gap:6, cursor:"pointer", fontSize:12, color:WHITE }}>
                <input type="checkbox" checked={!!greeterCfg[k]} onChange={e => setGreeterCfg(p=>({...p,[k]:e.target.checked}))} />
                {lbl}
              </label>
            ))}
          </div>
          <button onClick={saveGreeter} disabled={saving} style={{ ...btn(SIG), alignSelf:"flex-start" }}>
            {saving ? "Saving…" : "Save Greeter Config"}
          </button>
        </div>
      </div>

      <div style={card}>
        <SectionLabel>Visitor Flow Config</SectionLabel>
        <div style={{ display:"grid", gap:10 }}>
          <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr 1fr", gap:10 }}>
            <div>
              <span style={label}>Public Landing Path</span>
              <input value={flowCfg.public_landing||""} onChange={e => setFlowCfg(p=>({...p,public_landing:e.target.value}))} style={inp} />
            </div>
            <div>
              <span style={label}>Authenticated Landing</span>
              <input value={flowCfg.auth_landing||""} onChange={e => setFlowCfg(p=>({...p,auth_landing:e.target.value}))} style={inp} />
            </div>
            <div>
              <span style={label}>Fallback Path</span>
              <input value={flowCfg.fallback_path||""} onChange={e => setFlowCfg(p=>({...p,fallback_path:e.target.value}))} style={inp} />
            </div>
          </div>
          <div style={{ display:"flex", gap:16, flexWrap:"wrap" }}>
            {[["login_optional","Login Is Optional"],["show_supervisor_widget","Show Supervisor Widget"]].map(([k,lbl])=>(
              <label key={k} style={{ display:"flex", alignItems:"center", gap:6, cursor:"pointer", fontSize:12, color:WHITE }}>
                <input type="checkbox" checked={!!flowCfg[k]} onChange={e => setFlowCfg(p=>({...p,[k]:e.target.checked}))} />
                {lbl}
              </label>
            ))}
            <div style={{ display:"flex", alignItems:"center", gap:6, fontSize:12 }}>
              <span style={{ color: ERR, fontWeight:700 }}>Auto-Redirect to Login:</span>
              <span style={{ color:MUTED }}>Locked OFF (governance rule)</span>
            </div>
          </div>
          <button onClick={saveFlow} disabled={saving} style={{ ...btn(SIG), alignSelf:"flex-start" }}>
            {saving ? "Saving…" : "Save Visitor Flow"}
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Tab: Sage Sessions ────────────────────────────────────────────────────────
// Routes: GET /supervisor/sage/sessions
//         POST /supervisor/sage/sessions/{id}/flag
//         GET /admin/sage/cap, GET /admin/sage/status
function SageTab({ notify }) {
  const [sessions,  setSessions]  = useState([]);
  const [cap,       setCap]       = useState(null);
  const [status,    setSageStatus] = useState(null);
  const [uidFilter, setUidFilter] = useState("");
  const [flagForms, setFlagForms] = useState({});
  const [limit,     setLimit]     = useState(50);

  const load = useCallback(async () => {
    const params = new URLSearchParams({ limit: String(limit) });
    if (uidFilter.trim()) params.set("user_id", uidFilter.trim());
    try { const r = await api.get(`/supervisor/sage/sessions?${params}`); setSessions(r.data.sessions || []); } catch {}
    try { const r = await api.get("/admin/sage/cap");    setCap(r.data);        } catch {}
    try { const r = await api.get("/admin/sage/status"); setSageStatus(r.data); } catch {}
  }, [uidFilter, limit]);

  useEffect(() => { load(); }, [load]);

  async function flagSession(id) {
    const reason = flagForms[id] || "";
    try {
      await api.post(`/supervisor/sage/sessions/${id}/flag`, { reason });
      notify("Session flagged for exec review");
      setFlagForms(prev => { const n={...prev}; delete n[id]; return n; });
      load();
    } catch (e) { notify(e?.response?.data?.detail || "Flag failed", true); }
  }

  return (
    <div>
      {status && (
        <div style={card}>
          <SectionLabel>Sage Integrity</SectionLabel>
          <div style={{ display:"flex", gap:8, flexWrap:"wrap" }}>
            <div style={{ background:"rgba(255,255,255,0.04)", borderRadius:6, padding:"6px 12px" }}>
              <div style={{ color:MUTED, fontSize:9, textTransform:"uppercase" }}>Prompt Hash</div>
              <div style={{ color: status.prompt_hash_status==="match" ? OK : ERR, fontWeight:700, fontSize:12, marginTop:2 }}>
                {status.prompt_hash_status==="match" ? "✓ Match" : "✗ " + status.prompt_hash_status}
              </div>
            </div>
            <div style={{ background:"rgba(255,255,255,0.04)", borderRadius:6, padding:"6px 12px" }}>
              <div style={{ color:MUTED, fontSize:9, textTransform:"uppercase" }}>Fallback</div>
              <div style={{ color: status.fallback_active ? ERR : OK, fontWeight:700, fontSize:12, marginTop:2 }}>
                {status.fallback_active ? "Active" : "Off"}
              </div>
            </div>
            {status.modules && Object.entries(status.modules).map(([mod, st]) => (
              <div key={mod} style={{ background:"rgba(255,255,255,0.04)", borderRadius:6, padding:"6px 12px" }}>
                <div style={{ color:MUTED, fontSize:9, textTransform:"uppercase" }}>Module {mod}</div>
                <div style={{ color: st==="present" ? OK : ERR, fontWeight:700, fontSize:12, marginTop:2 }}>{st}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {cap && (
        <div style={card}>
          <SectionLabel>Safety Cap Status</SectionLabel>
          <InfoGrid items={[
            ["Global Cap", cap.global_cap],
            ["Tokens Used (hour)", cap.tokens_used],
            ["Cap %", cap.tokens_used && cap.global_cap ? Math.round(cap.tokens_used/cap.global_cap*100)+"%" : "—",
             cap.tokens_used/cap.global_cap > 0.8 ? ERR : OK],
          ]} />
        </div>
      )}

      <div style={card}>
        <SectionLabel>Sage Session Review</SectionLabel>
        <div style={{ display:"flex", gap:8, marginBottom:12, flexWrap:"wrap" }}>
          <input value={uidFilter} onChange={e => setUidFilter(e.target.value)} placeholder="Filter by user ID…"
            style={{ ...inp, width:220 }} />
          <select value={limit} onChange={e => setLimit(Number(e.target.value))}
            style={{ ...inp, width:100, background:"rgba(0,0,0,0.4)" }}>
            {[25,50,100,200].map(n => <option key={n} value={n}>{n}</option>)}
          </select>
          <button onClick={load} style={btn(SIG)}>Refresh</button>
        </div>

        {sessions.length === 0 ? (
          <div style={{ color:MUTED, fontSize:12 }}>No sessions found.</div>
        ) : sessions.map(s => (
          <div key={s.id || s._id} style={{ ...card, marginBottom:8, borderLeft: s.flagged ? `3px solid ${ERR}` : `3px solid ${BORDER}` }}>
            <div style={{ display:"flex", justifyContent:"space-between", gap:10 }}>
              <div>
                <div style={{ color:WHITE, fontSize:11, fontWeight:600 }}>{s.id || s._id}</div>
                <div style={{ color:MUTED, fontSize:10, marginTop:2 }}>
                  User: {s.user_id || "—"} · {s.created_at ? new Date(s.created_at).toLocaleString() : ""}
                  {s.flagged && <span style={{ color:ERR, marginLeft:8 }}>⚑ Flagged: {s.flag_reason || ""}</span>}
                </div>
                {s.message_count != null && <div style={{ color:MUTED, fontSize:10 }}>Messages: {s.message_count}</div>}
              </div>
              {!s.flagged && (
                <div style={{ display:"flex", flexDirection:"column", gap:4, flexShrink:0 }}>
                  <input value={flagForms[s.id]||""} onChange={e => setFlagForms(p=>({...p,[s.id]:e.target.value}))}
                    placeholder="Flag reason…" style={{ ...inp, fontSize:10, width:160 }} />
                  <button onClick={() => flagSession(s.id)} style={{ ...btn(WARN), fontSize:10 }}>⚑ Flag for Exec</button>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Tab: Backup System ────────────────────────────────────────────────────────
// Routes: GET  /supervisor/backup/status
//         POST /supervisor/backup/switch-provider
//         POST /supervisor/backup/reset-gateway
//         GET  /supervisor/backup/free-matrix
//         POST /supervisor/backup/emergency-broadcast
//         GET  /exec/panel, POST /exec/panel/toggle, POST /exec/panel/reset
//         POST /exec/failover
function BackupTab({ notify }) {
  const [status,    setStatus]   = useState(null);
  const [matrix,    setMatrix]   = useState(null);
  const [panel,     setPanel]    = useState(null);
  const [broadcast, setBroadcast] = useState({ title:"", message:"", target:"all" });
  const [switching, setSwitching] = useState("");
  const [confirmReset,     setConfirmReset]     = useState(false);
  const [confirmFailover,  setConfirmFailover]  = useState(null); // target string
  const [confirmBroadcast, setConfirmBroadcast] = useState(false);

  const load = useCallback(async () => {
    try { const r = await api.get("/supervisor/backup/status");     setStatus(r.data); } catch {}
    try { const r = await api.get("/supervisor/backup/free-matrix"); setMatrix(r.data); } catch {}
    try { const r = await api.get("/exec/panel");                   setPanel(r.data);  } catch {}
  }, []);

  useEffect(() => { load(); }, [load]);

  async function switchProvider(provider) {
    setSwitching(provider);
    try {
      await api.post("/supervisor/backup/switch-provider", { provider });
      notify(`${provider} promoted to primary`);
      load();
    } catch (e) { notify(e?.response?.data?.detail || "Switch failed", true); }
    finally { setSwitching(""); }
  }

  async function resetGateway() {
    try {
      const r = await api.post("/supervisor/backup/reset-gateway");
      notify(`Gateway reset. Previous: ${r.data.previous_tokens_used} tokens`);
      load();
    } catch (e) { notify(e?.response?.data?.detail || "Reset failed", true); }
    finally { setConfirmReset(false); }
  }

  async function toggleBreaker(breakerId) {
    try {
      await api.post("/exec/panel/toggle", { breaker_id: breakerId });
      notify(`Breaker ${breakerId} toggled`);
      load();
    } catch (e) { notify(e?.response?.data?.detail || "Toggle failed", true); }
  }

  async function resetBreaker(breakerId) {
    try {
      await api.post("/exec/panel/reset", { breaker_id: breakerId });
      notify(`Breaker ${breakerId} reset`);
      load();
    } catch (e) { notify(e?.response?.data?.detail || "Reset failed", true); }
  }

  async function triggerFailover() {
    if (!confirmFailover) return;
    try {
      await api.post("/exec/failover", { target: confirmFailover });
      notify("Failover triggered");
      load();
    } catch (e) { notify(e?.response?.data?.detail || "Failover failed", true); }
    finally { setConfirmFailover(null); }
  }

  async function sendBroadcast() {
    if (!broadcast.message.trim()) { notify("Message is required", true); return; }
    try {
      await api.post("/supervisor/backup/emergency-broadcast", broadcast);
      notify("Emergency broadcast sent");
      setBroadcast({ title:"", message:"", target:"all" });
    } catch (e) { notify(e?.response?.data?.detail || "Broadcast failed", true); }
    finally { setConfirmBroadcast(false); }
  }

  return (
    <div>
      <SectionLabel>Backup System Control Panel</SectionLabel>

      {/* Gateway Status */}
      {status && (
        <div style={card}>
          <div style={{ color:MUTED, fontSize:10, textTransform:"uppercase", letterSpacing:1, marginBottom:10 }}>Gateway + Database</div>
          <InfoGrid items={[
            ["Database", status.database, status.database==="connected" ? OK : ERR],
            ["Tokens Used", status.gateway?.tokens_used],
            ["Hour Cap",    status.gateway?.cap],
            ["Usage %",     status.gateway?.percent != null ? status.gateway.percent+"%" : "—",
             (status.gateway?.percent||0) > 80 ? ERR : OK],
          ]} />
          <div style={{ marginTop:12, display:"flex", gap:8, flexWrap:"wrap" }}>
            <button onClick={() => setConfirmReset(true)} style={btn(WARN)}>Reset Gateway Counter</button>
            <button onClick={() => setConfirmFailover("backup")} style={btn(ERR)}>Trigger Failover</button>
          </div>
        </div>
      )}

      {/* Provider Ranking + Switching */}
      <div style={card}>
        <div style={{ color:MUTED, fontSize:10, textTransform:"uppercase", letterSpacing:1, marginBottom:10 }}>Provider Ranking (Backup Override)</div>
        <div style={{ marginBottom:10, color:WHITE, fontSize:11 }}>
          Current: {status?.provider_ranking?.join(" → ") || "Loading…"}
        </div>
        <div style={{ display:"flex", gap:6, flexWrap:"wrap" }}>
          {PROVIDERS.map(p => (
            <button key={p} onClick={() => switchProvider(p)} disabled={switching===p}
              style={{ ...btn(SIG), opacity: switching===p ? 0.5 : 1 }}>
              {switching===p ? "Switching…" : `▲ ${p}`}
            </button>
          ))}
        </div>
        <div style={{ color:MUTED, fontSize:10, marginTop:8 }}>
          Clicking a provider promotes it to position 1 in the fallback chain. The gateway will use it first on the next call.
        </div>
      </div>

      {/* Free Backup Matrix */}
      {matrix && (
        <div style={card}>
          <div style={{ color:MUTED, fontSize:10, textTransform:"uppercase", letterSpacing:1, marginBottom:10 }}>Free Backup Matrix</div>
          {matrix.error ? (
            <div style={{ color:ERR, fontSize:11 }}>{matrix.error}</div>
          ) : (
            <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fit,minmax(140px,1fr))", gap:8 }}>
              {Object.entries(matrix).filter(([k]) => k !== "error" && k !== "note").map(([k,v]) => (
                <div key={k} style={{ background:"rgba(255,255,255,0.04)", borderRadius:6, padding:"7px 12px" }}>
                  <div style={{ color:MUTED, fontSize:9, textTransform:"uppercase" }}>{k.replace(/_/g," ")}</div>
                  <div style={{ color: v === true || v === "ok" ? OK : v === false ? ERR : WHITE, fontWeight:700, fontSize:12, marginTop:2 }}>
                    {typeof v === "object" ? JSON.stringify(v).slice(0,40) : String(v)}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Breaker Panel */}
      {panel && (
        <div style={card}>
          <div style={{ color:MUTED, fontSize:10, textTransform:"uppercase", letterSpacing:1, marginBottom:10 }}>Circuit Breaker Panel</div>
          {Array.isArray(panel) ? panel.map(b => (
            <div key={b.id} style={{ display:"flex", alignItems:"center", gap:10, padding:"7px 0", borderBottom:`1px solid ${BORDER}` }}>
              <StatusDot v={b.state==="closed" ? "ok" : b.state==="tripped" ? "error" : "warn"} />
              <span style={{ color:WHITE, fontSize:11, fontWeight:600, flex:1 }}>{b.id} <span style={{ color:MUTED, fontWeight:400 }}>({b.state})</span></span>
              <button onClick={() => toggleBreaker(b.id)} style={{ ...btn(WARN), fontSize:10 }}>Toggle</button>
              {b.state==="tripped" && <button onClick={() => resetBreaker(b.id)} style={{ ...btn(OK), fontSize:10 }}>Reset</button>}
            </div>
          )) : (
            <div style={{ color:MUTED, fontSize:11 }}>
              {typeof panel === "object" ? JSON.stringify(panel, null, 2).slice(0,300) : String(panel)}
            </div>
          )}
        </div>
      )}

      {/* Emergency Broadcast */}
      <div style={card}>
        <SectionLabel>Emergency Broadcast</SectionLabel>
        <div style={{ display:"grid", gap:10 }}>
          <div>
            <span style={label}>Title</span>
            <input value={broadcast.title} onChange={e => setBroadcast(p=>({...p,title:e.target.value}))}
              style={inp} placeholder="System notice title…" />
          </div>
          <div>
            <span style={label}>Message</span>
            <textarea value={broadcast.message} onChange={e => setBroadcast(p=>({...p,message:e.target.value}))}
              rows={3} style={{ ...inp, resize:"vertical" }} placeholder="Emergency message to users…" />
          </div>
          <div>
            <span style={label}>Target Audience</span>
            <select value={broadcast.target} onChange={e => setBroadcast(p=>({...p,target:e.target.value}))}
              style={{ ...inp, background:"rgba(0,0,0,0.4)", width:200 }}>
              {["all","executive_admin","admin","instructor","student"].map(t=>(
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
          </div>
          <button onClick={() => { if (!broadcast.message.trim()) { notify("Message is required", true); return; } setConfirmBroadcast(true); }}
            style={{ ...btn(ERR), alignSelf:"flex-start", borderColor:ERR }}>
            Send Emergency Broadcast
          </button>
        </div>
      </div>

      <div style={{ textAlign:"right" }}>
        <button onClick={load} style={btn(MUTED)}>↻ Refresh All</button>
      </div>

      {/* Reset gateway confirmation */}
      {confirmReset && (
        <div style={{ position:"fixed", inset:0, zIndex:1000, display:"flex", alignItems:"center", justifyContent:"center", background:"rgba(0,0,0,0.7)", padding:16 }}>
          <div style={{ background:PANEL, border:`1px solid ${BORDER}`, borderRadius:12, padding:28, maxWidth:360, width:"100%" }}>
            <div style={{ color:WHITE, fontWeight:700, fontSize:15, marginBottom:10 }}>Reset Gateway Counter?</div>
            <div style={{ color:MUTED, fontSize:12, marginBottom:20 }}>This clears the current hour token window. The hourly cap resets immediately.</div>
            <div style={{ display:"flex", justifyContent:"flex-end", gap:10 }}>
              <button onClick={() => setConfirmReset(false)} style={btn(MUTED)}>Cancel</button>
              <button onClick={resetGateway} style={btn(WARN)}>Reset</button>
            </div>
          </div>
        </div>
      )}

      {/* Failover confirmation */}
      {confirmFailover && (
        <div style={{ position:"fixed", inset:0, zIndex:1000, display:"flex", alignItems:"center", justifyContent:"center", background:"rgba(0,0,0,0.7)", padding:16 }}>
          <div style={{ background:PANEL, border:`1px solid ${BORDER}`, borderRadius:12, padding:28, maxWidth:360, width:"100%" }}>
            <div style={{ color:ERR, fontWeight:700, fontSize:15, marginBottom:10 }}>Trigger Failover?</div>
            <div style={{ color:MUTED, fontSize:12, marginBottom:20 }}>Trigger failover to <strong style={{ color:WHITE }}>{confirmFailover}</strong>? This immediately switches active systems.</div>
            <div style={{ display:"flex", justifyContent:"flex-end", gap:10 }}>
              <button onClick={() => setConfirmFailover(null)} style={btn(MUTED)}>Cancel</button>
              <button onClick={triggerFailover} style={btn(ERR)}>Confirm Failover</button>
            </div>
          </div>
        </div>
      )}

      {/* Emergency broadcast confirmation */}
      {confirmBroadcast && (
        <div style={{ position:"fixed", inset:0, zIndex:1000, display:"flex", alignItems:"center", justifyContent:"center", background:"rgba(0,0,0,0.7)", padding:16 }}>
          <div style={{ background:PANEL, border:`1px solid ${BORDER}`, borderRadius:12, padding:28, maxWidth:360, width:"100%" }}>
            <div style={{ color:ERR, fontWeight:700, fontSize:15, marginBottom:10 }}>Send Emergency Broadcast?</div>
            <div style={{ color:MUTED, fontSize:12, marginBottom:8 }}>Send to: <strong style={{ color:WHITE }}>{broadcast.target}</strong></div>
            <div style={{ color:WHITE, fontSize:12, background:"rgba(255,255,255,0.05)", borderRadius:6, padding:"8px 12px", marginBottom:20 }}>
              {broadcast.title && <div style={{ fontWeight:700, marginBottom:4 }}>{broadcast.title}</div>}
              <div>{broadcast.message}</div>
            </div>
            <div style={{ display:"flex", justifyContent:"flex-end", gap:10 }}>
              <button onClick={() => setConfirmBroadcast(false)} style={btn(MUTED)}>Cancel</button>
              <button onClick={sendBroadcast} style={btn(ERR)}>Send Broadcast</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Tab: RBAC ─────────────────────────────────────────────────────────────────
// Routes: GET/PATCH /admin/rbac/matrix
//         GET/PATCH /admin/mfa/config
//         GET /admin/access/ipwhitelist
//         POST /admin/access/ipwhitelist
//         DELETE /admin/access/ipwhitelist/{id}
function RbacTab({ notify }) {
  const [matrix,     setMatrix]    = useState(null);
  const [mfa,        setMfa]       = useState(null);
  const [ipList,     setIpList]    = useState([]);
  const [newIp,      setNewIp]     = useState({ ip:"", role:"executive_admin", note:"" });
  const [saving,     setSaving]    = useState(false);

  const load = useCallback(async () => {
    try { const r = await api.get("/admin/rbac/matrix");       setMatrix(r.data.matrix); } catch {}
    try { const r = await api.get("/admin/mfa/config");        setMfa(r.data.mfa);       } catch {}
    try { const r = await api.get("/admin/access/ipwhitelist"); setIpList(r.data.entries || []); } catch {}
  }, []);

  useEffect(() => { load(); }, [load]);

  async function saveMatrix() {
    setSaving(true);
    try {
      await api.patch("/admin/rbac/matrix", { matrix });
      notify("Permission matrix saved");
    } catch (e) { notify(e?.response?.data?.detail || "Save failed", true); }
    finally { setSaving(false); }
  }

  async function saveMfa() {
    setSaving(true);
    try {
      await api.patch("/admin/mfa/config", { mfa });
      notify("MFA config saved");
    } catch (e) { notify(e?.response?.data?.detail || "Save failed", true); }
    finally { setSaving(false); }
  }

  async function addIp() {
    if (!newIp.ip.trim()) { notify("IP is required", true); return; }
    try {
      const r = await api.post("/admin/access/ipwhitelist", newIp);
      setIpList(prev => [r.data, ...prev]);
      setNewIp({ ip:"", role:"executive_admin", note:"" });
      notify("IP added");
    } catch (e) { notify(e?.response?.data?.detail || "Add failed", true); }
  }

  async function removeIp(id) {
    try {
      await api.delete(`/admin/access/ipwhitelist/${id}`);
      setIpList(prev => prev.filter(e => e.id !== id));
      notify("IP removed");
    } catch (e) { notify(e?.response?.data?.detail || "Remove failed", true); }
  }

  const togglePerm = (role, perm) => {
    setMatrix(prev => ({ ...prev, [role]: { ...prev[role], [perm]: !prev[role]?.[perm] } }));
  };

  return (
    <div>
      {/* Permission Matrix */}
      <div style={card}>
        <SectionLabel>Permission Matrix</SectionLabel>
        <div style={{ overflowX:"auto" }}>
          <table style={{ width:"100%", borderCollapse:"collapse", fontSize:11 }}>
            <thead>
              <tr>
                <th style={{ color:MUTED, textAlign:"left", padding:"6px 8px", fontSize:9, textTransform:"uppercase" }}>Permission</th>
                {matrix && ALL_ROLES.map(r => (
                  <th key={r} style={{ color:SIG, textAlign:"center", padding:"6px 8px", fontSize:9, textTransform:"uppercase", whiteSpace:"nowrap" }}>
                    {ROLE_LABEL[r]}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {matrix && PERM_KEYS.map(perm => (
                <tr key={perm} style={{ borderTop:`1px solid ${BORDER}` }}>
                  <td style={{ color:WHITE, padding:"6px 8px", fontFamily:"monospace", fontSize:10 }}>{perm.replace(/_/g," ")}</td>
                  {ALL_ROLES.map(role => (
                    <td key={role} style={{ textAlign:"center", padding:"6px 8px" }}>
                      <input type="checkbox" checked={!!matrix[role]?.[perm]}
                        onChange={() => togglePerm(role, perm)} />
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {matrix && (
          <button onClick={saveMatrix} disabled={saving} style={{ ...btn(SIG), marginTop:12 }}>
            {saving ? "Saving…" : "Save Matrix"}
          </button>
        )}
      </div>

      {/* MFA Enforcement */}
      <div style={card}>
        <SectionLabel>MFA Enforcement per Role</SectionLabel>
        {mfa ? (
          <div>
            <div style={{ display:"flex", gap:16, flexWrap:"wrap", marginBottom:12 }}>
              {ALL_ROLES.map(role => (
                <label key={role} style={{ display:"flex", alignItems:"center", gap:6, cursor:"pointer", fontSize:12, color:WHITE }}>
                  <input type="checkbox" checked={!!mfa[role]}
                    onChange={e => setMfa(prev => ({...prev, [role]: e.target.checked}))} />
                  {ROLE_LABEL[role]}
                </label>
              ))}
            </div>
            <button onClick={saveMfa} disabled={saving} style={btn(SIG)}>
              {saving ? "Saving…" : "Save MFA Config"}
            </button>
          </div>
        ) : <div style={{ color:MUTED, fontSize:11 }}>Loading…</div>}
      </div>

      {/* IP Whitelist */}
      <div style={card}>
        <SectionLabel>IP Whitelist (Privileged Roles)</SectionLabel>
        <div style={{ display:"grid", gridTemplateColumns:"1fr 140px 1fr auto", gap:8, marginBottom:12, alignItems:"end" }}>
          <div>
            <span style={label}>IP / CIDR</span>
            <input value={newIp.ip} onChange={e => setNewIp(p=>({...p,ip:e.target.value}))} style={inp} placeholder="192.168.1.0/24" />
          </div>
          <div>
            <span style={label}>Role</span>
            <select value={newIp.role} onChange={e => setNewIp(p=>({...p,role:e.target.value}))}
              style={{ ...inp, background:"rgba(0,0,0,0.4)" }}>
              {ALL_ROLES.map(r => <option key={r} value={r}>{ROLE_LABEL[r]}</option>)}
            </select>
          </div>
          <div>
            <span style={label}>Note</span>
            <input value={newIp.note} onChange={e => setNewIp(p=>({...p,note:e.target.value}))} style={inp} placeholder="Office IP, VPN…" />
          </div>
          <button onClick={addIp} style={{ ...btn(SIG), whiteSpace:"nowrap" }}>Add IP</button>
        </div>
        {ipList.length === 0 ? (
          <div style={{ color:MUTED, fontSize:11 }}>No IP whitelist entries.</div>
        ) : ipList.map(entry => (
          <div key={entry.id} style={{ display:"flex", alignItems:"center", gap:10, padding:"6px 0", borderBottom:`1px solid ${BORDER}` }}>
            <span style={{ color:WHITE, fontFamily:"monospace", fontSize:11, flex:1 }}>{entry.ip}</span>
            <span style={{ ...chip(false), fontSize:9 }}>{ROLE_LABEL[entry.role]||entry.role}</span>
            <span style={{ color:MUTED, fontSize:10, flex:1 }}>{entry.note}</span>
            <button onClick={() => removeIp(entry.id)} style={{ ...btn(ERR), fontSize:10, padding:"2px 8px" }}>✕</button>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Tab: Audit Log ────────────────────────────────────────────────────────────
// Routes: GET /admin/audit, GET /admin/audit/export
function AuditTab({ notify }) {
  const [log,    setLog]    = useState([]);
  const [action, setAction] = useState("");
  const [actor,  setActor]  = useState("");
  const [limit,  setLimit]  = useState(100);

  const load = useCallback(async () => {
    const params = new URLSearchParams({ limit: String(limit) });
    if (action.trim()) params.set("action", action.trim());
    if (actor.trim())  params.set("actor_id", actor.trim());
    try {
      const r = await api.get(`/admin/audit?${params}`);
      setLog(Array.isArray(r.data) ? r.data : []);
    } catch {}
  }, [action, actor, limit]);

  const exportUrl = `/api/admin/audit/export?format=csv&limit=1000${action?`&action=${encodeURIComponent(action)}`:""}${actor?`&actor_id=${encodeURIComponent(actor)}`:""}`;

  return (
    <div>
      <SectionLabel>Audit Log</SectionLabel>
      <div style={{ display:"flex", gap:8, marginBottom:12, flexWrap:"wrap" }}>
        <input value={action} onChange={e => setAction(e.target.value)} placeholder="Filter by action (regex)…"
          style={{ ...inp, flex:1, minWidth:160 }} />
        <input value={actor} onChange={e => setActor(e.target.value)} placeholder="Actor ID…"
          style={{ ...inp, width:180 }} />
        <select value={limit} onChange={e => setLimit(Number(e.target.value))}
          style={{ ...inp, width:100, background:"rgba(0,0,0,0.4)" }}>
          {[50,100,200,500,1000].map(n => <option key={n} value={n}>{n}</option>)}
        </select>
        <button onClick={load} style={btn(SIG)}>Search</button>
        <a href={exportUrl} style={{ ...btn(OK), textDecoration:"none", display:"inline-block" }}>Export CSV</a>
      </div>

      <div style={{ ...card, padding:0, overflow:"hidden" }}>
        <div style={{ maxHeight:540, overflowY:"auto" }}>
          <table style={{ width:"100%", borderCollapse:"collapse", fontSize:11 }}>
            <thead style={{ position:"sticky", top:0, background:PANEL }}>
              <tr style={{ borderBottom:`2px solid ${BORDER}` }}>
                {["Time","Actor","Action","Target","Meta"].map(h => (
                  <th key={h} style={{ textAlign:"left", padding:"8px 12px", color:MUTED, fontSize:9, textTransform:"uppercase", letterSpacing:1 }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {log.length === 0 ? (
                <tr><td colSpan={5} style={{ padding:"24px", textAlign:"center", color:MUTED, fontSize:11 }}>No entries. Click Search to load.</td></tr>
              ) : log.map((a, i) => (
                <tr key={i} style={{ borderBottom:`1px solid ${BORDER}` }}>
                  <td style={{ padding:"6px 12px", color:MUTED, fontSize:10, whiteSpace:"nowrap" }}>
                    {a.at ? new Date(a.at).toLocaleString() : "—"}
                  </td>
                  <td style={{ padding:"6px 12px", color:WHITE, fontSize:10 }}>{a.actor_name || a.actor_id || "—"}</td>
                  <td style={{ padding:"6px 12px", fontFamily:"monospace", color:AMBER, fontSize:10 }}>{a.action}</td>
                  <td style={{ padding:"6px 12px", color:MUTED, fontSize:10, fontFamily:"monospace" }}>{a.target_id || "—"}</td>
                  <td style={{ padding:"6px 12px", color:MUTED, fontSize:10, maxWidth:200, overflow:"hidden", textOverflow:"ellipsis", whiteSpace:"nowrap" }}>
                    {a.meta ? JSON.stringify(a.meta).slice(0,80) : ""}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div style={{ padding:"6px 12px", borderTop:`1px solid ${BORDER}`, color:MUTED, fontSize:10 }}>
          {log.length} entries
        </div>
      </div>
    </div>
  );
}

// ── Root Component ────────────────────────────────────────────────────────────
export default function SeshatsHub() {
  const { user }      = useAuth();
  const navigate      = useNavigate();
  const [tab, setTab] = useState("overview");
  const [notice, setNotice] = useState({ msg:"", err:false });

  // Permission gate — executive_admin only (already enforced by SupervisorProtected in App.js,
  // but we enforce it in the component too so it never silently degrades)
  useEffect(() => {
    if (user && user.role !== "executive_admin") {
      navigate("/", { replace: true });
    }
  }, [user, navigate]);

  function notify(msg, err=false) {
    setNotice({ msg, err });
    setTimeout(() => setNotice({ msg:"", err:false }), 4000);
  }

  const tabProps = { notify };

  return (
    <div style={{ minHeight:"100vh", background:BG, color:WHITE, fontFamily:"system-ui,sans-serif" }}>
      {/* Header */}
      <div style={{ background:"#0b0d17", borderBottom:`1px solid ${BORDER}`, padding:"16px 28px", display:"flex", alignItems:"center", justifyContent:"space-between", flexWrap:"wrap", gap:10 }}>
        <div>
          <div style={{ fontSize:9, textTransform:"uppercase", letterSpacing:"0.15em", color:MUTED, marginBottom:4 }}>
            Supervisor Control Panel · Backup System
          </div>
          <div style={{ fontSize:20, fontWeight:800, color:WHITE, letterSpacing:"-0.02em" }}>Seshat's Hub</div>
          <div style={{ fontSize:11, color:MUTED, marginTop:2 }}>
            {user?.full_name || user?.email} · executive_admin
          </div>
        </div>
        <div style={{ display:"flex", alignItems:"center", gap:10 }}>
          <div style={{ width:8, height:8, borderRadius:"50%", background:SIG, boxShadow:`0 0 8px ${SIG}` }} />
          <span style={{ fontSize:11, color:SIG, fontWeight:700 }}>SUPERVISOR ONLINE</span>
          <Link to="/admin/users" style={{ ...btn(MUTED), textDecoration:"none", fontSize:10 }}>Admin Panel</Link>
        </div>
      </div>

      {/* Notice bar */}
      {notice.msg && (
        <div style={{ padding:"10px 28px", background: notice.err ? "rgba(248,113,113,0.15)" : "rgba(74,242,197,0.12)",
          borderBottom:`1px solid ${notice.err ? ERR : SIG}`, color: notice.err ? ERR : SIG, fontSize:12, fontWeight:600 }}>
          {notice.msg}
        </div>
      )}

      <div style={{ display:"flex", minHeight:"calc(100vh - 90px)" }}>
        {/* Sidebar nav */}
        <nav style={{ width:180, background:"#0e1020", borderRight:`1px solid ${BORDER}`, padding:"16px 0", flexShrink:0 }}>
          {TABS.map(t => (
            <button key={t.key} onClick={() => setTab(t.key)}
              style={{ display:"block", width:"100%", textAlign:"left", padding:"9px 20px", fontSize:12, fontWeight: tab===t.key ? 700 : 400,
                color: tab===t.key ? SIG : MUTED, background: tab===t.key ? "rgba(74,242,197,0.08)" : "transparent",
                border:"none", cursor:"pointer", borderLeft: tab===t.key ? `3px solid ${SIG}` : "3px solid transparent",
                transition:"all 0.15s" }}>
              {t.label}
            </button>
          ))}
        </nav>

        {/* Tab content */}
        <main style={{ flex:1, padding:"24px 28px", overflowY:"auto", maxHeight:"calc(100vh - 90px)" }}>
          {tab === "overview"    && <OverviewTab    {...tabProps} />}
          {tab === "moderation"  && <ModerationTab  {...tabProps} />}
          {tab === "escalations" && <EscalationsTab {...tabProps} />}
          {tab === "greeter"     && <GreeterTab     {...tabProps} />}
          {tab === "sage"        && <SageTab        {...tabProps} />}
          {tab === "backup"      && <BackupTab      {...tabProps} />}
          {tab === "rbac"        && <RbacTab        {...tabProps} />}
          {tab === "audit"       && <AuditTab       {...tabProps} />}
        </main>
      </div>
    </div>
  );
}
