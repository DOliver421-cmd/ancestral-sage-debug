import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import AppShell from "../components/AppShell";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import { toast } from "sonner";
import { KeyRound, ShieldCheck, AlertTriangle } from "lucide-react";

export default function Settings() {
  const { user } = useAuth();
  const [params] = useSearchParams();
  const forced = params.get("force") === "1" || user?.must_change_password;
  const [form, setForm] = useState({ current_password: "", new_password: "", confirm: "" });
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    if (form.new_password.length < 6) { toast.error("New password must be at least 6 characters"); return; }
    if (form.new_password === form.current_password) { toast.error("New password must differ from the current one"); return; }
    if (form.new_password !== form.confirm) { toast.error("New password and confirmation don't match"); return; }
    setBusy(true);
    try {
      await api.post("/auth/change-password", {
        current_password: form.current_password,
        new_password: form.new_password,
      });
      toast.success("Password changed. You're all set.");
      setForm({ current_password: "", new_password: "", confirm: "" });
      // If they were forced, send them home now.
      if (forced) {
        const role = user?.role;
        window.location.href = role === "executive_admin" || role === "admin" ? "/admin"
          : role === "instructor" ? "/instructor" : "/dashboard";
      }
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Change failed");
    } finally { setBusy(false); }
  };

  return (
    <AppShell>
      <div className="px-10 py-10 max-w-2xl">
        <div className="overline text-copper">Account</div>
        <h1 className="font-heading text-4xl font-bold mt-2 flex items-center gap-3">
          <ShieldCheck className="w-8 h-8 text-copper" /> Settings
        </h1>
        <p className="text-ink/60 mt-2">Signed in as <span className="font-mono">{user?.email}</span> ({user?.role}).</p>

        {forced && (
          <div className="card-flat p-4 mt-6 border-l-4 border-l-destructive bg-destructive/5" data-testid="force-banner">
            <div className="flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-destructive flex-shrink-0 mt-0.5" />
              <div>
                <div className="font-heading font-bold text-destructive">Password change required</div>
                <p className="text-sm text-ink/70 mt-1">You're using a temporary password set by an administrator. Choose a new one to continue.</p>
              </div>
            </div>
          </div>
        )}

        <form onSubmit={submit} className="card-flat p-6 mt-6" data-testid="change-password-form">
          <h3 className="font-heading text-xl font-bold flex items-center gap-2"><KeyRound className="w-5 h-5 text-copper" /> Change Password</h3>
          <div className="space-y-4 mt-5">
            <Field label="Current password" type="password" value={form.current_password}
              onChange={(v) => setForm({ ...form, current_password: v })} testid="input-current" />
            <Field label="New password (min 6 chars)" type="password" value={form.new_password}
              onChange={(v) => setForm({ ...form, new_password: v })} testid="input-new" />
            <Field label="Confirm new password" type="password" value={form.confirm}
              onChange={(v) => setForm({ ...form, confirm: v })} testid="input-confirm" />
          </div>
          <button type="submit" disabled={busy} className="btn-primary mt-5" data-testid="btn-change-password">
            {busy ? "Saving…" : "Update Password"}
          </button>
        </form>
      </div>
    </AppShell>
  );
}

function Field({ label, value, onChange, type = "text", testid }) {
  return (
    <label className="block">
      <span className="overline text-ink/60">{label}</span>
      <input type={type} value={value} onChange={(e) => onChange(e.target.value)} required
        className="w-full mt-2 px-4 py-3 bg-white border border-ink/20 focus:border-ink focus:outline-none focus:ring-2 focus:ring-signal"
        data-testid={testid} />
    </label>
  );
}
