import { useState, useEffect } from "react";
import { toast } from "sonner";
import { Globe, Copy, Check, RefreshCw, Wand2 } from "lucide-react";
import SharePanel from "../../SharePanel";

const CONTENT_TYPES = ["Single", "Album / EP", "Course", "Ebook / Guide", "Beat / Instrumental", "Podcast Episode", "Video / Reel", "Merch Drop"];
const GENRES = ["Hip-Hop", "R&B", "Gospel", "Afrobeats", "Neo-Soul", "Reggae", "Jazz", "Pop", "Spoken Word", "Educational", "Other"];

export default function PublishingGate({ tier = "base", sovereignDispatch, artifact }) {
  const [tab, setTab] = useState("metadata");
  const [form, setForm] = useState({ title: "", artist: "", content_type: "Single", genre: "Hip-Hop", description: "", tags: "" });
  const [meta, setMeta] = useState(null);
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState({});

  // Receive metadata JSON from Sovereign
  useEffect(() => {
    if (artifact) {
      try {
        const parsed = JSON.parse(artifact.replace(/```json\n?|```/g, "").trim());
        setMeta(parsed);
      } catch {
        setMeta({ raw: artifact });
      }
      setLoading(false);
    }
  }, [artifact]);

  const generate = async () => {
    if (!form.title.trim()) { toast.error("Title is required."); return; }
    if (!sovereignDispatch?.current) { toast.error("Sovereign is not connected."); return; }
    setLoading(true);
    setMeta(null);
    await sovereignDispatch.current({
      action: "generate_metadata",
      context: { title: form.title, content_type: form.content_type, genre: form.genre, description: form.description },
      message: `Generate release metadata for "${form.title}" — ${form.content_type}, ${form.genre} genre.`,
    });
  };

  const copyField = (key, value) => {
    navigator.clipboard?.writeText(value).then(() => {
      setCopied(c => ({ ...c, [key]: true }));
      toast.success(`${key} copied.`);
      setTimeout(() => setCopied(c => ({ ...c, [key]: false })), 2000);
    });
  };

  return (
    <div style={{ fontFamily: "inherit", color: "rgba(255,255,255,0.9)", display: "flex", flexDirection: "column", gap: 0 }}>
      {/* Tab bar */}
      <div style={{ display: "flex", gap: 0, borderBottom: "1px solid rgba(184,134,11,0.2)", marginBottom: 20 }}>
        {[["metadata", "Metadata Generator"], ["social", "Social Templates"], ["checklist", "Release Checklist"]].map(([key, label]) => (
          <button
            key={key}
            onClick={() => setTab(key)}
            style={{
              padding: "9px 16px", border: "none", cursor: "pointer", fontFamily: "monospace",
              fontSize: 11, fontWeight: 700, letterSpacing: "0.06em", textTransform: "uppercase",
              background: "transparent",
              color: tab === key ? "#ffd700" : "rgba(255,255,255,0.4)",
              borderBottom: tab === key ? "2px solid #ffd700" : "2px solid transparent",
              marginBottom: -1,
            }}
          >
            {label}
          </button>
        ))}
      </div>

      {/* Metadata tab */}
      {tab === "metadata" && (
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
            <div>
              <label style={labelStyle}>Title *</label>
              <input style={inputStyle} value={form.title} onChange={e => setForm(f => ({ ...f, title: e.target.value }))} placeholder="Your title..." maxLength={200} />
            </div>
            <div>
              <label style={labelStyle}>Artist / Creator Name</label>
              <input style={inputStyle} value={form.artist} onChange={e => setForm(f => ({ ...f, artist: e.target.value }))} placeholder="Your name or alias..." maxLength={100} />
            </div>
            <div>
              <label style={labelStyle}>Content Type</label>
              <select style={selectStyle} value={form.content_type} onChange={e => setForm(f => ({ ...f, content_type: e.target.value }))}>
                {CONTENT_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
              </select>
            </div>
            <div>
              <label style={labelStyle}>Genre</label>
              <select style={selectStyle} value={form.genre} onChange={e => setForm(f => ({ ...f, genre: e.target.value }))}>
                {GENRES.map(g => <option key={g} value={g}>{g}</option>)}
              </select>
            </div>
          </div>
          <div>
            <label style={labelStyle}>Description / About</label>
            <textarea style={{ ...inputStyle, height: 70, resize: "none" }} value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))} placeholder="What is this about? Theme, story, purpose..." maxLength={1000} />
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
            <div>
              <label style={labelStyle}>Release Date (optional)</label>
              <input style={inputStyle} type="date" value={form.release_date} onChange={e => setForm(f => ({ ...f, release_date: e.target.value }))} />
            </div>
            <div>
              <label style={labelStyle}>Keywords / Tags (comma separated)</label>
              <input style={inputStyle} value={form.tags} onChange={e => setForm(f => ({ ...f, tags: e.target.value }))} placeholder="love, healing, Blackjoy..." maxLength={300} />
            </div>
          </div>
          <button
            onClick={generate} disabled={loading}
            style={{ background: loading ? "rgba(184,134,11,0.3)" : "linear-gradient(135deg, #b8860b, #d4a017)", border: "none", color: "#0a0a0f", fontWeight: 900, fontSize: 13, padding: "11px 22px", cursor: loading ? "default" : "pointer", letterSpacing: "0.08em", textTransform: "uppercase", fontFamily: "monospace", display: "flex", alignItems: "center", gap: 8, alignSelf: "flex-start", boxShadow: loading ? "none" : "0 4px 0 #7a5c0a" }}
          >
            {loading ? <RefreshCw style={{ width: 13, height: 13, animation: "spin 1s linear infinite" }} /> : <Wand2 style={{ width: 13, height: 13 }} />}
            {loading ? "Generating..." : "Generate Metadata"}
          </button>

          {meta && (
            <div style={{ display: "flex", flexDirection: "column", gap: 10, marginTop: 4 }}>
              {Object.entries(meta).filter(([k]) => k !== "raw").map(([key, value]) => (
                <div key={key} style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(184,134,11,0.2)", padding: "10px 12px", borderRadius: 4 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 8 }}>
                    <div style={{ flex: 1 }}>
                      <div style={{ ...labelStyle, marginBottom: 4 }}>{key.replace(/_/g, " ")}</div>
                      <div style={{ fontSize: 13, color: "rgba(255,255,255,0.85)", lineHeight: 1.6 }}>{Array.isArray(value) ? value.join(", ") : value}</div>
                    </div>
                    <button onClick={() => copyField(key, Array.isArray(value) ? value.join(", ") : value)} style={{ ...actionBtn, flexShrink: 0 }}>
                      {copied[key] ? <Check style={{ width: 11, height: 11 }} /> : <Copy style={{ width: 11, height: 11 }} />}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
          <style>{`@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }`}</style>
        </div>
      )}

      {/* Social templates tab */}
      {tab === "social" && (
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {!form.title.trim() ? (
            <div style={{ color: "rgba(255,255,255,0.4)", fontSize: 13, padding: "20px 0" }}>
              Fill in the title and details in the Metadata tab first, then come back here.
            </div>
          ) : (
            <>
              <div style={{ color: "rgba(255,255,255,0.5)", fontSize: 12, marginBottom: 4 }}>
                Ready-made captions for each platform. Click to copy.
              </div>
              {buildSocialTemplates(form).map(({ platform, icon, color, text }) => (
                <div key={platform} style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.08)", borderRadius: 6, overflow: "hidden" }}>
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "8px 12px", borderBottom: "1px solid rgba(255,255,255,0.06)", background: `${color}15` }}>
                    <span style={{ fontSize: 12, fontWeight: 900, color, fontFamily: "monospace" }}>{icon} {platform}</span>
                    <button onClick={() => copyField(platform, text)} style={{ ...actionBtn, color, borderColor: `${color}50`, background: `${color}15` }}>
                      {copied[platform] ? <Check style={{ width: 11, height: 11 }} /> : <Copy style={{ width: 11, height: 11 }} />}
                      <span style={{ fontSize: 10 }}>{copied[platform] ? "Copied" : "Copy"}</span>
                    </button>
                  </div>
                  <div style={{ padding: "10px 12px", fontSize: 12, color: "rgba(255,255,255,0.75)", lineHeight: 1.7, whiteSpace: "pre-wrap" }}>{text}</div>
                </div>
              ))}
              <div style={{ marginTop: 8, paddingTop: 12, borderTop: "1px solid rgba(255,255,255,0.06)" }}>
                <div style={{ ...labelStyle, marginBottom: 8 }}>Or share the direct link</div>
                <SharePanel url={`/courses`} title={form.title} description={form.description} />
              </div>
            </>
          )}
        </div>
      )}

      {/* Release checklist tab */}
      {tab === "checklist" && (
        <ReleaseChecklist type={form.content_type} />
      )}
    </div>
  );
}

