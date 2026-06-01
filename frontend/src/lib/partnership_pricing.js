/**
 * Partnership Pricing System
 * Users earn discounts as they deepen their partnership
 * The more you build with us, the better our economics work FOR you
 */

export const PARTNERSHIP_LEVELS = [
  {
    name: "Seed",
    minPoints: 0,
    maxPoints: 100,
    discount: 0,
    waiMargin: 0.30,
    description: "Getting started",
    firstMilestone: 50,
    firstMilestoneUnlock: "Early Adopter (5% discount preview)"
  },
  {
    name: "Rooted",
    minPoints: 100,
    maxPoints: 300,
    discount: 0.05,
    waiMargin: 0.25,
    description: "Growing your impact",
    firstMilestone: 120,
    firstMilestoneUnlock: "Voice Badge (comment on discussions)"
  },
  {
    name: "Builder",
    minPoints: 300,
    maxPoints: 800,
    discount: 0.10,
    waiMargin: 0.20,
    description: "Shaping the foundation",
    firstMilestone: 325,
    firstMilestoneUnlock: "Teacher Badge (featured in top teachers)"
  },
  {
    name: "Steward",
    minPoints: 800,
    maxPoints: 2000,
    discount: 0.15,
    waiMargin: 0.15,
    description: "Holding space for others",
    firstMilestone: 850,
    firstMilestoneUnlock: "Decision Maker (vote on fund allocation)"
  },
  {
    name: "Elder",
    minPoints: 2000,
    maxPoints: 99999,
    discount: 0.15,
    waiMargin: 0.15,
    description: "Shaping the future",
    firstMilestone: 2100,
    firstMilestoneUnlock: "Board Advisory"
  },
];

/**
 * Get partnership level from points
 */
export function getPartnershipLevel(points) {
  return PARTNERSHIP_LEVELS.find(
    (level) => points >= level.minPoints && points < level.maxPoints
  ) || PARTNERSHIP_LEVELS[PARTNERSHIP_LEVELS.length - 1];
}

/**
 * Calculate discounted price based on partnership level
 * @param basePrice - Original course price
 * @param partnershipPoints - User's partnership points
 * @returns {Object} pricing breakdown
 */
export function calculatePartnershipPrice(basePrice, partnershipPoints) {
  const level = getPartnershipLevel(partnershipPoints);
  const discountAmount = basePrice * level.discount;
  const discountedPrice = basePrice - discountAmount;
  const waiEarnings = discountedPrice * level.waiMargin;
  const creatorEarnings = discountedPrice - waiEarnings;

  return {
    originalPrice: basePrice,
    discount: level.discount,
    discountAmount,
    finalPrice: discountedPrice,
    level: level.name,
    partnershipPoints,
    breakdown: {
      creatorEarnings: creatorEarnings,
      creatorPercent: ((creatorEarnings / discountedPrice) * 100).toFixed(1),
      waiEarnings: waiEarnings,
      waiPercent: (level.waiMargin * 100).toFixed(0),
    },
    savings: {
      amount: discountAmount,
      percent: (level.discount * 100).toFixed(0),
      message:
        level.discount === 0
          ? "Build your partnership to unlock discounts"
          : `You're saving ${(level.discount * 100).toFixed(0)}% as a ${level.name}`,
    },
  };
}

/**
 * Show what discount user will unlock at next level
 */
export function getNextLevelDiscount(currentPoints) {
  const currentLevel = getPartnershipLevel(currentPoints);
  const currentIndex = PARTNERSHIP_LEVELS.findIndex((l) => l.name === currentLevel.name);

  if (currentIndex >= PARTNERSHIP_LEVELS.length - 1) {
    return null; // Already at max
  }

  const nextLevel = PARTNERSHIP_LEVELS[currentIndex + 1];
  const pointsToNext = nextLevel.minPoints - currentPoints;
  const discountIncrease = (nextLevel.discount - currentLevel.discount) * 100;

  return {
    level: nextLevel.name,
    pointsNeeded: pointsToNext,
    newDiscount: (nextLevel.discount * 100).toFixed(0),
    discountIncrease,
    message:
      discountIncrease > 0
        ? `Reach ${nextLevel.name} for ${(nextLevel.discount * 100).toFixed(0)}% discount`
        : `Reach ${nextLevel.name} for additional benefits`,
  };
}

/**
 * Calculate lifetime savings from partnership discounts
 * Useful for showing the value of being a long-term partner
 */
export function calculatePartnershipSavings(
  totalSpent,
  currentPoints,
  courseCount = 1
) {
  const level = getPartnershipLevel(currentPoints);
  const averageCoursePrice = totalSpent / courseCount;

  // Calculate what they would have paid at each level
  const totalSavings = totalSpent * level.discount;
  const projectedSavingsNextYear = (totalSpent * 1.5) * level.discount; // Assuming 50% growth

  return {
    currentSavings: totalSavings,
    currentDiscountPercent: (level.discount * 100).toFixed(0),
    projectedNextYearSavings: projectedSavingsNextYear,
    averageCoursePrice,
    message: `You've saved $${totalSavings.toFixed(2)} as a ${level.name}. Keep building! 🚀`,
  };
}

/**
 * Create pricing card for display
 * Shows original price, discount, and final price
 */
export function createPricingCard(basePrice, partnershipPoints) {
  const pricing = calculatePartnershipPrice(basePrice, partnershipPoints);
  const nextLevel = getNextLevelDiscount(partnershipPoints);

  return {
    ...pricing,
    nextLevelInfo: nextLevel,
    displayText: {
      main: `$${pricing.finalPrice.toFixed(2)}`,
      original: pricing.discount > 0 ? `Was $${basePrice.toFixed(2)}` : null,
      savings: pricing.discount > 0 ? `Save $${pricing.discountAmount.toFixed(2)} (${(pricing.discount * 100).toFixed(0)}%)` : null,
      level: `${pricing.level} Partner Pricing`,
    },
  };
}
