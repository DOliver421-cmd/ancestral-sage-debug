import { useState, useEffect } from "react";
import { useLocation } from "react-router-dom";
import { api } from "../lib/api";

const CONSENT_KEY = "cookie_consent_v1";

// Admin/tool routes where the banner must not block the interface
const SUPPRESS_PATHS = ["/jamil", "/arena", "/projects", "/admin", "/store", "/studio",
  "/ghost-producer", "/band", "/creator", "/more/ops", "/supervisor"];

export default function CookieConsent() {
  const [visible, setVisible] = useState(false);
  const location = useLocation();

  const suppressed = SUPPRESS_PATHS.some(
    p => location.pathname === p || location.pathname.startsWith(p + "/")
  );

  useEffect(() => {
    if (suppressed) return;
    const stored = localStorage.getItem(CONSENT_KEY);
    if (!stored) {
      const timer = setTimeout(() => setVisible(true), 500);
      return () => clearTimeout(timer);
    }
  }, [suppressed]);

  const record = async (choice) => {
    try { await api.post("/consent/cookie", { choice }); } catch {}
  };

  const accept = () => {
    localStorage.setItem(CONSENT_KEY, "accepted");
    record("accepted");
    setVisible(false);
  };

  const decline = () => {
    localStorage.setItem(CONSENT_KEY, "declined");
    record("declined");
    setVisible(false);
  };

  if (!visible || suppressed) return null;

  return (
    <div className="fixed bottom-0 left-0 right-0 z-50 bg-ink text-white p-4 shadow-2xl border-t border-copper/30">
      <div className="max-w-4xl mx-auto flex flex-col sm:flex-row items-start sm:items-center gap-4">
        <p className="text-sm text-white/80 flex-1">
          We use essential cookies for authentication and security. We do not sell your data.
          By continuing, you agree to our{" "}
          <a href="/terms" className="text-copper hover:underline">Terms of Service</a>{" "}
          and{" "}
          <a href="/privacy" className="text-copper hover:underline">Privacy Policy</a>.
        </p>
        <div className="flex gap-3 shrink-0">
          <button
            onClick={decline}
            className="px-4 py-2 text-sm border border-white/30 rounded hover:bg-white/10 transition-colors"
          >
            Decline
          </button>
          <button
            onClick={accept}
            className="px-4 py-2 text-sm bg-copper text-white font-bold rounded hover:bg-copper/90 transition-colors"
          >
            Accept
          </button>
        </div>
      </div>
    </div>
  );
}
