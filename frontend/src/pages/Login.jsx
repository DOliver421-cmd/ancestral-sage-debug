import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../lib/auth";
import { WAI_LOGO, BRAND } from "../lib/brand";
import { toast } from "sonner";

export default function Login() {
  const { login } = useAuth();
  const nav = useNavigate();
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
      nav(u.role === "executive_admin" || u.role === "admin" ? "/admin"
        : u.role === "instructor" ? "/instructor"
        : "/dashboard");
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Login failed");
    } finally { setLoading(false); }
  };

  const quickFill = (e, p) => { setEmail(e); setPassword(p); };

  return (
    <div className="min-h-screen bg-bone grid lg:grid-cols-2">
      <div className="hidden lg:block bg-ink relative overflow-hidden">
        <div className="absolute inset-0 grid-paper opacity-10" />
        <div className="relative h-full flex flex-col justify-between p-12 text-white">
          <Link to="/" className="flex items-center gap-3" data-testid="login-brand">
            <img src={WAI_LOGO} alt="W.A.I." className="w-12 h-12 object-contain bg-white p-1" />
            <div>
              <div className="overline text-signal">{BRAND.short}</div>
              <div className="font-heading font-bold">{BRAND.name}</div>
            </div>
          </Link>
          <div>
            <div className="overline text-copper">Welcome back</div>
            <h1 className="font-heading text-5xl font-extrabold mt-4 leading-tight">Sign in to the shop floor.</h1>
            <p className="mt-6 text-white/70 max-w-md">Your curriculum, progress, and certificates are ready. Pick up where you left off.</p>
          </div>
          <div className="text-xs text-white/50 italic">"The Lord will guide you always." — Isaiah 58:11</div>
        </div>
      </div>

      <div className="flex items-center justify-center p-8">
        <form onSubmit={submit} className="w-full max-w-md" data-testid="login-form">
          <div className="overline text-copper">Sign In</div>
          <h2 className="font-heading text-3xl font-bold mt-2">Welcome back.</h2>
          <p className="text-ink/60 text-sm mt-2">Apprentices, instructors, and admins.</p>

          <div className="mt-8 space-y-4">
            <div>
              <label className="overline text-ink/60">Email</label>
              <input type="email" required value={email} onChange={(e) => setEmail(e.target.value)}
                className="w-full mt-2 px-4 py-3 bg-white border border-ink/20 focus:border-ink focus:outline-none focus:ring-2 focus:ring-signal"
                data-testid="input-email" />
            </div>
            <div>
              <label className="overline text-ink/60">Password</label>
              <input type="password" required value={password} onChange={(e) => setPassword(e.target.value)}
                className="w-full mt-2 px-4 py-3 bg-white border border-ink/20 focus:border-ink focus:outline-none focus:ring-2 focus:ring-signal"
                data-testid="input-password" />
            </div>
          </div>

          <button type="submit" disabled={loading} className="btn-primary w-full mt-6" data-testid="btn-submit">
            {loading ? "Signing in…" : "Sign In"}
          </button>

          <div className="mt-6 p-4 bg-white border border-ink/10">
            <div className="overline text-ink/50 mb-2">Demo accounts</div>
            <div className="space-y-1.5 text-xs">
              <button type="button" onClick={() => quickFill("student@lcewai.org", "Learn@LCE2026")}
                className="w-full text-left font-mono hover:text-copper" data-testid="demo-student">
                student@lcewai.org / Learn@LCE2026
              </button>
              <button type="button" onClick={() => quickFill("instructor@lcewai.org", "Teach@LCE2026")}
                className="w-full text-left font-mono hover:text-copper" data-testid="demo-instructor">
                instructor@lcewai.org / Teach@LCE2026
              </button>
              <button type="button" onClick={() => quickFill("admin@lcewai.org", "Admin@LCE2026")}
                className="w-full text-left font-mono hover:text-copper" data-testid="demo-admin">
                admin@lcewai.org / Admin@LCE2026
              </button>
            </div>
          </div>

          <div className="mt-6 text-sm">
            No account? <Link to="/register" className="text-copper font-semibold hover:underline" data-testid="link-register">Enroll as apprentice</Link>
          </div>
          <div className="mt-2 text-sm">
            <Link to="/forgot-password" className="text-ink/60 hover:text-copper hover:underline" data-testid="link-forgot-password">
              Forgot your password?
            </Link>
          </div>
        </form>
      </div>
    </div>
  );
}
