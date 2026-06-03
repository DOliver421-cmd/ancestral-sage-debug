import { useState, useEffect, useCallback } from "react";
import AppShell from "../components/AppShell";
import { api } from "../lib/api";
import { toast } from "sonner";
import {
  Shield, Users, Cpu, DollarSign, Lock, Globe, Eye, EyeOff,
  AlertTriangle, RefreshCw, ChevronDown, ChevronRight, CheckCircle,
  Clock, Activity, Zap
} from "lucide-react";

/* ────────────────── helpers ────────────────── */
function ago(iso) {
  if (!iso) return "—";
  const d = Date.now() - new Date(iso).getTime();
  if (d < 60000)    return "just now";
  if (d < 3600000)  return `${Math.floor(d / 60000)}m ago`;
  if (d < 86400000) return `${Math.floor(d / 3600000)}h ago`;
  return `${Math.floor(d / 86400000)}d ago`;
}

function Section({ icon: Icon, title, color = "#d4af37", children, defaultOpen = false }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div style={{ border: "1px solid rgba(212,175,55,0.18)", borderRadius: 12, marginBottom: "1rem", overflow: "hidden" }}>
      <button
        onClick={() => setOpen(v => !v)}
        style={{ width: "100%", display: "flex", alignItems: "center", gap: "0.6rem", padding: "0.85rem 1.1rem", background: "rgba(10,15,30,0.6)", border: "none", cursor: "pointer", textAlign: "left" }}
      >
        {Icon && <Icon size={16} color={color} />}
        <span style={{ color, fontWeight: "bold", fontSize: "0.85rem", flex: 1, fontFamily: "Trebuchet MS, sans-serif", textTransform: "uppercase", letterSpacing: "0.08em" }}>{title}</span>
        {open ? <ChevronDown size={14} color="#7a6e5a" /> : <ChevronRight size={14} color="#7a6e5a" />}
      </button>
      {open && <div style={{ padding: "1rem 1.1rem", background: "rgba(6,11,22,0.7)" }}>{children}</div>}
    </div>
  );
}

function Field({ label, children }) {
  return (
    <div style={{ marginBottom: "0.75rem" }}>
      <div style={{ fontSize: "0.68rem", color: "#d4af37", textTransform: "uppercase", letterSpacing: "0.09em", marginBottom: "0.25rem" }}>{label}</div>
      {children}
    </div>
  );
}

function Input({ ...props }) {
  return (
    <input
      {...props}
      style={{ background: "#060b16", border: "1px solid rgba(212,175,55,0.25)", borderRadius: 7, color: "#e8dfc8", padding: "0.45rem 0.7rem", fontSize: "0.82rem", width: "100%", outline: "none", ...props.style }}
    />
  );
}

function Select({ children, ...props }) {
  return (
    <select
      {...props}
      style={{ background: "#060b16", border: "1px solid rgba(212,175,55,0.25)", borderRadius: 7, color: "#e8dfc8", padding: "0.45rem 0.7rem", fontSize: "0.82rem", width: "100%", outline: "none", ...props.style }}
    >
      {children}
    </select>
  );
}

function Btn({ children, danger, busy, ...props }) {
  return (
    <button
      {...props}
      disabled={busy || props.disabled}
      style={{
        background: danger ? "#dc2626" : "#d4af37",
        color: danger ? "#fff" : "#1a1100",
        border: "none", borderRadius: 7, padding: "0.45rem 1rem",
        fontSize: "0.8rem", fontWeight: "bold", cursor: "pointer",
        opacity: (busy || props.disabled) ? 0.5 : 1,
        ...props.style
      }}
    >
      {busy ? "…" : children}
    </button>
  );
}

function ReasonInput({ value, onChange }) {
  return (
    <Field label="Reason (required)">
      <Input value={value} onChange={e => onChange(e.target.value)} placeholder="Justify this change…" />
    </Field>
  );
}

