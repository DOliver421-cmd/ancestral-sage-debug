import { useState, useEffect } from "react";
import { toast } from "sonner";
import { UserPlus, Trash2, Copy, Check, Users } from "lucide-react";
import { useAuth } from "../../../lib/auth";
import SharePanel from "../../SharePanel";

const ROLES = ["Lyricist", "Producer", "Visual Artist", "Editor", "Mix Engineer", "Voice / Spoken Word", "Other"];
const STATUSES = [
  { id: "invited", label: "Invited", color: "rgba(217,119,6,0.85)" },
  { id: "active",  label: "Active",  color: "rgba(14,116,144,0.9)" },
  { id: "done",    label: "Done",    color: "rgba(21,128,61,0.9)" },
];

const keyFor = (projectId, kind) => `studio_collab_${kind}:${projectId}`;

/**
 * Collaboration Chamber — real per-project guest management.
 * Track who's working on the project (name + role + status), define the scope
 * they own, and copy/share an invite message that names the project and role.
 * All local — no backend, no cost.
 */
export default function CollaborationChamber({ activeProject }) {
  const [roster, setRoster] = useState([]);
  const [name, setName] = useState("");
  const [role, setRole] = useState(ROLES[0]);
  const [scope, setScope] = useState("");
  const [copiedInvite, setCopiedInvite] = useState(false);
  const { user } = useAuth();

  useEffect(() => {
    if (!activeProject) return;
    try {
      setRoster(JSON.parse(localStorage.getItem(keyFor(activeProject.id, "roster")) || "[]"));
      setScope(localStorage.getItem(keyFor(activeProject.id, "scope")) || "");
    } catch { /* fresh state */ }
  }, [activeProject]);

  const persistRoster = (next) => {
    setRoster(next);
    if (activeProject) {
      try { localStorage.setItem(keyFor(activeProject.id, "roster"), JSON.stringify(next)); } catch {}
    }
  };

  const saveScope = () => {
    if (!activeProject) return;
    try { localStorage.setItem(keyFor(activeProject.id, "scope"), scope); } catch {}
    toast.success("Scope saved.");
  };

  const addGuest = () => {
    if (!activeProject) { toast.error("Open a project first (⊕ New Project) to build a team around it."); return; }
    if (!name.trim()) { toast.error("Enter the guest's name."); return; }
    const guest = { id: Date.now(), name: name.trim(), role, status: "invited" };
    persistRoster([...roster, guest]);
    setName("");
    toast.success(`${guest.name} added as ${role}.`);
  };

  const setStatus = (id, status) => {
    persistRoster(roster.map(g => g.id === id ? { ...g, status } : g));
  };

  const removeGuest = (id) => {
    persistRoster(roster.filter(g => g.id !== id));
  };

  const inviteText = () => {
    if (!activeProject) return "";
    const creator = user?.full_name || "M.O.R.E. creator";
    return [
      `${activeProject.name} — collaboration invite`,
      "",
      `I'm building "${activeProject.name}" in the M.O.R.E. Creator Suite and I want you on the team.`,
      `Role: ${role}`,
      `Scope: ${scope.trim() || "Let's define it together"}`,
      "",
      `Open the suite: ${window.location.origin}/studio?chamber=collaboration&project=${activeProject.id}`,
      `Let's make something real. — ${creator}`,
    ].join("\n");
  };

  const copyInvite = () => {
    const text = inviteText();
    if (!text) { toast.error("Open a project first."); return; }
    navigator.clipboard?.writeText(text).then(() => {
      setCopiedInvite(true);
      toast.success("Invite message copied.");
      setTimeout(() => setCopiedInvite(false), 2000);
    });
  };

  if (!activeProject) {
    return (
      <div style={{ textAlign: "center", padding: "60px 24px", border: "1px dashed rgba(109,40,217,0.25)", color: "rgba(28,25,23,0.35)" }}>
        <div style={{ fontSize: 40, marginBottom: 12, opacity: 0.4 }}>⊞</div>
        <div style={{ fontFamily: "Georgia, serif", fontSize: 16, marginBottom: 8 }}>No project selected</div>
        <div style={{ fontSize: 12, fontFamily: "monospace" }}>
          Create or open a project (⊕ New Project) to build a team around it.
        </div>
      </div>
    );
  }

  return (
    <div style={{ fontFamily: "inherit", color: "rgba(28,25,23,0.9)", display: "flex", flexDirection: "column", gap: 22 }}>
      {/* Active project header */}
      <div style={{ display: "flex", alignItems: "center", gap: 12, padding: "12px 14px", border: "1px solid rgba(109,40,217,0.25)", background: "rgba(109,40,217,0.05)" }}>
        <div style={{ fontSize: 26 }}>{activeProject.glyph || "⊞"}</div>
        <div>
          <div style={{ fontSize: 9, fontFamily: "monospace", letterSpacing: "0.18em", textTransform: "uppercase", color: "rgba(109,40,217,0.7)" }}>
            Collaborating on
          </div>
          <div style={{ fontSize: 15, fontWeight: 900, color: "#6d28d9" }}>{activeProject.name}</div>
        </div>
      </div>

      {/* Add guest */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
        <div>
          <label style={labelStyle}>Guest Name *</label>
          <input style={inputStyle} value={name} onChange={e => setName(e.target.value)} onKeyDown={e => e.key === "Enter" && addGuest()} placeholder="Who's joining?" maxLength={80} />
        </div>
        <div>
          <label style={labelStyle}>Role</label>
          <select style={inputStyle} value={role} onChange={e => setRole(e.target.value)}>
            {ROLES.map(r => <option key={r} value={r}>{r}</option>)}
          </select>
        </div>
      </div>
      <button
        onClick={addGuest}
        style={{ alignSelf: "flex-start", background: "rgba(109,40,217,0.15)", border: "1px solid rgba(109,40,217,0.4)", color: "#6d28d9", padding: "8px 18px", fontFamily: "monospace", fontSize: 11, fontWeight: 700, letterSpacing: "0.08em", cursor: "pointer", display: "flex", alignItems: "center", gap: 7 }}
      >
        <UserPlus style={{ width: 12, height: 12 }} /> Add Guest Creator
      </button>

      {/* Scope */}
      <div>
        <label style={labelStyle}>Scope — what does the team own?</label>
        <div style={{ display: "flex", gap: 8 }}>
          <textarea style={{ ...inputStyle, height: 56, resize: "none", flex: 1 }} value={scope} onChange={e => setScope(e.target.value)} placeholder="e.g. Maya writes the hook and the bridge; Dev handles the beat arrangement and mix." maxLength={400} />
          <button onClick={saveScope} style={{ background: "rgba(109,40,217,0.12)", border: "1px solid rgba(109,40,217,0.3)", color: "#6d28d9", padding: "0 14px", fontFamily: "monospace", fontSize: 10, fontWeight: 700, cursor: "pointer" }}>SAVE</button>
        </div>
      </div>

      {/* Roster */}
      <div>
        <div style={{ fontSize: 9, fontFamily: "monospace", letterSpacing: "0.2em", textTransform: "uppercase", color: "rgba(109,40,217,0.7)", marginBottom: 10, display: "flex", alignItems: "center", gap: 8 }}>
          <Users style={{ width: 12, height: 12 }} /> Guest Creators ({roster.length})
        </div>
        {roster.length === 0 ? (
          <div style={{ fontSize: 12, color: "rgba(28,25,23,0.3)", fontStyle: "italic", padding: "12px 0" }}>
            No guests yet. Add the people working on this project.
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {roster.map(g => {
              const st = STATUSES.find(s => s.id === g.status) || STATUSES[0];
              return (
                <div key={g.id} style={{ display: "flex", alignItems: "center", gap: 10, padding: "10px 12px", background: "rgba(28,25,23,0.04)", border: "1px solid rgba(28,25,23,0.07)" }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 13, fontWeight: 900 }}>{g.name}</div>
                    <div style={{ fontSize: 10, fontFamily: "monospace", color: "rgba(109,40,217,0.6)", marginTop: 2 }}>{g.role}</div>
                  </div>
                  <select
                    value={g.status}
                    onChange={e => setStatus(g.id, e.target.value)}
                    style={{ background: "rgba(28,25,23,0.04)", border: `1px solid ${st.color}`, color: st.color, padding: "4px 8px", fontSize: 10, fontFamily: "monospace", fontWeight: 700, outline: "none", borderRadius: 4, cursor: "pointer" }}
                  >
                    {STATUSES.map(s => <option key={s.id} value={s.id} style={{ color: "#1c1917" }}>{s.label}</option>)}
                  </select>
                  <button onClick={() => removeGuest(g.id)} title="Remove guest" style={{ background: "none", border: "none", color: "rgba(28,25,23,0.3)", cursor: "pointer", display: "flex", padding: 4 }}>
                    <Trash2 style={{ width: 13, height: 13 }} />
                  </button>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Invite + share */}
      <div style={{ borderTop: "1px solid rgba(28,25,23,0.07)", paddingTop: 16 }}>
        <div style={labelStyle}>Invite message — copy &amp; send</div>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <button
            onClick={copyInvite}
            style={{ background: copiedInvite ? "rgba(21,128,61,0.2)" : "rgba(109,40,217,0.12)", border: `1px solid ${copiedInvite ? "rgba(21,128,61,0.4)" : "rgba(109,40,217,0.35)"}`, color: copiedInvite ? "#15803d" : "#6d28d9", padding: "8px 16px", fontFamily: "monospace", fontSize: 11, fontWeight: 700, cursor: "pointer", display: "flex", alignItems: "center", gap: 7 }}
          >
            {copiedInvite ? <Check style={{ width: 12, height: 12 }} /> : <Copy style={{ width: 12, height: 12 }} />}
            {copiedInvite ? "Copied" : "Copy Invite"}
          </button>
        </div>
        <div style={{ marginTop: 12 }}>
          <SharePanel
            url={`/studio?chamber=collaboration&project=${activeProject.id}`}
            title={`${activeProject.name} — collaborate on M.O.R.E.`}
            description={`Collaborating on "${activeProject.name}" in the M.O.R.E. Creator Suite.`}
          />
        </div>
      </div>
    </div>
  );
}

const labelStyle = { display: "block", fontSize: 10, fontFamily: "monospace", letterSpacing: "0.1em", textTransform: "uppercase", color: "rgba(109,40,217,0.8)", marginBottom: 6 };
const inputStyle = { width: "100%", background: "rgba(28,25,23,0.04)", border: "1px solid rgba(109,40,217,0.25)", padding: "9px 12px", color: "rgba(28,25,23,0.9)", fontSize: 13, fontFamily: "inherit", outline: "none", borderRadius: 4, boxSizing: "border-box" };
