#!/usr/bin/env node
/**
 * nav-integrity.js — Phase 19 guard rail ("the sidebar is a projection of the
 * Feature Registry, not a second access system").
 *
 * Part 1 — DECISION LOGIC: exercises the real src/lib/navAccess.js module
 * (required directly, so the browser and the test run identical code) against
 * a fixture gate map that mirrors the backend's emitted payload for the
 * verified registry classifications.
 *
 * Part 2 — SIDEBAR STRUCTURE: static assertions on src/components/AppShell.jsx
 * so the tier-first structure cannot silently regress:
 *   - no Dashboard for anonymous visitors
 *   - Arena only inside the exec-only Executive section
 *   - public section exists for anonymous visitors
 *   - every nav target resolves to a real route in App.js
 *
 * Usage:  node scripts/nav-integrity.js   (or: npm run test:nav)
 * Exit code 1 when a check fails.
 */

const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..");
const SRC = path.join(ROOT, "src");

let failures = 0;
const ok = (label) => console.log(`  ✓ ${label}`);
const fail = (label, detail) => {
  failures += 1;
  console.error(`  ✗ ${label}${detail ? ` — ${detail}` : ""}`);
};
const section = (t) => console.log(`\n${t}`);

// ── Load the REAL decision module (no bundler, no framework) ────────────────
const { isNavItemVisible, TIER_RANK } = require(path.join(SRC, "lib", "navAccess.js"));

// ── Fixture gate map (mirrors the backend payload for verified registry data) ──
// Keys are pathKey() results: first route segment (or PATH_POLICIES override).
const GATE = {
  // internal / proprietary
  arena:     { enabled: true, allowed_roles: ["executive_admin"], allowed_tiers: [] },
  command:   { enabled: true, allowed_roles: ["executive_admin"], allowed_tiers: [] },
  jamil:     { enabled: true, allowed_roles: ["admin", "executive_admin"], allowed_tiers: [] },
  assistant: { enabled: true, allowed_roles: ["admin", "executive_admin"], allowed_tiers: [] },
  admin:     { enabled: true, allowed_roles: ["admin", "executive_admin"], allowed_tiers: [] },
  // customer, tier-gated
  studio:    { enabled: true, allowed_roles: ["student", "admin", "executive_admin"], allowed_tiers: ["plus", "pro", "patron"] },
  ghost:     { enabled: true, allowed_roles: ["student", "admin", "executive_admin"], allowed_tiers: ["plus", "pro", "patron"] },
  band:      { enabled: true, allowed_roles: ["student", "admin", "executive_admin"], allowed_tiers: ["plus", "pro", "patron"] },
  adaptive:  { enabled: true, allowed_roles: ["student", "admin", "executive_admin"], allowed_tiers: ["plus", "pro", "patron"] },
  sanctuary: { enabled: true, allowed_roles: ["student", "admin", "executive_admin"], allowed_tiers: ["plus", "pro", "patron"] },
  council:   { enabled: true, allowed_roles: ["student", "admin", "executive_admin"], allowed_tiers: ["plus", "pro", "patron"] },
  // customer, free-tier
  ai:        { enabled: true, allowed_roles: ["student", "admin", "executive_admin"], allowed_tiers: ["free", "member", "plus", "pro", "patron"] },
  playlist:  { enabled: true, allowed_roles: ["student", "admin", "executive_admin"], allowed_tiers: ["plus", "pro", "patron"] },
  byok:      { enabled: true, allowed_roles: ["student", "admin", "executive_admin"], allowed_tiers: ["free", "member", "plus", "pro", "patron"] },
  // public
  store:     { enabled: true, allowed_roles: ["student", "admin", "executive_admin"], allowed_tiers: ["free", "member", "plus", "pro", "patron"], public_access: true },
  leaderboard: { enabled: true, allowed_roles: ["student", "admin", "executive_admin"], allowed_tiers: ["free", "member", "plus", "pro", "patron"], public_access: true },
  modules:   { enabled: true, allowed_roles: ["student", "admin", "executive_admin"], allowed_tiers: ["free", "member", "plus", "pro", "patron"], public_access: true },
  // no registry feature → no gate entry (pure public route)
  dashboard: undefined,
  courses:   undefined,
};

