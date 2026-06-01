import { TrendingDown, Gift, Lock } from "lucide-react";
import { calculatePartnershipPrice, getNextLevelDiscount } from "../lib/partnership_pricing";

/**
 * Partnership Pricing Display Component
 * Shows discounts earned through partnership level
 * Used on course cards, checkout, and price displays
 */

export default function PartnershipPricing({
  basePrice,
  partnershipPoints = 0,
  partnershipLevel = "Seed",
  showBreakdown = false,
  showNextLevel = true,
  size = "normal", // normal, compact, large
}) {
  const pricing = calculatePartnershipPrice(basePrice, partnershipPoints);
  const nextLevel = showNextLevel ? getNextLevelDiscount(partnershipPoints) : null;

  if (size === "compact") {
    return (
      <div>
        {pricing.discount > 0 ? (
          <div className="inline-flex items-center gap-2 bg-green-50 border border-green-200 rounded px-3 py-2">
            <TrendingDown className="w-4 h-4 text-green-600" />
            <span className="text-sm font-bold text-green-600">
              Save {(pricing.discount * 100).toFixed(0)}% - ${pricing.discountAmount.toFixed(2)}
            </span>
          </div>
        ) : (
          <div className="inline-flex items-center gap-2 bg-ink/5 border border-ink/20 rounded px-3 py-2">
            <Lock className="w-4 h-4 text-ink/40" />
            <span className="text-sm text-ink/60">No discount yet</span>
          </div>
        )}
      </div>
    );
  }

  if (size === "large") {
    return (
      <div className="bg-gradient-to-br from-copper/10 to-copper/5 border-2 border-copper rounded-lg p-8">
        {/* Headline */}
        <div className="text-center mb-8">
          <p className="text-sm font-bold text-copper uppercase mb-2">Partnership Pricing</p>
          <h3 className="font-heading text-4xl font-bold text-ink mb-2">${pricing.finalPrice.toFixed(2)}</h3>

          {pricing.discount > 0 ? (
            <div>
              <p className="text-lg text-ink/60 line-through">${basePrice.toFixed(2)}</p>
              <p className="text-lg text-green-600 font-bold mt-2">
                Save ${pricing.discountAmount.toFixed(2)} ({(pricing.discount * 100).toFixed(0)}%)
              </p>
            </div>
          ) : (
            <p className="text-lg text-ink/60">Standard pricing</p>
          )}
        </div>

        {/* Level Badge */}
        <div className="text-center mb-8">
          <span className="inline-block bg-copper/20 border border-copper px-4 py-2 rounded-full font-bold text-copper">
            {pricing.level} Partnership
          </span>
        </div>

        {/* Breakdown */}
        <div className="bg-white/60 rounded-lg p-6 mb-8">
          <h4 className="font-bold text-ink mb-4">Economics of This Purchase</h4>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-ink/70">You pay</span>
              <span className="font-bold text-lg text-ink">${pricing.finalPrice.toFixed(2)}</span>
            </div>
            <div className="border-t border-ink/10 pt-3">
              <div className="flex justify-between items-center mb-2">
                <span className="text-ink/70">Creator receives (70%)</span>
                <span className="font-bold text-green-600">${pricing.breakdown.creatorEarnings.toFixed(2)}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-ink/70">WAI receives ({pricing.breakdown.waiPercent}%)</span>
                <span className="font-bold text-ink">${pricing.breakdown.waiEarnings.toFixed(2)}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Message */}
        <div className="text-center">
          <p className="text-sm text-ink/70 mb-4">
            {pricing.discount > 0
              ? `As a ${pricing.level}, you're getting better economics. The creator still gets 70%+ of what you pay.`
              : `Deepen your partnership to unlock discounts. Build with us, save together.`}
          </p>

          {nextLevel && (
            <div className="p-4 bg-white/60 rounded-lg border border-copper/30">
              <p className="text-sm font-bold text-copper mb-1">🎯 Next Level</p>
              <p className="text-sm text-ink">
                {nextLevel.pointsNeeded} more points to {nextLevel.level}
              </p>
              <p className="text-xs text-ink/60 mt-2">
                Unlock {nextLevel.newDiscount}% discount
              </p>
            </div>
          )}
        </div>
      </div>
    );
  }

  // Normal size (default)
  return (
    <div className="rounded-lg border border-ink/10 bg-white p-4">
      {/* Price */}
      <div className="mb-4">
        <p className="text-sm text-ink/60 font-bold uppercase mb-1">Price</p>
        <div className="flex items-baseline gap-3">
          <span className="text-3xl font-heading font-bold text-ink">${pricing.finalPrice.toFixed(2)}</span>
          {pricing.discount > 0 && (
            <>
              <span className="text-lg text-ink/40 line-through">${basePrice.toFixed(2)}</span>
              <span className="inline-block bg-green-100 text-green-700 px-2 py-1 rounded text-sm font-bold">
                -${pricing.discountAmount.toFixed(2)}
              </span>
            </>
          )}
        </div>
      </div>

      {/* Partnership Level */}
      {pricing.discount > 0 ? (
        <div className="p-3 bg-green-50 border border-green-200 rounded mb-4">
          <p className="text-xs font-bold text-green-700 uppercase mb-1">✓ Partnership Discount</p>
          <p className="text-sm text-green-800 font-bold">{pricing.level} gets {(pricing.discount * 100).toFixed(0)}% off</p>
          <p className="text-xs text-green-700 mt-1">{pricing.savings.message}</p>
        </div>
      ) : (
        <div className="p-3 bg-ink/5 border border-ink/10 rounded mb-4">
          <p className="text-xs font-bold text-ink/60 uppercase mb-1">🔓 Unlock Discounts</p>
          <p className="text-sm text-ink/70">
            {nextLevel
              ? `${nextLevel.pointsNeeded} more points to ${nextLevel.level} discount`
              : "Keep building your partnership"}
          </p>
        </div>
      )}

      {/* Breakdown (if enabled) */}
      {showBreakdown && (
        <div className="text-xs space-y-2 border-t border-ink/10 pt-4">
          <div className="flex justify-between">
            <span className="text-ink/60">Creator earns (70%)</span>
            <span className="font-bold text-green-600">${pricing.breakdown.creatorEarnings.toFixed(2)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-ink/60">WAI earns ({pricing.breakdown.waiPercent}%)</span>
            <span className="font-bold text-ink">${pricing.breakdown.waiEarnings.toFixed(2)}</span>
          </div>
        </div>
      )}
    </div>
  );
}
