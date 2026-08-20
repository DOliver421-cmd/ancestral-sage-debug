/**
 * ExecBusinessOffice.jsx — THE consolidated executive control console.
 *
 * One page, every control backed by a real audited endpoint.  Modeled on the
 * Business Office structure (sections, live state, no link lists).
 *
 * ENFORCEMENT HONESTY (non-negotiable):
 *   Platform flags (ai_chat/posts/courses)      — server-side enforced (/api/ai/*, /api/more/*, /api/modules*…)
 *   Per-user feature overrides (scope=user)     — server-side enforced (backend/security/feature_control.py)
 *   feature_tier on users                       — server-side enforced (posts→Member, courses→Plus; admin/instructor bypass)
 *   Page access board                           — "ai" enforced server-side; other pages hide in the UI only
 *   AI access "all"                             — server-side enforced (ai_access_override.all)
 *   AI access per-persona / legal tools         — NOT yet enforced; intentionally not offered as working controls
 *
 * Handlers below reuse the exact endpoint shapes proven in ExecControlPanel.
 */
import { useCallback, useEffect, useState } from "react";
import AppShell from "../components/AppShell";
import { api } from "../lib/api";
import { toast } from "sonner";
import { ROLES_ALL } from "../lib/roles";

const FEATURE_TIERS = ["free", "member", "plus", "pro", "patron", "executive"];
const BUDGET_KEYS = [
  "llm_monthly_usd", "sage_tts_monthly_usd", "director_monthly_usd",
  "orchestrator_monthly_usd", "scholar_monthly_usd",
];
const VISIBILITY_FLAGS = [
  { key: "show_pricing", label: "Pricing" },
  { key: "show_legal_tools", label: "Legal Tools" },
  { key: "show_revenue_division", label: "Revenue Division" },
  { key: "show_ghost_producer", label: "Ghost Producer" },
  { key: "show_band_on_page", label: "Band on a Page" },
];

// The enforcement contract — mirrors backend/security/feature_control.py.
// feature -> { tier required, api surface enforced }
const ENFORCED_FEATURES = {
  ai_chat:  { tier: "free",   api: "/api/ai/*",        detail: "Revocable per-user" },
  posts:    { tier: "member", api: "/api/more/*",      detail: "Free users blocked server-side" },
  courses:  { tier: "plus",   api: "/api/modules*",    detail: "Instructors bypass; free/member blocked" },
};

function ago(iso) {
  if (!iso) return "";
  const s = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
  if (s < 60) return `${s}s ago`;
  if (s < 3600) return `${Math.floor(s / 60)}m ago`;
  if (s < 86400) return `${Math.floor(s / 3600)}h ago`;
  return `${Math.floor(s / 86400)}d ago`;
}

// ── Small building blocks (light, readable — no sub-13px text) ───────────────
function Section({ icon, title, sub, defaultOpen = true, children }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <section className="card-flat rounded-xl p-5 mb-5">
      <button
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-center justify-between text-left"
      >
        <div className="flex items-center gap-2.5">
          <span className="text-lg">{icon}</span>
          <h2 className="font-heading text-base font-bold text-ink">{title}</h2>
          {sub && <span className="text-xs text-ink/50 font-medium">{sub}</span>}
        </div>
        <span className="text-ink/40 text-sm">{open ? "−" : "+"}</span>
      </button>
      {sub && <p className="text-[13px] text-ink/60 mt-1.5 leading-relaxed">{sub}</p>}
      {open && <div className="mt-4">{children}</div>}
    </section>
  );
}

function Field({ label, children }) {
  return (
    <label className="block">
      <span className="block text-[13px] font-semibold text-ink/70 mb-1">{label}</span>
      {children}
    </label>
  );
}

const inputCls =
  "w-full rounded-lg border border-ink/15 bg-white px-3 py-2 text-sm text-ink outline-none focus:border-copper focus:ring-1 focus:ring-copper";