function buildSocialTemplates(form) {
  const title = form.title || "New Release";
  const artist = form.artist ? ` by ${form.artist}` : "";
  const type = form.content_type.toLowerCase();
  return [
    {
      platform: "Instagram", icon: "◎", color: "#e1306c",
      text: `🎵 "${title}"${artist} is OUT NOW 🔥\n\n${form.description || `New ${type} dropping. This one is different.`}\n\nLink in bio 👆\n\n#WAIInstitute #NewMusic #BlackCreators #IndependentArtist`,
    },
    {
      platform: "X / Twitter", icon: "𝕏", color: "#ffffff",
      text: `"${title}"${artist} is live 🔥\n\n${form.description ? form.description.slice(0, 100) + (form.description.length > 100 ? "..." : "") : `New ${type}. No skips.`}\n\n#WAIInstitute #NewMusic`,
    },
    {
      platform: "TikTok", icon: "♪", color: "#ff0050",
      text: `${title} just dropped 🎧 Follow for more ${form.genre || "music"} #WAIInstitute #fyp #newmusic #${(form.genre || "music").replace(/\s/g, "").toLowerCase()}`,
    },
    {
      platform: "YouTube", icon: "▶", color: "#ff0000",
      text: `${title}${artist}\n\n${form.description || `New ${type}. Out now.`}\n\n${form.tags ? `Tags: ${form.tags}` : ""}\n\n🎧 Stream / Download: [your link]\n📲 Follow on IG: [your handle]\n\n#WAIInstitute #${(form.genre || "Music").replace(/\s/g, "")} #BlackCreators`,
    },
    {
      platform: "Facebook", icon: "f", color: "#1877f2",
      text: `🎵 "${title}"${artist} is available now!\n\n${form.description || `Fresh ${type} from the WAI community.`}\n\nStream it, share it, support independent Black creators. 🙏\n\n#WAIInstitute #NewMusic #SupportIndependent`,
    },
  ];
}

