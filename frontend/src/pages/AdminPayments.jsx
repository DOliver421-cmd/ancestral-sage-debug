import { useEffect, useState } from "react";
import { api } from "../lib/api";
import { DollarSign, Receipt } from "lucide-react";
import { toast } from "sonner";

const MODE_LABELS = {
  payment: "One-time",
  subscription: "Subscription",
  subscription_renewal: "Renewal",
};

export default function AdminPayments() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/admin/payments")
      .then(({ data }) => setData(data))
      .catch(() => toast.error("Could not load payment data."))
      .finally(() => setLoading(false));
  }, []);

  const totalDollars = data ? (data.total_revenue_cents / 100).toFixed(2) : "—";

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <div className="flex items-center gap-3 mb-8">
        <Receipt className="w-7 h-7 text-ink/60" />
        <h1 className="font-heading text-3xl font-bold text-ink">Revenue</h1>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-8">
        <div className="bg-white border border-ink/10 rounded-2xl p-6 shadow-sm">
          <div className="text-xs font-black uppercase tracking-widest text-ink/40 mb-1">Total Revenue</div>
          <div className="font-heading font-bold text-4xl text-ink flex items-center gap-1">
            <DollarSign className="w-7 h-7 text-signal" />{totalDollars}
          </div>
        </div>
        <div className="bg-white border border-ink/10 rounded-2xl p-6 shadow-sm">
          <div className="text-xs font-black uppercase tracking-widest text-ink/40 mb-1">Total Transactions</div>
          <div className="font-heading font-bold text-4xl text-ink">{data?.count ?? "—"}</div>
        </div>
      </div>

      {loading ? (
        <div className="text-ink/40 py-16 text-center">Loading…</div>
      ) : !data?.payments?.length ? (
        <div className="text-center py-16 text-ink/40">
          <Receipt className="w-12 h-12 mx-auto mb-3 opacity-30" />
          <div>No transactions yet.</div>
        </div>
      ) : (
        <div className="bg-white rounded-2xl border border-ink/10 overflow-hidden shadow-sm">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-ink/10 bg-bone text-xs font-black uppercase tracking-widest text-ink/40">
                <th className="px-6 py-3 text-left">Date</th>
                <th className="px-6 py-3 text-left">User</th>
                <th className="px-6 py-3 text-left">Product</th>
                <th className="px-6 py-3 text-left">Type</th>
                <th className="px-6 py-3 text-right">Amount</th>
                <th className="px-6 py-3 text-center">Status</th>
              </tr>
            </thead>
            <tbody>
              {data.payments.map((p) => (
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
                      p.status === "paid" ? "bg-green-100 text-green-700" : "bg-red-100 text-red-600"
                    }`}>{p.status}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
