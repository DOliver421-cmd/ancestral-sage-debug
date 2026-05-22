import { useState } from "react";
import { X, Bug, CheckCircle, ArrowRight } from "lucide-react";

// ── Steps the tester follows — shown before the form ──────────────────────────
const STEPS = [
  { n: "1", label: "Sign up free", desc: "Click 'Create Account' — takes 60 seconds.", action: { label: "Sign Up Now", href: "/register" } },
  { n: "2", label: "Explore the platform", desc: "Try to sign in, browse courses, open M.O.R.E., click things." },
  { n: "3", label: "Come back here and report", desc: "Tell us what you tried and what happened. You get paid either way." },
];

export default function BugReportModal() {
  const [isOpen, setIsOpen]       = useState(false);
  const [step, setStep]           = useState("instructions"); // "instructions" | "form" | "done"
  const [loading, setLoading]     = useState(false);
  const [formData, setFormData]   = useState({
    name: "",
    email: "",
    venmoOrPaypal: "",
    whatYouTried: "",
    whatBroke: "",
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await fetch("/api/bug-report", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });
      if (res.ok) {
        setStep("done");
      } else {
        alert("Submission error — please try again or text Delon directly.");
      }
    } catch {
      alert("Connection error — please try again.");
    } finally {
      setLoading(false);
    }
  };

  const open = () => { setIsOpen(true); setStep("instructions"); };
  const close = () => setIsOpen(false);

  return (
    <>
      {/* ── Floating trigger button — always visible ─────────────────────────── */}
      <button
        onClick={open}
        className="fixed bottom-5 right-5 z-50 flex items-center gap-2 bg-ink text-white font-bold text-sm px-4 py-3 rounded-full shadow-2xl hover:bg-copper hover:scale-105 transition-all border-2 border-copper/50"
        title="Bug Bounty — Get $1"
      >
        <Bug className="w-4 h-4" />
        <span>🐛 Report Bug — Get $1</span>
      </button>

      {/* ── Modal ────────────────────────────────────────────────────────────── */}
      {isOpen && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4 backdrop-blur-sm" onClick={(e) => e.target === e.currentTarget && close()}>
          <div className="bg-white w-full max-w-md shadow-2xl rounded-2xl overflow-hidden">

            {/* Header */}
            <div className="bg-gradient-to-r from-ink to-copper/80 px-6 py-5 text-white flex items-center justify-between">
              <div>
                <div className="font-heading font-extrabold text-xl flex items-center gap-2">
                  <Bug className="w-5 h-5" /> Bug Bounty
                </div>
                <p className="text-white/70 text-xs mt-0.5">$1 for trying · $1 + free membership for finding a bug</p>
              </div>
              <button onClick={close} className="text-white/60 hover:text-white transition-colors">
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* ── Step: Instructions ──────────────────────────────────────────── */}
            {step === "instructions" && (
              <div className="p-6">
                <p className="text-sm text-ink/70 leading-relaxed mb-6">
                  You're a <span className="font-bold text-ink">Beta Tester</span>. Your job: break things and tell us what happened. Here's the flow:
                </p>

                <div className="space-y-4 mb-6">
                  {STEPS.map(({ n, label, desc, action }) => (
                    <div key={n} className="flex gap-4 items-start">
                      <div className="w-8 h-8 rounded-full bg-copper text-white font-black flex items-center justify-center shrink-0 text-sm">{n}</div>
                      <div className="flex-1">
                        <div className="font-bold text-sm">{label}</div>
                        <p className="text-xs text-ink/60 mt-0.5 leading-relaxed">{desc}</p>
                        {action && (
                          <a href={action.href} className="inline-flex items-center gap-1 text-xs font-bold text-copper hover:text-copper/80 mt-1 transition-colors">
                            {action.label} <ArrowRight className="w-3 h-3" />
                          </a>
                        )}
                      </div>
                    </div>
                  ))}
                </div>

                <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 mb-5 text-sm text-amber-800">
                  <strong>Already explored?</strong> Click below to fill out your report and get paid.
                </div>

                <div className="flex gap-3">
                  <button
                    onClick={() => setStep("form")}
                    className="flex-1 bg-copper hover:bg-copper/90 text-white font-bold py-3 rounded-xl transition-colors"
                  >
                    I'm ready — Report a Bug
                  </button>
                  <a href="/register" className="flex-1 border-2 border-ink text-ink font-bold py-3 rounded-xl hover:bg-ink/5 transition-colors text-center text-sm flex items-center justify-center">
                    Sign Up First
                  </a>
                </div>
              </div>
            )}

            {/* ── Step: Form ─────────────────────────────────────────────────── */}
            {step === "form" && (
              <form onSubmit={handleSubmit} className="p-6 space-y-4">
                <button type="button" onClick={() => setStep("instructions")} className="text-xs text-ink/40 hover:text-ink mb-1 transition-colors">
                  ← Back to instructions
                </button>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-bold mb-1 text-ink/70">Your Name</label>
                    <input name="name" value={formData.name} onChange={handleChange} required
                      className="w-full px-3 py-2 border border-ink/20 rounded-lg text-sm bg-white focus:outline-none focus:border-copper"
                      placeholder="First name" />
                  </div>
                  <div>
                    <label className="block text-xs font-bold mb-1 text-ink/70">Email</label>
                    <input name="email" type="email" value={formData.email} onChange={handleChange} required
                      className="w-full px-3 py-2 border border-ink/20 rounded-lg text-sm bg-white focus:outline-none focus:border-copper"
                      placeholder="you@email.com" />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-bold mb-1 text-ink/70">Venmo or PayPal (to send your $1)</label>
                  <input name="venmoOrPaypal" value={formData.venmoOrPaypal} onChange={handleChange} required
                    className="w-full px-3 py-2 border border-ink/20 rounded-lg text-sm bg-white focus:outline-none focus:border-copper"
                    placeholder="@venmo-handle or paypal@email.com" />
                </div>

                <div>
                  <label className="block text-xs font-bold mb-1 text-ink/70">What did you try to do?</label>
                  <select name="whatYouTried" value={formData.whatYouTried} onChange={handleChange} required
                    className="w-full px-3 py-2 border border-ink/20 rounded-lg text-sm bg-white focus:outline-none focus:border-copper">
                    <option value="">Choose one...</option>
                    <option value="signup">Sign up for an account</option>
                    <option value="login">Log in</option>
                    <option value="browse-more">Browse M.O.R.E. Help Center</option>
                    <option value="post-more">Post in M.O.R.E.</option>
                    <option value="courses">Browse or access courses</option>
                    <option value="subscribe">Try to subscribe</option>
                    <option value="payment">Add payment method</option>
                    <option value="profile">View profile / settings</option>
                    <option value="just-browsed">Just browsed around</option>
                    <option value="other">Something else</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-bold mb-1 text-ink/70">What happened? (bug, error, or "nothing broke")</label>
                  <textarea name="whatBroke" value={formData.whatBroke} onChange={handleChange} required
                    className="w-full px-3 py-2 border border-ink/20 rounded-lg text-sm bg-white focus:outline-none focus:border-copper h-20 resize-none"
                    placeholder="Describe what you saw — error messages, blank screens, things that felt off, or just 'looked fine to me'" />
                </div>

                <button type="submit" disabled={loading}
                  className="w-full bg-ink hover:bg-ink/80 text-white font-bold py-3 rounded-xl transition-colors disabled:opacity-50">
                  {loading ? "Sending..." : "Submit — I'm Done Testing"}
                </button>

                <p className="text-xs text-ink/40 text-center">
                  You get <strong>$1</strong> just for trying. Finding a real bug = <strong>$1 + free BASIC membership</strong>.
                </p>
              </form>
            )}

            {/* ── Step: Done ─────────────────────────────────────────────────── */}
            {step === "done" && (
              <div className="p-8 text-center">
                <CheckCircle className="w-14 h-14 text-emerald-500 mx-auto mb-4" />
                <h3 className="font-heading font-extrabold text-2xl mb-2">You're a tester. 🙏</h3>
                <p className="text-ink/60 text-sm leading-relaxed mb-4">
                  Report received. Delon will send your <strong>$1</strong> within 24 hours.
                  If you found a bug, you'll also get a <strong>free BASIC membership</strong> — automatically.
                </p>
                <p className="text-xs text-ink/40">
                  Questions? Text or DM @namoshun. You're part of the community now.
                </p>
                <button onClick={close} className="mt-6 text-sm font-bold text-ink/50 hover:text-ink transition-colors">
                  Close
                </button>
              </div>
            )}

          </div>
        </div>
      )}
    </>
  );
}
