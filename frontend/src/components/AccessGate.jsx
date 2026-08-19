import { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import { loadGates, isPageEnabled } from "../lib/accessGates";

/**
 * AccessGate — wraps <Routes>. When an exec gate disables the current page,
 * the gate renders an "offline" card instead of the page. Gates load once and
 * default to open, so a backend hiccup never takes the site down.
 */
export default function AccessGate({ children }) {
  const location = useLocation();
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

  if (!ready) return children;

  if (!isPageEnabled(location.pathname)) {
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
