import { useEffect, useState, useRef, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import { Shield, Lock, Unlock, AlertTriangle, FileText, Brain, Plus, Trash2, Eye, ChevronDown, ChevronUp, Send, Zap, RotateCcw, CheckCircle } from "lucide-react";

// ── Palette ──────────────────────────────────────────────────────────────────
const BG      = "#0a0a0f";
const CARD    = "#111118";
const BORDER  = "#1e1e2e";
const WHITE   = "#e8e6f0";
const MUTED   = "#6b6880";
const RED     = "#e05c5c";
const AMBER   = "#d4a017";
const GREEN   = "#4caf82";
const COPPER  = "#c07a3a";

const s = {
  page:   { background: BG, minHeight: "100vh", color: WHITE, fontFamily: "monospace", padding: "0" },
  header: { background: CARD, borderBottom: `1px solid ${BORDER}`, padding: "18px 32px", display: "flex", alignItems: "center", gap: 12 },
  title:  { fontSize: 16, fontWeight: 700, color: WHITE, letterSpacing: 2, textTransform: "uppercase" },
  sub:    { fontSize: 11, color: MUTED, letterSpacing: 1 },
  body:   { padding: "28px 32px", maxWidth: 1100 },
  tabs:   { display: "flex", gap: 4, marginBottom: 24, borderBottom: `1px solid ${BORDER}`, paddingBottom: 0 },
  tab:    (active) => ({ padding: "8px 18px", fontSize: 11, fontWeight: 700, letterSpacing: 1, textTransform: "uppercase", cursor: "pointer", border: "none", background: "transparent", color: active ? WHITE : MUTED, borderBottom: active ? `2px solid ${COPPER}` : "2px solid transparent", transition: "all .15s" }),
  card:   { background: CARD, border: `1px solid ${BORDER}`, borderRadius: 8, padding: "18px 22px", marginBottom: 14 },
  label:  { fontSize: 10, fontWeight: 700, color: MUTED, letterSpacing: 2, textTransform: "uppercase", marginBottom: 6 },
  val:    { fontSize: 13, color: WHITE },
  input:  { background: "#0d0d14", border: `1px solid ${BORDER}`, borderRadius: 6, color: WHITE, fontSize: 12, padding: "9px 12px", width: "100%", boxSizing: "border-box", fontFamily: "monospace", outline: "none" },
  textarea: { background: "#0d0d14", border: `1px solid ${BORDER}`, borderRadius: 6, color: WHITE, fontSize: 12, padding: "9px 12px", width: "100%", boxSizing: "border-box", fontFamily: "monospace", outline: "none", minHeight: 120, resize: "vertical" },
  btn:    (color) => ({ padding: "8px 16px", fontSize: 11, fontWeight: 700, letterSpacing: 1, textTransform: "uppercase", border: `1px solid ${color}`, borderRadius: 5, background: "transparent", color: color, cursor: "pointer" }),
  row:    { display: "flex", gap: 10, alignItems: "flex-start", flexWrap: "wrap" },
  badge:  (color) => ({ fontSize: 9, fontWeight: 700, letterSpacing: 1, textTransform: "uppercase", background: color + "22", color: color, border: `1px solid ${color}44`, borderRadius: 4, padding: "2px 7px" }),
};

// ── Threat Monitor ───────────────────────────────────────────────────────────
function ThreatMonitor() {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const r = await api.get("/sentinel/status");
      setStatus(r.data);
    } catch {}
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  const level = status?.threat_level;
  const levelColor = level === "nominal" ? GREEN : level === "elevated" ? AMBER : RED;

  return (
    <div>
      {loading && <div style={{ color: MUTED, fontSize: 12 }}>Scanning…</div>}
      {status && (
        <>
          <div style={{ ...s.card, borderColor: levelColor + "44" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 14 }}>
              <Shield size={16} color={levelColor} />
              <span style={{ fontSize: 13, fontWeight: 700, color: levelColor, letterSpacing: 2, textTransform: "uppercase" }}>
                Threat Level: {level}
              </span>
              <span style={{ color: MUTED, fontSize: 10, marginLeft: "auto" }}>
                {status.checked_at ? new Date(status.checked_at).toLocaleString() : ""}
              </span>
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill,minmax(180px,1fr))", gap: 12 }}>
              {[
                ["Logins (24h)",        status.login_spike_24h,        status.login_spike_24h > 50 ? RED : GREEN],
                ["Role Escalations (7d)", status.role_escalations_7d, status.role_escalations_7d > 0 ? AMBER : GREEN],
                ["Integrity Failures (7d)", status.integrity_failures_7d, status.integrity_failures_7d > 0 ? RED : GREEN],
                ["Open Incidents",      status.open_incidents,         status.open_incidents > 0 ? AMBER : GREEN],
              ].map(([label, val, color]) => (
                <div key={label} style={{ background: "#0d0d14", border: `1px solid ${BORDER}`, borderRadius: 6, padding: "12px 14px" }}>
                  <div style={s.label}>{label}</div>
                  <div style={{ fontSize: 22, fontWeight: 700, color }}>{val}</div>
                </div>
              ))}
            </div>
          </div>

          {status.anomalies_7d?.length > 0 && (
            <div style={s.card}>
              <div style={s.label}>Critical Audit Events (7d)</div>
              {status.anomalies_7d.map((a, i) => (
                <div key={i} style={{ padding: "7px 0", borderBottom: `1px solid ${BORDER}`, fontSize: 11, color: MUTED }}>
                  <span style={{ color: RED, marginRight: 8 }}>[{a.severity || "CRITICAL"}]</span>
                  <span style={{ color: WHITE }}>{a.action}</span>
                  <span style={{ marginLeft: 8 }}>{a.detail || ""}</span>
                  <span style={{ float: "right", color: MUTED }}>{a.at ? new Date(a.at).toLocaleString() : ""}</span>
                </div>
              ))}
            </div>
          )}
        </>
      )}
      <button onClick={load} style={{ ...s.btn(COPPER), marginTop: 8 }}>Refresh Scan</button>
    </div>
  );
}

