/**
 * visual-capture.mjs — free visual-state capture for the Dual-Trigger
 * Visual Rollback System (owner directive, 2026-09-02).
 *
 * Runs on a GitHub Actions ubuntu-latest runner with `puppeteer` installed
 * (see .github/workflows/visual-state-capture.yml).  Captures full-page
 * screenshots of the public landing page, the login page, and — when
 * MORE_SHOT_EMAIL / MORE_SHOT_PASSWORD are provided — the member dashboard
 * after a best-effort sign-in.  Each PNG is gzip+base64 encoded and posted
 * to the backend ingest endpoint /api/v1/system/visual-state, signed with
 * HMAC-SHA256 in the X-MORE-Signature header (same secret as the emergency
 * revert webhook).  Zero paid infrastructure.
 */

import { createHmac } from "node:crypto";
import { gzipSync } from "node:zlib";
import puppeteer from "puppeteer";

const PUBLIC_URL = (process.env.MORE_PUBLIC_URL || "https://charming-analysis-morehelpcenter.up.railway.app").replace(/\/+$/, "");
const BACKEND_URL = (process.env.MORE_BACKEND_URL || PUBLIC_URL).replace(/\/+$/, "");
const SECRET = process.env.MORE_ROLLBACK_WEBHOOK_SECRET || "";
const SHOT_EMAIL = process.env.MORE_SHOT_EMAIL || "";
const SHOT_PASSWORD = process.env.MORE_SHOT_PASSWORD || "";

if (!SECRET) {
  console.error("visual-capture: MORE_ROLLBACK_WEBHOOK_SECRET is not configured — aborting.");
  process.exit(1);
}

const encodeShot = (png) => gzipSync(Buffer.from(png)).toString("base64");

async function capturePage(page, url, name) {
  await page.goto(url, { waitUntil: "networkidle2", timeout: 45000 });
  await new Promise((r) => setTimeout(r, 1500));
  const png = await page.screenshot({ fullPage: true, type: "png" });
  console.log(`visual-capture: captured ${name} (${png.length} bytes)`);
  return encodeShot(png);
}

async function main() {
  const browser = await puppeteer.launch({
    headless: "new",
    args: ["--no-sandbox", "--disable-setuid-sandbox"],
  });
  try {
    const page = await browser.newPage();
    await page.setViewport({ width: 1440, height: 900 });

    const urls = {};
    urls.landing = await capturePage(page, `${PUBLIC_URL}/`, "landing");
    urls.login = await capturePage(page, `${PUBLIC_URL}/login`, "login");

    if (SHOT_EMAIL && SHOT_PASSWORD) {
      try {
        await page.type('input[type="email"], input[name="email"]', SHOT_EMAIL);
        await page.type('input[type="password"], input[name="password"]', SHOT_PASSWORD);
        await Promise.all([
          page.waitForNavigation({ waitUntil: "networkidle2", timeout: 30000 }).catch(() => {}),
          page.click('button[type="submit"], button:has-text("Sign in")').catch(() => {}),
        ]);
        await new Promise((r) => setTimeout(r, 2500));
        urls.dashboard = await capturePage(page, `${PUBLIC_URL}/dashboard`, "dashboard");
      } catch (err) {
        console.warn(`visual-capture: dashboard login attempt failed (${err.message}) — public shots only.`);
      }
    }

    const body = JSON.stringify({
      urls,
      captured_at: new Date().toISOString(),
    });
    const signature = createHmac("sha256", SECRET).update(body).digest("hex");

    const resp = await fetch(`${BACKEND_URL}/api/v1/system/visual-state`, {
      method: "POST",
      headers: {
        "content-type": "application/json",
        "x-more-signature": signature,
      },
      body,
    });
    const text = await resp.text();
    console.log(`visual-capture: ingest status=${resp.status} body=${text.slice(0, 300)}`);
    if (resp.status >= 400) process.exitCode = 2;
  } finally {
    await browser.close();
  }
}

main().catch((err) => {
  console.error("visual-capture failed:", err);
  process.exit(1);
});