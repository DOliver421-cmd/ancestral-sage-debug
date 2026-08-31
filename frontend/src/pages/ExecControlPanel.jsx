/**
 * ExecControlPanel — Owner's Governance Console
 *
 * Every executive control surface in one clean console:
 *  1. Platform Prices   — CRUD every price the platform charges.
 *  2. Feature Tiers     — Define commercial tiers + authz matrix (which tier
 *                          unlocks which feature, server-enforced).
 *  3. Feature Flags     — Platform-wide feature toggles.
 *  4. User Controls     — Role, tier, AI access, lifecycle per user.
 *  5. Page Access       — Toggle public/role-gated page visibility.
 *
 * Design: matches the AI Business Office — BONE canvas, GREEN/GOLD/COPPER
 * accents, clean white cards, font-heading typography.
 *
 * Every toggle here is enforced server-side in security/feature_control.py
 * and routers/exec_control.py — nothing is UI-only.
 */

import { useState, useEffect, useCallback } from "react";
import AppShell from "../components/AppShell";
import { api } from "../lib/api";
import { toast } from "sonner";
import {
  DollarSign, Layers, Flag, Users, Globe,
  Plus, Save, Trash2, Shield, ChevronDown,
  RefreshCw, CheckCircle, XCircle, AlertTriangle,
  Wrench, Eye, EyeOff, Search,
} from "lucide-react";

/* ── design tokens ───────────────────────────────────────────── */
const GREEN  = "#1B4332";
const GOLD   = "#E8A51E";
const COPPER = "#C0572D";
const BONE   = "#FDFBF5";

/* ── helpers ─────────────────────────────────────────────────── */
function fmt(cents) {
  if (cents == null) return "—";
  return "$" + (cents / 100).toLocaleString("en-US", { maximumFractionDigits: 2 });
}
function ago(iso) {
  if (!iso) return "—";
  const d = Date.now() - new Date(iso).getTime();
  if (d < 60000)    return "just now";
  if (d < 3600000)  return `${Math.floor(d / 60000)}m`;
  if (d < 86400000) return `${Math.floor(d / 3600000)}h`;
  return `${Math.floor(d / 86400000)}d`;
}

const TABS = [
  { key: "prices",       label: "Prices",       icon: DollarSign },
  { key: "tiers",        label: "Feature Tiers", icon: Layers },
  { key: "flags",        label: "Feature Flags", icon: Flag },
  { key: "users",        label: "User Controls", icon: Users },
  { key: "pages",        label: "Page Access",   icon: Globe },
];

const ALL_ROLES = ["student", "instructor", "admin", "executive_admin"];
const ALL_TIERS = ["free", "member", "plus", "pro", "patron", "executive"];
const PERSONA_LIST = ["all", "jamil", "sage", "cipher", "oracle", "revenue_director", "ambassador", "architect"];

