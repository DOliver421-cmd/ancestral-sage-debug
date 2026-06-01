import { TrendingDown, Gift, Lock, DollarSign } from "lucide-react";
import PartnershipPricing from "../components/PartnershipPricing";
import { PARTNERSHIP_LEVELS } from "../lib/partnership_pricing";

/**
 * Partnership Discounts Page
 * Shows how pricing works and how to unlock better discounts
 */

export default function PartnershipDiscounts() {
  const demoPrice = 9.99;
  const userPoints = 650; // Mock user data

  return (
    <div className="min-h-screen bg-bone text-ink">
      {/* Header */}
      <div className="border-b border-ink/10 bg-white">
        <div className="max-w-7xl mx-auto px-6 py-12">
          <h1 className="font-heading text-4xl font-bold mb-4">Partnership Pricing</h1>
          <p className="text-xl text-ink/60">
            The deeper your partnership, the better our economics work for you.
          </p>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-6 py-12">
        {/* Core Concept */}
        <div className="mb-16">
          <div className="bg-gradient-to-r from-copper/10 to-copper/5 border-2 border-copper rounded-lg p-8">
            <h2 className="font-heading text-2xl font-bold mb-4 text-ink">How It Works</h2>
            <div className="grid md:grid-cols-3 gap-8">
              <div>
                <h3 className="font-bold text-lg mb-2">Seed Level (0-100 pts)</h3>
                <p className="text-ink/70 mb-4">You're just starting. Pay full price to support the platform.</p>
                <div className="bg-white/60 rounded p-3">
                  <p className="text-xs text-ink/60 mb-2">Example: $9.99 course</p>
                  <p className="font-bold text-lg text-ink">$9.99</p>
                  <p className="text-xs text-ink/60">0% discount</p>
                </div>
              </div>

              <div>
                <h3 className="font-bold text-lg mb-2">Rooted → Builder (100-800 pts)</h3>
                <p className="text-ink/70 mb-4">Growing your impact. Start saving 5-10%.</p>
                <div className="bg-green-50 rounded p-3 border border-green-200">
                  <p className="text-xs text-green-700 mb-2">Example: $9.99 course</p>
                  <p className="font-bold text-lg text-green-600">$9.49</p>
                  <p className="text-xs text-green-700">5% discount</p>
                </div>
              </div>

              <div>
                <h3 className="font-bold text-lg mb-2">Steward → Elder (800+ pts)</h3>
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

        {/* Discount Tiers */}
        <div className="mb-16">
          <h2 className="font-heading text-2xl font-bold mb-8 text-ink">Your Discount Structure</h2>

          <div className="grid gap-6">
            {PARTNERSHIP_LEVELS.map((level, idx) => (
              <div
                key={idx}
                className={`rounded-lg border-2 p-8 transition-all ${
                  level.minPoints <= userPoints && userPoints < level.maxPoints
                    ? "border-copper bg-copper/5"
                    : "border-ink/10 bg-white"
                }`}
              >
                <div className="flex items-start justify-between mb-6">
                  <div>
                    <div className="flex items-center gap-3 mb-2">
                      <span className="text-3xl">{["🌱", "🌿", "🔨", "🤝", "⭐"][idx]}</span>
                      <div>
                        <h3 className="font-heading font-bold text-2xl text-ink">{level.name}</h3>
                        <p className="text-sm text-ink/60">{level.minPoints.toLocaleString()}-{level.maxPoints === 99999 ? "∞" : level.maxPoints.toLocaleString()} points</p>
                      </div>
                    </div>
                  </div>

                  {level.minPoints <= userPoints && userPoints < level.maxPoints && (
                    <div className="bg-copper text-white px-4 py-2 rounded-full font-bold text-sm">
                      You Are Here
                    </div>
                  )}
                </div>

                <div className="grid md:grid-cols-3 gap-6 mb-6">
                  {/* Discount */}
                  <div>
                    <p className="text-sm text-ink/60 font-bold uppercase mb-2">Your Discount</p>
                    <div className="flex items-baseline gap-2">
                      <span className="text-3xl font-heading font-bold text-copper">
                        {(level.discount * 100).toFixed(0)}%
                      </span>
                      <span className="text-ink/60">off courses</span>
                    </div>
                  </div>

                  {/* WAI Margin */}
                  <div>
                    <p className="text-sm text-ink/60 font-bold uppercase mb-2">WAI Takes</p>
                    <div className="flex items-baseline gap-2">
                      <span className="text-3xl font-heading font-bold text-ink">{(level.waiMargin * 100).toFixed(0)}%</span>
                      <span className="text-ink/60">of course price</span>
                    </div>
                  </div>

                  {/* Example Price */}
                  <div>
                    <p className="text-sm text-ink/60 font-bold uppercase mb-2">$9.99 Course Costs</p>
                    <div className="text-3xl font-heading font-bold">
                      <span className={level.discount > 0 ? "text-green-600" : "text-ink"}>
                        ${(9.99 * (1 - level.discount)).toFixed(2)}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Economics explanation */}
                <div className="p-4 bg-ink/5 rounded border border-ink/10">
                  <p className="text-sm text-ink/70">
                    <strong>What this means:</strong> At {level.name}, you pay{" "}
                    {level.discount > 0
                      ? `only ${((1 - level.discount) * 100).toFixed(0)}% of course price`
                      : "full price"}
                    . Creators still get 70%+ of what you pay. WAI takes the smallest share—{(level.waiMargin * 100).toFixed(0)}%.
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Savings Calculator */}
        <div className="mb-16 bg-white border border-ink/10 rounded-lg p-8">
          <h2 className="font-heading text-2xl font-bold mb-6 text-ink">How Much You'll Save</h2>

          <div className="grid md:grid-cols-2 gap-8">
            {/* Calculate for a year */}
            <div>
              <h3 className="font-bold text-lg mb-4 text-ink">One Year of Courses</h3>
              <p className="text-ink/60 mb-6">If you enroll in 12 courses at average $9.99 each:</p>

              <div className="space-y-4">
                <div className="p-4 bg-ink/5 rounded border border-ink/10">
                  <p className="text-sm text-ink/60 mb-1">Seed Level (0% discount)</p>
                  <p className="text-2xl font-bold text-ink">$119.88</p>
                  <p className="text-xs text-ink/60">Total paid</p>
                </div>

                <div className="p-4 bg-yellow-50 rounded border border-yellow-200">
                  <p className="text-sm text-yellow-700 mb-1">Rooted Level (5% discount)</p>
                  <p className="text-2xl font-bold text-yellow-600">$113.88</p>
                  <p className="text-xs text-yellow-600 font-bold">Save $6.00</p>
                </div>

                <div className="p-4 bg-green-50 rounded border border-green-200">
                  <p className="text-sm text-green-700 mb-1">Builder Level (10% discount)</p>
                  <p className="text-2xl font-bold text-green-600">$107.88</p>
                  <p className="text-xs text-green-600 font-bold">Save $12.00</p>
                </div>

                <div className="p-4 bg-green-50 rounded border border-green-300">
                  <p className="text-sm text-green-700 mb-1">Steward/Elder Level (15% discount)</p>
                  <p className="text-2xl font-bold text-green-700">$101.88</p>
                  <p className="text-xs text-green-700 font-bold">Save $18.00</p>
                </div>
              </div>
            </div>

            {/* Calculate for 5 years */}
            <div>
              <h3 className="font-bold text-lg mb-4 text-ink">Five Years of Courses</h3>
              <p className="text-ink/60 mb-6">Cumulative savings (60 courses at average $9.99):</p>

              <div className="space-y-4">
                <div className="p-4 bg-ink/5 rounded border border-ink/10">
                  <p className="text-sm text-ink/60 mb-1">Seed Level (0% discount)</p>
                  <p className="text-2xl font-bold text-ink">$599.40</p>
                  <p className="text-xs text-ink/60">Total paid</p>
                </div>

                <div className="p-4 bg-yellow-50 rounded border border-yellow-200">
                  <p className="text-sm text-yellow-700 mb-1">Rooted Level (5% discount)</p>
                  <p className="text-2xl font-bold text-yellow-600">$569.43</p>
                  <p className="text-xs text-yellow-600 font-bold">Save $30</p>
                </div>

                <div className="p-4 bg-green-50 rounded border border-green-200">
                  <p className="text-sm text-green-700 mb-1">Builder Level (10% discount)</p>
                  <p className="text-2xl font-bold text-green-600">$539.46</p>
                  <p className="text-xs text-green-600 font-bold">Save $60</p>
                </div>

                <div className="p-4 bg-green-50 rounded border border-green-300">
                  <p className="text-sm text-green-700 mb-1">Steward/Elder Level (15% discount)</p>
                  <p className="text-2xl font-bold text-green-700">$509.49</p>
                  <p className="text-xs text-green-700 font-bold">Save $90</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Why This Works */}
        <div className="bg-gradient-to-r from-copper/10 to-copper/5 border-2 border-copper rounded-lg p-8">
          <h2 className="font-heading text-2xl font-bold mb-6 text-ink">Why We Do This</h2>

          <div className="grid md:grid-cols-3 gap-8">
            <div>
              <h3 className="font-bold text-lg mb-3 flex items-center gap-2">
                <Gift className="w-5 h-5 text-copper" />
                Rewards Loyalty
              </h3>
              <p className="text-ink/70">
                The longer you stay and the more you contribute, the better economics work for you. Real, material benefit.
              </p>
            </div>

            <div>
              <h3 className="font-bold text-lg mb-3 flex items-center gap-2">
                <DollarSign className="w-5 h-5 text-copper" />
                Shares The Win
              </h3>
              <p className="text-ink/70">
                As you invest in us, we invest back in you. Smaller margins for WAI = bigger savings for partners.
              </p>
            </div>

            <div>
              <h3 className="font-bold text-lg mb-3 flex items-center gap-2">
                <TrendingDown className="w-5 h-5 text-copper" />
                Proves Partnership
              </h3>
              <p className="text-ink/70">
                Not a marketing gimmick. Real discounts backed by transparent math. You can verify every number.
              </p>
            </div>
          </div>
        </div>

        {/* CTA */}
        <div className="mt-16 text-center">
          <h2 className="font-heading text-2xl font-bold mb-4 text-ink">Ready to Build Your Partnership?</h2>
          <p className="text-lg text-ink/60 mb-8">
            Every course you take, every post you write, every mentor you help—it deepens your partnership and unlocks better discounts.
          </p>
          <a href="/marketplace" className="btn-primary inline-flex items-center gap-2">
            Browse Courses and Start Saving
          </a>
        </div>
      </div>
    </div>
  );
}
