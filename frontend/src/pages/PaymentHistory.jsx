import { useEffect, useState } from "react";
import { api } from "../lib/api";
import { Receipt, ExternalLink } from "lucide-react";
import { toast } from "sonner";

const LABELS = {
  payment: "One-time",
  subscription: "Subscription",
  subscription_renewal: "Renewal",
};

export default function PaymentHistory() {
  const [payments, setPayments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [portalLoading, setPortalLoading] = useState(false);

  useEffect(() => {
    api.get("/payments/history")
      .then(({ data }) => setPayments(data.payments || []))
      .catch(() => toast.error("Could not load payment history."))
      .finally(() => setLoading(false));
  }, []);

  async function openPortal() {
    setPortalLoading(true);
    try {
      const { data } = await api.get("/payments/portal");
      window.location.href = data.url;
    } catch (e) {
      toast.error(e?.response?.data?.detail || "No billing account found.");
      setPortalLoading(false);
    }
  }

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-3">
          <Receipt className="w-7 h-7 text-ink/60" />
          <h1 className="font-heading text-3xl font-bold text-ink">Payment History</h1>
        </div>
        <button
          onClick={openPortal}
          disabled={portalLoading}
          className="flex items-center gap-2 px-4 py-2 border border-ink/20 text-ink text-sm font-bold rounded-lg hover:bg-ink/5 transition-colors disabled:opacity-50"
        >
          <ExternalLink className="w-4 h-4" />
          {portalLoading ? "Loading…" : "Manage Subscriptions"}
        </button>
      </div>

      {loading ? (
        <div className="text-ink/60 py-16 text-center">Loading…</div>
      ) : payments.length === 0 ? (
        <div className="text-center py-16 text-ink/60">
          <Receipt className="w-12 h-12 mx-auto mb-3 opacity-30" />
          <div>No payments yet.</div>
        </div>
      ) : (
        <div className="bg-white rounded-2xl border border-ink/10 overflow-hidden shadow-sm">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-ink/10 bg-bone text-xs font-black uppercase tracking-widest text-ink/60">
                <th className="px-6 py-3 text-left">Date</th>
                <th className="px-6 py-3 text-left">Item</th>
                <th className="px-6 py-3 text-left">Type</th>
                <th className="px-6 py-3 text-right">Amount</th>
                <th className="px-6 py-3 text-center">Status</th>
              </tr>
            </thead>
            <tbody>
              {payments.map((p) => (
                <tr key={p.id} className="border-b border-ink/5 hover:bg-bone/50 transition-colors">
                  <td className="px-6 py-4 text-ink/60 whitespace-nowrap">
                    {new Date(p.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 font-medium text-ink">
                    {p.product_key
                      ? p.product_key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())
                      : "—"}
                  </td>
                  <td className="px-6 py-4 text-ink/60">
                    {LABELS[p.mode] || p.mode || "—"}
                  </td>
                  <td className="px-6 py-4 text-right font-mono font-semibold text-ink">
                    ${((p.amount_cents || 0) / 100).toFixed(2)}
                  </td>
                  <td className="px-6 py-4 text-center">
                    <span className={`px-2 py-0.5 rounded-full text-[11px] font-bold uppercase ${
                      p.status === "paid"
                        ? "bg-green-100 text-green-700"
                        : "bg-red-100 text-red-600"
                    }`}>
                      {p.status}
                    </span>
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
