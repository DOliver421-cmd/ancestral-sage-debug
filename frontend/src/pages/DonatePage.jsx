import { useState } from "react";
import { api } from "../lib/api";
import { Heart } from "lucide-react";
import { toast } from "sonner";

const PRESET_AMOUNTS = [10, 25, 50, 100, 250];

export default function DonatePage() {
  const [selected, setSelected] = useState(25);
  const [custom, setCustom] = useState("");
  const [loading, setLoading] = useState(false);

  const effectiveAmount = custom ? parseFloat(custom) : selected;
  const amountCents = Math.round(effectiveAmount * 100);
  const valid = effectiveAmount >= 1 && effectiveAmount <= 10000;

  async function donate() {
    if (!valid) return toast.error("Please enter an amount between $1 and $10,000.");
    setLoading(true);
    try {
      const { data } = await api.post("/payments/checkout", {
        product_key: "donation",
        amount_cents: amountCents,
        quantity: 1,
      });
      window.location.href = data.url;
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Could not start checkout.");
      setLoading(false);
    }
  }

  return (
    <div className="p-8 max-w-2xl mx-auto">
      <div className="flex items-center gap-3 mb-2">
        <Heart className="w-8 h-8 text-red-500" />
        <h1 className="font-heading text-3xl font-bold text-ink">Support the WAI Mission</h1>
      </div>
      <p className="text-ink/60 mb-8">
        Your donation directly funds workforce training scholarships, lab equipment, and the M.O.R.E. community
        platform. Every dollar keeps the path to a skilled trade open for the next generation.
      </p>

      <div className="bg-white border border-ink/10 rounded-2xl p-6 shadow-sm space-y-6">
        <div>
          <div className="text-xs font-black uppercase tracking-widest text-ink/40 mb-3">Choose an amount</div>
          <div className="flex flex-wrap gap-3">
            {PRESET_AMOUNTS.map((amt) => (
              <button
                key={amt}
                onClick={() => { setSelected(amt); setCustom(""); }}
                className={`px-5 py-2.5 rounded-lg font-bold text-sm border-2 transition-colors ${
                  selected === amt && !custom
                    ? "border-signal bg-signal/10 text-ink"
                    : "border-ink/10 text-ink/60 hover:border-ink/30"
                }`}
              >
                ${amt}
              </button>
            ))}
          </div>
        </div>

        <div>
          <div className="text-xs font-black uppercase tracking-widest text-ink/40 mb-2">Or enter a custom amount</div>
          <div className="relative">
            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-ink/40 font-bold">$</span>
            <input
              type="number"
              min="1"
              max="10000"
              step="1"
              value={custom}
              onChange={(e) => { setCustom(e.target.value); setSelected(null); }}
              placeholder="Enter amount"
              className="w-full pl-8 pr-4 py-3 border-2 border-ink/10 rounded-lg text-ink focus:outline-none focus:border-signal font-medium"
            />
          </div>
        </div>

        <div className="border-t border-ink/10 pt-4 flex items-center justify-between">
          <div>
            <div className="text-xs text-ink/40 uppercase tracking-widest">Your donation</div>
            <div className="font-heading font-bold text-3xl text-ink">
              ${valid ? effectiveAmount.toFixed(2) : "—"}
            </div>
          </div>
          <button
            onClick={donate}
            disabled={loading || !valid}
            className="px-8 py-3 bg-ink text-white font-bold rounded-lg hover:bg-ink/80 transition-colors disabled:opacity-50 flex items-center gap-2"
          >
            <Heart className="w-4 h-4" />
            {loading ? "Redirecting…" : "Donate"}
          </button>
        </div>
      </div>

      <p className="text-xs text-ink/40 text-center mt-4">
        Payments are processed securely by Stripe. WAI Institute / LCE is a registered organization.
      </p>
    </div>
  );
}