function ReleaseChecklist({ type }) {
  const CHECKLIST = {
    "Single": ["✅ Final master file (WAV/MP3)", "✅ Cover art (3000×3000px min)", "✅ Metadata filled (title, artist, ISRC)", "✅ Distribution platform selected", "✅ Social posts drafted", "✅ Release date set", "✅ Pre-save link created", "✅ YouTube lyric/visualizer video", "✅ Playlisting pitch sent"],
    "Album / EP": ["✅ All tracks mastered", "✅ Track listing finalized", "✅ Album art front + back", "✅ Credits documented", "✅ UPC code registered", "✅ Distribution submitted (2-3 weeks early)", "✅ Press kit / bio updated", "✅ Rollout plan: singles → album", "✅ Merchandise ready"],
    "Course": ["✅ Course outline complete", "✅ All sections written", "✅ Thumbnail image created", "✅ Promo video recorded", "✅ Price set", "✅ Published on Creator Studio", "✅ Social posts scheduled", "✅ Email list notified", "✅ WAI Arcade promoted alongside"],
    "default": ["✅ Content finalized", "✅ Title and description ready", "✅ Cover/thumbnail created", "✅ Distribution or upload ready", "✅ Social posts drafted", "✅ Links ready to share"],
  };
  const items = CHECKLIST[type] || CHECKLIST.default;
  const [checked, setChecked] = useState({});
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
      <div style={{ color: "rgba(255,255,255,0.5)", fontSize: 12, marginBottom: 4 }}>{type} release checklist</div>
      {items.map((item, i) => (
        <label key={i} style={{ display: "flex", alignItems: "flex-start", gap: 10, cursor: "pointer", padding: "8px 10px", background: checked[i] ? "rgba(34,197,94,0.07)" : "rgba(255,255,255,0.02)", border: `1px solid ${checked[i] ? "rgba(34,197,94,0.25)" : "rgba(255,255,255,0.07)"}`, borderRadius: 4, transition: "all 0.15s" }}>
          <input type="checkbox" checked={!!checked[i]} onChange={() => setChecked(c => ({ ...c, [i]: !c[i] }))} style={{ accentColor: "#22c55e", marginTop: 2 }} />
          <span style={{ fontSize: 13, color: checked[i] ? "rgba(34,197,94,0.8)" : "rgba(255,255,255,0.8)", textDecoration: checked[i] ? "line-through" : "none" }}>
            {item.replace("✅ ", "")}
          </span>
        </label>
      ))}
      <div style={{ marginTop: 8, fontSize: 12, color: "rgba(255,215,0,0.6)", fontFamily: "monospace" }}>
        {Object.values(checked).filter(Boolean).length}/{items.length} complete
      </div>
    </div>
  );
}

const labelStyle = { display: "block", fontSize: 10, fontFamily: "monospace", letterSpacing: "0.1em", textTransform: "uppercase", color: "rgba(184,134,11,0.8)", marginBottom: 6 };
const inputStyle = { width: "100%", background: "rgba(255,255,255,0.04)", border: "1px solid rgba(184,134,11,0.25)", padding: "9px 12px", color: "rgba(255,255,255,0.9)", fontSize: 13, fontFamily: "inherit", outline: "none", borderRadius: 4, boxSizing: "border-box" };
const selectStyle = { ...inputStyle, cursor: "pointer" };
const actionBtn = { background: "rgba(184,134,11,0.15)", border: "1px solid rgba(184,134,11,0.3)", color: "#b8860b", padding: "5px 8px", cursor: "pointer", borderRadius: 4, display: "flex", alignItems: "center", gap: 4, fontSize: 11, fontWeight: 700 };
