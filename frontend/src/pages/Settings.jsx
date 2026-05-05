import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import AppShell from "../components/AppShell";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import { toast } from "sonner";
import { KeyRound, ShieldCheck, AlertTriangle, User as UserIcon, Save, Mail } from "lucide-react";

export default function Settings() {
  const { user, refresh } = useAuth();
  const [params] = useSearchParams();
  const forced = params.get("force") === "1" || user?.must_change_password;
  const [tab, setTab] = useState(forced ? "password" : "profile");

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
    if (pw.new_password.length < 6) return toast.error("New password must be at least 6 characters");
    if (pw.new_password === pw.current_password) return toast.error("New password must differ from the current one");
    if (pw.new_password !== pw.confirm) return toast.error("New password and confirmation don't match");
    setPwBusy(true);
    try {
      await api.post("/auth/change-password", {
        current_password: pw.current_password,
        new_password: pw.new_password,
      });
      toast.success("Password changed.");
      setPw({ current_password: "", new_password: "", confirm: "" });
      if (forced) {
        const role = user?.role;
        window.location.href =
          role === "executive_admin" || role === "admin" ? "/admin"
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
        </div>

        {/* PROFILE */}
        {tab === "profile" && (
          <form onSubmit={saveProfile} className="card-flat p-6 mt-6" data-testid="profile-form">
            <h3 className="font-heading text-xl font-bold flex items-center gap-2">
              <UserIcon className="w-5 h-5 text-copper" /> Profile
            </h3>
            <p className="text-xs text-ink/50 mt-1">
              Edit your display name and email. Role and associate are managed by an administrator.
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
      </div>
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
