import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../lib/auth";
import { WAI_LOGO, BRAND } from "../lib/brand";
import { toast } from "sonner";
import { ArrowRight, Heart, CheckCircle } from "lucide-react";

export default function Register() {
  const { register } = useAuth();
  const nav = useNavigate();
  const [form, setForm] = useState({ full_name: "", email: "", password: "", associate: "Associate-Alpha", agreed_terms: false, over_13: false });
  const [loading, setLoading] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    if (!form.agreed_terms) { toast.error("You must agree to the Terms of Service and Privacy Policy."); setLoading(false); return; }
    if (!form.over_13) { toast.error("You must be at least 13 years old to create an account."); setLoading(false); return; }
    setLoading(true);
    try {
      const u = await register(form);
      toast.success(`Welcome, ${u.full_name}!`);
      nav("/dashboard");
    } catch (err) {
      const status = err?.response?.status;
      if (status >= 500) {
        // api.js interceptor already fired "Server error" toast for 5xx — stay silent here.
      } else if (!status) {
        // Network error (no response at all) — api.js interceptor did NOT fire.
        toast.error("Can't reach the server — wait 60 seconds and try again.");
      } else {
        toast.error(err?.response?.data?.detail || "Registration failed");
      }
    } finally { setLoading(false); }
  };

  return (
    <div className="min-h-screen bg-bone">
      {/* Top Navigation */}
      <header className="border-b border-ink/10 bg-bone">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-3">
            <img src={WAI_LOGO} alt="W.A.I." className="w-10 h-10 object-contain" style={{ mixBlendMode: "multiply" }} />
            <div>
              <div className="overline text-copper leading-none text-xs">{BRAND.short}</div>
              <div className="font-heading font-bold text-sm">{BRAND.name}</div>
            </div>
          </Link>
          <div className="flex items-center gap-4">
            <span className="text-sm text-ink/60">Already joined?</span>
            <Link to="/login" className="text-sm font-bold uppercase tracking-widest text-copper hover:text-copper/80">
              Sign In
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="bg-gradient-to-b from-copper/10 to-bone border-b border-copper/20 py-16">
        <div className="max-w-3xl mx-auto px-6 text-center">
          <h1 className="font-heading text-5xl font-bold mb-4">
            Join the Community
          </h1>
          <p className="text-xl text-ink/60 mb-8">
            Creator. Learner. Healer. Artist. Community member. Whatever brings you here — this is for you.
          </p>
          <div className="grid md:grid-cols-3 gap-4 max-w-2xl mx-auto">
            <div className="flex items-start gap-3">
              <CheckCircle className="w-5 h-5 text-copper flex-shrink-0 mt-0.5" />
              <div className="text-sm">
                <div className="font-bold">You keep 70%</div>
                <div className="text-ink/60">If you're creating</div>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <CheckCircle className="w-5 h-5 text-copper flex-shrink-0 mt-0.5" />
              <div className="text-sm">
                <div className="font-bold">Free Access</div>
                <div className="text-ink/60">To learning & community</div>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <CheckCircle className="w-5 h-5 text-copper flex-shrink-0 mt-0.5" />
              <div className="text-sm">
                <div className="font-bold">No Extraction</div>
                <div className="text-ink/60">Built with you, not off you</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Registration Form */}
      <section className="py-16">
        <div className="max-w-md mx-auto px-6">
          <form onSubmit={submit} className="space-y-6" data-testid="register-form">
            <div>
              <div className="overline text-copper mb-2">Create Your Account</div>
              <h2 className="font-heading text-2xl font-bold">Tell us about yourself</h2>
            </div>

            {/* Full Name */}
            <div>
              <label className="block overline text-ink/60 mb-3">Full Name</label>
              <input
                type="text"
                required
                value={form.full_name}
                onChange={(e) => setForm({ ...form, full_name: e.target.value })}
                placeholder="Your name"
                className="w-full px-4 py-3 bg-white border border-ink/20 rounded focus:border-copper focus:outline-none focus:ring-2 focus:ring-copper/30 transition-all"
                data-testid="input-name"
              />
            </div>

            {/* Email */}
            <div>
              <label className="block overline text-ink/60 mb-3">Email</label>
              <input
                type="email"
                required
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                placeholder="you@example.com"
                className="w-full px-4 py-3 bg-white border border-ink/20 rounded focus:border-copper focus:outline-none focus:ring-2 focus:ring-copper/30 transition-all"
                data-testid="input-email"
              />
            </div>

            {/* Password */}
            <div>
              <label className="block overline text-ink/60 mb-3">Password</label>
              <input
                type="password"
                required
                minLength={8}
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
                placeholder="At least 8 characters"
                className="w-full px-4 py-3 bg-white border border-ink/20 rounded focus:border-copper focus:outline-none focus:ring-2 focus:ring-copper/30 transition-all"
                data-testid="input-password"
              />
              <p className="text-xs text-ink/50 mt-2">Use a strong password to protect your account</p>
            </div>

            {/* Hidden: Associate field (keep for compatibility) */}
            <input
              type="hidden"
              value={form.associate}
              onChange={(e) => setForm({ ...form, associate: e.target.value })}
              data-testid="input-associate"
            />

            {/* Legal Checkboxes */}
            <div className="space-y-3">
              <label className="flex items-start gap-3 cursor-pointer group">
                <input
                  type="checkbox"
                  checked={form.agreed_terms}
                  onChange={(e) => setForm({ ...form, agreed_terms: e.target.checked })}
                  className="mt-0.5 w-4 h-4 rounded border-ink/30 text-copper focus:ring-copper/30"
                  data-testid="checkbox-terms"
                />
                <span className="text-sm text-ink/70 group-hover:text-ink transition-colors">
                  I agree to the <Link to="/terms" className="text-copper hover:underline">Terms of Service</Link> and <Link to="/privacy" className="text-copper hover:underline">Privacy Policy</Link>
                </span>
              </label>
              <label className="flex items-start gap-3 cursor-pointer group">
                <input
                  type="checkbox"
                  checked={form.over_13}
                  onChange={(e) => setForm({ ...form, over_13: e.target.checked })}
                  className="mt-0.5 w-4 h-4 rounded border-ink/30 text-copper focus:ring-copper/30"
                  data-testid="checkbox-age"
                />
                <span className="text-sm text-ink/70 group-hover:text-ink transition-colors">
                  I confirm that I am at least 13 years old
                </span>
              </label>
            </div>

            {/* Submit */}
            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 px-4 bg-copper text-white font-bold uppercase tracking-widest hover:bg-copper/90 disabled:bg-copper/50 transition-colors rounded flex items-center justify-center gap-2"
              data-testid="btn-submit"
            >
              {loading ? "Creating account…" : (
                <>
                  Join Us <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>

            {/* Divider */}
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-ink/10"></div>
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-bone text-ink/50">Already have an account?</span>
              </div>
            </div>

            {/* Sign In Link */}
            <Link
              to="/login"
              className="w-full py-3 px-4 border-2 border-copper text-copper font-bold uppercase tracking-widest hover:bg-copper hover:text-white transition-colors rounded flex items-center justify-center gap-2"
              data-testid="link-login"
            >
              Sign In
            </Link>
          </form>

          {/* Support */}
          <div className="mt-8 text-center text-xs text-ink/50">
            Questions? <Link to="/help-center" className="text-copper hover:text-copper/80 font-medium">Help Center</Link>
          </div>
        </div>
      </section>

      {/* Trust Section */}
      <section className="bg-ink text-white py-16 border-t border-copper/20">
        <div className="max-w-3xl mx-auto px-6 text-center">
          <h3 className="font-heading text-2xl font-bold mb-6">You're Safe Here</h3>
          <div className="grid md:grid-cols-3 gap-8">
            <div>
              <div className="text-3xl mb-3">🔒</div>
              <h4 className="font-bold mb-2">Your Privacy</h4>
              <p className="text-sm text-white/60">
                We don't sell your data. We don't track you. Your information is yours.
              </p>
            </div>
            <div>
              <div className="text-3xl mb-3">💪</div>
              <h4 className="font-bold mb-2">Your Control</h4>
              <p className="text-sm text-white/60">
                You decide what you share. You can delete your account anytime.
              </p>
            </div>
            <div>
              <div className="text-3xl mb-3">❤️</div>
              <h4 className="font-bold mb-2">Community Care</h4>
              <p className="text-sm text-white/60">
                This platform is built by people who care. We're not here to exploit you.
              </p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