// ── Protocol Vault ───────────────────────────────────────────────────────────
function ProtocolVault() {
  const [protocols, setProtocols] = useState([]);
  const [unlocked, setUnlocked] = useState({});
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState({ title: "", category: "incident_response", content: "", passphrase: "" });
  const [unlockForm, setUnlockForm] = useState({});

  const CATEGORIES = ["incident_response", "legal_defense", "technical_defense", "governance", "reputation", "general"];

  const load = useCallback(async () => {
    try { const r = await api.get("/sentinel/protocols"); setProtocols(r.data.protocols || []); } catch {}
  }, []);

  useEffect(() => { load(); }, [load]);

  async function handleCreate(e) {
    e.preventDefault();
    if (!form.title || !form.content || !form.passphrase) return;
    try {
      await api.post("/sentinel/protocols", form);
      setForm({ title: "", category: "incident_response", content: "", passphrase: "" });
      setCreating(false);
      load();
    } catch {}
  }

  async function handleUnlock(id) {
    const pw = unlockForm[id] || "";
    if (!pw) return;
    try {
      const r = await api.post("/sentinel/protocols/unlock", { protocol_id: id, passphrase: pw });
      setUnlocked(u => ({ ...u, [id]: r.data }));
      setUnlockForm(f => ({ ...f, [id]: "" }));
    } catch { alert("Invalid passphrase."); }
  }

  async function handleDelete(id) {
    if (!window.confirm("Permanently delete this protocol?")) return;
    try { await api.delete(`/sentinel/protocols/${id}`); load(); } catch {}
  }

  const catColor = { incident_response: RED, legal_defense: AMBER, technical_defense: COPPER, governance: GREEN, reputation: "#a78bfa", general: MUTED };

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <div style={{ color: MUTED, fontSize: 11 }}>Each protocol is locked with its own passphrase. Content is never sent without it.</div>
        <button onClick={() => setCreating(c => !c)} style={s.btn(COPPER)}>
          <Plus size={11} style={{ marginRight: 4 }} />{creating ? "Cancel" : "New Protocol"}
        </button>
      </div>

      {creating && (
        <form onSubmit={handleCreate} style={{ ...s.card, borderColor: COPPER + "44" }}>
          <div style={s.label}>New Protocol</div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, marginBottom: 10 }}>
            <input style={s.input} placeholder="Title" value={form.title} onChange={e => setForm(f => ({ ...f, title: e.target.value }))} />
            <select style={s.input} value={form.category} onChange={e => setForm(f => ({ ...f, category: e.target.value }))}>
              {CATEGORIES.map(c => <option key={c} value={c}>{c.replace(/_/g, " ")}</option>)}
            </select>
          </div>
          <textarea style={{ ...s.textarea, marginBottom: 10 }} placeholder="Protocol content…" value={form.content} onChange={e => setForm(f => ({ ...f, content: e.target.value }))} />
          <input style={{ ...s.input, marginBottom: 10 }} type="password" placeholder="Set unlock passphrase (required)" value={form.passphrase} onChange={e => setForm(f => ({ ...f, passphrase: e.target.value }))} />
          <button type="submit" style={s.btn(GREEN)}>Save Protocol</button>
        </form>
      )}

      {protocols.length === 0 && !creating && (
        <div style={{ color: MUTED, fontSize: 12, padding: "20px 0" }}>No protocols yet. Create the first one.</div>
      )}

      {protocols.map(p => (
        <div key={p.id} style={s.card}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 10 }}>
            <Lock size={12} color={MUTED} />
            <span style={{ fontSize: 13, fontWeight: 700, color: WHITE, flex: 1 }}>{p.title}</span>
            <span style={s.badge(catColor[p.category] || MUTED)}>{p.category?.replace(/_/g, " ")}</span>
            <span style={{ color: MUTED, fontSize: 10 }}>{p.created_at ? new Date(p.created_at).toLocaleDateString() : ""}</span>
            <button onClick={() => handleDelete(p.id)} style={{ background: "none", border: "none", cursor: "pointer", color: MUTED, padding: 2 }}>
              <Trash2 size={11} />
            </button>
          </div>

          {unlocked[p.id] ? (
            <div>
              <div style={{ background: "#0d0d14", border: `1px solid ${BORDER}`, borderRadius: 5, padding: "12px 14px", fontSize: 12, color: WHITE, whiteSpace: "pre-wrap", lineHeight: 1.7 }}>
                {unlocked[p.id].content}
              </div>
              <button onClick={() => setUnlocked(u => { const n = { ...u }; delete n[p.id]; return n; })} style={{ ...s.btn(MUTED), marginTop: 8, fontSize: 10 }}>
                <Lock size={10} style={{ marginRight: 4 }} />Lock
              </button>
            </div>
          ) : (
            <div style={{ display: "flex", gap: 8 }}>
              <input
                style={{ ...s.input, flex: 1 }}
                type="password"
                placeholder="Enter passphrase to unlock…"
                value={unlockForm[p.id] || ""}
                onChange={e => setUnlockForm(f => ({ ...f, [p.id]: e.target.value }))}
                onKeyDown={e => e.key === "Enter" && handleUnlock(p.id)}
              />
              <button onClick={() => handleUnlock(p.id)} style={s.btn(COPPER)}>
                <Unlock size={11} style={{ marginRight: 4 }} />Unlock
              </button>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

// ── Research Notes ───────────────────────────────────────────────────────────
function ResearchNotes() {
  const [notes, setNotes] = useState([]);
  const [expanded, setExpanded] = useState({});
  const [form, setForm] = useState({ title: "", content: "", tags: "" });
  const [creating, setCreating] = useState(false);

  const load = useCallback(async () => {
    try { const r = await api.get("/sentinel/research"); setNotes(r.data.notes || []); } catch {}
  }, []);

  useEffect(() => { load(); }, [load]);

  async function handleCreate(e) {
    e.preventDefault();
    if (!form.title || !form.content) return;
    const tags = form.tags.split(",").map(t => t.trim()).filter(Boolean);
    try {
      await api.post("/sentinel/research", { title: form.title, content: form.content, tags });
      setForm({ title: "", content: "", tags: "" });
      setCreating(false);
      load();
    } catch {}
  }

  async function handleDelete(id) {
    if (!window.confirm("Delete this research note?")) return;
    try { await api.delete(`/sentinel/research/${id}`); load(); } catch {}
  }

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <div style={{ color: MUTED, fontSize: 11 }}>Private notes — AI governance, legal defense, threat intelligence, organizational resilience.</div>
        <button onClick={() => setCreating(c => !c)} style={s.btn(COPPER)}>
          <Plus size={11} style={{ marginRight: 4 }} />{creating ? "Cancel" : "New Note"}
        </button>
      </div>

      {creating && (
        <form onSubmit={handleCreate} style={{ ...s.card, borderColor: COPPER + "44" }}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, marginBottom: 10 }}>
            <input style={s.input} placeholder="Title" value={form.title} onChange={e => setForm(f => ({ ...f, title: e.target.value }))} />
            <input style={s.input} placeholder="Tags (comma-separated)" value={form.tags} onChange={e => setForm(f => ({ ...f, tags: e.target.value }))} />
          </div>
          <textarea style={{ ...s.textarea, marginBottom: 10 }} placeholder="Research content…" value={form.content} onChange={e => setForm(f => ({ ...f, content: e.target.value }))} />
          <button type="submit" style={s.btn(GREEN)}>Save Note</button>
        </form>
      )}

      {notes.length === 0 && !creating && (
        <div style={{ color: MUTED, fontSize: 12, padding: "20px 0" }}>No notes yet.</div>
      )}

      {notes.map(n => (
        <div key={n.id} style={s.card}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, cursor: "pointer" }} onClick={() => setExpanded(e => ({ ...e, [n.id]: !e[n.id] }))}>
            <FileText size={12} color={COPPER} />
            <span style={{ fontSize: 13, fontWeight: 700, color: WHITE, flex: 1 }}>{n.title}</span>
            {(n.tags || []).map(t => <span key={t} style={s.badge(MUTED)}>{t}</span>)}
            <span style={{ color: MUTED, fontSize: 10 }}>{n.created_at ? new Date(n.created_at).toLocaleDateString() : ""}</span>
            <button onClick={e => { e.stopPropagation(); handleDelete(n.id); }} style={{ background: "none", border: "none", cursor: "pointer", color: MUTED, padding: 2 }}>
              <Trash2 size={11} />
            </button>
            {expanded[n.id] ? <ChevronUp size={12} color={MUTED} /> : <ChevronDown size={12} color={MUTED} />}
          </div>
          {expanded[n.id] && (
            <div style={{ marginTop: 12, background: "#0d0d14", border: `1px solid ${BORDER}`, borderRadius: 5, padding: "12px 14px", fontSize: 12, color: WHITE, whiteSpace: "pre-wrap", lineHeight: 1.7 }}>
              {n.content}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

// ── AI Brief ────────────────────────────────────────────────────────────────
function AIBrief() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const endRef = useRef(null);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);

  async function send() {
    const q = input.trim();
    if (!q || loading) return;
    setInput("");
    setMessages(m => [...m, { role: "user", text: q }]);
    setLoading(true);
    try {
      const r = await api.post("/sentinel/ai-brief", { question: q });
      setMessages(m => [...m, { role: "sentinel", text: r.data.response }]);
    } catch (e) {
      setMessages(m => [...m, { role: "sentinel", text: "Unavailable. " + (e?.response?.data?.detail || e.message) }]);
    }
    setLoading(false);
  }

  return (
    <div>
      <div style={{ color: MUTED, fontSize: 11, marginBottom: 16 }}>
        Private intelligence briefing. Not stored in shared chat history. Focused on defensive research only.
      </div>
      <div style={{ background: "#0d0d14", border: `1px solid ${BORDER}`, borderRadius: 8, minHeight: 320, maxHeight: 480, overflowY: "auto", padding: "14px 16px", marginBottom: 12 }}>
        {messages.length === 0 && (
          <div style={{ color: MUTED, fontSize: 12, textAlign: "center", paddingTop: 40 }}>
            Ask about AI governance, threat frameworks, legal defense, platform security…
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} style={{ marginBottom: 14 }}>
            <div style={{ fontSize: 9, fontWeight: 700, letterSpacing: 2, color: m.role === "user" ? COPPER : GREEN, marginBottom: 4, textTransform: "uppercase" }}>
              {m.role === "user" ? "D. Oliver" : "Sentinel"}
            </div>
            <div style={{ fontSize: 12, color: WHITE, lineHeight: 1.7, whiteSpace: "pre-wrap" }}>{m.text}</div>
          </div>
        ))}
        {loading && <div style={{ color: MUTED, fontSize: 12 }}>Analyzing…</div>}
        <div ref={endRef} />
      </div>
      <div style={{ display: "flex", gap: 8 }}>
        <input
          style={{ ...s.input, flex: 1 }}
          placeholder="Ask the Sentinel…"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === "Enter" && !e.shiftKey && send()}
        />
        <button onClick={send} disabled={loading} style={s.btn(COPPER)}>
          <Send size={12} />
        </button>
      </div>
    </div>
  );
}

