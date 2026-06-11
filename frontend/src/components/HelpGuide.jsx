import { useState, useEffect, useRef, useCallback } from "react";
import { useLocation } from "react-router-dom";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import { HelpCircle, X, Search, ArrowRight, ExternalLink } from "lucide-react";

// Routes that have their own tool panels — HelpGuide is suppressed here
const SUPPRESS_PATHS = ["/jamil", "/arena", "/projects"];

export default function HelpGuide() {
  const { user } = useAuth();
  const location = useLocation();

  if (SUPPRESS_PATHS.some(p => location.pathname === p || location.pathname.startsWith(p + "/"))) {
    return null;
  }
  const [open, setOpen] = useState(false);
  const [help, setHelp] = useState(null);
  const [query, setQuery] = useState("");
  const [busy, setBusy] = useState(false);
  const panelRef = useRef(null);

  const fetchHelp = useCallback(async (path, q) => {
    if (!user) return;
    setBusy(true);
    try {
      const r = await api.post("/help/guide", { path, query: q || null });
      setHelp(r.data);
    } catch {
      setHelp(null);
    } finally {
      setBusy(false);
    }
  }, [user]);

  useEffect(() => {
    if (open) fetchHelp(location.pathname, query);
  }, [open, location.pathname, query, fetchHelp]);

  useEffect(() => {
    if (!open) return;
    const handler = (e) => {
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [open]);

  useEffect(() => {
    if (!open || !panelRef.current) return;
    const handler = (e) => {
      if (panelRef.current && !panelRef.current.contains(e.target) && !e.target.closest("[data-help-toggle]")) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [open]);

  return (
    <>
      {/* Floating toggle button */}
      <button
        data-help-toggle
        onClick={() => setOpen(!open)}
        className="fixed bottom-6 right-6 z-50 w-14 h-14 bg-copper text-white rounded-full shadow-2xl flex items-center justify-center hover:bg-copper/90 transition-all hover:scale-110 focus:outline-none focus:ring-4 focus:ring-copper/30"
        aria-label="Help guide"
        title="Help guide (?)"
      >
        {open ? <X className="w-6 h-6" /> : <HelpCircle className="w-6 h-6" />}
      </button>

      {/* Help panel */}
      {open && (
        <div
          ref={panelRef}
          className="fixed bottom-24 right-6 z-50 w-80 sm:w-96 max-h-[70vh] bg-white rounded-2xl shadow-2xl border border-ink/10 flex flex-col overflow-hidden animate-fade-in"
        >
          {/* Header */}
          <div className="bg-ink text-white px-5 py-4">
            <div className="flex items-center justify-between">
              <h3 className="font-heading font-bold text-sm uppercase tracking-wider">Sage Guide</h3>
              <span className="text-xs text-white/50">Context help</span>
            </div>
            {/* Search */}
            <div className="mt-3 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/40" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search help…"
                className="w-full pl-10 pr-4 py-2 text-sm bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-copper/50"
              />
            </div>
          </div>

          {/* Body */}
          <div className="flex-1 overflow-y-auto p-5 space-y-4">
            {busy && (
              <div className="flex items-center justify-center py-8">
                <div className="w-6 h-6 border-2 border-copper border-t-transparent rounded-full animate-spin" />
              </div>
            )}

            {!busy && help && (
              <>
                <div>
                  <h4 className="font-heading font-bold text-lg text-ink">{help.title}</h4>
                  <p className="text-sm text-ink/70 mt-1">{help.summary}</p>
                </div>

                {help.tip && (
                  <div className="bg-copper/5 border-l-4 border-copper rounded-r-lg px-4 py-3">
                    <p className="text-xs font-bold text-copper uppercase tracking-wider">Tip for you</p>
                    <p className="text-sm text-ink/80 mt-1">{help.tip}</p>
                  </div>
                )}

                {help.details && help.details.length > 0 && (
                  <div>
                    <p className="text-xs font-bold text-ink/50 uppercase tracking-wider mb-2">Key Info</p>
                    <ul className="space-y-2">
                      {help.details.map((d, i) => (
                        <li key={i} className="text-sm text-ink/70 flex items-start gap-2">
                          <span className="text-copper mt-1 shrink-0">•</span>
                          {d}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {help.common_tasks && help.common_tasks.length > 0 && (
                  <div>
                    <p className="text-xs font-bold text-ink/50 uppercase tracking-wider mb-2">Quick Actions</p>
                    <div className="flex flex-wrap gap-2">
                      {help.common_tasks.map((task, i) => (
                        <a
                          key={i}
                          href={task}
                          className="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-bold bg-copper/10 text-copper rounded-lg hover:bg-copper/20 transition-colors"
                        >
                          <ArrowRight className="w-3 h-3" /> {task.replace("/", "").replace("-", " ") || "Home"}
                        </a>
                      ))}
                    </div>
                  </div>
                )}

                {help.related && help.related.length > 0 && (
                  <div className="pt-2 border-t border-ink/10">
                    <p className="text-xs font-bold text-ink/50 uppercase tracking-wider mb-2">Related Pages</p>
                    <div className="flex flex-wrap gap-2">
                      {help.related.map((link, i) => (
                        <a
                          key={i}
                          href={link}
                          className="inline-flex items-center gap-1 text-xs text-ink/60 hover:text-copper transition-colors"
                        >
                          <ExternalLink className="w-3 h-3" /> {link}
                        </a>
                      ))}
                    </div>
                  </div>
                )}
              </>
            )}

            {!busy && !help && (
              <div className="text-center py-8 text-sm text-ink/50">
                <p>Sign in to get personalized help for this page.</p>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="border-t border-ink/10 px-5 py-3 bg-ink/5">
            <a
              href="/help-center"
              className="text-xs text-copper hover:underline flex items-center gap-1"
            >
              <ExternalLink className="w-3 h-3" /> Visit Help Center
            </a>
          </div>
        </div>
      )}

      {/* Keyboard shortcut hint */}
      {!open && (
        <div className="fixed bottom-6 right-6 z-40 pointer-events-none translate-y-16 opacity-0" />
      )}
    </>
  );
}