/* ────────────────── main component ────────────────── */
export default function ExecControlPanel() {
  const [state,   setState]   = useState(null);
  const [audit,   setAudit]   = useState([]);
  const [glass,   setGlass]   = useState([]);
  const [loading, setLoading] = useState(true);
  const [users,   setUsers]   = useState([]);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [sR, aR, gR, uR] = await Promise.allSettled([
        api.get("/exec/control/state"),
        api.get("/exec/control/audit?limit=30"),
        api.get("/exec/control/break-glass/active"),
        api.get("/admin/users?limit=200"),
      ]);
      if (sR.status === "fulfilled") setState(sR.value.data);
      if (aR.status === "fulfilled") setAudit(aR.value.data?.records || []);
      if (gR.status === "fulfilled") setGlass(gR.value.data?.active_overrides || []);
      if (uR.status === "fulfilled") setUsers(uR.value.data?.users || uR.value.data || []);
    } catch (e) {
      toast.error("Failed to load exec state");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  /* ── User Role ── */
  const [roleForm, setRoleForm] = useState({ user_id: "", new_role: "student", reason: "" });
  const [roleBusy, setRoleBusy] = useState(false);
  async function applyRole() {
    if (!roleForm.user_id || !roleForm.reason.trim()) return toast.error("Fill all fields");
    setRoleBusy(true);
    try {
      await api.post("/exec/control/user/role", roleForm);
      toast.success("Role updated");
      setRoleForm(f => ({ ...f, reason: "" }));
      load();
    } catch(e) { toast.error(e?.response?.data?.detail || "Failed"); }
    finally { setRoleBusy(false); }
  }

  /* ── User Tier ── */
  const [tierForm, setTierForm] = useState({ user_id: "", new_feature_tier: "free", new_sage_tier: "", reason: "" });
  const [tierBusy, setTierBusy] = useState(false);
  async function applyTier() {
    if (!tierForm.user_id || !tierForm.reason.trim()) return toast.error("Fill all fields");
    setTierBusy(true);
    try {
      const body = { ...tierForm };
      if (!body.new_sage_tier) delete body.new_sage_tier;
      await api.post("/exec/control/user/tier", body);
      toast.success("Tier updated");
      setTierForm(f => ({ ...f, reason: "" }));
      load();
    } catch(e) { toast.error(e?.response?.data?.detail || "Failed"); }
    finally { setTierBusy(false); }
  }

  /* ── Feature Flag ── */
  const [flagForm, setFlagForm] = useState({ flag_name: "", enabled: true, scope: "platform", user_id: "", reason: "" });
  const [flagBusy, setFlagBusy] = useState(false);
  async function applyFlag() {
    if (!flagForm.flag_name || !flagForm.reason.trim()) return toast.error("Fill all fields");
    setFlagBusy(true);
    try {
      const body = { ...flagForm };
      if (body.scope !== "user") delete body.user_id;
      await api.post("/exec/control/feature-flag", body);
      toast.success(`Flag ${flagForm.flag_name} ${flagForm.enabled ? "enabled" : "disabled"}`);
      setFlagForm(f => ({ ...f, reason: "" }));
      load();
    } catch(e) { toast.error(e?.response?.data?.detail || "Failed"); }
    finally { setFlagBusy(false); }
  }

  /* ── AI Access ── */
  const [aiForm, setAiForm] = useState({ user_id: "", persona: "all", enabled: true, reason: "" });
  const [aiBusy, setAiBusy] = useState(false);
  async function applyAI() {
    if (!aiForm.user_id || !aiForm.reason.trim()) return toast.error("Fill all fields");
    setAiBusy(true);
    try {
      await api.post("/exec/control/ai-access", aiForm);
      toast.success("AI access updated");
      setAiForm(f => ({ ...f, reason: "" }));
    } catch(e) { toast.error(e?.response?.data?.detail || "Failed"); }
    finally { setAiBusy(false); }
  }

  /* ── Budget ── */
  const [budgetForm, setBudgetForm] = useState({ budget_key: "llm_monthly_usd", limit: "", reason: "" });
  const [budgetBusy, setBudgetBusy] = useState(false);
  async function applyBudget() {
    if (!budgetForm.limit || !budgetForm.reason.trim()) return toast.error("Fill all fields");
    setBudgetBusy(true);
    try {
      await api.post("/exec/control/budget", { ...budgetForm, limit: parseFloat(budgetForm.limit) });
      toast.success("Budget updated");
      setBudgetForm(f => ({ ...f, reason: "" }));
      load();
    } catch(e) { toast.error(e?.response?.data?.detail || "Failed"); }
    finally { setBudgetBusy(false); }
  }

  /* ── Visibility Flag ── */
  const [visForm, setVisForm] = useState({ flag: "", enabled: true, reason: "" });
  const [visBusy, setVisBusy] = useState(false);
  async function applyVis() {
    if (!visForm.flag || !visForm.reason.trim()) return toast.error("Fill all fields");
    setVisBusy(true);
    try {
      await api.post("/exec/control/visibility", visForm);
      toast.success("Visibility updated");
      setVisForm(f => ({ ...f, reason: "" }));
      load();
    } catch(e) { toast.error(e?.response?.data?.detail || "Failed"); }
    finally { setVisBusy(false); }
  }

  /* ── Break Glass ── */
  const [bgForm, setBgForm] = useState({ reason: "", scope: "sage_pipeline", target_uid: "", duration_minutes: 60 });
  const [bgBusy, setBgBusy] = useState(false);
  async function activateBreakGlass() {
    if (bgForm.reason.length < 20) return toast.error("Reason must be at least 20 characters");
    if (!window.confirm("BREAK GLASS: This activates an executive override and is fully audited. Proceed?")) return;
    setBgBusy(true);
    try {
      const body = { ...bgForm };
      if (!body.target_uid) delete body.target_uid;
      const r = await api.post("/exec/control/break-glass/activate", body);
      toast.success(`Override activated: ${r.data.override_id.slice(0, 8)}… expires in ${bgForm.duration_minutes}m`);
      setBgForm(f => ({ ...f, reason: "" }));
      load();
    } catch(e) { toast.error(e?.response?.data?.detail || "Failed"); }
    finally { setBgBusy(false); }
  }

  async function revokeGlass(id) {
    const reason = window.prompt("Reason for revoking this override:");
    if (!reason) return;
    try {
      await api.post("/exec/control/break-glass/revoke", { override_id: id, reason });
      toast.success("Override revoked");
      load();
    } catch(e) { toast.error(e?.response?.data?.detail || "Failed"); }
  }

  const ROW = { display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem" };
  const ROLES = ["guest","student","instructor","creator","mentor","moderator","steward","elder","admin","executive_admin"];

  return (
    <AppShell>
      <div style={{ padding: "2rem 1.5rem", maxWidth: 900, margin: "0 auto", color: "#e8dfc8" }}>

        {/* Header */}
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "1.75rem" }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.25rem" }}>
              <Shield size={18} color="#d4af37" />
              <span style={{ fontSize: "0.7rem", textTransform: "uppercase", letterSpacing: "0.12em", color: "#d4af37", fontFamily: "Trebuchet MS, sans-serif" }}>Executive Control Layer</span>
            </div>
            <h1 style={{ fontSize: "1.6rem", fontWeight: "bold", color: "#f0d060", fontFamily: "Trebuchet MS, sans-serif" }}>Sovereign Command</h1>
            <p style={{ fontSize: "0.78rem", color: "#7a6e5a", marginTop: "0.2rem" }}>All actions are audited, persisted, and immediately effective.</p>
          </div>
          <button onClick={load} title="Refresh" style={{ background: "none", border: "1px solid rgba(212,175,55,0.25)", borderRadius: 8, padding: "0.5rem", cursor: "pointer", color: "#d4af37" }}>
            <RefreshCw size={16} className={loading ? "animate-spin" : ""} />
          </button>
        </div>

        {/* Active break-glass alert */}
        {glass.length > 0 && (
          <div style={{ background: "rgba(220,38,38,0.12)", border: "1px solid #dc2626", borderRadius: 10, padding: "0.85rem 1rem", marginBottom: "1.2rem", display: "flex", alignItems: "center", gap: "0.6rem" }}>
            <AlertTriangle size={16} color="#ef4444" />
            <span style={{ color: "#ef4444", fontSize: "0.82rem", fontWeight: "bold" }}>{glass.length} active break-glass override{glass.length > 1 ? "s" : ""}</span>
          </div>
        )}

        {/* ── USER CONTROLS ── */}
        <Section icon={Users} title="User Role" defaultOpen={true}>
          <div style={ROW}>
            <Field label="Select User">
              <Select value={roleForm.user_id} onChange={e => setRoleForm(f => ({ ...f, user_id: e.target.value }))}>
                <option value="">— choose —</option>
                {users.map(u => <option key={u.id} value={u.id}>{u.email} ({u.role})</option>)}
              </Select>
            </Field>
            <Field label="New Role">
              <Select value={roleForm.new_role} onChange={e => setRoleForm(f => ({ ...f, new_role: e.target.value }))}>
                {ROLES.map(r => <option key={r} value={r}>{r}</option>)}
              </Select>
            </Field>
          </div>
          <ReasonInput value={roleForm.reason} onChange={v => setRoleForm(f => ({ ...f, reason: v }))} />
          <Btn onClick={applyRole} busy={roleBusy}>Apply Role Change</Btn>
        </Section>

        <Section icon={Zap} title="User Feature Tier">
          <div style={ROW}>
            <Field label="Select User">
              <Select value={tierForm.user_id} onChange={e => setTierForm(f => ({ ...f, user_id: e.target.value }))}>
                <option value="">— choose —</option>
                {users.map(u => <option key={u.id} value={u.id}>{u.email}</option>)}
              </Select>
            </Field>
            <Field label="Feature Tier">
              <Select value={tierForm.new_feature_tier} onChange={e => setTierForm(f => ({ ...f, new_feature_tier: e.target.value }))}>
                <option value="free">Free</option>
                <option value="premium">Premium</option>
                <option value="executive">Executive</option>
              </Select>
            </Field>
          </div>
          <div style={ROW}>
            <Field label="Sage Tier (optional)">
              <Select value={tierForm.new_sage_tier} onChange={e => setTierForm(f => ({ ...f, new_sage_tier: e.target.value }))}>
                <option value="">— unchanged —</option>
                <option value="basic">Basic</option>
                <option value="advanced">Advanced</option>
              </Select>
            </Field>
            <div />
          </div>
          <ReasonInput value={tierForm.reason} onChange={v => setTierForm(f => ({ ...f, reason: v }))} />
          <Btn onClick={applyTier} busy={tierBusy}>Apply Tier Change</Btn>
        </Section>

        <Section icon={Cpu} title="AI Persona Access">
          <div style={ROW}>
            <Field label="Select User">
              <Select value={aiForm.user_id} onChange={e => setAiForm(f => ({ ...f, user_id: e.target.value }))}>
                <option value="">— choose —</option>
                {users.map(u => <option key={u.id} value={u.id}>{u.email}</option>)}
              </Select>
            </Field>
            <Field label="Persona">
              <Select value={aiForm.persona} onChange={e => setAiForm(f => ({ ...f, persona: e.target.value }))}>
                <option value="all">All Personas</option>
                <option value="director">Director</option>
                <option value="sage">Sage</option>
                <option value="sovereign">Sovereign</option>
                <option value="prt">P.R.T.</option>
                <option value="cipher">Cipher</option>
              </Select>
            </Field>
          </div>
          <Field label="Access">
            <Select value={aiForm.enabled ? "true" : "false"} onChange={e => setAiForm(f => ({ ...f, enabled: e.target.value === "true" }))}>
              <option value="true">Grant Access</option>
              <option value="false">Revoke Access</option>
            </Select>
          </Field>
          <ReasonInput value={aiForm.reason} onChange={v => setAiForm(f => ({ ...f, reason: v }))} />
          <Btn onClick={applyAI} busy={aiBusy}>Apply AI Access</Btn>
        </Section>

        {/* ── PLATFORM CONTROLS ── */}
        <Section icon={Globe} title="Feature Flags">
          <div style={ROW}>
            <Field label="Flag Name">
              <Input value={flagForm.flag_name} onChange={e => setFlagForm(f => ({ ...f, flag_name: e.target.value }))} placeholder="e.g. labs_disabled" />
            </Field>
            <Field label="Scope">
              <Select value={flagForm.scope} onChange={e => setFlagForm(f => ({ ...f, scope: e.target.value }))}>
                <option value="platform">Platform-wide</option>
                <option value="user">Per User</option>
              </Select>
            </Field>
          </div>
          {flagForm.scope === "user" && (
            <Field label="User">
              <Select value={flagForm.user_id} onChange={e => setFlagForm(f => ({ ...f, user_id: e.target.value }))}>
                <option value="">— choose —</option>
                {users.map(u => <option key={u.id} value={u.id}>{u.email}</option>)}
              </Select>
            </Field>
          )}
          <Field label="State">
            <Select value={flagForm.enabled ? "true" : "false"} onChange={e => setFlagForm(f => ({ ...f, enabled: e.target.value === "true" }))}>
              <option value="true">Enable</option>
              <option value="false">Disable</option>
            </Select>
          </Field>
          <ReasonInput value={flagForm.reason} onChange={v => setFlagForm(f => ({ ...f, reason: v }))} />
          <Btn onClick={applyFlag} busy={flagBusy}>Set Flag</Btn>
        </Section>

        <Section icon={DollarSign} title="Spending Budgets">
          <div style={ROW}>
            <Field label="Budget Key">
              <Select value={budgetForm.budget_key} onChange={e => setBudgetForm(f => ({ ...f, budget_key: e.target.value }))}>
                <option value="llm_monthly_usd">LLM ($/month)</option>
                <option value="tts_monthly_chars">TTS (chars/month)</option>
                <option value="stt_monthly_mins">STT (mins/month)</option>
              </Select>
            </Field>
            <Field label="New Limit">
              <Input type="number" min="0" value={budgetForm.limit} onChange={e => setBudgetForm(f => ({ ...f, limit: e.target.value }))} placeholder="0.00" />
            </Field>
          </div>
          <ReasonInput value={budgetForm.reason} onChange={v => setBudgetForm(f => ({ ...f, reason: v }))} />
          <Btn onClick={applyBudget} busy={budgetBusy}>Set Budget</Btn>

          {/* Current budgets */}
          {state?.budgets?.length > 0 && (
            <div style={{ marginTop: "0.75rem", display: "flex", flexWrap: "wrap", gap: "0.5rem" }}>
              {state.budgets.map(b => (
                <div key={b.key} style={{ background: "rgba(212,175,55,0.08)", border: "1px solid rgba(212,175,55,0.2)", borderRadius: 6, padding: "0.3rem 0.65rem", fontSize: "0.72rem" }}>
                  <span style={{ color: "#d4af37" }}>{b.key}</span>: {b.limit}
                </div>
              ))}
            </div>
          )}
        </Section>

        <Section icon={Eye} title="UI Visibility Flags">
          <div style={ROW}>
            <Field label="Flag Name">
              <Select value={visForm.flag} onChange={e => setVisForm(f => ({ ...f, flag: e.target.value }))}>
                <option value="">— choose —</option>
                <option value="show_pricing">Show Pricing</option>
                <option value="show_legal_tools">Show Legal Tools</option>
                <option value="show_revenue_division">Show Revenue Division</option>
                <option value="show_ghost_producer">Show Ghost Producer</option>
                <option value="show_band_on_page">Show Band on Page</option>
              </Select>
            </Field>
            <Field label="State">
              <Select value={visForm.enabled ? "true" : "false"} onChange={e => setVisForm(f => ({ ...f, enabled: e.target.value === "true" }))}>
                <option value="true">Show</option>
                <option value="false">Hide</option>
              </Select>
            </Field>
          </div>
          <ReasonInput value={visForm.reason} onChange={v => setVisForm(f => ({ ...f, reason: v }))} />
          <Btn onClick={applyVis} busy={visBusy}>Set Visibility</Btn>

          {/* Current flags */}
          {state?.visibility_flags?.length > 0 && (
            <div style={{ marginTop: "0.75rem", display: "flex", flexWrap: "wrap", gap: "0.5rem" }}>
              {state.visibility_flags.map(v => (
                <div key={v.flag} style={{ background: v.enabled ? "rgba(109,189,138,0.12)" : "rgba(239,68,68,0.1)", border: `1px solid ${v.enabled ? "rgba(109,189,138,0.3)" : "rgba(239,68,68,0.3)"}`, borderRadius: 6, padding: "0.3rem 0.65rem", fontSize: "0.72rem" }}>
                  {v.enabled ? <CheckCircle size={10} color="#6dbd8a" style={{ display: "inline", marginRight: 4 }} /> : <EyeOff size={10} color="#ef4444" style={{ display: "inline", marginRight: 4 }} />}
                  {v.flag}
                </div>
              ))}
            </div>
          )}
        </Section>

        {/* ── BREAK GLASS ── */}
        <Section icon={AlertTriangle} title="Break-Glass Override" color="#ef4444">
          <p style={{ fontSize: "0.78rem", color: "#7a6e5a", marginBottom: "0.75rem", lineHeight: 1.6 }}>
            Time-bound executive override. Requires a 20-character minimum justification. Fully logged and visible in audit.
          </p>
          <div style={ROW}>
            <Field label="Scope">
              <Select value={bgForm.scope} onChange={e => setBgForm(f => ({ ...f, scope: e.target.value }))}>
                <option value="sage_pipeline">Sage Pipeline</option>
                <option value="user_tier">User Tier</option>
                <option value="legal_access">Legal Access</option>
                <option value="platform_lock">Platform Lock</option>
                <option value="ai_pipeline">AI Pipeline</option>
              </Select>
            </Field>
            <Field label="Duration (minutes)">
              <Select value={bgForm.duration_minutes} onChange={e => setBgForm(f => ({ ...f, duration_minutes: parseInt(e.target.value) }))}>
                <option value={15}>15 min</option>
                <option value={30}>30 min</option>
                <option value={60}>1 hour</option>
                <option value={120}>2 hours</option>
                <option value={480}>8 hours</option>
              </Select>
            </Field>
          </div>
          <Field label="Target User (optional)">
            <Select value={bgForm.target_uid} onChange={e => setBgForm(f => ({ ...f, target_uid: e.target.value }))}>
              <option value="">— platform-wide —</option>
              {users.map(u => <option key={u.id} value={u.id}>{u.email}</option>)}
            </Select>
          </Field>
          <Field label="Justification (min 20 chars)">
            <textarea
              value={bgForm.reason}
              onChange={e => setBgForm(f => ({ ...f, reason: e.target.value }))}
              rows={3}
              placeholder="Explain why this override is necessary…"
              style={{ background: "#060b16", border: "1px solid rgba(212,175,55,0.25)", borderRadius: 7, color: "#e8dfc8", padding: "0.45rem 0.7rem", fontSize: "0.82rem", width: "100%", outline: "none", resize: "vertical" }}
            />
            <div style={{ fontSize: "0.65rem", color: bgForm.reason.length >= 20 ? "#6dbd8a" : "#7a6e5a", marginTop: "0.2rem" }}>{bgForm.reason.length}/20 chars minimum</div>
          </Field>
          <Btn onClick={activateBreakGlass} busy={bgBusy} danger>Activate Break-Glass</Btn>

          {/* Active overrides */}
          {glass.length > 0 && (
            <div style={{ marginTop: "0.85rem" }}>
              <div style={{ fontSize: "0.68rem", color: "#d4af37", textTransform: "uppercase", letterSpacing: "0.09em", marginBottom: "0.4rem" }}>Active Overrides</div>
              {glass.map(g => (
                <div key={g.id} style={{ background: "rgba(220,38,38,0.1)", border: "1px solid rgba(239,68,68,0.3)", borderRadius: 8, padding: "0.6rem 0.8rem", marginBottom: "0.4rem", display: "flex", alignItems: "center", justifyContent: "space-between", gap: "0.5rem" }}>
                  <div>
                    <div style={{ fontSize: "0.78rem", color: "#ef4444", fontWeight: "bold" }}>{g.scope}</div>
                    <div style={{ fontSize: "0.68rem", color: "#7a6e5a" }}>{g.reason?.slice(0, 60)}{g.reason?.length > 60 ? "…" : ""}</div>
                  </div>
                  <Btn onClick={() => revokeGlass(g.id)} danger style={{ padding: "0.3rem 0.6rem", fontSize: "0.72rem" }}>Revoke</Btn>
                </div>
              ))}
            </div>
          )}
        </Section>

        {/* ── AUDIT LOG ── */}
        <Section icon={Activity} title="Executive Audit Log">
          {audit.length === 0
            ? <div style={{ color: "#7a6e5a", fontSize: "0.8rem" }}>No actions recorded yet.</div>
            : (
              <div style={{ overflowX: "auto" }}>
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.75rem" }}>
                  <thead>
                    <tr style={{ borderBottom: "1px solid rgba(212,175,55,0.15)" }}>
                      {["Action","Target","Note","When"].map(h => (
                        <th key={h} style={{ padding: "0.4rem 0.5rem", textAlign: "left", color: "#d4af37", fontWeight: "bold", textTransform: "uppercase", letterSpacing: "0.07em", fontSize: "0.65rem" }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {audit.map((row, i) => (
                      <tr key={row.id || i} style={{ borderBottom: "1px solid rgba(212,175,55,0.07)" }}>
                        <td style={{ padding: "0.4rem 0.5rem", color: "#d4af37", fontFamily: "monospace" }}>{row.action}</td>
                        <td style={{ padding: "0.4rem 0.5rem", color: "#e8dfc8", maxWidth: 120, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{row.target_id || "—"}</td>
                        <td style={{ padding: "0.4rem 0.5rem", color: "#7a6e5a", maxWidth: 200, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{row.note || "—"}</td>
                        <td style={{ padding: "0.4rem 0.5rem", color: "#7a6e5a", whiteSpace: "nowrap" }}>{ago(row.created_at)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )
          }
        </Section>

      </div>
    </AppShell>
  );
}
