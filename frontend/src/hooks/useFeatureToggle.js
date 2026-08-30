/**
 * useFeatureToggle — Executive Feature Toggle Hook
 *
 * Checks runtime availability of platform features and pages via the
 * executive control plane.  Reads from the same backend stores as the
 * enforcement middleware:
 *   - db.platform_flags   (feature flags)
 *   - db.page_access      (page visibility)
 *   - db.feature_configs  (FCC overrides)
 *
 * Usage:
 *   const { isFeatureEnabled, isPageEnabled, loading } = useFeatureToggle();
 *   if (!isFeatureEnabled('ai_chat')) return <Disabled />;
 */

import { useState, useEffect, useCallback } from "react";
import { api } from "../lib/api";

const FLAGS_URL = "/exec/control/access/public";

export function useFeatureToggle() {
  const [flags, setFlags] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let alive = true;
    api.get(FLAGS_URL)
      .then((r) => {
        if (alive) {
          setFlags(r.data?.pages || {});
          setLoading(false);
        }
      })
      .catch(() => {
        if (alive) setLoading(false);
      });
    return () => { alive = false; };
  }, []);

  const isFeatureEnabled = useCallback((featureId) => {
    if (loading) return true;
    const entry = flags[featureId];
    if (!entry) return true;
    return entry.enabled !== false;
  }, [flags, loading]);

  const isPageEnabled = useCallback((pathname) => {
    if (loading) return true;
    const key = pathToKey(pathname);
    const entry = flags[key];
    if (!entry) return true;
    return entry.enabled !== false;
  }, [flags, loading]);

  return { isFeatureEnabled, isPageEnabled, flags, loading };
}

function pathToKey(pathname) {
  const p = pathname || "/";
  if (p === "/admin/control") return "site-control";
  if (p === "/admin/features") return "feature-control";
  if (p === "/admin/office") return "exec-business-office";
  if (p === "/admin/exec-control") return "exec-control";
  if (p === "/admin/director") return "director";
  if (p === "/admin/accounts") return "account-controls";
  if (p === "/partnership/discounts") return "partnership-discounts";
  if (p === "/creator/payouts") return "creator-payouts";
  if (p === "/missing-kameron") return "missing-kameron";
  return p.split("/").filter(Boolean)[0] || "home";
}
