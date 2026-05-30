/**
 * MORE Help Center — unified entry point
 *
 * Three render modes, determined automatically:
 *   greeter — unauthenticated or student/instructor (public-facing welcome)
 *   exec    — admin / executive_admin (all greeter content + embedded Supervisor controls)
 *   decoy   — API unreachable (friendly offline page, static, no API calls)
 *
 * All section visibility is group-toggled by role, never per-user hard-coding.
 */

import { useEffect, useState, useCallback } from "react";
import { Link } from "react-router-dom";
import {
  Heart, BookOpen, MessageSquare, ArrowRight, Phone, Shield, Users, Globe,
  Activity, BadgeCheck, ShieldCheck, Sparkles, MapPin,
  Send, Eye, EyeOff, Crown,
} from "lucide-react";
import { api, BACKEND_URL } from "../lib/api";
import { useAuth } from "../lib/auth";

// ── Legacy tokens (kept for ExecPanel internal use) ───────────────────────────
const GOLD        = "#e8b83e";
const TEAL        = "#0d7377";
const TEAL_DARK   = "#095b5e";
const WARM        = "#f9f5f0";
const CREAM       = "#fff8f0";
const SUPPORT_EMAIL = "morehelpcenter@gmail.com";

// ── African Marketplace palette ────────────────────────────────────────────────
const MARKET_BG   = "#FFF8EC";   // page background, warm cream
const FOREST      = "#2D6A4F";   // primary brand green
const GROVE       = "#1B4332";   // Legal Clearing, deep forest
const AMBER       = "#E8A51E";   // accents, highlights
const COPPER      = "#C47A1E";   // section headers, carved symbols
const EARTH       = "#8B4513";   // borders, depth
const TERRACOTTA  = "#C1440E";   // CTA buttons, feature cards
const BARK        = "#3E2723";   // text, carved header lines
const SAND        = "#F5DEB3";   // card backgrounds
const CARVED_BG   = "#FFF1DC";   // organic card fill

// ── Role helpers ───────────────────────────────────────────────────────────────
const ROLE_RANK = { student: 1, instructor: 2, admin: 3, executive_admin: 4 };
function hasRank(user, min) { return (ROLE_RANK[user?.role] ?? 0) >= min; }
const isExec    = (u) => hasRank(u, 3);
const isSupExec = (u) => hasRank(u, 4);

// ── Static content ─────────────────────────────────────────────────────────────
const FEATURES = [
  { icon: BookOpen,      title: "Free Learning",       desc: "Hands-on training, free modules, and certification pathways — no paywall at the door." },
  { icon: MessageSquare, title: "Community Support",   desc: "Ask questions, share knowledge, and get real answers from real people in your community." },
  { icon: Shield,        title: "Legal & Compliance",  desc: "Governance guidance, risk controls, and community-safe procedures built into every process." },
  { icon: Users,         title: "Community Market",    desc: "A virtual African market plaza where visitors discover services, training, and trusted allies." },
  { icon: Sparkles,      title: "Creative Production", desc: "Media, course-building, branding, and storytelling tools keep the hub vibrant and alive." },
  { icon: Activity,      title: "Autonomous Finance",  desc: "Self-managing finance operations run budgets, compliance, and expense flow for the center." },
];

const WAYPOINTS = [
  { icon: MapPin,     title: "Entrance Atrium",      desc: "Step in like a mall visitor and find the main path to finance, legal, and community services." },
  { icon: Users,      title: "Service Lanes",         desc: "Move through themed lanes for support, training, production, and marketplace discovery." },
  { icon: BadgeCheck, title: "Human Oversight Desk", desc: "Every AI-driven direction is backed by human review, audit, and executive supervision." },
  { icon: Globe,      title: "WAI Infrastructure",   desc: "This hub is connected to the full WAI system, from course catalogs to executive controls." },
];

const ROLE_LANES = [
  { icon: Globe,       title: "Visitor lane",    desc: "Public guests are guided to support, community learning, and marketplace discovery." },
  { icon: Activity,    title: "Operator lane",   desc: "Platform operators manage service routing, compliance checks, and live response workflows." },
  { icon: BadgeCheck,  title: "Supervisor lane", desc: "Supervisors review AI suggestions, coordinate escalations, and maintain executive visibility." },
  { icon: ShieldCheck, title: "Auditor lane",    desc: "Auditors verify governance, privacy, and finance decisions with transparent records." },
];

const NAV_LINKS = [
  { label: "Free Modules", to: "/modules" },
  { label: "Community",    to: "/community" },
  { label: "Courses",      to: "/courses" },
  { label: "Help Center",  to: "/help-center" },
  { label: "Store",        to: "/store" },
  { label: "Plans",        to: "/plans" },
];

const SUPERVISOR_TOGGLES = [
  { label: "Visitor Access",   href: "/more-help-center", description: "Browse public help resources and community support without signing in.", bg: "#f6d06d", color: "#1a1a2e" },
  { label: "Supervisor Login", href: "/login",            description: "Authenticate as an executive supervisor to access secure MORE Help Center controls.", bg: GROVE, color: "white" },
];

const PANEL_MODES = [
  { id: "exec",    label: "Exec Mode",    description: "Executive controls, monitoring, and audit-ready command links." },
  { id: "greeter", label: "Greeter Mode", description: "Warm public greeting flow for visitors and guided help navigation." },
  { id: "decoy",   label: "Decoy Mode",   description: "Fallback content and messaging when the main experience is down." },
];

const MODE_DETAILS = {
  exec: {
    title: "Executive Command Mode",
    summary: "This mode surfaces executive oversight workflows, live status, and privileged admin actions.",
    action: "Review platform health, audit pipelines, and secure escalation workflows.",
    links: [
      { label: "Admin System",  to: "/admin/system" },
      { label: "M.O.R.E. Admin", to: "/more/admin" },
      { label: "M.O.R.E. Ops", to: "/more/ops" },
      { label: "Audit Log",     to: "/admin/audit" },
    ],
  },
  greeter: {
    title: "Greeter / Visitor Mode",
    summary: "Use this mode to welcome visitors, route them to help resources, and keep the page calm and clear.",
    action: "Guide people to the MORE Help Center, community support, and public learning paths.",
    links: [
      { label: "MORE Help Center", to: "/more-help-center" },
      { label: "Courses",          to: "/courses" },
      { label: "Community",        to: "/community" },
    ],
  },
  decoy: {
    title: "Decoy / Fallback Mode",
    summary: "Activate this mode when the main experience is unavailable so the page still looks alive and helpful.",
    action: "Offer a credible fallback experience, point users to core resources, and preserve trust.",
    links: [
      { label: "MORE Help Center", to: "/more-help-center" },
      { label: "Help Desk",        to: "/help-center" },
      { label: "Login",            to: "/login" },
    ],
  },
};

// ── Carved section header ──────────────────────────────────────────────────────
function CarvedHeader({ label }) {
  return (
    <div style={{ fontSize: 11, fontWeight: 800, textTransform: "uppercase", letterSpacing: "0.2em", color: COPPER, marginBottom: 6, fontFamily: "Georgia, serif", borderBottom: `2px solid ${TERRACOTTA}`, paddingBottom: 4, display: "inline-block" }}>
      ✦ {label}
    </div>
  );
}

// ── Decoy Mode ─────────────────────────────────────────────────────────────────
function DecoyMode() {
  return (
    <div style={{ minHeight: "100vh", background: GROVE, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: 32, textAlign: "center" }}>
      <div style={{ width: 64, height: 64, borderRadius: "50%", background: AMBER, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 28, fontWeight: 900, color: BARK, marginBottom: 24 }}>M</div>
      <h1 style={{ color: "white", fontSize: 36, fontWeight: 900, marginBottom: 12, fontFamily: "Georgia, serif" }}>MORE Help Center</h1>
      <p style={{ color: "#c8e6c9", fontSize: 18, maxWidth: 480, lineHeight: 1.6, marginBottom: 8 }}>
        We're temporarily offline for maintenance. Our team is working on it.
      </p>
      <p style={{ color: "#c8e6c9", fontSize: 14, marginBottom: 32 }}>
        All your data is safe. We'll be back shortly.
      </p>
      <a href={`mailto:${SUPPORT_EMAIL}`} style={{ background: AMBER, color: BARK, padding: "12px 28px", borderRadius: 4, fontWeight: 700, fontSize: 14, textDecoration: "none", display: "inline-block" }}>
        Email Support
      </a>
      <p style={{ color: "rgba(255,255,255,0.3)", marginTop: 40, fontSize: 12 }}>WAI-Institute · MORE Help Center</p>
    </div>
  );
}

// ── Role constants for user DB inside panel ────────────────────────────────────
const PANEL_ROLES      = ["student", "instructor", "admin", "executive_admin"];
const PANEL_ROLE_LABELS= { student:"Student", instructor:"Instructor", admin:"Admin", executive_admin:"Exec Admin" };

