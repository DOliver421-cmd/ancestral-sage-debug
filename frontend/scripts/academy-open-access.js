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
let academyLike = [];
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

// ── 2. No Academy surface links into a paywalled route ─────────────────────
// A route is paywalled when its TierGate's feature has a minimum tier above
// "free" in the real frontend tier map (src/lib/tiers.js). Derived, not
// hardcoded: when the tier table changes, this guard changes with it.
section("Academy outbound links");
const academyDir = path.join(SRC, "pages", "academy");
const academyFiles = fs.readdirSync(academyDir).filter((f) => f.endsWith(".jsx"));

const tiersSrc = read(path.join(SRC, "lib", "tiers.js"));
const tierBlock = (tiersSrc.split("export const TIER_FOR_FEATURE = {")[1] || "").split("\n};")[0];
const featureMinTier = {};
for (const m of tierBlock.matchAll(/([a-z_]+):\s*"([a-z]+)"/g)) featureMinTier[m[1]] = m[2];

const paywalledRoutes = [];
for (const tag of routeTags) {
  const feature = (tag.match(/TierGate feature="([^"]+)"/) || [])[1];
  if (!feature) continue;
  const minTier = featureMinTier[feature];
  if (minTier && minTier !== "free") paywalledRoutes.push({ route: pathOf(tag), feature, minTier });
}
ok(`paywalled routes (min tier above free): ${paywalledRoutes.map((p) => `${p.route} [${p.feature}=${p.minTier}]`).join(", ")}`);
if (paywalledRoutes.length === 0) fail("no paywalled routes derived — tier parser may be stale");

let linkCount = 0;
for (const file of academyFiles) {
  const src = read(path.join(academyDir, file));
  for (const m of src.matchAll(/to="([^"]+)"/g)) {
    const href = m[1];
    linkCount += 1;
    if (paywalledRoutes.some((p) => p.route === href)) {
      fail(`${file} links to a paywalled route`, `${href} [${(paywalledRoutes.find((p) => p.route === href) || {}).feature}]`);
    }
  }
}
ok(`${linkCount} Academy links checked across ${academyFiles.length} pages — none lead to a paywalled route`);

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

// ── 5. The rest of the site KEEPS its paywalls ────────────────────────────
// The owner's standing rule: the Homeschool Academy is free to every
// registered member, but the platform's paid surfaces stay paid. "Make the
// Academy free" must never be read as "free the site", so assert the paid
// tiers are still recorded and still enforced on their routes.
section("Platform paywalls stay in place");
const paidFeatures = Object.entries(featureMinTier).filter(([, t]) => t !== "free");
ok(`${paidFeatures.length} paid features still carry a tier: ${paidFeatures.map(([f, t]) => `${f}=${t}`).join(", ")}`);
// The Academy must not appear in the paid map under any name.
academyLike = Object.keys(featureMinTier).filter((f) => /academ|homeschool|curriculum-.*(course|lesson)/.test(f));
if (academyLike.length) fail("Academy-shaped keys appear in the tier map", academyLike.join(", "));
else ok("no Academy-shaped key carries a platform tier");
for (const { route, feature, minTier } of paywalledRoutes) {
  const tag = routeTags.find((t) => pathOf(t) === route);
  if (!tag || !/TierGate/.test(tag)) fail(`${route} lost its TierGate`, `${feature} (${minTier})`);
}
ok(`${paywalledRoutes.length} paid routes still carry their TierGate`);
// Every destination the Academy links to must be a free route. The feature
// keys are not the same as routes (/courses is a free catalog page; selling
// creator courses at /creator/courses is the paid feature), so check the
// routes the Academy actually points at.
const academyDestinations = new Set();
for (const file of academyFiles) {
  for (const m of read(path.join(academyDir, file)).matchAll(/to="([^"]+)"/g)) {
    if (m[1].startsWith("/")) academyDestinations.add(m[1]);
  }
}
const paywalledDestinations = [...academyDestinations].filter((d) => paywalledRoutes.some((p) => p.route === d));
if (paywalledDestinations.length) fail("the Academy links to paid routes", paywalledDestinations.join(", "));
else ok(`${academyDestinations.size} Academy destinations, all free (${[...academyDestinations].sort().join(", ")})`);
// Sanity: the paid catalog of creator courses must still be paid — the Academy
// is free, the creator marketplace is not.
const creatorCourses = paywalledRoutes.find((p) => p.route === "/creator/courses");
if (creatorCourses) ok(`/creator/courses is still paid (${creatorCourses.feature}=${creatorCourses.minTier}) — the Academy is free, the marketplace is not`);
else fail("/creator/courses lost its TierGate — a platform paywall was removed");

console.log(`\n${failures === 0 ? "PASS" : `FAIL (${failures})`} — Academy open-access guard rail\n`);
process.exit(failures ? 1 : 0);
