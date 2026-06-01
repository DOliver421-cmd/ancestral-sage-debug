/**
 * Billing Admin — executive/admin dashboard for credits, refunds, and Sage sessions.
 * Routes: GET /billing/credits/balance, POST /billing/credits/grant
 *         POST /billing/refunds/site-credits, POST /billing/refunds/cash
 *         GET/POST /billing/sage-sessions, POST /billing/sage-sessions/{id}/resolve
 */
import { useState, useEffect, useCallback } from "react";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import { toast } from "sonner";
import { DollarSign, RefreshCw, CheckCircle, XCircle, CreditCard, Clock } from "lucide-react";

const fmt = (cents) => `$${(cents / 100).toFixed(2)}`;

export default function BillingAdmin() {
  const { user } = useAuth();
  const [tab, setTab]             = useState("credits");
  const [loading, setLoading]     = useState(false);

  // credits
  const [balanceUid, setBalanceUid]   = useState("");
  const [balance, setBalance]         = useState(null);
  const [grantForm, setGrantForm]     = useState({ user_id: "", amount_cents: "", reason: "" });
  const [granting, setGranting]       = useState(false);

  // site-credit refund
  const [scForm, setScForm]   = useState({ user_id: "", platform_cost_cents: "", reason: "", user_received_value: false });
  const [scBusy, setScBusy]   = useState(false);

  // cash refund
  const [cashForm, setCashForm] = useState({
    user_id: "", amount_cents: "", reason: "",
    is_extreme_violation: false, user_not_at_fault: false,
    is_legal: false, no_harm_to_wai: false, supervisor_approved: false,
  });
  const [cashBusy, setCashBusy] = useState(false);

  // sage sessions
  const [sessions, setSessions]     = useState([]);
  const [resolving, setResolving]   = useState({});

  const loadSessions = useCallback(async () => {
    try {
      const r = await api.get("/billing/sage-sessions");
      setSessions(Array.isArray(r.data) ? r.data : r.data.sessions || []);
    } catch { setSessions([]); }
  }, []);

  useEffect(() => { if (tab === "sage") loadSessions(); }, [tab, loadSessions]);

  const lookupBalance = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const r = await api.get(`/billing/credits/balance${balanceUid ? `?user_id=${balanceUid}` : ""}`);
      setBalance(r.data);
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Failed to load balance");
    } finally { setLoading(false); }
  };

  const grantCredits = async (e) => {
    e.preventDefault();
    setGranting(true);
    try {
      await api.post("/billing/credits/grant", {
        user_id: grantForm.user_id,
        amount_cents: parseInt(grantForm.amount_cents),
        reason: grantForm.reason,
      });
      toast.success(`${fmt(parseInt(grantForm.amount_cents))} credited`);
      setGrantForm({ user_id: "", amount_cents: "", reason: "" });
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Grant failed");
    } finally { setGranting(false); }
  };

  const issueSiteCredit = async (e) => {
    e.preventDefault();
    setScBusy(true);
    try {
      const r = await api.post("/billing/refunds/site-credits", {
        user_id: scForm.user_id,
        platform_cost_cents: parseInt(scForm.platform_cost_cents),
        reason: scForm.reason,
        user_received_value: scForm.user_received_value,
      });
      toast.success(`Site credit issued: ${fmt(r.data.amount_cents || parseInt(scForm.platform_cost_cents))}`);
      setScForm({ user_id: "", platform_cost_cents: "", reason: "", user_received_value: false });
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Refund failed");
    } finally { setScBusy(false); }
  };

  const issueCashRefund = async (e) => {
    e.preventDefault();
    const conditions = {
      is_extreme_violation: cashForm.is_extreme_violation,
      user_not_at_fault:    cashForm.user_not_at_fault,
      is_legal:             cashForm.is_legal,
      no_harm_to_wai:       cashForm.no_harm_to_wai,
      supervisor_approved:  cashForm.supervisor_approved,
    };
    const allMet = Object.values(conditions).every(Boolean);
    if (!allMet) {
      toast.error("All 5 conditions must be confirmed for a cash refund.");
      return;
    }
    setCashBusy(true);
    try {
      await api.post("/billing/refunds/cash", {
        user_id: cashForm.user_id,
        amount_cents: parseInt(cashForm.amount_cents),
        reason: cashForm.reason,
        conditions,
      });
      toast.success("Cash refund submitted for processing");
      setCashForm({ user_id: "", amount_cents: "", reason: "", is_extreme_violation: false, user_not_at_fault: false, is_legal: false, no_harm_to_wai: false, supervisor_approved: false });
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Cash refund failed");
    } finally { setCashBusy(false); }
  };

  const resolveSession = async (sessionId, selfCorrected) => {
    setResolving(r => ({ ...r, [sessionId]: true }));
    try {
      const r = await api.post(`/billing/sage-sessions/${sessionId}/resolve`, {
        user_self_corrected: selfCorrected,
        actor_id: user.id,
      });
      toast.success(selfCorrected ? "Session resolved — fee waived" : "Session escalated");
      loadSessions();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Failed to resolve session");
    } finally { setResolving(r => ({ ...r, [sessionId]: false })); }
  };

  const inp = "w-full border border-ink/20 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gold";
  const chk = (key, val, setter, label) => (
    <label className="flex items-center gap-2 text-sm cursor-pointer select-none">
      <input type="checkbox" checked={val} onChange={e => setter(f => ({ ...f, [key]: e.target.checked }))}
        className="w-4 h-4 rounded border-ink/30 text-gold" />
      <span className={val ? "text-ink font-medium" : "text-ink/60"}>{label}</span>
    </label>
  );

  return (
    <div className="min-h-screen bg-bone">
      <div className="max-w-4xl mx-auto px-6 py-10">
        <div className="mb-8">
          <h1 className="font-heading text-3xl font-bold text-ink">Billing & Credits</h1>
          <p className="text-ink/60 mt-1 text-sm">Issue credits, process refunds, and manage Sage conduct sessions.</p>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 mb-6 border-b border-ink/10">
          {[["credits","Credits"], ["refunds","Refunds"], ["cash","Cash Refunds"], ["sage","Sage Sessions"]].map(([id, label]) => (
            <button key={id} onClick={() => setTab(id)}
              className={`px-4 py-2 text-sm font-semibold border-b-2 transition ${tab === id ? "border-gold text-ink" : "border-transparent text-ink/50 hover:text-ink"}`}>
              {label}
            </button>
          ))}
        </div>

        {/* ── CREDITS TAB ── */}
        {tab === "credits" && (
          <div className="space-y-6">
            {/* Balance lookup */}
            <div className="bg-white border border-ink/10 rounded-xl p-5">
              <h2 className="font-bold mb-4 flex items-center gap-2"><CreditCard className="w-4 h-4" /> Check Balance</h2>
              <form onSubmit={lookupBalance} className="flex gap-3">
                <input value={balanceUid} onChange={e => setBalanceUid(e.target.value)} className={`${inp} flex-1`} placeholder="User ID (leave blank for your own)" />
                <button type="submit" disabled={loading} className="bg-gold text-white text-sm font-semibold px-4 py-2 rounded-lg disabled:opacity-50 shrink-0">
                  {loading ? "…" : "Look up"}
                </button>
              </form>
              {balance && (
                <div className="mt-4 p-4 bg-bone rounded-lg">
                  <p className="text-2xl font-bold text-ink">{fmt(balance.balance_cents ?? balance.balance ?? 0)}</p>
                  <p className="text-xs text-ink/50 mt-1">User: {balance.user_id || "—"}</p>
                </div>
              )}
            </div>

            {/* Grant credits */}
            <div className="bg-white border border-ink/10 rounded-xl p-5">
              <h2 className="font-bold mb-4">Grant Site Credits</h2>
              <form onSubmit={grantCredits} className="space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <div><label className="text-xs font-medium text-ink/60 mb-1 block">User ID *</label>
                    <input required value={grantForm.user_id} onChange={e => setGrantForm(f => ({...f, user_id: e.target.value}))} className={inp} /></div>
                  <div><label className="text-xs font-medium text-ink/60 mb-1 block">Amount (cents) *</label>
                    <input required type="number" min="1" value={grantForm.amount_cents} onChange={e => setGrantForm(f => ({...f, amount_cents: e.target.value}))} className={inp} placeholder="500 = $5.00" /></div>
                </div>
                <div><label className="text-xs font-medium text-ink/60 mb-1 block">Reason *</label>
                  <input required value={grantForm.reason} onChange={e => setGrantForm(f => ({...f, reason: e.target.value}))} className={inp} /></div>
                <button type="submit" disabled={granting} className="bg-gold text-white text-sm font-semibold px-4 py-2 rounded-lg disabled:opacity-50">
                  {granting ? "Granting…" : "Grant Credits"}
                </button>
              </form>
            </div>
          </div>
        )}

        {/* ── SITE CREDIT REFUNDS TAB ── */}
        {tab === "refunds" && (
          <div className="bg-white border border-ink/10 rounded-xl p-5">
            <h2 className="font-bold mb-2 flex items-center gap-2"><RefreshCw className="w-4 h-4" /> Issue Site Credit Refund</h2>
            <p className="text-xs text-ink/50 mb-4">Default refund method. Amount = cost + 10% if no value was delivered; cost only if value was received.</p>
            <form onSubmit={issueSiteCredit} className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div><label className="text-xs font-medium text-ink/60 mb-1 block">User ID *</label>
                  <input required value={scForm.user_id} onChange={e => setScForm(f => ({...f, user_id: e.target.value}))} className={inp} /></div>
                <div><label className="text-xs font-medium text-ink/60 mb-1 block">Platform Cost (cents) *</label>
                  <input required type="number" min="1" value={scForm.platform_cost_cents} onChange={e => setScForm(f => ({...f, platform_cost_cents: e.target.value}))} className={inp} placeholder="1000 = $10.00" /></div>
              </div>
              <div><label className="text-xs font-medium text-ink/60 mb-1 block">Reason *</label>
                <input required value={scForm.reason} onChange={e => setScForm(f => ({...f, reason: e.target.value}))} className={inp} /></div>
              {chk("user_received_value", scForm.user_received_value, setScForm, "User received value (refund = cost only, no bonus)")}
              <div className="bg-bone rounded-lg p-3 text-sm text-ink/60">
                Refund amount: <strong className="text-ink">{scForm.platform_cost_cents
                  ? fmt(scForm.user_received_value ? parseInt(scForm.platform_cost_cents) : Math.round(parseInt(scForm.platform_cost_cents) * 1.10))
                  : "—"}</strong>
              </div>
              <button type="submit" disabled={scBusy} className="bg-gold text-white text-sm font-semibold px-4 py-2 rounded-lg disabled:opacity-50">
                {scBusy ? "Processing…" : "Issue Site Credit"}
              </button>
            </form>
          </div>
        )}

        {/* ── CASH REFUNDS TAB ── */}
        {tab === "cash" && (
          <div className="bg-white border border-ink/10 rounded-xl p-5">
            <h2 className="font-bold mb-2 flex items-center gap-2"><DollarSign className="w-4 h-4" /> Cash Refund</h2>
            <p className="text-xs text-ink/50 mb-4">All 5 conditions must be confirmed. This is routed through the Compliance Engine before execution.</p>
            <form onSubmit={issueCashRefund} className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div><label className="text-xs font-medium text-ink/60 mb-1 block">User ID *</label>
                  <input required value={cashForm.user_id} onChange={e => setCashForm(f => ({...f, user_id: e.target.value}))} className={inp} /></div>
                <div><label className="text-xs font-medium text-ink/60 mb-1 block">Amount (cents) *</label>
                  <input required type="number" min="1" value={cashForm.amount_cents} onChange={e => setCashForm(f => ({...f, amount_cents: e.target.value}))} className={inp} /></div>
              </div>
              <div><label className="text-xs font-medium text-ink/60 mb-1 block">Reason *</label>
                <input required value={cashForm.reason} onChange={e => setCashForm(f => ({...f, reason: e.target.value}))} className={inp} /></div>
              <div className="bg-bone rounded-lg p-4 space-y-2">
                <p className="text-xs font-bold text-ink/60 uppercase tracking-wide mb-2">Required Conditions</p>
                {chk("is_extreme_violation",  cashForm.is_extreme_violation,  setCashForm, "This is an extreme platform violation")}
                {chk("user_not_at_fault",     cashForm.user_not_at_fault,     setCashForm, "User was not at fault")}
                {chk("is_legal",              cashForm.is_legal,              setCashForm, "Refund is legally appropriate")}
                {chk("no_harm_to_wai",        cashForm.no_harm_to_wai,        setCashForm, "Refund causes no harm to WAI")}
                {chk("supervisor_approved",   cashForm.supervisor_approved,   setCashForm, "Supervisor has approved this refund")}
              </div>
              <button type="submit" disabled={cashBusy} className="bg-red-600 text-white text-sm font-semibold px-4 py-2 rounded-lg disabled:opacity-50">
                {cashBusy ? "Processing…" : "Submit Cash Refund"}
              </button>
            </form>
          </div>
        )}

        {/* ── SAGE SESSIONS TAB ── */}
        {tab === "sage" && (
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <p className="text-sm text-ink/60">{sessions.length} session{sessions.length !== 1 ? "s" : ""}</p>
              <button onClick={loadSessions} className="text-xs text-ink/50 hover:text-ink flex items-center gap-1"><RefreshCw className="w-3 h-3" /> Refresh</button>
            </div>
            {sessions.length === 0 && <p className="text-center py-10 text-ink/50 text-sm">No Sage sessions found.</p>}
            {sessions.map(s => (
              <div key={s._id || s.id} className="bg-white border border-ink/10 rounded-xl px-5 py-4">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <Clock className="w-4 h-4 text-ink/40" />
                      <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${s.status === "resolved" ? "bg-green-100 text-green-700" : s.status === "escalated" ? "bg-red-100 text-red-700" : "bg-amber-100 text-amber-700"}`}>
                        {s.status || "pending"}
                      </span>
                    </div>
                    <p className="font-semibold text-sm text-ink">{s.trigger_reason || "Conduct review"}</p>
                    <p className="text-xs text-ink/50 mt-0.5">User: {s.user_id} · Fee: {fmt(s.fee_amount || 300)} · {s.created_at ? new Date(s.created_at).toLocaleString() : "—"}</p>
                  </div>
                  {s.status === "pending_correction" && (
                    <div className="flex gap-2 shrink-0">
                      <button onClick={() => resolveSession(s._id || s.id, true)} disabled={resolving[s._id || s.id]}
                        className="flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-lg bg-green-50 text-green-700 border border-green-200 hover:bg-green-100 disabled:opacity-50">
                        <CheckCircle className="w-3.5 h-3.5" /> Self-corrected (waive fee)
                      </button>
                      <button onClick={() => resolveSession(s._id || s.id, false)} disabled={resolving[s._id || s.id]}
                        className="flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-lg bg-red-50 text-red-700 border border-red-200 hover:bg-red-100 disabled:opacity-50">
                        <XCircle className="w-3.5 h-3.5" /> Refused (escalate)
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