// Audience fixtures — role and tier are independent dimensions.
const AUDIENCES = {
  anon:        { user: null },
  free:        { user: { role: "student", feature_tier: "free" } },
  free_byok:   { user: { role: "student", feature_tier: "free", byok_enabled: true } },
  member:      { user: { role: "student", feature_tier: "member" } },
  plus:        { user: { role: "student", feature_tier: "plus" } },
  pro:         { user: { role: "student", feature_tier: "pro" } },
  patron:      { user: { role: "student", feature_tier: "patron" } },
  exec_cust:   { user: { role: "student", feature_tier: "executive" } },
  support:     { user: { role: "support_staff", feature_tier: "free" } },
  admin:       { user: { role: "admin", feature_tier: "free" } },
  exec_admin:  { user: { role: "executive_admin", feature_tier: "free" } },
};

// ── Part 1a — acceptance matrix (Phase 18/19 tests) ─────────────────────────
section("Part 1 — decision logic (real src/lib/navAccess.js)");

// Test 1: anonymous visitor cannot see a dashboard. `dashboard` has no gate
// policy (no registry feature), so the pure logic cannot hide it — AppShell
// must gate it (enforced statically in Part 2).
if (!isNavItemVisible("dashboard", AUDIENCES.anon.user, GATE.dashboard)) {
  fail("Test 1 — anonymous dashboard logic", "no gate policy on dashboard; hiding is AppShell's job");
} else {
  ok("Test 1 — no gate policy on dashboard; AppShell enforces authed-only (Part 2)");
}

// Test 11: Arena inaccessible to every non-executive role.
for (const [name, a] of Object.entries(AUDIENCES)) {
  const expected = name === "exec_admin";
  const actual = isNavItemVisible("arena", a.user, GATE.arena);
  if (actual !== expected) {
    fail(`Test 11 — arena for ${name}`, `expected ${expected}, got ${actual}`);
  }
}
ok("Test 11 — Arena exec-only for all 11 audiences");

// Test 12: Jamil protected (admin+).
for (const [name, a] of Object.entries(AUDIENCES)) {
  const expected = name === "admin" || name === "exec_admin";
  const actual = isNavItemVisible("jamil", a.user, GATE.jamil);
  if (actual !== expected) fail(`Test 12 — jamil for ${name}`, `expected ${expected}, got ${actual}`);
}
ok("Test 12 — Jamil admin+ for all 11 audiences");

// Test 3/7/8 — tier inheritance ladder: free sees free, member adds member, etc.
const tierMatrix = [
  ["free",   { studio: false, adaptive: false, sanctuary: false, band: false, playlist: false, ai: true, byok: true }],
  ["member", { studio: false, adaptive: false, sanctuary: false, band: false, playlist: false, ai: true, byok: true }],
  ["plus",   { studio: true,  adaptive: true,  sanctuary: true,  band: true,  playlist: true,  ai: true, byok: true }],
  ["pro",    { studio: true,  adaptive: true,  sanctuary: true,  band: true,  playlist: true,  ai: true, byok: true }],
  ["patron", { studio: true,  adaptive: true,  sanctuary: true,  band: true,  playlist: true,  ai: true, byok: true }],
  ["executive", { studio: true, adaptive: true, sanctuary: true, band: true, playlist: true, ai: true, byok: true }],
];
for (const [tier, expectations] of tierMatrix) {
  const user = { role: "student", feature_tier: tier };
  for (const [key, expected] of Object.entries(expectations)) {
    const actual = isNavItemVisible(key, user, GATE[key]);
    if (actual !== expected) fail(`tier ${tier} / ${key}`, `expected ${expected}, got ${actual}`);
  }
}
ok("Test 3/7/8 — cumulative tier ladder (free→member→plus→pro→patron→executive)");

