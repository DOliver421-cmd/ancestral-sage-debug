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
    const next = searchParams.get("next") || "/dashboard";

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

        // Store the local JWT
        localStorage.setItem("lce_token", data.token);

        // Store user info
        localStorage.setItem("lce_user", JSON.stringify({ role: data.role }));

        setStatus("Login successful! Redirecting…");

        // Navigate to the intended page
        setTimeout(() => navigate(next, { replace: true }), 500);
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
