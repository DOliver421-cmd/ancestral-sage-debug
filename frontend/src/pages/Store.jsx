import { useState } from "react";
import { api } from "../lib/api";
import { ShoppingBag, Package, BookOpen, Shirt } from "lucide-react";
import { toast } from "sonner";

const ITEMS = [
  {
    key: "tshirt",
    name: "WAI Institute T-Shirt",
    price: "$25.00",
    icon: Shirt,
    description: "Official WAI Apprentice tee. Show your trade pride.",
    badge: null,
  },
  {
    key: "workbook",
    name: "WAI Apprentice Workbook",
    price: "$15.00",
    icon: BookOpen,
    description: "Printed study guide — electrical theory, code, and lab prep.",
    badge: null,
  },
  {
    key: "kit",
    name: "WAI Apprentice Kit",
    price: "$45.00",
    icon: Package,
    description: "T-Shirt + Workbook bundle. Best value for new apprentices.",
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

export default function Store() {
  const [loading, setLoading] = useState(null);

  async function checkout(key) {
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
    </div>
  );
}
