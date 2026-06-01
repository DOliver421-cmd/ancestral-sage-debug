import { useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import { ShoppingBag, Package, BookOpen, Shirt, LogIn, UserPlus, X } from "lucide-react";
import { toast } from "sonner";

const ITEMS = [
  {
    key: "tshirt",
    name: "WAI Institute T-Shirt",
    price: "$25.00",
    icon: Shirt,
    description: "Official WAI Workforce tee. Show your trade pride.",
    badge: null,
  },
  {
    key: "workbook",
    name: "WAI Workforce Workbook",
    price: "$15.00",
    icon: BookOpen,
    description: "Printed study guide — electrical theory, code, and lab prep.",
    badge: null,
  },
  {
    key: "kit",
    name: "WAI Workforce Kit",
    price: "$45.00",
    icon: Package,
    description: "T-Shirt + Workbook bundle. Best value for new trainees.",
    badge: "Best Value",
  },
  {
    key: "credential",
    name: "Credential Certificate",
    price: "$25.00",
    icon: ShoppingBag,
    description: "Official printed credential certificate mailed to you.",
    badge: null,
  },
];

function AuthGate({ onClose }) {
  return (
    <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4 backdrop-blur-sm">
      <div className="bg-white w-full max-w-sm shadow-2xl rounded-2xl overflow-hidden">
        <div className="bg-gradient-to-r from-amber-500 to-orange-500 p-6 text-white">
          <div className="flex items-center justify-between">
            <div className="font-heading font-extrabold text-xl">Sign in to purchase</div>
            <button onClick={onClose} className="text-white/60 hover:text-white"><X className="w-5 h-5" /></button>
          </div>
          <p className="text-white/80 text-sm mt-2">Browse freely. Purchase with an account — it's free to join.</p>
        </div>
        <div className="p-6 flex flex-col gap-3">
          <Link to="/register" className="flex items-center justify-center gap-2 bg-amber-500 hover:bg-amber-400 text-ink font-bold py-3 rounded-xl transition-colors">
            <UserPlus className="w-4 h-4" /> Create Free Account
          </Link>
          <Link to="/login" className="flex items-center justify-center gap-2 border-2 border-ink/20 hover:border-ink font-bold py-3 rounded-xl transition-colors text-sm">
            <LogIn className="w-4 h-4" /> Sign In
          </Link>
        </div>
      </div>
    </div>
  );
}

export default function Store() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(null);
  const [showGate, setShowGate] = useState(false);

  async function checkout(key) {
    if (!user) { setShowGate(true); return; }
    setLoading(key);
    try {
      const { data } = await api.post("/payments/checkout", { product_key: key, quantity: 1 });
      window.location.href = data.url;
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Checkout failed. Please try again.");
      setLoading(null);
    }
  }

  return (
    <div className="p-8 max-w-5xl mx-auto">
      <div className="mb-8">
        <h1 className="font-heading text-3xl font-bold text-ink mb-2">WAI Store</h1>
        <p className="text-ink/60">Support the mission. Gear up for the trade.</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-2 gap-6">
        {ITEMS.map((item) => {
          const Icon = item.icon;
          return (
            <div key={item.key} className="bg-white border border-ink/10 rounded-2xl p-6 flex flex-col gap-4 shadow-sm relative">
              {item.badge && (
                <span className="absolute top-4 right-4 bg-signal text-ink text-[10px] font-black px-2 py-0.5 rounded-full uppercase tracking-widest">
                  {item.badge}
                </span>
              )}
              <div className="w-12 h-12 bg-bone rounded-xl flex items-center justify-center">
                <Icon className="w-6 h-6 text-ink/60" />
              </div>
              <div>
                <div className="font-heading font-bold text-lg text-ink">{item.name}</div>
                <div className="text-ink/60 text-sm mt-1">{item.description}</div>
              </div>
              <div className="mt-auto flex items-center justify-between pt-4 border-t border-ink/10">
                <span className="font-heading font-bold text-2xl text-ink">{item.price}</span>
                <button
                  onClick={() => checkout(item.key)}
                  disabled={!!loading}
                  className="px-5 py-2 bg-ink text-white text-sm font-bold rounded-lg hover:bg-ink/80 transition-colors disabled:opacity-50"
                >
                  {loading === item.key ? "Redirecting…" : "Buy Now"}
                </button>
              </div>
            </div>
          );
        })}
      </div>
      {showGate && <AuthGate onClose={() => setShowGate(false)} />}
    </div>
  );
}
