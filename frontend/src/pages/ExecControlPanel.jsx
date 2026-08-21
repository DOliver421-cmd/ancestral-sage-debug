import { useState, useEffect, useCallback } from "react";
import AppShell from "../components/AppShell";
import { api } from "../lib/api";
import { ROLES_ALL } from "../lib/roles";
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
  const [accessPages, setAccessPages] = useState([]);
  const [accessBusy, setAccessBusy] = useState(null);
  const [routeAccess, setRouteAccess] = useState([]);
  const [routeSearch, setRouteSearch] = useState("");
  const [authzMatrix, setAuthzMatrix] = useState(null);
  const [authzBusy, setAuthzBusy] = useState(false);
  const [userRouteForm, setUserRouteForm] = useState({ user_id: "", route_key: "", enabled: false, reason: "" });
  const [userRouteBusy, setUserRouteBusy] = useState(false);

  // One executive surface for real user provisioning and lifecycle CRUD.
  const [provisionForm, setProvisionForm] = useState({ email: "", full_name: "", password: "", role: "student", associate: "" });
  const [provisionBusy, setProvisionBusy] = useState(false);
  const [lifecycleForm, setLifecycleForm] = useState({ user_id: "", full_name: "", email: "", associate: "", new_password: "", ban_reason: "" });
  const [lifecycleBusy, setLifecycleBusy] = useState(false);

  const selectLifecycleUser = (userId) => {
    const target = users.find((candidate) => candidate.id === userId);
    setLifecycleForm({
      user_id: userId,
      full_name: target?.full_name || "",
      email: target?.email || "",
      associate: target?.associate || "",
      new_password: "",
      ban_reason: target?.ban_reason || "",
    });
  };

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [sR, aR, gR, uR, xR, rR, mR] = await Promise.allSettled([
        api.get("/exec/control/state"),
        api.get("/exec/control/audit?limit=30"),
        api.get("/exec/control/break-glass/active"),
        api.get("/admin/users?limit=200"),
        api.get("/exec/control/access"),
        api.get("/exec/control/route-access"),
        api.get("/exec/control/authz-matrix"),
      ]);
      if (sR.status === "fulfilled") setState(sR.value.data);
      if (aR.status === "fulfilled") setAudit(aR.value.data?.records || []);
      if (gR.status === "fulfilled") setGlass(gR.value.data?.active_overrides || []);
      if (uR.status === "fulfilled") setUsers(uR.value.data?.users || uR.value.data || []);
      if (xR.status === "fulfilled") setAccessPages(xR.value.data?.pages || []);
      if (rR.status === "fulfilled") setRouteAccess(rR.value.data?.routes || []);
      if (mR.status === "fulfilled") setAuthzMatrix(mR.value.data || null);
    } catch (e) {
      toast.error("Failed to load exec state");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  async function provisionUser() {
    if (!provisionForm.email.trim() || !provisionForm.full_name.trim() || provisionForm.password.length < 8) {
      return toast.error("Email, full name, and an 8-character password are required");
    }
    setProvisionBusy(true);
    try {
      await api.post("/admin/users", {
        email: provisionForm.email.trim().toLowerCase(),
        full_name: provisionForm.full_name.trim(),
        password: provisionForm.password,
        role: provisionForm.role,
        ...(provisionForm.associate.trim() ? { associate: provisionForm.associate.trim() } : {}),
      });
      toast.success("User provisioned");
      setProvisionForm({ email: "", full_name: "", password: "", role: "student", associate: "" });
      load();
    } catch (e) { toast.error(e?.response?.data?.detail || "Failed to provision user"); }
    finally { setProvisionBusy(false); }
  }

  async function saveLifecycleIdentity() {
    if (!lifecycleForm.user_id || !lifecycleForm.full_name.trim() || !lifecycleForm.email.trim()) {
      return toast.error("Choose a user and provide a name and email");
    }
    setLifecycleBusy(true);
    try {
      await api.patch(`/admin/users/${lifecycleForm.user_id}`, {
        full_name: lifecycleForm.full_name.trim(),
        email: lifecycleForm.email.trim().toLowerCase(),
        associate: lifecycleForm.associate.trim() || null,
      });
      if (lifecycleForm.new_password.trim()) {
        if (lifecycleForm.new_password.trim().length < 8) throw new Error("Password must be at least 8 characters");
        await api.post(`/admin/users/${lifecycleForm.user_id}/password`, { new_password: lifecycleForm.new_password.trim() });
      }
      toast.success("Identity and credentials updated; prior sessions were revoked");
      setLifecycleForm((form) => ({ ...form, new_password: "" }));
      load();
    } catch (e) { toast.error(e?.response?.data?.detail || e.message || "Failed to update identity"); }
    finally { setLifecycleBusy(false); }
  }

  async function lifecycleAction(action) {
    const uid = lifecycleForm.user_id;
    if (!uid) return toast.error("Choose a user first");
    const target = users.find((candidate) => candidate.id === uid);
    if (!target) return toast.error("Selected user is no longer available");
    if (action === "delete" && !window.confirm(`Permanently delete ${target.email}? This cannot be undone.`)) return;
    if (action === "ban" && lifecycleForm.ban_reason.trim().length < 5) return toast.error("Ban reason must be at least 5 characters");
    setLifecycleBusy(true);
    try {
      if (action === "active") {
        await api.patch(`/admin/users/${uid}/active`, { is_active: target.is_active === false });
      } else if (action === "ban") {
        await api.post(`/admin/users/${uid}/ban`, { reason: lifecycleForm.ban_reason.trim() });
      } else if (action === "unban") {
        await api.post(`/admin/users/${uid}/unban`);
      } else if (action === "logout") {
        await api.delete(`/admin/users/${uid}/sessions`);
      } else if (action === "delete") {
        await api.delete(`/admin/users/${uid}`);
        setLifecycleForm({ user_id: "", full_name: "", email: "", associate: "", new_password: "", ban_reason: "" });
      }
      toast.success(action === "active" ? "Account status updated" : action === "logout" ? "All sessions revoked" : `User ${action} complete`);
      load();
    } catch (e) { toast.error(e?.response?.data?.detail || `Failed to ${action} user`); }
    finally { setLifecycleBusy(false); }
  }

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

  /* ── Page & Feature Access ── */
  async function toggleAccess(page, currentEnabled) {
    setAccessBusy(page.key);
    try {
      await api.post("/exec/control/access", {
        page: page.key,
        enabled: !currentEnabled,
        reason: "Toggled from Sovereign Command",
      });
      toast.success(`${page.label} ${!currentEnabled ? "enabled" : "disabled"}`);
      load();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Failed to update access");
    } finally {
      setAccessBusy(null);
    }
  }

  /* ── Live route authorization matrix ── */
  const visibleRoutes = routeAccess.filter(r => {
    const q = routeSearch.trim().toLowerCase();
    return !q || r.route_key.toLowerCase().includes(q);
  });

  async function setRoutePolicy(row, patch) {
    setAccessBusy(`route:${row.route_key}`);
    try {
      await api.patch("/exec/control/route-access", { route_key: row.route_key, ...patch });
      toast.success(`Policy updated for ${row.route_key}`);
      load();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Failed to update route policy");
    } finally {
      setAccessBusy(null);
    }
  }

  async function saveAuthzMatrix() {
    if (!authzMatrix) return;
    setAuthzBusy(true);
    try {
      const requirements = Object.fromEntries((authzMatrix.features || []).map(f => [f.key, f.min_tier]));
      const r = await api.post("/exec/control/authz-matrix", {
        requirements,
        reason: "Updated from Sovereign Command authorization matrix",
      });
      setAuthzMatrix(m => ({ ...m, effective: r.data?.effective || requirements }));
      toast.success("Feature tier matrix saved and enforced server-side");
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Failed to save authorization matrix");
    } finally {
      setAuthzBusy(false);
    }
  }

  async function saveUserRouteOverride() {
    if (!userRouteForm.user_id || !userRouteForm.route_key || !userRouteForm.reason.trim()) {
      return toast.error("Choose a user, route, and provide a reason");
    }
    setUserRouteBusy(true);
    try {
      await api.patch("/exec/control/user-route-access", userRouteForm);
      toast.success("Per-user route override saved");
      setUserRouteForm(f => ({ ...f, reason: "" }));
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Failed to save per-user override");
    } finally {
      setUserRouteBusy(false);
    }
  }

  /* ── Break Glass ── */
  const [bgForm, setBgForm] = useState({ reason: "", scope: "sage_pipeline", target_uid: "", duration_minutes: 60 });
  const [bgBusy, setBgBusy] = useState(false);
  const [confirmBreakGlass, setConfirmBreakGlass] = useState(false);
  const [revokeTarget, setRevokeTarget] = useState(null);
  const [revokeReason, setRevokeReason] = useState("");

  async function activateBreakGlass() {
    if (bgForm.reason.length < 20) return toast.error("Reason must be at least 20 characters");
    setConfirmBreakGlass(true);
  }

  async function doActivateBreakGlass() {
    setConfirmBreakGlass(false);
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
    setRevokeTarget(id);
    setRevokeReason("");
  }

  async function doRevokeGlass() {
    const id = revokeTarget;
    const reason = revokeReason;
    setRevokeTarget(null);
    setRevokeReason("");
    if (!reason?.trim()) return;
    try {
      await api.post("/exec/control/break-glass/revoke", { override_id: id, reason });
      toast.success("Override revoked");
      load();
    } catch(e) { toast.error(e?.response?.data?.detail || "Failed"); }
  }

  const ROW = { display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem" };
  // Canonical 7-role RBAC from lib/roles.js (mirrors backend/roles.py).
  const ROLES = ROLES_ALL;

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
        <Section icon={Users} title="Provisioning & Identity Lifecycle" defaultOpen={true}>
          <p style={{ fontSize: "0.78rem", color: "#7a6e5a", marginBottom: "0.9rem", lineHeight: 1.6 }}>
            These controls write to the live users collection. Credential, role, tier, activation, ban, deletion, and logout mutations are server-authorized and revoke affected sessions.
          </p>
          <div style={{ color: "#d4af37", fontSize: "0.7rem", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: "0.45rem" }}>Create user</div>
          <div style={ROW}>
            <Input value={provisionForm.full_name} onChange={e => setProvisionForm(f => ({ ...f, full_name: e.target.value }))} placeholder="Full name" aria-label="New user's full name" />
            <Input type="email" value={provisionForm.email} onChange={e => setProvisionForm(f => ({ ...f, email: e.target.value }))} placeholder="Email" aria-label="New user's email" />
          </div>
          <div style={{ ...ROW, marginTop: "0.65rem" }}>
            <Input type="password" value={provisionForm.password} onChange={e => setProvisionForm(f => ({ ...f, password: e.target.value }))} placeholder="Temporary password (8+ chars)" aria-label="Temporary password" />
            <Select value={provisionForm.role} onChange={e => setProvisionForm(f => ({ ...f, role: e.target.value }))} aria-label="New user's role">
              {ROLES.map(role => <option key={role} value={role}>{role}</option>)}
            </Select>
          </div>
          <Input value={provisionForm.associate} onChange={e => setProvisionForm(f => ({ ...f, associate: e.target.value }))} placeholder="Associate / cohort (optional)" style={{ marginTop: "0.65rem" }} />
          <div style={{ marginTop: "0.65rem" }}><Btn onClick={provisionUser} busy={provisionBusy}>Create Account</Btn></div>

          <div style={{ marginTop: "1.2rem", paddingTop: "1rem", borderTop: "1px solid rgba(212,175,55,0.12)" }}>
            <div style={{ color: "#d4af37", fontSize: "0.7rem", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: "0.45rem" }}>Edit identity, credentials, and status</div>
            <Select value={lifecycleForm.user_id} onChange={e => selectLifecycleUser(e.target.value)} aria-label="Select user for lifecycle controls">
              <option value="">— choose user —</option>
              {users.map(u => <option key={u.id} value={u.id}>{u.email} ({u.role})</option>)}
            </Select>
            {lifecycleForm.user_id && (
              <>
                <div style={{ ...ROW, marginTop: "0.65rem" }}>
                  <Input value={lifecycleForm.full_name} onChange={e => setLifecycleForm(f => ({ ...f, full_name: e.target.value }))} placeholder="Full name" />
                  <Input type="email" value={lifecycleForm.email} onChange={e => setLifecycleForm(f => ({ ...f, email: e.target.value }))} placeholder="Email" />
                </div>
                <div style={{ ...ROW, marginTop: "0.65rem" }}>
                  <Input value={lifecycleForm.associate} onChange={e => setLifecycleForm(f => ({ ...f, associate: e.target.value }))} placeholder="Associate / cohort" />
                  <Input type="password" value={lifecycleForm.new_password} onChange={e => setLifecycleForm(f => ({ ...f, new_password: e.target.value }))} placeholder="New password (optional)" />
                </div>
                <Input value={lifecycleForm.ban_reason} onChange={e => setLifecycleForm(f => ({ ...f, ban_reason: e.target.value }))} placeholder="Ban reason (required only to ban)" style={{ marginTop: "0.65rem" }} />
                <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem", marginTop: "0.7rem" }}>
                  <Btn onClick={saveLifecycleIdentity} busy={lifecycleBusy}>Save Identity</Btn>
                  <Btn onClick={() => lifecycleAction("active")} busy={lifecycleBusy}>{users.find(u => u.id === lifecycleForm.user_id)?.is_active === false ? "Activate" : "Deactivate"}</Btn>
                  {users.find(u => u.id === lifecycleForm.user_id)?.banned ? <Btn onClick={() => lifecycleAction("unban")} busy={lifecycleBusy}>Unban</Btn> : <Btn onClick={() => lifecycleAction("ban")} busy={lifecycleBusy} danger>Ban</Btn>}
                  <Btn onClick={() => lifecycleAction("logout")} busy={lifecycleBusy}>Revoke Sessions</Btn>
                  <Btn onClick={() => lifecycleAction("delete")} busy={lifecycleBusy} danger>Delete User</Btn>
                </div>
              </>
            )}
          </div>
        </Section>

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

        {/* ── PAGE & FEATURE ACCESS ── */}
        <Section icon={Lock} title="Page & Feature Access" defaultOpen={true}>
          <p style={{ fontSize: "0.78rem", color: "#7a6e5a", marginBottom: "0.75rem", lineHeight: 1.6 }}>
            One board for the whole site. Flipping a page OFF hides it from every sidebar and
            blocks the route immediately — exec-only pages stay exec-only, and any page can be
            closed without touching code. Every change is audited.
          </p>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(250px, 1fr))", gap: "0.5rem" }}>
            {accessPages.map(p => (
              <button
                key={p.key}
                onClick={() => toggleAccess(p, p.enabled)}
                disabled={accessBusy === p.key}
                title={`${p.label} — click to ${p.enabled ? "disable" : "enable"}`}
                style={{
                  display: "flex", alignItems: "center", justifyContent: "space-between", gap: "0.5rem",
                  padding: "0.5rem 0.7rem", borderRadius: 8, cursor: "pointer", textAlign: "left",
                  border: p.enabled ? "1px solid rgba(109,189,138,0.3)" : "1px solid rgba(239,68,68,0.3)",
                  background: p.enabled ? "rgba(109,189,138,0.08)" : "rgba(239,68,68,0.08)",
                }}
              >
                <span style={{ fontSize: "0.78rem", color: "#e8dfc8" }}>
                  <span style={{ display: "block", fontWeight: "bold" }}>{p.label}</span>
                  <span style={{ fontSize: "0.65rem", color: "#7a6e5a" }}>{p.path}</span>
                </span>
                <span style={{ fontSize: "0.68rem", fontWeight: "bold", color: p.enabled ? "#6dbd8a" : "#ef4444", flexShrink: 0 }}>
                  {accessBusy === p.key ? "…" : p.enabled ? "ON" : "OFF"}
                </span>
              </button>
            ))}
            {accessPages.length === 0 && (
              <p style={{ fontSize: "0.78rem", color: "#7a6e5a" }}>Loading registry…</p>
            )}
          </div>
        </Section>

        {/* ── AUTHORIZATION MATRIX ── */}
        <Section icon={Shield} title="Feature Tier Authorization Matrix" defaultOpen={true}>
          <p style={{ fontSize: "0.78rem", color: "#7a6e5a", marginBottom: "0.75rem", lineHeight: 1.6 }}>
            These are the feature gates the backend actually evaluates. Changing a row writes the live authorization policy; it is not a frontend-only label.
          </p>
          {authzMatrix?.features?.map(feature => (
            <div key={feature.key} style={{ display: "grid", gridTemplateColumns: "1.2fr 1fr 1.6fr auto", gap: "0.65rem", alignItems: "center", padding: "0.55rem 0", borderBottom: "1px solid rgba(212,175,55,0.1)" }}>
              <span style={{ color: "#e8dfc8", fontSize: "0.8rem", fontWeight: "bold" }}>{feature.label}</span>
              <Select value={feature.min_tier} onChange={e => setAuthzMatrix(m => ({ ...m, features: m.features.map(f => f.key === feature.key ? { ...f, min_tier: e.target.value } : f) }))}>
                {(authzMatrix.tiers || []).map(t => <option key={t} value={t}>{t}</option>)}
              </Select>
              <span style={{ color: "#aaa08f", fontSize: "0.7rem" }}>{feature.api} · {feature.detail}</span>
              <span style={{ color: "#6dbd8a", fontSize: "0.68rem", fontWeight: "bold" }}>LIVE</span>
            </div>
          ))}
          <div style={{ marginTop: "0.8rem" }}><Btn onClick={saveAuthzMatrix} busy={authzBusy}>Save Feature Matrix</Btn></div>
        </Section>

        {/* ── LIVE ROUTE MATRIX ── */}
        <Section icon={Lock} title={`Live API Route Matrix (${routeAccess.length})`} defaultOpen={false}>
          <p style={{ fontSize: "0.78rem", color: "#7a6e5a", marginBottom: "0.75rem", lineHeight: 1.6 }}>
            Every authenticated FastAPI route is discovered from its real dependency graph. Handler minimums cannot be loosened; executive policies can further restrict which stored roles may use a route.
          </p>
          <Input value={routeSearch} onChange={e => setRouteSearch(e.target.value)} placeholder="Search method, path, or feature…" style={{ marginBottom: "0.75rem" }} />
          <div style={{ maxHeight: 520, overflowY: "auto", border: "1px solid rgba(212,175,55,0.12)", borderRadius: 8 }}>
            {visibleRoutes.slice(0, 250).map(row => {
              const selected = row.allowed_roles || [];
              const busy = accessBusy === `route:${row.route_key}`;
              return (
                <div key={row.route_key} style={{ display: "grid", gridTemplateColumns: "minmax(220px, 1.8fr) 0.8fr 1.4fr auto", gap: "0.6rem", alignItems: "center", padding: "0.55rem 0.65rem", borderBottom: "1px solid rgba(212,175,55,0.08)" }}>
                  <span style={{ color: "#e8dfc8", fontSize: "0.7rem", fontFamily: "monospace", overflowWrap: "anywhere" }}>{row.route_key}</span>
                  <span style={{ color: "#d4af37", fontSize: "0.68rem" }}>min {row.handler_min_role}</span>
                  <Select multiple value={selected} onChange={e => setRoutePolicy(row, { allowed_roles: Array.from(e.target.selectedOptions).map(o => o.value), enabled: row.enabled })} style={{ minHeight: 42, fontSize: "0.68rem" }} aria-label={`Allowed roles for ${row.route_key}`}>
                    {ROLES.map(role => <option key={role} value={role}>{role}</option>)}
                  </Select>
                  <button onClick={() => setRoutePolicy(row, { enabled: !row.enabled, allowed_roles: row.allowed_roles })} disabled={busy} style={{ border: `1px solid ${row.enabled ? "rgba(109,189,138,0.35)" : "rgba(239,68,68,0.35)"}`, background: "transparent", color: row.enabled ? "#6dbd8a" : "#ef4444", borderRadius: 6, padding: "0.35rem 0.5rem", fontSize: "0.65rem", cursor: "pointer" }}>{busy ? "…" : row.enabled ? "ON" : "OFF"}</button>
                </div>
              );
            })}
          </div>
          {visibleRoutes.length > 250 && <div style={{ color: "#7a6e5a", fontSize: "0.7rem", marginTop: "0.5rem" }}>Showing 250 of {visibleRoutes.length}; search to narrow.</div>}
          <div style={{ marginTop: "1rem", paddingTop: "0.8rem", borderTop: "1px solid rgba(212,175,55,0.12)" }}>
            <div style={{ color: "#d4af37", fontSize: "0.7rem", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: "0.45rem" }}>Per-user route exception</div>
            <div style={ROW}>
              <Select value={userRouteForm.user_id} onChange={e => setUserRouteForm(f => ({ ...f, user_id: e.target.value }))}>
                <option value="">— choose user —</option>
                {users.map(u => <option key={u.id} value={u.id}>{u.email} ({u.role})</option>)}
              </Select>
              <Select value={userRouteForm.route_key} onChange={e => setUserRouteForm(f => ({ ...f, route_key: e.target.value }))}>
                <option value="">— choose route —</option>
                {routeAccess.map(r => <option key={r.route_key} value={r.route_key}>{r.route_key}</option>)}
              </Select>
            </div>
            <div style={{ ...ROW, marginTop: "0.65rem" }}>
              <Select value={userRouteForm.enabled ? "true" : "false"} onChange={e => setUserRouteForm(f => ({ ...f, enabled: e.target.value === "true" }))}>
                <option value="false">Deny this user</option>
                <option value="true">Allow this user</option>
              </Select>
              <Input value={userRouteForm.reason} onChange={e => setUserRouteForm(f => ({ ...f, reason: e.target.value }))} placeholder="Reason (required)" />
            </div>
            <div style={{ marginTop: "0.65rem" }}><Btn onClick={saveUserRouteOverride} busy={userRouteBusy}>Save Per-User Override</Btn></div>
          </div>
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

      {confirmBreakGlass && (
        <div style={{ position:"fixed", inset:0, zIndex:1000, display:"flex", alignItems:"center", justifyContent:"center", background:"rgba(0,0,0,0.7)", padding:16 }}>
          <div style={{ background:"#131620", border:"1px solid rgba(74,242,197,0.15)", borderRadius:12, padding:28, maxWidth:380, width:"100%" }}>
            <div style={{ color:"#f0f4ff", fontWeight:700, fontSize:15, marginBottom:10 }}>Break Glass Override</div>
            <div style={{ color:"rgba(200,210,230,0.45)", fontSize:12, marginBottom:20 }}>This activates an executive override and is fully audited. Proceed?</div>
            <div style={{ display:"flex", justifyContent:"flex-end", gap:10 }}>
              <button onClick={() => setConfirmBreakGlass(false)} style={{ border:"1px solid rgba(200,210,230,0.45)", background:"transparent", color:"rgba(200,210,230,0.45)", borderRadius:6, padding:"5px 14px", fontSize:11, fontWeight:700, cursor:"pointer" }}>Cancel</button>
              <button onClick={doActivateBreakGlass} style={{ border:"1px solid #f87171", background:"transparent", color:"#f87171", borderRadius:6, padding:"5px 14px", fontSize:11, fontWeight:700, cursor:"pointer" }}>Activate</button>
            </div>
          </div>
        </div>
      )}

      {revokeTarget && (
        <div style={{ position:"fixed", inset:0, zIndex:1000, display:"flex", alignItems:"center", justifyContent:"center", background:"rgba(0,0,0,0.7)", padding:16 }}>
          <div style={{ background:"#131620", border:"1px solid rgba(74,242,197,0.15)", borderRadius:12, padding:28, maxWidth:380, width:"100%" }}>
            <div style={{ color:"#f0f4ff", fontWeight:700, fontSize:15, marginBottom:10 }}>Revoke Override</div>
            <div style={{ color:"rgba(200,210,230,0.45)", fontSize:12, marginBottom:12 }}>Enter the reason for revoking this override:</div>
            <input
              value={revokeReason}
              onChange={e => setRevokeReason(e.target.value)}
              placeholder="Reason (required)"
              style={{ background:"#0d0d14", border:"1px solid rgba(200,210,230,0.2)", borderRadius:6, color:"#f0f4ff", fontSize:12, padding:"8px 12px", width:"100%", boxSizing:"border-box", marginBottom:20 }}
            />
            <div style={{ display:"flex", justifyContent:"flex-end", gap:10 }}>
              <button onClick={() => { setRevokeTarget(null); setRevokeReason(""); }} style={{ border:"1px solid rgba(200,210,230,0.45)", background:"transparent", color:"rgba(200,210,230,0.45)", borderRadius:6, padding:"5px 14px", fontSize:11, fontWeight:700, cursor:"pointer" }}>Cancel</button>
              <button onClick={doRevokeGlass} disabled={!revokeReason.trim()} style={{ border:"1px solid #f87171", background:"transparent", color:"#f87171", borderRadius:6, padding:"5px 14px", fontSize:11, fontWeight:700, cursor:"pointer", opacity: revokeReason.trim() ? 1 : 0.4 }}>Revoke</button>
            </div>
          </div>
        </div>
      )}

    </AppShell>
  );
}
