import { useEffect, useState } from "react";
import AppShell from "../components/AppShell";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import { DollarSign, Key, Shield, BookOpen, Clock, Users, FileText, Building, Plus, X, Check, Copy, ExternalLink, RefreshCw, TrendingUp, Zap, CreditCard } from "lucide-react";
import { toast } from "sonner";

export default function RevenueDivision() {
  const { user } = useAuth();
  const isExec = user?.role === "executive_admin";
  const [tab, setTab] = useState(isExec ? "overview" : "keys");
  const [keys, setKeys] = useState([]);
  const [tiers, setTiers] = useState({});
  const [showCreateKey, setShowCreateKey] = useState(false);
  const [newKeyLabel, setNewKeyLabel] = useState("");
  const [newKeyTier, setNewKeyTier] = useState("free");
  const [newKeyResult, setNewKeyResult] = useState(null);
  const [busy, setBusy] = useState(false);
  const [freshKey, setFreshKey] = useState(null);
  const [revokeTarget, setRevokeTarget] = useState(null);
  const [confirmPayouts, setConfirmPayouts] = useState(false);

  const [licenses, setLicenses] = useState([]);
  const [publicCourses, setPublicCourses] = useState([]);

  const [compliance, setCompliance] = useState(null);
  const [associateFilter, setAssociateFilter] = useState("");

  const [workspaces, setWorkspaces] = useState([]);
  const [wsName, setWsName] = useState("");

  const [resume, setResume] = useState(null);
  const [overview, setOverview] = useState(null);
  const [overviewBusy, setOverviewBusy] = useState(false);
  const [payoutBusy, setPayoutBusy] = useState(false);

  useEffect(() => {
    if (isExec) loadOverview();
    loadKeys();
    api.get("/revenue/api-keys/tiers").then(r => setTiers(r.data.tiers || {})).catch(() => {});
    api.get("/revenue/courses/public").then(r => setPublicCourses(r.data.courses || [])).catch(() => {});
    api.get("/revenue/courses/my-licenses").then(r => setLicenses(r.data.licenses || [])).catch(() => {});
    loadWorkspaces();
    loadResume();
  }, []);

  const loadKeys = async () => {
    try { const r = await api.get("/revenue/api-keys"); setKeys(r.data.keys || []); } catch {}
  };

  const loadWorkspaces = async () => {
    if (user?.role === "admin" || user?.role === "executive_admin") {
      try { const r = await api.get("/revenue/sovereign/workspaces"); setWorkspaces(r.data.workspaces || []); } catch {}
    }
  };

  const loadResume = async () => {
    try { const r = await api.get("/revenue/resume/preview"); setResume(r.data); } catch {}
  };

  const loadOverview = async () => {
    setOverviewBusy(true);
    try { const r = await api.get("/revenue/exec-overview"); setOverview(r.data); }
    catch { toast.error("Failed to load revenue overview."); }
    finally { setOverviewBusy(false); }
  };

  const processPayouts = () => {
    setConfirmPayouts(true);
  };

  const doProcessPayouts = async () => {
    setConfirmPayouts(false);
    setPayoutBusy(true);
    try {
      const r = await api.post("/admin/creator-payouts/process");
      toast.success(`${r.data.payouts_initiated} payout(s) initiated.`);
      loadOverview();
    } catch (err) { toast.error(err?.response?.data?.detail || "Payout processing failed."); }
    finally { setPayoutBusy(false); }
  };

  const fmtUSD = (cents) => `$${(cents / 100).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

  const loadCompliance = async () => {
    setBusy(true);
    try {
      const r = await api.get(`/revenue/employer/compliance?associate=${associateFilter}`);
      setCompliance(r.data);
    } catch { toast.error("Failed to load compliance data."); }
    finally { setBusy(false); }
  };

  const createKey = async (e) => {
    e.preventDefault();
    try {
      const r = await api.post("/revenue/api-keys", { label: newKeyLabel, tier: newKeyTier });
      setFreshKey(r.data.key);
      setNewKeyResult(r.data);
      setShowCreateKey(false);
      setNewKeyLabel("");
      loadKeys();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Failed to create key");
    }
  };

  const revokeKey = async (hash) => {
    try {
      await api.delete(`/revenue/api-keys/${hash}`);
      toast.success("Key revoked.");
      setRevokeTarget(null);
      loadKeys();
    } catch { toast.error("Failed to revoke key."); }
  };

  const createLicense = async (e) => {
    e.preventDefault();
    const form = e.target;
    try {
      const r = await api.post("/revenue/courses/license", {
        organization: form.org.value,
        course_slugs: Array.from(form.querySelectorAll("[name=courses]:checked")).map(c => c.value),
        seats: parseInt(form.seats.value) || 1,
      });
      toast.success(`License created: ${r.data.license_id.slice(0, 8)}...`);
      const lic = await api.get("/revenue/courses/my-licenses");
      setLicenses(lic.data.licenses || []);
    } catch (err) { toast.error(err?.response?.data?.detail || "License failed."); }
  };

  const createWorkspace = async (e) => {
    e.preventDefault();
    try {
      await api.post("/revenue/sovereign/workspace", { name: wsName, member_ids: [] });
      toast.success("Workspace created.");
      setWsName("");
      loadWorkspaces();
    } catch (err) { toast.error(err?.response?.data?.detail || "Failed."); }
  };

  const TabBtn = ({ id, icon: Icon, children }) => (
    <button
      onClick={() => setTab(id)}
      className={`px-4 py-2 text-sm font-bold border-b-2 inline-flex items-center gap-2 transition-colors ${
        tab === id ? "border-copper text-ink" : "border-transparent text-ink/50 hover:text-ink"
      }`}
    ><Icon className="w-4 h-4" /> {children}</button>
  );

  return (
    <AppShell>
      <div className="px-10 py-10 max-w-6xl">
        <div className="flex items-center gap-3 mb-2">
          <DollarSign className="w-6 h-6 text-copper" />
          <span className="overline text-copper">Revenue Division</span>
        </div>
        <h1 className="font-heading text-4xl font-bold">AI Revenue Operations</h1>
        <p className="text-ink/60 mt-2">API keys, credential verification, course licensing, compliance tracking, Sovereign workspaces, and resume builder.</p>

        {/* Tabs */}
        <div className="mt-8 flex gap-1 border-b border-ink/10 overflow-x-auto" role="tablist">
          {isExec && <TabBtn id="overview" icon={TrendingUp}>Revenue Overview</TabBtn>}
          <TabBtn id="keys" icon={Key}>API Keys</TabBtn>
          <TabBtn id="verify" icon={Shield}>Verification</TabBtn>
          <TabBtn id="courses" icon={BookOpen}>Course Licensing</TabBtn>
          <TabBtn id="compliance" icon={Clock}>Compliance</TabBtn>
          <TabBtn id="sovereign" icon={Users}>Sovereign Seats</TabBtn>
          <TabBtn id="resume" icon={FileText}>Resume Builder</TabBtn>
        </div>

        {/* ── REVENUE OVERVIEW (exec only) ─────────────────────────────────────── */}
        {tab === "overview" && isExec && (
          <div className="mt-6 space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="font-heading text-2xl font-bold">Revenue Overview</h2>
              <button onClick={loadOverview} disabled={overviewBusy}
                className="text-sm text-ink/50 hover:text-ink inline-flex items-center gap-1">
                <RefreshCw className={`w-4 h-4 ${overviewBusy ? "animate-spin" : ""}`} /> Refresh
              </button>
            </div>

            {overview ? (<>
              {/* $8k/month progress */}
              <div className="bg-white rounded-2xl border border-ink/10 p-6">
                <div className="flex items-center justify-between mb-2">
                  <div>
                    <p className="text-xs font-bold uppercase text-ink/50">Monthly Revenue Goal</p>
                    <p className="text-3xl font-bold font-mono text-ink mt-1">{fmtUSD(overview.goal.month_cents)}</p>
                    <p className="text-xs text-ink/40 mt-0.5">of {fmtUSD(overview.goal.monthly_target_cents)} target</p>
                  </div>
                  <div className="text-right">
                    <p className="text-5xl font-bold font-mono" style={{ color: overview.goal.progress_pct >= 100 ? "#16a34a" : overview.goal.progress_pct >= 60 ? "#d97706" : "#dc2626" }}>
                      {overview.goal.progress_pct}%
                    </p>
                  </div>
                </div>
                <div className="h-4 bg-ink/10 rounded-full overflow-hidden mt-4">
                  <div className="h-full rounded-full transition-all duration-700"
                    style={{
                      width: `${Math.min(overview.goal.progress_pct, 100)}%`,
                      background: overview.goal.progress_pct >= 100 ? "#16a34a" : overview.goal.progress_pct >= 60 ? "#d97706" : "#dc2626",
                    }} />
                </div>
                <div className="flex justify-between text-xs text-ink/40 mt-2">
                  <span>Today: {fmtUSD(overview.goal.today_cents)}</span>
                  <span>All-time: {fmtUSD(overview.goal.alltime_cents)}</span>
                </div>
              </div>

              {/* Stats row */}
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="bg-white rounded-xl border border-ink/10 p-5 text-center">
                  <p className="text-xs text-ink/50 uppercase">Active Subs</p>
                  <p className="text-2xl font-bold font-mono text-ink">{overview.subscriptions.active}</p>
                  <p className="text-xs text-ink/30">{overview.subscriptions.canceled} canceled</p>
                </div>
                <div className="bg-white rounded-xl border border-ink/10 p-5 text-center">
                  <p className="text-xs text-ink/50 uppercase">Creators Owed</p>
                  <p className="text-2xl font-bold font-mono text-ink">{overview.creator_payouts.creators_pending}</p>
                  <p className="text-xs text-ink/30">{fmtUSD(overview.creator_payouts.total_pending_cents)} pending</p>
                </div>
                <div className="bg-white rounded-xl border border-ink/10 p-5 text-center">
                  <p className="text-xs text-ink/50 uppercase">AI Spend / Month</p>
                  <p className="text-2xl font-bold font-mono text-ink">${overview.ai_spend.month_usd.toFixed(2)}</p>
                  <p className="text-xs text-ink/30">{overview.ai_spend.calls_month.toLocaleString()} calls</p>
                </div>
                <div className="bg-white rounded-xl border border-ink/10 p-5 text-center">
                  <p className="text-xs text-ink/50 uppercase">Revenue Share</p>
                  <p className="text-2xl font-bold font-mono text-ink">70/30</p>
                  <p className="text-xs text-ink/30">creator / platform</p>
                </div>
              </div>

              {/* Monthly trend */}
              {overview.monthly_trend?.length > 0 && (
                <div className="bg-white rounded-2xl border border-ink/10 p-6">
                  <h3 className="font-heading font-bold text-sm uppercase text-ink/50 mb-4 flex items-center gap-2">
                    <TrendingUp className="w-4 h-4" /> 6-Month Trend
                  </h3>
                  <div className="flex items-end gap-3 h-32">
                    {(() => {
                      const max = Math.max(...overview.monthly_trend.map(m => m.revenue_cents), 1);
                      return overview.monthly_trend.map((m, i) => (
                        <div key={m.period} className="flex-1 flex flex-col items-center gap-1">
                          <span className="text-[10px] text-ink/40">{fmtUSD(m.revenue_cents)}</span>
                          <div className="w-full rounded-t-sm transition-all"
                            style={{
                              height: `${Math.max((m.revenue_cents / max) * 80, 4)}px`,
                              background: i === overview.monthly_trend.length - 1 ? "#b45309" : "#e5e7eb",
                            }} />
                          <span className="text-[10px] text-ink/50">{m.period.slice(5)}/{m.period.slice(2, 4)}</span>
                        </div>
                      ));
                    })()}
                  </div>
                </div>
              )}

              {/* Revenue by product */}
              {Object.keys(overview.by_product).length > 0 && (
                <div className="bg-white rounded-2xl border border-ink/10 p-6">
                  <h3 className="font-heading font-bold text-sm uppercase text-ink/50 mb-4 flex items-center gap-2">
                    <CreditCard className="w-4 h-4" /> Revenue by Product (This Month)
                  </h3>
                  <div className="space-y-3">
                    {Object.entries(overview.by_product).sort((a, b) => b[1] - a[1]).map(([key, cents]) => {
                      const pct = overview.goal.month_cents > 0 ? Math.round(cents / overview.goal.month_cents * 100) : 0;
                      return (
                        <div key={key}>
                          <div className="flex justify-between text-sm mb-1">
                            <span className="text-ink font-medium capitalize">{key.replace(/_/g, " ")}</span>
                            <span className="font-mono text-ink/70">{fmtUSD(cents)} <span className="text-ink/40 text-xs">({pct}%)</span></span>
                          </div>
                          <div className="h-2 bg-ink/10 rounded-full overflow-hidden">
                            <div className="h-full bg-copper rounded-full" style={{ width: `${pct}%` }} />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* AI spend by provider */}
              {Object.keys(overview.ai_spend.by_provider).length > 0 && (
                <div className="bg-white rounded-2xl border border-ink/10 p-6">
                  <h3 className="font-heading font-bold text-sm uppercase text-ink/50 mb-4 flex items-center gap-2">
                    <Zap className="w-4 h-4" /> AI Spend by Provider (This Month)
                  </h3>
                  <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                    {Object.entries(overview.ai_spend.by_provider).sort((a, b) => b[1] - a[1]).map(([prov, usd]) => (
                      <div key={prov} className="bg-ink/5 rounded-xl p-3 text-center">
                        <p className="text-xs font-bold text-ink/50 uppercase">{prov}</p>
                        <p className="text-base font-bold font-mono text-ink mt-1">${usd.toFixed(4)}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Creator payout table */}
              <div className="bg-white rounded-2xl border border-ink/10 p-6">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h3 className="font-heading font-bold text-sm uppercase text-ink/50 flex items-center gap-2">
                      <Users className="w-4 h-4" /> Creator Pending Payouts
                    </h3>
                    <p className="text-xs text-ink/40 mt-0.5">Platform owes {fmtUSD(overview.creator_payouts.total_pending_cents)} to {overview.creator_payouts.creators_pending} creator(s)</p>
                  </div>
                  {overview.creator_payouts.creators_pending > 0 && (
                    <button onClick={processPayouts} disabled={payoutBusy}
                      className="btn-primary text-sm flex items-center gap-2 px-4 py-2">
                      {payoutBusy ? <RefreshCw className="w-4 h-4 animate-spin" /> : <DollarSign className="w-4 h-4" />}
                      Process All Payouts
                    </button>
                  )}
                </div>

                {overview.creator_payouts.detail.length > 0 ? (
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-ink/10">
                          <th className="text-left py-2 text-xs text-ink/50 uppercase font-bold">Creator</th>
                          <th className="text-right py-2 text-xs text-ink/50 uppercase font-bold">Pending</th>
                          <th className="text-right py-2 text-xs text-ink/50 uppercase font-bold">Sales</th>
                          <th className="text-center py-2 text-xs text-ink/50 uppercase font-bold">Bank</th>
                        </tr>
                      </thead>
                      <tbody>
                        {overview.creator_payouts.detail.map(c => (
                          <tr key={c.creator_id} className="border-b border-ink/5 last:border-0">
                            <td className="py-3">
                              <p className="font-medium text-ink">{c.name}</p>
                              <p className="text-xs text-ink/40">{c.email}</p>
                            </td>
                            <td className="py-3 text-right font-mono font-bold text-ink">{fmtUSD(c.pending_cents)}</td>
                            <td className="py-3 text-right text-ink/60">{c.sales}</td>
                            <td className="py-3 text-center">
                              {c.bank_on_file
                                ? <span className="text-xs bg-green-50 text-green-700 font-bold px-2 py-0.5 rounded-full">On file</span>
                                : <span className="text-xs bg-red-50 text-red-600 px-2 py-0.5 rounded-full">Missing</span>}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p className="text-sm text-ink/50 text-center py-6">No pending payouts.</p>
                )}
              </div>
            </>) : (
              <div className="text-center py-16 text-ink/40">
                {overviewBusy
                  ? <RefreshCw className="w-8 h-8 mx-auto animate-spin mb-3" />
                  : <TrendingUp className="w-12 h-12 mx-auto mb-4 opacity-30" />}
                <p>{overviewBusy ? "Loading revenue data..." : "No data loaded."}</p>
              </div>
            )}
          </div>
        )}

        {/* ── API KEYS ──────────────────────────────────────────────────────────── */}
        {tab === "keys" && (
          <div className="mt-6 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="font-heading text-xl font-bold">Your API Keys</h2>
              <button onClick={() => { setShowCreateKey(true); setFreshKey(null); }} className="btn-primary inline-flex items-center gap-2 text-sm">
                <Plus className="w-4 h-4" /> Create Key
              </button>
            </div>

            {/* Tier info */}
            {Object.keys(tiers).length > 0 && (
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                {Object.entries(tiers).map(([tier, cfg]) => (
                  <div key={tier} className="bg-white rounded-xl border border-ink/10 p-4 text-center">
                    <p className="text-xs font-bold uppercase text-ink/50">{tier}</p>
                    <p className="text-lg font-bold font-mono text-ink mt-1">{(cfg.requests_per_hour || 0).toLocaleString()}/hr</p>
                    <p className="text-xs text-ink/50">{(cfg.max_tokens_per_call || 0).toLocaleString()} tokens max</p>
                  </div>
                ))}
              </div>
            )}

            {/* Create key form */}
            {showCreateKey && (
              <form onSubmit={createKey} className="bg-white rounded-xl border border-ink/10 p-5 space-y-4">
                <h3 className="font-heading font-bold">New API Key</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs text-ink/50 uppercase mb-1">Label</label>
                    <input required value={newKeyLabel} onChange={e => setNewKeyLabel(e.target.value)}
                      className="w-full px-3 py-2 border border-ink/20 rounded-lg text-sm" placeholder="My App" />
                  </div>
                  <div>
                    <label className="block text-xs text-ink/50 uppercase mb-1">Tier</label>
                    <select value={newKeyTier} onChange={e => setNewKeyTier(e.target.value)}
                      className="w-full px-3 py-2 border border-ink/20 rounded-lg text-sm">
                      {Object.keys(tiers).map(t => <option key={t} value={t}>{t}</option>)}
                    </select>
                  </div>
                </div>
                <div className="flex gap-3">
                  <button type="submit" className="btn-primary text-sm">Generate Key</button>
                  <button type="button" onClick={() => setShowCreateKey(false)} className="text-sm text-ink/50 hover:text-ink">Cancel</button>
                </div>
              </form>
            )}

            {/* Fresh key display */}
            {freshKey && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-4">
                <p className="text-xs font-bold text-yellow-700 uppercase">Save this key — it will never be shown again</p>
                <div className="flex items-center gap-2 mt-2">
                  <code className="flex-1 px-3 py-2 bg-white border border-yellow-300 rounded text-sm font-mono break-all">{freshKey}</code>
                  <button onClick={() => { navigator.clipboard.writeText(freshKey); toast.success("Copied!"); }}
                    className="px-3 py-2 bg-yellow-100 rounded-lg hover:bg-yellow-200"><Copy className="w-4 h-4" /></button>
                </div>
              </div>
            )}

            {/* Key list */}
            {keys.length > 0 && (
              <div className="bg-white rounded-xl border border-ink/10 overflow-hidden">
                {keys.map(k => (
                  <div key={k.key_hash} className="flex items-center justify-between p-4 border-b border-ink/10 last:border-0">
                    <div>
                      <p className="font-medium text-ink text-sm">{k.label}</p>
                      <p className="text-xs text-ink/50 font-mono">{k.key_hash.slice(0, 16)}... · {k.tier} · {k.usage_count || 0} calls</p>
                    </div>
                    {k.active ? (
                      <button onClick={() => setRevokeTarget(k)}
                        className="text-xs text-destructive hover:text-destructive/80">Revoke</button>
                    ) : (
                      <span className="text-xs text-ink/30">Revoked</span>
                    )}
                  </div>
                ))}
              </div>
            )}

            {keys.length === 0 && !showCreateKey && (
              <div className="text-center py-12 text-ink/50">
                <Key className="w-12 h-12 mx-auto mb-4 opacity-30" />
                <p>No API keys yet. Create one to get started.</p>
              </div>
            )}
          </div>
        )}

        {/* ── CREDENTIAL VERIFICATION ──────────────────────────────────────────── */}
        {tab === "verify" && (
          <div className="mt-6 space-y-6">
            <div className="bg-white rounded-xl border border-ink/10 p-6">
              <h2 className="font-heading text-xl font-bold flex items-center gap-2"><Shield className="w-5 h-5 text-copper" /> Verify a Credential</h2>
              <p className="text-sm text-ink/60 mt-1">Enter a verification code to check a candidate's credential.</p>
              <form className="mt-4 flex gap-3" onSubmit={async (e) => {
                e.preventDefault();
                const code = e.target.code.value.trim();
                if (!code) return;
                try {
                  const r = await api.post("/revenue/verify-credential", { verification_code: code });
                  toast.success(`✅ Valid: ${r.data.credential} — ${r.data.holder}`);
                  e.target.code.value = "";
                } catch (err) {
                  toast.error(err?.response?.data?.detail || "Credential not found");
                }
              }}>
                <input name="code" required placeholder="Enter verification code"
                  className="flex-1 px-4 py-2 border border-ink/20 rounded-lg text-sm" />
                <button type="submit" className="btn-primary text-sm flex items-center gap-2"><Shield className="w-4 h-4" /> Verify</button>
              </form>
            </div>

            {user?.role !== "student" && (
              <div className="bg-white rounded-xl border border-ink/10 p-6">
                <h2 className="font-heading text-xl font-bold flex items-center gap-2"><Building className="w-5 h-5 text-copper" /> Batch Verify</h2>
                <p className="text-sm text-ink/60 mt-1">Verify multiple codes at once (comma-separated). Instructor+.</p>
                <form className="mt-4 flex gap-3" onSubmit={async (e) => {
                  e.preventDefault();
                  const codes = e.target.codes.value.trim();
                  if (!codes) return;
                  try {
                    const r = await api.get(`/revenue/employer/verify-batch?codes=${encodeURIComponent(codes)}`);
                    toast.success(`${r.data.valid}/${r.data.total} valid`);
                  } catch (err) { toast.error("Batch verify failed."); }
                }}>
                  <input name="codes" required placeholder="CODE1, CODE2, CODE3"
                    className="flex-1 px-4 py-2 border border-ink/20 rounded-lg text-sm" />
                  <button type="submit" className="btn-primary text-sm">Verify Batch</button>
                </form>
              </div>
            )}

            <div className="bg-ink/5 rounded-xl p-6 text-center">
              <p className="text-sm text-ink/50">Employers: Use the public API to batch-verify credentials at scale.</p>
              <p className="text-xs text-ink/30 mt-1">POST /api/revenue/verify-credential with {"{\"verification_code\": \"...\"}"}</p>
            </div>
          </div>
        )}

        {/* ── COURSE LICENSING ─────────────────────────────────────────────────── */}
        {tab === "courses" && (
          <div className="mt-6 grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-white rounded-xl border border-ink/10 p-6">
              <h2 className="font-heading text-xl font-bold flex items-center gap-2"><BookOpen className="w-5 h-5 text-copper" /> License Courses</h2>
              <p className="text-sm text-ink/60 mt-1">License WAI curriculum for your organization.</p>
              <form onSubmit={createLicense} className="mt-4 space-y-4">
                <div>
                  <label className="block text-xs text-ink/50 uppercase mb-1">Organization</label>
                  <input name="org" required className="w-full px-3 py-2 border border-ink/20 rounded-lg text-sm" placeholder="Your Company, Inc." />
                </div>
                <div>
                  <label className="block text-xs text-ink/50 uppercase mb-1">Seats</label>
                  <input name="seats" type="number" min="1" max="1000" defaultValue="5"
                    className="w-full px-3 py-2 border border-ink/20 rounded-lg text-sm" />
                </div>
                <div>
                  <p className="text-xs text-ink/50 uppercase mb-2">Select Courses</p>
                  {publicCourses.length > 0 ? (
                    <div className="space-y-2 max-h-48 overflow-y-auto">
                      {publicCourses.map(c => (
                        <label key={c.slug} className="flex items-center gap-3 text-sm cursor-pointer">
                          <input type="checkbox" name="courses" value={c.slug} className="rounded border-ink/30 text-copper" />
                          <span>{c.title} <span className="text-ink/40">({c.hours}h)</span></span>
                        </label>
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-ink/50 italic">Loading courses...</p>
                  )}
                </div>
                <button type="submit" className="btn-primary text-sm w-full">Create License</button>
              </form>
            </div>

            <div className="bg-white rounded-xl border border-ink/10 p-6">
              <h2 className="font-heading text-xl font-bold flex items-center gap-2"><Building className="w-5 h-5 text-copper" /> Your Licenses</h2>
              {licenses.length > 0 ? (
                <div className="mt-4 space-y-3">
                  {licenses.map(l => (
                    <div key={l.license_id} className="p-3 bg-ink/5 rounded-lg">
                      <p className="font-medium text-sm">{l.organization}</p>
                      <p className="text-xs text-ink/50 mt-0.5">{l.seats} seats · {l.course_slugs?.length || 0} courses · {l.active ? "Active" : "Inactive"}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-ink/50 mt-4">No active licenses.</p>
              )}
            </div>
          </div>
        )}

        {/* ── COMPLIANCE HOURS ──────────────────────────────────────────────────── */}
        {tab === "compliance" && (
          <div className="mt-6 space-y-4">
            <div className="bg-white rounded-xl border border-ink/10 p-6">
              <h2 className="font-heading text-xl font-bold flex items-center gap-2"><Clock className="w-5 h-5 text-copper" /> Compliance Hours Dashboard</h2>
              <p className="text-sm text-ink/60 mt-1">Track apprentice compliance hours by cohort. Instructor+.</p>
              <div className="flex gap-3 mt-4">
                <input value={associateFilter} onChange={e => setAssociateFilter(e.target.value)}
                  placeholder="Filter by cohort (optional)" className="flex-1 px-4 py-2 border border-ink/20 rounded-lg text-sm" />
                <button onClick={loadCompliance} disabled={busy} className="btn-primary text-sm flex items-center gap-2">
                  {busy ? <RefreshCw className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />} Load
                </button>
              </div>
            </div>

            {compliance && (
              <div className="grid grid-cols-3 gap-4">
                <div className="bg-white rounded-xl border border-ink/10 p-5 text-center">
                  <p className="text-xs text-ink/50 uppercase">Apprentices</p>
                  <p className="text-2xl font-bold font-mono text-ink">{compliance.total_apprentices}</p>
                </div>
                <div className="bg-white rounded-xl border border-ink/10 p-5 text-center">
                  <p className="text-xs text-ink/50 uppercase">Total Hours</p>
                  <p className="text-2xl font-bold font-mono text-ink">{compliance.total_hours}</p>
                </div>
                <div className="bg-white rounded-xl border border-ink/10 p-5 text-center">
                  <p className="text-xs text-ink/50 uppercase">Avg Hours</p>
                  <p className="text-2xl font-bold font-mono text-ink">{compliance.average_hours}</p>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ── SOVEREIGN WORKSPACES ──────────────────────────────────────────────── */}
        {tab === "sovereign" && (
          <div className="mt-6 space-y-4">
            <div className="bg-white rounded-xl border border-ink/10 p-6">
              <h2 className="font-heading text-xl font-bold flex items-center gap-2"><Users className="w-5 h-5 text-copper" /> Sovereign AI Workspaces</h2>
              <p className="text-sm text-ink/60 mt-1">Multi-user Sovereign AI with shared memory per workspace. Admin+.</p>
              <form onSubmit={createWorkspace} className="mt-4 flex gap-3">
                <input value={wsName} onChange={e => setWsName(e.target.value)} required
                  placeholder="Workspace name" className="flex-1 px-4 py-2 border border-ink/20 rounded-lg text-sm" />
                <button type="submit" className="btn-primary text-sm flex items-center gap-2"><Plus className="w-4 h-4" /> Create</button>
              </form>
            </div>

            {workspaces.length > 0 && (
              <div className="bg-white rounded-xl border border-ink/10 overflow-hidden">
                {workspaces.map(ws => (
                  <div key={ws.workspace_id} className="p-4 border-b border-ink/10 last:border-0 flex items-center justify-between">
                    <div>
                      <p className="font-medium text-ink">{ws.name}</p>
                      <p className="text-xs text-ink/50">{ws.member_ids?.length || 0} members · Created {ws.created_at ? new Date(ws.created_at).toLocaleDateString() : ""}</p>
                    </div>
                    <span className="text-xs text-ink/30 font-mono">{ws.workspace_id?.slice(0, 8)}...</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* ── RESUME BUILDER ────────────────────────────────────────────────────── */}
        {tab === "resume" && (
          <div className="mt-6 space-y-4">
            <div className="bg-white rounded-xl border border-ink/10 p-6">
              <h2 className="font-heading text-xl font-bold flex items-center gap-2"><FileText className="w-5 h-5 text-copper" /> AI Resume Builder</h2>
              <p className="text-sm text-ink/60 mt-1">Auto-generated resume from your portfolio and credentials.</p>
            </div>

            {resume && (
              <div className="bg-white rounded-xl border border-ink/10 p-6">
                <div className="border-b border-ink/10 pb-4 mb-4">
                  <p className="text-xl font-bold text-ink">{resume.name || "Your Name"}</p>
                  <p className="text-sm text-ink/50">{resume.email}</p>
                </div>

                {resume.portfolio_bio && (
                  <div className="mb-4">
                    <p className="text-xs font-bold text-ink/50 uppercase mb-1">Summary</p>
                    <p className="text-sm text-ink/70">{resume.portfolio_bio}</p>
                  </div>
                )}

                <div className="mb-4">
                  <p className="text-xs font-bold text-ink/50 uppercase mb-2">Credentials ({resume.credentials?.length || 0})</p>
                  {resume.credentials?.length > 0 ? (
                    <div className="space-y-2">
                      {resume.credentials.map((c, i) => (
                        <div key={i} className="flex items-center gap-3 text-sm p-2 bg-ink/5 rounded-lg">
                          <Check className="w-4 h-4 text-green-600 shrink-0" />
                          <span className="text-ink/80">{c.title}</span>
                          <span className="text-xs text-ink/40 ml-auto">{c.issued_at ? new Date(c.issued_at).toLocaleDateString() : ""}</span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-ink/50 italic">No credentials yet.</p>
                  )}
                </div>

                {resume.portfolio_projects?.length > 0 && (
                  <div>
                    <p className="text-xs font-bold text-ink/50 uppercase mb-2">Projects ({resume.portfolio_projects.length})</p>
                    <div className="space-y-2">
                      {resume.portfolio_projects.map((p, i) => (
                        <div key={i} className="text-sm p-2 bg-ink/5 rounded-lg">
                          <p className="font-medium text-ink">{p.title || p.name || `Project ${i + 1}`}</p>
                          <p className="text-xs text-ink/50">{p.description || ""}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <div className="mt-6 pt-4 border-t border-ink/10">
                  <button className="btn-primary text-sm flex items-center gap-2" onClick={() => {
                    const win = window.open("", "_blank");
                    if (win) {
                      win.document.write(`<html><head><title>Resume - ${resume.name}</title></head><body><pre>${JSON.stringify(resume, null, 2)}</pre></body></html>`);
                      win.document.close();
                    }
                  }}>
                    <ExternalLink className="w-4 h-4" /> Preview Full Resume
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {revokeTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
          <div className="bg-white rounded-2xl p-6 max-w-sm w-full shadow-xl">
            <p className="font-bold text-ink text-sm mb-1">Revoke API key?</p>
            <p className="text-xs text-ink/60 mb-4">"{revokeTarget.label}" — this cannot be undone.</p>
            <div className="flex gap-2 justify-end">
              <button onClick={() => setRevokeTarget(null)} className="text-sm px-4 py-2 text-ink/60 hover:text-ink">Cancel</button>
              <button onClick={() => revokeKey(revokeTarget.key_hash)}
                className="text-sm font-bold bg-destructive hover:bg-destructive/90 text-white px-4 py-2 rounded-lg">
                Revoke Key
              </button>
            </div>
          </div>
        </div>
      )}
      {confirmPayouts && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-sm p-6">
            <h2 className="font-heading font-bold text-lg text-slate-900 mb-2">Process Payouts</h2>
            <p className="text-sm text-slate-600 mb-6">Process all pending creator payouts now?</p>
            <div className="flex justify-end gap-3">
              <button onClick={() => setConfirmPayouts(false)} className="text-sm px-4 py-2 rounded-lg text-slate-600 hover:bg-slate-50">Cancel</button>
              <button onClick={doProcessPayouts} className="text-sm px-4 py-2 rounded-lg bg-red-600 text-white font-bold hover:bg-red-700">Process</button>
            </div>
          </div>
        </div>
      )}
    </AppShell>
  );
}