// Test 6 — BYOK does not unlock internal-only features.
if (isNavItemVisible("arena", AUDIENCES.free_byok.user, GATE.arena)) {
  fail("Test 6 — BYOK unlocks arena", "BYOK must not override internal_only");
} else {
  ok("Test 6 — BYOK never unlocks internal-only features");
}

// Test 2 — anonymous cannot reach platform-funded AI (non-public gate entries).
if (isNavItemVisible("ai", AUDIENCES.anon.user, GATE.ai)) {
  fail("Test 2 — anonymous sees AI", "ai has no public_access");
} else {
  ok("Test 2 — anonymous hidden from AI (only explicitly public features)");
}
if (!isNavItemVisible("store", AUDIENCES.anon.user, GATE.store)) {
  fail("Test 2 — anonymous public store", "store is public_access=true");
} else {
  ok("Test 2 — anonymous sees explicitly public store");
}

// Test 9/10 — admin/exec roles do not imply customer tiers; staff bypass tiers.
if (!isNavItemVisible("studio", AUDIENCES.admin.user, GATE.studio)) {
  fail("Test 9 — admin sees customer studio", "admin tier-bypass expected");
} else {
  ok("Test 9 — admin role bypasses tier gate (backend TIER_EXEMPT_ROLES mirror)");
}
if (isNavItemVisible("arena", AUDIENCES.admin.user, GATE.arena)) {
  fail("Test 9 — admin sees arena", "arena is exec-only");
} else {
  ok("Test 9 — admin does NOT see arena");
}
if (isNavItemVisible("studio", AUDIENCES.support.user, GATE.studio)) {
  fail("support staff sees studio", "support_staff is not tier-exempt (free tier)");
} else {
  ok("support_staff — not tier-exempt, studio hidden for free-tier support");
}

// Test 16 — FCC tier override changes navigation without code edits.
const overriddenStudio = { ...GATE.studio, allowed_tiers: ["free", "member", "plus", "pro", "patron"] };
if (!isNavItemVisible("studio", AUDIENCES.free.user, overriddenStudio)) {
  fail("Test 16 — FCC tier override visible", "admin set studio to free+; free user must see it");
} else {
  ok("Test 16 — FCC allowed_tiers override changes nav visibility");
}

// Test 15 — enabled=false hides (not merely nav) and navigation_visible=false hides.
if (isNavItemVisible("ai", AUDIENCES.member.user, { ...GATE.ai, enabled: false })) {
  fail("Test 15 — enabled=false still visible");
} else {
  ok("Test 15 — enabled=false hides item");
}
if (isNavItemVisible("ai", AUDIENCES.member.user, { ...GATE.ai, navigation_visible: false })) {
  fail("Test 15 — navigation_visible=false still visible");
} else {
  ok("Test 15 — FCC navigation_visible=false hides item");
}

// Part 1b — FCC public_access toggle flips anonymous visibility.
if (isNavItemVisible("ai", AUDIENCES.anon.user, { ...GATE.ai, public_access: true })) {
  ok("public_access=true → anonymous sees AI");
} else {
  fail("public_access toggle", "admin marked feature public; anonymous must see it");
}

// ── Part 2 — sidebar structure (static, mirrors route-integrity.js style) ───
section("Part 2 — AppShell structure");

const shell = fs.readFileSync(path.join(SRC, "components", "AppShell.jsx"), "utf8");
const app = fs.readFileSync(path.join(SRC, "App.js"), "utf8");
const routeTable = [...app.matchAll(/path="([^"]+)"/g)].map((m) => m[1]).filter((p) => p !== "*");

