#!/usr/bin/env node
/**
 * route-integrity.js — Phase B guard rail (the "no dead paths" standard).
 *
 * Crawls the app's link graph and fails when a link would dead-end:
 *
 *   1. REGISTRY DRIFT — every ROUTES constant / ROUTE_BUILDERS builder in
 *      src/lib/routes.js must resolve against a <Route> in src/App.js.
 *   2. LINK CRAWL — every <Link to>, nav()/navigate(), <Navigate to>,
 *      internal <a href> and window.location target in src/ must resolve to
 *      a real route (not the catch-all 404).
 *   3. STATIC ASSETS — every ORIGINAL_TOOLS path must have a real file under
 *      public/ (catches a deleted original before it 404s in production).
 *
 * Usage:  node scripts/route-integrity.js   (or: npm run test:routes)
 * Exit code 1 when dead links are found — wire this into CI.
 */

const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..");
const SRC = path.join(ROOT, "src");
const PUBLIC = path.join(ROOT, "public");

const failures = [];
const warnings = [];

// ── 1. Build the route table from App.js (the authority) ────────────────────
const appSource = fs.readFileSync(path.join(SRC, "App.js"), "utf8");
// Matches path="/x", path="/x/:slug", path="*"
const routePatterns = [...appSource.matchAll(/path="([^"]+)"/g)]
  .map((m) => m[1])
  .filter((p) => p !== "*"); // the catch-all renders Error404 — not a real destination

// Redirect targets must themselves resolve (no redirect-to-a-404).
const redirectTargets = [...appSource.matchAll(/<Navigate[^>]*\sto=["']([^"']+)["']/g)].map((m) => m[1]);

