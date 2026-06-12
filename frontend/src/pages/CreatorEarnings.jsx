import { useState, useEffect } from "react";
import AppShell from "../components/AppShell";
import CreatorContextBar from "../components/CreatorContextBar";
import BackButton from "../components/BackButton";
import { api } from "../lib/api";
import { toast } from "sonner";
import { DollarSign, TrendingUp, Clock, CheckCircle, Building, AlertCircle, ChevronDown, ChevronUp } from "lucide-react";

export default function CreatorEarnings() {
  const [summary, setSummary] = useState(null);
  const [payouts, setPayouts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState("overview");
  const [bankForm, setBankForm] = useState({ account_holder_name: "", routing_number: "", account_number: "", account_type: "checking" });
  const [bankOnFile, setBankOnFile] = useState(null);
  const [bankSaving, setBankSaving] = useState(false);
  const [expandedMonth, setExpandedMonth] = useState(null);

  useEffect(() => { load(); }, []);

  async function load() {
    setLoading(true);
    try {
      const [earningsRes, payoutsRes, bankRes] = await Promise.all([
        api.get("/creator/earnings"),
        api.get("/creator/payouts"),
        api.get("/creator/bank-account"),
      ]);
      setSummary(earningsRes.data);
      setPayouts(payoutsRes.data.payouts || []);
      setBankOnFile(bankRes.data.bank_account);
    } catch {
      toast.error("Could not load earnings data.");
    } finally {
      setLoading(false);
    }
  }

  async function saveBank(e) {
    e.preventDefault();
    if (bankForm.routing_number.length !== 9 || !/^\d{9}$/.test(bankForm.routing_number)) {
      toast.error("Routing number must be exactly 9 digits.");
      return;
    }
    if (bankForm.account_number.length < 4) {
      toast.error("Account number is too short.");
      return;
    }
    setBankSaving(true);
    try {
      const { data } = await api.post("/creator/bank-account", bankForm);
      setBankOnFile({ ...bankForm, account_number_masked: data.account_number_masked });
      setBankForm({ account_holder_name: "", routing_number: "", account_number: "", account_type: "checking" });
      toast.success("Bank account saved. Payouts will be sent on the 1st.");
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Could not save bank account.");
    } finally {
      setBankSaving(false);
    }
  }

  const fmt = (cents) => `$${((cents || 0) / 100).toFixed(2)}`;

  return (
    <AppShell>
      <CreatorContextBar current="earnings" />
      <div className="px-6 py-10 max-w-4xl">
        <BackButton className="mb-4" />
        <div className="overline text-copper mb-1">Creator Studio</div>
        <h1 className="font-heading text-4xl font-bold text-ink">Earnings & Payouts</h1>
        <p className="text-ink/60 mt-1 mb-8">
          You keep <span className="font-bold text-copper">70%</span> of every sale. WAI keeps 30%. Payouts on the 1st of each month.
        </p>

        {loading ? (
          <div className="text-ink/50 text-sm py-12 text-center">Loading earnings…</div>
        ) : (
          <>
            {/* Summary cards */}
            <div className="grid grid-cols-3 gap-4 mb-8">
              <EarnCard
                icon={TrendingUp}
                label="Total Earned"
                value={fmt(summary?.total_earned_cents)}
                accent="text-green-600"
              />
              <EarnCard
                icon={Clock}
                label="Pending Payout"
                value={fmt(summary?.total_pending_cents)}
                accent="text-amber-600"
              />
              <EarnCard
                icon={CheckCircle}
                label="Total Paid Out"
                value={fmt(summary?.total_paid_cents)}
                accent="text-ink"
              />
            </div>

            {/* Bank account notice */}
            {!summary?.bank_account_on_file && (
              <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 flex items-start gap-3 mb-6">
                <AlertCircle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
                <div>
                  <div className="font-semibold text-amber-800">No payout account on file</div>
                  <div className="text-sm text-amber-700 mt-0.5">
                    Add your bank account below so we can send your earnings on the 1st.
                  </div>
                </div>
                <button onClick={() => setTab("bank")} className="ml-auto text-sm font-bold text-amber-700 underline whitespace-nowrap">
                  Add Account
                </button>
              </div>
            )}

            {/* Tabs */}
            <div className="flex gap-1 mb-6 border-b border-ink/10">
              {[["overview", "Monthly Breakdown"], ["payouts", "Payout History"], ["bank", "Bank Account"]].map(([key, label]) => (
                <button
                  key={key}
                  onClick={() => setTab(key)}
                  className={`px-4 py-2 text-sm font-bold border-b-2 transition-colors ${tab === key ? "border-copper text-copper" : "border-transparent text-ink/50 hover:text-ink"}`}
                >
                  {label}
                </button>
              ))}
            </div>

            {/* Overview tab */}
            {tab === "overview" && (
              <div>
                {(!summary?.months || summary.months.length === 0) ? (
                  <EmptyState
                    icon={DollarSign}
                    title="No sales yet"
                    body="When students enroll in your courses, your earnings will appear here by month."
                  />
                ) : (
                  <div className="space-y-2">
                    {summary.months.map(m => (
                      <div key={m.period} className="card-flat overflow-hidden">
                        <div
                          className="flex items-center gap-4 p-4 cursor-pointer hover:bg-bone/50 transition-colors"
                          onClick={() => setExpandedMonth(expandedMonth === m.period ? null : m.period)}
                        >
                          <div className="flex-1">
                            <div className="font-heading font-bold text-ink">{formatPeriod(m.period)}</div>
                            <div className="text-xs text-ink/50 mt-0.5">{m.sales} sale{m.sales !== 1 ? "s" : ""}</div>
                          </div>
                          <div className="text-right">
                            <div className="font-bold text-green-700">{fmt(m.creator_share_cents)}</div>
                            <div className="text-xs text-ink/40">gross {fmt(m.gross_cents)}</div>
                          </div>
                          <PayoutBadge status={m.payout_status} />
                          {expandedMonth === m.period
                            ? <ChevronUp className="w-4 h-4 text-ink/30" />
                            : <ChevronDown className="w-4 h-4 text-ink/30" />}
                        </div>
                        {expandedMonth === m.period && (
                          <div className="border-t border-ink/10 px-4 py-3 bg-bone/30 text-sm text-ink/60 grid grid-cols-3 gap-4">
                            <div><span className="font-semibold text-ink">Gross</span><br />{fmt(m.gross_cents)}</div>
                            <div><span className="font-semibold text-ink">Your 70%</span><br />{fmt(m.creator_share_cents)}</div>
                            <div><span className="font-semibold text-ink">Platform 30%</span><br />{fmt(m.gross_cents - m.creator_share_cents)}</div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Payout history tab */}
            {tab === "payouts" && (
              <div>
                {payouts.length === 0 ? (
                  <EmptyState
                    icon={CheckCircle}
                    title="No payouts yet"
                    body="Your first payout will be sent on the 1st of next month once you have a bank account on file."
                  />
                ) : (
                  <div className="space-y-2">
                    {payouts.map(p => (
                      <div key={p.payout_id} className="card-flat p-4 flex items-center gap-4">
                        <div className="flex-1">
                          <div className="font-heading font-bold">{fmt(p.amount_cents)}</div>
                          <div className="text-xs text-ink/50 mt-0.5">
                            {p.sale_count} sale{p.sale_count !== 1 ? "s" : ""} · {new Date(p.created_at).toLocaleDateString()}
                          </div>
                        </div>
                        <PayoutBadge status={p.status} />
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Bank account tab */}
            {tab === "bank" && (
              <div className="max-w-lg">
                {bankOnFile && (
                  <div className="bg-green-50 border border-green-200 rounded-xl p-4 flex items-center gap-3 mb-6">
                    <CheckCircle className="w-5 h-5 text-green-600 shrink-0" />
                    <div>
                      <div className="font-semibold text-green-800">Bank account on file</div>
                      <div className="text-sm text-green-700">
                        {bankOnFile.account_holder_name} · {bankOnFile.account_type} ····{bankOnFile.account_number_masked?.slice(-4)}
                      </div>
                    </div>
                  </div>
                )}
                <div className="card-flat p-6">
                  <div className="flex items-center gap-2 mb-4">
                    <Building className="w-5 h-5 text-copper" />
                    <h2 className="font-heading font-bold text-lg">{bankOnFile ? "Update" : "Add"} Bank Account</h2>
                  </div>
                  <form onSubmit={saveBank} className="space-y-4">
                    <div>
                      <label className="overline text-xs text-ink/50 block mb-1">Account Holder Name</label>
                      <input
                        className="input w-full"
                        value={bankForm.account_holder_name}
                        onChange={e => setBankForm(f => ({ ...f, account_holder_name: e.target.value }))}
                        placeholder="Full legal name"
                        required
                      />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="overline text-xs text-ink/50 block mb-1">Routing Number</label>
                        <input
                          className="input w-full font-mono"
                          value={bankForm.routing_number}
                          onChange={e => setBankForm(f => ({ ...f, routing_number: e.target.value.replace(/\D/g, "").slice(0, 9) }))}
                          placeholder="9 digits"
                          maxLength={9}
                          required
                        />
                      </div>
                      <div>
                        <label className="overline text-xs text-ink/50 block mb-1">Account Number</label>
                        <input
                          className="input w-full font-mono"
                          value={bankForm.account_number}
                          onChange={e => setBankForm(f => ({ ...f, account_number: e.target.value.replace(/\D/g, "").slice(0, 17) }))}
                          placeholder="4–17 digits"
                          required
                        />
                      </div>
                    </div>
                    <div>
                      <label className="overline text-xs text-ink/50 block mb-1">Account Type</label>
                      <div className="flex gap-4">
                        {["checking", "savings"].map(t => (
                          <label key={t} className="flex items-center gap-2 text-sm cursor-pointer">
                            <input
                              type="radio"
                              name="account_type"
                              value={t}
                              checked={bankForm.account_type === t}
                              onChange={() => setBankForm(f => ({ ...f, account_type: t }))}
                            />
                            {t.charAt(0).toUpperCase() + t.slice(1)}
                          </label>
                        ))}
                      </div>
                    </div>
                    <button type="submit" disabled={bankSaving} className="btn-copper w-full text-sm disabled:opacity-50">
                      {bankSaving ? "Saving…" : "Save Bank Account"}
                    </button>
                  </form>
                  <p className="text-xs text-ink/40 mt-4 text-center">
                    Your account details are encrypted at rest. Payouts sent via ACH on the 1st of each month.
                  </p>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </AppShell>
  );
}

function EarnCard({ icon: Icon, label, value, accent }) {
  return (
    <div className="card-flat p-5">
      <Icon className={`w-5 h-5 mb-2 ${accent}`} />
      <div className={`font-heading text-2xl font-black ${accent}`}>{value}</div>
      <div className="overline text-ink/50 mt-1">{label}</div>
    </div>
  );
}

function PayoutBadge({ status }) {
  if (status === "paid" || status === "processing") return (
    <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-green-100 text-green-700">
      {status === "processing" ? "Processing" : "Paid"}
    </span>
  );
  return <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-amber-100 text-amber-700">Pending</span>;
}

function EmptyState({ icon: Icon, title, body }) {
  return (
    <div className="card-flat p-12 text-center">
      <Icon className="w-10 h-10 text-ink/20 mx-auto mb-3" />
      <div className="font-heading font-bold text-ink/60">{title}</div>
      <p className="text-sm text-ink/40 mt-1 max-w-sm mx-auto">{body}</p>
    </div>
  );
}

function formatPeriod(period) {
  const [y, m] = period.split("-");
  return new Date(parseInt(y), parseInt(m) - 1).toLocaleDateString("en-US", { month: "long", year: "numeric" });
}
