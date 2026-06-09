import { lazy } from "react";

export const ARCADE_GAMES = [
  {
    slug: "black-wall-street",
    title: "Black Wall Street",
    category: "Culture",
    description: "Build the Greenwood District business community before 1921. Every decision shapes your legacy.",
    tagline: "Turn-based business sim",
    xpReward: 150,
    featured: true,
    emoji: "🏛️",
  },
  {
    slug: "dont-get-played",
    title: "Don't Get Played",
    category: "Finance",
    description: "Spot predatory loans, rent-to-own traps, and high-APR schemes before they drain your wallet.",
    tagline: "Financial literacy scenarios",
    xpReward: 100,
    featured: false,
    emoji: "💰",
  },
  {
    slug: "drum-builder",
    title: "Drum Builder",
    category: "Music",
    description: "Compose a West African rhythm on an 8-step sequencer. Djembe, shekere, bell, and bass.",
    tagline: "8-step rhythm sequencer",
    xpReward: 50,
    featured: false,
    emoji: "🥁",
  },
  {
    slug: "scripture-scramble",
    title: "Scripture Scramble",
    category: "Faith",
    description: "Reassemble shuffled Bible verses against the clock. How well do you know the Word?",
    tagline: "Timed verse reorder",
    xpReward: 75,
    featured: false,
    emoji: "📖",
  },
];

export const CATEGORY_COLORS = {
  Culture: "badge-signal",
  Finance: "badge-copper",
  Music: "badge-ink",
  Faith: "badge-outline",
  Trades: "badge-copper",
};

export const GAME_COMPONENT_MAP = {
  "black-wall-street": lazy(() => import("../components/arcade/BlackWallStreet")),
  "dont-get-played": lazy(() => import("../components/arcade/DontGetPlayed")),
  "drum-builder": lazy(() => import("../components/arcade/DrumBuilder")),
  "scripture-scramble": lazy(() => import("../components/arcade/ScriptureScramble")),
};
