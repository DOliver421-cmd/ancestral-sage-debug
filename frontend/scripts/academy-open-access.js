#!/usr/bin/env node
/**
 * academy-open-access.js — guard rail for "the Homeschool Academy has no paywall".
 *
 * The Academy is free for every registered member. That promise can be broken
 * three ways, and this script checks all three:
 *
 *   1. A page inside the Academy links to a tier-gated route (TierGate in
 *      App.js), so a free member clicks through the curriculum and lands on an
 *      upgrade card.
 *   2. An Academy route in App.js is wrapped in a TierGate/role requirement
 *      that a plain registered member cannot satisfy.
 *   3. An Academy API route is mapped to a paid feature tier in the backend
 *      access contract (security/feature_control.py FEATURE_API_PATHS).
 *
 * Uses the real route table and the real access contract, so a paywall cannot
 * reappear without failing here.
 *
 * Usage:  node scripts/academy-open-access.js   (or: npm run test:academy-access)
 * Exit code 1 when a check fails.
 */

const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..");
const SRC = path.join(ROOT, "src");
const BACKEND = path.resolve(ROOT, "..", "backend");

let failures = 0;
const ok = (label) => console.log(`  ✓ ${label}`);
const fail = (label, detail) => {
  failures += 1;
  console.error(`  ✗ ${label}${detail ? ` — ${detail}` : ""}`);
};
const section = (t) => console.log(`\n${t}`);

const read = (p) => fs.readFileSync(p, "utf8");

// ── 1. Tier-gated destinations, taken from the real App.js route table ──────
section("Route inventory");
const appSrc = read(path.join(SRC, "App.js"));

// Parse whole <Route …/> tags. Splitting on the tag opener is robust to the
// multi-line wrapping and nested braces in App.js, which a single-line regex
// silently mishandles (it would miss every route whose element is a chain).
const routeTags = appSrc.split("<Route ").slice(1).map((t) => t.slice(0, t.indexOf("/>") + 2));
const pathOf = (tag) => (tag.match(/^path="([^"]+)"/) || [])[1];

const tierGatedRoutes = routeTags.filter((t) => /TierGate/.test(t)).map(pathOf);
ok(`found ${tierGatedRoutes.length} tier-gated routes in App.js: ${tierGatedRoutes.join(", ")}`);
if (tierGatedRoutes.length === 0) fail("no TierGate routes found — the route parser may have drifted");
if (!tierGatedRoutes.includes("/ai")) fail("/ai is not detected as tier-gated — route parser is stale");

// Academy routes that MUST stay open to any registered member.
const academyRoutes = routeTags.filter((t) => /^\/academy/.test(pathOf(t))).map((t) => [pathOf(t), t]);
if (academyRoutes.length < 8) fail("academy route inventory looks incomplete", `found ${academyRoutes.length}`);
else ok(`${academyRoutes.length} Academy routes found`);

const ACADEMY_STAFF_ROUTES = ["/academy/build"]; // staff build tracker is legitimate
for (const [routePath, tag] of academyRoutes) {
  if (ACADEMY_STAFF_ROUTES.includes(routePath)) continue;
  if (/TierGate/.test(tag)) {
    fail(`Academy route is tier-gated`, routePath);
  } else if (/roles=\{/.test(tag)) {
    fail(`Academy route is role-restricted`, routePath);
  }
}
ok("no Academy route (other than the staff build tracker) is tier-gated or role-restricted");

for (const staffRoute of ACADEMY_STAFF_ROUTES) {
  const found = academyRoutes.find(([p]) => p === staffRoute);
  if (found && !/roles=/.test(found[1])) {
    fail(`${staffRoute} lost its staff role requirement`);
  }
}
ok("staff-only Academy routes still carry an explicit role requirement");

// ── 2. No Academy surface links into a gated route ─────────────────────────
section("Academy outbound links");
const academyDir = path.join(SRC, "pages", "academy");
const academyFiles = fs.readdirSync(academyDir).filter((f) => f.endsWith(".jsx"));
const GATED_HREFS = new Set(["/ai", "/adaptive", "/band", "/studio", "/social/publish"]);
const GATED_PREFIXES = ["/creator/courses", "/creator/earnings", "/creator/payouts", "/creator-lounge", "/my-projects", "/ghost-producer", "/studio/music"];
const inNav = read(path.join(SRC, "components", "AppShell.jsx"));
const navTargets = new Set([...inNav.matchAll(/to="([^"]+)"/g)].map((x) => x[1]));

let linkCount = 0;
for (const file of academyFiles) {
  const src = read(path.join(academyDir, file));
  const hrefs = [...src.matchAll(/to="([^"]+)"/g)].map((x) => x[1]);
  for (const href of hrefs) {
    linkCount += 1;
    const gated = GATED_HREFS.has(href) || GATED_PREFIXES.some((p) => href.startsWith(p));
    if (gated) fail(`${file} links to a tier-gated route`, href);
  }
}
ok(`${linkCount} Academy links checked — none lead to a paywalled route`);

// ── 3. Backend: Academy API must not map to a paid feature tier ─────────────
section("Backend access contract");
const fcSrc = read(path.join(BACKEND, "security", "feature_control.py"));
const featurePathsBlock = fcSrc.split("FEATURE_API_PATHS: dict = {")[1]?.split("\n}")[0] || "";
const mapped = [...featurePathsBlock.matchAll(/"([^"]+)":\s*\[([^\]]+)\]/g)].map(([, k, v]) => ({
  feature: k,
  prefixes: v.replace(/"/g, "").split(",").map((s) => s.trim()).filter(Boolean),
}));
const minTierBlock = fcSrc.split("FEATURE_MIN_TIER: dict = {")[1]?.split("\n}")[0] || "";
if (!mapped.length) fail("could not parse FEATURE_API_PATHS — check feature_control.py");
else ok(`parsed ${mapped.length} mapped backend features`);

for (const { feature, prefixes } of mapped) {
  for (const prefix of prefixes) {
    if (prefix.startsWith("/api/academy")) {
      fail(`Academy API path is gated by feature '${feature}'`, prefix);
    }
  }
}
ok("no /api/academy/* path is mapped to a tier-gated feature");

// The Academy must not inherit a paid tier by being covered by a broader prefix.
const ACADEMY_API_PATHS = [
  "/api/academy/courses",
  "/api/academy/students",
  "/api/academy/compliance/generate",
  "/api/academy/curriculum-audit",
];
function coveredBy(path) {
  for (const { feature, prefixes } of mapped) {
    if (prefixes.some((p) => path.startsWith(p) && path !== p + "/")) return feature;
  }
  return null;
}
for (const p of ACADEMY_API_PATHS) {
  const owner = coveredBy(p);
  if (owner) {
    const required = (minTierBlock.match(new RegExp(`"${owner}":\\s*"([^"]+)"`)) || [])[1];
    if (required && required !== "free") {
      fail(`${p} falls under paid feature '${owner}' (min tier ${required})`);
    }
  }
}

// ── 4. Academy content is reachable without an entitlement ─────────────────
section("Course content gates");
const academySrc = read(path.join(BACKEND, "routers", "academy.py"));
if (!/content_visible/.test(academySrc)) fail("course detail lost its content_visible gate");
if (/current_user\(\).*subscription|require_subscription\(/.test(academySrc)) {
  fail("academy router requires a subscription");
}
ok("academy router has no subscription requirement");

console.log(`\n${failures === 0 ? "PASS" : `FAIL (${failures})`} — Academy open-access guard rail\n`);
process.exit(failures ? 1 : 0);
