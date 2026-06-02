import { useState } from "react";
import { Link } from "react-router-dom";
import AppShell from "../components/AppShell";
import { WAI_LOGO, BRAND } from "../lib/brand";
import { Scale, ArrowLeft, ExternalLink, Shield, AlertTriangle, HandHelping, HelpCircle } from "lucide-react";

export default function LitigationWeapon() {
  const [agreed, setAgreed] = useState(false);

  return (
    <AppShell>
    <div className="min-h-screen flex flex-col bg-bone">
      {/* Public top bar */}
      <header className="border-b border-ink/10 bg-bone shrink-0">
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between gap-4">
          <Link to="/" className="flex items-center gap-3">
            <img src={WAI_LOGO} alt="W.A.I." className="w-9 h-9 object-contain" style={{ mixBlendMode: "multiply" }} />
            <div className="hidden sm:block">
              <div className="overline text-copper text-xs leading-none">{BRAND.short}</div>
              <div className="font-heading font-bold text-xs leading-tight">{BRAND.name}</div>
            </div>
          </Link>

          <div className="flex items-center gap-2 font-heading font-bold">
            <Scale className="w-5 h-5 text-signal" />
            Legal Help Tool
          </div>

          <nav className="flex items-center gap-3">
            <Link to="/more" className="flex items-center gap-1.5 text-sm font-medium hover:text-copper">
              <HandHelping className="w-4 h-4" /><span className="hidden sm:inline">M.O.R.E.</span>
            </Link>
            <Link to="/helper" className="flex items-center gap-1.5 text-sm font-medium hover:text-copper">
              <HelpCircle className="w-4 h-4" /><span className="hidden sm:inline">Help Center</span>
            </Link>
            <Link to="/register" className="btn-copper text-sm">Join Free</Link>
          </nav>
        </div>
      </header>

      {!agreed ? (
        <div className="flex-1 flex items-center justify-center p-8">
          <div className="max-w-lg w-full space-y-6">
            <div className="flex items-start gap-4 bg-amber-50 border border-amber-200 p-5">
              <AlertTriangle className="w-6 h-6 text-amber-600 shrink-0 mt-0.5" />
              <div>
                <h2 className="font-heading font-bold text-amber-900 mb-2">Before You Continue</h2>
                <ul className="text-sm text-amber-800 space-y-2 leading-relaxed">
                  <li>• This is an educational tool, not legal advice.</li>
                  <li>• Always consult a licensed attorney for your specific situation.</li>
                  <li>• Content is for informational and self-advocacy purposes only.</li>
                  <li>• Your data stays on your device — nothing is sent to our servers.</li>
                </ul>
              </div>
            </div>

            <div className="bg-ink text-white p-5">
              <div className="flex items-start gap-3">
                <Shield className="w-5 h-5 text-signal shrink-0 mt-0.5" />
                <div>
                  <div className="font-heading font-bold mb-1">Know Your Rights</div>
                  <p className="text-white/70 text-sm leading-relaxed">
                    This tool helps you understand federal discrimination law, build evidence checklists,
                    calculate damages, and generate document templates for EEOC, MSPB, and federal court filings.
                  </p>
                </div>
              </div>
            </div>

            <div className="flex gap-3">
              <Link to="/more" className="btn-ghost text-sm flex items-center gap-2 flex-1 justify-center">
                <ArrowLeft className="w-4 h-4" /> Back to M.O.R.E.
              </Link>
              <button onClick={() => setAgreed(true)}
                className="btn-copper text-sm font-bold flex-1">
                I Understand — Open Tool
              </button>
            </div>

            <div className="text-center">
              <a href="/tools/litigation-weapon.html" target="_blank" rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 text-xs text-ink/40 hover:text-copper transition-colors">
                <ExternalLink className="w-3 h-3" /> Open full screen (offline-friendly)
              </a>
            </div>
          </div>
        </div>
      ) : (
        <iframe
          src="/tools/litigation-weapon.html"
          title="Universal Litigation Weapon"
          className="flex-1 w-full border-0"
          sandbox="allow-scripts allow-same-origin allow-forms allow-downloads"
        />
      )}
    </div>
    </AppShell>
  );
}
