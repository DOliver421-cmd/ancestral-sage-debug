import React, { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { BACKEND_URL } from "../lib/api";

/**
 * CrossSiteLogin — handles the SSO redirect from the partner site.
 *
 * Flow:
 *   1. User is on wai-institute.org, clicks "Open in M.O.R.E."
 *   2. wai-institute.org generates a cross-site token via /api/auth/cross-site-token
 *   3. Frontend redirects to morehelp.center/auth/cross-site?token=<token>&next=<path>
 *   4. This page exchanges the token for a local JWT via /api/auth/cross-site-login
 *   5. Stores the JWT and navigates to the intended page (or dashboard)
 */
export default function CrossSiteLogin() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState("Exchanging token…");

  useEffect(() => {
    const token = searchParams.get("token");
    const nextRaw = searchParams.get("next") || "/dashboard";

    // `next` arrives in a URL an attacker can craft, and this page applies it
    // with window.location.assign AFTER a successful sign-in — an
    // unvalidated value is an open redirect that hands the freshly
    // authenticated user to any origin. Only accept same-site paths.
    const next = (() => {
      if (typeof nextRaw !== "string" || !nextRaw.startsWith("/") || nextRaw.startsWith("//")) {
        return "/dashboard";
      }
      try {
        // Resolve against this origin and compare hosts: blocks //evil.com
        // (protocol-relative) and "/\evil.com" style tricks the startsWith
        // checks above miss.
        const resolved = new URL(nextRaw, window.location.origin);
        if (resolved.origin !== window.location.origin) return "/dashboard";
        return resolved.pathname + resolved.search + resolved.hash;
      } catch {
        return "/dashboard";
      }
    })();

    if (!token) {
      setStatus("No token provided. Redirecting to login…");
      setTimeout(() => navigate("/login", { replace: true }), 2000);
      return;
    }

    (async () => {
      try {
        const res = await fetch(`${BACKEND_URL}/api/auth/cross-site-login`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ token }),
        });

        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          setStatus(err.detail || "Token expired or invalid. Redirecting to login…");
          setTimeout(() => navigate("/login", { replace: true }), 2000);
          return;
        }

        const data = await res.json();

        // Store the local JWT first: it is the one guaranteed part of this
        // response.
        localStorage.setItem("lce_token", data.token);

        // Hydrate the cached user from /auth/me instead of trusting the
        // response body. The peer deployment is a separate build that may be
        // older than this one, so `user` is not guaranteed to exist in the
        // response; falling back to a role-only object is what left every
        // useAuth() consumer showing incomplete data.
        let hydrated = null;
        try {
          const me = await fetch(`${BACKEND_URL}/api/auth/me`, {
            headers: { Authorization: `Bearer ${data.token}` },
          });
          if (me.ok) hydrated = await me.json();
        } catch { /* fall through to the login redirect below */ }

        if (!hydrated || !hydrated.id) {
          // A token with no readable user is not a sign-in. Clear the partial
          // state rather than limping along with a half-session.
          localStorage.removeItem("lce_token");
          localStorage.removeItem("lce_user");
          setStatus("Could not complete the sign-in. Redirecting to login…");
          setTimeout(() => navigate("/login", { replace: true }), 1500);
          return;
        }

        localStorage.setItem("lce_user", JSON.stringify(hydrated));

        setStatus("Login successful! Redirecting…");

        // A full reload lets the AuthProvider re-initialise from the cached
        // user rather than relying on a one-shot mount effect that has
        // already run.
        setTimeout(() => { window.location.assign(next); }, 500);
      } catch (e) {
        setStatus("Connection error. Redirecting to login…");
        setTimeout(() => navigate("/login", { replace: true }), 2000);
      }
    })();
  }, [searchParams, navigate]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-bg">
      <div className="bg-card border border-border rounded-xl p-8 max-w-md w-full text-center">
        <div className="animate-spin w-8 h-8 border-2 border-accent border-t-transparent rounded-full mx-auto mb-4" />
        <p className="text-ink font-heading text-lg">{status}</p>
        <p className="text-muted text-sm mt-2">
          Connecting you to the partner site…
        </p>
      </div>
    </div>
  );
}
