import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import BackButton from "../components/BackButton";
import { useAuth } from "../lib/auth";
import { api } from "../lib/api";
import { CheckSquare, Square, CheckCircle } from "lucide-react";

export default function TermsOfService() {
  const { user } = useAuth();
  const nav = useNavigate();
  const [accepted, setAccepted] = useState(() => {
    try { return !!localStorage.getItem("terms_accepted_v1"); } catch { return false; }
  });
  const [checked, setChecked] = useState(false);
  const [saving, setSaving] = useState(false);
  const [done, setDone] = useState(accepted);

  const handleAccept = async () => {
    if (!checked) return;
    setSaving(true);
    try {
      if (user) {
        await api.post("/users/accept-terms", { version: "v1", timestamp: new Date().toISOString() }).catch(() => {});
      }
      localStorage.setItem("terms_accepted_v1", new Date().toISOString());
      setDone(true);
      setAccepted(true);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="min-h-screen bg-bone">
      <nav className="bg-ink text-white px-6 py-4 flex items-center gap-4">
        <BackButton fallback="/" />
        <span className="font-heading font-bold text-lg">Terms of Service</span>
        {done && (
          <span className="ml-auto flex items-center gap-2 text-sm text-signal font-semibold">
            <CheckCircle className="w-4 h-4" /> Terms Accepted
          </span>
        )}
      </nav>

      <div className="max-w-3xl mx-auto px-6 py-12">
        <div className="prose prose-ink max-w-none">
          <h1>Terms of Service</h1>
          <p className="text-sm text-ink/60">Last updated: May 2026</p>

          <h2>1. Acceptance</h2>
          <p>By creating an account, you agree to these terms. If you do not agree, do not use the platform.</p>

          <h2>2. Account</h2>
          <p>You are responsible for keeping your password secure. You must be at least 13 years old. One account per person.</p>

          <h2>3. Acceptable Use</h2>
          <p>You agree not to: (a) use the platform for any illegal purpose; (b) attempt to bypass security or rate limits; (c) harass other users; (d) submit false or misleading information.</p>

          <h2>4. Content</h2>
          <p>Course content is provided for educational purposes. Lab submissions and portfolio content remain your intellectual property. You grant us a license to display your public portfolio.</p>

          <h2>5. Termination</h2>
          <p>We may suspend accounts that violate these terms. You may delete your account at any time via Account Settings.</p>

          <h2>6. Disclaimer</h2>
          <p>The platform is provided "as is" without warranty. We are not liable for any damages arising from use of the platform.</p>

          <h2>7. Changes</h2>
          <p>We may update these terms. Continued use after changes constitutes acceptance. We will notify registered users of material changes.</p>

          <h2>8. Contact</h2>
          <p>Questions? Visit our <Link to="/help-center" className="text-copper hover:underline">Help Center</Link>.</p>
        </div>

        {/* Acceptance block */}
        <div className="mt-10 p-6 border-2 border-copper/30 bg-white rounded-lg">
          {done ? (
            <div className="flex items-center gap-3 text-signal font-semibold">
              <CheckCircle className="w-6 h-6" />
              <div>
                <div className="text-lg">You have accepted these terms.</div>
                <div className="text-sm text-ink/50 font-normal mt-0.5">
                  Accepted on {new Date(localStorage.getItem("terms_accepted_v1") || Date.now()).toLocaleDateString()}
                </div>
              </div>
            </div>
          ) : (
            <>
              <button
                onClick={() => setChecked(v => !v)}
                className="flex items-start gap-3 text-left w-full mb-5 group"
              >
                {checked
                  ? <CheckSquare className="w-5 h-5 text-copper shrink-0 mt-0.5" />
                  : <Square className="w-5 h-5 text-ink/40 shrink-0 mt-0.5" />}
                <span className="text-sm text-ink/80 leading-relaxed">
                  I have read and agree to the WAI Institute Terms of Service. I understand that my use of the platform constitutes acceptance of these terms.
                </span>
              </button>
              <button
                onClick={handleAccept}
                disabled={!checked || saving}
                className="btn-primary w-full py-3 text-sm font-bold uppercase tracking-widest disabled:opacity-40 disabled:cursor-not-allowed"
              >
                {saving ? "Saving..." : "Accept Terms & Continue"}
              </button>
              {!user && (
                <p className="text-xs text-ink/40 mt-3 text-center">
                  <Link to="/login" className="text-copper hover:underline">Sign in</Link> to permanently save your acceptance to your account.
                </p>
              )}
            </>
          )}
        </div>

        <div className="mt-6 flex gap-4 justify-center">
          <Link to="/privacy" className="text-sm text-copper hover:underline">Privacy Policy</Link>
          <Link to="/help-center" className="text-sm text-copper hover:underline">Help Center</Link>
          {done && (
            <button onClick={() => nav(-1)} className="text-sm text-copper hover:underline">← Go Back</button>
          )}
        </div>
      </div>
    </div>
  );
}
