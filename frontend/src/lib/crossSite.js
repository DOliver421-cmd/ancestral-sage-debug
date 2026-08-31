/**
 * crossSite.js — Cross-site SSO navigation helper.
 *
 * Usage:
 *   import { openPartnerSite } from "../lib/crossSite";
 *
 *   // In a button onClick:
 *   openPartnerSite("more");  // navigates to morehelp.center
 *   openPartnerSite("wai");   // navigates to wai-institute.org
 */

import { BACKEND_URL } from "./api";

const PARTNER_URLS = {
  more: "https://www.morehelp.center",
  wai: "https://www.wai-institute.org",
};

/**
 * Navigate to the partner site with a cross-site SSO token.
 *
 * 1. Fetches a cross-site token from the current site's API
 * 2. Redirects to the partner site with the token + intended path
 *
 * @param {"more" | "wai"} partner - which partner site to open
 * @param {string} nextPath - path to navigate to on the partner site (default: /dashboard)
 */
export async function openPartnerSite(partner, nextPath = "/dashboard") {
  const partnerUrl = PARTNER_URLS[partner];
  if (!partnerUrl) {
    console.error("Unknown partner:", partner);
    return;
  }

  const token = localStorage.getItem("lce_token");
  if (!token) {
    // Not logged in — just go to the partner site's login
    window.location.href = `${partnerUrl}/login`;
    return;
  }

  try {
    // Get a cross-site token from the current site
    const res = await fetch(`${BACKEND_URL}/api/auth/cross-site-token`, {
      headers: { Authorization: `Bearer ${token}` },
    });

    if (!res.ok) {
      // Token expired or invalid — redirect to partner login
      window.location.href = `${partnerUrl}/login`;
      return;
    }

    const data = await res.json();
    const crossToken = data.token;

    // Redirect to the partner site with the token
    const partnerLoginUrl = `${partnerUrl}/auth/cross-site?token=${encodeURIComponent(crossToken)}&next=${encodeURIComponent(nextPath)}`;
    window.location.href = partnerLoginUrl;
  } catch (e) {
    // Network error — fallback to partner login
    console.error("Cross-site token exchange failed:", e);
    window.location.href = `${partnerUrl}/login`;
  }
}
