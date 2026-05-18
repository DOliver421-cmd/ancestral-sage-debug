import { useState } from "react";
import { Link } from "react-router-dom";
import AppShell from "../components/AppShell";
import { Scale, ArrowLeft, ExternalLink, Shield, AlertTriangle } from "lucide-react";

export default function LitigationWeapon() {
  const [agreed, setAgreed] = useState(false);

  return (
    <AppShell>
      <div className="flex flex-col h-screen">
        {/* Header */}
        <div className="border-b border-ink/10 bg-bone px-6 py-4 flex items-center gap-4 shrink-0">
          <Link to="/more" className="text-ink/50 hover:text-ink transition-colors">
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <Scale className="w-6 h-6 text-signal shrink-0" />
          <div className="flex-1">
            <h1 className="font-heading font-bold">Universal Litigation Weapon</h1>
            <p className="text-xs text-ink/50">Hypothetical legal self-help tool · For educational purposes</p>
          </div>
          <a
            href="/tools/litigation-weapon.html"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 text-xs text-ink/50 hover:text-copper transition-colors"
          >
            <ExternalLink className="w-3.5 h-3.5" />
            Open Full Screen
          </a>
        </div>

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
                      It was built to empower — not replace — professional legal counsel.
                    </p>
                  </div>
                </div>
              </div>
              <button
                onClick={() => setAgreed(true)}
                className="btn-copper w-full text-sm font-bold uppercase tracking-widest"
              >
                I Understand — Open the Tool
              </button>
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
