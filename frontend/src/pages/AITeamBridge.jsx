import { useState, useEffect, useCallback } from "react";
import { api } from "../lib/api";
import AppShell from "../components/AppShell";
import {
  Network, Save, Users, Send, ScrollText, Pencil, Check, X, Shield, Link2, Globe, Settings2,
} from "lucide-react";

// ── Design tokens ─────────────────────────────────────────────────────────────
const COPPER = "#b5651d";
const INK = "#1a1a1a";
const BONE = "#f5f0e8";

const KIND_OPTIONS = [
  { value: "task", label: "Task" },
  { value: "project", label: "Project" },
  { value: "update", label: "Update" },
  { value: "ack", label: "Acknowledgment" },
];

// ── Small UI helpers ─────────────────────────────────────────────────────────
function Field({ label, children }) {
  return (
    <label style={{ display: "block", marginBottom: 14 }}>
      <span style={{ fontSize: 11, fontWeight: 800, textTransform: "uppercase", letterSpacing: "0.08em", color: COPPER, display: "block", marginBottom: 6 }}>
        {label}
      </span>
      {children}
    </label>
  );
}

const inputStyle = {
  width: "100%",
  border: `1.5px solid #ddd`,
  borderRadius: 8,
  padding: "10px 12px",
  fontSize: 14,
  color: INK,
  background: "#fff",
  outline: "none",
  boxSizing: "border-box",
};

const btnPrimary = {
  background: COPPER,
  color: "#fff",
  border: "none",
  borderRadius: 8,
  padding: "10px 20px",
  fontWeight: 800,
  fontSize: 13,
  cursor: "pointer",
  textTransform: "uppercase",
  letterSpacing: "0.06em",
  display: "inline-flex",
  alignItems: "center",
  gap: 8,
};

const btnGhost = {
  background: "transparent",
  color: COPPER,
  border: `1.5px solid ${COPPER}`,
  borderRadius: 8,
  padding: "10px 20px",
  fontWeight: 800,
  fontSize: 13,
  cursor: "pointer",
  textTransform: "uppercase",
  letterSpacing: "0.06em",
  display: "inline-flex",
  alignItems: "center",
  gap: 8,
};

function Card({ title, icon: Icon, children }) {
  return (
    <div style={{ background: "#fff", border: `2px solid ${BONE}`, borderRadius: 12, padding: 20, marginBottom: 20, boxShadow: "0 2px 8px rgba(26,26,26,0.05)" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 16 }}>
        {Icon && <Icon size={18} color={COPPER} />}
        <h3 style={{ margin: 0, fontSize: 16, fontWeight: 800, color: INK }}>{title}</h3>
      </div>
      {children}
    </div>
  );
}

