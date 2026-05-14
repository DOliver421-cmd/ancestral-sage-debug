import { useEffect } from "react";
import { useAuth } from "../lib/auth";

// Helper routes render the actual standalone HTML helper UIs via iframe.
// /helper     → public/helper/index.html  (no auth required)
// /app/helper → app/helper/index.html     (requires WAI session)

export default function Helper({ requireAuth = false }) {
  const { user, loading } = useAuth();

  useEffect(() => {
    // Hide the floating Help Center FAB on these pages to avoid recursion
    const fab = document.getElementById("wai-helper-fab");
    if (fab) fab.style.display = "none";
    return () => {
      if (fab) fab.style.display = "";
    };
  }, []);

  if (loading) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100vh", fontFamily: "system-ui" }}>
        Loading…
      </div>
    );
  }

  if (requireAuth && !user) {
    window.location.href = "/login";
    return null;
  }

  const src = requireAuth ? "/app/helper/index.html" : "/public/helper/index.html";

  return (
    <iframe
      src={src}
      title={requireAuth ? "Helper – Authenticated Workspace" : "W.A.I. Help Center"}
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        width: "100%",
        height: "100%",
        border: "none",
        zIndex: 1,
      }}
      allow="microphone; camera"
    />
  );
}
