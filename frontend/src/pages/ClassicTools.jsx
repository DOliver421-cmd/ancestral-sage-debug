/**
 * ClassicTools — the hub for the ORIGINAL standalone HTML applications.
 *
 * Every full-featured original (the Creator's Sanctuary suite, the original
 * M.O.R.E. Help Center, the Supervisor, the Sovereign, the litigation weapons,
 * the original helper, the Ancestral Sage) is preserved and served by the
 * build. This page launches them in-app or full-screen. Nothing original has
 * been abandoned — the React pages are the modern front-ends; the originals
 * stay launchable here.
 */

import { Link } from "react-router-dom";
import AppShell from "../components/AppShell";
import { ORIGINAL_TOOLS, ORIGINAL_SUITES } from "../lib/originalTools";
import { ExternalLink, Archive, ArrowRight } from "lucide-react";

const GREEN = "#1B4332";
const GOLD = "#E8A51E";
const COPPER = "#C0572D";
const BONE = "#FDFBF5";

export default function ClassicTools() {
  return (
    <AppShell>
      <div style={{ background: BONE, minHeight: "100vh" }}>
        {/* Header */}
        <div style={{ background: `linear-gradient(135deg, ${GREEN}, #2D6A4F)`, padding: "36px 32px 28px", color: "#fff" }}>
          <div className="flex items-center gap-3 flex-wrap">
            <Archive className="w-7 h-7" style={{ color: GOLD }} />
            <h1 className="font-heading text-2xl font-bold tracking-tight">Classic Tools — the originals</h1>
            <span className="ml-1 text-[10px] font-black uppercase tracking-widest px-2 py-1 rounded" style={{ background: GOLD, color: "#0a0a0a" }}>
              {ORIGINAL_TOOLS.length} preserved
            </span>
          </div>
          <p className="text-white/80 text-sm mt-2 max-w-3xl">
            These are the full-featured standalone applications the site shipped before the React pages —
            the hand-built originals with the complete user experience. They are <b>preserved, never deleted</b>,
            and launchable here or full-screen. If a modern page ever feels thin, the original is one click away.
          </p>
        </div>

        <div className="max-w-5xl mx-auto px-6 py-8 space-y-10">
          {ORIGINAL_SUITES.map(([suite, tools]) => (
            <section key={suite}>
              <h2 className="font-heading text-lg font-bold text-ink flex items-center gap-2">
                <span className="text-[10px] font-black uppercase tracking-widest px-2 py-1 rounded" style={{ background: "rgba(232,165,30,0.15)", color: "#8a6400" }}>
                  {suite}
                </span>
              </h2>
              <div className="grid sm:grid-cols-2 gap-4 mt-3">
                {tools.map((t) => (
                  <div key={t.slug} className="card-flat rounded-2xl p-5 border flex flex-col" style={{ background: "#fff", borderColor: "#eee7d8" }}>
                    <div className="flex items-start justify-between gap-2">
                      <span style={{ fontSize: 30 }}>{t.icon}</span>
                      <span className="text-[9px] font-black uppercase tracking-widest px-2 py-0.5 rounded" style={{ background: "rgba(27,67,50,0.1)", color: GREEN }}>
                        Original
                      </span>
                    </div>
                    <div className="font-heading font-bold text-ink mt-3">{t.title}</div>
                    <p className="text-xs text-ink/60 mt-1.5 leading-snug flex-1">{t.desc}</p>
                    <div className="flex items-center gap-2 mt-4">
                      <Link to={`/classic/${t.slug}`}
                        className="flex-1 inline-flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg text-xs font-black text-white no-underline"
                        style={{ background: GREEN }}>
                        Launch in-app <ArrowRight className="w-3.5 h-3.5" />
                      </Link>
                      <a href={t.path} target="_blank" rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 px-3 py-2 rounded-lg text-xs font-bold border no-underline"
                        style={{ borderColor: "#ddd3bf", color: COPPER }}>
                        <ExternalLink className="w-3.5 h-3.5" /> Full screen
                      </a>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          ))}

          <p className="text-[11px] text-ink/40 max-w-3xl leading-relaxed">
            Inventory: see <code>frontend/src/lib/originalTools.js</code> and <code>docs/ORIGINAL_TOOLS.md</code>.
            Every file ships in the frontend build from <code>/tools/*</code> and <code>/originals/*</code> — the
            originals are part of the platform, not an afterthought.
          </p>
        </div>
      </div>
    </AppShell>
  );
}