// ── Main page ────────────────────────────────────────────────────────────────
export default function AITeamBridge() {
  const [tab, setTab] = useState("config");
  const [config, setConfig] = useState(null);
  const [personas, setPersonas] = useState([]);
  const [log, setLog] = useState({ outbound: [], inbound: [] });
  const [saving, setSaving] = useState(false);
  const [toast, setToast] = useState(null);

  const flash = (msg) => {
    setToast(msg);
    setTimeout(() => setToast(null), 3500);
  };

  const loadConfig = useCallback(async () => {
    try {
      const r = await api.get("/bridge/config");
      setConfig(r.data.config || {});
    } catch (e) {
      flash("Could not load bridge config: " + (e?.response?.data?.detail || e?.message || "network error"));
    }
  }, []);

  const loadPersonas = useCallback(async () => {
    try {
      const r = await api.get("/bridge/personas");
      setPersonas(r.data.personas || []);
    } catch (e) {
      flash("Could not load bridge personas.");
    }
  }, []);

  const loadLog = useCallback(async () => {
    try {
      const r = await api.get("/bridge/log?limit=30");
      setLog({ outbound: r.data.outbound || [], inbound: r.data.inbound || [] });
    } catch (e) {
      /* non-fatal */
    }
  }, []);

  useEffect(() => {
    loadConfig();
    loadPersonas();
  }, [loadConfig, loadPersonas]);

  const switchTab = (t) => {
    setTab(t);
    if (t === "log") loadLog();
    if (t === "personas") loadPersonas();
    if (t === "config") loadConfig();
  };

  const saveConfig = async () => {
    if (!config) return;
    setSaving(true);
    try {
      const r = await api.put("/bridge/config", {
        enabled: config.enabled,
        partner_team_name: config.partner_team_name,
        partner_domain: config.partner_domain,
        goals: config.goals,
        protocol: config.protocol,
        webhook_url: config.webhook_url,
        dispatch_mode: config.dispatch_mode,
        shared_secret: config.shared_secret,
      });
      setConfig(r.data.config);
      flash("Bridge configuration saved.");
    } catch (e) {
      flash("Save failed: " + (e?.response?.data?.detail || e?.message || "network error"));
    } finally {
      setSaving(false);
    }
  };

  const savePersona = async (personaKey, updates) => {
    try {
      const r = await api.put(`/bridge/personas/${personaKey}`, updates);
      setPersonas((prev) => prev.map((p) => (p.key === personaKey ? r.data.persona : p)));
      flash("Persona updated.");
    } catch (e) {
      flash("Persona update failed: " + (e?.response?.data?.detail || e?.message || "network error"));
    }
  };

  return (
    <AppShell>
      <div style={{ maxWidth: 960, margin: "0 auto", padding: "28px 20px" }}>
        {/* Header */}
        <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 16, flexWrap: "wrap", marginBottom: 8 }}>
          <div>
            <h1 style={{ margin: 0, fontSize: 28, fontWeight: 900, color: INK, letterSpacing: "-0.02em", display: "flex", alignItems: "center", gap: 12 }}>
              <Network color={COPPER} size={28} /> AI Team Bridge
            </h1>
            <p style={{ margin: "6px 0 0", color: "#666", fontSize: 14, maxWidth: 620 }}>
              Direct communication & coordination between the M.O.R.E. AI Director (with NAM Oshun Scholar)
              and the partner AI team at wai-institute.org — for tasks and projects.
            </p>
          </div>
          <div style={{
            background: config?.enabled ? "#e7f4ec" : "#fdeaea",
            color: config?.enabled ? "#1b7a3d" : "#b3261e",
            fontSize: 12, fontWeight: 800, textTransform: "uppercase", letterSpacing: "0.08em",
            padding: "6px 12px", borderRadius: 999,
          }}>
            {config?.enabled ? "● Bridge active" : "○ Bridge paused"}
          </div>
        </div>

        {toast && (
          <div style={{ background: INK, color: "#fff", fontSize: 13, padding: "10px 16px", borderRadius: 8, margin: "12px 0" }}>
            {toast}
          </div>
        )}

        {/* Tabs */}
        <div style={{ display: "flex", gap: 8, margin: "20px 0", flexWrap: "wrap" }}>
          {[
            { id: "config", label: "Configuration", icon: Settings2 },
            { id: "personas", label: "AI Team Roster", icon: Users },
            { id: "dispatch", label: "Dispatch", icon: Send },
            { id: "log", label: "Coordination Log", icon: ScrollText },
          ].map((t) => (
            <button key={t.id} onClick={() => switchTab(t.id)} style={{
              display: "inline-flex", alignItems: "center", gap: 8,
              background: tab === t.id ? COPPER : "#fff",
              color: tab === t.id ? "#fff" : INK,
              border: `1.5px solid ${tab === t.id ? COPPER : "#ddd"}`,
              borderRadius: 999, padding: "8px 16px", fontSize: 13, fontWeight: 700, cursor: "pointer",
            }}>
              <t.icon size={15} /> {t.label}
            </button>
          ))}
        </div>

        {/* ── CONFIG ─────────────────────────────────────────────────────── */}
        {tab === "config" && config && (
          <Card title="Bridge Configuration" icon={Settings2}>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0 20px" }}>
              <Field label="Partner team name">
                <input style={inputStyle} value={config.partner_team_name || ""}
                  onChange={(e) => setConfig({ ...config, partner_team_name: e.target.value })} />
              </Field>
              <Field label="Partner domain">
                <div style={{ position: "relative" }}>
                  <Globe size={15} color="#aaa" style={{ position: "absolute", left: 10, top: 12 }} />
                  <input style={{ ...inputStyle, paddingLeft: 32 }} value={config.partner_domain || ""}
                    onChange={(e) => setConfig({ ...config, partner_domain: e.target.value })} />
                </div>
              </Field>
            </div>

            <Field label="Shared goals">
              <textarea rows={3} style={inputStyle} value={config.goals || ""}
                onChange={(e) => setConfig({ ...config, goals: e.target.value })} />
            </Field>

            <Field label="Coordination protocol">
              <textarea rows={4} style={inputStyle} value={config.protocol || ""}
                onChange={(e) => setConfig({ ...config, protocol: e.target.value })} />
            </Field>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0 20px" }}>
              <Field label="Inbound webhook URL (optional — for receiving partner messages)">
                <div style={{ position: "relative" }}>
                  <Link2 size={15} color="#aaa" style={{ position: "absolute", left: 10, top: 12 }} />
                  <input style={{ ...inputStyle, paddingLeft: 32 }} placeholder="https://…/api/bridge/receive"
                    value={config.webhook_url || ""}
                    onChange={(e) => setConfig({ ...config, webhook_url: e.target.value })} />
                </div>
              </Field>
              <Field label="Outbound delivery mode">
                <select style={inputStyle} value={config.dispatch_mode || "manual"}
                  onChange={(e) => setConfig({ ...config, dispatch_mode: e.target.value })}>
                  <option value="manual">Manual (log + copy — free)</option>
                  <option value="webhook">Webhook (POST to partner endpoint)</option>
                </select>
              </Field>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0 20px" }}>
              <Field label="Shared secret (optional — protects the receive endpoint)">
                <input style={inputStyle} placeholder="Leave blank to keep as-is"
                  value={config.shared_secret || ""}
                  onChange={(e) => setConfig({ ...config, shared_secret: e.target.value })} />
              </Field>
              <Field label="Bridge enabled">
                <label style={{ display: "inline-flex", alignItems: "center", gap: 10, fontSize: 14, color: INK, cursor: "pointer", marginTop: 4 }}>
                  <input type="checkbox" checked={!!config.enabled}
                    onChange={(e) => setConfig({ ...config, enabled: e.target.checked })} />
                  Accept inbound messages & allow dispatches
                </label>
              </Field>
            </div>

            <div style={{ display: "flex", gap: 10, marginTop: 8 }}>
              <button style={btnPrimary} onClick={saveConfig} disabled={saving}>
                <Save size={15} /> {saving ? "Saving…" : "Save Configuration"}
              </button>
            </div>

            <div style={{ marginTop: 18, background: BONE, borderRadius: 8, padding: "12px 16px", fontSize: 12, color: "#555", lineHeight: 1.6 }}>
              <Shield size={14} color={COPPER} style={{ verticalAlign: "-2px", marginRight: 6 }} />
              <strong>Free by design:</strong> all AI coordination runs through the free-first LLM gateway.
              Dispatches are produced and logged locally; they only leave the platform if you set an outbound
              webhook URL and choose "webhook" mode. No paid provider is ever called directly.
            </div>
          </Card>
        )}

        {/* ── PERSONAS ───────────────────────────────────────────────────── */}
        {tab === "personas" && (
          <Card title="AI Team Roster — who speaks for the Institute" icon={Users}>
            <p style={{ margin: "0 0 16px", fontSize: 13, color: "#666" }}>
              The Director and <strong style={{ color: COPPER }}>NAM Oshun Scholar</strong> always participate in
              dispatches. Toggle others on/off and edit each participant's name, role, and goals.
            </p>
            {personas.map((p) => (
              <PersonaRow key={p.key} persona={p} onSave={savePersona} />
            ))}
          </Card>
        )}

        {/* ── DISPATCH ───────────────────────────────────────────────────── */}
        {tab === "dispatch" && (
          <DispatchTab config={config} personas={personas} flash={flash} />
        )}

        {/* ── LOG ────────────────────────────────────────────────────────── */}
        {tab === "log" && (
          <LogTab log={log} />
        )}
      </div>
    </AppShell>
  );
}

