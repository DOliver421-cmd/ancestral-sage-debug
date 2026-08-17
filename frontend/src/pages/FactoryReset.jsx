import { useState } from "react";
import { Link } from "react-router-dom";
import { WAI_LOGO, BRAND } from "../lib/brand";
import { api } from "../lib/api";
import { AlertTriangle, ShieldCheck, ArrowRight } from "lucide-react";

/**
 * Factory reset page — the browser-accessible break-glass wipe.
 *
 * Deletes ALL accounts and user data on the server, then the very next
 * registration becomes the executive_admin (owner) account. Requires the
 * break-glass secret (EXEC_RESET_SECRET or RESEND_API_KEY) which the owner
 * pastes here — the server validates it, so this page is harmless without it.
 */
export default function FactoryReset() {
  const [secret, setSecret] = useState("");
  const [confirmText, setConfirmText] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);   // {ok, deleted, message} | error string
  const [done, setDone] = useState(false);

  const confirmOk = confirmText === "DELETE ALL";

  const submit = async (e) => {
    e.preventDefault();
    if (!secret.trim()) { setResult("Enter the break-glass secret first."); return; }
    if (!confirmOk) { setResult("Type DELETE ALL exactly to confirm."); return; }
    setLoading(true);
    setResult(null);
    try {
      const r = await api.post("/auth/factory-reset", {
        secret: secret.trim(),
        confirm: "DELETE ALL",
      });
      setResult({ ok: true, ...r.data });
      setDone(true);
    } catch (err) {
      const status = err?.response?.status;
      if (status === 403) setResult("Wrong secret — the server rejected it.");
      else if (status === 404) setResult("Factory reset is not enabled on this server (no break-glass secret reached it).");
      else setResult(err?.response?.data?.detail || "Request failed — try again.");
    } finally { setLoading(false); }
  };

  return (
    <div className="min-h-screen bg-bone">
      <header className="border-b border-ink/10 bg-bone">
        <div className="max-w-3xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-3">
            <img src={WAI_LOGO} alt="M.O.R.E." className="w-10 h-10 object-contain" />
            <div>
              <div className="overline text-copper leading-none text-xs">{BRAND.short}</div>
              <div className="font-heading font-bold text-sm">{BRAND.name}</div>
            </div>
          </Link>
          <Link to="/login" className="text-sm font-bold uppercase tracking-widest text-copper hover:text-copper/80">
            Sign In
          </Link>
        </div>
      </header>

      <main className="max-w-xl mx-auto px-6 py-16">
        <div className="flex items-center gap-3 mb-2">
          <AlertTriangle className="w-6 h-6 text-red-700" />
          <span className="overline text-red-800 text-xs font-bold">Owner Only</span>
        </div>
        <h1 className="font-heading text-3xl font-bold text-ink mb-2">Factory Reset</h1>
        <p className="text-ink/70 text-sm leading-relaxed mb-8">
          This wipes <strong>every account and all user data</strong> on the server — students,
          progress, certificates, portfolios, everything. There is no undo. After the wipe, the
          <strong> next account created becomes the owner</strong> (executive admin).
        </p>

        {!done ? (
          <form onSubmit={submit} className="bg-white border border-ink/10 rounded-2xl p-6 shadow-sm space-y-5">
            <div>
              <label className="block text-xs font-bold uppercase tracking-widest text-ink/60 mb-1.5">
                Break-glass secret
              </label>
              <input
                type="password"
                value={secret}
                onChange={(e) => setSecret(e.target.value)}
                placeholder="Paste EXEC_RESET_SECRET or your Resend API key"
                className="w-full border border-ink/20 rounded-lg px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-copper"
              />
              <p className="text-xs text-ink/50 mt-1.5">
                Copy it from Railway → backend service → Variables → click the value to reveal it.
              </p>
            </div>

            <div>
              <label className="block text-xs font-bold uppercase tracking-widest text-ink/60 mb-1.5">
                Type <span className="text-red-700">DELETE ALL</span> to confirm
              </label>
              <input
                type="text"
                value={confirmText}
                onChange={(e) => setConfirmText(e.target.value)}
                placeholder="DELETE ALL"
                className="w-full border border-ink/20 rounded-lg px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-copper"
              />
            </div>

            <button
              type="submit"
              disabled={loading || !confirmOk}
              className="w-full rounded-lg bg-red-800 text-white font-bold py-3.5 text-sm uppercase tracking-widest hover:bg-red-900 disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {loading ? "Wiping…" : (<><ShieldCheck className="w-4 h-4" /> Delete all accounts</>)}
            </button>

            {result && typeof result === "string" && (
              <p className="text-sm text-red-700 bg-red-50 border border-red-200 rounded-lg px-4 py-3">{result}</p>
            )}
          </form>
        ) : (
          <div className="bg-white border border-ink/10 rounded-2xl p-6 shadow-sm space-y-4">
            <div className="flex items-center gap-2 text-green-800">
              <ShieldCheck className="w-5 h-5" />
              <span className="font-bold text-sm uppercase tracking-widest">Reset complete</span>
            </div>
            <p className="text-sm text-ink/70">
              {result?.deleted?.users != null && (
                <span className="block mb-1"><strong>{result.deleted.users}</strong> account(s) deleted.</span>
              )}
              The site is now empty. <strong>Create the owner account now</strong> — the first account
              registered becomes the executive admin.
            </p>
            <Link
              to="/register"
              className="inline-flex items-center gap-2 rounded-lg bg-ink text-white font-bold py-3 px-6 text-sm uppercase tracking-widest hover:bg-ink/85"
            >
              Create owner account <ArrowRight className="w-4 h-4" />
            </Link>
            <p className="text-xs text-ink/50">
              Anyone who registers before you would become owner — so do it immediately.
            </p>
          </div>
        )}
      </main>
    </div>
  );
}
