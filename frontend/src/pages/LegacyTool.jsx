/**
 * LegacyTool — full-page wrapper for an ORIGINAL standalone HTML application.
 *
 * The originals are full-featured apps (some 100KB+ of hand-built HTML/JS/CSS)
 * that predate the React pages. They are preserved — never deleted — and this
 * wrapper serves them in-app with the platform shell: title bar, back link,
 * and an "Open full screen" escape hatch for the standalone experience.
 *
 * Usage: <LegacyTool slug="djedi-oracle" />
 */

import { Link, Navigate } from "react-router-dom";
import AppShell from "../components/AppShell";
import { ORIGINAL_BY_SLUG } from "../lib/originalTools";
import { ArrowLeft, ExternalLink, FileArchive } from "lucide-react";

export default function LegacyTool({ slug }) {
  const tool = ORIGINAL_BY_SLUG[slug];
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

        {/* The original app */}
        <div className="flex-1 relative" data-testid="legacy-tool-frame">
          <iframe
            src={tool.path}
            title={tool.title}
            className="absolute inset-0 w-full h-full border-0"
            sandbox="allow-scripts allow-same-origin allow-forms allow-downloads allow-popups"
          />
        </div>

        {/* Footnote */}
        <footer className="bg-white border-t border-ink/10 shrink-0">
          <div className="max-w-[1400px] mx-auto px-4 sm:px-6 py-2 flex items-center gap-2 text-[11px] text-ink/40">
            <FileArchive className="w-3.5 h-3.5" />
            Preserved original — the full-featured standalone edition remains launchable and is never replaced or deleted.
          </div>
        </footer>
      </div>
    </AppShell>
  );
}
