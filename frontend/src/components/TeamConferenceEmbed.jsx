/**
 * TeamConferenceEmbed — exec-admin-only Team Conference bridge.
 *
 * Reality correction (2026-08-27): the conference-bridge embed was previously a
 * static script tag in public/index.html, so the floating "Team Conference"
 * panel + shared room rendered for EVERY visitor. Team Conference is an
 * executive/admin feature — not a public interface. This component injects the
 * same embed script (same slug/origin/label attrs, so the WAI side keeps
 * matching this deployment) but ONLY when the signed-in user holds admin rank
 * or higher. Logged-out and non-staff visitors get nothing.
 */
import { useEffect, useRef } from "react";
import { useAuth } from "../lib/auth";
import { ROLE_RANK } from "../lib/roles";

const EMBED_URL = "https://wai-institute-production.up.railway.app/embed/conference-bridge.js";

const EMBED_ATTRS = {
  src: EMBED_URL,
  "data-slug": "wai-morehelp-bridge",
  "data-origin": "morehelp",
  "data-label": "MORE Help Center",
  "data-site-url": "https://www.morehelp.center",
};

export default function TeamConferenceEmbed() {
  const { user, loading } = useAuth();
  const injectedRef = useRef(false);

  useEffect(() => {
    if (loading || !user) return;
    const rank = ROLE_RANK[user.role] ?? 0;
    if (rank < (ROLE_RANK.admin ?? 0)) return;
    if (injectedRef.current || document.getElementById("wai-conference-bridge-script")) return;

    const script = document.createElement("script");
    script.id = "wai-conference-bridge-script";
    for (const [k, v] of Object.entries(EMBED_ATTRS)) {
      script.setAttribute(k, v);
    }
    script.defer = true;
    document.body.appendChild(script);
    injectedRef.current = true;
  }, [user, loading]);

  return null;
}