// ── Autonomous Response + Reversals ─────────────────────────────────────────
function ResponsePanel() {
  const [running, setRunning] = useState(false);
  const [lastResult, setLastResult] = useState(null);
  const [reversals, setReversals] = useState([]);
  const [reversing, setReversing] = useState({});

  const loadReversals = useCallback(async () => {
    try { const r = await api.get("/sentinel/reversals"); setReversals(r.data.reversals || []); } catch {}
  }, []);

  useEffect(() => { loadReversals(); }, [loadReversals]);

  async function runResponse() {
    setRunning(true);
    setLastResult(null);
    try {
      const r = await api.post("/sentinel/respond");
      setLastResult(r.data);
      loadReversals();
    } catch (e) {
      setLastResult({ error: e?.response?.data?.detail || e.message });
    }
    setRunning(false);
  }

  async function reverse(id) {
    if (!window.confirm("Reverse this action? This will undo the protective measure.")) return;
    setReversing(r => ({ ...r, [id]: true }));
    try {
      await api.post(`/sentinel/reverse/${id}`);
      loadReversals();
    } catch (e) {
      alert(e?.response?.data?.detail || "Reversal failed.");
    }
    setReversing(r => ({ ...r, [id]: false }));
  }

  const typeColor = {
    lock_protocols: AMBER,
    vault_lockout: RED,
    revert_role: COPPER,
    suspend_account: RED,
  };

  const activeCount = reversals.filter(r => r.status === "active").length;

  return (
    <div>
      {/* Run engine */}
      <div style={{ ...s.card, borderColor: activeCount > 0 ? RED + "55" : BORDER }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 14 }}>
          <Zap size={14} color={activeCount > 0 ? RED : GREEN} />
          <div>
            <div style={{ fontSize: 13, fontWeight: 700, color: WHITE }}>Autonomous Response Engine</div>
            <div style={{ fontSize: 11, color: MUTED, marginTop: 2 }}>
              Scans for active threats and takes the minimum reversible protective action. Sends email report after each run.
            </div>
          </div>
          <div style={{ marginLeft: "auto" }}>
            {activeCount > 0 && <span style={s.badge(RED)}>{activeCount} active action{activeCount !== 1 ? "s" : ""}</span>}
          </div>
        </div>

        <button onClick={runResponse} disabled={running} style={{ ...s.btn(running ? MUTED : COPPER), display: "flex", alignItems: "center", gap: 6 }}>
          <Zap size={11} />{running ? "Scanning…" : "Run Threat Response"}
        </button>

        {lastResult && (
          <div style={{ marginTop: 14, background: "#0d0d14", borderRadius: 6, padding: "12px 14px" }}>
            {lastResult.error ? (
              <div style={{ color: RED, fontSize: 12 }}>Error: {lastResult.error}</div>
            ) : lastResult.actions_taken === 0 ? (
              <div style={{ color: GREEN, fontSize: 12, display: "flex", alignItems: "center", gap: 6 }}>
                <CheckCircle size={12} /> No active threats detected. No actions taken.
              </div>
            ) : (
              <>
                <div style={{ color: AMBER, fontSize: 12, fontWeight: 700, marginBottom: 10 }}>
                  {lastResult.actions_taken} action(s) taken — report sent to your email.
                </div>
                {(lastResult.actions || []).map((a, i) => (
                  <div key={i} style={{ padding: "6px 0", borderBottom: `1px solid ${BORDER}`, fontSize: 11 }}>
                    <span style={s.badge(typeColor[a.type] || MUTED)}>{a.type?.replace(/_/g," ")}</span>
                    <span style={{ color: MUTED, marginLeft: 8 }}>{a.reason}</span>
                  </div>
                ))}
              </>
            )}
          </div>
        )}
      </div>

      {/* Reversals list */}
      <div style={{ ...s.label, marginTop: 8 }}>Action History &amp; Human Override</div>
      {reversals.length === 0 && (
        <div style={{ color: MUTED, fontSize: 12, padding: "14px 0" }}>No autonomous actions recorded.</div>
      )}
      {reversals.map(r => (
        <div key={r.id} style={{ ...s.card, borderColor: r.status === "active" ? (typeColor[r.action_type] || BORDER) + "55" : BORDER, opacity: r.status === "reversed" ? 0.6 : 1 }}>
          <div style={{ display: "flex", alignItems: "flex-start", gap: 10 }}>
            <div style={{ flex: 1 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
                <span style={s.badge(typeColor[r.action_type] || MUTED)}>{r.action_type?.replace(/_/g," ")}</span>
                <span style={s.badge(r.status === "active" ? RED : GREEN)}>{r.status}</span>
                <span style={{ color: MUTED, fontSize: 10, marginLeft: "auto" }}>
                  {r.created_at ? new Date(r.created_at).toLocaleString() : ""}
                </span>
              </div>
              <div style={{ fontSize: 12, color: WHITE, lineHeight: 1.6 }}>{r.description}</div>
              {r.status === "reversed" && r.result_note && (
                <div style={{ fontSize: 11, color: GREEN, marginTop: 6 }}>
                  <CheckCircle size={10} style={{ marginRight: 4 }} />{r.result_note}
                </div>
              )}
            </div>
            {r.status === "active" && (
              <button
                onClick={() => reverse(r.id)}
                disabled={reversing[r.id]}
                style={{ ...s.btn(AMBER), whiteSpace: "nowrap", display: "flex", alignItems: "center", gap: 5, flexShrink: 0 }}
              >
                <RotateCcw size={11} />{reversing[r.id] ? "…" : "Reverse"}
              </button>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

// ── Main Page ────────────────────────────────────────────────────────────────
const TABS = [
  { id: "monitor",   label: "Threat Monitor",  icon: AlertTriangle },
  { id: "response",  label: "Response",        icon: Zap },
  { id: "protocols", label: "Protocol Vault",  icon: Lock },
  { id: "research",  label: "Research Notes",  icon: FileText },
  { id: "brief",     label: "AI Brief",        icon: Brain },
];

export default function SentinelResearch() {
  const { user, loading } = useAuth();
  const navigate = useNavigate();
  const [tab, setTab] = useState("monitor");

  useEffect(() => {
    if (!loading && user?.role !== "executive_admin") navigate("/", { replace: true });
  }, [user, loading, navigate]);

  if (loading || user?.role !== "executive_admin") return null;

  return (
    <div style={s.page}>
      <div style={s.header}>
        <Shield size={18} color={COPPER} />
        <div>
          <div style={s.title}>Sentinel Research</div>
          <div style={s.sub}>Defensive Intelligence · WAI-Institute / M.O.R.E. — Executive Access Only</div>
        </div>
        <div style={{ marginLeft: "auto", display: "flex", gap: 8, alignItems: "center" }}>
          <Eye size={12} color={MUTED} />
          <span style={{ fontSize: 10, color: MUTED, letterSpacing: 1 }}>All access audit-logged</span>
        </div>
      </div>

      <div style={s.body}>
        <div style={s.tabs}>
          {TABS.map(t => {
            const Icon = t.icon;
            return (
              <button key={t.id} onClick={() => setTab(t.id)} style={s.tab(tab === t.id)}>
                <Icon size={10} style={{ marginRight: 5, display: "inline" }} />{t.label}
              </button>
            );
          })}
        </div>

        {tab === "monitor"   && <ThreatMonitor />}
        {tab === "response"  && <ResponsePanel />}
        {tab === "protocols" && <ProtocolVault />}
        {tab === "research"  && <ResearchNotes />}
        {tab === "brief"     && <AIBrief />}
      </div>
    </div>
  );
}