// ── Persona row (editable) ───────────────────────────────────────────────────
function PersonaRow({ persona, onSave }) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(null);
  const isScholar = persona.key === "nam_oshun_scholar";

  const begin = () => {
    setDraft({
      display_name: persona.display_name || "",
      role: persona.role || "",
      goals: persona.goals || "",
      participating: !!persona.participating,
    });
    setEditing(true);
  };

  const save = async () => {
    await onSave(persona.key, draft);
    setEditing(false);
  };

  return (
    <div style={{
      border: `1.5px solid ${isScholar ? COPPER : "#eee"}`,
      background: isScholar ? "#fdf6ee" : "#fff",
      borderRadius: 10, padding: "14px 16px", marginBottom: 12,
      display: "flex", gap: 14, alignItems: "flex-start",
    }}>
      <div style={{
        width: 40, height: 40, borderRadius: 10, flexShrink: 0,
        background: isScholar ? COPPER : INK, color: "#fff",
        display: "flex", alignItems: "center", justifyContent: "center",
        fontWeight: 900, fontSize: 16,
      }}>
        {isScholar ? "NS" : (persona.display_name || persona.key).slice(0, 2).toUpperCase()}
      </div>

      {!editing ? (
        <>
          <div style={{ flex: 1 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
              <span style={{ fontWeight: 800, color: INK, fontSize: 15 }}>{persona.display_name || persona.key}</span>
              {isScholar && (
                <span style={{ background: COPPER, color: "#fff", fontSize: 10, fontWeight: 800, textTransform: "uppercase", letterSpacing: "0.06em", padding: "2px 8px", borderRadius: 999 }}>
                  Scholar
                </span>
              )}
              <span style={{
                fontSize: 10, fontWeight: 800, textTransform: "uppercase", letterSpacing: "0.06em",
                padding: "2px 8px", borderRadius: 999,
                background: persona.participating ? "#e7f4ec" : "#f0f0f0",
                color: persona.participating ? "#1b7a3d" : "#888",
              }}>
                {persona.participating ? "Participating" : "Standby"}
              </span>
            </div>
            <div style={{ fontSize: 12, color: "#777", marginTop: 2 }}>{persona.role}</div>
            {persona.goals && <div style={{ fontSize: 13, color: "#555", marginTop: 6, lineHeight: 1.5 }}>{persona.goals}</div>}
          </div>
          <button style={{ ...btnGhost, padding: "6px 12px" }} onClick={begin}>
            <Pencil size={13} /> Edit
          </button>
        </>
      ) : (
        <>
          <div style={{ flex: 1 }}>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0 12px" }}>
              <Field label="Display name">
                <input style={inputStyle} value={draft.display_name}
                  onChange={(e) => setDraft({ ...draft, display_name: e.target.value })} />
              </Field>
              <Field label="Role">
                <input style={inputStyle} value={draft.role}
                  onChange={(e) => setDraft({ ...draft, role: e.target.value })} />
              </Field>
            </div>
            <Field label="Goals">
              <textarea rows={2} style={inputStyle} value={draft.goals}
                onChange={(e) => setDraft({ ...draft, goals: e.target.value })} />
            </Field>
            <label style={{ display: "inline-flex", alignItems: "center", gap: 8, fontSize: 13, color: INK, cursor: "pointer" }}>
              <input type="checkbox" checked={!!draft.participating}
                onChange={(e) => setDraft({ ...draft, participating: e.target.checked })} />
              Participates in dispatches
            </label>
          </div>
          <div style={{ display: "flex", gap: 8, flexDirection: "column" }}>
            <button style={{ ...btnPrimary, padding: "6px 12px" }} onClick={save}>
              <Check size={13} /> Save
            </button>
            <button style={{ ...btnGhost, padding: "6px 12px" }} onClick={() => setEditing(false)}>
              <X size={13} /> Cancel
            </button>
          </div>
        </>
      )}
    </div>
  );
}

// ── Dispatch tab ─────────────────────────────────────────────────────────────
function DispatchTab({ config, personas, flash }) {
  const [kind, setKind] = useState("task");
  const [title, setTitle] = useState("");
  const [task, setTask] = useState("");
  const [selected, setSelected] = useState([]);
  const [dispatching, setDispatching] = useState(false);
  const [result, setResult] = useState(null);

  const participatingKeys = (personas || []).filter((p) => p.participating).map((p) => p.key);

  const togglePersona = (key) => {
    setSelected((prev) => (prev.includes(key) ? prev.filter((k) => k !== key) : [...prev, key]));
  };

  const dispatch = async () => {
    if (!title.trim() || !task.trim()) {
      flash("Both a title and a task/project description are required.");
      return;
    }
    setDispatching(true);
    setResult(null);
    try {
      const r = await api.post("/bridge/dispatch", {
        kind,
        title: title.trim(),
        task: task.trim(),
        participants: selected.length ? selected : undefined,
      });
      setResult(r.data.dispatch);
      flash(r.data.message || "Dispatch created.");
    } catch (e) {
      flash("Dispatch failed: " + (e?.response?.data?.detail || e?.message || "network error"));
    } finally {
      setDispatching(false);
    }
  };

  return (
    <Card title="Dispatch a Task or Project to the Partner AI Team" icon={Send}>
      <p style={{ margin: "0 0 16px", fontSize: 13, color: "#666" }}>
        Addressed to <strong style={{ color: COPPER }}>{config?.partner_team_name || "the partner AI team"}</strong>.
        The Director and NAM Oshun Scholar contribute coordination notes, then the dispatch is{" "}
        {config?.dispatch_mode === "webhook" && config?.webhook_url ? "sent via webhook" : "produced and logged for manual hand-off"}.
      </p>

      <div style={{ display: "grid", gridTemplateColumns: "160px 1fr", gap: "0 12px" }}>
        <Field label="Kind">
          <select style={inputStyle} value={kind} onChange={(e) => setKind(e.target.value)}>
            {KIND_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>
        </Field>
        <Field label="Title">
          <input style={inputStyle} value={title} onChange={(e) => setTitle(e.target.value)}
            placeholder="e.g. Joint curriculum blueprint — Intro to Solar Installations" />
        </Field>
      </div>

      <Field label="Task / project brief">
        <textarea rows={5} style={inputStyle} value={task} onChange={(e) => setTask(e.target.value)}
          placeholder="Describe the task or project for the partner AI team: objective, scope, constraints, and what coordination you need back." />
      </Field>

      <Field label="Who contributes (defaults to all participating)">
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          {(personas || []).map((p) => (
            <button key={p.key} onClick={() => togglePersona(p.key)}
              style={{
                display: "inline-flex", alignItems: "center", gap: 6, cursor: "pointer",
                background: selected.includes(p.key) ? COPPER : "#fff",
                color: selected.includes(p.key) ? "#fff" : INK,
                border: `1.5px solid ${selected.includes(p.key) ? COPPER : "#ddd"}`,
                borderRadius: 999, padding: "6px 12px", fontSize: 12, fontWeight: 700,
              }}>
              {p.display_name || p.key}
              {(p.key === "director" || p.key === "nam_oshun_scholar") && " ★"}
            </button>
          ))}
        </div>
        {selected.length === 0 && (
          <div style={{ fontSize: 11, color: "#888", marginTop: 6 }}>
            None selected — will use all participating personas (includes Director ★ and NAM Oshun Scholar ★).
          </div>
        )}
      </Field>

      <div style={{ display: "flex", gap: 10, marginTop: 4 }}>
        <button style={btnPrimary} onClick={dispatch} disabled={dispatching}>
          <Send size={15} /> {dispatching ? "Coordinating…" : "Draft & Dispatch"}
        </button>
      </div>

      {result && (
        <div style={{ marginTop: 20, background: BONE, borderRadius: 10, padding: 18 }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: 8, marginBottom: 10 }}>
            <div style={{ fontWeight: 800, color: INK, fontSize: 14 }}>
              Dispatch {result.dispatch_id?.slice(0, 8)} — {result.status}
            </div>
            <div style={{ fontSize: 11, color: "#888" }}>
              Channel: {result.channel} · To: {result.recipient}
            </div>
          </div>
          <pre style={{
            whiteSpace: "pre-wrap", fontFamily: "Georgia, serif", fontSize: 13, lineHeight: 1.7,
            color: INK, background: "#fff", border: "1px solid #e5ddd0", borderRadius: 8, padding: 14,
            maxHeight: 360, overflowY: "auto",
          }}>
            {result.dispatch_body}
          </pre>
          <button style={{ ...btnGhost, marginTop: 12 }} onClick={() => {
            navigator.clipboard?.writeText(result.dispatch_body);
            flash("Dispatch copied to clipboard.");
          }}>
            <Link2 size={14} /> Copy dispatch
          </button>
        </div>
      )}
    </Card>
  );
}

// ── Log tab ──────────────────────────────────────────────────────────────────
function LogTab({ log }) {
  return (
    <>
      <Card title="Outbound Dispatches" icon={Send}>
        {log.outbound.length === 0 && <p style={{ color: "#999", fontSize: 13 }}>No dispatches yet.</p>}
        {log.outbound.map((d) => (
          <div key={d.dispatch_id} style={{ borderBottom: `1px solid ${BONE}`, padding: "12px 0" }}>
            <div style={{ display: "flex", justifyContent: "space-between", gap: 8, flexWrap: "wrap" }}>
              <div style={{ fontWeight: 700, color: INK, fontSize: 14 }}>{d.title}</div>
              <span style={{
                fontSize: 10, fontWeight: 800, textTransform: "uppercase", letterSpacing: "0.06em",
                padding: "2px 8px", borderRadius: 999,
                background: d.status === "sent" ? "#e7f4ec" : d.status === "failed" ? "#fdeaea" : "#f0f0f0",
                color: d.status === "sent" ? "#1b7a3d" : d.status === "failed" ? "#b3261e" : "#888",
              }}>
                {d.status}
              </span>
            </div>
            <div style={{ fontSize: 11, color: "#999", marginTop: 2 }}>
              {d.kind} · {d.channel} · {d.created_at} · by {d.created_by || "—"}
            </div>
            {d.task && <div style={{ fontSize: 13, color: "#555", marginTop: 6, lineHeight: 1.5 }}>{d.task.slice(0, 300)}</div>}
          </div>
        ))}
      </Card>

      <Card title="Inbound from Partner Team" icon={Network}>
        {log.inbound.length === 0 && <p style={{ color: "#999", fontSize: 13 }}>No inbound messages yet. Share your inbound webhook URL with the partner team to receive updates.</p>}
        {log.inbound.map((m) => (
          <div key={m.message_id} style={{ borderBottom: `1px solid ${BONE}`, padding: "12px 0" }}>
            <div style={{ fontWeight: 700, color: INK, fontSize: 14 }}>{m.subject}</div>
            <div style={{ fontSize: 11, color: "#999", marginTop: 2 }}>
              From {m.from_team} · {m.received_at}
            </div>
            {m.body && <div style={{ fontSize: 13, color: "#555", marginTop: 6, lineHeight: 1.5 }}>{m.body.slice(0, 400)}</div>}
          </div>
        ))}
      </Card>
    </>
  );
}
