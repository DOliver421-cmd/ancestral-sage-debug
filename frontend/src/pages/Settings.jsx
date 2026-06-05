import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import AppShell from "../components/AppShell";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import { toast } from "sonner";
import { KeyRound, ShieldCheck, AlertTriangle, User as UserIcon, Save, Mail, Trash2, Download, Monitor, XCircle, X, ExternalLink } from "lucide-react";
import { Link } from "react-router-dom";

export default function Settings() {
  const { user, refresh } = useAuth();
  const [params] = useSearchParams();
  const forced = params.get("force") === "1" || user?.must_change_password;
  const [tab, setTab] = useState(forced ? "password" : "profile");
  const [showDeleteModal, setShowDeleteModal] = useState(false);

  // ---- Profile tab state -------------------------------------------------
  const [profile, setProfile] = useState({ full_name: "", email: "" });
  const [profileBusy, setProfileBusy] = useState(false);
  const [profileDirty, setProfileDirty] = useState(false);

  useEffect(() => {
    if (user) {
      setProfile({ full_name: user.full_name || "", email: user.email || "" });
      setProfileDirty(false);
    }
  }, [user]);

  const saveProfile = async (e) => {
    e.preventDefault();
    if (!profile.full_name.trim()) return toast.error("Name cannot be empty");
    if (!profile.email.trim()) return toast.error("Email cannot be empty");
    setProfileBusy(true);
    try {
      await api.patch("/auth/me", {
        full_name: profile.full_name.trim(),
        email: profile.email.trim(),
      });
      toast.success("Profile updated");
      setProfileDirty(false);
      if (refresh) await refresh();
    } catch (err) {
      const detail = err?.response?.data?.detail;
      toast.error(typeof detail === "string" ? detail : "Update failed");
    } finally {
      setProfileBusy(false);
    }
  };

  // ---- Password tab state -----------------------------------------------
  const [pw, setPw] = useState({ current_password: "", new_password: "", confirm: "" });
  const [pwBusy, setPwBusy] = useState(false);

  const submitPassword = async (e) => {
    e.preventDefault();
    if (pw.new_password.length < 8) return toast.error("New password must be at least 8 characters");
    if (pw.new_password === pw.current_password) return toast.error("New password must differ from the current one");
    if (pw.new_password !== pw.confirm) return toast.error("New password and confirmation don't match");
    setPwBusy(true);
    try {
      const r = await api.post("/auth/change-password", {
        current_password: pw.current_password,
        new_password: pw.new_password,
      });
      // Update token and cached user immediately so the redirect lands with
      // fresh state — no stale must_change_password in localStorage.
      if (r.data?.access_token) {
        localStorage.setItem("lce_token", r.data.access_token);
      }
      if (r.data?.user) {
        localStorage.setItem("lce_user", JSON.stringify(r.data.user));
      }
      toast.success("Password changed.");
      setPw({ current_password: "", new_password: "", confirm: "" });
      if (forced) {
        const role = r.data?.user?.role || user?.role;
        window.location.href =
          role === "executive_admin" ? "/admin/system"
            : role === "admin" ? "/admin"
            : role === "instructor" ? "/instructor" : "/dashboard";
      } else {
        if (refresh) await refresh();
      }
    } catch (err) {
      const detail = err?.response?.data?.detail;
      toast.error(typeof detail === "string" ? detail : "Change failed");
    } finally {
      setPwBusy(false);
    }
  };

  return (
    <AppShell>
      <div className="px-10 py-10 max-w-3xl">
        <div className="overline text-copper">Account</div>
        <h1 className="font-heading text-4xl font-bold mt-2 flex items-center gap-3">
          <ShieldCheck className="w-8 h-8 text-copper" /> Settings
        </h1>
        <p className="text-ink/60 mt-2" data-testid="settings-identity">
          Signed in as <span className="font-mono">{user?.email}</span> ({user?.role})
          {user?.associate ? <> &middot; <span className="font-mono">{user.associate}</span></> : null}.
        </p>

        {forced && (
          <div className="card-flat p-4 mt-6 border-l-4 border-l-destructive bg-destructive/5" data-testid="force-banner">
            <div className="flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-destructive flex-shrink-0 mt-0.5" />
              <div>
                <div className="font-heading font-bold text-destructive">Password change required</div>
                <p className="text-sm text-ink/70 mt-1">
                  You're using a temporary password set by an administrator. Choose a new one to continue.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* tab strip */}
        <div className="mt-8 flex gap-1 border-b border-ink/10" role="tablist">
          <TabBtn id="profile" active={tab === "profile"} onClick={() => setTab("profile")} icon={UserIcon}>
            Profile
          </TabBtn>
          <TabBtn id="password" active={tab === "password"} onClick={() => setTab("password")} icon={KeyRound}>
            Password
          </TabBtn>
          <TabBtn id="privacy" active={tab === "privacy"} onClick={() => setTab("privacy")} icon={ShieldCheck}>
            Privacy
          </TabBtn>
          <TabBtn id="sessions" active={tab === "sessions"} onClick={() => setTab("sessions")} icon={Monitor}>
            Sessions
          </TabBtn>
        </div>

        {/* PROFILE */}
        {tab === "profile" && (
          <form onSubmit={saveProfile} className="card-flat p-6 mt-6" data-testid="profile-form">
            <h3 className="font-heading text-xl font-bold flex items-center gap-2">
              <UserIcon className="w-5 h-5 text-copper" /> Profile
            </h3>
            <p className="text-xs text-ink/50 mt-1">
              Edit your display name and email.{" "}
              <Link to="/my-position" className="text-copper hover:underline inline-flex items-center gap-1">
                Manage your position and role <ExternalLink className="w-3 h-3" />
              </Link>
            </p>
            <div className="space-y-4 mt-5">
              <Field
                label="Full name"
                value={profile.full_name}
                onChange={(v) => { setProfile({ ...profile, full_name: v }); setProfileDirty(true); }}
                testid="input-profile-name"
              />
              <Field
                label="Email"
                type="email"
                value={profile.email}
                onChange={(v) => { setProfile({ ...profile, email: v }); setProfileDirty(true); }}
                testid="input-profile-email"
              />
              <div className="grid grid-cols-2 gap-4 pt-2">
                <ReadOnly label="Role" value={user?.role || ""} testid="ro-role" />
                <ReadOnly label="Associate" value={user?.associate || "—"} testid="ro-associate" />
              </div>
            </div>
            <button
              type="submit"
              disabled={profileBusy || !profileDirty}
              className="btn-primary mt-6 inline-flex items-center gap-2"
              data-testid="btn-save-profile"
            >
              <Save className="w-4 h-4" /> {profileBusy ? "Saving…" : "Save changes"}
            </button>
          </form>
        )}

        {/* PASSWORD */}
        {tab === "password" && (
          <form onSubmit={submitPassword} className="card-flat p-6 mt-6" data-testid="change-password-form">
            <h3 className="font-heading text-xl font-bold flex items-center gap-2">
              <KeyRound className="w-5 h-5 text-copper" /> Change Password
            </h3>
            <div className="space-y-4 mt-5">
              <Field
                label="Current password"
                type="password"
                value={pw.current_password}
                onChange={(v) => setPw({ ...pw, current_password: v })}
                testid="input-current"
              />
              <Field
                label="New password (min 6 chars)"
                type="password"
                value={pw.new_password}
                onChange={(v) => setPw({ ...pw, new_password: v })}
                testid="input-new"
              />
              <Field
                label="Confirm new password"
                type="password"
                value={pw.confirm}
                onChange={(v) => setPw({ ...pw, confirm: v })}
                testid="input-confirm"
              />
            </div>
            <button type="submit" disabled={pwBusy} className="btn-primary mt-5" data-testid="btn-change-password">
              {pwBusy ? "Saving…" : "Update password"}
            </button>
            <p className="text-xs text-ink/50 mt-4 flex items-center gap-1.5">
              <Mail className="w-3.5 h-3.5" /> Forgot it? Sign out and use the “Forgot password?” link on the login page.
            </p>
          </form>
        )}

        {/* SESSIONS */}
        {tab === "sessions" && (
          <SessionManager />
        )}

        {/* PRIVACY / GDPR */}
        {tab === "privacy" && (
          <div className="card-flat p-6 mt-6 space-y-6">
            <h3 className="font-heading text-xl font-bold flex items-center gap-2">
              <ShieldCheck className="w-5 h-5 text-copper" /> Privacy & Legal
            </h3>

            {/* Export Data */}
            <div>
              <p className="text-sm text-ink/70 mb-3">
                Download all personal data we hold about you (GDPR Article 20 — Data Portability).
              </p>
              <button
                type="button"
                className="btn-primary inline-flex items-center gap-2"
                onClick={async () => {
                  try {
                    const r = await api.get("/auth/account/export");
                    const blob = new Blob([JSON.stringify(r.data, null, 2)], { type: "application/json" });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement("a");
                    a.href = url;
                    a.download = `sage-export-${new Date().toISOString().split("T")[0]}.json`;
                    a.click();
                    URL.revokeObjectURL(url);
                    toast.success("Data exported.");
                  } catch (err) {
                    toast.error("Export failed. Try again later.");
                  }
                }}
              >
                <Download className="w-4 h-4" /> Export My Data
              </button>
            </div>

            {/* Delete Account */}
            <div className="border-t border-ink/10 pt-6">
              <p className="text-sm text-ink/70 mb-3">
                Permanently delete your account and anonymize all personal data
                (GDPR Article 17 — Right to Erasure). This action cannot be undone.
              </p>
              <button
                type="button"
                className="px-4 py-2 text-sm font-bold border-2 border-destructive text-destructive rounded hover:bg-destructive/10 transition-colors inline-flex items-center gap-2"
                onClick={() => setShowDeleteModal(true)}
              >
                <Trash2 className="w-4 h-4" /> Delete My Account
              </button>
            </div>
          </div>
        )}
      </div>
      {showDeleteModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md">
            <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <Trash2 className="w-4 h-4 text-red-600" />
                <h2 className="font-heading font-bold text-lg text-slate-900">Delete Your Account</h2>
              </div>
              <button onClick={() => setShowDeleteModal(false)} className="text-slate-400 hover:text-slate-600"><X className="w-5 h-5" /></button>
            </div>
            <div className="px-6 py-5 space-y-3">
              <div className="bg-red-50 border border-red-200 rounded-lg px-4 py-3 text-sm text-red-800">
                <strong>This cannot be undone.</strong> Your account will be immediately anonymized and permanently deleted after 30 days (GDPR Article 17). You can contact support within that period to cancel.
              </div>
              <p className="text-sm text-slate-600">All progress, submissions, and personal data will be lost.</p>
            </div>
            <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-slate-100">
              <button onClick={() => setShowDeleteModal(false)} className="text-sm px-4 py-2 rounded-lg text-slate-600 hover:bg-slate-50">Cancel</button>
              <button
                className="flex items-center gap-2 text-sm px-5 py-2 rounded-lg bg-red-600 text-white font-bold hover:bg-red-700"
                onClick={async () => {
                  try {
                    await api.delete("/auth/account");
                    toast.success("Account scheduled for deletion. You will be signed out.");
                    localStorage.removeItem("auth_token");
                    window.location.href = "/";
                  } catch (err) {
                    const detail = err?.response?.data?.detail;
                    toast.error(typeof detail === "string" ? detail : "Account deletion failed.");
                    setShowDeleteModal(false);
                  }
                }}
              >
                <Trash2 className="w-4 h-4" /> Permanently Delete Account
              </button>
            </div>
          </div>
        </div>
      )}
    </AppShell>
  );
}

function TabBtn({ active, onClick, icon: Icon, children, id }) {
  return (
    <button
      type="button"
      role="tab"
      aria-selected={active}
      onClick={onClick}
      className={`px-4 py-2 text-sm font-bold border-b-2 inline-flex items-center gap-2 transition-colors ${
        active ? "border-copper text-ink" : "border-transparent text-ink/50 hover:text-ink"
      }`}
      data-testid={`tab-${id}`}
    >
      <Icon className="w-4 h-4" /> {children}
    </button>
  );
}

function Field({ label, value, onChange, type = "text", testid }) {
  return (
    <label className="block">
      <span className="overline text-ink/60">{label}</span>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        required
        className="w-full mt-2 px-4 py-3 bg-white border border-ink/20 focus:border-ink focus:outline-none focus:ring-2 focus:ring-signal"
        data-testid={testid}
      />
    </label>
  );
}

function ReadOnly({ label, value, testid }) {
  return (
    <div>
      <span className="overline text-ink/60">{label}</span>
      <div className="mt-2 px-4 py-3 bg-ink/5 border border-ink/10 font-mono text-sm" data-testid={testid}>
        {value}
      </div>
    </div>
  );
}

function SessionManager() {
  const [sessions, setSessions] = useState([]);
  const [busy, setBusy] = useState(false);

  const load = async () => {
    setBusy(true);
    try {
      const r = await api.get("/auth/sessions");
      setSessions(r.data.sessions || []);
    } catch {
      toast.error("Failed to load sessions.");
    } finally {
      setBusy(false);
    }
  };

  useEffect(() => { load(); }, []);

  const revokeAll = async () => {
    if (!window.confirm("Log out all other devices? You will need to sign in again on those devices.")) return;
    try {
      await api.delete("/auth/sessions");
      toast.success("Other sessions revoked.");
      setSessions([]);
    } catch {
      toast.error("Failed to revoke sessions.");
    }
  };

  const revokeOne = async (sid) => {
    try {
      await api.delete(`/auth/sessions/${sid}`);
      toast.success("Session revoked.");
      load();
    } catch {
      toast.error("Failed to revoke session.");
    }
  };

  return (
    <div className="card-flat p-6 mt-6">
      <h3 className="font-heading text-xl font-bold flex items-center gap-2">
        <Monitor className="w-5 h-5 text-copper" /> Active Sessions
      </h3>
      <p className="text-xs text-ink/50 mt-1">Devices currently logged into your account.</p>

      {busy && <p className="text-sm text-ink/50 mt-4">Loading sessions…</p>}

      {!busy && sessions.length === 0 && (
        <p className="text-sm text-ink/50 mt-4">No other active sessions.</p>
      )}

      {!busy && sessions.length > 0 && (
        <>
          <div className="space-y-3 mt-4">
            {sessions.map((s) => (
              <div key={s.session_id} className="flex items-center justify-between p-3 bg-ink/5 rounded-lg">
                <div className="text-sm">
                  <p className="font-medium text-ink">{s.user_agent ? s.user_agent.slice(0, 60) : "Unknown device"}</p>
                  <p className="text-xs text-ink/50 mt-0.5">
                    {s.ip ? `${s.ip} · ` : ""}
                    {s.created_at ? new Date(s.created_at).toLocaleDateString() : ""}
                  </p>
                </div>
                <button
                  onClick={() => revokeOne(s.session_id)}
                  className="text-destructive hover:text-destructive/80 transition-colors"
                  title="Revoke session"
                >
                  <XCircle className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
          <button
            onClick={revokeAll}
            className="mt-4 px-4 py-2 text-sm border border-destructive text-destructive rounded-lg hover:bg-destructive/10 transition-colors"
          >
            Log out all other devices
          </button>
        </>
      )}
    </div>
  );
}