export default function ExecControlPanel() {
  const [tab, setTab] = useState("prices");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(null);

  // ── shared state ────────────────────────────────────────────
  const [prices, setPrices] = useState([]);
  const [tiers, setTiers] = useState([]);
  const [authz, setAuthz] = useState(null);
  const [flags, setFlags] = useState({});
  const [users, setUsers] = useState([]);
  const [pages, setPages] = useState([]);
  const [userSearch, setUserSearch] = useState("");

  // ── form state (prices) ─────────────────────────────────────
  const [priceForm, setPriceForm] = useState({ key: "", label: "", amount_cents: "" });
  const [priceEditId, setPriceEditId] = useState(null);

  // ── form state (tiers) ──────────────────────────────────────
  const [tierForm, setTierForm] = useState({ tier_id: "", label: "", rank: 0, description: "", color: "#b5651d", price_hint: "" });

  // ── reason field (all audited actions) ──────────────────────
  const [reason, setReason] = useState("");

  // ── load everything ─────────────────────────────────────────
  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [pR, tR, mR, cR, uR, aR] = await Promise.allSettled([
        api.get("/admin/prices"),
        api.get("/exec/control/tiers"),
        api.get("/exec/control/authz-matrix"),
        api.get("/admin/control-panel"),
        api.get("/admin/users?limit=200"),
        api.get("/exec/control/access"),
      ]);
      if (pR.status === "fulfilled") setPrices(pR.value.data?.prices || []);
      if (tR.status === "fulfilled") setTiers(tR.value.data?.tiers || []);
      if (mR.status === "fulfilled") setAuthz(mR.value.data);
      if (cR.status === "fulfilled") setFlags(cR.value.data?.platform_flags || {});
      if (uR.status === "fulfilled") setUsers(uR.value.data?.users || uR.value.data || []);
      if (aR.status === "fulfilled") setPages(aR.value.data?.pages || []);
    } catch {
      // individual errors are non-fatal
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  // ── audit reason helper ─────────────────────────────────────
  async function act(label, fn) {
    if (!reason.trim()) return toast.error("A reason is required — all exec actions are audited.");
    setBusy(label);
    try {
      await fn();
      toast.success(label + " — done.");
      setReason("");
      load();
    } catch (e) {
      toast.error(e?.response?.data?.detail || label + " failed.");
    } finally {
      setBusy(null);
    }
  }

  /* ── Prices tab ─────────────────────────────────────────────── */
  async function savePrice() {
    await act("Price saved", async () => {
      const body = {
        key: priceForm.key.trim(),
        description: priceForm.label.trim(),
        value: parseFloat(priceForm.amount_cents) || 0,
      };
      if (priceEditId) {
        await api.patch(`/admin/prices/${priceEditId}`, body);
      } else {
        await api.post("/admin/prices", body);
      }
      setPriceForm({ key: "", label: "", amount_cents: "" });
      setPriceEditId(null);
    });
  }

  async function deletePrice(id) {
    if (!window.confirm("Delete this price?")) return;
    await act("Price deleted", () => api.delete(`/admin/prices/${id}`));
  }

  function editPrice(p) {
    setPriceForm({ key: p.key, label: p.description || "", amount_cents: String(p.value) });
    setPriceEditId(p.id);
    setTab("prices");
  }

  /* ── Tiers / Authz tab ─────────────────────────────────────── */
  async function saveTier() {
    await act("Tier saved", async () => {
      await api.post("/exec/control/tiers", {
        tier_id: tierForm.tier_id.trim(),
        label: tierForm.label.trim(),
        rank: Number(tierForm.rank),
        description: tierForm.description.trim(),
        color: tierForm.color,
        price_hint: tierForm.price_hint.trim(),
      });
      setTierForm({ tier_id: "", label: "", rank: 0, description: "", color: "#b5651d", price_hint: "" });
    });
  }

  async function deleteTier(id) {
    if (!window.confirm("Delete this tier?")) return;
    await act("Tier deleted", () => api.delete(`/exec/control/tiers/${id}`));
  }

  async function setAuthzFeature(featKey, minTier) {
    await act(`AuthZ: ${featKey} → ${minTier}`, async () => {
      const map = {};
      (authz?.features || []).forEach(f => { map[f.key] = f.min_tier; });
      map[featKey] = minTier;
      await api.post("/exec/control/authz-matrix", { requirements: map });
    });
  }

  /* ── Feature Flags tab ─────────────────────────────────────── */
  async function toggleFlag(flagName, enabled) {
    await act(`Flag ${flagName} ${enabled ? "enabled" : "disabled"}`, async () => {
      await api.post("/exec/control/feature-flag", {
        flag_name: flagName, enabled, scope: "platform", reason: reason,
      });
    });
  }

  async function togglePage(pageKey, enabled) {
    await act(`Page ${pageKey} ${enabled ? "enabled" : "disabled"}`, async () => {
      await api.post("/exec/control/access", {
        page: pageKey, enabled, reason: reason,
      });
    });
  }

  /* ── User Controls tab ─────────────────────────────────────── */
  const [selectedUser, setSelectedUser] = useState(null);

  async function setUserRole(uid, role) {
    await act(`User role → ${role}`, () =>
      api.post("/exec/control/user/role", { user_id: uid, new_role: role, reason }));
  }

  async function setUserTier(uid, tier) {
    await act(`User tier → ${tier}`, () =>
      api.post("/exec/control/user/tier", { user_id: uid, new_feature_tier: tier, reason }));
  }

  async function setUserAI(uid, persona, enabled) {
    await act(`AI access ${enabled ? "granted" : "revoked"}`, () =>
      api.post("/exec/control/ai-access", { user_id: uid, persona, enabled, reason }));
  }

  async function toggleUserActive(uid, isActive) {
    const label = isActive ? "Activate" : "Deactivate";
    await act(label + " user", () =>
      api.patch(`/admin/users/${uid}/active`, { is_active: !isActive }));
  }

  const filteredUsers = users.filter(u =>
    !userSearch || u.email?.includes(userSearch) || u.full_name?.toLowerCase().includes(userSearch.toLowerCase())
  );

  /* ── render ────────────────────────────────────────────────── */
  if (loading) {
    return (
      <AppShell>
        <div className="p-12 text-black font-heading">Loading executive controls…</div>
      </AppShell>
    );
  }

  const TabIcon = TABS.find(t => t.key === tab)?.icon || Wrench;

  return (
    <AppShell>
      <div style={{ background: BONE, minHeight: "100vh" }}>
        {/* ── Header ─────────────────────────────────────────── */}
        <div style={{ background: `linear-gradient(135deg, ${GREEN}, #2D6A4F)`, padding: "32px 32px 0", color: "#fff" }}>
          <div className="flex items-center gap-3 mb-2">
            <Shield size={28} />
            <h1 className="font-heading text-2xl font-bold tracking-tight">Executive Governance Console</h1>
            <span className="text-[10px] font-black uppercase tracking-widest px-2 py-1 rounded" style={{ background: GOLD, color: "#0a0a0a" }}>
              Owner Controls
            </span>
          </div>
          {/* ── Tabs ─────────────────────────────────────── */}
          <div className="flex flex-wrap gap-1 mt-5 -mb-px">
            {TABS.map(t => (
              <button key={t.key} onClick={() => setTab(t.key)}
                className="flex items-center gap-1.5 px-4 py-3 text-sm font-bold rounded-t-lg transition-colors"
                style={{
                  background: tab === t.key ? BONE : "transparent",
                  color: tab === t.key ? GREEN : "rgba(255,255,255,0.8)",
                  border: tab === t.key ? `1px solid ${BONE}` : "1px solid transparent",
                  borderBottom: tab === t.key ? `1px solid ${BONE}` : "1px solid transparent",
                }}>
                <t.icon size={15} /> {t.label}
              </button>
            ))}
          </div>
        </div>

        <div className="max-w-6xl mx-auto px-6 py-8 space-y-10">
          {/* ── Reason bar (shared) ────────────────────────── */}
          <div className="flex items-center gap-3 bg-white rounded-xl p-3 border border-slate-200 shadow-sm">
            <span className="text-xs font-black uppercase tracking-widest text-slate-500 whitespace-nowrap">Audit Reason</span>
            <input
              value={reason}
              onChange={e => setReason(e.target.value)}
              placeholder="Required — every exec action is audited…"
              className="flex-1 text-sm px-3 py-1.5 border-0 outline-none bg-transparent font-medium"
            />
            <button onClick={load} className="flex items-center gap-1 text-xs font-bold px-3 py-1.5 rounded-lg bg-slate-100 text-slate-600 hover:bg-slate-200 transition-colors">
              <RefreshCw size={13} /> Refresh
            </button>
          </div>

          {/* ═══════════════ TAB: PRICES ═══════════════════════ */}
          {tab === "prices" && (
            <section>
              {/* ── New / Edit price form ─────────────────── */}
              <div className="bg-white rounded-2xl p-6 border border-slate-100 shadow-sm mb-6">
                <h2 className="font-heading text-lg font-bold text-black flex items-center gap-2 mb-4">
                  <DollarSign size={18} style={{ color: GOLD }} />
                  {priceEditId ? "Edit Price" : "Add Price"}
                </h2>
                <div className="grid sm:grid-cols-4 gap-3">
                  <input value={priceForm.key} onChange={e => setPriceForm({...priceForm, key: e.target.value})}
                    placeholder="Key (e.g., monthly_basic)" className="text-sm px-3 py-2 rounded-lg border border-slate-200 outline-none focus:border-amber-400" />
                  <input value={priceForm.label} onChange={e => setPriceForm({...priceForm, label: e.target.value})}
                    placeholder="Label (e.g., Basic Monthly)" className="text-sm px-3 py-2 rounded-lg border border-slate-200 outline-none focus:border-amber-400" />
                  <input value={priceForm.amount_cents} onChange={e => setPriceForm({...priceForm, amount_cents: e.target.value})}
                    placeholder="Price in cents (e.g., 999)" type="number" className="text-sm px-3 py-2 rounded-lg border border-slate-200 outline-none focus:border-amber-400" />
                  <button onClick={savePrice} disabled={busy === "Price saved"}
                    className="font-bold text-sm px-4 py-2 rounded-lg text-white flex items-center justify-center gap-1.5 transition-opacity"
                    style={{ background: GREEN, opacity: busy === "Price saved" ? 0.6 : 1 }}>
                    {priceEditId ? <Save size={15} /> : <Plus size={15} />}
                    {priceEditId ? "Update" : "Create"}
                  </button>
                </div>
                {priceEditId && (
                  <button onClick={() => { setPriceEditId(null); setPriceForm({ key: "", label: "", amount_cents: "" }); }}
                    className="text-xs text-slate-500 mt-3 underline">Cancel edit</button>
                )}
              </div>

              {/* ── Price table ──────────────────────────────── */}
              <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b-2 border-slate-100 bg-slate-50">
                      <th className="text-left py-3 px-4 text-xs uppercase tracking-wider text-slate-600 font-bold">Key</th>
                      <th className="text-left py-3 px-4 text-xs uppercase tracking-wider text-slate-600 font-bold">Label</th>
                      <th className="text-right py-3 px-4 text-xs uppercase tracking-wider text-slate-600 font-bold">Price</th>
                      <th className="text-right py-3 px-4 text-xs uppercase tracking-wider text-slate-600 font-bold">Last Modified</th>
                      <th className="py-3 px-4" />
                    </tr>
                  </thead>
                  <tbody>
                    {prices.length === 0 && (
                      <tr><td colSpan={5} className="py-8 text-center text-slate-500">No prices configured yet.</td></tr>
                    )}
                    {prices.map(p => (
                      <tr key={p.id} className="border-b border-slate-50 hover:bg-slate-50 transition-colors">
                        <td className="py-3 px-4 font-mono font-bold text-slate-700">{p.key}</td>
                        <td className="py-3 px-4 text-slate-600">{p.description || "—"}</td>
                        <td className="py-3 px-4 text-right font-heading font-bold" style={{ color: GREEN }}>
                          {p.value != null ? `$${(p.value).toFixed(2)}` : "—"}
                        </td>
                        <td className="py-3 px-4 text-right text-xs text-slate-500">{ago(p.last_modified_at)}</td>
                        <td className="py-3 px-4 text-right">
                          <button onClick={() => editPrice(p)} className="text-xs font-bold px-2 py-1 rounded text-slate-600 hover:bg-slate-200">Edit</button>
                          <button onClick={() => deletePrice(p.id)} className="text-xs font-bold px-2 py-1 rounded text-red-600 hover:bg-red-50 ml-1">Delete</button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          )}

          {/* ═══════════════ TAB: FEATURE TIERS ══════════════════ */}
          {tab === "tiers" && (
            <>
              {/* ── Tier definitions ──────────────────────────── */}
              <section>
                <h2 className="font-heading text-lg font-bold text-black flex items-center gap-2 mb-4">
                  <Layers size={18} style={{ color: GOLD }} /> Tier Definitions
                </h2>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
                  {tiers.map(t => (
                    <div key={t.tier_id} className="bg-white rounded-2xl p-5 border border-slate-100 shadow-sm relative">
                      <div className="flex items-center gap-2 mb-2">
                        <div className="w-3 h-3 rounded-full" style={{ background: t.color }} />
                        <span className="font-heading font-bold text-slate-800">{t.label}</span>
                        <span className="text-[10px] font-mono text-slate-400 ml-auto">rank {t.rank}</span>
                      </div>
                      <div className="text-xs text-slate-600 mb-1">{t.description || "—"}</div>
                      <div className="text-xs font-bold" style={{ color: GREEN }}>{t.price_hint || "—"}</div>
                      <div className="text-[10px] font-mono text-slate-400">{t.tier_id}</div>
                      {!["free","member","plus","pro","patron","executive"].includes(t.tier_id) && (
                        <button onClick={() => deleteTier(t.tier_id)} className="absolute top-3 right-3 text-red-400 hover:text-red-600">
                          <Trash2 size={14} />
                        </button>
                      )}
                    </div>
                  ))}
                </div>

                {/* ── Add custom tier ──────────────────────── */}
                <div className="bg-white rounded-2xl p-6 border border-slate-100 shadow-sm mb-8">
                  <h3 className="font-heading font-bold text-black mb-3">Add Custom Tier</h3>
                  <div className="grid sm:grid-cols-6 gap-3">
                    <input value={tierForm.tier_id} onChange={e => setTierForm({...tierForm, tier_id: e.target.value})}
                      placeholder="tier_id" className="text-sm px-3 py-2 rounded-lg border border-slate-200 outline-none focus:border-amber-400 col-span-1" />
                    <input value={tierForm.label} onChange={e => setTierForm({...tierForm, label: e.target.value})}
                      placeholder="Label" className="text-sm px-3 py-2 rounded-lg border border-slate-200 outline-none focus:border-amber-400 col-span-1" />
                    <input value={tierForm.rank} onChange={e => setTierForm({...tierForm, rank: e.target.value})}
                      placeholder="Rank" type="number" className="text-sm px-3 py-2 rounded-lg border border-slate-200 outline-none focus:border-amber-400" />
                    <input value={tierForm.price_hint} onChange={e => setTierForm({...tierForm, price_hint: e.target.value})}
                      placeholder="Price hint" className="text-sm px-3 py-2 rounded-lg border border-slate-200 outline-none focus:border-amber-400" />
                    <input value={tierForm.color} onChange={e => setTierForm({...tierForm, color: e.target.value})}
                      placeholder="#color" className="text-sm px-3 py-2 rounded-lg border border-slate-200 outline-none focus:border-amber-400" />
                    <button onClick={saveTier} disabled={busy === "Tier saved"}
                      className="font-bold text-sm px-3 py-2 rounded-lg text-white flex items-center justify-center gap-1"
                      style={{ background: GREEN, opacity: busy === "Tier saved" ? 0.6 : 1 }}>
                      <Plus size={15} /> Add
                    </button>
                  </div>
                  <input value={tierForm.description} onChange={e => setTierForm({...tierForm, description: e.target.value})}
                    placeholder="Description" className="text-sm px-3 py-2 rounded-lg border border-slate-200 outline-none focus:border-amber-400 w-full mt-3" />
                </div>
              </section>

              {/* ── Authorization matrix ───────────────────── */}
              <section>
                <h2 className="font-heading text-lg font-bold text-black flex items-center gap-2 mb-4">
                  <Shield size={18} style={{ color: COPPER }} /> Authorization Matrix
                </h2>
                <p className="text-xs text-slate-600 mb-4">
                  Minimum feature tier required per capability. Server-enforced — changing a value here immediately gates the API.
                </p>
                <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b-2 border-slate-100 bg-slate-50">
                        <th className="text-left py-3 px-4 text-xs uppercase tracking-wider text-slate-600 font-bold">Feature</th>
                        <th className="text-left py-3 px-4 text-xs uppercase tracking-wider text-slate-600 font-bold">API surface</th>
                        {ALL_TIERS.map(tr => (
                          <th key={tr} className="text-center py-3 px-3 text-[10px] uppercase tracking-wider text-slate-600 font-bold">{tr}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {(authz?.features || []).map(f => (
                        <tr key={f.key} className="border-b border-slate-50 hover:bg-slate-50 transition-colors">
                          <td className="py-2.5 px-4 font-bold text-slate-700">{f.label}</td>
                          <td className="py-2.5 px-4 font-mono text-[10px] text-slate-500">{f.api}</td>
                          {ALL_TIERS.map(tr => {
                            const isSet = f.min_tier === tr;
                            const rank = authz?.tier_ranks?.[tr] ?? (ALL_TIERS.indexOf(tr));
                            const minRank = authz?.tier_ranks?.[f.min_tier] ?? 0;
                            const isGrey = rank < minRank;
                            return (
                              <td key={tr} className="text-center py-2.5 px-1">
                                <button onClick={() => setAuthzFeature(f.key, tr)}
                                  className="w-7 h-7 rounded-full text-xs font-bold transition-all"
                                  style={{
                                    background: isSet ? GOLD : isGrey ? "#f1f5f9" : "#e2e8f0",
                                    color: isSet ? "#0a0a0a" : "#94a3b8",
                                    border: isSet ? `2px solid ${GOLD}` : "2px solid transparent",
                                  }}
                                  title={`Set ${f.label} → ${tr}`}>
                                  {isSet ? "●" : "○"}
                                </button>
                              </td>
                            );
                          })}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>
            </>
          )}

          {/* ═══════════════ TAB: FEATURE FLAGS ═══════════════════ */}
          {tab === "flags" && (
            <section>
              <h2 className="font-heading text-lg font-bold text-black flex items-center gap-2 mb-4">
                <Flag size={18} style={{ color: GOLD }} /> Platform Feature Flags
              </h2>
              <p className="text-xs text-slate-600 mb-4">
                Toggle platform-wide features. Disabling a flag blocks its API routes server-side via feature_control.py.
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {Object.entries(flags).map(([key, val]) => {
                  const enabled = val?.enabled !== false; // absent = allowed
                  return (
                    <div key={key} className="bg-white rounded-2xl p-5 border border-slate-100 shadow-sm flex items-center justify-between">
                      <div>
                        <div className="font-heading font-bold text-slate-800 text-sm">{key}</div>
                        <div className="text-[10px] text-slate-500 mt-0.5">
                          {enabled ? "Active" : "Disabled"} · updated {ago(val?.updated_at)}
                        </div>
                      </div>
                      <button onClick={() => toggleFlag(key, !enabled)} disabled={busy}
                        className="px-3 py-1.5 rounded-lg text-xs font-bold transition-all"
                        style={{
                          background: enabled ? "#dcfce7" : "#fee2e2",
                          color: enabled ? GREEN : "#dc2626",
                        }}>
                        {enabled ? <Eye size={14} /> : <EyeOff size={14} />}
                      </button>
                    </div>
                  );
                })}
                {Object.keys(flags).length === 0 && (
                  <div className="col-span-full text-center text-slate-500 py-8">No platform flags registered yet.</div>
                )}
              </div>
            </section>
          )}

          {/* ═══════════════ TAB: USER CONTROLS ═══════════════════ */}
          {tab === "users" && (
            <section>
              <h2 className="font-heading text-lg font-bold text-black flex items-center gap-2 mb-4">
                <Users size={18} style={{ color: GOLD }} /> User Controls
              </h2>
              {/* ── Search ─────────────────────────────────── */}
              <div className="bg-white rounded-2xl p-4 border border-slate-100 shadow-sm mb-4 flex items-center gap-3">
                <Search size={16} className="text-slate-400" />
                <input value={userSearch} onChange={e => setUserSearch(e.target.value)}
                  placeholder="Search by email or name…" className="flex-1 text-sm outline-none" />
              </div>

              <div className="grid lg:grid-cols-3 gap-6">
                {/* ── User list ──────────────────────────────── */}
                <div className="lg:col-span-1 bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden" style={{ maxHeight: "70vh" }}>
                  <div className="overflow-y-auto h-full">
                    {filteredUsers.slice(0, 100).map(u => (
                      <button key={u.id || u.email}
                        onClick={() => setSelectedUser(u)}
                        className="w-full text-left px-4 py-3 border-b border-slate-50 hover:bg-slate-50 transition-colors flex items-center justify-between"
                        style={{ background: selectedUser?.id === u.id ? "#fef3c7" : "transparent" }}>
                        <div>
                          <div className="text-sm font-bold text-slate-800">{u.full_name || u.email}</div>
                          <div className="text-[10px] font-mono text-slate-400">{u.email}</div>
                        </div>
                        <div className="flex items-center gap-1.5">
                          <span className="text-[9px] font-black uppercase px-1.5 py-0.5 rounded"
                            style={{ background: u.role === "executive_admin" ? "#fee2e2" : "#e2e8f0", color: u.role === "executive_admin" ? "#dc2626" : "#475569" }}>
                            {u.role}
                          </span>
                          {u.is_active === false && (
                            <XCircle size={12} className="text-red-500" />
                          )}
                        </div>
                      </button>
                    ))}
                  </div>
                </div>

                {/* ── User detail + controls ──────────────────── */}
                <div className="lg:col-span-2 space-y-6">
                  {!selectedUser ? (
                    <div className="bg-white rounded-2xl p-12 border border-slate-100 shadow-sm text-center text-slate-500">
                      Select a user to manage their role, tier, and access.
                    </div>
                  ) : (
                    <>
                      {/* User info card */}
                      <div className="bg-white rounded-2xl p-6 border border-slate-100 shadow-sm">
                        <div className="flex items-center justify-between mb-4">
                          <div>
                            <h3 className="font-heading font-bold text-lg text-black">
                              {selectedUser.full_name}
                            </h3>
                            <div className="text-sm text-slate-500 font-mono">{selectedUser.email}</div>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className={`text-[10px] font-black uppercase px-2 py-1 rounded ${
                              selectedUser.is_active !== false ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"
                            }`}>
                              {selectedUser.is_active !== false ? "Active" : "Deactivated"}
                            </span>
                            <button onClick={() => toggleUserActive(selectedUser.id, selectedUser.is_active !== false)}
                              className="text-xs font-bold px-3 py-1.5 rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-100">
                              {selectedUser.is_active !== false ? "Deactivate" : "Activate"}
                            </button>
                          </div>
                        </div>
                        <div className="grid grid-cols-3 gap-3 text-xs">
                          <div><span className="text-slate-400">Role:</span> <span className="font-bold">{selectedUser.role}</span></div>
                          <div><span className="text-slate-400">Tier:</span> <span className="font-bold">{selectedUser.feature_tier || "free"}</span></div>
                          <div><span className="text-slate-400">Joined:</span> <span className="font-bold">{ago(selectedUser.created_at)}</span></div>
                        </div>
                      </div>

                      {/* Role */}
                      <div className="bg-white rounded-2xl p-6 border border-slate-100 shadow-sm">
                        <h4 className="font-heading font-bold text-sm text-black mb-3">Change Role</h4>
                        <div className="flex flex-wrap gap-2">
                          {ALL_ROLES.map(r => (
                            <button key={r} onClick={() => setUserRole(selectedUser.id, r)} disabled={busy}
                              className="px-4 py-2 rounded-lg text-xs font-bold transition-all"
                              style={{
                                background: selectedUser.role === r ? GOLD : "#f1f5f9",
                                color: selectedUser.role === r ? "#0a0a0a" : "#64748b",
                              }}>
                              {r.replace("_", " ")}
                            </button>
                          ))}
                        </div>
                      </div>

                      {/* Feature Tier */}
                      <div className="bg-white rounded-2xl p-6 border border-slate-100 shadow-sm">
                        <h4 className="font-heading font-bold text-sm text-black mb-3">Change Feature Tier</h4>
                        <div className="flex flex-wrap gap-2">
                          {tiers.map(t => (
                            <button key={t.tier_id} onClick={() => setUserTier(selectedUser.id, t.tier_id)} disabled={busy}
                              className="px-4 py-2 rounded-lg text-xs font-bold transition-all"
                              style={{
                                background: (selectedUser.feature_tier || "free") === t.tier_id ? t.color : "#f1f5f9",
                                color: (selectedUser.feature_tier || "free") === t.tier_id ? "#fff" : "#64748b",
                              }}>
                              {t.label}
                            </button>
                          ))}
                        </div>
                      </div>

                      {/* AI Access */}
                      <div className="bg-white rounded-2xl p-6 border border-slate-100 shadow-sm">
                        <h4 className="font-heading font-bold text-sm text-black mb-3">AI Access</h4>
                        <div className="flex flex-wrap gap-2">
                          {PERSONA_LIST.map(p => (
                            <button key={p} onClick={() => setUserAI(selectedUser.id, p, true)} disabled={busy}
                              className="px-3 py-1.5 rounded-lg text-xs font-bold bg-green-50 text-green-700 hover:bg-green-100 transition-colors">
                              <CheckCircle size={12} className="inline mr-1" /> {p}
                            </button>
                          ))}
                          <button onClick={() => setUserAI(selectedUser.id, "all", false)} disabled={busy}
                            className="px-3 py-1.5 rounded-lg text-xs font-bold bg-red-50 text-red-600 hover:bg-red-100 transition-colors">
                            <XCircle size={12} className="inline mr-1" /> Revoke all
                          </button>
                        </div>
                      </div>
                    </>
                  )}
                </div>
              </div>
            </section>
          )}

          {/* ═══════════════ TAB: PAGE ACCESS ════════════════════ */}
          {tab === "pages" && (
            <section>
              <h2 className="font-heading text-lg font-bold text-black flex items-center gap-2 mb-4">
                <Globe size={18} style={{ color: GOLD }} /> Page Access
              </h2>
              <p className="text-xs text-slate-600 mb-4">
                Toggle public visibility of pages and set allowed roles. Changes take effect server-side.
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {pages.map(p => {
                  const enabled = p.enabled !== false;
                  return (
                    <div key={p.key || p.page} className="bg-white rounded-2xl p-5 border border-slate-100 shadow-sm flex items-center justify-between">
                      <div>
                        <div className="font-heading font-bold text-slate-800 text-sm">{p.label || p.page}</div>
                        <div className="text-[10px] font-mono text-slate-400">{p.path || p.key}</div>
                        {p.allowed_roles?.length > 0 && (
                          <div className="flex gap-1 mt-1.5">
                            {p.allowed_roles.map(r => (
                              <span key={r} className="text-[9px] px-1.5 py-0.5 rounded bg-slate-100 text-slate-600 font-bold">{r}</span>
                            ))}
                          </div>
                        )}
                      </div>
                      <button onClick={() => togglePage(p.key || p.page, !enabled)} disabled={busy}
                        className="px-3 py-1.5 rounded-lg text-xs font-bold transition-all"
                        style={{
                          background: enabled ? "#dcfce7" : "#fee2e2",
                          color: enabled ? GREEN : "#dc2626",
                        }}>
                        {enabled ? <Eye size={14} /> : <EyeOff size={14} />}
                      </button>
                    </div>
                  );
                })}
                {pages.length === 0 && (
                  <div className="col-span-full text-center text-slate-500 py-8">No page access records found.</div>
                )}
              </div>
            </section>
          )}
        </div>
      </div>
    </AppShell>
  );
}