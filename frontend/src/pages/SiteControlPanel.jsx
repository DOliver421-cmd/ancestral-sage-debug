import { useState, useEffect, useCallback } from "react";
import AppShell from "../components/AppShell";
import { api } from "../lib/api";
import { toast } from "sonner";
import {
  Users, DollarSign, AlertTriangle, CheckCircle, Activity, Zap, Shield, BookOpen,
  MessageSquare, TrendingUp, RefreshCw, X, Megaphone, ToggleLeft, ToggleRight,
  CreditCard, Server, Clock, Eye, Ban
} from "lucide-react";

const FLAG_LABELS = {
  platform_locked:     { label: "Platform Locked",     desc: "Locks ALL non-exec access to the site", danger: true },
  marketplace_disabled:{ label: "Store Disabled",       desc: "Disables all checkout and store routes", danger: true },
  ai_disabled:         { label: "AI Features Off",      desc: "Disables all AI endpoints site-wide", danger: false },
  community_disabled:  { label: "Community Off",        desc: "Disables M.O.R.E. Hub and community posts", danger: false },
  labs_disabled:       { label: "Labs Disabled",        desc: "Disables workforce lab submissions", danger: false },
};

function fmt(cents) { return `$${((cents || 0) / 100).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`; }
function fmtUSD(usd) { return `$${(usd || 0).toFixed(4)}`; }
function fmtNum(n) { return (n || 0).toLocaleString(); }
function ago(iso) {
  if (!iso) return "—";
  const diff = Date.now() - new Date(iso).getTime();
  if (diff < 60000) return "just now";
  if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
  return `${Math.floor(diff / 86400000)}d ago`;
}

