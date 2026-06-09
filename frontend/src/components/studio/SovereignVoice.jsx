import { useState, useRef, useEffect, useCallback } from "react";
import { api } from "../../lib/api";
import { Send, ChevronRight, ChevronLeft } from "lucide-react";

const GREETINGS = [
  "Boss, what are we building today?",
  "The Sanctuary is live. Where do we start?",
  "Your tools are ready. What's the vision?",
  "I've got everything prepped. Your call.",
];

const CHAMBER_NOTES = {
  "lyric-forge": "Lyric Forge is open. What are we writing — hook, verse, or bridge?",
  "visual-altar": "Boss, the Visual Altar is lit. Moodboard first, then we'll align the palette.",
  "script": "Script Scriptorium is ready. Tell me the format and I'll help shape the structure.",
  "sound-lab": "Sound Lab is live. Lock in your BPM and I'll build the blueprint.",
  "vault": "Vault of Versions pulled up. Seal a version before any major changes.",
  "publishing-gate": "Publishing Gate open. Let's handle metadata and socials.",
  "marketplace": "Marketplace Forge is coming. You're already ahead by being here.",
  "collaboration": "Collaboration Chamber — when it drops, your co-creators step through this door.",
};

/**
 * Sovereign is the single AI the creator talks to.
 * All chamber actions (generate lyrics, metadata, scripts, blueprints, visual direction)
 * dispatch through Sovereign — he routes internally and delivers in his own voice.
 *
 * Props:
 *   activeChamber  — current chamber id (string)
 *   onArtifact     — callback(artifact_type, artifact_text) — lets the active chamber receive AI output
 *   dispatchRef    — ref that chambers use to trigger a Sovereign action without the user typing
 */