function Btn({ children, busy, danger, onClick }) {
  return (
    <button
      onClick={onClick}
      disabled={busy}
      className={`mt-3 px-4 py-2 rounded-lg text-sm font-bold transition-colors disabled:opacity-50 ${
        danger
          ? "bg-red-600 text-white hover:bg-red-700"
          : "bg-ink text-white hover:bg-ink/85"
      }`}
    >
      {busy ? "Working…" : children}
    </button>
  );
}

// ── The console ───────────────────────────────────────────────────────────────
export default function ExecBusinessOffice() {
  const { user } = useAuth();
  const [state, setState] = useState(null);
  const [audit, setAudit] = useState([]);
  const [glass, setGlass] = useState([]);
  const [users, setUsers] = useState([]);
  const [accessPages, setAccessPages] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [st, au, gl, us, ac] = await Promise.all([
        api.get("/exec/control/state"),
        api.get("/exec/control/audit?limit=30"),
        api.get("/exec/control/break-glass/active"),
        api.get("/admin/users?limit=200"),
        api.get("/exec/control/access"),
      ]);
      setState(st.data);
      setAudit(au.data?.records || au.data || []);
      setGlass(gl.data?.active_overrides || gl.data || []);
      setUsers(us.data?.users || us.data || []);
      setAccessPages(ac.data?.pages || ac.data || []);
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Failed to load executive state");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  // ── User role change ──────────────────────────────────────────────────────
  const [roleForm, setRoleForm] = useState({ user_id: "", new_role: "student", reason: "" });
  const [roleBusy, setRoleBusy] = useState(false);
  async function applyRole() {
    if (!roleForm.user_id || !roleForm.reason.trim()) return toast.error("Pick a user and add a reason");
    setRoleBusy(true);
    try {
      await api.post("/exec/control/user/role", roleForm);
      toast.success("Role updated — audited");
      setRoleForm(f => ({ ...f, reason: "" }));
      load();
    } catch (e) { toast.error(e?.response?.data?.detail || "Failed"); }
    finally { setRoleBusy(false); }
  }

  // ── User feature tier (server-side enforced) ──────────────────────────────
  const [tierForm, setTierForm] = useState({ user_id: "", new_feature_tier: "free", new_sage_tier: "", reason: "" });
  const [tierBusy, setTierBusy] = useState(false);
  async function applyTier() {
    if (!tierForm.user_id || !tierForm.reason.trim()) return toast.error("Pick a user and add a reason");
    setTierBusy(true);
    try {
      const body = { user_id: tierForm.user_id, new_feature_tier: tierForm.new_feature_tier, reason: tierForm.reason };
      if (tierForm.new_sage_tier) body.new_sage_tier = tierForm.new_sage_tier;
      await api.post("/exec/control/user/tier", body);
      toast.success(`Tier set to ${tierForm.new_feature_tier} — enforced server-side`);
      setTierForm(f => ({ ...f, reason: "" }));
      load();
    } catch (e) { toast.error(e?.response?.data?.detail || "Failed"); }
    finally { setTierBusy(false); }
  }

  // ── Platform feature flag ─────────────────────────────────────────────────
  const [flagForm, setFlagForm] = useState({ flag_name: "ai_chat", enabled: false, scope: "platform", user_id: "", reason: "" });
  const [flagBusy, setFlagBusy] = useState(false);
  async function applyFlag() {
    if (!flagForm.flag_name || !flagForm.reason.trim()) return toast.error("Pick a flag and add a reason");
    setFlagBusy(true);
    try {
      await api.post("/exec/control/feature-flag", flagForm);
      toast.success(`Flag ${flagForm.enabled ? "enabled" : "disabled"} — enforced server-side`);
      setFlagForm(f => ({ ...f, reason: "" }));
      load();
    } catch (e) { toast.error(e?.response?.data?.detail || "Failed"); }
    finally { setFlagBusy(false); }
  }

  // ── Per-user override (scope=user) — THE must-have control ────────────────
  const [userFlagForm, setUserFlagForm] = useState({ user_id: "", flag_name: "ai_chat", enabled: false, reason: "" });
  const [userFlagBusy, setUserFlagBusy] = useState(false);
  async function applyUserFlag() {
    if (!userFlagForm.user_id || !userFlagForm.reason.trim()) return toast.error("Pick a user and add a reason");
    setUserFlagBusy(true);
    try {
      await api.post("/exec/control/feature-flag", {
        flag_name: userFlagForm.flag_name, enabled: userFlagForm.enabled,
        scope: "user", user_id: userFlagForm.user_id, reason: userFlagForm.reason,
      });
      toast.success(`Per-user ${userFlagForm.enabled ? "grant" : "revoke"} applied — enforced server-side`);
      setUserFlagForm(f => ({ ...f, reason: "" }));
      load();
    } catch (e) { toast.error(e?.response?.data?.detail || "Failed"); }
    finally { setUserFlagBusy(false); }
  }

  // ── AI access (all-persona revoke/grant — enforced) ───────────────────────
  const [aiForm, setAiForm] = useState({ user_id: "", persona: "all", enabled: true, reason: "" });
  const [aiBusy, setAiBusy] = useState(false);
  async function applyAI() {
    if (!aiForm.user_id || !aiForm.reason.trim()) return toast.error("Pick a user and add a reason");
    setAiBusy(true);
    try {
      await api.post("/exec/control/ai-access", aiForm);
      toast.success(`AI access ${aiForm.enabled ? "granted" : "revoked"} for this user — enforced server-side`);
      setAiForm(f => ({ ...f, reason: "" }));
      load();
    } catch (e) { toast.error(e?.response?.data?.detail || "Failed"); }
    finally { setAiBusy(false); }
  }

  // ── Page access board ─────────────────────────────────────────────────────
  const [accessBusy, setAccessBusy] = useState(null);
  async function toggleAccess(page, currentEnabled) {
    if (!page.key) return;
    setAccessBusy(page.key);
    try {
      await api.post("/exec/control/access", {
        page: page.key, enabled: !currentEnabled,
        reason: `Toggled from Business Office by ${user?.email || user?.id}`,
      });
      toast.success(`Page "${page.key}" ${currentEnabled ? "closed" : "opened"}`);
      load();
    } catch (e) { toast.error(e?.response?.data?.detail || "Failed"); }
    finally { setAccessBusy(null); }
  }

  // ── Budgets & visibility ──────────────────────────────────────────────────
  const [budgetForm, setBudgetForm] = useState({ budget_key: BUDGET_KEYS[0], limit: "", reason: "" });
  const [budgetBusy, setBudgetBusy] = useState(false);
  async function applyBudget() {
    if (!budgetForm.limit || !budgetForm.reason.trim()) return toast.error("Enter a limit and a reason");
    setBudgetBusy(true);
    try {
      await api.post("/exec/control/budget", { ...budgetForm, limit: parseFloat(budgetForm.limit) });
      toast.success("Budget cap updated");
      setBudgetForm(f => ({ ...f, limit: "", reason: "" }));
      load();
    } catch (e) { toast.error(e?.response?.data?.detail || "Failed"); }
    finally { setBudgetBusy(false); }
  }

  const [visForm, setVisForm] = useState({ flag: VISIBILITY_FLAGS[0].key, enabled: true, reason: "" });
  const [visBusy, setVisBusy] = useState(false);
  async function applyVis() {
    if (!visForm.reason.trim()) return toast.error("Add a reason");
    setVisBusy(true);
    try {
      await api.post("/exec/control/visibility", visForm);
      toast.success(`Visibility "${visForm.flag}" → ${visForm.enabled ? "shown" : "hidden"}`);
      setVisForm(f => ({ ...f, reason: "" }));
      load();
    } catch (e) { toast.error(e?.response?.data?.detail || "Failed"); }
    finally { setVisBusy(false); }
  }

  // ── Break glass ───────────────────────────────────────────────────────────
  const [bgForm, setBgForm] = useState({ reason: "", scope: "sage_pipeline", target_uid: "", duration_minutes: 60 });
  const [bgBusy, setBgBusy] = useState(false);
  const [confirmBg, setConfirmBg] = useState(false);
  async function activateBreakGlass() {
    setBgBusy(true);
    try {
      const r = await api.post("/exec/control/break-glass/activate", bgForm);
      toast.success(`Override activated: ${r.data.override_id?.slice(0, 8)}… expires in ${bgForm.duration_minutes}m`);
      setBgForm(f => ({ ...f, reason: "" }));
      setConfirmBg(false);
      load();
    } catch (e) { toast.error(e?.response?.data?.detail || "Failed"); }
    finally { setBgBusy(false); }
  }
  async function revokeGlass(id) {
    try {
      await api.post("/exec/control/break-glass/revoke", { override_id: id, reason: `Revoked by ${user?.email || user?.id} from Business Office` });
      toast.success("Override revoked");
      load();
    } catch (e) { toast.error(e?.response?.data?.detail || "Failed"); }
  }

  const budgets = state?.budgets || [];
  const visFlags = state?.visibility_flags || [];

  return (
    <AppShell>
      <div className="max-w-5xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <div className="text-[13px] font-bold uppercase tracking-[0.15em] text-copper mb-1">Executive Console</div>
            <h1 className="font-heading text-2xl font-bold text-ink">Business Office</h1>
            <p className="text-sm text-ink/60 mt-1">
              Every control below is a live, audited action — no link lists, no placeholders.
            </p>
          </div>
          <button
            onClick={load}
            className="px-4 py-2 rounded-lg border border-ink/15 text-sm font-bold text-ink hover:bg-ink hover:text-white transition-colors"
          >
            {loading ? "Loading…" : "Refresh"}
          </button>
        </div>

        {/* Active break-glass alert */}
        {glass.length > 0 && (
          <div className="flex items-center gap-3 bg-red-50 border border-red-300 rounded-xl px-4 py-3 mb-5">
            <span className="text-red-600 font-bold text-sm">
              ⚠ {glass.length} active break-glass override{glass.length > 1 ? "s" : ""}
            </span>
            <div className="flex gap-2 flex-wrap">
              {glass.map(g => (
                <span key={g.override_id || g.id} className="inline-flex items-center gap-2 bg-white border border-red-200 rounded-lg px-3 py-1 text-[13px] text-red-700">
                  {g.scope}{g.target_uid ? ` → ${g.target_uid}` : ""} · {g.reason}
                  <button onClick={() => revokeGlass(g.override_id || g.id)} className="text-red-500 font-bold hover:text-red-700">✕</button>
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Live status strip */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
          <div className="card-flat rounded-xl p-4">
            <div className="text-[13px] font-bold uppercase tracking-wider text-ink/50">Users</div>
            <div className="text-2xl font-bold text-ink mt-1">{users.length || "—"}</div>
          </div>
          <div className="card-flat rounded-xl p-4">
            <div className="text-[13px] font-bold uppercase tracking-wider text-ink/50">Audit Events</div>
            <div className="text-2xl font-bold text-ink mt-1">{audit.length || "—"}</div>
          </div>
          <div className="card-flat rounded-xl p-4">
            <div className="text-[13px] font-bold uppercase tracking-wider text-ink/50">Budget Caps</div>
            <div className="text-2xl font-bold text-ink mt-1">{budgets.length || "0"}</div>
          </div>
          <div className="card-flat rounded-xl p-4">
            <div className="text-[13px] font-bold uppercase tracking-wider text-ink/50">Break-Glass</div>
            <div className="text-2xl font-bold mt-1" style={{ color: glass.length ? "#dc2626" : "#059669" }}>{glass.length || "0"}</div>
          </div>
        </div>

        {/* ── Users & Roles ─────────────────────────────────────────────── */}
        <Section icon="👤" title="Users & Roles" sub="Change a user's RBAC role or their feature tier. Both are enforced server-side and audited.">
          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <Field label="Select User">
                <select className={inputCls} value={roleForm.user_id} onChange={e => setRoleForm(f => ({ ...f, user_id: e.target.value }))}>
                  <option value="">— choose —</option>
                  {users.map(u => <option key={u.id} value={u.id}>{u.email} ({u.role})</option>)}
                </select>
              </Field>
              <Field label="New Role">
                <select className={inputCls} value={roleForm.new_role} onChange={e => setRoleForm(f => ({ ...f, new_role: e.target.value }))}>
                  {ROLES_ALL.map(r => <option key={r} value={r}>{r}</option>)}
                </select>
              </Field>
              <Field label="Reason (audit trail)">
                <input className={inputCls} value={roleForm.reason} onChange={e => setRoleForm(f => ({ ...f, reason: e.target.value }))} placeholder="Why is this role changing?" />
              </Field>
              <Btn onClick={applyRole} busy={roleBusy}>Apply Role Change</Btn>
            </div>
            <div>
              <Field label="Select User">
                <select className={inputCls} value={tierForm.user_id} onChange={e => setTierForm(f => ({ ...f, user_id: e.target.value }))}>
                  <option value="">— choose —</option>
                  {users.map(u => <option key={u.id} value={u.id}>{u.email} · {u.feature_tier || "free"}</option>)}
                </select>
              </Field>
              <Field label="Feature Tier (server-enforced)">
                <select className={inputCls} value={tierForm.new_feature_tier} onChange={e => setTierForm(f => ({ ...f, new_feature_tier: e.target.value }))}>
                  {FEATURE_TIERS.map(t => <option key={t} value={t}>{t}</option>)}
                </select>
              </Field>
              <Field label="Reason (audit trail)">
                <input className={inputCls} value={tierForm.reason} onChange={e => setTierForm(f => ({ ...f, reason: e.target.value }))} placeholder="Why is this tier changing?" />
              </Field>
              <Btn onClick={applyTier} busy={tierBusy}>Apply Feature Tier</Btn>
              <p className="text-[13px] text-ink/50 mt-3 leading-relaxed">
                Free users are blocked from posts &amp; courses at the API. Instructors bypass course gates; admins bypass all tier gates.
              </p>
            </div>
          </div>
        </Section>

        {/* ── Feature Controls (platform) ───────────────────────────────── */}
        <Section icon="🚦" title="Feature Controls — Platform" sub="Toggling a platform flag blocks its API surface for everyone. Every flag is enforced by the server middleware (backend/security/feature_control.py).">
          <div className="grid md:grid-cols-2 gap-6">
            <div className="space-y-2">
              {Object.entries(ENFORCED_FEATURES).map(([key, info]) => {
                const isOff = (state?.platform_flags?.flags?.[key] && state.platform_flags.flags[key].enabled === false);
                return (
                  <div key={key} className="flex items-center justify-between border border-ink/10 rounded-lg px-4 py-3 bg-white">
                    <div>
                      <div className="text-sm font-bold text-ink">{key}</div>
                      <div className="text-[13px] text-ink/50">API: {info.api} · min tier: {info.tier}</div>
                    </div>
                    <span className={`text-[13px] font-bold px-2.5 py-1 rounded-md ${isOff ? "bg-red-100 text-red-700" : "bg-green-100 text-green-700"}`}>
                      {isOff ? "DISABLED" : "ENABLED"}
                    </span>
                  </div>
                );
              })}
            </div>
            <div>
              <div className="grid grid-cols-2 gap-3">
                <Field label="Flag">
                  <select className={inputCls} value={flagForm.flag_name} onChange={e => setFlagForm(f => ({ ...f, flag_name: e.target.value }))}>
                    {Object.keys(ENFORCED_FEATURES).map(k => <option key={k} value={k}>{k}</option>)}
                  </select>
                </Field>
                <Field label="State">
                  <select className={inputCls} value={flagForm.enabled ? "true" : "false"} onChange={e => setFlagForm(f => ({ ...f, enabled: e.target.value === "true" }))}>
                    <option value="false">Disabled (blocks API)</option>
                    <option value="true">Enabled</option>
                  </select>
                </Field>
              </div>
              <Field label="Reason (audit trail)">
                <input className={inputCls} value={flagForm.reason} onChange={e => setFlagForm(f => ({ ...f, reason: e.target.value }))} placeholder="Why?" />
              </Field>
              <Btn onClick={applyFlag} busy={flagBusy}>Set Platform Flag</Btn>
            </div>
          </div>
        </Section>

        {/* ── Per-User Access — the must-have ───────────────────────────── */}
        <Section icon="🔐" title="Per-User Feature Access" sub="Grant or revoke a feature for ONE user. An explicit revoke returns 403 to that user alone; an explicit grant overrides a platform-wide disable. Enforced server-side.">
          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <Field label="Select User">
                <select className={inputCls} value={userFlagForm.user_id} onChange={e => setUserFlagForm(f => ({ ...f, user_id: e.target.value }))}>
                  <option value="">— choose —</option>
                  {users.map(u => <option key={u.id} value={u.id}>{u.email} ({u.role})</option>)}
                </select>
              </Field>
              <div className="grid grid-cols-2 gap-3 mt-3">
                <Field label="Feature">
                  <select className={inputCls} value={userFlagForm.flag_name} onChange={e => setUserFlagForm(f => ({ ...f, flag_name: e.target.value }))}>
                    {Object.keys(ENFORCED_FEATURES).map(k => <option key={k} value={k}>{k}</option>)}
                  </select>
                </Field>
                <Field label="Action">
                  <select className={inputCls} value={userFlagForm.enabled ? "true" : "false"} onChange={e => setUserFlagForm(f => ({ ...f, enabled: e.target.value === "true" }))}>
                    <option value="false">Revoke (block)</option>
                    <option value="true">Grant (allow)</option>
                  </select>
                </Field>
              </div>
              <Field label="Reason (audit trail)">
                <input className={inputCls} value={userFlagForm.reason} onChange={e => setUserFlagForm(f => ({ ...f, reason: e.target.value }))} placeholder="Why this user?" />
              </Field>
              <Btn onClick={applyUserFlag} busy={userFlagBusy}>Apply Per-User Override</Btn>
            </div>
            <div>
              <Field label="Select User">
                <select className={inputCls} value={aiForm.user_id} onChange={e => setAiForm(f => ({ ...f, user_id: e.target.value }))}>
                  <option value="">— choose —</option>
                  {users.map(u => <option key={u.id} value={u.id}>{u.email} ({u.role})</option>)}
                </select>
              </Field>
              <div className="grid grid-cols-2 gap-3 mt-3">
                <Field label="Persona">
                  <select className={inputCls} value="all" disabled>
                    <option value="all">All personas (enforced)</option>
                  </select>
                </Field>
                <Field label="Action">
                  <select className={inputCls} value={aiForm.enabled ? "true" : "false"} onChange={e => setAiForm(f => ({ ...f, enabled: e.target.value === "true" }))}>
                    <option value="true">Grant</option>
                    <option value="false">Revoke</option>
                  </select>
                </Field>
              </div>
              <Field label="Reason (audit trail)">
                <input className={inputCls} value={aiForm.reason} onChange={e => setAiForm(f => ({ ...f, reason: e.target.value }))} placeholder="Why?" />
              </Field>
              <Btn onClick={applyAI} busy={aiBusy}>Apply AI Access</Btn>
              <p className="text-[13px] text-ink/50 mt-3 leading-relaxed">
                "All personas" revokes the entire AI suite for that user (ai_access_override.all, enforced). Persona-specific toggles are intentionally not offered — they are not yet enforced server-side.
              </p>
            </div>
          </div>
        </Section>

        {/* ── Page & Feature Access board ───────────────────────────────── */}
        <Section icon="🗂️" title="Page & Feature Access Board" sub="One board for the whole site. Disabling a page hides it everywhere; the ai page is also blocked at the API. Every change is audited.">
          {accessPages.length === 0 ? (
            <p className="text-sm text-ink/50">No page-access entries returned — the board is empty or the endpoint returned none.</p>
          ) : (
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {accessPages.map(p => (
                <button
                  key={p.key}
                  onClick={() => toggleAccess(p, p.enabled)}
                  disabled={accessBusy === p.key}
                  className={`flex items-center justify-between rounded-lg border px-4 py-3 text-left transition-colors ${
                    p.enabled ? "bg-white border-green-300" : "bg-red-50 border-red-300"
                  } ${accessBusy === p.key ? "opacity-50" : ""}`}
                >
                  <span className="text-sm font-bold text-ink">{p.key}</span>
                  <span className={`text-[13px] font-bold ${p.enabled ? "text-green-700" : "text-red-700"}`}>
                    {p.enabled ? "OPEN" : "CLOSED"}
                  </span>
                </button>
              ))}
            </div>
          )}
        </Section>

        {/* ── Budgets & Visibility ──────────────────────────────────────── */}
        <Section icon="💰" title="Budgets & Visibility">
          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <Field label="Budget Key">
                <select className={inputCls} value={budgetForm.budget_key} onChange={e => setBudgetForm(f => ({ ...f, budget_key: e.target.value }))}>
                  {BUDGET_KEYS.map(k => <option key={k} value={k}>{k}</option>)}
                </select>
              </Field>
              <Field label="Monthly Limit (USD)">
                <input className={inputCls} type="number" min="0" value={budgetForm.limit} onChange={e => setBudgetForm(f => ({ ...f, limit: e.target.value }))} placeholder="e.g. 50" />
              </Field>
              <Field label="Reason (audit trail)">
                <input className={inputCls} value={budgetForm.reason} onChange={e => setBudgetForm(f => ({ ...f, reason: e.target.value }))} placeholder="Why?" />
              </Field>
              <Btn onClick={applyBudget} busy={budgetBusy}>Set Budget Cap</Btn>
              {budgets.length > 0 && (
                <div className="flex flex-wrap gap-2 mt-4">
                  {budgets.map(b => (
                    <span key={b.key} className="text-[13px] bg-ink/5 border border-ink/10 rounded-md px-2.5 py-1">
                      <b className="text-ink">{b.key}</b> <span className="text-ink/60">${b.limit}</span>
                    </span>
                  ))}
                </div>
              )}
            </div>
            <div>
              <Field label="Visibility Flag">
                <select className={inputCls} value={visForm.flag} onChange={e => setVisForm(f => ({ ...f, flag: e.target.value }))}>
                  {VISIBILITY_FLAGS.map(v => <option key={v.key} value={v.key}>{v.label}</option>)}
                </select>
              </Field>
              <Field label="State">
                <select className={inputCls} value={visForm.enabled ? "true" : "false"} onChange={e => setVisForm(f => ({ ...f, enabled: e.target.value === "true" }))}>
                  <option value="true">Show</option>
                  <option value="false">Hide</option>
                </select>
              </Field>
              <Field label="Reason (audit trail)">
                <input className={inputCls} value={visForm.reason} onChange={e => setVisForm(f => ({ ...f, reason: e.target.value }))} placeholder="Why?" />
              </Field>
              <Btn onClick={applyVis} busy={visBusy}>Set Visibility</Btn>
              {visFlags.length > 0 && (
                <div className="flex flex-wrap gap-2 mt-4">
                  {visFlags.map(v => (
                    <span key={v.flag} className={`text-[13px] border rounded-md px-2.5 py-1 ${v.enabled ? "bg-green-50 border-green-300 text-green-700" : "bg-red-50 border-red-300 text-red-700"}`}>
                      {v.enabled ? "✓" : "✕"} {v.flag}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        </Section>

        {/* ── Break Glass ───────────────────────────────────────────────── */}
        <Section icon="🧯" title="Break Glass" sub="Emergency override for a failing pipeline. Every activation is audited and auto-expires.">
          {!confirmBg ? (
            <Btn onClick={() => setConfirmBg(true)} danger>Activate Break-Glass Override</Btn>
          ) : (
            <div className="border border-red-300 bg-red-50 rounded-xl p-4">
              <p className="text-sm font-bold text-red-700 mb-3">Confirm — this bypasses normal safety gates.</p>
              <div className="grid md:grid-cols-3 gap-3">
                <Field label="Scope">
                  <select className={inputCls} value={bgForm.scope} onChange={e => setBgForm(f => ({ ...f, scope: e.target.value }))}>
                    <option value="sage_pipeline">sage_pipeline</option>
                    <option value="all_ai">all_ai</option>
                    <option value="billing">billing</option>
                  </select>
                </Field>
                <Field label="Target User (optional)">
                  <input className={inputCls} value={bgForm.target_uid} onChange={e => setBgForm(f => ({ ...f, target_uid: e.target.value }))} placeholder="user id" />
                </Field>
                <Field label="Duration (min)">
                  <input className={inputCls} type="number" min="5" value={bgForm.duration_minutes} onChange={e => setBgForm(f => ({ ...f, duration_minutes: parseInt(e.target.value) || 60 }))} />
                </Field>
              </div>
              <Field label="Reason (audit trail)">
                <input className={inputCls} value={bgForm.reason} onChange={e => setBgForm(f => ({ ...f, reason: e.target.value }))} placeholder="Emergency reason — required" />
              </Field>
              <div className="flex gap-3">
                <Btn onClick={activateBreakGlass} busy={bgBusy} danger>Confirm Activation</Btn>
                <Btn onClick={() => setConfirmBg(false)}>Cancel</Btn>
              </div>
            </div>
          )}
        </Section>

        {/* ── Audit Log ─────────────────────────────────────────────────── */}
        <Section icon="📜" title="Recent Audit Log" sub="The last 30 audited executive actions.">
          {audit.length === 0 ? (
            <p className="text-sm text-ink/50">No audit entries returned.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-ink/10 text-left text-[13px] text-ink/50 uppercase tracking-wider">
                    <th className="py-2 pr-4 font-semibold">Time</th>
                    <th className="py-2 pr-4 font-semibold">Actor</th>
                    <th className="py-2 pr-4 font-semibold">Action</th>
                    <th className="py-2 font-semibold">Detail</th>
                  </tr>
                </thead>
                <tbody>
                  {audit.map((a, i) => (
                    <tr key={a.id || i} className="border-b border-ink/5">
                      <td className="py-2 pr-4 text-[13px] text-ink/60 whitespace-nowrap">{ago(a.created_at || a.ts)}</td>
                      <td className="py-2 pr-4 text-[13px] text-ink whitespace-nowrap">{a.actor_email || a.actor || a.actor_id || "—"}</td>
                      <td className="py-2 pr-4 text-[13px] font-medium text-ink">{a.action}</td>
                      <td className="py-2 text-[13px] text-ink/60">{a.note || a.detail || ""}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Section>

        <p className="text-center text-[13px] text-ink/40 mt-8">
          Signed in as {user?.email || user?.id} · All actions audited · Enforcement: backend/security/feature_control.py
        </p>
      </div>
    </AppShell>
  );
}
