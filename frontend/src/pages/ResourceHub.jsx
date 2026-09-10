/**
 * /resources — Unified Resource Hub
 *
 * Grants, Fundraising, Business Resources — one workspace with real workflows.
 * Not a link collection. Interactive forms, status tracking, guided workflows.
 * Access: Plus+ tier, free for staff.
 */

import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import { canAccess } from "../lib/tiers";
import AppShell from "../components/AppShell";
import BackButton from "../components/BackButton";
import ResourceHubPanel from "../components/ResourceHubPanel";
import { Loader2, Briefcase } from "lucide-react";

export default function ResourceHub() {
  const { user, loading } = useAuth();
  const [tier, setTier] = useState("free");

  useEffect(() => {
    if (user) {
      const t = user.feature_tier || "free";
      const r = user.role || "";
      const isStaff = ["instructor", "admin", "executive_admin", "support_staff", "oversight"].includes(r);
      setTier(isStaff ? "staff" : t);
    }
  }, [user]);

  if (loading) {
    return (
      <AppShell>
        <div className="flex items-center justify-center py-24 text-ink/40">
          <Loader2 className="w-5 h-5 animate-spin mr-2" /> Loading Resource Hub…
        </div>
      </AppShell>
    );
  }

  if (!user) {
    return (
      <AppShell>
        <div className="max-w-xl mx-auto mt-16 card-flat p-8 text-center">
          <Briefcase className="w-8 h-8 text-copper mx-auto mb-3" />
          <h1 className="font-heading font-bold text-xl text-ink">Sign in to the Resource Hub</h1>
          <p className="text-sm text-ink/60 mt-2">Grants, fundraising, business resources — all in one workspace.</p>
        </div>
      </AppShell>
    );
  }

  if (!canAccess(user, "resource_hub")) {
    return (
      <AppShell>
        <div className="max-w-xl mx-auto mt-16 card-flat p-8 text-center">
          <Briefcase className="w-8 h-8 text-copper mx-auto mb-3" />
          <h1 className="font-heading font-bold text-xl text-ink">Plus membership required</h1>
          <p className="text-sm text-ink/60 mt-2">The Resource Hub requires a Plus subscription or higher. Staff access is included automatically.</p>
          <Link to="/subscribe" className="btn-primary mt-4 inline-flex">Upgrade to Plus</Link>
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <BackButton />
      <ResourceHubPanel user={user} />
    </AppShell>
  );
}