// ── 2. Load the canonical registry (drift check) ────────────────────────────
const routesSource = fs.readFileSync(path.join(SRC, "lib", "routes.js"), "utf8");
const registryEntries = []; // { label, pattern }
for (const m of routesSource.matchAll(/^\s{2}(\w+):\s*"(\/[^"]*)",?$/gm)) {
  registryEntries.push({ label: `ROUTES.${m[1]}`, pattern: m[2] });
}
for (const m of routesSource.matchAll(/^\s{2}(\w+):\s*\([^)]*\)\s*=>\s*`([^`]*)`,?$/gm)) {
  const tpl = m[2].replace(/\$\{[^}]*\}/g, ":p"); // builder template → pattern
  registryEntries.push({ label: `builder ${m[1]}`, pattern: tpl });
}

// ── 3. Crawl every source file for link targets ─────────────────────────────
const LINK_RULES = [
  { name: "Link/JSX to= string", re: /to=["']([^"']+)["']/g },
  { name: "Link/JSX to= template", re: /to=\{`([^`]+)`\}/g },
  { name: "nav()/navigate()", re: /\b(?:nav|navigate)\(\s*["'`]([^"'`]+)["'`]\s*\)/g },
  { name: "internal <a href>", re: /href=["']([^"']+)["']/g },
  { name: "window.location", re: /window\.location\.(?:replace|assign|href)\s*=\s*["']([^"']+)["']/g },
];

function walk(dir) {
  const out = [];
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    if (entry.name.startsWith(".") || entry.name === "node_modules") continue;
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) out.push(...walk(full));
    else if (/\.(js|jsx)$/.test(entry.name)) out.push(full);
  }
  return out;
}

const candidates = []; // { file, line, raw, via }
for (const file of walk(SRC)) {
  const source = fs.readFileSync(file, "utf8");
  for (const rule of LINK_RULES) {
    let m;
    rule.re.lastIndex = 0;
    while ((m = rule.re.exec(source)) !== null) {
      const line = source.slice(0, m.index).split("\n").length;
      candidates.push({ file, line, raw: m[1], via: rule.name });
    }
  }
}

// ── 4. Normalize + match ────────────────────────────────────────────────────
function normalize(pathStr) {
  let p = pathStr.trim();
  if (!p.startsWith("/")) return null;
  if (p.startsWith("//")) return null; // protocol-relative
  if (/^(https?:|mailto:|tel:|data:|javascript:)/.test(p)) return null; // external
  if (p.startsWith("#")) return null; // in-page anchor
  p = p.split("?")[0].split("#")[0]; // strip query / fragment
  p = p.replace(/\$\{[^}]*\}/g, ":p"); // template literal params → wildcard
  return p || null;
}

function routeMatches(pattern, candidate) {
  const ps = pattern.split("/").filter(Boolean);
  const cs = candidate.split("/").filter(Boolean);
  if (ps.length !== cs.length) return false;
  return ps.every((seg, i) => seg.startsWith(":") || seg === cs[i]);
}

// ── 5. Checks ───────────────────────────────────────────────────────────────
for (const entry of registryEntries) {
  const ok = routePatterns.some((rp) => routeMatches(rp, normalize(entry.pattern) || ""));
  if (!ok) failures.push(`REGISTRY DRIFT: ${entry.label} (${entry.pattern}) does not resolve to any <Route> in App.js`);
}

for (const target of redirectTargets) {
  const norm = normalize(target);
  if (norm && !routePatterns.some((rp) => routeMatches(rp, norm))) {
    failures.push(`App.js <Navigate to="${target}"> points at an unregistered route`);
  }
}

// A link is also valid when it targets a real static asset (href to a file in
// public/, e.g. the original HTML tools) — it just isn't a React route.
function isPublicAsset(candidate) {
  return fs.existsSync(path.join(PUBLIC, candidate));
}

const seen = new Set();
for (const c of candidates) {
  const norm = normalize(c.raw);
  if (!norm) continue;
  if (norm.startsWith("/api/")) continue; // backend endpoint — covered by backend tests, not SPA routing
  const key = `${c.file}:${c.line}:${norm}`;
  if (seen.has(key)) continue;
  seen.add(key);
  if (routePatterns.some((rp) => routeMatches(rp, norm))) continue;
  if (isPublicAsset(norm)) continue; // real file under public/ — valid static link
  failures.push(`${c.file}:${c.line} — ${c.raw} (via ${c.via}) does not resolve to a route or public asset`);
}

// Static assets: every original tool path must exist in public/ — unless the
// tool is explicitly marked `status: "unavailable"` (honest retired state).
const toolsSource = fs.readFileSync(path.join(SRC, "lib", "originalTools.js"), "utf8");
const toolEntries = [];
for (const m of toolsSource.matchAll(/slug:\s*"([^"]+)"[\s\S]*?path:\s*"([^"]+)"[\s\S]*?(?:status:\s*"([^"]+)")?[\s\S]*?},/g)) {
  toolEntries.push({ slug: m[1], asset: m[2], status: m[3] || "available" });
}
for (const t of toolEntries) {
  if (t.status === "unavailable") {
    warnings.push(`originalTools.js: ${t.slug} is marked unavailable — hub will show the availability banner`);
    continue;
  }
  if (!fs.existsSync(path.join(PUBLIC, t.asset))) {
    failures.push(`originalTools.js: "${t.slug}" path "${t.asset}" has no file in public/ — the Launch button would 404`);
  }
}

// ── 6. Report ───────────────────────────────────────────────────────────────
console.log(`route-integrity: ${routePatterns.length} routes, ${registryEntries.length} registry entries, ${seen.size} link candidates, ${redirectTargets.length} redirects, ${toolEntries.length} original tools`);

if (failures.length) {
  console.error("\n❌ DEAD LINKS / DRIFT FOUND — fix before shipping:\n");
  for (const f of failures) console.error("  - " + f);
  console.error(`\n${failures.length} failure(s).`);
  process.exit(1);
}

if (warnings.length) {
  console.log("\n⚠️  Warnings:");
  for (const w of warnings) console.log("  - " + w);
}

console.log("\n✅ All links resolve. No dead paths.");
