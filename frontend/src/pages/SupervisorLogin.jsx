import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../lib/auth";
import { toast } from "sonner";

export default function SupervisorLogin() {
  const navigate = useNavigate();
  const { login, logout } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async (event) => {
    event.preventDefault();
    setLoading(true);
    try {
      const user = await login(email.trim(), password);
      if (!user || user.role !== "executive_admin") {
        toast.error("Supervisor login requires an executive admin account.");
        await logout();
        setLoading(false);
        return;
      }
      toast.success("Supervisor session active. Redirecting to supervisor hub...");
      navigate("/supervisor", { replace: true });
    } catch (error) {
      toast.error("Unable to sign in. Please check supervisor credentials and try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100 px-4 py-12 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-xl rounded-3xl border border-slate-800 bg-slate-900/95 p-10 shadow-2xl shadow-slate-950/40">
        <div className="mb-8 text-center">
          <p className="text-sm uppercase tracking-[0.4em] text-cyan-300">Supervisor Access</p>
          <h1 className="mt-4 text-3xl font-bold text-white">Executive / Supervisor Login</h1>
          <p className="mt-3 text-sm text-slate-400">
            Use the supervisor sign in flow to access secure executive controls and the centralized MORE Help Center experience.
          </p>
        </div>

        <form onSubmit={submit} className="space-y-6">
          <label className="block">
            <span className="text-sm font-semibold text-slate-200">Email</span>
            <input
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
              className="mt-2 w-full rounded-2xl border border-slate-700 bg-slate-950/70 px-4 py-3 text-sm text-white outline-none transition focus:border-cyan-400 focus:ring-2 focus:ring-cyan-500/20"
            />
          </label>

          <label className="block">
            <span className="text-sm font-semibold text-slate-200">Password</span>
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
              className="mt-2 w-full rounded-2xl border border-slate-700 bg-slate-950/70 px-4 py-3 text-sm text-white outline-none transition focus:border-cyan-400 focus:ring-2 focus:ring-cyan-500/20"
            />
          </label>

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-2xl bg-cyan-500 px-4 py-3 text-sm font-bold uppercase tracking-[0.2em] text-slate-950 transition hover:bg-cyan-400 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {loading ? "Signing in…" : "Supervisor sign in"}
          </button>
        </form>

        <div className="mt-8 space-y-3 text-center text-sm text-slate-400">
          <p>
            If you are not a supervisor, please use the standard platform login.
          </p>
          <Link to="/login" className="font-semibold text-cyan-300 hover:text-cyan-200">
            Back to main sign in
          </Link>
        </div>
      </div>
    </main>
  );
}
