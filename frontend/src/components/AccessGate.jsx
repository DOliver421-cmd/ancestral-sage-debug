import { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import { loadGates, isPageEnabled, isGatesFailed, isLaunchMode } from "../lib/accessGates";
import { useAuth } from "../lib/auth";

/**
 * AccessGate — wraps <Routes>. When an exec gate disables the current page,
 * the gate renders an "offline" card instead of the page. When gates fail to
 * load AND launch_mode is active, the gate defaults to hiding pages (fail-closed).
 */
export default function AccessGate({ children }) {
  const location = useLocation();
  const { user } = useAuth();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let alive = true;
    loadGates().finally(() => {
      if (alive) setReady(true);
    });
    return () => {
      alive = false;
    };
  }, []);

  // While gates are loading, show a neutral loading state — NOT children.
  // A disabled page must not flash before the gate map resolves.
  if (!ready) {
    return (
      <div className="min-h-screen bg-bone flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-copper border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  // If gates failed to load AND launch_mode is on, fail-closed:
  // hide the page rather than rendering it blind.
  if (isGatesFailed() && isLaunchMode()) {
    return (
      <div className="min-h-screen bg-bone flex items-center justify-center px-6">
        <div className="text-center max-w-md">
          <div className="text-5xl mb-4">🚧</div>
          <h1 className="font-heading text-2xl font-bold mb-2">Access temporarily unavailable</h1>
          <p className="text-ink/60 text-sm leading-relaxed">
            The access gate is unavailable and launch mode is active. Try again in a moment.
          </p>
        </div>
      </div>
    );
  }

  if (!isPageEnabled(location.pathname, user)) {
    return (
      <div className="min-h-screen bg-bone flex items-center justify-center px-6">
        <div className="text-center max-w-md">
          <div className="text-5xl mb-4">🚧</div>
          <h1 className="font-heading text-2xl font-bold mb-2">This page is currently offline</h1>
          <p className="text-ink/60 text-sm leading-relaxed">
            The executive team has temporarily closed this page. It will be back — explore the rest of the site in the meantime.
          </p>
        </div>
      </div>
    );
  }

  return children;
}