export default function SiteControlPanel() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [flagBusy, setFlagBusy] = useState({});
  const [broadcastForm, setBroadcastForm] = useState({ message: "", kind: "info", active: true });
  const [broadcastSaving, setBroadcastSaving] = useState(false);
  const [flagReasonModal, setFlagReasonModal] = useState(null); // { flag, value }
  const [flagReason, setFlagReason] = useState("");
  const [activeTab, setActiveTab] = useState("overview");

  const load = useCallback(async (silent = false) => {
    if (!silent) setLoading(true);
    else setRefreshing(true);
    try {
      const { data: d } = await api.get("/admin/control-panel");
      setData(d);
      if (d.active_broadcast) {
        setBroadcastForm({ message: d.active_broadcast.message || "", kind: d.active_broadcast.kind || "info", active: d.active_broadcast.active !== false });
      }
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Failed to load control panel.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  async function toggleFlag(flag, currentEnabled) {
    const newVal = !currentEnabled;
    if (newVal && FLAG_LABELS[flag]?.danger) {
      setFlagReasonModal({ flag, value: newVal });
      return;
    }
    await applyFlag(flag, newVal, "");
  }

  async function applyFlag(flag, value, reason) {
    setFlagBusy(b => ({ ...b, [flag]: true }));
    try {
      await api.post(`/admin/platform/flags/${flag}`, { value, reason });
      toast.success(`${FLAG_LABELS[flag]?.label || flag}: ${value ? "ENABLED" : "DISABLED"}`);
      await load(true);
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Flag update failed.");
    } finally {
      setFlagBusy(b => ({ ...b, [flag]: false }));
      setFlagReasonModal(null);
      setFlagReason("");
    }
  }

  async function saveBroadcast() {
    setBroadcastSaving(true);
    try {
      await api.post("/admin/control-panel/broadcast", broadcastForm);
      toast.success(broadcastForm.active ? "Banner published to all users." : "Banner cleared.");
      await load(true);
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Broadcast failed.");
    } finally {
      setBroadcastSaving(false);
    }
  }

  if (loading) return (
    <AppShell>
      <div className="p-10 text-ink/50 text-sm flex items-center gap-2">
        <RefreshCw className="w-4 h-4 animate-spin" /> Loading control panel…
      </div>
    </AppShell>
  );

  if (!data) return (
    <AppShell>
      <div className="p-10 text-destructive text-sm">Control panel data unavailable.</div>
    </AppShell>
  );

  const { users, revenue, stripe, platform_flags, creator_economy, learning, ai_spend, community, governance, recent_failures, recent_audit, active_broadcast } = data;

  // Determine critical alerts
  const alerts = [];
  if (stripe.mode === "test") alerts.push({ level: "warning", msg: "Stripe is in TEST mode — no real money is moving" });
  if (revenue.failed_payments > 0) alerts.push({ level: "error", msg: `${revenue.failed_payments} failed payment${revenue.failed_payments > 1 ? "s" : ""} on record` });
  if (governance.pending_refunds > 0) alerts.push({ level: "warning", msg: `${governance.pending_refunds} pending refund${governance.pending_refunds > 1 ? "s" : ""}` });
  if (governance.pending_escalations > 0) alerts.push({ level: "error", msg: `${governance.pending_escalations} open escalation${governance.pending_escalations > 1 ? "s" : ""}` });
  if (community.flags_pending > 0) alerts.push({ level: "warning", msg: `${community.flags_pending} M.O.R.E. post${community.flags_pending > 1 ? "s" : ""} flagged for review` });
  if (learning.incidents_open > 0) alerts.push({ level: "warning", msg: `${learning.incidents_open} open incident report${learning.incidents_open > 1 ? "s" : ""}` });
  if (platform_flags?.platform_locked?.enabled) alerts.push({ level: "error", msg: "PLATFORM IS LOCKED — public access blocked" });
  if (recent_failures?.length > 5) alerts.push({ level: "warning", msg: `${recent_failures.length} failure/denial events in the last 24 hours` });

  const tabs = [
    ["overview", "Overview"],
    ["revenue", "Revenue"],
    ["flags", "Platform Flags"],
    ["creators", "Creator Economy"],
    ["learning", "Learning"],
    ["ai", "AI Spend"],
    ["community", "Community"],
    ["governance", "Governance"],
    ["broadcast", "Broadcast"],
  ];

  return (
    <AppShell>
      <div className="px-6 py-8 max-w-7xl">

        {/* Header */}
        <div className="flex items-center justify-between mb-2">
          <div>
            <div className="overline text-red-600 text-xs font-black">EXECUTIVE ONLY</div>
            <h1 className="font-heading text-4xl font-bold text-ink">Site Control Panel</h1>
          </div>
          <button onClick={() => load(true)} disabled={refreshing} className="flex items-center gap-2 text-sm text-ink/50 hover:text-ink transition-colors">
            <RefreshCw className={`w-4 h-4 ${refreshing ? "animate-spin" : ""}`} />
            {refreshing ? "Refreshing…" : `Updated ${ago(data.generated_at)}`}
          </button>
        </div>

        {/* Alert bar */}
        {alerts.length > 0 && (
          <div className="space-y-2 mb-6 mt-4">
            {alerts.map((a, i) => (
              <div key={i} className={`flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-semibold ${
                a.level === "error" ? "bg-red-50 border border-red-300 text-red-800" : "bg-amber-50 border border-amber-300 text-amber-800"
              }`}>
                <AlertTriangle className="w-4 h-4 shrink-0" />
                {a.msg}
              </div>
            ))}
          </div>
        )}

        {/* Stripe mode pill */}
        <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-black mb-6 ${
          stripe.mode === "live" ? "bg-green-100 text-green-800" :
          stripe.mode === "test" ? "bg-amber-100 text-amber-800" :
          "bg-ink/10 text-ink/60"
        }`}>
          <CreditCard className="w-3 h-3" />
          Stripe: {stripe.mode.toUpperCase()}
          {stripe.balance && stripe.balance.available?.[0] && (
            <span className="ml-1 font-normal">· available {fmt(stripe.balance.available[0].amount)}</span>
          )}
        </div>

        {/* Tabs */}
        <div className="flex gap-1 flex-wrap mb-6 border-b border-ink/10">
          {tabs.map(([key, label]) => (
            <button key={key} onClick={() => setActiveTab(key)}
              className={`px-3 py-2 text-xs font-bold border-b-2 transition-colors whitespace-nowrap ${
                activeTab === key ? "border-copper text-copper" : "border-transparent text-ink/50 hover:text-ink"
              }`}
            >{label}</button>
          ))}
        </div>

        {/* ── OVERVIEW ── */}
        {activeTab === "overview" && (
          <div className="space-y-6">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <MetricCard icon={Users} label="Total Users" value={fmtNum(users.total)} sub={`+${users.new_today} today`} />
              <MetricCard icon={Users} label="Active Users" value={fmtNum(users.active)} sub={`${users.suspended} suspended`} accent="text-green-600" />
              <MetricCard icon={DollarSign} label="Revenue Today" value={fmt(revenue.today_cents)} accent="text-green-700" />
              <MetricCard icon={DollarSign} label="Revenue This Month" value={fmt(revenue.month_cents)} accent="text-green-700" />
              <MetricCard icon={Activity} label="Active Subscriptions" value={fmtNum(revenue.active_subscriptions)} sub={`${revenue.canceled_subscriptions} canceled`} />
              <MetricCard icon={BookOpen} label="Course Completions" value={fmtNum(learning.completions_total)} sub={`+${learning.completions_today} today`} />
              <MetricCard icon={Zap} label="AI Spend Today" value={fmtUSD(ai_spend.today_usd)} sub={`$${ai_spend.month_usd.toFixed(2)} this month`} />
              <MetricCard icon={Shield} label="Open Escalations" value={fmtNum(governance.pending_escalations)} accent={governance.pending_escalations > 0 ? "text-red-600" : "text-ink"} />
            </div>

            {/* Recent failures */}
            {recent_failures?.length > 0 && (
              <div className="card-flat p-5">
                <div className="flex items-center gap-2 mb-3">
                  <AlertTriangle className="w-4 h-4 text-red-500" />
                  <span className="font-bold text-sm">Recent Failures & Denials (24h)</span>
                  <span className="ml-auto text-xs text-ink/40">{recent_failures.length} events</span>
                </div>
                <div className="space-y-1">
                  {recent_failures.slice(0, 10).map((r, i) => (
                    <div key={i} className="flex items-center gap-3 text-xs py-1 border-b border-ink/5 last:border-0">
                      <span className="font-mono text-ink/40 w-20 shrink-0">{ago(r.at)}</span>
                      <span className="font-semibold text-red-700 flex-1 truncate">{r.action}</span>
                      <span className="text-ink/50 truncate max-w-[120px]">{r.actor_name}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Recent audit trail */}
            <div className="card-flat p-5">
              <div className="flex items-center gap-2 mb-3">
                <Clock className="w-4 h-4 text-copper" />
                <span className="font-bold text-sm">Audit Trail — Last 20 Actions</span>
              </div>
              <div className="space-y-1">
                {recent_audit.map((r, i) => (
                  <div key={i} className="flex items-center gap-3 text-xs py-1 border-b border-ink/5 last:border-0">
                    <span className="font-mono text-ink/40 w-20 shrink-0">{ago(r.at)}</span>
                    <span className="font-semibold text-ink flex-1 truncate">{r.action}</span>
                    <span className="text-ink/50 truncate max-w-[140px]">{r.actor_name}</span>
                    <span className="text-ink/30 truncate max-w-[80px]">{r.actor_role}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ── REVENUE ── */}
        {activeTab === "revenue" && (
          <div className="space-y-6">
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              <MetricCard icon={DollarSign} label="Today" value={fmt(revenue.today_cents)} accent="text-green-700" />
              <MetricCard icon={DollarSign} label="This Month" value={fmt(revenue.month_cents)} accent="text-green-700" />
              <MetricCard icon={DollarSign} label="All Time" value={fmt(revenue.alltime_cents)} accent="text-green-800" />
              <MetricCard icon={Activity} label="Active Subs" value={fmtNum(revenue.active_subscriptions)} />
              <MetricCard icon={Ban} label="Failed Payments" value={fmtNum(revenue.failed_payments)} accent={revenue.failed_payments > 0 ? "text-red-600" : "text-ink"} />
              <MetricCard icon={Clock} label="Pending Creator Payouts" value={fmt(revenue.pending_creator_payouts_cents)} accent="text-amber-600" />
            </div>

            <div className="card-flat p-5">
              <div className="font-bold text-sm mb-4">Revenue by Product This Month</div>
              {Object.keys(revenue.by_product_month || {}).length === 0 ? (
                <div className="text-ink/40 text-sm">No sales this month.</div>
              ) : (
                <div className="space-y-2">
                  {Object.entries(revenue.by_product_month)
                    .sort((a, b) => b[1] - a[1])
                    .map(([key, cents]) => (
                      <div key={key} className="flex items-center gap-3 text-sm">
                        <span className="font-mono text-ink/60 flex-1">{key}</span>
                        <span className="font-bold text-green-700">{fmt(cents)}</span>
                      </div>
                    ))}
                </div>
              )}
            </div>

            {stripe.balance && (
              <div className="card-flat p-5">
                <div className="flex items-center gap-2 mb-3">
                  <CreditCard className="w-4 h-4 text-copper" />
                  <span className="font-bold text-sm">Stripe Account Balance</span>
                  <span className={`ml-2 text-xs font-black px-2 py-0.5 rounded-full ${stripe.mode === "live" ? "bg-green-100 text-green-800" : "bg-amber-100 text-amber-800"}`}>{stripe.mode.toUpperCase()}</span>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="overline text-xs text-ink/40 mb-1">Available</div>
                    {stripe.balance.available.map((b, i) => (
                      <div key={i} className="font-bold text-green-700">{fmt(b.amount)} <span className="text-xs text-ink/40 font-normal">{b.currency.toUpperCase()}</span></div>
                    ))}
                  </div>
                  <div>
                    <div className="overline text-xs text-ink/40 mb-1">Pending</div>
                    {stripe.balance.pending.map((b, i) => (
                      <div key={i} className="font-bold text-amber-600">{fmt(b.amount)} <span className="text-xs text-ink/40 font-normal">{b.currency.toUpperCase()}</span></div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ── PLATFORM FLAGS ── */}
        {activeTab === "flags" && (
          <div className="space-y-4">
            <p className="text-sm text-ink/60 mb-4">These switches affect all users site-wide immediately. Dangerous flags require a reason before activating.</p>
            {Object.entries(FLAG_LABELS).map(([flag, meta]) => {
              const current = platform_flags?.[flag];
              const enabled = current?.enabled === true;
              return (
                <div key={flag} className={`card-flat p-5 flex items-start gap-4 ${enabled && meta.danger ? "border-red-300 bg-red-50/30" : ""}`}>
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-bold">{meta.label}</span>
                      {meta.danger && <span className="text-xs font-black text-red-600 px-1.5 py-0.5 bg-red-100 rounded">DANGEROUS</span>}
                      {enabled && <span className="text-xs font-black text-green-700 px-1.5 py-0.5 bg-green-100 rounded">ACTIVE</span>}
                    </div>
                    <div className="text-sm text-ink/60 mt-1">{meta.desc}</div>
                    {enabled && current?.reason && (
                      <div className="text-xs text-ink/50 mt-1">Reason: "{current.reason}" · set {ago(current.set_at)}</div>
                    )}
                  </div>
                  <button
                    onClick={() => toggleFlag(flag, enabled)}
                    disabled={flagBusy[flag]}
                    className={`flex items-center gap-2 text-sm font-bold px-4 py-2 rounded-xl transition-colors disabled:opacity-50 ${
                      enabled ? "bg-red-100 text-red-700 hover:bg-red-200" : "bg-ink/10 text-ink hover:bg-ink/20"
                    }`}
                  >
                    {flagBusy[flag] ? <RefreshCw className="w-4 h-4 animate-spin" /> : enabled ? <ToggleRight className="w-4 h-4" /> : <ToggleLeft className="w-4 h-4" />}
                    {enabled ? "Disable" : "Enable"}
                  </button>
                </div>
              );
            })}
          </div>
        )}

        {/* ── CREATOR ECONOMY ── */}
        {activeTab === "creators" && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              <MetricCard icon={BookOpen} label="Creator Courses" value={fmtNum(creator_economy.courses_total)} sub={`${creator_economy.courses_published} published`} />
              <MetricCard icon={Users} label="Creator Profiles" value={fmtNum(creator_economy.creator_profiles)} />
              <MetricCard icon={DollarSign} label="Pending Payouts" value={fmt(revenue.pending_creator_payouts_cents)} accent="text-amber-600" />
            </div>
            <div className="card-flat p-5 text-sm text-ink/60">
              <div className="font-bold text-ink mb-1">Payout Processing</div>
              To trigger payouts for all creators with pending earnings from prior months:
              <code className="block mt-2 p-3 bg-ink/5 rounded-lg font-mono text-xs">POST /api/admin/creator-payouts/process</code>
              <p className="mt-2 text-xs text-ink/40">This marks all pre-current-month pending earnings as "processing" and notifies each creator. Run on the 1st of each month.</p>
            </div>
          </div>
        )}

        {/* ── LEARNING ── */}
        {activeTab === "learning" && (
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            <MetricCard icon={BookOpen} label="Curriculum Modules" value={fmtNum(learning.modules)} />
            <MetricCard icon={CheckCircle} label="Completions Total" value={fmtNum(learning.completions_total)} sub={`+${learning.completions_today} today`} />
            <MetricCard icon={Activity} label="Labs Pending Review" value={fmtNum(learning.labs_pending_review)} accent={learning.labs_pending_review > 5 ? "text-amber-600" : "text-ink"} />
            <MetricCard icon={CheckCircle} label="Credentials Issued" value={fmtNum(learning.credentials_issued)} />
            <MetricCard icon={AlertTriangle} label="Open Incidents" value={fmtNum(learning.incidents_open)} accent={learning.incidents_open > 0 ? "text-red-600" : "text-ink"} />
          </div>
        )}

        {/* ── AI SPEND ── */}
        {activeTab === "ai" && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              <MetricCard icon={Zap} label="AI Spend Today" value={fmtUSD(ai_spend.today_usd)} accent="text-amber-600" />
              <MetricCard icon={Zap} label="AI Spend This Month" value={`$${ai_spend.month_usd.toFixed(4)}`} accent="text-amber-600" />
              <MetricCard icon={Activity} label="API Calls This Month" value={fmtNum(ai_spend.calls_this_month)} />
            </div>
            <div className="card-flat p-5">
              <div className="font-bold text-sm mb-3">Spend by Provider This Month</div>
              {Object.keys(ai_spend.by_provider || {}).length === 0 ? (
                <div className="text-ink/40 text-sm">No AI usage recorded this month.</div>
              ) : (
                <div className="space-y-2">
                  {Object.entries(ai_spend.by_provider)
                    .sort((a, b) => b[1] - a[1])
                    .map(([provider, usd]) => (
                      <div key={provider} className="flex items-center gap-3 text-sm">
                        <span className="font-mono text-ink/60 flex-1">{provider}</span>
                        <span className="font-bold text-amber-700">${usd.toFixed(4)}</span>
                      </div>
                    ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* ── COMMUNITY ── */}
        {activeTab === "community" && (
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            <MetricCard icon={Users} label="M.O.R.E. Members" value={fmtNum(community.more_members)} />
            <MetricCard icon={MessageSquare} label="Total Posts" value={fmtNum(community.posts_total)} sub={`+${community.posts_today} today`} />
            <MetricCard icon={Activity} label="Open Needs" value={fmtNum(community.needs_open)} />
            <MetricCard icon={AlertTriangle} label="Flagged Posts" value={fmtNum(community.flags_pending)} accent={community.flags_pending > 0 ? "text-red-600" : "text-ink"} />
          </div>
        )}

        {/* ── GOVERNANCE ── */}
        {activeTab === "governance" && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              <MetricCard icon={Shield} label="Audit Events Today" value={fmtNum(governance.audit_events_today)} />
              <MetricCard icon={Shield} label="Governance Log Total" value={fmtNum(governance.governance_log_entries)} />
              <MetricCard icon={AlertTriangle} label="Pending Refunds" value={fmtNum(governance.pending_refunds)} accent={governance.pending_refunds > 0 ? "text-amber-600" : "text-ink"} />
              <MetricCard icon={AlertTriangle} label="Open Escalations" value={fmtNum(governance.pending_escalations)} accent={governance.pending_escalations > 0 ? "text-red-600" : "text-ink"} />
            </div>

            <div className="card-flat p-5">
              <div className="font-bold text-sm mb-3 flex items-center gap-2">
                <Clock className="w-4 h-4 text-copper" /> Full Audit Trail — Last 20 Actions
              </div>
              <div className="space-y-1">
                {recent_audit.map((r, i) => (
                  <div key={i} className="flex items-center gap-3 text-xs py-1.5 border-b border-ink/5 last:border-0">
                    <span className="font-mono text-ink/40 w-24 shrink-0">{ago(r.at)}</span>
                    <span className="font-semibold text-ink flex-1">{r.action}</span>
                    <span className="text-ink/50">{r.actor_name}</span>
                    <span className="text-ink/30 text-[10px]">{r.actor_role}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ── BROADCAST ── */}
        {activeTab === "broadcast" && (
          <div className="max-w-xl space-y-4">
            {active_broadcast?.active && (
              <div className={`flex items-start gap-3 p-4 rounded-xl border ${
                active_broadcast.kind === "error" ? "bg-red-50 border-red-300" :
                active_broadcast.kind === "warning" ? "bg-amber-50 border-amber-300" :
                "bg-blue-50 border-blue-300"
              }`}>
                <Megaphone className="w-4 h-4 mt-0.5 shrink-0" />
                <div>
                  <div className="font-bold text-sm">Active Banner</div>
                  <div className="text-sm mt-0.5">{active_broadcast.message}</div>
                </div>
              </div>
            )}

            <div className="card-flat p-6 space-y-4">
              <h2 className="font-heading font-bold text-lg flex items-center gap-2">
                <Megaphone className="w-5 h-5 text-copper" /> Site-Wide Announcement
              </h2>
              <div>
                <label className="overline text-xs text-ink/50 block mb-1">Message</label>
                <textarea
                  className="input w-full h-24 resize-none"
                  value={broadcastForm.message}
                  onChange={e => setBroadcastForm(f => ({ ...f, message: e.target.value }))}
                  placeholder="Message shown to all logged-in users…"
                  maxLength={500}
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="overline text-xs text-ink/50 block mb-1">Type</label>
                  <select className="input w-full" value={broadcastForm.kind} onChange={e => setBroadcastForm(f => ({ ...f, kind: e.target.value }))}>
                    <option value="info">Info (blue)</option>
                    <option value="warning">Warning (amber)</option>
                    <option value="error">Critical (red)</option>
                  </select>
                </div>
                <div className="flex items-end">
                  <label className="flex items-center gap-2 text-sm cursor-pointer">
                    <input type="checkbox" checked={broadcastForm.active} onChange={e => setBroadcastForm(f => ({ ...f, active: e.target.checked }))} />
                    Active (visible to users)
                  </label>
                </div>
              </div>
              <div className="flex gap-3">
                <button onClick={saveBroadcast} disabled={broadcastSaving} className="btn-copper text-sm disabled:opacity-50">
                  {broadcastSaving ? "Publishing…" : broadcastForm.active ? "Publish Banner" : "Clear Banner"}
                </button>
                {active_broadcast?.active && (
                  <button onClick={() => { setBroadcastForm(f => ({ ...f, active: false })); }} className="btn-ghost text-sm">
                    Clear existing
                  </button>
                )}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Flag reason modal */}
      {flagReasonModal && (
        <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center px-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6">
            <div className="flex items-center gap-2 mb-4">
              <AlertTriangle className="w-5 h-5 text-red-600" />
              <h3 className="font-heading font-bold text-lg">Confirm Dangerous Action</h3>
              <button onClick={() => { setFlagReasonModal(null); setFlagReason(""); }} className="ml-auto">
                <X className="w-4 h-4 text-ink/40" />
              </button>
            </div>
            <p className="text-sm text-ink/70 mb-4">
              You are enabling <strong>{FLAG_LABELS[flagReasonModal.flag]?.label}</strong>.
              This affects all users immediately. You must provide a reason.
            </p>
            <textarea
              className="input w-full h-24 resize-none mb-4"
              value={flagReason}
              onChange={e => setFlagReason(e.target.value)}
              placeholder="Reason for enabling this flag…"
              autoFocus
            />
            <div className="flex gap-3 justify-end">
              <button onClick={() => { setFlagReasonModal(null); setFlagReason(""); }} className="btn-ghost text-sm">Cancel</button>
              <button
                onClick={() => applyFlag(flagReasonModal.flag, flagReasonModal.value, flagReason)}
                disabled={!flagReason.trim() || flagBusy[flagReasonModal.flag]}
                className="bg-red-600 text-white text-sm font-bold px-5 py-2 rounded-xl hover:bg-red-700 disabled:opacity-50 transition-colors"
              >
                Enable Flag
              </button>
            </div>
          </div>
        </div>
      )}
    </AppShell>
  );
}

function MetricCard({ icon: Icon, label, value, sub, accent = "text-ink" }) {
  return (
    <div className="card-flat p-5">
      <Icon className={`w-4 h-4 mb-2 ${accent}`} />
      <div className={`font-heading text-2xl font-black ${accent}`}>{value}</div>
      <div className="overline text-ink/50 mt-0.5">{label}</div>
      {sub && <div className="text-xs text-ink/40 mt-0.5">{sub}</div>}
    </div>
  );
}
