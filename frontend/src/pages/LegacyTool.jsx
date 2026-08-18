/**
 * LegacyTool — full-page wrapper for an ORIGINAL standalone HTML application.
 *
 * The originals are full-featured apps (some 100KB+ of hand-built HTML/JS/CSS)
 * that predate the React pages. They are preserved — never deleted — and this
 * wrapper serves them in-app with the platform shell: title bar, back link,
 * and an "Open full screen" escape hatch for the standalone experience.
 *
 * If the browser blocks the iframe (X-Frame-Options or CSP from a proxy/CDN),
 * the component shows a graceful fallback with a direct link to the full-screen
 * version so the user never hits a dead end.
 *
 * Usage: <LegacyTool slug="djedi-oracle" />
 */

import { useState } from "react";
import { Link, Navigate } from "react-router-dom";
import AppShell from "../components/AppShell";
import { ORIGINAL_BY_SLUG } from "../lib/originalTools";
import { ArrowLeft, ExternalLink, FileArchive, AlertTriangle } from "lucide-react";

export default function LegacyTool({ slug }) {
  const tool = ORIGINAL_BY_SLUG[slug];
  const [blocked, setBlocked] = useState(false);

  if (!tool) return <Navigate to="/classic-tools" replace />;

  return (
    <AppShell>
      <div className="min-h-screen flex flex-col bg-bone">
        {/* Title bar */}
        <header className="border-b border-ink/10 bg-white shrink-0" data-testid="legacy-tool-bar">
          <div className="max-w-[1400px] mx-auto px-4 sm:px-6 py-3 flex items-center justify-between gap-3 flex-wrap">
            <div className="flex items-center gap-3 min-w-0">
              <Link to="/classic-tools" className="flex items-center gap-1.5 text-sm font-bold text-ink/60 hover:text-copper transition-colors shrink-0">
                <ArrowLeft className="w-4 h-4" /> Classic Tools
              </Link>
              <span className="text-ink/15">|</span>
              <span style={{ fontSize: 20 }}>{tool.icon}</span>
              <div className="min-w-0">
                <div className="font-heading font-bold text-ink truncate">{tool.title}</div>
                <div className="text-[10px] font-black uppercase tracking-widest text-copper">
                  Original edition · {tool.suite}
                </div>
              </div>
            </div>
            <a
              href={tool.path}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 text-xs font-black px-3 py-2 rounded-lg border transition-colors"
              style={{ borderColor: "#ddd3bf", color: "#1B4332" }}
            >
              <ExternalLink className="w-3.5 h-3.5" /> Open full screen
            </a>
          </div>
        </header>

        {/* The original app — or a graceful fallback if the iframe is blocked */}
        <div className="flex-1 relative" data-testid="legacy-tool-frame">
          {blocked ? (
            <div className="absolute inset-0 flex items-center justify-center bg-bone p-8">
              <div className="max-w-md w-full text-center space-y-5">
                <div className="flex items-center justify-center gap-3 text-amber-700">
                  <AlertTriangle className="w-8 h-8" />
                  <span className="font-heading font-bold text-xl">Inline view blocked</span>
                </div>
                <p className="text-ink/70 text-sm leading-relaxed">
                  Your browser's security settings are preventing this tool from loading inside the page.
                  The tool itself is fully working — open it in its own tab using the button below.
                </p>
                <a
                  href={tool.path}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 px-6 py-3 rounded-xl text-sm font-black text-white"
                  style={{ background: "#1B4332" }}
                >
                  <ExternalLink className="w-4 h-4" />
                  Open {tool.title} — full screen
                </a>
                <div>
                  <Link to="/classic-tools" className="text-xs text-ink/40 hover:text-copper transition-colors">
                    ← Back to Classic Tools
                  </Link>
                </div>
              </div>
            </div>
          ) : (
            <iframe
              src={tool.path}
              title={tool.title}
              className="absolute inset-0 w-full h-full border-0"
              sandbox="allow-scripts allow-same-origin allow-forms allow-downloads allow-popups allow-modals allow-top-navigation-by-user-activation"
              onError={() => setBlocked(true)}
              onLoad={(e) => {
                // When a CDN/proxy injects X-Frame-Options:DENY the browser
                // renders a cross-origin error page (e.g. chrome-error://) inside
                // the frame. Accessing contentDocument from a cross-origin frame
                // throws a SecurityError, which we use to detect the block.
                try { void e.target.contentDocument; }
                catch { setBlocked(true); }
              }}
            />
          )}
        </div>

        {/* Footnote */}
        <footer className="bg-white border-t border-ink/10 shrink-0">
          <div className="max-w-[1400px] mx-auto px-4 sm:px-6 py-2 flex items-center gap-2 text-[11px] text-ink/40">
            <FileArchive className="w-3.5 h-3.5" />
            Preserved original — the full-featured standalone edition remains launchable and is never replaced or deleted.
            {!blocked && (
              <span className="ml-auto">
                Blocked?{" "}
                <button onClick={() => setBlocked(true)} className="underline hover:text-copper transition-colors">
                  Open full screen instead
                </button>
              </span>
            )}
          </div>
        </footer>
      </div>
    </AppShell>
  );
}
