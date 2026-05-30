import { useState, useEffect } from "react";
import { TrendingDown, Gift, DollarSign } from "lucide-react";
import PartnershipPricing from "../components/PartnershipPricing";
import { PARTNERSHIP_LEVELS } from "../lib/partnership_pricing";
import { api } from "../lib/api";

export default function PartnershipDiscounts() {
  const [status, setStatus] = useState(null);

  useEffect(() => {
    api.get("/partnership/status").then(r => setStatus(r.data)).catch(() => {});
  }, []);

  const userPoints = status?.points ?? 0;
  const userTier = status?.tier ?? null;

  return (
    <div className="min-h-screen bg-bone text-ink">
      <div className="border-b border-ink/10 bg-white">
        <div className="max-w-7xl mx-auto px-6 py-12">
          <h1 className="font-heading text-4xl font-bold mb-4">Partnership Pricing</h1>
          <p className="text-xl text-ink/60">
            The deeper your partnership, the better our economics work for you.
          </p>
          {status && (
            <div className="mt-4 inline-flex items-center gap-3 bg-copper/10 border border-copper rounded-full px-5 py-2">
              <span className="font-bold text-copper">{status.tier}</span>
              <span className="text-ink/70">·</span>
              <span className="text-ink/70">{status.points.toLocaleString()} pts</span>
              {status.next_tier && (
                <>
                  <span className="text-ink/70">·</span>
                  <span className="text-sm text-ink/60">{status.points_to_next} pts to {status.next_tier}</span>
                </>
              )}
            </div>
          )}
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-12">
        <div className="mb-16">
          <div className="bg-gradient-to-r from-copper/10 to-copper/5 border-2 border-copper rounded-lg p-8">
            <h2 className="font-heading text-2xl font-bold mb-4 text-ink">How It Works</h2>
            <div className="grid md:grid-cols-3 gap-8">
              <div>
                <h3 className="font-bold text-lg mb-2">Seed Level (0-300 pts)</h3>
                <p className="text-ink/70 mb-4">You're just starting. Pay full price to support the platform.</p>
                <div className="bg-white/60 rounded p-3">
                  <p className="text-xs text-ink/60 mb-2">Example: $9.99 course</p>
                  <p className="font-bold text-lg text-ink">$9.99</p>
                  <p className="text-xs text-ink/60">0% discount</p>
                </div>
              </div>
              <div>
                <h3 className="font-bold text-lg mb-2">Rooted → Builder</h3>
                <p className="text-ink/70 mb-4">Growing your impact. Start saving 5-10%.</p>
                <div className="bg-green-50 rounded p-3 border border-green-200">
                  <p className="text-xs text-green-700 mb-2">Example: $9.99 course</p>
                  <p className="font-bold text-lg text-green-600">$9.49</p>
                  <p className="text-xs text-green-700">5% discount</p>
                </div>
              </div>
              <div>
                <h3 className="font-bold text-lg mb-2">Steward → Elder</h3>
                <p className="text-ink/70 mb-4">Deepest partnership. Max savings at 15%.</p>
                <div className="bg-green-50 rounded p-3 border border-green-200">
                  <p className="text-xs text-green-700 mb-2">Example: $9.99 course</p>
                  <p className="font-bold text-lg text-green-600">$8.49</p>
                  <p className="text-xs text-green-700">15% discount</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="mb-16">
          <h2 className="font-heading text-2xl font-bold mb-8 text-ink">Your Discount Structure</h2>
          <div className="grid gap-6">
            {PARTNERSHIP_LEVELS.map((level, idx) => {
              const isActive = level.minPoints <= userPoints && userPoints < level.maxPoints;
              return (
                <div
                  key={idx}
                  className={`rounded-lg border-2 p-8 transition-all ${isActive ? "border-copper bg-copper/5" : "border-ink/10 bg-white"}`}
                >
                  <div className="flex items-start justify-between mb-6">
                    <div className="flex items-center gap-3 mb-2">
                      <span className="text-3xl">{["🌱", "🌿", "🔨", "🤝", "⭐"][idx]}</span>
                      <div>
                        <h3 className="font-heading font-bold text-2xl text-ink">{level.name}</h3>
                        <p className="text-sm text-ink/60">{level.minPoints.toLocaleString()}–{level.maxPoints === 99999 ? "∞" : level.maxPoints.toLocaleString()} points</p>
                      </div>
                    </div>
                    {isActive && (
                      <div className="bg-copper text-white px-4 py-2 rounded-full font-bold text-sm">
                        You Are Here
                      </div>
                    )}
                  </div>

                  <div className="grid md:grid-cols-3 gap-6 mb-6">
                    <div>
                      <p className="text-sm text-ink/60 font-bold uppercase mb-2">Your Discount</p>
                      <div className="flex items-baseline gap-2">
                        <span className="text-3xl font-heading font-bold text-copper">
                          {(level.discount * 100).toFixed(0)}%
                        </span>
                        <span className="text-ink/60">off courses</span>
                      </div>
                    </div>
                    <div>
                      <p className="text-sm text-ink/60 font-bold uppercase mb-2">WAI Takes</p>
                      <div className="flex items-baseline gap-2">
                        <span className="text-3xl font-heading font-bold text-ink">{(level.waiMargin * 100).toFixed(0)}%</span>
                        <span className="text-ink/60">of course price</span>
                      </div>
                    </div>
                    <div>
                      <p className="text-sm text-ink/60 font-bold uppercase mb-2">$9.99 Course Costs</p>
                      <div className="text-3xl font-heading font-bold">
                        <span className={level.discount > 0 ? "text-green-600" : "text-ink"}>
                          ${(9.99 * (1 - level.discount)).toFixed(2)}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="p-4 bg-ink/5 rounded border border-ink/10">
                    <p className="text-sm text-ink/70">
                      <strong>What this means:</strong> At {level.name}, you pay{" "}
                      {level.discount > 0 ? `only ${((1 - level.discount) * 100).toFixed(0)}% of course price` : "full price"}.
                      Creators still get 70%+ of what you pay. WAI takes the smallest share—{(level.waiMargin * 100).toFixed(0)}%.
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        <div className="mb-16 bg-white border border-ink/10 rounded-lg p-8">
          <h2 className="font-heading text-2xl font-bold mb-6 text-ink">How Much You'll Save</h2>
          <div className="grid md:grid-cols-2 gap-8">
            <div>
              <h3 className="font-bold text-lg mb-4 text-ink">One Year of Courses</h3>
              <p className="text-ink/60 mb-6">If you enroll in 12 courses at average $9.99 each:</p>
              <div className="space-y-4">
                {[
                  { label: "Seed Level (0% discount)", total: 119.88, save: 0, bg: "bg-ink/5", border: "border-ink/10", text: "text-ink", label_c: "text-ink/60" },
                  { label: "Rooted Level (5% discount)", total: 113.88, save: 6, bg: "bg-yellow-50", border: "border-yellow-200", text: "text-yellow-600", label_c: "text-yellow-700" },
                  { label: "Builder Level (10% discount)", total: 107.88, save: 12, bg: "bg-green-50", border: "border-green-200", text: "text-green-600", label_c: "text-green-700" },
                  { label: "Steward/Elder Level (15% discount)", total: 101.88, save: 18, bg: "bg-green-50", border: "border-green-300", text: "text-green-700", label_c: "text-green-700" },
                ].map((row, i) => (
                  <div key={i} className={`p-4 ${row.bg} rounded border ${row.border}`}>
                    <p className={`text-sm ${row.label_c} mb-1`}>{row.label}</p>
                    <p className={`text-2xl font-bold ${row.text}`}>${row.total.toFixed(2)}</p>
                    {row.save > 0 && <p className={`text-xs ${row.text} font-bold`}>Save ${row.save.toFixed(2)}</p>}
                    {row.save === 0 && <p className={`text-xs ${row.label_c}`}>Total paid</p>}
                  </div>
                ))}
              </div>
            </div>
            <div>
              <h3 className="font-bold text-lg mb-4 text-ink">Five Years of Courses</h3>
              <p className="text-ink/60 mb-6">Cumulative savings (60 courses at average $9.99):</p>
              <div className="space-y-4">
                {[
                  { label: "Seed Level (0% discount)", total: 599.40, save: 0, bg: "bg-ink/5", border: "border-ink/10", text: "text-ink", label_c: "text-ink/60" },
                  { label: "Rooted Level (5% discount)", total: 569.43, save: 30, bg: "bg-yellow-50", border: "border-yellow-200", text: "text-yellow-600", label_c: "text-yellow-700" },
                  { label: "Builder Level (10% discount)", total: 539.46, save: 60, bg: "bg-green-50", border: "border-green-200", text: "text-green-600", label_c: "text-green-700" },
                  { label: "Steward/Elder Level (15% discount)", total: 509.49, save: 90, bg: "bg-green-50", border: "border-green-300", text: "text-green-700", label_c: "text-green-700" },
                ].map((row, i) => (
                  <div key={i} className={`p-4 ${row.bg} rounded border ${row.border}`}>
                    <p className={`text-sm ${row.label_c} mb-1`}>{row.label}</p>
                    <p className={`text-2xl font-bold ${row.text}`}>${row.total.toFixed(2)}</p>
                    {row.save > 0 && <p className={`text-xs ${row.text} font-bold`}>Save ${row.save}</p>}
                    {row.save === 0 && <p className={`text-xs ${row.label_c}`}>Total paid</p>}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        <div className="bg-gradient-to-r from-copper/10 to-copper/5 border-2 border-copper rounded-lg p-8">
          <h2 className="font-heading text-2xl font-bold mb-6 text-ink">Why We Do This</h2>
          <div className="grid md:grid-cols-3 gap-8">
            <div>
              <h3 className="font-bold text-lg mb-3 flex items-center gap-2">
                <Gift className="w-5 h-5 text-copper" />
                Rewards Loyalty
              </h3>
              <p className="text-ink/70">The longer you stay and the more you contribute, the better economics work for you. Real, material benefit.</p>
            </div>
            <div>
              <h3 className="font-bold text-lg mb-3 flex items-center gap-2">
                <DollarSign className="w-5 h-5 text-copper" />
                Shares The Win
              </h3>
              <p className="text-ink/70">As you invest in us, we invest back in you. Smaller margins for WAI = bigger savings for partners.</p>
            </div>
            <div>
              <h3 className="font-bold text-lg mb-3 flex items-center gap-2">
                <TrendingDown className="w-5 h-5 text-copper" />
                Proves Partnership
              </h3>
              <p className="text-ink/70">Not a marketing gimmick. Real discounts backed by transparent math. You can verify every number.</p>
            </div>
          </div>
        </div>

        <div className="mt-16 text-center">
          <h2 className="font-heading text-2xl font-bold mb-4 text-ink">Ready to Build Your Partnership?</h2>
          <p className="text-lg text-ink/60 mb-8">
            Every course you take, every post you write, every mentor you help—it deepens your partnership and unlocks better discounts.
          </p>
          <a href="/modules" className="btn-primary inline-flex items-center gap-2">
            Browse Courses and Start Saving
          </a>
        </div>
      </div>
    </div>
  );
}
