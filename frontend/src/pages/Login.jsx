import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "../lib/auth";
import { WAI_LOGO, BRAND } from "../lib/brand";
import { toast } from "sonner";
import { ArrowRight, Heart, ExternalLink } from "lucide-react";
import { isWaiDoor, MORE_HOME } from "../lib/domain";

export default function Login() {
  const waiDoor = isWaiDoor();
  const { login } = useAuth();
  const nav = useNavigate();
  const [params] = useSearchParams();
  const returnTo = params.get("returnTo");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const u = await login(email, password);
      toast.success(`Welcome back, ${u.full_name}`);
      if (u.must_change_password) {
        toast.info("Please change your temporary password before continuing.");
        nav("/settings?force=1");
        return;
      }
      // Honor a returnTo destination (e.g. persona pages), otherwise land on
      // the landing page — they choose where to go from there.
      nav(returnTo && returnTo.startsWith("/") ? returnTo : "/");
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Login failed");
    } finally { setLoading(false); }
  };

  return (
    <div className="min-h-screen bg-bone grid lg:grid-cols-2">
      {/* Left: Brand & Message */}
      <div className="hidden lg:flex flex-col justify-between p-12 bg-ink text-white relative overflow-hidden">
        <div className="absolute inset-0 grid-paper opacity-10 pointer-events-none" />
        <div className="relative">
          <Link to="/" className="flex items-center gap-3 inline-block" data-testid="login-brand">
            <img src={WAI_LOGO} alt="M.O.R.E." className="w-12 h-12 object-contain bg-white p-1 rounded" />
            <div>
              <div className="overline text-copper leading-none">{BRAND.short}</div>
              <div className="font-heading font-bold text-sm">{BRAND.name}</div>
            </div>
          </Link>
        </div>

        <div className="relative">
          <div className="overline text-copper mb-4">Welcome back</div>
          <h1 className="font-heading text-5xl font-extrabold leading-tight mb-6">
            Your community<br />is waiting for you.
          </h1>
          <p className="text-lg text-white/80 max-w-md leading-relaxed">
            Create. Heal. Earn with dignity. Continue your journey with a platform built for you, not against you.
          </p>
        </div>

        <div className="relative">
          <p className="text-xs text-white/50 italic">
            "{BRAND.mission}"
          </p>
        </div>
      </div>

      {/* Right: Login Form */}
      <div className="flex flex-col items-center justify-center p-8 bg-bone">
        <div className="w-full max-w-sm">
          {/* Mobile Header */}
          <div className="lg:hidden mb-8 text-center">
            <Link to="/" className="inline-flex items-center gap-3 mb-6" data-testid="login-brand-mobile">
              <img src={WAI_LOGO} alt="M.O.R.E." className="w-10 h-10 object-contain" />
              <div>
                <div className="overline text-copper leading-none text-xs">{BRAND.short}</div>
                <div className="font-heading font-bold text-sm">{BRAND.name}</div>
              </div>
            </Link>
          </div>

          <form onSubmit={submit} className="space-y-6" data-testid="login-form">
            {/* Heading */}
            <div className="text-center mb-8">
              <h2 className="font-heading text-3xl font-bold mb-2">Sign in</h2>
              <p className="text-ink/60 text-sm">Creators, artists, and community members</p>
            </div>

            {/* Email */}
            <div>
              <label className="block overline text-ink/60 mb-3">Email</label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
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
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full px-4 py-3 bg-white border border-ink/20 rounded focus:border-copper focus:outline-none focus:ring-2 focus:ring-copper/30 transition-all"
                data-testid="input-password"
              />
            </div>

            {/* Forgot Password — account recovery is self-service on the M.O.R.E. door */}
            <div className="text-right">
              {waiDoor ? (
                <a
                  href={`${MORE_HOME}/forgot-password`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-sm text-copper hover:text-copper/80 font-medium"
                >
                  Forgot password? <ExternalLink className="w-3 h-3" />
                </a>
              ) : (
                <Link to="/forgot-password" className="text-sm text-copper hover:text-copper/80 font-medium">
                  Forgot password?
                </Link>
              )}
            </div>

            {/* Submit */}
            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 px-4 bg-copper text-white font-bold uppercase tracking-widest hover:bg-copper/90 disabled:bg-copper/50 transition-colors rounded flex items-center justify-center gap-2"
              data-testid="btn-submit"
            >
              {loading ? "Signing in…" : (
                <>
                  Sign In <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>

            {/* Divider */}
            <div className="relative my-8">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-ink/10"></div>
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-bone text-ink/50">New here?</span>
              </div>
            </div>

            {/* Sign Up — account creation is for everyone; creator is a tier you
                select inside the community, not the registration path itself. */}
            <Link
              to="/register"
              className="w-full py-3 px-4 border-2 border-copper text-copper font-bold uppercase tracking-widest hover:bg-copper hover:text-white transition-colors rounded flex items-center justify-center gap-2"
              data-testid="btn-register"
            >
              <Heart className="w-4 h-4" />
              Create Account
            </Link>
          </form>

          {/* Footer Link — support lives on the M.O.R.E. Help Center */}
          <div className="mt-8 text-center">
            <p className="text-xs text-ink/50">
<<<<<<< HEAD
              Need help? <Link to="/more-help-center" className="text-copper hover:text-copper/80 font-medium">MORE Help Center</Link>
=======
              Need help?{" "}
              {waiDoor ? (
                <a href={`${MORE_HOME}/help-center`} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 text-copper hover:text-copper/80 font-medium">
                  Help Center <ExternalLink className="w-3 h-3" />
                </a>
              ) : (
                <Link to="/help-center" className="text-copper hover:text-copper/80 font-medium">Help Center</Link>
              )}
>>>>>>> b5e17a90a093ef2f7a081efc8d479b5b9f58558e
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