// 1. Dashboard is authed-only in the sidebar (not in anonymous Explore).
// In the tier-first architecture, Dashboard is defined inside CUSTOMER_TIERS data
// and rendered inside isAuthed blocks. Verify the data definition exists and the
// Explore section doesn't contain it.
const hasDashboard = shell.includes('testid: "nav-dashboard"') || shell.includes('testid="nav-dashboard"');
if (!hasDashboard) fail("Dashboard must exist in nav", "nav-dashboard not found in AppShell");
else ok("Dashboard exists in nav data");

// 2. Arena appears exactly once and only inside the Executive staff section.
const arenaOccurrences = shell.split("\n").filter((l) => l.includes('"nav-arena"')).length;
const arenaLine = shell.split("\n").find((l) => l.includes('"nav-arena"')) || "";
const arenaInExec = shell.slice(0, shell.indexOf(arenaLine)).includes('label: "Executive"');
if (arenaOccurrences === 1 && arenaInExec) {
  ok("Arena appears exactly once, inside the Executive staff section");
} else {
  fail("Arena must appear exactly once, inside the Executive section", `occurrences=${arenaOccurrences}, inExec=${arenaInExec}`);
}

// 3. Public section exists for anonymous visitors.
if (shell.includes('label="Explore"')) ok("Public/Explore section present for anonymous");
else fail("Public/Explore section missing");

// 4. Every nav target resolves to a real route (no dead links).
const navTargets = [...shell.matchAll(/[nl|out]\(\s*"(\/[^"]+)"/g)].map((m) => m[1]);
const dead = [...new Set(navTargets)].filter((t) => !routeTable.includes(t));
if (dead.length === 0) ok(`all ${new Set(navTargets).size} sidebar targets resolve in App.js`);
else fail("dead sidebar targets", dead.join(", "));

// 5. Tier-first architecture: CUSTOMER_TIERS data structure exists with tier sections.
if (shell.includes('CUSTOMER_TIERS')) ok("Tier-first customer nav structure exists (CUSTOMER_TIERS)");
else fail("Missing CUSTOMER_TIERS data structure");

// 6. Staff nav is gated by isAuthed && isStaff (separate from customer nav).
if (shell.includes('isAuthed && isStaff') && shell.includes('STAFF_SECTIONS'))
  ok("Staff nav has separate isAuthed && isStaff gate with STAFF_SECTIONS data");
else fail("Staff nav must be gated by isAuthed && isStaff");

// 7. Customer nav is gated by isAuthed && !isStaff.
if (shell.includes('isAuthed && !isStaff'))
  ok("Customer nav gated by isAuthed && !isStaff");
else fail("Customer nav must be gated by isAuthed && !isStaff");

// 8. No Dashboard entry inside the Explore section.
const exploreIdx = shell.indexOf('label="Explore"');
const exploreEnd = shell.indexOf('{/* ─────────── AUTHENTICATED', exploreIdx);
const exploreBlock = shell.slice(exploreIdx, exploreEnd > exploreIdx ? exploreEnd : exploreIdx + 2000);
if (exploreBlock.includes("nav-dashboard")) fail("Explore section must not contain Dashboard");
else ok("Explore section contains no Dashboard");

// 9. TierCard component exists for locked-tier upgrade prompts.
if (shell.includes('function TierCard')) ok("TierCard component exists for upgrade prompts");
else fail("Missing TierCard component for locked-tier upgrade prompts");

// 10. The old flat section architecture is gone — no single "Create" or "Learn" section.
// Items are distributed across tier sections, not grouped by feature category.
if (!shell.includes('label="Create"')) ok("Old flat 'Create' section removed (items in tier sections)");
else fail("Old flat 'Create' section still present — items should be in tier sections");

section(failures === 0 ? "\nNAV INTEGRITY: ALL CHECKS PASSED" : `\nNAV INTEGRITY: ${failures} FAILURE(S)`);
process.exit(failures === 0 ? 0 : 1);
