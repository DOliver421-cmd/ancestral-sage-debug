import { useEffect, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { api } from "../lib/api";
import { WAI_LOGO, BRAND } from "../lib/brand";
import { toast } from "sonner";
import { CheckCircle2, KeyRound, AlertTriangle } from "lucide-react";

export default function ResetPassword() {
  const [params] = useSearchParams();
  const nav = useNavigate();
  const token = params.get("token") || "";
  const [pw, setPw] = useState("");
  const [confirm, setConfirm] = useState("");
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(null); // null | { email }
  const [tokenError, setTokenError] = useState(!token ? "No token in URL" : "");

  useEffect(() => {
    if (!token) setTokenError("No token in URL");
  }, [token]);

  const submit = async (e) => {
    e.preventDefault();
    if (pw.length < 6) return toast.error("Password must be at least 6 characters");
    if (pw !== confirm) return toast.error("New password and confirmation don't match");
    setBusy(true);
    try {
      const r = await api.post("/auth/reset-password", { token, new_password: pw });
      setDone({ email: r.data?.email || "" });
      toast.success("Password reset. You can sign in now.");
      setTimeout(() => nav("/login"), 2500);
    } catch (err) {
      const detail = err?.response?.data?.detail;
      toast.error(typeof detail === "string" ? detail : "Reset failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="min-h-screen bg-bone grid lg:grid-cols-2">
      <div className="hidden lg:block bg-ink relative overflow-hidden">
        <div className="absolute inset-0 grid-paper opacity-10" />
        <div className="relative h-full flex flex-col justify-between p-12 text-white">
          <Link to="/" className="flex items-center gap-3" data-testid="reset-brand">
            <img src={WAI_LOGO} alt="W.A.I." className="w-12 h-12 object-contain bg-white p-1" />
            <div>
              <div className="overline text-signal">{BRAND.short}</div>
              <div className="font-heading font-bold">{BRAND.name}</div>
            </div>
          </Link>
          <div>
            <div className="overline text-copper">Choose a new password</div>
            <h1 className="font-heading text-5xl font-extrabold mt-4 leading-tight">
              Pick something strong.
            </h1>
            <p className="mt-6 text-white/70 max-w-md">
              At least 6 characters &mdash; mix letters, numbers, and a symbol if you can.
              This link is single-use; if you need another one, request again.
            </p>
          </div>
          <div className="text-xs text-white/50 italic">
            "Set a guard, O Lord, over my mouth; keep watch over the door of my lips." &mdash; Psalm 141:3
          </div>
        </div>
      </div>

      <div className="flex items-center justify-center p-8">
        <div className="w-full max-w-md">
          {done ? (
            <div data-testid="reset-success-card">
              <div className="overline text-signal">Done</div>
              <h2 className="font-heading text-3xl font-bold mt-2 flex items-center gap-3">
                <CheckCircle2 className="w-7 h-7 text-signal" /> Password reset.
              </h2>
              <p className="text-ink/60 mt-3">
                {done.email ? <>Your password for <span className="font-mono">{done.email}</span> is updated.</> : "Your password is updated."}
                Redirecting you to sign in&hellip;
              </p>
              <Link to="/login" className="btn-primary mt-6 inline-flex" data-testid="reset-go-login">Sign in now</Link>
            </div>
          ) : tokenError ? (
            <div data-testid="reset-token-error">
              <div className="overline text-destructive">Invalid link</div>
              <h2 className="font-heading text-3xl font-bold mt-2 flex items-center gap-3">
                <AlertTriangle className="w-7 h-7 text-destructive" /> This link looks broken.
              </h2>
              <p className="text-ink/60 mt-3">{tokenError}. Please request a fresh reset link.</p>
              <Link to="/forgot-password" className="btn-primary mt-6 inline-flex" data-testid="reset-request-new">
                Request a new link
              </Link>
            </div>
          ) : (
            <form onSubmit={submit} data-testid="reset-form">
              <div className="overline text-copper">Reset Password</div>
              <h2 className="font-heading text-3xl font-bold mt-2 flex items-center gap-3">
                <KeyRound className="w-7 h-7 text-copper" /> Set a new password.
              </h2>
              <p className="text-ink/60 text-sm mt-2">Single-use link. Expires 30 min after issue.</p>

              <div className="mt-8 space-y-4">
                <div>
                  <label className="overline text-ink/60">New password (min 6 chars)</label>
                  <input
                    type="password"
                    required
                    minLength={6}
                    value={pw}
                    onChange={(e) => setPw(e.target.value)}
                    className="w-full mt-2 px-4 py-3 bg-white border border-ink/20 focus:border-ink focus:outline-none focus:ring-2 focus:ring-signal"
                    data-testid="input-reset-password"
                  />
                </div>
                <div>
                  <label className="overline text-ink/60">Confirm new password</label>
                  <input
                    type="password"
                    required
                    minLength={6}
                    value={confirm}
                    onChange={(e) => setConfirm(e.target.value)}
                    className="w-full mt-2 px-4 py-3 bg-white border border-ink/20 focus:border-ink focus:outline-none focus:ring-2 focus:ring-signal"
                    data-testid="input-reset-confirm"
                  />
                </div>
              </div>

              <button type="submit" disabled={busy} className="btn-primary w-full mt-6" data-testid="btn-reset-submit">
                {busy ? "Updating…" : "Reset password"}
              </button>

              <div className="mt-6 text-sm">
                <Link to="/login" className="text-copper font-semibold hover:underline" data-testid="reset-link-login">
                  Back to sign in
                </Link>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
