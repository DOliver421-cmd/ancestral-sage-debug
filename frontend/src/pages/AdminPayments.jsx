import { useCallback, useEffect, useState } from "react";
import AppShell from "../components/AppShell";
import { api } from "../lib/api";
import { Link } from "react-router-dom";
import { DollarSign, Receipt, RefreshCw, AlertTriangle, CheckCircle2, Loader2, KeyRound } from "lucide-react";
import { toast } from "sonner";

const MODE_LABELS = {
  payment: "One-time",
  subscription: "Subscription",
  subscription_renewal: "Renewal",
};

export default function AdminPayments() {
  const [data, setData] = useState(null);
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    const [p, h] = await Promise.allSettled([
      api.get("/admin/payments"),
      api.get("/health"),
    ]);
    if (p.status === "fulfilled") setData(p.value.data);
    else setError(p.reason?.response?.data?.detail || p.reason?.message || "Could not load payment data.");
    if (h.status === "fulfilled") setHealth(h.value.data);
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  const payConfigured = health?.checks?.payments?.status === "configured";
  const records = data?.payments || [];
  const paidCount = records.filter((r) => r.status === "paid").length;
  const totalDollars = data ? (data.total_revenue_cents / 100).toFixed(2) : "—";

  return (
    <AppShell>
    <div className="p-8 max-w-6xl mx-auto">
      <div className="flex items-center justify-between gap-4 flex-wrap mb-8">
        <div className="flex items-center gap-3">
          <Receipt className="w-7 h-7 text-ink/60" />
          <div>
            <h1 className="font-heading text-3xl font-bold text-ink">Revenue</h1>
            <p className="text-sm text-ink/50 mt-1">Live payment records from the platform — refunds and disputes included in the list below.</p>
          </div>
        </div>
        <button onClick={load} disabled={loading}
          className="flex items-center gap-1.5 px-4 py-2 border border-copper text-copper text-xs font-black uppercase tracking-widest rounded-lg hover:bg-copper/5 transition-colors disabled:opacity-50">
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} /> Refresh
        </button>
      </div>

      {/* Payment config status — the real reason a zero here means zero */}
      <div className={`rounded-xl border p-4 mb-6 flex items-start gap-3 text-sm ${
        payConfigured ? "bg-green-50 border-green-200 text-green-800" : "bg-amber-50 border-amber-200 text-amber-800"
      }`}>
        {payConfigured
          ? <CheckCircle2 className="w-5 h-5 shrink-0" />
          : <AlertTriangle className="w-5 h-5 shrink-0" />}
        <div>
          <div className="font-bold">{payConfigured ? "Payments are configured" : "Payments are NOT configured"}</div>
          <div className="text-xs mt-0.5 opacity-80">
            {payConfigured
              ? "A payment key is set (Stripe / Lemon Squeezy / Gumroad). Transactions will appear here as they process."
              : "No payment key is set, so no transaction can ever succeed — which is why this page is empty. Add a key on the Providers page, then new purchases will show up here."}
          </div>
          {!payConfigured && (
            <Link to="/admin/providers" className="inline-flex items-center gap-1.5 text-xs font-black mt-2 text-amber-900 underline underline-offset-2">
              <KeyRound className="w-3.5 h-3.5" /> Add a payment key on the Providers page →
            </Link>
          )}
        </div>
      </div>

      {error && (
        <div className="rounded-xl border border-red-200 bg-red-50 p-4 mb-6 text-sm text-red-700 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 shrink-0" />
          <div>
            <div className="font-bold">Could not load payment data.</div>
            <div className="text-xs mt-0.5">{error} — this is a site problem, not yours.</div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-3 gap-4 mb-8 max-md:grid-cols-1">
        <div className="bg-white border border-ink/10 rounded-2xl p-6 shadow-sm">
          <div className="text-xs font-black uppercase tracking-widest text-ink/60 mb-1">Total Revenue (paid)</div>
          <div className="font-heading font-bold text-4xl text-ink flex items-center gap-1">
            <DollarSign className="w-7 h-7 text-signal" />{totalDollars}
          </div>
        </div>
        <div className="bg-white border border-ink/10 rounded-2xl p-6 shadow-sm">
          <div className="text-xs font-black uppercase tracking-widest text-ink/60 mb-1">Total Transactions</div>
          <div className="font-heading font-bold text-4xl text-ink">{data?.count ?? "—"}</div>
        </div>
        <div className="bg-white border border-ink/10 rounded-2xl p-6 shadow-sm">
          <div className="text-xs font-black uppercase tracking-widest text-ink/60 mb-1">Paid / Pending</div>
          <div className="font-heading font-bold text-4xl text-ink">{paidCount}<span className="text-lg text-ink/40"> / {records.length - paidCount}</span></div>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-16 text-ink/40"><Loader2 className="w-6 h-6 animate-spin mr-2" /> Loading payments…</div>
      ) : records.length === 0 ? (
        <div className="text-center py-16 text-ink/60">
          <Receipt className="w-12 h-12 mx-auto mb-3 opacity-30" />
          <div className="font-bold">No transactions yet.</div>
          <div className="text-sm mt-1 max-w-md mx-auto text-ink/40">
            {payConfigured
              ? "No purchases have been recorded. When a checkout succeeds, the transaction lands here."
              : "This list is empty because no payment provider is configured — the Providers page is the place to fix that."}
          </div>
        </div>
      ) : (
        <div className="bg-white rounded-2xl border border-ink/10 overflow-hidden shadow-sm">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-ink/10 bg-bone text-xs font-black uppercase tracking-widest text-ink/60">
                <th className="px-6 py-3 text-left">Date</th>
                <th className="px-6 py-3 text-left">User</th>
                <th className="px-6 py-3 text-left">Product</th>
                <th className="px-6 py-3 text-left">Type</th>
                <th className="px-6 py-3 text-right">Amount</th>
                <th className="px-6 py-3 text-center">Status</th>
              </tr>
            </thead>
            <tbody>
              {records.map((p) => (
                <tr key={p.id} className="border-b border-ink/5 hover:bg-bone/50 transition-colors">
                  <td className="px-6 py-3 text-ink/60 whitespace-nowrap">
                    {new Date(p.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-3 text-ink/60 text-xs font-mono">{p.user_id?.slice(0, 8) ?? "—"}</td>
                  <td className="px-6 py-3 font-medium text-ink">
                    {(p.product_key || "—").replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
                  </td>
                  <td className="px-6 py-3 text-ink/60">{MODE_LABELS[p.mode] || p.mode || "—"}</td>
                  <td className="px-6 py-3 text-right font-mono font-semibold text-ink">
                    ${((p.amount_cents || 0) / 100).toFixed(2)}
                  </td>
                  <td className="px-6 py-3 text-center">
                    <span className={`px-2 py-0.5 rounded-full text-[11px] font-bold uppercase ${
                      p.status === "paid" ? "bg-green-100 text-green-700" : p.status === "refunded" ? "bg-amber-100 text-amber-700" : "bg-red-100 text-red-600"
                    }`}>{p.status}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
    </AppShell>
  );
}
