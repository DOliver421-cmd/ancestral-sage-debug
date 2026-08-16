import { useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import { WAI_LOGO, BRAND } from "../lib/brand";
import { toast } from "sonner";
import { ArrowLeft, MailCheck, KeyRound } from "lucide-react";

// status: "form" | "sent" | "notdelivered" | "error"
//  - sent:         backend confirmed the email was handed to a provider
//  - notdelivered: backend answered 200 but email_sent=false (provider missing
//                  or send failed). Same response shape for unknown emails, so
//                  this card never leaks whether an account exists.
//  - error:        network failure or server error — honest retry path.
export default function ForgotPassword() {
  const [email, setEmail] = useState("");
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState("form");
  const [errorMsg, setErrorMsg] = useState("");

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    setStatus("form");
    setErrorMsg("");
    try {
      // Backend always returns 200 for valid requests (no enumeration),
      // with email_sent indicating whether delivery actually completed.
      const r = await api.post("/auth/forgot-password", { email });
      setStatus(r?.data?.email_sent === true ? "sent" : "notdelivered");
    } catch (err) {
      if (err?.response) {
        // Server answered (4xx/5xx — rate limit, validation, outage). Show the
        // backend message; never claim a link was sent.
        const detail = err?.response?.data?.detail;
        if (typeof detail === "string") toast.error(detail);
        setStatus("error");
        setErrorMsg(typeof detail === "string" ? detail : "The server hit an error. Please try again in a moment.");
      } else {
        // Network / CORS failure — the request never reached the server.
        setStatus("error");
        setErrorMsg("Could not reach the server. Check your connection and try again.");
      }
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="min-h-screen bg-bone grid lg:grid-cols-2">
      <div className="hidden lg:block bg-ink relative overflow-hidden">
        <div className="absolute inset-0 grid-paper opacity-10" />
        <div className="relative h-full flex flex-col justify-between p-12 text-white">
          <Link to="/" className="flex items-center gap-3" data-testid="forgot-brand">
            <img src={WAI_LOGO} alt="W.A.I." className="w-12 h-12 object-contain bg-white p-1" />
            <div>
              <div className="overline text-signal">{BRAND.short}</div>
              <div className="font-heading font-bold">{BRAND.name}</div>
            </div>
          </Link>
          <div>
            <div className="overline text-copper">Account recovery</div>
            <h1 className="font-heading text-5xl font-extrabold mt-4 leading-tight">
              Locked out? <br /> We've got you.
            </h1>
            <p className="mt-6 text-white/70 max-w-md">
              We'll send a single-use reset link to your email. Links expire in 30 minutes for your safety.
            </p>
          </div>
          <div className="text-xs text-white/50 italic">
            "He restoreth my soul." — Psalm 23:3
          </div>
        </div>
      </div>

      <div className="flex items-center justify-center p-8">
        <div className="w-full max-w-md">
          {status === "sent" ? (
            <div data-testid="forgot-submitted-card">
              <div className="overline text-copper">Check your email</div>
              <h2 className="font-heading text-3xl font-bold mt-2 flex items-center gap-3">
                <MailCheck className="w-7 h-7 text-signal" /> Request received.
              </h2>
              <p className="text-ink/60 mt-3">
                If <span className="font-mono font-semibold">{email}</span> is associated with a W.A.I. account,
                a password-reset link is on its way. The link is valid for <strong>30 minutes</strong> and can
                only be used once.
              </p>
              <div className="card-flat p-4 mt-6 bg-white border-l-4 border-l-signal">
                <p className="text-sm text-ink/70">
                  Didn't get an email? Check your spam folder or
                  <strong> contact your program administrator</strong> &mdash; they can mint a reset link for you directly.
                </p>
              </div>
              <Link to="/login" className="btn-secondary mt-6 inline-flex items-center gap-2" data-testid="forgot-back-to-login">
                <ArrowLeft className="w-4 h-4" /> Back to sign in
              </Link>
            </div>
          ) : status === "notdelivered" ? (
            <div data-testid="forgot-notdelivered-card">
              <div className="overline text-copper">Almost there</div>
              <h2 className="font-heading text-3xl font-bold mt-2 flex items-center gap-3">
                <MailCheck className="w-7 h-7 text-signal" /> Request received.
              </h2>
              <p className="text-ink/60 mt-3">
                If <span className="font-mono font-semibold">{email}</span> is associated with a W.A.I. account,
                we attempted to send a reset link &mdash; but our email service did not confirm delivery.
              </p>
              <div className="card-flat p-4 mt-6 bg-white border-l-4 border-l-signal">
                <p className="text-sm text-ink/70">
                  <strong>No email arrived?</strong> Please <strong>contact your program administrator</strong> &mdash;
                  they can mint a working reset link for you directly. (Administrators: check the backend logs for the
                  one-time recovery link, or use the &ldquo;reset link&rdquo; action in the admin panel.)
                </p>
              </div>
              <Link to="/login" className="btn-secondary mt-6 inline-flex items-center gap-2" data-testid="forgot-back-to-login">
                <ArrowLeft className="w-4 h-4" /> Back to sign in
              </Link>
            </div>
          ) : status === "error" ? (
            <div data-testid="forgot-error-card">
              <div className="overline text-destructive">Something went wrong</div>
              <h2 className="font-heading text-3xl font-bold mt-2">We couldn't submit your request.</h2>
              <p className="text-ink/60 mt-3">{errorMsg}</p>
              <div className="mt-6 flex flex-col gap-3">
                <button type="button" onClick={() => setStatus("form")} className="btn-primary w-full" data-testid="forgot-retry">
                  Try again
                </button>
                <Link to="/login" className="btn-secondary w-full inline-flex items-center justify-center gap-2" data-testid="forgot-back-to-login">
                  <ArrowLeft className="w-4 h-4" /> Back to sign in
                </Link>
              </div>
            </div>
          ) : (
            <form onSubmit={submit} data-testid="forgot-form">
              <div className="overline text-copper">Forgot Password</div>
              <h2 className="font-heading text-3xl font-bold mt-2 flex items-center gap-3">
                <KeyRound className="w-7 h-7 text-copper" /> Reset password.
              </h2>
              <p className="text-ink/60 text-sm mt-2">
                Enter the email tied to your W.A.I. account. We'll send a one-shot reset link.
              </p>

              <div className="mt-8 space-y-4">
                <div>
                  <label className="overline text-ink/60">Email</label>
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full mt-2 px-4 py-3 bg-white border border-ink/20 focus:border-ink focus:outline-none focus:ring-2 focus:ring-signal"
                    data-testid="input-forgot-email"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={busy}
                className="btn-primary w-full mt-6"
                data-testid="btn-forgot-submit"
              >
                {busy ? "Sending…" : "Send reset link"}
              </button>

              <div className="mt-6 text-sm">
                Remembered it?{" "}
                <Link to="/login" className="text-copper font-semibold hover:underline" data-testid="forgot-link-login">
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
