/**
 * ContentLibrary — displays the free starter library books.
 *
 * These are static Markdown files in content/starter-library/ that were not
 * previously displayed anywhere in the UI. This registry provides metadata
 * for displaying them via the /api/media/content/ endpoint (public access).
 *
 * NOTE: This is NOT a second catalog system. It's a frontend registry for
 * static public content that exists as Markdown files. The authoritative
 * content is in the .md files themselves. This registry only provides
 * display metadata (titles, descriptions, tags) for the UI.
 */

export const STARTER_LIBRARY = [
  {
    slug: "the-black-ownership-playbook",
    title: "The Black Ownership Playbook",
    subtitle: "From Survival to Sovereignty in the Everyday Economy",
    description: "A practical guide for Black workers, creators, families, organizers, and small-business owners who want practical control over more of the value they create. It offers a sequence of decisions, not a shortcut.",
    price: 0,
    priceLabel: "Free",
    tags: ["ownership", "economics", "business"],
    readTime: "25 min read",
  },
  {
    slug: "ai-without-the-intimidation",
    title: "AI Without the Intimidation",
    subtitle: "A Plain-Spoken Guide to Tools That Actually Help",
    description: "An accessible introduction to AI tools for people who are tired of the hype. Focuses on practical uses that respect your time, your work, and your autonomy.",
    price: 0,
    priceLabel: "Free",
    tags: ["AI", "technology", "productivity"],
    readTime: "18 min read",
  },
  {
    slug: "from-creator-to-product",
    title: "From Creator to Product",
    subtitle: "Turning What You Know Into Something That Travels",
    description: "A guide for creators who want to turn their knowledge, voice, and practice into products that can reach people beyond a single room, platform, or moment.",
    price: 0,
    priceLabel: "Free",
    tags: ["creators", "products", "monetization"],
    readTime: "20 min read",
  },
  {
    slug: "the-automation-trap",
    title: "The Automation Trap",
    subtitle: "What Gets Lost When Convenience Wins",
    description: "An examination of the hidden costs of automation when it is adopted without intention. A reminder that efficiency without sovereignty is just a different form of dependency.",
    price: 0,
    priceLabel: "Free",
    tags: ["technology", "sovereignty", "critical-thinking"],
    readTime: "15 min read",
  },
  {
    slug: "the-community-funding-starter",
    title: "The Community Funding Starter",
    subtitle: "A Practical Beginning for Mutual Support",
    description: "A starter guide for communities that want to build their own funding practices — small, real, and accountable — instead of waiting for outside salvation.",
    price: 0,
    priceLabel: "Free",
    tags: ["community", "funding", "mutual-aid"],
    readTime: "12 min read",
  },
  {
    slug: "the-human-made-difference",
    title: "The Human-Made Difference",
    subtitle: "Why People Still Matter in an Automated World",
    description: "A reflection on the kinds of value that only people can make, and why those values should stay centered even as tools change around us.",
    price: 0,
    priceLabel: "Free",
    tags: ["humanity", "creativity", "technology"],
    readTime: "10 min read",
  },
  {
    slug: "the-small-start",
    title: "The Small Start",
    subtitle: "How Little Begins Become Real Things",
    description: "A guide for anyone who feels behind and is trying to begin anyway. Focuses on small, durable steps instead of dramatic launches that disappear by Friday.",
    price: 0,
    priceLabel: "Free",
    tags: ["starting-out", "growth", "mindset"],
    readTime: "8 min read",
  },
  {
    slug: "when-ai-is-wrong",
    title: "When AI Is Wrong",
    subtitle: "A Practical Guide to Spotting Mistakes Before They Become Your Mistakes",
    description: "A field guide for working with AI output without outsourcing your judgment. Includes common failure patterns and practical habits for catching them early.",
    price: 0,
    priceLabel: "Free",
    tags: ["AI", "critical-thinking", "judgment"],
    readTime: "14 min read",
  },
  {
    slug: "conspiracy-brother-the-receipts-are-on-the-table",
    title: "Conspiracy Brother: The Receipts Are on the Table",
    subtitle: "A Satirical Investigation",
    description: "A satirical investigation that uses humor to expose how conspiracy thinking works, why it spreads, and what it costs the communities it claims to protect.",
    price: 0,
    priceLabel: "Free",
    tags: ["satire", "media-literacy", "critical-thinking"],
    readTime: "16 min read",
  },
];

/**
 * Normalize a starter-library slug into a readable title for the content file.
 */
export function libraryContentPath(slug) {
  return `/api/media/content/starter-library/${slug}.md`;
}