// ── Exec Supervisor Control Panel ──────────────────────────────────────────────
function ExecPanel({ apiOnline, visibility, setVisibility, superExec }) {
  const [tab, setTab]               = useState("health");
  const [health, setHealth]         = useState(null);
  // ── users ──────────────────────────────────────────────────────────────────
  const [users, setUsers]           = useState([]);
  const [userQ, setUserQ]           = useState("");
  const [userRoleFilter, setUserRoleFilter] = useState("");
  const [userActiveFilter, setUserActiveFilter] = useState("");
  const [editing, setEditing]       = useState(null);   // user being edited
  const [creating, setCreating]     = useState(false);
  const [promoting, setPromoting]   = useState({});
  // ── edit modal state ───────────────────────────────────────────────────────
  const [editName, setEditName]         = useState("");
  const [editEmail, setEditEmail]       = useState("");
  const [editRole, setEditRole]         = useState("student");
  const [editPw, setEditPw]             = useState("");
  const [editShowPw, setEditShowPw]     = useState(false);
  const [editResetLink, setEditResetLink] = useState(null);
  const [editUserIncidents, setEditUserIncidents] = useState([]);
  const [editUserAudit, setEditUserAudit]         = useState([]);
  const [editHistoryLoaded, setEditHistoryLoaded] = useState(false);
  // ── create modal state ─────────────────────────────────────────────────────
  const [newName, setNewName]       = useState("");
  const [newEmail, setNewEmail]     = useState("");
  const [newRole, setNewRole]       = useState("student");
  const [newPw, setNewPw]           = useState("");
  const [newShowPw, setNewShowPw]   = useState(false);
  const [newResetLink, setNewResetLink] = useState(null);
  const [newCreated, setNewCreated] = useState(null);
  // ── other tabs ─────────────────────────────────────────────────────────────
  const [incidents, setIncidents]   = useState([]);
  const [resolvingId, setResolvingId] = useState(null);
  const [resolveText, setResolveText] = useState("");
  const [auditLog, setAuditLog]     = useState([]);
  const [auditActionQ, setAuditActionQ] = useState("");
  const [auditActorQ, setAuditActorQ]   = useState("");
  const [auditLimit, setAuditLimit]     = useState(50);
  const [sageAuditLog, setSageAuditLog] = useState([]);
  const [sageAuditKind, setSageAuditKind] = useState("all");
  const [sageAuditUid, setSageAuditUid]   = useState("");
  const [broadcastMsg, setBroadcast]    = useState("");
  const [broadcastTitle, setBcastTitle] = useState("");
  const [broadcastTarget, setBcastTarget] = useState("all");
  const [sending, setSending]       = useState(false);
  const [gwStatus, setGwStatus]     = useState(null);
  const [apiKeys, setApiKeys]       = useState({});
  const [showKeys, setShowKeys]     = useState({});
  const [sysInfo, setSysInfo]       = useState(null);
  const [sysStats, setSysStats]     = useState(null);
  const [sageStatus, setSageStatus] = useState(null);
  const [capLevel, setCapLevel]     = useState("");
  const [capOverrides, setCapOverrides] = useState([]);
  const [capOverrideUid, setCapOverrideUid] = useState("");
  const [capOverrideLvl, setCapOverrideLvl] = useState("standard");
  const [loading, setLoading]       = useState(false);
  const [notice, setNotice]         = useState("");
  // ── gateway controls ───────────────────────────────────────────────────────
  const [budgetCap, setBudgetCap]         = useState("");
  const [gwRanking, setGwRanking]         = useState(null);
  // ── failover tab ───────────────────────────────────────────────────────────
  const [backupMatrix, setBackupMatrix]   = useState(null);
  const [failoverTarget, setFailoverTarget] = useState("backup");
  const [failoverReason, setFailoverReason] = useState("");
  const [heartbeatSecret, setHeartbeatSecret] = useState(null);
  const [breakerPanel, setBreakerPanel]   = useState(null);
  const [panelHealth, setPanelHealth]     = useState(null);
  const [platformFlags, setPlatformFlags] = useState(null);
  // ── mode switcher (exec/greeter/decoy) ─────────────────────────────────────
  const [pageMode, setPageMode]     = useState(() => {
    try { return localStorage.getItem("more_help_center_mode") || "greeter"; } catch { return "greeter"; }
  });
  const PAGE_MODES = [
    { id:"exec",    label:"Exec Mode",    desc:"Executive controls, monitoring, and audit-ready command links." },
    { id:"greeter", label:"Greeter Mode", desc:"Warm public greeting flow for visitors and guided help navigation." },
    { id:"decoy",   label:"Decoy Mode",   desc:"Fallback content and messaging when the main experience is down." },
  ];

  const notify = (msg) => {
    setNotice(msg);
    setTimeout(() => setNotice(""), 3500);
  };

  const loadHealth = useCallback(async () => {
    setLoading(true);
    try { const r = await api.get("/health"); setHealth(r.data); } catch { setHealth(null); }
    try { const r = await api.get("/exec/system"); setSysInfo(r.data); } catch {}
    try { const r = await api.get("/admin/sage/status"); setSageStatus(r.data); } catch {}
    try { const r = await api.get("/admin/stats"); setSysStats(r.data); } catch {}
    finally { setLoading(false); }
  }, []);

  const loadGateway = useCallback(async () => {
    try {
      const r = await api.get("/admin/gateway/status");
      setGwStatus(r.data);
      if (r.data?.budget?.hourly_cap) setBudgetCap(String(r.data.budget.hourly_cap));
    } catch {}
    try {
      const r2 = await api.get("/admin/gateway/ranking");
      setGwRanking(r2.data);
    } catch {}
  }, []);

  const loadUsers = useCallback(async (q, role, active) => {
    try {
      const params = new URLSearchParams();
      if (q)      params.set("q", q);
      if (role)   params.set("role", role);
      if (active) params.set("active", active);
      const r = await api.get(`/admin/users?${params}`);
      setUsers(Array.isArray(r.data) ? r.data : []);
    } catch {}
  }, []);

  const loadBackupMatrix = useCallback(async () => {
    try { const r = await api.get("/exec/free-backup-matrix"); setBackupMatrix(r.data); } catch {}
    try { const r = await api.get("/exec/panel"); setBreakerPanel(r.data); } catch {}
    try { const r = await api.get("/exec/panel/health"); setPanelHealth(r.data); } catch {}
    try { const r = await api.get("/admin/platform/flags"); setPlatformFlags(r.data?.flags || {}); } catch {}
  }, []);

  const loadIncidents = useCallback(async () => {
    try {
      const r = await api.get("/incidents?status=open");
      setIncidents(Array.isArray(r.data) ? r.data.slice(0, 20) : []);
    } catch {}
  }, []);

  const loadAudit = useCallback(async (action, actorId, limit) => {
    const params = new URLSearchParams({ limit: limit || 50 });
    if (action) params.set("action", action);
    if (actorId) params.set("actor_id", actorId);
    try { const r = await api.get(`/admin/audit?${params}`); setAuditLog(Array.isArray(r.data) ? r.data : []); } catch {}
  }, []);

  const loadSageAudit = useCallback(async (kind, uid) => {
    const params = new URLSearchParams({ kind: kind || "all", limit: 50 });
    if (uid) params.set("user_id", uid);
    try { const r = await api.get(`/admin/sage/audit?${params}`); setSageAuditLog(Array.isArray(r.data) ? r.data : []); } catch {}
  }, []);

  const loadSageCap = useCallback(async () => {
    try {
      const r = await api.get("/admin/sage/cap");
      setCapLevel(r.data?.global_level || "");
      setCapOverrides(Array.isArray(r.data?.overrides) ? r.data.overrides : []);
    } catch {}
  }, []);

  useEffect(() => {
    loadHealth();
    loadGateway();
  }, [loadHealth, loadGateway]);

  useEffect(() => {
    if (tab === "users")     loadUsers(userQ, userRoleFilter, userActiveFilter);
    if (tab === "incidents") loadIncidents();
    if (tab === "audit")     { loadAudit(auditActionQ, auditActorQ, auditLimit); if (superExec) loadSageAudit(sageAuditKind, sageAuditUid); }
    if (tab === "safety")    loadSageCap();
    if (tab === "failover")  loadBackupMatrix();
  }, [tab, loadUsers, loadIncidents, loadAudit, loadSageAudit, loadSageCap, loadBackupMatrix, userQ, userRoleFilter, userActiveFilter, auditActionQ, auditActorQ, auditLimit, sageAuditKind, sageAuditUid, superExec]);

  // ── User governance actions ────────────────────────────────────────────────
  function openEdit(u) {
    setEditing(u);
    setEditName(u.full_name || "");
    setEditEmail(u.email || "");
    setEditRole(u.role || "student");
    setEditPw("");
    setEditShowPw(false);
    setEditResetLink(null);
    setEditUserIncidents([]);
    setEditUserAudit([]);
    setEditHistoryLoaded(false);
    // load incidents and audit for this user in background
    api.get("/incidents").then(r => {
      const all = Array.isArray(r.data) ? r.data : [];
      setEditUserIncidents(all.filter(i => i.reported_by === u.id || (i.involved_user_ids || []).includes(u.id)));
    }).catch(() => {});
    api.get("/admin/audit?limit=200").then(r => {
      const all = Array.isArray(r.data) ? r.data : [];
      setEditUserAudit(all.filter(a => a.actor_id === u.id || a.target === u.id));
      setEditHistoryLoaded(true);
    }).catch(() => { setEditHistoryLoaded(true); });
  }

  async function saveEdit() {
    if (!editing) return;
    try {
      await api.patch(`/admin/users/${editing.id}`, { full_name: editName, email: editEmail });
      if (editRole !== editing.role) await api.patch(`/admin/users/${editing.id}/role`, { role: editRole });
      if (editPw.trim()) await api.post(`/admin/users/${editing.id}/password`, { new_password: editPw });
      setUsers(prev => prev.map(x => x.id === editing.id ? { ...x, full_name: editName, email: editEmail, role: editRole } : x));
      notify(`${editName} updated`);
      setEditing(null);
    } catch (e) { notify(`Save failed: ${e?.response?.data?.detail || e.message}`); }
  }

  async function genEditResetLink() {
    if (!editing) return;
    try {
      const r = await api.post(`/admin/users/${editing.id}/reset-link`);
      setEditResetLink(r.data.reset_url || r.data.link || JSON.stringify(r.data));
    } catch (e) { notify(`Failed: ${e?.response?.data?.detail || e.message}`); }
  }

  async function toggleActive(u) {
    try {
      await api.patch(`/admin/users/${u.id}/active`, { is_active: u.is_active === false });
      setUsers(prev => prev.map(x => x.id === u.id ? { ...x, is_active: u.is_active === false } : x));
      notify(`${u.full_name || u.email} ${u.is_active === false ? "activated" : "deactivated"}`);
      setEditing(null);
    } catch (e) { notify(`Failed: ${e?.response?.data?.detail || e.message}`); }
  }

  async function deleteUser(u) {
    if (!window.confirm(`Permanently delete ${u.full_name || u.email}? Cannot be undone.`)) return;
    try {
      await api.delete(`/admin/users/${u.id}`);
      setUsers(prev => prev.filter(x => x.id !== u.id));
      notify(`${u.full_name || u.email} deleted`);
      setEditing(null);
    } catch (e) { notify(`Failed: ${e?.response?.data?.detail || e.message}`); }
  }

  async function quickRole(u, newRole) {
    setPromoting(p => ({ ...p, [u.id]: true }));
    try {
      await api.patch(`/admin/users/${u.id}/role`, { role: newRole });
      setUsers(prev => prev.map(x => x.id === u.id ? { ...x, role: newRole } : x));
      notify(`${u.full_name || u.email} → ${PANEL_ROLE_LABELS[newRole]}`);
    } catch (e) { notify(`Role change failed: ${e?.response?.data?.detail || e.message}`); }
    finally { setPromoting(p => ({ ...p, [u.id]: false })); }
  }

  async function createUser() {
    if (!newName.trim() || !newEmail.trim() || newPw.length < 8) {
      notify("Name, email, and password (min 8 chars) are required"); return;
    }
    try {
      const r = await api.post("/admin/users", { full_name: newName.trim(), email: newEmail.trim().toLowerCase(), password: newPw, role: newRole });
      const u = r.data;
      setUsers(prev => [u, ...prev]);
      setNewCreated(u);
      try {
        const lr = await api.post(`/admin/users/${u.id}/reset-link`);
        setNewResetLink(lr.data.reset_url || lr.data.link || null);
      } catch {}
      notify(`${newName} created`);
    } catch (e) { notify(`Create failed: ${e?.response?.data?.detail || e.message}`); }
  }

  // ── Failover actions ──────────────────────────────────────────────────────
  async function triggerFailover() {
    if (!failoverReason.trim()) { notify("Enter a reason before triggering failover"); return; }
    try {
      await api.post("/exec/failover", { target: failoverTarget, reason: failoverReason });
      notify(`Failover to ${failoverTarget} triggered`);
      setFailoverReason("");
    } catch (e) { notify(`Failover failed: ${e?.response?.data?.detail || e.message}`); }
  }

  async function loadHeartbeatSecret() {
    try {
      const r = await api.get("/exec/panel/heartbeat-secret");
      setHeartbeatSecret(r.data.secret);
    } catch (e) { notify(`Failed: ${e?.response?.data?.detail || e.message}`); }
  }

  async function setPlatformFlag(flag, value, reason) {
    try {
      await api.post(`/admin/platform/flags/${flag}`, { value, reason });
      notify(`${flag} set to ${value}`);
      const r = await api.get("/admin/platform/flags"); setPlatformFlags(r.data?.flags || {});
    } catch (e) { notify(`Flag failed: ${e?.response?.data?.detail || e.message}`); }
  }

  async function toggleBreaker(breakerId) {
    try {
      await api.post("/exec/panel/toggle", { breaker_id: breakerId });
      notify(`Breaker ${breakerId} toggled`);
      const r = await api.get("/exec/panel"); setBreakerPanel(r.data);
    } catch (e) { notify(`Toggle failed: ${e?.response?.data?.detail || e.message}`); }
  }

  async function resetBreaker(breakerId) {
    try {
      await api.post("/exec/panel/reset", { breaker_id: breakerId });
      notify(`Breaker ${breakerId} reset`);
      const r = await api.get("/exec/panel"); setBreakerPanel(r.data);
    } catch (e) { notify(`Reset failed: ${e?.response?.data?.detail || e.message}`); }
  }

  const sendBroadcast = async () => {
    if (!broadcastMsg.trim()) return;
    setSending(true);
    try {
      await api.post("/admin/broadcast", { message: broadcastMsg.trim(), title: broadcastTitle.trim() || "Platform Announcement", target: broadcastTarget });
      notify("Broadcast sent");
      setBroadcast("");
    } catch { notify("Broadcast failed", true); }
    finally { setSending(false); }
  };

  const setSafetyCap = async (level) => {
    try {
      await api.put("/admin/sage/cap/global", { level: level || null });
      setCapLevel(level);
      notify(`Safety cap set: ${level || "cleared"}`);
    } catch { notify("Failed to set cap", true); }
  };

  const setUserCapOverride = async (uid, level) => {
    if (!uid.trim()) { notify("Enter a user ID"); return; }
    try {
      await api.put(`/admin/sage/cap/user/${uid.trim()}`, { level: level || null });
      notify(`Per-user cap set for ${uid.trim()}: ${level || "cleared"}`);
      await loadSageCap();
    } catch (e) { notify(`User cap failed: ${e?.response?.data?.detail || e.message}`); }
  };

  const clearUserCapOverride = async (uid) => {
    try {
      await api.put(`/admin/sage/cap/user/${uid}`, { level: null });
      notify(`Cap override cleared for ${uid}`);
      await loadSageCap();
    } catch (e) { notify(`Clear failed: ${e?.response?.data?.detail || e.message}`); }
  };

  const pushApiKey = async (envKey, value) => {
    if (!value) return;
    try {
      await api.post("/admin/gateway/keys", { var_name: envKey, value });
      notify(`${envKey} pushed to gateway`);
      await loadGateway();
    } catch (e) { notify(`Failed to push ${envKey}: ${e?.response?.data?.detail || e.message}`); }
  };

  const [keyEnabled, setKeyEnabled] = useState({});

  const revokeApiKey = async (envKey) => {
    if (!window.confirm(`Revoke ${envKey}? This clears the key from the live gateway immediately.`)) return;
    try {
      await api.delete(`/admin/gateway/keys/${envKey}`);
      notify(`${envKey} revoked from gateway`);
      await loadGateway();
    } catch (e) { notify(`Revoke failed: ${e?.response?.data?.detail || e.message}`); }
  };

  const toggleApiKey = async (envKey, enable) => {
    try {
      await api.patch(`/admin/gateway/keys/${envKey}/toggle`, { enabled: enable });
      setKeyEnabled(s => ({ ...s, [envKey]: enable }));
      notify(`${envKey} ${enable ? "enabled" : "disabled"}`);
      await loadGateway();
    } catch (e) { notify(`Toggle failed: ${e?.response?.data?.detail || e.message}`); }
  };

  const saveBudgetCap = async () => {
    const cap = parseInt(budgetCap, 10);
    if (isNaN(cap) || cap < 1000) { notify("Minimum budget cap is 1,000 tokens"); return; }
    try {
      await api.patch("/admin/gateway/budget", { hourly_cap: cap });
      notify(`Hourly cap set to ${cap.toLocaleString()} tokens`);
      await loadGateway();
    } catch (e) { notify(`Budget update failed: ${e?.response?.data?.detail || e.message}`); }
  };

  const resetBudgetCounter = async () => {
    if (!window.confirm("Zero out the current-hour token counter? This lets the gateway accept new calls immediately.")) return;
    try {
      const r = await api.post("/admin/gateway/reset-budget");
      notify(`Token counter reset (was ${r.data.previous_tokens_used?.toLocaleString()})`);
      await loadGateway();
    } catch (e) { notify(`Reset failed: ${e?.response?.data?.detail || e.message}`); }
  };

  const moveRanking = async (index, dir) => {
    if (!gwRanking?.ranking) return;
    const arr = [...gwRanking.ranking];
    const swap = index + dir;
    if (swap < 0 || swap >= arr.length) return;
    [arr[index], arr[swap]] = [arr[swap], arr[index]];
    try {
      await api.patch("/admin/gateway/ranking", { ranking: arr });
      setGwRanking(r => ({ ...r, ranking: arr }));
      notify("Provider ranking updated");
    } catch (e) { notify(`Ranking update failed: ${e?.response?.data?.detail || e.message}`); }
  };

  const TABS = [
    { key: "health",     label: "Health" },
    { key: "gateway",    label: "Gateway" },
    { key: "users",      label: "Users" },
    { key: "broadcast",  label: "Broadcast" },
    { key: "incidents",  label: "Incidents" },
    { key: "safety",     label: "Safety Cap" },
    { key: "apikeys",    label: "API Keys" },
    { key: "audit",      label: "Audit Log" },
    { key: "visibility", label: "Visibility" },
    { key: "modes",      label: "Page Mode" },
    ...(superExec ? [{ key: "failover", label: "⚡ Failover" }] : []),
  ];

  const INK = "#2e1065";
  const SIG = "#FFD100";

  return (
    <div style={{ background: INK, borderRadius: 16, overflow: "hidden", boxShadow: "0 8px 40px rgba(0,0,0,0.4)", marginBottom: 32 }}>
      <div style={{ padding: "16px 24px", borderBottom: "1px solid rgba(255,255,255,0.1)", display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: 12 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <div style={{ width: 36, height: 36, borderRadius: "50%", background: SIG, display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 900, fontSize: 14, color: INK }}>S</div>
          <div>
            <div style={{ color: "white", fontWeight: 800, fontSize: 15 }}>Supervisor Panel</div>
            <div style={{ color: "rgba(255,255,255,0.45)", fontSize: 11 }}>Executive Control — MORE Help Center</div>
          </div>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <div style={{ width: 8, height: 8, borderRadius: "50%", background: apiOnline ? "#22c55e" : "#dc2626" }} />
          <span style={{ fontSize: 12, color: "rgba(255,255,255,0.6)" }}>{apiOnline ? "API online" : "API offline"}</span>
          <Link to="/admin/system" style={{ background: SIG, color: INK, padding: "5px 12px", borderRadius: 6, fontSize: 11, fontWeight: 700, textDecoration: "none", marginLeft: 8 }}>
            Full Dashboard →
          </Link>
        </div>
      </div>

      <div style={{ display: "flex", overflowX: "auto", borderBottom: "1px solid rgba(255,255,255,0.08)", padding: "0 16px" }}>
        {TABS.map(t => (
          <button key={t.key} onClick={() => setTab(t.key)}
            style={{ padding: "10px 14px", border: "none", background: "none", color: tab === t.key ? SIG : "rgba(255,255,255,0.55)", fontWeight: tab === t.key ? 700 : 500, fontSize: 12, cursor: "pointer", borderBottom: tab === t.key ? `2px solid ${SIG}` : "2px solid transparent", whiteSpace: "nowrap" }}>
            {t.label}
          </button>
        ))}
      </div>

      {notice && (
        <div style={{ margin: "12px 20px 0", background: "rgba(255,255,255,0.1)", borderRadius: 8, padding: "8px 14px", fontSize: 12, color: SIG }}>{notice}</div>
      )}

      <div style={{ padding: 20, minHeight: 220 }}>

        {tab === "health" && (
          <div>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16, flexWrap: "wrap", gap: 8 }}>
              <span style={{ color: "white", fontWeight: 700, fontSize: 14 }}>Platform Health</span>
              <div style={{ display: "flex", gap: 6 }}>
                <button onClick={loadHealth} disabled={loading} style={{ background: "rgba(255,255,255,0.1)", border: "none", color: "white", padding: "5px 12px", borderRadius: 6, fontSize: 11, cursor: "pointer" }}>
                  {loading ? "…" : "Refresh"}
                </button>
                <button onClick={async () => {
                  try { await api.post("/admin/run-checks"); notify("Escalation & engagement checks complete"); }
                  catch (e) { notify(`Checks failed: ${e?.response?.data?.detail || e.message}`); }
                }} style={{ background: "rgba(255,209,0,0.2)", border: "1px solid rgba(255,209,0,0.4)", color: SIG, padding: "5px 12px", borderRadius: 6, fontSize: 11, fontWeight: 700, cursor: "pointer" }}>
                  Run Checks
                </button>
              </div>
            </div>
            {health ? (
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(140px,1fr))", gap: 10, marginBottom: 20 }}>
                {Object.entries(health).filter(([k]) => typeof health[k] !== "object").map(([k, v]) => (
                  <div key={k} style={{ background: "rgba(255,255,255,0.07)", borderRadius: 8, padding: "10px 14px" }}>
                    <div style={{ color: "rgba(255,255,255,0.45)", fontSize: 10, textTransform: "uppercase", letterSpacing: 1 }}>{k}</div>
                    <div style={{ color: v === "up" || v === true ? "#22c55e" : v === "down" || v === false ? "#dc2626" : SIG, fontWeight: 700, fontSize: 13, marginTop: 4 }}>{String(v)}</div>
                  </div>
                ))}
              </div>
            ) : (
              <p style={{ color: "rgba(255,255,255,0.4)", fontSize: 13 }}>Click Refresh to run health check.</p>
            )}
            {sysStats && (
              <div style={{ background: "rgba(255,255,255,0.05)", borderRadius: 10, padding: "14px 18px", marginBottom: 14 }}>
                <div style={{ color: SIG, fontWeight: 700, fontSize: 12, textTransform: "uppercase", letterSpacing: 1, marginBottom: 10 }}>Platform Stats</div>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(130px,1fr))", gap: 8 }}>
                  {Object.entries(sysStats).filter(([,v]) => typeof v !== "object").map(([k, v]) => (
                    <div key={k} style={{ background: "rgba(255,255,255,0.06)", borderRadius: 6, padding: "6px 10px" }}>
                      <div style={{ color: "rgba(255,255,255,0.4)", fontSize: 9, textTransform: "uppercase", letterSpacing: 1 }}>{k.replace(/_/g," ")}</div>
                      <div style={{ color: "white", fontWeight: 700, fontSize: 13, marginTop: 2 }}>{String(v)}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
            {sysInfo && (
              <div style={{ background: "rgba(255,255,255,0.05)", borderRadius: 10, padding: "14px 18px" }}>
                <div style={{ color: SIG, fontWeight: 700, fontSize: 12, textTransform: "uppercase", letterSpacing: 1, marginBottom: 10 }}>System Info (Exec)</div>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(160px,1fr))", gap: 8, marginBottom: 10 }}>
                  <div style={{ background: "rgba(255,255,255,0.06)", borderRadius: 6, padding: "8px 12px" }}>
                    <div style={{ color: "rgba(255,255,255,0.4)", fontSize: 10, textTransform: "uppercase" }}>Version</div>
                    <div style={{ color: "white", fontSize: 12, fontWeight: 700, marginTop: 3, fontFamily: "monospace" }}>{sysInfo.version || "—"}</div>
                  </div>
                  <div style={{ background: "rgba(255,255,255,0.06)", borderRadius: 6, padding: "8px 12px" }}>
                    <div style={{ color: "rgba(255,255,255,0.4)", fontSize: 10, textTransform: "uppercase" }}>Audit Log Entries</div>
                    <div style={{ color: "white", fontSize: 12, fontWeight: 700, marginTop: 3 }}>{sysInfo.audit_log_total?.toLocaleString() || "—"}</div>
                  </div>
                  {sysInfo.env && Object.entries(sysInfo.env).map(([k, v]) => (
                    <div key={k} style={{ background: "rgba(255,255,255,0.06)", borderRadius: 6, padding: "8px 12px" }}>
                      <div style={{ color: "rgba(255,255,255,0.4)", fontSize: 10, textTransform: "uppercase" }}>{k.replace(/_/g, " ")}</div>
                      <div style={{ color: "white", fontSize: 11, fontWeight: 600, marginTop: 3, fontFamily: "monospace", wordBreak: "break-all" }}>{String(v)}</div>
                    </div>
                  ))}
                </div>
                {sysInfo.role_counts && (
                  <div>
                    <div style={{ color: "rgba(255,255,255,0.4)", fontSize: 10, textTransform: "uppercase", letterSpacing: 1, marginBottom: 6 }}>Role Distribution</div>
                    <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                      {Object.entries(sysInfo.role_counts).map(([role, count]) => (
                        <div key={role} style={{ background: "rgba(255,255,255,0.08)", borderRadius: 5, padding: "4px 10px", fontSize: 11 }}>
                          <span style={{ color: "rgba(255,255,255,0.6)", textTransform: "capitalize" }}>{role.replace("_", " ")}</span>
                          <span style={{ color: SIG, fontWeight: 800, marginLeft: 6 }}>{count}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
            {sageStatus && (
              <div style={{ background: "rgba(255,255,255,0.05)", borderRadius: 10, padding: "14px 18px", marginTop: 14 }}>
                <div style={{ color: SIG, fontWeight: 700, fontSize: 12, textTransform: "uppercase", letterSpacing: 1, marginBottom: 10 }}>Sage Integrity Status</div>
                <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 10 }}>
                  <div style={{ background: "rgba(255,255,255,0.06)", borderRadius: 6, padding: "6px 12px" }}>
                    <div style={{ color: "rgba(255,255,255,0.4)", fontSize: 10, textTransform: "uppercase" }}>Prompt Hash</div>
                    <div style={{ color: sageStatus.prompt_hash_status === "match" ? "#22c55e" : "#ef4444", fontWeight: 700, fontSize: 12, marginTop: 2, textTransform: "capitalize" }}>
                      {sageStatus.prompt_hash_status === "match" ? "✓ Match" : "✗ " + sageStatus.prompt_hash_status}
                    </div>
                  </div>
                  <div style={{ background: "rgba(255,255,255,0.06)", borderRadius: 6, padding: "6px 12px" }}>
                    <div style={{ color: "rgba(255,255,255,0.4)", fontSize: 10, textTransform: "uppercase" }}>Fallback</div>
                    <div style={{ color: sageStatus.fallback_active ? "#f87171" : "#22c55e", fontWeight: 700, fontSize: 12, marginTop: 2 }}>
                      {sageStatus.fallback_active ? "Active" : "Off"}
                    </div>
                  </div>
                  {sageStatus.modules && Object.entries(sageStatus.modules).map(([mod, status]) => (
                    <div key={mod} style={{ background: "rgba(255,255,255,0.06)", borderRadius: 6, padding: "6px 12px" }}>
                      <div style={{ color: "rgba(255,255,255,0.4)", fontSize: 10, textTransform: "uppercase" }}>Module {mod}</div>
                      <div style={{ color: status === "present" ? "#22c55e" : "#ef4444", fontWeight: 700, fontSize: 12, marginTop: 2, textTransform: "capitalize" }}>{status}</div>
                    </div>
                  ))}
                </div>
                {sageStatus.last_audit_id && (
                  <div style={{ color: "rgba(255,255,255,0.35)", fontSize: 10, fontFamily: "monospace" }}>Last audit ID: {sageStatus.last_audit_id}</div>
                )}
              </div>
            )}
          </div>
        )}

        {tab === "gateway" && (
          <div>
            <div style={{ color: "white", fontWeight: 700, fontSize: 14, marginBottom: 14 }}>LLM Gateway Controls</div>

            {/* Provider status grid */}
            {gwStatus ? (
              <div>
                <div style={{ color: SIG, fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: 1, marginBottom: 8 }}>Provider Status</div>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(160px,1fr))", gap: 10, marginBottom: 18 }}>
                  {Object.entries(gwStatus.providers || {}).map(([name, p]) => (
                    <div key={name} style={{ background: "rgba(255,255,255,0.07)", borderRadius: 8, padding: "10px 14px" }}>
                      <div style={{ color: "white", fontWeight: 700, fontSize: 13, textTransform: "capitalize" }}>{name}</div>
                      <div style={{ color: p.available ? "#22c55e" : "#dc2626", fontSize: 11, marginTop: 3 }}>
                        {p.available ? "✓ Active" : "✗ No key"}
                      </div>
                      <div style={{ color: SIG, fontSize: 10, marginTop: 2 }}>Tier {p.tier} · {p.cost}</div>
                    </div>
                  ))}
                </div>

                {/* Budget controls */}
                {gwStatus.budget && (
                  <div style={{ background: "rgba(255,255,255,0.06)", borderRadius: 8, padding: "12px 16px", marginBottom: 18 }}>
                    <div style={{ color: SIG, fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: 1, marginBottom: 8 }}>Hourly Token Budget</div>
                    <div style={{ fontSize: 12, color: "rgba(255,255,255,0.6)", marginBottom: 10 }}>
                      Used: {gwStatus.budget.tokens_used?.toLocaleString()} / {gwStatus.budget.hourly_cap?.toLocaleString()} tokens ({gwStatus.budget.budget_pct}%)
                      {gwStatus.budget.over_budget && <span style={{ color: "#dc2626", marginLeft: 8, fontWeight: 700 }}>⚠ OVER BUDGET</span>}
                    </div>
                    <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
                      <input
                        type="number"
                        value={budgetCap || gwStatus.budget.hourly_cap || ""}
                        onChange={e => setBudgetCap(e.target.value)}
                        placeholder="tokens/hour"
                        style={{ background: "rgba(255,255,255,0.1)", border: "1px solid rgba(255,255,255,0.2)", borderRadius: 6, padding: "6px 10px", color: "white", fontSize: 12, width: 140, outline: "none" }}
                      />
                      <button onClick={saveBudgetCap}
                        style={{ background: SIG, border: "none", color: INK, padding: "6px 14px", borderRadius: 6, fontSize: 11, fontWeight: 800, cursor: "pointer" }}>
                        Set Cap
                      </button>
                      <button onClick={resetBudgetCounter}
                        style={{ background: "rgba(220,38,38,0.25)", border: "none", color: "#f87171", padding: "6px 14px", borderRadius: 6, fontSize: 11, fontWeight: 800, cursor: "pointer" }}>
                        Reset Counter
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <p style={{ color: "rgba(255,255,255,0.4)", fontSize: 13 }}>Loading gateway status…</p>
            )}

            {/* Provider ranking */}
            <div style={{ background: "rgba(255,255,255,0.06)", borderRadius: 8, padding: "12px 16px", marginBottom: 14 }}>
              <div style={{ color: SIG, fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: 1, marginBottom: 6 }}>Provider Priority Order (Free-First)</div>
              <div style={{ color: "rgba(255,255,255,0.4)", fontSize: 10, marginBottom: 10 }}>
                Soft preference stored in DB. Use API Keys tab to push/revoke/disable providers to enforce hard routing.
              </div>
              {gwRanking?.ranking ? (
                <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                  {gwRanking.ranking.map((prov, i) => (
                    <div key={prov} style={{ display: "flex", alignItems: "center", gap: 8, background: "rgba(255,255,255,0.05)", borderRadius: 6, padding: "6px 10px" }}>
                      <span style={{ color: SIG, fontWeight: 800, fontSize: 11, width: 20 }}>#{i + 1}</span>
                      <span style={{ color: "white", fontSize: 12, flex: 1, textTransform: "capitalize" }}>{prov}</span>
                      <button onClick={() => moveRanking(i, -1)} disabled={i === 0}
                        style={{ background: "none", border: "none", color: i === 0 ? "rgba(255,255,255,0.2)" : "rgba(255,255,255,0.6)", fontSize: 14, cursor: i === 0 ? "default" : "pointer", padding: "0 4px" }}>▲</button>
                      <button onClick={() => moveRanking(i, 1)} disabled={i === gwRanking.ranking.length - 1}
                        style={{ background: "none", border: "none", color: i === gwRanking.ranking.length - 1 ? "rgba(255,255,255,0.2)" : "rgba(255,255,255,0.6)", fontSize: 14, cursor: i === gwRanking.ranking.length - 1 ? "default" : "pointer", padding: "0 4px" }}>▼</button>
                    </div>
                  ))}
                </div>
              ) : (
                <p style={{ color: "rgba(255,255,255,0.4)", fontSize: 12 }}>Loading ranking…</p>
              )}
            </div>

            <button onClick={loadGateway} style={{ background: "rgba(255,255,255,0.1)", border: "none", color: "white", padding: "5px 12px", borderRadius: 6, fontSize: 11, cursor: "pointer" }}>
              Refresh Status
            </button>
          </div>
        )}

        {tab === "users" && (
          <div>
            {/* ── Create modal ── */}
            {creating && (
              <div style={{ position:"fixed", inset:0, zIndex:200, background:"rgba(0,0,0,0.7)", display:"flex", alignItems:"center", justifyContent:"center", padding:16 }}
                onClick={e => e.target === e.currentTarget && setCreating(false)}>
                <div style={{ background:"white", borderRadius:16, width:"100%", maxWidth:480, overflow:"hidden" }}>
                  <div style={{ padding:"14px 20px", borderBottom:"1px solid #e5e7eb", display:"flex", justifyContent:"space-between", alignItems:"center" }}>
                    <span style={{ fontWeight:800, color:"#1e293b" }}>Create New Account</span>
                    <button onClick={() => { setCreating(false); setNewCreated(null); setNewResetLink(null); }} style={{ border:"none", background:"none", fontSize:20, cursor:"pointer", color:"#64748b" }}>×</button>
                  </div>
                  {newCreated ? (
                    <div style={{ padding:20 }}>
                      <div style={{ color:"#166534", fontWeight:700, marginBottom:8 }}>✓ {newCreated.full_name} created as {PANEL_ROLE_LABELS[newCreated.role]}</div>
                      {newResetLink && (
                        <div style={{ background:"#fefce8", border:"1px solid #fde68a", borderRadius:8, padding:12, marginTop:8 }}>
                          <div style={{ fontSize:11, fontWeight:700, color:"#92400e", marginBottom:4 }}>One-time login link:</div>
                          <div style={{ fontSize:11, fontFamily:"monospace", wordBreak:"break-all", color:"#78350f" }}>{newResetLink}</div>
                          <button onClick={() => navigator.clipboard?.writeText(newResetLink)} style={{ marginTop:6, fontSize:11, color:"#b45309", fontWeight:700, border:"none", background:"none", cursor:"pointer" }}>Copy link</button>
                        </div>
                      )}
                      <button onClick={() => { setCreating(false); setNewCreated(null); setNewResetLink(null); setNewName(""); setNewEmail(""); setNewPw(""); setNewRole("student"); }}
                        style={{ marginTop:14, background:"#1e293b", color:"white", border:"none", padding:"8px 20px", borderRadius:8, fontWeight:700, fontSize:13, cursor:"pointer" }}>Done</button>
                    </div>
                  ) : (
                    <div style={{ padding:20 }}>
                      {[["Full Name", newName, setNewName, "text", "First Last"], ["Email", newEmail, setNewEmail, "email", "email@example.com"]].map(([label, val, setter, type, ph]) => (
                        <div key={label} style={{ marginBottom:12 }}>
                          <div style={{ fontSize:11, fontWeight:700, color:"#64748b", textTransform:"uppercase", letterSpacing:1, marginBottom:4 }}>{label}</div>
                          <input type={type} value={val} onChange={e => setter(e.target.value)} placeholder={ph}
                            style={{ width:"100%", border:"1px solid #cbd5e1", borderRadius:8, padding:"7px 10px", fontSize:13, boxSizing:"border-box" }} />
                        </div>
                      ))}
                      <div style={{ marginBottom:12 }}>
                        <div style={{ fontSize:11, fontWeight:700, color:"#64748b", textTransform:"uppercase", letterSpacing:1, marginBottom:4 }}>Role</div>
                        <select value={newRole} onChange={e => setNewRole(e.target.value)}
                          style={{ width:"100%", border:"1px solid #cbd5e1", borderRadius:8, padding:"7px 10px", fontSize:13 }}>
                          {PANEL_ROLES.map(r => <option key={r} value={r}>{PANEL_ROLE_LABELS[r]}</option>)}
                        </select>
                      </div>
                      <div style={{ marginBottom:16 }}>
                        <div style={{ fontSize:11, fontWeight:700, color:"#64748b", textTransform:"uppercase", letterSpacing:1, marginBottom:4 }}>Password (min 8 chars)</div>
                        <div style={{ display:"flex", gap:6 }}>
                          <input type={newShowPw ? "text" : "password"} value={newPw} onChange={e => setNewPw(e.target.value)} placeholder="Min 8 characters"
                            style={{ flex:1, border:"1px solid #cbd5e1", borderRadius:8, padding:"7px 10px", fontSize:13, fontFamily:"monospace" }} />
                          <button onClick={() => setNewShowPw(s => !s)} style={{ border:"1px solid #cbd5e1", borderRadius:8, background:"white", padding:"0 10px", cursor:"pointer" }}>
                            {newShowPw ? <EyeOff style={{ width:14, height:14 }} /> : <Eye style={{ width:14, height:14 }} />}
                          </button>
                        </div>
                      </div>
                      <div style={{ display:"flex", justifyContent:"flex-end", gap:8 }}>
                        <button onClick={() => setCreating(false)} style={{ border:"none", background:"none", color:"#64748b", fontSize:13, cursor:"pointer", padding:"8px 14px" }}>Cancel</button>
                        <button onClick={createUser} style={{ background:"#f59e0b", color:"white", border:"none", padding:"8px 20px", borderRadius:8, fontWeight:700, fontSize:13, cursor:"pointer" }}>Create Account</button>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* ── Edit modal ── */}
            {editing && (
              <div style={{ position:"fixed", inset:0, zIndex:200, background:"rgba(0,0,0,0.7)", display:"flex", alignItems:"center", justifyContent:"center", padding:16 }}
                onClick={e => e.target === e.currentTarget && setEditing(null)}>
                <div style={{ background:"white", borderRadius:16, width:"100%", maxWidth:480, maxHeight:"90vh", overflow:"auto" }}>
                  <div style={{ padding:"14px 20px", borderBottom:"1px solid #e5e7eb", display:"flex", justifyContent:"space-between", alignItems:"center", position:"sticky", top:0, background:"white" }}>
                    <div>
                      <div style={{ fontWeight:800, color:"#1e293b" }}>{editing.full_name || editing.email}</div>
                      <div style={{ fontSize:11, color:"#64748b" }}>{editing.email}</div>
                    </div>
                    <button onClick={() => setEditing(null)} style={{ border:"none", background:"none", fontSize:20, cursor:"pointer", color:"#64748b" }}>×</button>
                  </div>
                  <div style={{ padding:20 }}>
                    {[["Full Name", editName, setEditName, "text"], ["Email", editEmail, setEditEmail, "email"]].map(([label, val, setter, type]) => (
                      <div key={label} style={{ marginBottom:12 }}>
                        <div style={{ fontSize:11, fontWeight:700, color:"#64748b", textTransform:"uppercase", letterSpacing:1, marginBottom:4 }}>{label}</div>
                        <input type={type} value={val} onChange={e => setter(e.target.value)}
                          style={{ width:"100%", border:"1px solid #cbd5e1", borderRadius:8, padding:"7px 10px", fontSize:13, boxSizing:"border-box" }} />
                      </div>
                    ))}
                    <div style={{ marginBottom:12 }}>
                      <div style={{ fontSize:11, fontWeight:700, color:"#64748b", textTransform:"uppercase", letterSpacing:1, marginBottom:4 }}>Role</div>
                      <select value={editRole} onChange={e => setEditRole(e.target.value)}
                        style={{ width:"100%", border:"1px solid #cbd5e1", borderRadius:8, padding:"7px 10px", fontSize:13 }}>
                        {PANEL_ROLES.map(r => <option key={r} value={r}>{PANEL_ROLE_LABELS[r]}</option>)}
                      </select>
                    </div>
                    <div style={{ marginBottom:12 }}>
                      <div style={{ fontSize:11, fontWeight:700, color:"#64748b", textTransform:"uppercase", letterSpacing:1, marginBottom:4 }}>Set New Password (leave blank to keep current)</div>
                      <div style={{ display:"flex", gap:6 }}>
                        <input type={editShowPw ? "text" : "password"} value={editPw} onChange={e => setEditPw(e.target.value)} placeholder="Min 8 characters"
                          style={{ flex:1, border:"1px solid #cbd5e1", borderRadius:8, padding:"7px 10px", fontSize:13, fontFamily:"monospace", boxSizing:"border-box" }} />
                        <button onClick={() => setEditShowPw(s => !s)} style={{ border:"1px solid #cbd5e1", borderRadius:8, background:"white", padding:"0 10px", cursor:"pointer" }}>
                          {editShowPw ? <EyeOff style={{ width:14, height:14 }} /> : <Eye style={{ width:14, height:14 }} />}
                        </button>
                      </div>
                    </div>
                    <div style={{ marginBottom:16 }}>
                      <div style={{ fontSize:11, fontWeight:700, color:"#64748b", textTransform:"uppercase", letterSpacing:1, marginBottom:6 }}>Password Reset Link</div>
                      <button onClick={genEditResetLink} style={{ fontSize:11, color:"#b45309", fontWeight:700, border:"1px solid #fde68a", background:"#fefce8", padding:"5px 12px", borderRadius:6, cursor:"pointer" }}>Generate one-time link</button>
                      {editResetLink && (
                        <div style={{ marginTop:8, background:"#fefce8", border:"1px solid #fde68a", borderRadius:8, padding:10 }}>
                          <div style={{ fontSize:11, fontFamily:"monospace", wordBreak:"break-all", color:"#78350f" }}>{editResetLink}</div>
                          <button onClick={() => navigator.clipboard?.writeText(editResetLink)} style={{ fontSize:11, color:"#b45309", fontWeight:700, border:"none", background:"none", cursor:"pointer", marginTop:4 }}>Copy</button>
                        </div>
                      )}
                    </div>
                    {/* ── User history ── */}
                    <div style={{ marginBottom:16 }}>
                      <div style={{ fontSize:11, fontWeight:700, color:"#64748b", textTransform:"uppercase", letterSpacing:1, marginBottom:8 }}>
                        User History & Incidents {!editHistoryLoaded && <span style={{ color:"#94a3b8" }}>loading…</span>}
                      </div>
                      {editUserIncidents.length > 0 && (
                        <div style={{ marginBottom:8 }}>
                          <div style={{ fontSize:10, fontWeight:700, color:"#dc2626", textTransform:"uppercase", letterSpacing:1, marginBottom:4 }}>Incidents ({editUserIncidents.length})</div>
                          {editUserIncidents.slice(0,5).map(inc => (
                            <div key={inc.id} style={{ background:"#fef2f2", border:"1px solid #fecaca", borderRadius:6, padding:"6px 10px", marginBottom:4, fontSize:11 }}>
                              <div style={{ fontWeight:700, color:"#991b1b" }}>{inc.title || inc.description}</div>
                              <div style={{ color:"#64748b", fontSize:10, marginTop:2 }}>
                                {inc.status} · {inc.severity || ""} · {inc.created_at ? new Date(inc.created_at).toLocaleDateString() : ""}
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                      {editHistoryLoaded && editUserIncidents.length === 0 && (
                        <div style={{ fontSize:11, color:"#94a3b8" }}>No incidents on record.</div>
                      )}
                      {editUserAudit.length > 0 && (
                        <div>
                          <div style={{ fontSize:10, fontWeight:700, color:"#475569", textTransform:"uppercase", letterSpacing:1, marginBottom:4 }}>Audit Trail ({editUserAudit.length} entries)</div>
                          {editUserAudit.slice(0,8).map((a, i) => (
                            <div key={a.id || i} style={{ display:"flex", gap:8, padding:"4px 0", borderBottom:"1px solid #f1f5f9", fontSize:11 }}>
                              <div style={{ color:"#7c3aed", fontFamily:"monospace", flex:1 }}>{a.action}</div>
                              <div style={{ color:"#94a3b8", whiteSpace:"nowrap" }}>{a.at ? new Date(a.at).toLocaleString() : ""}</div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>

                    <div style={{ display:"flex", justifyContent:"space-between", flexWrap:"wrap", gap:8, borderTop:"1px solid #f1f5f9", paddingTop:14 }}>
                      <div style={{ display:"flex", gap:6 }}>
                        <button onClick={() => toggleActive(editing)}
                          style={{ fontSize:12, fontWeight:700, padding:"6px 12px", borderRadius:8, cursor:"pointer", border: editing.is_active === false ? "1px solid #10b981" : "1px solid #f97316", color: editing.is_active === false ? "#059669" : "#ea580c", background:"transparent" }}>
                          {editing.is_active === false ? "Activate" : "Deactivate"}
                        </button>
                        <button onClick={() => deleteUser(editing)}
                          style={{ fontSize:12, fontWeight:700, padding:"6px 12px", borderRadius:8, cursor:"pointer", border:"1px solid #fca5a5", color:"#dc2626", background:"transparent" }}>
                          Delete
                        </button>
                      </div>
                      <div style={{ display:"flex", gap:6 }}>
                        <button onClick={() => setEditing(null)} style={{ border:"none", background:"none", color:"#64748b", fontSize:13, cursor:"pointer", padding:"6px 12px" }}>Cancel</button>
                        <button onClick={saveEdit} style={{ background:"#f59e0b", color:"white", border:"none", padding:"6px 18px", borderRadius:8, fontWeight:700, fontSize:13, cursor:"pointer" }}>Save Changes</button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* ── User list ── */}
            <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between", marginBottom:12, flexWrap:"wrap", gap:8 }}>
              <span style={{ color:"white", fontWeight:700, fontSize:14 }}>User Database ({users.length})</span>
              <div style={{ display:"flex", gap:6, flexWrap:"wrap" }}>
                <input value={userQ} onChange={e => setUserQ(e.target.value)} placeholder="Search name or email…"
                  style={{ background:"rgba(255,255,255,0.08)", border:"1px solid rgba(255,255,255,0.2)", borderRadius:6, padding:"4px 10px", color:"white", fontSize:12, outline:"none", width:160 }} />
                <select value={userRoleFilter} onChange={e => setUserRoleFilter(e.target.value)}
                  style={{ background:"rgba(255,255,255,0.08)", border:"1px solid rgba(255,255,255,0.2)", borderRadius:6, padding:"4px 8px", color:"white", fontSize:12, cursor:"pointer" }}>
                  <option value="">All Roles</option>
                  {PANEL_ROLES.map(r => <option key={r} value={r}>{PANEL_ROLE_LABELS[r]}</option>)}
                </select>
                <select value={userActiveFilter} onChange={e => setUserActiveFilter(e.target.value)}
                  style={{ background:"rgba(255,255,255,0.08)", border:"1px solid rgba(255,255,255,0.2)", borderRadius:6, padding:"4px 8px", color:"white", fontSize:12, cursor:"pointer" }}>
                  <option value="">Any Status</option>
                  <option value="true">Active only</option>
                  <option value="false">Inactive only</option>
                </select>
                <button onClick={() => loadUsers(userQ, userRoleFilter, userActiveFilter)} style={{ background:"rgba(255,255,255,0.1)", border:"none", color:"white", padding:"4px 10px", borderRadius:6, fontSize:11, cursor:"pointer" }}>Refresh</button>
                <button onClick={() => { setCreating(true); setNewCreated(null); setNewResetLink(null); }}
                  style={{ background:SIG, border:"none", color:INK, padding:"4px 12px", borderRadius:6, fontSize:11, fontWeight:700, cursor:"pointer" }}>+ Create</button>
              </div>
            </div>
            <div style={{ overflowX:"auto", maxHeight: 480, overflowY:"auto" }}>
              <table style={{ width:"100%", borderCollapse:"collapse", fontSize:12 }}>
                <thead style={{ position:"sticky", top:0, background:"#2e1065", zIndex:1 }}>
                  <tr>
                    {["Name / Email", "Role", "Status", "Joined", "Actions"].map(h => (
                      <th key={h} style={{ textAlign:"left", padding:"6px 10px", color:"rgba(255,255,255,0.4)", fontWeight:700, borderBottom:"1px solid rgba(255,255,255,0.08)", textTransform:"uppercase", fontSize:10, whiteSpace:"nowrap" }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {users.map(u => (
                    <tr key={u.id || u.email} style={{ borderBottom:"1px solid rgba(255,255,255,0.06)" }}>
                      <td style={{ padding:"7px 10px" }}>
                        <div style={{ color:"white", fontWeight:600 }}>{u.full_name || "—"}</div>
                        <div style={{ color:"rgba(255,255,255,0.45)", fontSize:10 }}>{u.email}</div>
                      </td>
                      <td style={{ padding:"7px 10px" }}>
                        <div style={{ display:"flex", gap:3, flexWrap:"wrap" }}>
                          {PANEL_ROLES.map(r => (
                            <button key={r} onClick={() => quickRole(u, r)} disabled={!!promoting[u.id]}
                              style={{ fontSize:9, padding:"2px 6px", borderRadius:10, border:"none", cursor:"pointer", fontWeight:700,
                                background: u.role === r ? (r === "executive_admin" ? SIG : r === "admin" ? "#7c3aed" : r === "instructor" ? "#2563eb" : "#10b981") : "rgba(255,255,255,0.12)",
                                color: u.role === r ? (r === "executive_admin" ? INK : "white") : "rgba(255,255,255,0.5)" }}>
                              {PANEL_ROLE_LABELS[r]}
                            </button>
                          ))}
                        </div>
                      </td>
                      <td style={{ padding:"7px 10px" }}>
                        <span style={{ fontSize:10, fontWeight:700, color: u.is_active === false ? "#ef4444" : "#22c55e" }}>
                          {u.is_active === false ? "Inactive" : "Active"}
                        </span>
                      </td>
                      <td style={{ padding:"7px 10px", color:"rgba(255,255,255,0.45)", fontSize:10, whiteSpace:"nowrap" }}>
                        {u.created_at ? new Date(u.created_at).toLocaleDateString() : "—"}
                      </td>
                      <td style={{ padding:"7px 10px" }}>
                        <button onClick={() => openEdit(u)}
                          style={{ fontSize:10, fontWeight:700, padding:"3px 10px", borderRadius:6, border:"1px solid rgba(255,209,0,0.5)", color:SIG, background:"transparent", cursor:"pointer" }}>
                          Edit
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {users.length === 0 && <p style={{ color:"rgba(255,255,255,0.4)", fontSize:13, marginTop:12 }}>No users loaded. Use search or Refresh.</p>}
            </div>
          </div>
        )}

        {tab === "broadcast" && (
          <div>
            <div style={{ color: "white", fontWeight: 700, fontSize: 14, marginBottom: 14 }}>Send Platform Broadcast</div>
            <div style={{ marginBottom: 10 }}>
              <div style={{ color: "rgba(255,255,255,0.5)", fontSize: 11, marginBottom: 4 }}>Title (optional)</div>
              <input value={broadcastTitle} onChange={e => setBcastTitle(e.target.value)}
                placeholder="Platform Announcement"
                style={{ width: "100%", background: "rgba(255,255,255,0.08)", border: "1px solid rgba(255,255,255,0.15)", borderRadius: 8, padding: "8px 12px", color: "white", fontSize: 13, outline: "none", boxSizing: "border-box" }} />
            </div>
            <div style={{ marginBottom: 10 }}>
              <div style={{ color: "rgba(255,255,255,0.5)", fontSize: 11, marginBottom: 4 }}>Target audience</div>
              <select value={broadcastTarget} onChange={e => setBcastTarget(e.target.value)}
                style={{ background: "rgba(255,255,255,0.08)", border: "1px solid rgba(255,255,255,0.15)", borderRadius: 8, padding: "8px 12px", color: "white", fontSize: 13, cursor: "pointer" }}>
                <option value="all">All users</option>
                {PANEL_ROLES.map(r => <option key={r} value={r}>{PANEL_ROLE_LABELS[r]}s only</option>)}
              </select>
            </div>
            <textarea
              value={broadcastMsg}
              onChange={e => setBroadcast(e.target.value)}
              placeholder="Type a message to broadcast…"
              rows={4}
              style={{ width: "100%", background: "rgba(255,255,255,0.08)", border: "1px solid rgba(255,255,255,0.15)", borderRadius: 8, padding: "10px 14px", color: "white", fontSize: 13, resize: "vertical", outline: "none", boxSizing: "border-box" }}
            />
            <button onClick={sendBroadcast} disabled={sending || !broadcastMsg.trim()}
              style={{ marginTop: 10, background: SIG, border: "none", color: INK, padding: "9px 20px", borderRadius: 7, fontSize: 13, fontWeight: 700, cursor: "pointer", display: "flex", alignItems: "center", gap: 6 }}>
              <Send style={{ width: 14, height: 14 }} /> {sending ? "Sending…" : `Send to ${broadcastTarget === "all" ? "all users" : PANEL_ROLE_LABELS[broadcastTarget] + "s"}`}
            </button>
          </div>
        )}

        {tab === "incidents" && (
          <div>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 14 }}>
              <span style={{ color: "white", fontWeight: 700, fontSize: 14 }}>Open Incidents ({incidents.length})</span>
              <button onClick={loadIncidents} style={{ background: "rgba(255,255,255,0.1)", border: "none", color: "white", padding: "5px 10px", borderRadius: 6, fontSize: 11, cursor: "pointer" }}>Refresh</button>
            </div>
            {incidents.length === 0
              ? <p style={{ color: "rgba(255,255,255,0.4)", fontSize: 13 }}>No open incidents.</p>
              : incidents.map(inc => (
                <div key={inc.id} style={{ background: "rgba(220,38,38,0.10)", border: "1px solid rgba(220,38,38,0.25)", borderRadius: 8, padding: "12px 16px", marginBottom: 10 }}>
                  <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 8, flexWrap: "wrap" }}>
                    <div style={{ flex: 1 }}>
                      <div style={{ color: "white", fontWeight: 700, fontSize: 13 }}>{inc.title || inc.description}</div>
                      <div style={{ color: "rgba(255,255,255,0.45)", fontSize: 11, marginTop: 3 }}>
                        {inc.created_at ? new Date(inc.created_at).toLocaleString() : ""}
                        {inc.severity ? ` · ${inc.severity}` : ""}
                        {inc.reporter ? ` · Reported by: ${inc.reporter.full_name || inc.reporter.email}` : ""}
                      </div>
                      {inc.involved?.length > 0 && (
                        <div style={{ color: "rgba(255,255,255,0.4)", fontSize: 10, marginTop: 3 }}>
                          Involved: {inc.involved.map(u => u.full_name || u.email).join(", ")}
                        </div>
                      )}
                    </div>
                    <button onClick={() => { setResolvingId(resolvingId === inc.id ? null : inc.id); setResolveText(""); }}
                      style={{ background: "rgba(34,197,94,0.2)", border: "1px solid rgba(34,197,94,0.4)", color: "#4ade80", padding: "4px 10px", borderRadius: 5, fontSize: 10, fontWeight: 700, cursor: "pointer", whiteSpace: "nowrap" }}>
                      Resolve
                    </button>
                  </div>
                  {resolvingId === inc.id && (
                    <div style={{ marginTop: 10, display: "flex", gap: 6, flexWrap: "wrap" }}>
                      <input value={resolveText} onChange={e => setResolveText(e.target.value)}
                        placeholder="Resolution note (required)…"
                        style={{ flex: 1, minWidth: 180, background: "rgba(255,255,255,0.08)", border: "1px solid rgba(255,255,255,0.2)", borderRadius: 6, padding: "5px 10px", color: "white", fontSize: 12, outline: "none" }} />
                      <button disabled={!resolveText.trim()} onClick={async () => {
                        try {
                          await api.post(`/incidents/${inc.id}/resolve`, { resolution: resolveText });
                          notify(`Incident resolved`);
                          setResolvingId(null); setResolveText("");
                          await loadIncidents();
                        } catch (e) { notify(`Resolve failed: ${e?.response?.data?.detail || e.message}`); }
                      }}
                        style={{ background: resolveText.trim() ? "#22c55e" : "rgba(255,255,255,0.1)", border: "none", color: resolveText.trim() ? "white" : "rgba(255,255,255,0.3)", padding: "5px 12px", borderRadius: 6, fontSize: 11, fontWeight: 700, cursor: resolveText.trim() ? "pointer" : "not-allowed" }}>
                        Confirm
                      </button>
                    </div>
                  )}
                </div>
              ))
            }
          </div>
        )}

        {tab === "safety" && (
          <div>
            {/* Global cap */}
            <div style={{ color: "white", fontWeight: 700, fontSize: 14, marginBottom: 6 }}>Global Sage Safety Cap</div>
            <div style={{ color: "rgba(255,255,255,0.5)", fontSize: 12, marginBottom: 14 }}>
              Current: <strong style={{ color: SIG }}>{capLevel || "No restriction"}</strong>
            </div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 28 }}>
              {["conservative", "standard", "exploratory"].map(lvl => (
                <button key={lvl} onClick={() => setSafetyCap(lvl)}
                  style={{ background: capLevel === lvl ? SIG : "rgba(255,255,255,0.1)", border: "none", color: capLevel === lvl ? INK : "white", padding: "8px 16px", borderRadius: 7, fontSize: 12, fontWeight: 700, cursor: "pointer", textTransform: "capitalize" }}>
                  {lvl}
                </button>
              ))}
              <button onClick={() => setSafetyCap("")}
                style={{ background: "rgba(220,38,38,0.2)", border: "1px solid rgba(220,38,38,0.4)", color: "#fca5a5", padding: "8px 16px", borderRadius: 7, fontSize: 12, fontWeight: 700, cursor: "pointer" }}>
                Clear Restriction
              </button>
            </div>

            {/* Per-user overrides — exec only */}
            {superExec && (
              <div>
                <div style={{ color: SIG, fontWeight: 700, fontSize: 12, textTransform: "uppercase", letterSpacing: 1, marginBottom: 10 }}>Per-User Cap Overrides</div>
                <div style={{ color: "rgba(255,255,255,0.45)", fontSize: 11, marginBottom: 12 }}>
                  Override the global cap for a specific user. Use User ID from the Users tab. Set to null to remove.
                </div>
                <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 16 }}>
                  <input value={capOverrideUid} onChange={e => setCapOverrideUid(e.target.value)}
                    placeholder="User ID…"
                    style={{ flex: 1, minWidth: 180, background: "rgba(255,255,255,0.08)", border: "1px solid rgba(255,255,255,0.2)", borderRadius: 6, padding: "6px 10px", color: "white", fontSize: 12, outline: "none" }} />
                  <select value={capOverrideLvl} onChange={e => setCapOverrideLvl(e.target.value)}
                    style={{ background: "rgba(255,255,255,0.08)", border: "1px solid rgba(255,255,255,0.2)", borderRadius: 6, padding: "6px 10px", color: "white", fontSize: 12, cursor: "pointer" }}>
                    {["conservative", "standard", "exploratory"].map(lvl => <option key={lvl} value={lvl}>{lvl}</option>)}
                  </select>
                  <button onClick={() => setUserCapOverride(capOverrideUid, capOverrideLvl)}
                    style={{ background: SIG, border: "none", color: INK, padding: "6px 14px", borderRadius: 6, fontSize: 11, fontWeight: 800, cursor: "pointer" }}>
                    Set Override
                  </button>
                </div>
                {capOverrides.length > 0 ? (
                  <div>
                    <div style={{ color: "rgba(255,255,255,0.5)", fontSize: 11, marginBottom: 8 }}>Active overrides ({capOverrides.length}):</div>
                    {capOverrides.map(ov => (
                      <div key={ov.user_id} style={{ display: "flex", alignItems: "center", gap: 10, padding: "6px 10px", background: "rgba(255,255,255,0.06)", borderRadius: 6, marginBottom: 5 }}>
                        <div style={{ flex: 1 }}>
                          <span style={{ color: "white", fontSize: 12, fontWeight: 600 }}>{ov.full_name || ov.email || ov.user_id}</span>
                          <span style={{ color: "rgba(255,255,255,0.4)", fontSize: 10, marginLeft: 8 }}>{ov.user_id}</span>
                        </div>
                        <span style={{ color: SIG, fontSize: 11, fontWeight: 700, textTransform: "capitalize" }}>{ov.level}</span>
                        <button onClick={() => clearUserCapOverride(ov.user_id)}
                          style={{ background: "rgba(220,38,38,0.2)", border: "none", color: "#fca5a5", padding: "3px 8px", borderRadius: 5, fontSize: 10, fontWeight: 700, cursor: "pointer" }}>
                          Clear
                        </button>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p style={{ color: "rgba(255,255,255,0.35)", fontSize: 12 }}>No per-user overrides active.</p>
                )}
              </div>
            )}
          </div>
        )}

        {tab === "apikeys" && (
          <div>
            <div style={{ color:"white", fontWeight:700, fontSize:14, marginBottom:4 }}>Push API Keys to Gateway</div>
            <div style={{ color:"rgba(255,255,255,0.45)", fontSize:11, marginBottom:16 }}>
              Free-tier providers listed first. Keys inject live into the running gateway without a redeploy.
              Active status reflects gateway's current provider availability.
            </div>
            {/* Free-first order — matches backend ALLOWED set exactly */}
            {[
              { label: "1. Groq",        env: "GROQ_API_KEY",        prefix: "gsk_",  tier:"free" },
              { label: "2. Cerebras",    env: "CEREBRAS_API_KEY",    prefix: "csk-",  tier:"free" },
              { label: "3. Gemini",      env: "GEMINI_API_KEY",      prefix: "AI",    tier:"free" },
              { label: "4. xAI / Grok", env: "XAI_API_KEY",         prefix: "xai-",  tier:"free" },
              { label: "5. Cohere",      env: "COHERE_API_KEY",      prefix: "",      tier:"free" },
              { label: "6. HuggingFace",env: "HUGGINGFACE_API_KEY", prefix: "hf_",   tier:"free" },
              { label: "7. OpenRouter",  env: "OPENROUTER_API_KEY",  prefix: "sk-or", tier:"free" },
            ].map(({ label, env, prefix, tier }) => {
              const val = apiKeys[env] || "";
              const shown = showKeys[env];
              const provKey = env.replace("_API_KEY","").toLowerCase();
              const isActive = gwStatus?.providers?.[provKey]?.available;
              return (
                <div key={env} style={{ marginBottom:10, display:"flex", alignItems:"center", gap:8, flexWrap:"wrap" }}>
                  <div style={{ minWidth:150, display:"flex", flexDirection:"column", gap:2 }}>
                    <span style={{ color:"rgba(255,255,255,0.85)", fontSize:12, fontWeight:700 }}>{label}</span>
                    <span style={{ fontSize:9, fontWeight:700, textTransform:"uppercase", letterSpacing:1,
                      color: isActive === true ? "#22c55e" : isActive === false ? "#ef4444" : "rgba(255,255,255,0.3)" }}>
                      {isActive === true ? "● Active" : isActive === false ? "○ No key" : "○ Unknown"}
                    </span>
                  </div>
                  <div style={{ flex:1, display:"flex", gap:6, minWidth:220 }}>
                    <input
                      type={shown ? "text" : "password"}
                      placeholder={prefix ? `${prefix}…` : "paste key…"}
                      value={val}
                      onChange={e => setApiKeys(k => ({ ...k, [env]: e.target.value }))}
                      style={{ flex:1, background:"rgba(255,255,255,0.08)", border:"1px solid rgba(255,255,255,0.15)", borderRadius:6, padding:"6px 10px", color:"white", fontSize:12, outline:"none" }}
                    />
                    <button onClick={() => setShowKeys(s => ({ ...s, [env]: !s[env] }))}
                      style={{ background:"rgba(255,255,255,0.1)", border:"none", color:"white", width:30, borderRadius:6, cursor:"pointer" }}>
                      {shown ? <EyeOff style={{ width:13, height:13 }} /> : <Eye style={{ width:13, height:13 }} />}
                    </button>
                    <button onClick={() => pushApiKey(env, val)} disabled={!val}
                      style={{ background: val ? SIG : "rgba(255,255,255,0.08)", border:"none", color: val ? INK : "rgba(255,255,255,0.3)", padding:"6px 12px", borderRadius:6, fontSize:11, fontWeight:700, cursor: val ? "pointer" : "not-allowed" }}>
                      Push
                    </button>
                    <button onClick={() => toggleApiKey(env, !(keyEnabled[env] !== false && isActive !== false))}
                      title={keyEnabled[env] === false ? "Enable key in gateway" : "Disable key (saves for re-enable)"}
                      style={{ background: keyEnabled[env] === false ? "rgba(234,179,8,0.25)" : "rgba(255,255,255,0.1)", border:"none", color: keyEnabled[env] === false ? "#fbbf24" : "rgba(255,255,255,0.7)", padding:"6px 10px", borderRadius:6, fontSize:11, fontWeight:700, cursor:"pointer", whiteSpace:"nowrap" }}>
                      {keyEnabled[env] === false ? "Enable" : "Disable"}
                    </button>
                    <button onClick={() => revokeApiKey(env)}
                      title="Permanently remove key from live gateway"
                      style={{ background:"rgba(220,38,38,0.18)", border:"none", color:"#f87171", padding:"6px 10px", borderRadius:6, fontSize:11, fontWeight:700, cursor:"pointer" }}>
                      Revoke
                    </button>
                  </div>
                </div>
              );
            })}
            <button onClick={loadGateway} style={{ marginTop:8, background:"rgba(255,255,255,0.1)", border:"none", color:"white", padding:"5px 12px", borderRadius:6, fontSize:11, cursor:"pointer" }}>
              Refresh Status
            </button>
          </div>
        )}

        {tab === "visibility" && (
          <VisibilityTab visibility={visibility} setVisibility={setVisibility} />
        )}

        {tab === "modes" && (
          <div>
            <div style={{ color:"white", fontWeight:700, fontSize:14, marginBottom:6 }}>Page Display Mode</div>
            <div style={{ color:"rgba(255,255,255,0.5)", fontSize:11, marginBottom:16 }}>
              Controls what public visitors see on this page. Stored in their browser's localStorage.
            </div>
            <div style={{ display:"flex", flexWrap:"wrap", gap:8, marginBottom:20 }}>
              {PAGE_MODES.map(m => (
                <button key={m.id} onClick={() => {
                  setPageMode(m.id);
                  try { localStorage.setItem("more_help_center_mode", m.id); } catch {}
                  notify(`Page mode set to ${m.label}`);
                }}
                  style={{ background: pageMode === m.id ? SIG : "rgba(255,255,255,0.1)", border:"none", color: pageMode === m.id ? INK : "white", padding:"8px 18px", borderRadius:7, fontSize:12, fontWeight:700, cursor:"pointer", textTransform:"capitalize" }}>
                  {m.label}
                </button>
              ))}
            </div>
            {PAGE_MODES.map(m => (
              <div key={m.id} style={{ marginBottom:12, background: pageMode === m.id ? "rgba(255,209,0,0.12)" : "rgba(255,255,255,0.05)", border: pageMode === m.id ? `1px solid ${SIG}44` : "1px solid rgba(255,255,255,0.08)", borderRadius:8, padding:"12px 16px" }}>
                <div style={{ color: pageMode === m.id ? SIG : "rgba(255,255,255,0.7)", fontWeight:700, fontSize:12 }}>{m.label}</div>
                <div style={{ color:"rgba(255,255,255,0.5)", fontSize:11, marginTop:4 }}>{m.desc}</div>
              </div>
            ))}
          </div>
        )}

        {tab === "failover" && superExec && (
          <div>
            <div style={{ color:"white", fontWeight:700, fontSize:14, marginBottom:4 }}>⚡ Gateway Failover</div>
            <div style={{ color:"rgba(255,255,255,0.45)", fontSize:11, marginBottom:16 }}>
              Executive-only. Triggers a live gateway failover to backup or emergency provider.
            </div>

            {/* Backup matrix */}
            <div style={{ marginBottom:20 }}>
              <div style={{ color:SIG, fontWeight:700, fontSize:12, marginBottom:8 }}>Free API Backup Matrix</div>
              {backupMatrix ? (
                <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fit,minmax(160px,1fr))", gap:8 }}>
                  {Object.entries(backupMatrix).map(([svc, info]) => (
                    <div key={svc} style={{ background:"rgba(255,255,255,0.07)", borderRadius:8, padding:"10px 14px" }}>
                      <div style={{ color:"white", fontWeight:700, fontSize:12, textTransform:"capitalize" }}>{svc}</div>
                      <div style={{ color: info?.available ? "#22c55e" : "#ef4444", fontSize:11, marginTop:3 }}>
                        {info?.available ? "✓ Available" : "✗ Unavailable"}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <button onClick={loadBackupMatrix} style={{ background:"rgba(255,255,255,0.1)", border:"none", color:"white", padding:"5px 12px", borderRadius:6, fontSize:11, cursor:"pointer" }}>
                  Load Matrix
                </button>
              )}
            </div>

            {/* Failover trigger */}
            <div style={{ background:"rgba(220,38,38,0.1)", border:"1px solid rgba(220,38,38,0.3)", borderRadius:10, padding:16, marginBottom:16 }}>
              <div style={{ color:"#fca5a5", fontWeight:700, fontSize:12, marginBottom:12 }}>Trigger Failover</div>
              <div style={{ display:"flex", gap:8, marginBottom:10, flexWrap:"wrap" }}>
                {["backup", "emergency"].map(t => (
                  <button key={t} onClick={() => setFailoverTarget(t)}
                    style={{ background: failoverTarget === t ? "#dc2626" : "rgba(255,255,255,0.1)", border:"none", color:"white", padding:"6px 14px", borderRadius:6, fontSize:12, fontWeight:700, cursor:"pointer", textTransform:"capitalize" }}>
                    {t}
                  </button>
                ))}
              </div>
              <input value={failoverReason} onChange={e => setFailoverReason(e.target.value)}
                placeholder="Reason for failover (required)…"
                style={{ width:"100%", background:"rgba(255,255,255,0.08)", border:"1px solid rgba(255,255,255,0.2)", borderRadius:6, padding:"8px 12px", color:"white", fontSize:12, outline:"none", boxSizing:"border-box", marginBottom:10 }} />
              <button onClick={triggerFailover} disabled={!failoverReason.trim()}
                style={{ background: failoverReason.trim() ? "#dc2626" : "rgba(255,255,255,0.08)", border:"none", color:"white", padding:"8px 20px", borderRadius:7, fontSize:12, fontWeight:700, cursor: failoverReason.trim() ? "pointer" : "not-allowed" }}>
                Trigger Failover → {failoverTarget}
              </button>
            </div>

            {/* Heartbeat secret */}
            <div style={{ background:"rgba(255,255,255,0.05)", borderRadius:10, padding:16, marginBottom:16 }}>
              <div style={{ color:"rgba(255,255,255,0.7)", fontWeight:700, fontSize:12, marginBottom:8 }}>Heartbeat Secret (for backup server)</div>
              <button onClick={loadHeartbeatSecret} style={{ background:"rgba(255,255,255,0.1)", border:"none", color:"white", padding:"5px 12px", borderRadius:6, fontSize:11, cursor:"pointer" }}>
                Retrieve Secret
              </button>
              {heartbeatSecret && (
                <div style={{ marginTop:10, background:"rgba(0,0,0,0.3)", borderRadius:6, padding:"8px 12px" }}>
                  <div style={{ fontFamily:"monospace", fontSize:12, color:SIG, wordBreak:"break-all" }}>{heartbeatSecret}</div>
                  <button onClick={() => navigator.clipboard?.writeText(heartbeatSecret)}
                    style={{ fontSize:11, color:"rgba(255,255,255,0.6)", fontWeight:700, border:"none", background:"none", cursor:"pointer", marginTop:4 }}>Copy</button>
                </div>
              )}
            </div>

            {/* Platform Feature Flags */}
            <div style={{ marginBottom:24 }}>
              <div style={{ color:SIG, fontWeight:700, fontSize:12, marginBottom:6 }}>Emergency Platform Flags</div>
              <div style={{ color:"rgba(255,255,255,0.4)", fontSize:11, marginBottom:10 }}>
                Instantly disable platform features without a redeploy. Exec-only. Each change is audited.
              </div>
              {platformFlags !== null ? (
                <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fit,minmax(200px,1fr))", gap:8 }}>
                  {["platform_locked","marketplace_disabled","ai_disabled","community_disabled","labs_disabled"].map(flag => {
                    const info = platformFlags[flag];
                    const enabled = info?.enabled === true;
                    return (
                      <div key={flag} style={{ background: enabled ? "rgba(220,38,38,0.15)" : "rgba(255,255,255,0.06)", borderRadius:8, padding:"10px 14px", border: `1px solid ${enabled ? "rgba(220,38,38,0.4)" : "rgba(255,255,255,0.1)"}` }}>
                        <div style={{ color:"white", fontWeight:700, fontSize:11, textTransform:"capitalize", marginBottom:4 }}>{flag.replace(/_/g," ")}</div>
                        <div style={{ color: enabled ? "#f87171" : "#22c55e", fontSize:10, fontWeight:700, marginBottom:8 }}>{enabled ? "● ENABLED" : "○ off"}</div>
                        <button onClick={() => setPlatformFlag(flag, !enabled, enabled ? "Exec override: disable" : "Exec override: enable")}
                          style={{ background: enabled ? "rgba(220,38,38,0.3)" : "rgba(34,197,94,0.2)", border:"none", color: enabled ? "#fca5a5" : "#4ade80", padding:"3px 10px", borderRadius:4, fontSize:9, fontWeight:700, cursor:"pointer" }}>
                          {enabled ? "Disable" : "Enable"}
                        </button>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <p style={{ color:"rgba(255,255,255,0.35)", fontSize:12 }}>Loading platform flags…</p>
              )}
            </div>

            {/* Breaker Panel */}
            <div style={{ marginBottom:20 }}>
              <div style={{ color:SIG, fontWeight:700, fontSize:12, marginBottom:8 }}>Circuit Breaker Panel</div>
              {panelHealth && (
                <div style={{ display:"flex", gap:8, flexWrap:"wrap", marginBottom:10 }}>
                  {Object.entries(panelHealth).filter(([,v]) => typeof v !== "object").map(([k, v]) => (
                    <div key={k} style={{ background:"rgba(255,255,255,0.07)", borderRadius:6, padding:"5px 10px", fontSize:10 }}>
                      <span style={{ color:"rgba(255,255,255,0.4)", textTransform:"uppercase" }}>{k}: </span>
                      <span style={{ color: v === "up" || v === true ? "#22c55e" : v === "down" || v === false ? "#ef4444" : "white", fontWeight:700 }}>{String(v)}</span>
                    </div>
                  ))}
                </div>
              )}
              {breakerPanel?.breakers ? (
                <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fit,minmax(200px,1fr))", gap:8 }}>
                  {Object.entries(breakerPanel.breakers).map(([id, breaker]) => {
                    const state = breaker?.state || breaker?.status || "unknown";
                    const isOn = state === "on" || state === "active" || state === "closed";
                    const isTripped = state === "tripped" || state === "fault";
                    return (
                      <div key={id} style={{ background:"rgba(255,255,255,0.06)", borderRadius:8, padding:"10px 14px", border:`1px solid ${isTripped ? "rgba(220,38,38,0.4)" : "rgba(255,255,255,0.1)"}` }}>
                        <div style={{ color:"white", fontWeight:700, fontSize:11, textTransform:"capitalize", marginBottom:4 }}>{id.replace(/_/g," ")}</div>
                        <div style={{ color: isTripped ? "#f87171" : isOn ? "#22c55e" : "#94a3b8", fontSize:10, fontWeight:700, textTransform:"uppercase", marginBottom:8 }}>{state}</div>
                        <div style={{ display:"flex", gap:5 }}>
                          <button onClick={() => toggleBreaker(id)}
                            style={{ background:"rgba(255,255,255,0.1)", border:"none", color:"white", padding:"3px 8px", borderRadius:4, fontSize:9, fontWeight:700, cursor:"pointer" }}>
                            Toggle
                          </button>
                          {isTripped && (
                            <button onClick={() => resetBreaker(id)}
                              style={{ background:"rgba(234,179,8,0.25)", border:"none", color:"#fbbf24", padding:"3px 8px", borderRadius:4, fontSize:9, fontWeight:700, cursor:"pointer" }}>
                              Reset
                            </button>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <p style={{ color:"rgba(255,255,255,0.35)", fontSize:12 }}>Breaker data loading with backup matrix…</p>
              )}
            </div>

            {/* Emergency UI link */}
            <a href="/api/emergency" target="_blank" rel="noopener noreferrer"
              style={{ display:"inline-flex", alignItems:"center", gap:6, background:"rgba(255,255,255,0.08)", border:"1px solid rgba(255,255,255,0.2)", color:"white", padding:"8px 16px", borderRadius:7, fontSize:12, fontWeight:700, textDecoration:"none" }}>
              Open Emergency UI (works without React SPA) ↗
            </a>
          </div>
        )}

        {tab === "audit" && (
          <div>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12, flexWrap: "wrap", gap: 8 }}>
              <span style={{ color: "white", fontWeight: 700, fontSize: 14 }}>Audit Log ({auditLog.length})</span>
              <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                <input value={auditActionQ} onChange={e => setAuditActionQ(e.target.value)} placeholder="Filter by action…"
                  style={{ background: "rgba(255,255,255,0.08)", border: "1px solid rgba(255,255,255,0.2)", borderRadius: 6, padding: "4px 10px", color: "white", fontSize: 11, outline: "none", width: 140 }} />
                <input value={auditActorQ} onChange={e => setAuditActorQ(e.target.value)} placeholder="Actor user ID…"
                  style={{ background: "rgba(255,255,255,0.08)", border: "1px solid rgba(255,255,255,0.2)", borderRadius: 6, padding: "4px 10px", color: "white", fontSize: 11, outline: "none", width: 130 }} />
                <select value={auditLimit} onChange={e => setAuditLimit(Number(e.target.value))}
                  style={{ background: "rgba(255,255,255,0.08)", border: "1px solid rgba(255,255,255,0.2)", borderRadius: 6, padding: "4px 8px", color: "white", fontSize: 11, cursor: "pointer" }}>
                  {[20, 50, 100, 200, 500].map(n => <option key={n} value={n}>{n} rows</option>)}
                </select>
                <button onClick={() => loadAudit(auditActionQ, auditActorQ, auditLimit)}
                  style={{ background: "rgba(255,255,255,0.1)", border: "none", color: "white", padding: "4px 10px", borderRadius: 6, fontSize: 11, cursor: "pointer" }}>Search</button>
              </div>
            </div>
            {auditLog.length === 0
              ? <p style={{ color: "rgba(255,255,255,0.4)", fontSize: 13 }}>No audit entries. Adjust filters or click Search.</p>
              : auditLog.map((a, i) => (
                <div key={a.id || i} style={{ display: "flex", gap: 12, padding: "7px 0", borderBottom: "1px solid rgba(255,255,255,0.06)", alignItems: "flex-start" }}>
                  <div style={{ width: 6, height: 6, borderRadius: "50%", background: SIG, marginTop: 6, flexShrink: 0 }} />
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ color: "white", fontSize: 12, fontWeight: 600 }}>{a.actor?.full_name || a.actor?.email || a.actor_id || "system"}</div>
                    <div style={{ color: "rgba(255,209,0,0.7)", fontSize: 11, fontFamily: "monospace" }}>{a.action}</div>
                    {a.meta && <div style={{ color: "rgba(255,255,255,0.3)", fontSize: 10, fontFamily: "monospace", marginTop: 2 }}>{JSON.stringify(a.meta)}</div>}
                  </div>
                  <div style={{ color: "rgba(255,255,255,0.35)", fontSize: 10, whiteSpace: "nowrap" }}>{a.at ? new Date(a.at).toLocaleString() : ""}</div>
                </div>
              ))
            }

            {/* Sage Session Audit — exec only */}
            {superExec && (
              <div style={{ marginTop: 24, borderTop: "1px solid rgba(255,255,255,0.08)", paddingTop: 20 }}>
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12, flexWrap: "wrap", gap: 8 }}>
                  <span style={{ color: SIG, fontWeight: 700, fontSize: 13 }}>Sage Session Audit (Exec)</span>
                  <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                    <select value={sageAuditKind} onChange={e => setSageAuditKind(e.target.value)}
                      style={{ background: "rgba(255,255,255,0.08)", border: "1px solid rgba(255,255,255,0.2)", borderRadius: 6, padding: "4px 8px", color: "white", fontSize: 11, cursor: "pointer" }}>
                      {["all","chat","refusal","crisis","consent"].map(k => <option key={k} value={k}>{k}</option>)}
                    </select>
                    <input value={sageAuditUid} onChange={e => setSageAuditUid(e.target.value)} placeholder="User ID filter…"
                      style={{ background: "rgba(255,255,255,0.08)", border: "1px solid rgba(255,255,255,0.2)", borderRadius: 6, padding: "4px 10px", color: "white", fontSize: 11, outline: "none", width: 130 }} />
                    <button onClick={() => loadSageAudit(sageAuditKind, sageAuditUid)}
                      style={{ background: "rgba(255,255,255,0.1)", border: "none", color: "white", padding: "4px 10px", borderRadius: 6, fontSize: 11, cursor: "pointer" }}>Search</button>
                  </div>
                </div>
                {sageAuditLog.length === 0
                  ? <p style={{ color: "rgba(255,255,255,0.35)", fontSize: 12 }}>No sage sessions. Adjust filters or click Search.</p>
                  : sageAuditLog.map((a, i) => (
                    <div key={a.id || i} style={{ display: "flex", gap: 10, padding: "6px 0", borderBottom: "1px solid rgba(255,255,255,0.05)", alignItems: "flex-start" }}>
                      <div style={{ width: 5, height: 5, borderRadius: "50%", background: a.refusal_reason ? "#f87171" : "#22c55e", marginTop: 6, flexShrink: 0 }} />
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ color: "white", fontSize: 11, fontWeight: 600 }}>{a.user_id || "anon"}</div>
                        <div style={{ color: "rgba(255,255,255,0.5)", fontSize: 10, fontFamily: "monospace" }}>
                          {a.persona || ""}{a.refusal_reason ? ` · REFUSED: ${a.refusal_reason}` : ""}
                        </div>
                        {a.messages?.[0]?.content && (
                          <div style={{ color: "rgba(255,255,255,0.3)", fontSize: 10, marginTop: 2, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", maxWidth: 300 }}>
                            {typeof a.messages[0].content === "string" ? a.messages[0].content.slice(0, 80) : ""}…
                          </div>
                        )}
                      </div>
                      <div style={{ color: "rgba(255,255,255,0.3)", fontSize: 9, whiteSpace: "nowrap" }}>{a.created_at ? new Date(a.created_at).toLocaleString() : ""}</div>
                    </div>
                  ))
                }
              </div>
            )}
          </div>
        )}

      </div>
    </div>
  );
}

// ── Default section visibility ─────────────────────────────────────────────────
const DEFAULT_VISIBILITY = {
  freeModules:  { label: "Free Modules",       minRank: 0 },
  features:     { label: "What We Do",         minRank: 0 },
  finance:      { label: "Finance Backbone",   minRank: 0 },
  roleLanes:    { label: "Role Lanes",         minRank: 0 },
  marketPulse:  { label: "Market Pulse",       minRank: 0 },
  governance:   { label: "Governance Pulse",   minRank: 0 },
  resources:    { label: "Resources",          minRank: 0 },
  support:      { label: "Support",            minRank: 0 },
};

// ── Visibility toggle panel ────────────────────────────────────────────────────
function VisibilityTab({ visibility, setVisibility }) {
  const RANK_LABELS = { 0: "Everyone", 1: "Students+", 2: "Instructors+", 3: "Admins+", 4: "Exec only" };
  const INK = "#2e1065"; const SIG = "#FFD100";
  return (
    <div>
      <div style={{ color: "white", fontWeight: 700, fontSize: 14, marginBottom: 6 }}>Section Visibility</div>
      <div style={{ color: "rgba(255,255,255,0.5)", fontSize: 11, marginBottom: 16 }}>
        Control which sections appear for each access level. Changes save instantly.
      </div>
      {Object.entries(visibility).map(([key, cfg]) => (
        <div key={key} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "8px 0", borderBottom: "1px solid rgba(255,255,255,0.07)" }}>
          <span style={{ color: "rgba(255,255,255,0.85)", fontSize: 13 }}>{cfg.label}</span>
          <div style={{ display: "flex", gap: 4 }}>
            {[0,1,2,3,4].map(rank => (
              <button key={rank} onClick={() => {
                const next = { ...visibility, [key]: { ...cfg, minRank: rank } };
                setVisibility(next);
                try { localStorage.setItem("mhc_visibility", JSON.stringify(next)); } catch {}
              }}
                style={{ padding: "3px 8px", borderRadius: 4, border: "none", fontSize: 10, fontWeight: 700, cursor: "pointer",
                  background: cfg.minRank === rank ? SIG : "rgba(255,255,255,0.12)",
                  color: cfg.minRank === rank ? INK : "rgba(255,255,255,0.6)" }}>
                {RANK_LABELS[rank]}
              </button>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

// ── Main component ─────────────────────────────────────────────────────────────
export default function MoreHelpCenter() {
  const { user } = useAuth();
  const [freeModules,  setFreeModules]  = useState([]);
  const [apiOnline,    setApiOnline]    = useState(null);
  const [gwLabel,      setGwLabel]      = useState("Checking…");
  const [visibility,   setVisibility]   = useState(() => {
    try { const s = localStorage.getItem("mhc_visibility"); return s ? JSON.parse(s) : DEFAULT_VISIBILITY; } catch { return DEFAULT_VISIBILITY; }
  });

  useEffect(() => {
    fetch(`${BACKEND_URL}/api/health`, { signal: AbortSignal.timeout(5000) })
      .then(r => { setApiOnline(r.ok); setGwLabel(r.ok ? "Gateway online" : "Gateway unavailable"); })
      .catch(() => { setApiOnline(false); setGwLabel("Gateway unavailable"); });
  }, []);

  useEffect(() => {
    if (apiOnline) {
      fetch(`${BACKEND_URL}/api/modules`)
        .then(r => r.ok ? r.json() : [])
        .then(data => setFreeModules((data || []).filter(m => m.free)))
        .catch(() => {});
    }
  }, [apiOnline]);

  if (apiOnline === null) {
    return (
      <div style={{ minHeight: "100vh", background: MARKET_BG, display: "flex", alignItems: "center", justifyContent: "center" }}>
        <div style={{ color: COPPER, fontSize: 14, fontFamily: "Georgia, serif" }}>Loading MORE Help Center…</div>
      </div>
    );
  }

  if (apiOnline === false && !isSupExec(user)) {
    return <DecoyMode />;
  }

  const execMode  = isSupExec(user);   // executive_admin only
  const superExec = isSupExec(user);
  const userRank  = ROLE_RANK[user?.role] ?? 0;
  const canSee    = (key) => userRank >= (visibility[key]?.minRank ?? 0);
  const modeMeta  = MODE_DETAILS[pageMode] || MODE_DETAILS.greeter;

  const USER_DASHBOARD = {
    executive_admin: { label: "Executive Dashboard", to: "/admin/system", color: GROVE },
    admin:           { label: "Admin Dashboard",      to: "/admin",        color: FOREST },
    instructor:      { label: "Instructor Hub",       to: "/instructor",   color: COPPER },
    student:         { label: "My Dashboard",         to: "/dashboard",    color: FOREST },
  };

  return (
    <div style={{ minHeight: "100vh", background: MARKET_BG, color: BARK }}>
      {/* Accent bar */}
      <div style={{ height: 5, background: `linear-gradient(90deg, ${BARK} 0%, ${TERRACOTTA} 25%, ${AMBER} 60%, ${COPPER} 100%)` }} />

      {/* ── Header ── */}
      <header style={{ position: "sticky", top: 0, zIndex: 40, background: "#ffffff", borderBottom: `1px solid ${EARTH}44` }}>
        <div style={{ maxWidth: 1200, margin: "0 auto", padding: "10px 24px", display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: 12 }}>
          <Link to="/more-help-center" style={{ display: "flex", alignItems: "center", gap: 10, textDecoration: "none" }}>
            <div style={{ width: 36, height: 36, borderRadius: 8, background: FOREST, display: "flex", alignItems: "center", justifyContent: "center", color: "white", fontWeight: 900, fontSize: 18 }}>M</div>
            <div>
              <div style={{ fontWeight: 800, fontSize: 14, color: FOREST, lineHeight: 1.2, fontFamily: "Georgia, serif" }}>MORE Help Center</div>
              <div style={{ fontSize: 10, fontWeight: 700, textTransform: "uppercase", letterSpacing: 3, color: COPPER }}>
                {execMode ? (superExec ? "Exec · Supervisor Mode" : "Admin Mode") : "Goodwill Wing"}
              </div>
            </div>
          </Link>

          <nav style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
            {NAV_LINKS.map(({ label, to }) => (
              <Link key={to} to={to} style={{ fontSize: 10, fontWeight: 800, textTransform: "uppercase", letterSpacing: 2, color: "white", textDecoration: "none", background: TERRACOTTA, padding: "4px 11px", borderRadius: 4 }}>{label}</Link>
            ))}
            {execMode && (
              <Link to="/admin/system" style={{ fontSize: 10, fontWeight: 800, textTransform: "uppercase", letterSpacing: 2, color: AMBER, textDecoration: "none", background: BARK, padding: "4px 11px", borderRadius: 4, display: "flex", alignItems: "center", gap: 4 }}>
                <Crown style={{ width: 12, height: 12 }} /> Dashboard
              </Link>
            )}
            {!user && (
              <Link to="/login" style={{ background: AMBER, color: BARK, padding: "6px 16px", borderRadius: 4, fontSize: 11, fontWeight: 800, textDecoration: "none" }}>Sign In →</Link>
            )}
          </nav>
        </div>
      </header>

      <main style={{ maxWidth: 1200, margin: "0 auto", padding: "0 24px" }}>

        {/* ── Hero ── */}
        <section style={{ borderRadius: 16, overflow: "hidden", marginTop: 32, marginBottom: 28, background: `linear-gradient(165deg, ${BARK} 0%, ${TERRACOTTA} 35%, ${AMBER} 70%, ${COPPER} 100%)`, padding: "56px 40px", textAlign: "center", position: "relative" }}>
          <div style={{ position: "absolute", inset: 0, opacity: 0.07, backgroundImage: "radial-gradient(circle at 20px 20px, #f5e6c8 1.5px, transparent 0)", backgroundSize: "40px 40px" }} />
          <div style={{ position: "relative", zIndex: 1 }}>
            <div style={{ display: "inline-flex", alignItems: "center", gap: 6, padding: "6px 16px", borderRadius: 4, background: "rgba(0,0,0,0.25)", color: AMBER, fontSize: 11, fontWeight: 800, textTransform: "uppercase", letterSpacing: 3, marginBottom: 24 }}>
              <Heart style={{ width: 12, height: 12 }} /> 100% Free · Community-Powered
            </div>
            <h1 style={{ color: "white", fontSize: "clamp(32px, 6vw, 56px)", fontWeight: 900, lineHeight: 1.1, marginBottom: 16, fontFamily: "Georgia, serif" }}>
              Help is here.<br /><span style={{ color: AMBER }}>Free, always.</span>
            </h1>
            <p style={{ color: "#ffe8cc", fontSize: 18, maxWidth: 560, margin: "0 auto 28px", lineHeight: 1.7 }}>
              No paywalls. No sign-ups for core help. Free training, community support, and real guidance — no strings attached.
            </p>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 12, justifyContent: "center" }}>
              <a href="#modules" style={{ background: AMBER, color: BARK, padding: "12px 28px", borderRadius: 4, fontWeight: 800, fontSize: 13, textDecoration: "none", textTransform: "uppercase", letterSpacing: 2 }}>Start Learning Free</a>
              <a href="#support" style={{ border: `2px solid ${AMBER}`, color: "white", padding: "12px 28px", borderRadius: 4, fontWeight: 800, fontSize: 13, textDecoration: "none", textTransform: "uppercase", letterSpacing: 2 }}>Get Support</a>
              <Link to="/community" style={{ border: "2px solid rgba(255,255,255,0.5)", color: "white", padding: "12px 28px", borderRadius: 4, fontWeight: 800, fontSize: 13, textDecoration: "none", textTransform: "uppercase", letterSpacing: 2 }}>Join Community</Link>
            </div>
          </div>
        </section>

        {/* ── Logged-in user card ── */}
        {user && USER_DASHBOARD[user.role] && (
          <div style={{ background: "white", borderRadius: 10, border: `1px solid ${EARTH}44`, padding: "14px 20px", marginBottom: 24, display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: 12 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <div style={{ width: 36, height: 36, borderRadius: "50%", background: USER_DASHBOARD[user.role].color, display: "flex", alignItems: "center", justifyContent: "center", color: "white", fontWeight: 900, fontSize: 14 }}>
                {(user.full_name || "U")[0].toUpperCase()}
              </div>
              <div>
                <div style={{ fontWeight: 700, fontSize: 14, color: BARK }}>Welcome back, {user.full_name?.split(" ")[0] || "there"}.</div>
                <div style={{ fontSize: 11, color: COPPER, textTransform: "capitalize" }}>{(user.role || "").replace("_", " ")} · WAI-Institute</div>
              </div>
            </div>
            <Link to={USER_DASHBOARD[user.role].to} style={{ background: USER_DASHBOARD[user.role].color, color: "white", padding: "8px 18px", borderRadius: 6, fontWeight: 700, fontSize: 12, textDecoration: "none", display: "flex", alignItems: "center", gap: 6 }}>
              {USER_DASHBOARD[user.role].label} <ArrowRight style={{ width: 13, height: 13 }} />
            </Link>
          </div>
        )}

        {/* ── Exec Supervisor Panel ── */}
        {execMode && (
          <div style={{ marginBottom: 32 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 16 }}>
              <Crown style={{ width: 18, height: 18, color: AMBER }} />
              <span style={{ fontWeight: 800, fontSize: 16, color: BARK, fontFamily: "Georgia, serif" }}>Supervisor Controls</span>
              <span style={{ fontSize: 11, color: COPPER, background: CARVED_BG, padding: "2px 8px", borderRadius: 20, fontWeight: 700, textTransform: "uppercase", letterSpacing: 1 }}>
                {superExec ? "Executive Admin" : "Admin"}
              </span>
            </div>
            <ExecPanel apiOnline={apiOnline} visibility={visibility} setVisibility={setVisibility} superExec={superExec} />
          </div>
        )}

        {/* ── Gateway status strip ── */}
        <div style={{ background: "white", borderRadius: 8, padding: "12px 20px", marginBottom: 32, display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: 12, border: `1px solid ${EARTH}44` }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <div style={{ width: 8, height: 8, borderRadius: "50%", background: apiOnline ? "#22c55e" : "#dc2626" }} />
            <span style={{ fontSize: 13, fontWeight: 600, color: BARK }}>{gwLabel}</span>
          </div>
          <div style={{ display: "flex", gap: 16, flexWrap: "wrap" }}>
            {[
              { label: "WAI Help Center",    to: "/help-center" },
              { label: "Explore M.O.R.E.",   to: "/more" },
              { label: "Plans & Programs",   to: "/plans" },
              ...(execMode ? [{ label: "Executive Corridor", to: "/admin/system" }] : []),
            ].map(({ label, to }) => (
              <Link key={to} to={to} style={{ fontSize: 12, fontWeight: 700, color: TERRACOTTA, textDecoration: "underline" }}>{label}</Link>
            ))}
          </div>
        </div>

        {/* ── Supervisor Controls ── */}
        <section id="supervisor-controls" style={{ marginBottom: 48 }}>
          <div style={{ textAlign: "center", marginBottom: 28 }}>
            <CarvedHeader label="Supervisor Controls" />
            <h2 style={{ fontSize: 28, fontWeight: 900, color: BARK, fontFamily: "Georgia, serif", marginTop: 8 }}>Choose your permission level</h2>
            <p style={{ color: EARTH, marginTop: 8, maxWidth: 560, margin: "8px auto 0" }}>
              Public users can browse help resources. Supervisors may sign in and access secure executive controls inside the same MORE Help Center.
            </p>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(240px,1fr))", gap: 20, marginBottom: superExec ? 32 : 0 }}>
            {SUPERVISOR_TOGGLES.map((item) => (
              <a key={item.label} href={item.href} style={{ display: "block", borderRadius: 24, padding: "24px 28px", background: item.bg, color: item.color, textDecoration: "none", boxShadow: "0 20px 45px rgba(97,64,35,0.08)", transition: "transform 0.15s" }}
                onMouseOver={e => e.currentTarget.style.transform = "translateY(-4px)"}
                onMouseOut={e => e.currentTarget.style.transform = "none"}>
                <div style={{ fontSize: 11, textTransform: "uppercase", letterSpacing: "0.4em", fontWeight: 800, marginBottom: 10 }}>{item.label}</div>
                <div style={{ fontSize: 14, lineHeight: 1.6 }}>{item.description}</div>
              </a>
            ))}
          </div>

          {/* Exec-only: mode switcher + mode description card */}
          {superExec && (
            <div style={{ borderRadius: 24, border: `1px solid ${EARTH}44`, background: "white", padding: 28, boxShadow: "0 20px 60px rgba(97,60,20,0.08)" }}>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 16, alignItems: "flex-start", justifyContent: "space-between", marginBottom: 24 }}>
                <div>
                  <CarvedHeader label="Executive mode" />
                  <h3 style={{ fontSize: 24, fontWeight: 900, color: BARK, fontFamily: "Georgia, serif", marginTop: 8 }}>Supervisor mode controls</h3>
                  <p style={{ color: EARTH, marginTop: 6, maxWidth: 480, fontSize: 14, lineHeight: 1.7 }}>
                    Switch between the MORE Help Center's display modes: public greeting, executive oversight, or fallback support.
                  </p>
                </div>
                <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                  {PANEL_MODES.map((m) => (
                    <button key={m.id} onClick={() => {
                      setPageMode(m.id);
                      try { localStorage.setItem("more_help_center_mode", m.id); } catch {}
                    }}
                      style={{ borderRadius: 999, padding: "10px 20px", fontSize: 13, fontWeight: 800, textTransform: "uppercase", letterSpacing: "0.18em", cursor: "pointer", border: "none", transition: "background 0.15s",
                        background: pageMode === m.id ? EARTH : CARVED_BG,
                        color: pageMode === m.id ? "white" : BARK }}>
                      {m.label}
                    </button>
                  ))}
                </div>
              </div>
              <div style={{ borderRadius: 20, border: `1px solid ${EARTH}66`, background: CARVED_BG, padding: "28px 32px" }}>
                <div style={{ fontSize: 11, textTransform: "uppercase", letterSpacing: "0.35em", fontWeight: 800, color: COPPER, marginBottom: 12 }}>{modeMeta.title}</div>
                <p style={{ fontSize: 16, color: BARK, lineHeight: 1.7, marginBottom: 10 }}>{modeMeta.summary}</p>
                <p style={{ fontSize: 13, color: EARTH, marginBottom: 20 }}>{modeMeta.action}</p>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(160px,1fr))", gap: 10 }}>
                  {modeMeta.links.map((link) => (
                    <Link key={link.to} to={link.to} style={{ borderRadius: 20, border: `1px solid ${EARTH}55`, background: "#fff5e0", padding: "14px 18px", fontSize: 13, fontWeight: 600, color: BARK, textDecoration: "none", transition: "transform 0.12s" }}
                      onMouseOver={e => e.currentTarget.style.transform = "translateY(-2px)"}
                      onMouseOut={e => e.currentTarget.style.transform = "none"}>
                      {link.label}
                    </Link>
                  ))}
                </div>
              </div>
            </div>
          )}
        </section>

        {/* ── Waypoints ── */}
        <section style={{ marginBottom: 48 }}>
          <div style={{ marginBottom: 24 }}>
            <CarvedHeader label="How the plaza works" />
            <h2 style={{ fontSize: 28, fontWeight: 900, color: BARK, fontFamily: "Georgia, serif", marginTop: 8 }}>Your path through the center</h2>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(220px,1fr))", gap: 16 }}>
            {WAYPOINTS.map(pt => {
              const Icon = pt.icon;
              return (
                <div key={pt.title} style={{ background: SAND, borderRadius: 8, padding: 24, border: `1px solid ${EARTH}66`, boxShadow: `0 14px 35px rgba(139,69,19,0.08)` }}>
                  <div style={{ width: 48, height: 48, borderRadius: 12, background: TERRACOTTA, display: "flex", alignItems: "center", justifyContent: "center", color: "white", marginBottom: 16 }}>
                    <Icon style={{ width: 22, height: 22 }} />
                  </div>
                  <h3 style={{ fontWeight: 800, fontSize: 16, color: BARK, marginBottom: 8, fontFamily: "Georgia, serif" }}>{pt.title}</h3>
                  <p style={{ fontSize: 13, color: EARTH, lineHeight: 1.6 }}>{pt.desc}</p>
                </div>
              );
            })}
          </div>
        </section>

        {/* ── Free Modules ── */}
        {canSee("freeModules") && freeModules.length > 0 && (
          <section id="modules" style={{ marginBottom: 48 }}>
            <div style={{ textAlign: "center", marginBottom: 32 }}>
              <CarvedHeader label="Free Curriculum" />
              <h2 style={{ fontSize: 28, fontWeight: 900, color: BARK, fontFamily: "Georgia, serif", marginTop: 8 }}>Start Here — No Account Needed</h2>
              <p style={{ color: EARTH, marginTop: 8 }}>Complete free modules and earn Partnership Points toward the full program.</p>
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(280px,1fr))", gap: 20 }}>
              {freeModules.map(m => (
                <Link to={`/modules/${m.slug}`} key={m.slug} style={{ display: "block", padding: 24, borderRadius: 8, background: CARVED_BG, border: `1px solid ${EARTH}55`, textDecoration: "none" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 12 }}>
                    <span style={{ background: AMBER, color: BARK, padding: "3px 10px", borderRadius: 4, fontSize: 10, fontWeight: 900, textTransform: "uppercase" }}>FREE</span>
                    {m.points && <span style={{ fontSize: 12, fontWeight: 700, color: FOREST }}>+{m.points} pts</span>}
                  </div>
                  <h3 style={{ fontWeight: 800, fontSize: 18, color: BARK, marginBottom: 8, fontFamily: "Georgia, serif" }}>{m.title}</h3>
                  <p style={{ fontSize: 13, color: EARTH, lineHeight: 1.6 }}>{m.summary}</p>
                  <div style={{ display: "flex", gap: 16, marginTop: 14, fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: 1, color: FOREST }}>
                    <span>{m.hours}h</span>
                    <ArrowRight style={{ width: 13, height: 13 }} />
                  </div>
                </Link>
              ))}
            </div>
            <div style={{ textAlign: "center", marginTop: 24 }}>
              <Link to="/register" style={{ display: "inline-flex", alignItems: "center", gap: 8, padding: "10px 24px", border: `2px solid ${FOREST}`, borderRadius: 4, color: FOREST, fontWeight: 700, fontSize: 13, textDecoration: "none", textTransform: "uppercase", letterSpacing: 1 }}>
                Create Account for Full Program <ArrowRight style={{ width: 15, height: 15 }} />
              </Link>
            </div>
          </section>
        )}

        {/* ── Features — market-stall grid ── */}
        {canSee("features") && (
          <section style={{ marginBottom: 48 }}>
            <div style={{ display: "flex", alignItems: "flex-end", justifyContent: "space-between", marginBottom: 24, flexWrap: "wrap", gap: 12 }}>
              <div>
                <CarvedHeader label="Designed around the hub" />
                <h2 style={{ fontSize: 28, fontWeight: 900, color: BARK, fontFamily: "Georgia, serif", marginTop: 8 }}>What this center is built to do</h2>
              </div>
              <div style={{ background: CARVED_BG, border: `1px solid ${EARTH}55`, borderRadius: 4, padding: "8px 18px", fontSize: 13, fontWeight: 600, color: BARK }}>
                Finance-led autonomy + community guidance
              </div>
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(260px,1fr))", gap: 20 }}>
              {FEATURES.map(f => {
                const Icon = f.icon;
                return (
                  <div key={f.title} style={{ background: "white", borderRadius: 0, padding: 28, border: `2px solid ${TERRACOTTA}88`, borderTop: `4px solid ${TERRACOTTA}`, boxShadow: `0 20px 45px rgba(193,68,14,0.08)` }}>
                    <div style={{ width: 52, height: 52, borderRadius: 8, background: TERRACOTTA, display: "flex", alignItems: "center", justifyContent: "center", color: "white", marginBottom: 16 }}>
                      <Icon style={{ width: 24, height: 24 }} />
                    </div>
                    <h3 style={{ fontWeight: 800, fontSize: 18, color: BARK, marginBottom: 8, fontFamily: "Georgia, serif" }}>{f.title}</h3>
                    <p style={{ fontSize: 13, color: EARTH, lineHeight: 1.7 }}>{f.desc}</p>
                  </div>
                );
              })}
            </div>
          </section>
        )}

        {/* ── Finance backbone ── */}
        {canSee("finance") && (
          <section style={{ marginBottom: 48, background: SAND, borderRadius: 12, border: `1px solid ${EARTH}88`, padding: "40px 36px", boxShadow: `0 24px 80px rgba(139,69,19,0.10)` }}>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(280px,1fr))", gap: 32, alignItems: "start" }}>
              <div>
                <CarvedHeader label="Finance Backbone" />
                <h2 style={{ fontSize: 30, fontWeight: 900, color: BARK, marginBottom: 16, fontFamily: "Georgia, serif", marginTop: 8 }}>The finance department acts like its own autonomous staff.</h2>
                <p style={{ fontSize: 15, color: EARTH, lineHeight: 1.8, marginBottom: 20 }}>
                  Every resource in the center is supported by finance, compliance, and revenue operations — making this not just a landing spot, but a living marketplace.
                </p>
                <ul style={{ listStyle: "none", padding: 0 }}>
                  {["Real-time budget visibility for help center initiatives.", "Compliance and approvals built into autonomous workflows.", "Finance staff personas coordinate with production, legal, and community teams."].map(item => (
                    <li key={item} style={{ display: "flex", gap: 10, marginBottom: 12, fontSize: 14, color: BARK }}>
                      <BadgeCheck style={{ width: 18, height: 18, color: TERRACOTTA, marginTop: 2, flexShrink: 0 }} /> {item}
                    </li>
                  ))}
                </ul>
              </div>
              <div style={{ background: `rgba(193,68,14,0.07)`, borderRadius: 8, border: `1px solid ${TERRACOTTA}55`, padding: 24 }}>
                <CarvedHeader label="Supervisor briefing" />
                <p style={{ fontSize: 13, color: BARK, lineHeight: 1.7, marginBottom: 12, marginTop: 8 }}>
                  The Supervisor is the landing greeter and navigator — the host offering a warm welcome and making the mission obvious from the first moment.
                </p>
                <p style={{ fontSize: 13, fontWeight: 700, color: BARK, lineHeight: 1.7 }}>
                  Human oversight is a must-have: executive review, audit checkpoints, and real people ensure every action is safe, compliant, and accountable.
                </p>
                <div style={{ marginTop: 16, background: `rgba(123,63,0,0.08)`, borderRadius: 8, padding: 16 }}>
                  <div style={{ fontWeight: 700, color: BARK, fontSize: 13 }}>Gateway status</div>
                  <div style={{ fontSize: 16, fontWeight: 800, color: apiOnline ? "#166534" : "#991b1b", marginTop: 6 }}>{gwLabel}</div>
                </div>
              </div>
            </div>
          </section>
        )}

        {/* ── Role lanes ── */}
        {canSee("roleLanes") && (
          <section style={{ marginBottom: 48 }}>
            <div style={{ marginBottom: 24 }}>
              <CarvedHeader label="Role-based lanes" />
              <h2 style={{ fontSize: 28, fontWeight: 900, color: BARK, fontFamily: "Georgia, serif", marginTop: 8 }}>Choose your entry path</h2>
              <p style={{ marginTop: 8, fontSize: 14, color: EARTH, maxWidth: 480 }}>
                The center supports different personas with specific corridors: visitors, operators, supervisors, and auditors all have distinct journeys.
              </p>
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(200px,1fr))", gap: 16 }}>
              {ROLE_LANES.map(lane => {
                const Icon = lane.icon;
                return (
                  <div key={lane.title} style={{ background: SAND, borderRadius: 8, padding: 24, border: `1px solid ${EARTH}66`, boxShadow: `0 18px 45px rgba(193,68,14,0.08)` }}>
                    <div style={{ width: 44, height: 44, borderRadius: 10, background: TERRACOTTA, display: "flex", alignItems: "center", justifyContent: "center", color: "white", marginBottom: 14 }}>
                      <Icon style={{ width: 20, height: 20 }} />
                    </div>
                    <h3 style={{ fontWeight: 800, fontSize: 16, color: BARK, marginBottom: 8, fontFamily: "Georgia, serif" }}>{lane.title}</h3>
                    <p style={{ fontSize: 13, color: EARTH, lineHeight: 1.6 }}>{lane.desc}</p>
                  </div>
                );
              })}
            </div>
          </section>
        )}

        {/* ── Market Pulse ── */}
        {canSee("marketPulse") && (
          <section style={{ marginBottom: 48 }}>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(280px,1fr))", gap: 32, alignItems: "start" }}>
              <div>
                <CarvedHeader label="Meet the market" />
                <h2 style={{ fontSize: 28, fontWeight: 900, color: BARK, marginBottom: 16, fontFamily: "Georgia, serif", marginTop: 8 }}>What visitors do here</h2>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(200px,1fr))", gap: 16 }}>
                  {[
                    { icon: MapPin, title: "Receive a guided welcome",  desc: "The Supervisor points new visitors to platform support, finance tools, and the help center." },
                    { icon: Globe,  title: "Access the help center",     desc: "Find help across housing, legal, training, and community resources with a single click." },
                    { icon: Users,  title: "Join the market experience", desc: "Browse the community marketplace of services, courses, and production support." },
                  ].map(item => {
                    const Icon = item.icon;
                    return (
                      <div key={item.title} style={{ background: SAND, borderRadius: 8, padding: 24, border: `1px solid ${EARTH}66`, boxShadow: `0 18px 45px rgba(139,69,19,0.08)` }}>
                        <div style={{ width: 44, height: 44, borderRadius: 10, background: TERRACOTTA, display: "flex", alignItems: "center", justifyContent: "center", color: "white", marginBottom: 14 }}>
                          <Icon style={{ width: 20, height: 20 }} />
                        </div>
                        <h3 style={{ fontWeight: 800, fontSize: 16, color: BARK, marginBottom: 8, fontFamily: "Georgia, serif" }}>{item.title}</h3>
                        <p style={{ fontSize: 13, color: EARTH, lineHeight: 1.7 }}>{item.desc}</p>
                      </div>
                    );
                  })}
                </div>
              </div>
              <div style={{ background: CARVED_BG, borderRadius: 8, border: `1px solid ${EARTH}66`, padding: 24, boxShadow: `0 14px 50px rgba(139,69,19,0.08)` }}>
                <CarvedHeader label="Market Pulse" />
                <div style={{ fontSize: 20, fontWeight: 800, color: BARK, marginBottom: 20, fontFamily: "Georgia, serif", marginTop: 8 }}>Live services in this plaza</div>
                <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                  <Link to="/help-center" style={{ display: "block", borderRadius: 0, padding: "14px 18px", fontSize: 13, fontWeight: 700, textDecoration: "none", background: AMBER, color: BARK, fontFamily: "Georgia, serif" }}>Visit the Help Center</Link>
                  <Link to="/more"        style={{ display: "block", borderRadius: 0, padding: "14px 18px", fontSize: 13, fontWeight: 700, textDecoration: "none", background: TERRACOTTA, color: "white", fontFamily: "Georgia, serif" }}>Explore M.O.R.E.</Link>
                  <Link to="/community"   style={{ display: "block", borderRadius: 0, padding: "14px 18px", fontSize: 13, fontWeight: 700, textDecoration: "none", background: FOREST, color: "white", fontFamily: "Georgia, serif" }}>Community Marketplace</Link>
                  {execMode && (
                    <Link to="/admin/system" style={{ display: "block", borderRadius: 0, padding: "14px 18px", fontSize: 13, fontWeight: 700, textDecoration: "none", background: GROVE, color: AMBER, fontFamily: "Georgia, serif" }}>Executive Oversight</Link>
                  )}
                </div>
              </div>
            </div>
          </section>
        )}

        {/* ── Governance Pulse ── */}
        {canSee("governance") && (
          <section style={{ marginBottom: 48, background: SAND, borderRadius: 12, border: `1px solid ${EARTH}88`, padding: "36px 32px", boxShadow: `0 24px 60px rgba(139,69,19,0.10)` }}>
            <div style={{ display: "flex", alignItems: "flex-end", justifyContent: "space-between", flexWrap: "wrap", gap: 12, marginBottom: 24 }}>
              <div>
                <CarvedHeader label="Governance pulse" />
                <h2 style={{ fontSize: 26, fontWeight: 900, color: BARK, fontFamily: "Georgia, serif", marginTop: 8 }}>Live oversight, analytics, and process flow</h2>
              </div>
              <div style={{ background: CARVED_BG, border: `1px solid ${EARTH}55`, borderRadius: 4, padding: "7px 16px", fontSize: 13, fontWeight: 600, color: BARK }}>
                Built for human review and executive visibility
              </div>
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(280px,1fr))", gap: 20 }}>
              <div style={{ background: "white", borderRadius: 8, padding: 24, border: `1px solid ${EARTH}66`, boxShadow: `0 18px 50px rgba(193,68,14,0.08)` }}>
                <CarvedHeader label="Process map" />
                <div style={{ display: "flex", flexDirection: "column", gap: 10, marginTop: 8 }}>
                  {[
                    { step: "1. Request", desc: "A visitor enters the plaza and selects help, service, finance, or community support." },
                    { step: "2. Review",  desc: "The Supervisor and operator lane assess the need, apply compliance checks, and route the request." },
                    { step: "3. Approve", desc: "Human oversight verifies decisions, triggers executive visibility, or escalates to audit if needed." },
                    { step: "4. Execute", desc: "Workflows are completed and results are published to the help system for future reference." },
                  ].map(s => (
                    <div key={s.step} style={{ background: `rgba(193,68,14,0.07)`, borderRadius: 8, padding: "12px 16px" }}>
                      <div style={{ fontWeight: 700, color: BARK, fontSize: 13, fontFamily: "Georgia, serif" }}>{s.step}</div>
                      <div style={{ fontSize: 12, color: EARTH, marginTop: 4, lineHeight: 1.6 }}>{s.desc}</div>
                    </div>
                  ))}
                </div>
              </div>
              <div style={{ background: CARVED_BG, borderRadius: 8, padding: 24, border: `1px solid ${EARTH}66`, boxShadow: `0 18px 50px rgba(193,68,14,0.08)` }}>
                <CarvedHeader label="Service ownership" />
                <div style={{ marginTop: 8 }}>
                  {[
                    { owner: "Finance",    desc: "Manages budgets, approvals, and audit trails for every community and help service." },
                    { owner: "Compliance", desc: "Verifies that recommendations follow policy, privacy, and safety standards." },
                    { owner: "Community",  desc: "Operates the marketplace lanes and ensures each service has a visible help manual entry." },
                  ].map(s => (
                    <div key={s.owner} style={{ marginBottom: 16 }}>
                      <div style={{ fontWeight: 700, color: BARK, fontSize: 14, fontFamily: "Georgia, serif" }}>{s.owner}</div>
                      <div style={{ fontSize: 12, color: EARTH, marginTop: 4, lineHeight: 1.6 }}>{s.desc}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </section>
        )}

        {/* ── Forest Court · Legal Clearing ── */}
        <section style={{ marginBottom: 48, background: GROVE, borderRadius: 12, padding: "40px 36px" }}>
          <div style={{ marginBottom: 28, textAlign: "center" }}>
            <div style={{ fontSize: 11, fontWeight: 800, textTransform: "uppercase", letterSpacing: "0.2em", color: AMBER, marginBottom: 6, fontFamily: "Georgia, serif", borderBottom: `2px solid ${AMBER}55`, paddingBottom: 4, display: "inline-block" }}>
              ✦ Forest Court
            </div>
            <h2 style={{ fontSize: 28, fontWeight: 900, color: "white", fontFamily: "Georgia, serif", marginTop: 10, marginBottom: 10 }}>Legal Clearing</h2>
            <p style={{ color: "#c8e6c9", fontSize: 15, maxWidth: 520, margin: "0 auto", lineHeight: 1.7 }}>
              Where disputes are heard, rights are protected, and community law is made plain.
            </p>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(220px,1fr))", gap: 16, marginBottom: 28 }}>
            {[
              { icon: Shield,      title: "Community Rights",   desc: "Plain-language summaries of your rights as a community member, student, and creator." },
              { icon: ShieldCheck, title: "Compliance Lane",    desc: "Governance, privacy, and policy verification built into every workflow." },
              { icon: BadgeCheck,  title: "Dispute Resolution", desc: "Human oversight at every escalation point — no automated final decisions." },
            ].map(card => {
              const Icon = card.icon;
              return (
                <div key={card.title} style={{ background: "white", borderRadius: 8, padding: 24, border: `1px solid ${TERRACOTTA}55` }}>
                  <div style={{ width: 44, height: 44, borderRadius: 10, background: FOREST, display: "flex", alignItems: "center", justifyContent: "center", color: AMBER, marginBottom: 14 }}>
                    <Icon style={{ width: 20, height: 20 }} />
                  </div>
                  <h3 style={{ fontWeight: 800, fontSize: 16, color: BARK, marginBottom: 8, fontFamily: "Georgia, serif" }}>{card.title}</h3>
                  <p style={{ fontSize: 13, color: EARTH, lineHeight: 1.6 }}>{card.desc}</p>
                </div>
              );
            })}
          </div>
          <div style={{ display: "flex", gap: 12, justifyContent: "center", flexWrap: "wrap" }}>
            <Link to="/help-center" style={{ display: "inline-flex", alignItems: "center", gap: 8, background: AMBER, color: BARK, padding: "11px 28px", borderRadius: 4, fontWeight: 800, fontSize: 13, textDecoration: "none", textTransform: "uppercase", letterSpacing: 1, fontFamily: "Georgia, serif" }}>
              Legal Resources <ArrowRight style={{ width: 14, height: 14 }} />
            </Link>
            <Link to="/terms" style={{ display: "inline-flex", alignItems: "center", gap: 8, background: "transparent", color: AMBER, border: `2px solid ${AMBER}`, padding: "11px 28px", borderRadius: 4, fontWeight: 800, fontSize: 13, textDecoration: "none", textTransform: "uppercase", letterSpacing: 1, fontFamily: "Georgia, serif" }}>
              Accept Legal Terms
            </Link>
          </div>
        </section>

        {/* ── Creator's Sanctuary ── */}
        <section style={{ marginBottom: 48, background: SAND, borderRadius: 12, border: `2px solid ${FOREST}55`, padding: "40px 36px" }}>
          <div style={{ marginBottom: 28, textAlign: "center" }}>
            <div style={{ fontSize: 11, fontWeight: 800, textTransform: "uppercase", letterSpacing: "0.2em", color: FOREST, marginBottom: 6, fontFamily: "Georgia, serif", borderBottom: `2px solid ${FOREST}`, paddingBottom: 4, display: "inline-block" }}>
              ✦ Protected Space
            </div>
            <h2 style={{ fontSize: 28, fontWeight: 900, color: BARK, fontFamily: "Georgia, serif", marginTop: 10, marginBottom: 10 }}>Creator's Sanctuary</h2>
            <p style={{ color: EARTH, fontSize: 15, maxWidth: 520, margin: "0 auto", lineHeight: 1.7 }}>
              A protected space for artists, educators, authors, and storytellers building inside the WAI ecosystem.
            </p>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(220px,1fr))", gap: 16, marginBottom: 28 }}>
            {[
              { icon: Sparkles,  title: "Course Builder",       desc: "Build and publish your own training modules with instructor tools." },
              { icon: Activity,  title: "Media Production",     desc: "Video, audio, and written content tools keep the community vibrant." },
              { icon: BookOpen,  title: "Publishing Pipeline",  desc: "From manuscript to Gumroad listing — the full book pipeline is here." },
            ].map(card => {
              const Icon = card.icon;
              return (
                <div key={card.title} style={{ background: "white", borderRadius: 8, padding: 24, border: `1px solid ${EARTH}66`, boxShadow: `0 14px 35px rgba(45,106,79,0.07)` }}>
                  <div style={{ width: 44, height: 44, borderRadius: 10, background: GROVE, display: "flex", alignItems: "center", justifyContent: "center", color: AMBER, marginBottom: 14 }}>
                    <Icon style={{ width: 20, height: 20 }} />
                  </div>
                  <h3 style={{ fontWeight: 800, fontSize: 16, color: BARK, marginBottom: 8, fontFamily: "Georgia, serif" }}>{card.title}</h3>
                  <p style={{ fontSize: 13, color: EARTH, lineHeight: 1.6 }}>{card.desc}</p>
                </div>
              );
            })}
          </div>
          <div style={{ textAlign: "center" }}>
            <Link to="/social/publish" style={{ display: "inline-flex", alignItems: "center", gap: 8, background: GROVE, color: AMBER, padding: "11px 28px", borderRadius: 4, fontWeight: 800, fontSize: 13, textDecoration: "none", textTransform: "uppercase", letterSpacing: 1, fontFamily: "Georgia, serif" }}>
              Enter the Sanctuary <ArrowRight style={{ width: 14, height: 14 }} />
            </Link>
          </div>
        </section>

        {/* ── Resources ── */}
        {canSee("resources") && (
          <section id="resources" style={{ marginBottom: 48 }}>
            <div style={{ textAlign: "center", marginBottom: 32 }}>
              <CarvedHeader label="Goodwill Resources" />
              <h2 style={{ fontSize: 28, fontWeight: 900, color: BARK, fontFamily: "Georgia, serif", marginTop: 8 }}>Everything You Need, No Cost</h2>
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(220px,1fr))", gap: 16 }}>
              {[
                { icon: BookOpen,      title: "Free Modules",  desc: "Hands-on training free forever.",             to: "/modules",      internal: true },
                { icon: MessageSquare, title: "Community",     desc: "Real answers from real people.",              to: "/community",    internal: true },
                { icon: Shield,        title: "Support Line",  desc: "Email us — no bots, no runaround.",           to: `mailto:${SUPPORT_EMAIL}`, internal: false },
                { icon: Globe,         title: "Full Program",  desc: "Enroll in the complete WAI curriculum.",      to: "/courses",      internal: true },
                { icon: BadgeCheck,    title: "Help Center",   desc: "Core support and community navigation.",      to: "/help-center",  internal: true },
                { icon: Activity,      title: "Plans",         desc: "Training, services, and subscriptions.",      to: "/plans",        internal: true },
              ].map(r => {
                const Icon = r.icon;
                const content = (
                  <>
                    <div style={{ width: 40, height: 40, borderRadius: 8, background: TERRACOTTA, display: "flex", alignItems: "center", justifyContent: "center", marginBottom: 14 }}>
                      <Icon style={{ width: 18, height: 18, color: "white" }} />
                    </div>
                    <h3 style={{ fontWeight: 800, fontSize: 16, color: BARK, marginBottom: 6, fontFamily: "Georgia, serif" }}>{r.title}</h3>
                    <p style={{ fontSize: 13, color: EARTH, lineHeight: 1.6 }}>{r.desc}</p>
                  </>
                );
                const sharedStyle = { display: "block", background: CARVED_BG, padding: 22, borderRadius: 8, border: `1px solid ${EARTH}55`, textDecoration: "none" };
                return r.internal
                  ? <Link key={r.title} to={r.to} style={sharedStyle}>{content}</Link>
                  : <a    key={r.title} href={r.to} style={sharedStyle}>{content}</a>;
              })}
            </div>
          </section>
        )}

        {/* ── Support ── */}
        {canSee("support") && (
          <section id="support" style={{ textAlign: "center", background: SAND, borderRadius: 12, padding: "48px 32px", marginBottom: 48, border: `1px solid ${EARTH}88` }}>
            <div style={{ display: "inline-flex", alignItems: "center", gap: 8, padding: "6px 16px", borderRadius: 4, background: TERRACOTTA, color: AMBER, fontSize: 11, fontWeight: 800, textTransform: "uppercase", letterSpacing: 2, marginBottom: 20 }}>
              <Phone style={{ width: 13, height: 13 }} /> Get In Touch
            </div>
            <h2 style={{ fontSize: 28, fontWeight: 900, color: BARK, marginBottom: 12, fontFamily: "Georgia, serif" }}>Need Help?</h2>
            <p style={{ fontSize: 16, color: EARTH, maxWidth: 480, margin: "0 auto 28px" }}>
              Email us at{" "}
              <a href={`mailto:${SUPPORT_EMAIL}`} style={{ color: TERRACOTTA, fontWeight: 700 }}>{SUPPORT_EMAIL}</a>
              {" "}— we respond within 24 hours.
            </p>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 12, justifyContent: "center" }}>
              <a href={`mailto:${SUPPORT_EMAIL}`} style={{ background: TERRACOTTA, color: "white", padding: "11px 24px", borderRadius: 4, fontWeight: 700, fontSize: 13, textDecoration: "none" }}>Email Support</a>
              <Link to="/help-center" style={{ border: `2px solid ${TERRACOTTA}`, color: BARK, padding: "11px 24px", borderRadius: 4, fontWeight: 700, fontSize: 13, textDecoration: "none" }}>Help Center</Link>
              <Link to="/community"   style={{ border: `2px solid ${TERRACOTTA}`, color: BARK, padding: "11px 24px", borderRadius: 4, fontWeight: 700, fontSize: 13, textDecoration: "none" }}>Community Forum</Link>
            </div>
          </section>
        )}

        {/* ── Exec-only Governance Pulse ── */}
        {execMode && canSee("governance") && (
          <section style={{ marginBottom: 48, background: CARVED_BG, borderRadius: 12, border: `1px solid ${EARTH}88`, padding: "36px 32px" }}>
            <div style={{ marginBottom: 20 }}>
              <CarvedHeader label="Governance pulse" />
              <h2 style={{ fontSize: 24, fontWeight: 900, color: BARK, fontFamily: "Georgia, serif", marginTop: 8 }}>Live oversight, analytics, and process flow</h2>
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(180px,1fr))", gap: 12, marginBottom: 24 }}>
              {["Audit readiness", "Observability", "Fallback mode"].map(label => (
                <div key={label} style={{ background: "white", borderRadius: 8, padding: 20, border: `1px solid ${EARTH}55` }}>
                  <div style={{ fontWeight: 700, color: BARK, marginBottom: 8, fontFamily: "Georgia, serif" }}>{label}</div>
                  <p style={{ fontSize: 12, color: EARTH, lineHeight: 1.6 }}>
                    {label === "Audit readiness" && "Every task can be traced back to a supervisor review and compliance checklist."}
                    {label === "Observability" && "Usage trends, service demand, and escalation volume are visible in the dashboard."}
                    {label === "Fallback mode" && "When automation is unstable, the Supervisor switches to manual support and exec review routes."}
                  </p>
                </div>
              ))}
            </div>
            <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
              <Link to="/admin/system"     style={{ background: GROVE, color: "white", padding: "10px 20px", borderRadius: 4, fontWeight: 700, fontSize: 13, textDecoration: "none" }}>Executive Dashboard</Link>
              <Link to="/admin/audit"      style={{ border: `1px solid ${EARTH}88`, color: COPPER, padding: "10px 20px", borderRadius: 4, fontWeight: 700, fontSize: 13, textDecoration: "none" }}>Audit Log</Link>
              <Link to="/admin/health"     style={{ border: `1px solid ${EARTH}88`, color: COPPER, padding: "10px 20px", borderRadius: 4, fontWeight: 700, fontSize: 13, textDecoration: "none" }}>System Health</Link>
              <Link to="/admin/moderation" style={{ border: `1px solid ${EARTH}88`, color: COPPER, padding: "10px 20px", borderRadius: 4, fontWeight: 700, fontSize: 13, textDecoration: "none" }}>Moderation</Link>
            </div>
          </section>
        )}

      </main>

      {/* ── Footer ── */}
      <footer style={{ background: GROVE, color: "#c8b896", padding: "28px 24px" }}>
        <div style={{ maxWidth: 1200, margin: "0 auto", display: "flex", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between", gap: 16, fontSize: 12 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <Heart style={{ width: 13, height: 13 }} />
            <span>MORE Help Center — Goodwill Wing of WAI Institute</span>
          </div>
          <div style={{ display: "flex", gap: 20, flexWrap: "wrap" }}>
            <Link to="/privacy"   style={{ color: "#c8b896", textDecoration: "none" }}>Privacy</Link>
            <Link to="/terms"     style={{ color: "#c8b896", textDecoration: "none" }}>Terms</Link>
            <Link to="/modules"   style={{ color: "#c8b896", textDecoration: "none" }}>Modules</Link>
            <Link to="/community" style={{ color: "#c8b896", textDecoration: "none" }}>Community</Link>
            <Link to="/register"  style={{ color: AMBER, fontWeight: 700, textDecoration: "none" }}>Join WAI →</Link>
            <a href={`mailto:${SUPPORT_EMAIL}`} style={{ color: "#c8b896", textDecoration: "none" }}>Contact</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
