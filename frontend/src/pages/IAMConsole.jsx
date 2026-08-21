import { useCallback, useEffect, useMemo, useState } from "react";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import {
  ROLES_ALL, ROLE_LABELS, ROLE_COLORS, ROLE_RANK, roleAtLeast, canModifyRole,
} from "../lib/roles";
import {
  Search, ShieldCheck, KeyRound, UserPlus, Ban, CircleCheck, Trash2,
  RefreshCw, Grid3X3, Users, Loader2, X,
} from "lucide-react";
import { toast } from "sonner";

const PERMISSION_KEYS = [
  "content_read",
  "content_create",
  "content_edit_own",
  "content_delete_own",
  "user_warn",
  "user_mute",
  "user_ban",
  "api_access",
  "billing_view",
  "export_data",
];

const PERMISSION_LABELS = {
  content_read: "Read content",
  content_create: "Create content",
  content_edit_own: "Edit own content",
  content_delete_own: "Delete own content",
  user_warn: "Warn users",
  user_mute: "Mute users",
  user_ban: "Ban users",
  api_access: "API access",
  billing_view: "View billing",
  export_data: "Export data",
};

export default function IAMConsole() {
  const { user: me } = useAuth();
  const [tab, setTab] = useState("users"); // "users" | "matrix"
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [q, setQ] = useState("");
  const [roleFilter, setRoleFilter] = useState("");
  const [matrix, setMatrix] = useState(null);
  const [matrixDirty, setMatrixDirty] = useState(false);
  const [busyId, setBusyId] = useState(null);
  const [verifyingId, setVerifyingId] = useState(null);

  const isExec = roleAtLeast(me?.role, "executive_admin");
  const isAdmin = roleAtLeast(me?.role, "admin");

  const loadUsers = useCallback(async () => {
    if (!isAdmin) return;
    setLoading(true);
    try {
      const params = {};
      if (q.trim()) params.q = q.trim();
      if (roleFilter) params.role = roleFilter;
      const r = await api.get("/admin/users", { params });
      setUsers(Array.isArray(r.data) ? r.data : []);
    } catch (e) {
      toast.error("Could not load users.");
    } finally {
      setLoading(false);
    }
  }, [q, roleFilter, isAdmin]);

  const loadMatrix = useCallback(async () => {
    if (!isExec) return;
    try {
      const r = await api.get("/admin/rbac/matrix");
      setMatrix(r.data?.matrix || null);
    } catch (e) {
      setMatrix(null);
    }
  }, [isExec]);

  useEffect(() => {
    loadUsers();
  }, [loadUsers]);

  useEffect(() => {
    if (tab === "matrix") loadMatrix();
  }, [tab, loadMatrix]);

  // ── Atomic enforcement: secondary GET that proves DB state, not intent ──────
  const verify = useCallback(async (uid) => {
    setVerifyingId(uid);
    try {
      const r = await api.get(`/admin/users/${uid}`);
      return r.data;
    } finally {
      setVerifyingId(null);
    }
  }, []);

  const runMutation = useCallback(async (label, fn, uid) => {
    setBusyId(uid);
    try {
      const res = await fn();
      // After ANY mutation, re-read from the DB to confirm enforcement state.
      const verified = await verify(uid);
      toast.success(`${label} — verified: ${ROLE_LABELS[verified?.role] || verified?.role} / ${verified?.is_active === false ? "locked" : "active"}`);
      await loadUsers();
      return res;
    } catch (e) {
      toast.error(e?.response?.data?.detail || `${label} failed.`);
      throw e;
    } finally {
      setBusyId(null);
    }
  }, [verify, loadUsers]);

  const changeRole = (u, role) =>
    runMutation("Role updated", () => api.patch(`/admin/users/${u.id}/role`, { role }), u.id);

  const toggleActive = (u) =>
    runMutation(
      u.is_active === false ? "Account reactivated" : "Account locked",
      () => api.patch(`/admin/users/${u.id}/active`, { is_active: u.is_active === false }),
      u.id,
    );

  const resetPassword = (u) => {
    const pw = window.prompt(`Set a temporary password for ${u.full_name || u.email}. They must change it on next login.`);
    if (!pw) return;
    return runMutation(
      "Password reset",
      () => api.post(`/admin/users/${u.id}/password`, { new_password: pw }),
      u.id,
    );
  };

  const deleteUser = (u) => {
    if (!window.confirm(`Permanently delete ${u.email}? This cannot be undone.`)) return;
    setBusyId(u.id);
    api.delete(`/admin/users/${u.id}`)
      .then(() => { toast.success("User deleted."); loadUsers(); })
      .catch((e) => toast.error(e?.response?.data?.detail || "Delete failed."))
      .finally(() => setBusyId(null));
  };

  const saveMatrix = async () => {
    if (!isExec) return;
    try {
      await api.patch("/admin/rbac/matrix", { matrix });
      setMatrixDirty(false);
      toast.success("Privilege matrix saved.");
      loadMatrix();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Matrix save failed.");
    }
  };

  const togglePerm = (role, perm) => {
    setMatrix((m) => {
      const next = JSON.parse(JSON.stringify(m || {}));
      next[role] = next[role] || {};
      next[role][perm] = !next[role][perm];
      return next;
    });
    setMatrixDirty(true);
  };

  const sortedUsers = useMemo(
    () => [...users].sort((a, b) => (ROLE_RANK[b.role] ?? 0) - (ROLE_RANK[a.role] ?? 0)),
    [users],
  );

  return (
    <div className="min-h-screen bg-bone text-ink">
      {/* Header */}
      <header className="border-b border-ink/10 bg-white sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-6 py-5 flex items-center justify-between gap-4 flex-wrap">
          <div className="flex items-center gap-3">
            <div className="w-11 h-11 rounded-lg bg-ink text-signal flex items-center justify-center">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div>
              <div className="overline text-copper leading-none">Executive Control</div>
              <h1 className="font-heading font-bold text-xl leading-tight">Identity & Access Management</h1>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setTab("users")}
              className={`px-4 py-2 text-sm font-bold rounded-sm border transition-colors ${tab === "users" ? "bg-ink text-white border-ink" : "bg-white border-ink/20 hover:border-ink"}`}
            >
              <Users className="w-4 h-4 inline mr-1.5" /> Users
            </button>
            {isExec && (
              <button
                onClick={() => setTab("matrix")}
                className={`px-4 py-2 text-sm font-bold rounded-sm border transition-colors ${tab === "matrix" ? "bg-ink text-white border-ink" : "bg-white border-ink/20 hover:border-ink"}`}
              >
                <Grid3X3 className="w-4 h-4 inline mr-1.5" /> Privilege Matrix
              </button>
            )}
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {tab === "users" ? (
          <>
            {/* Search / filter bar */}
            <div className="flex items-center gap-3 mb-6 flex-wrap">
              <div className="flex-1 min-w-[240px] relative">
                <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-ink/40" />
                <input
                  value={q}
                  onChange={(e) => setQ(e.target.value)}
                  placeholder="Search by name or email…"
                  className="w-full pl-9 pr-3 py-2.5 border border-ink/15 rounded-sm bg-white text-sm focus:outline-none focus:border-copper"
                />
              </div>
              <select
                value={roleFilter}
                onChange={(e) => setRoleFilter(e.target.value)}
                className="py-2.5 px-3 border border-ink/15 rounded-sm bg-white text-sm focus:outline-none focus:border-copper"
              >
                <option value="">All roles</option>
                {ROLES_ALL.map((r) => (
                  <option key={r} value={r}>{ROLE_LABELS[r]}</option>
                ))}
              </select>
              <button onClick={loadUsers} className="btn-ghost text-sm inline-flex items-center gap-1.5">
                <RefreshCw className="w-4 h-4" /> Refresh
              </button>
            </div>

            {/* Users table */}
            <div className="bg-white border border-ink/10 rounded-sm overflow-hidden">
              <div className="grid grid-cols-[1fr_auto_auto_auto] gap-3 px-4 py-2.5 bg-ink text-white text-[10px] font-black uppercase tracking-widest">
                <span>User</span>
                <span>Role / Tier</span>
                <span>Status</span>
                <span className="text-right">Actions</span>
              </div>
              {loading ? (
                <div className="p-12 text-center text-ink/50 flex items-center justify-center gap-2">
                  <Loader2 className="w-4 h-4 animate-spin" /> Loading users…
                </div>
              ) : sortedUsers.length === 0 ? (
                <div className="p-12 text-center text-ink/50">No users match your filters.</div>
              ) : (
                <div className="divide-y divide-ink/5">
                  {sortedUsers.map((u) => {
                    const canTouch = canModifyRole(me?.role, u.role) && u.id !== me?.id;
                    return (
                      <div key={u.id} className="grid grid-cols-[1fr_auto_auto_auto] gap-3 px-4 py-3 items-center hover:bg-bone/60">
                        <div className="min-w-0">
                          <div className="font-bold text-sm truncate">{u.full_name || "—"}</div>
                          <div className="text-xs text-ink/50 truncate">{u.email}</div>
                          {u.associate && <div className="text-[11px] text-copper font-bold">{u.associate}</div>}
                        </div>
                        <div>
                          <span className={`text-[11px] font-black px-2 py-1 rounded-sm ${ROLE_COLORS[u.role] || "bg-ink/10"}`}>
                            {ROLE_LABELS[u.role] || u.role}
                          </span>
                          <div className="text-[10px] text-ink/40 mt-0.5 text-center">{u.feature_tier || "free"}</div>
                        </div>
                        <div>
                          {u.is_active === false ? (
                            <span className="inline-flex items-center gap-1 text-[11px] font-bold text-destructive"><Ban className="w-3 h-3" /> Locked</span>
                          ) : (
                            <span className="inline-flex items-center gap-1 text-[11px] font-bold text-emerald-700"><CircleCheck className="w-3 h-3" /> Active</span>
                          )}
                        </div>
                        <div className="flex items-center justify-end gap-1.5">
                          {/* Role dropdown = privilege matrix single-cell elevation */}
                          <select
                            value={u.role}
                            disabled={!canTouch || busyId === u.id}
                            onChange={(e) => changeRole(u, e.target.value)}
                            className="py-1.5 px-2 border border-ink/15 rounded-sm text-xs bg-white focus:outline-none disabled:opacity-40"
                            title="Elevate / demote role"
                          >
                            {ROLES_ALL.filter((r) => canModifyRole(me?.role, r)).map((r) => (
                              <option key={r} value={r}>{ROLE_LABELS[r]}</option>
                            ))}
                          </select>
                          <button
                            onClick={() => resetPassword(u)}
                            disabled={!canTouch || busyId === u.id}
                            className="p-1.5 border border-ink/15 rounded-sm hover:border-copper disabled:opacity-40"
                            title="Send password reset"
                          >
                            <KeyRound className="w-3.5 h-3.5" />
                          </button>
                          <button
                            onClick={() => toggleActive(u)}
                            disabled={!canTouch || busyId === u.id}
                            className="p-1.5 border border-ink/15 rounded-sm hover:border-copper disabled:opacity-40"
                            title={u.is_active === false ? "Reactivate" : "Lock account"}
                          >
                            {u.is_active === false ? <CircleCheck className="w-3.5 h-3.5" /> : <Ban className="w-3.5 h-3.5" />}
                          </button>
                          <button
                            onClick={() => deleteUser(u)}
                            disabled={!canTouch || busyId === u.id}
                            className="p-1.5 border border-ink/15 rounded-sm hover:border-destructive hover:text-destructive disabled:opacity-40"
                            title="Delete user"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                          {verifyingId === u.id && <Loader2 className="w-4 h-4 animate-spin text-copper" />}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            <p className="text-xs text-ink/50 mt-4 flex items-center gap-1.5">
              <ShieldCheck className="w-3.5 h-3.5 text-copper" />
              Atomic enforcement: every change is followed by a secondary GET that re-reads the database before the row updates. Your own account cannot be modified here.
            </p>
          </>
        ) : (
          /* ── Privilege matrix ── */
          <div className="bg-white border border-ink/10 rounded-sm">
            <div className="px-5 py-4 border-b border-ink/10 flex items-center justify-between">
              <div>
                <h2 className="font-heading font-bold text-lg">Privilege Matrix</h2>
                <p className="text-sm text-ink/50">Toggle exactly what each role may do. Persisted to the platform config store.</p>
              </div>
              <button
                onClick={saveMatrix}
                disabled={!matrixDirty}
                className="btn-copper text-sm disabled:opacity-40"
              >
                Save Matrix
              </button>
            </div>
            {matrix === null ? (
              <div className="p-12 text-center text-ink/50">Loading matrix…</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="bg-bone text-left">
                      <th className="px-4 py-3 text-[10px] font-black uppercase tracking-widest text-ink/50">Permission</th>
                      {ROLES_ALL.map((r) => (
                        <th key={r} className="px-4 py-3 text-center text-[10px] font-black uppercase tracking-widest">{ROLE_LABELS[r]}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-ink/5">
                    {PERMISSION_KEYS.map((perm) => (
                      <tr key={perm} className="hover:bg-bone/50">
                        <td className="px-4 py-2.5 font-medium">{PERMISSION_LABELS[perm]}</td>
                        {ROLES_ALL.map((r) => {
                          const on = matrix[r]?.[perm];
                          return (
                            <td key={r} className="px-4 py-2.5 text-center">
                              <button
                                onClick={() => togglePerm(r, perm)}
                                className={`w-9 h-5 rounded-full relative transition-colors ${on ? "bg-copper" : "bg-ink/15"}`}
                                title={`${ROLE_LABELS[r]}: ${PERMISSION_LABELS[perm]}`}
                              >
                                <span className={`absolute top-0.5 w-4 h-4 rounded-full bg-white transition-all ${on ? "left-[18px]" : "left-0.5"}`} />
                              </button>
                            </td>
                          );
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