export default function SovereignVoice({ activeChamber, onArtifact, dispatchRef }) {
  const [collapsed, setCollapsed] = useState(false);
  const [messages, setMessages] = useState([
    { role: "sovereign", text: GREETINGS[Math.floor(Math.random() * GREETINGS.length)] }
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Greet creator on chamber change
  useEffect(() => {
    if (activeChamber && CHAMBER_NOTES[activeChamber]) {
      setMessages(m => [...m, { role: "sovereign", text: CHAMBER_NOTES[activeChamber] }]);
    }
  }, [activeChamber]);

  const callSovereign = useCallback(async ({ action = "chat", context = {}, message = "", silent = false }) => {
    if (!silent) {
      setMessages(m => [...m, { role: "user", text: message || `[${action}]` }]);
    }
    setLoading(true);
    // Auto-open when Sovereign has something to say
    setCollapsed(false);
    try {
      const r = await api.post("/studio/sovereign", {
        chamber: activeChamber || "map",
        action,
        context,
        message: message || "",
      });
      const { response, artifact, artifact_type } = r.data;
      setMessages(m => [...m, { role: "sovereign", text: response || "Done.", artifact: artifact ? true : false }]);
      if (artifact && artifact_type && onArtifact) {
        onArtifact(artifact_type, artifact);
      }
    } catch {
      setMessages(m => [...m, { role: "sovereign", text: "Give me a moment — I'll be right back." }]);
    } finally {
      setLoading(false);
    }
  }, [activeChamber, onArtifact]);

  // Expose callSovereign to chambers via ref
  useEffect(() => {
    if (dispatchRef) dispatchRef.current = callSovereign;
  }, [dispatchRef, callSovereign]);

  const send = () => {
    const msg = input.trim();
    if (!msg || loading) return;
    setInput("");
    callSovereign({ action: "chat", message: msg });
  };

  return (
    <div style={{
      position: "fixed", left: 0, top: 0, bottom: 0, zIndex: 50,
      display: "flex", alignItems: "stretch",
      transition: "all 0.3s ease",
    }}>
      {/* Panel */}
      <div style={{
        width: collapsed ? 0 : 280,
        overflow: "hidden",
        transition: "width 0.3s ease",
        background: "rgba(8,8,16,0.97)",
        borderRight: "1px solid rgba(184,134,11,0.25)",
        display: "flex", flexDirection: "column",
      }}>
        {/* Header */}
        <div style={{ padding: "20px 16px 12px", borderBottom: "1px solid rgba(184,134,11,0.15)" }}>
          <div style={{ color: "#b8860b", fontSize: 10, fontFamily: "monospace", letterSpacing: "0.12em", textTransform: "uppercase", marginBottom: 4 }}>
            Sovereign
          </div>
          <div style={{ color: "rgba(255,255,255,0.9)", fontSize: 13, fontWeight: 700 }}>
            Your Studio Manager
          </div>
          <div style={{ color: "rgba(255,255,255,0.35)", fontSize: 10, marginTop: 3 }}>
            All tools report to him.
          </div>
        </div>

        {/* Messages */}
        <div style={{ flex: 1, overflowY: "auto", padding: "12px 14px", display: "flex", flexDirection: "column", gap: 10 }}>
          {messages.map((m, i) => (
            <div key={i} style={{ display: "flex", justifyContent: m.role === "user" ? "flex-end" : "flex-start" }}>
              <div style={{
                maxWidth: "88%",
                padding: "8px 12px",
                borderRadius: m.role === "user" ? "12px 12px 2px 12px" : "12px 12px 12px 2px",
                fontSize: 12,
                lineHeight: 1.6,
                background: m.role === "user" ? "rgba(184,134,11,0.2)" : "rgba(255,255,255,0.06)",
                border: `1px solid ${m.role === "user" ? "rgba(184,134,11,0.35)" : "rgba(255,255,255,0.08)"}`,
                color: m.role === "user" ? "#ffd700" : "rgba(255,255,255,0.88)",
              }}>
                {m.text}
                {m.artifact && (
                  <div style={{ marginTop: 6, fontSize: 10, color: "rgba(184,134,11,0.7)", fontFamily: "monospace", letterSpacing: "0.08em" }}>
                    ↳ RESULT SENT TO CHAMBER
                  </div>
                )}
              </div>
            </div>
          ))}
          {loading && (
            <div style={{ display: "flex" }}>
              <div style={{ padding: "8px 12px", borderRadius: "12px 12px 12px 2px", background: "rgba(255,255,255,0.06)", border: "1px solid rgba(255,255,255,0.08)", color: "rgba(255,255,255,0.3)", fontSize: 12 }}>
                ...
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {/* Input */}
        <div style={{ padding: "10px 12px", borderTop: "1px solid rgba(184,134,11,0.15)", display: "flex", gap: 8 }}>
          <input
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === "Enter" && send()}
            placeholder="Talk to Sovereign..."
            style={{
              flex: 1, background: "rgba(255,255,255,0.04)", border: "1px solid rgba(184,134,11,0.25)",
              padding: "7px 10px", color: "white", fontSize: 12, fontFamily: "inherit", outline: "none", borderRadius: 6,
            }}
          />
          <button
            onClick={send}
            disabled={!input.trim() || loading}
            style={{ background: input.trim() && !loading ? "#b8860b" : "rgba(184,134,11,0.2)", border: "none", borderRadius: 6, padding: "7px 10px", cursor: input.trim() && !loading ? "pointer" : "default", display: "flex", alignItems: "center" }}
          >
            <Send style={{ width: 13, height: 13, color: "#0a0a0f" }} />
          </button>
        </div>
      </div>

      {/* Toggle tab */}
      <button
        onClick={() => setCollapsed(v => !v)}
        style={{
          width: 20, alignSelf: "center",
          background: "rgba(184,134,11,0.15)",
          border: "1px solid rgba(184,134,11,0.3)",
          borderLeft: "none",
          padding: "12px 0",
          cursor: "pointer",
          color: "#b8860b",
          borderRadius: "0 6px 6px 0",
          display: "flex", alignItems: "center", justifyContent: "center",
        }}
        title={collapsed ? "Open Sovereign" : "Collapse Sovereign"}
      >
        {collapsed ? <ChevronRight style={{ width: 12, height: 12 }} /> : <ChevronLeft style={{ width: 12, height: 12 }} />}
      </button>
    </div>
  );
}
