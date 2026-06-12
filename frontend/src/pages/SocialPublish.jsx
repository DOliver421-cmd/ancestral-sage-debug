/**
 * Social Blast — write once, AI adapts for every platform.
 * Dark atmospheric design matching Creator's Sanctuary aesthetic.
 */

import { useState } from "react";
import { useAuth } from "../lib/auth";
import { api } from "../lib/api";
import { toast } from "sonner";
import AppShell from "../components/AppShell";
import CreatorContextBar from "../components/CreatorContextBar";
import { Copy, ExternalLink, Sparkles, Loader, CheckCircle, Settings, Zap } from "lucide-react";
import { Link } from "react-router-dom";

/* ── design tokens ── */
const T = {
  bg:      "#08060f",
  card:    "#100e1a",
  border:  "rgba(74,222,128,0.2)",
  green:   "#4ade80",
  greenDim:"#22c55e",
  gold:    "#d4af37",
  purple:  "#a855f7",
  text:    "#e0d8f0",
  muted:   "#6b6480",
  input:   "#060410",
};

const PLATFORMS = [
  { id: "twitter",   label: "𝕏 Twitter",  limit: 280,   color: "#e2e8f0", neon: "#94a3b8", emoji: "𝕏", hint: "Short, punchy. Hook first. Under 280 chars.", shareUrl: (t) => `https://twitter.com/intent/tweet?text=${encodeURIComponent(t)}` },
  { id: "instagram", label: "Instagram",  limit: 2200,  color: "#f0abfc", neon: "#c084fc", emoji: "📸", hint: "Story-style. End with hashtags.", shareUrl: null },
  { id: "facebook",  label: "Facebook",   limit: 63206, color: "#93c5fd", neon: "#60a5fa", emoji: "👥", hint: "Conversational, longer OK. Include a link.", shareUrl: (t, l) => l ? `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(l)}&quote=${encodeURIComponent(t)}` : `https://www.facebook.com/sharer/sharer.php?quote=${encodeURIComponent(t)}` },
  { id: "tiktok",    label: "TikTok",     limit: 2200,  color: "#fca5a5", neon: "#f87171", emoji: "🎵", hint: "Hook in first 3 words. Energetic. Trending.", shareUrl: null },
  { id: "threads",   label: "Threads",    limit: 500,   color: "#d1d5db", neon: "#9ca3af", emoji: "🧵", hint: "Conversational. Under 500 chars. Hot take.", shareUrl: (t) => `https://www.threads.net/intent/post?text=${encodeURIComponent(t)}` },
  { id: "linkedin",  label: "LinkedIn",   limit: 3000,  color: "#7dd3fc", neon: "#38bdf8", emoji: "💼", hint: "Professional insight. Value-first. Can go long.", shareUrl: (t, l) => l ? `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(l)}&summary=${encodeURIComponent(t)}` : `https://www.linkedin.com/feed/?shareActive=true&text=${encodeURIComponent(t)}` },
];

function PlatformCard({ platform, result, linkUrl, copied, onCopy }) {
  const shareUrl = platform.shareUrl?.(result, linkUrl) ?? null;
  const overLimit = result.length > platform.limit;

  return (
    <div style={{
      background: T.card,
      border: `1px solid ${platform.neon}30`,
      borderRadius: 14,
      overflow: "hidden",
      boxShadow: `0 0 16px ${platform.neon}08`,
    }}>
      <div style={{
        padding: "10px 16px",
        display: "flex", alignItems: "center", justifyContent: "space-between",
        borderBottom: `1px solid ${platform.neon}20`,
        background: `linear-gradient(135deg, ${platform.neon}08, transparent)`,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{ fontSize: 16 }}>{platform.emoji}</span>
          <span style={{ fontWeight: 700, fontSize: 12, color: platform.neon, fontFamily: "monospace", letterSpacing: "0.05em" }}>{platform.label}</span>
        </div>
        <span style={{ fontSize: 10, fontWeight: 700, color: overLimit ? "#f87171" : T.muted, fontFamily: "monospace" }}>
          {result.length}{platform.limit < 63206 ? `/${platform.limit}` : ""}
        </span>
      </div>

      <div style={{ padding: "14px 16px" }}>
        <pre style={{
          whiteSpace: "pre-wrap", wordBreak: "break-word",
          fontSize: "0.82rem", lineHeight: 1.7, color: T.text,
          margin: 0, fontFamily: "inherit", minHeight: 60,
          maxHeight: 160, overflowY: "auto",
        }}>
          {result}
        </pre>
        {overLimit && (
          <p style={{ color: "#f87171", fontSize: 11, marginTop: 8, fontWeight: 600 }}>
            Over {platform.label} limit — trim before posting.
          </p>
        )}
      </div>

      <div style={{ padding: "10px 16px", borderTop: `1px solid ${platform.neon}15`, display: "flex", gap: 8 }}>
        <button
          onClick={() => onCopy(platform.id, result)}
          style={{
            flex: 1, display: "flex", alignItems: "center", justifyContent: "center",
            gap: 6, padding: "8px", border: `1px solid ${platform.neon}40`,
            borderRadius: 8, background: "transparent", color: platform.neon,
            fontSize: 12, fontWeight: 600, cursor: "pointer", fontFamily: "monospace",
          }}
        >
          {copied === platform.id ? <><CheckCircle size={12} /> Copied!</> : <><Copy size={12} /> Copy</>}
        </button>
        {shareUrl && (
          <a href={shareUrl} target="_blank" rel="noopener noreferrer"
            style={{
              flex: 1, display: "flex", alignItems: "center", justifyContent: "center",
              gap: 6, padding: "8px", background: `${platform.neon}20`,
              border: `1px solid ${platform.neon}50`,
              color: platform.neon, borderRadius: 8, fontSize: 12, fontWeight: 600,
              textDecoration: "none", fontFamily: "monospace",
            }}
          >
            <ExternalLink size={12} /> Open
          </a>
        )}
      </div>
    </div>
  );
}

export default function SocialPublish() {
  const { user } = useAuth();
  const [content, setContent]   = useState("");
  const [linkUrl, setLinkUrl]   = useState("");
  const [selected, setSelected] = useState(["twitter", "instagram", "facebook"]);
  const [results, setResults]   = useState(null);
  const [loading, setLoading]   = useState(false);
  const [copied, setCopied]     = useState(null);

  function togglePlatform(id) {
    setSelected(prev => prev.includes(id) ? prev.filter(p => p !== id) : [...prev, id]);
  }

  async function generate() {
    if (!content.trim()) { toast.error("Write your base post first"); return; }
    if (selected.length === 0) { toast.error("Select at least one platform"); return; }
    setLoading(true);
    setResults(null);

    const platformList = PLATFORMS.filter(p => selected.includes(p.id));
    const systemPrompt = `You are a professional social media manager.
Rewrite the user's post for each platform specified, following each platform's conventions strictly.
Return ONLY a valid JSON object — no markdown, no explanation — with platform IDs as keys and the adapted post text as values.
Platform guidelines:
${platformList.map(p => `- ${p.id}: ${p.hint} Max ${p.limit < 63206 ? p.limit + " chars" : "unlimited"}.`).join("\n")}`;

    const userMessage = `Base post: ${content.trim()}${linkUrl ? `\nLink to include: ${linkUrl}` : ""}
Platforms needed: ${selected.join(", ")}
Return JSON only.`;

    try {
      const res = await api.post("/ai/chat", {
        messages: [{ role: "user", content: userMessage }],
        system: systemPrompt,
        persona_label: "social_publisher",
        max_tokens: 1500,
      });

      const raw = res.data?.response || res.data?.text || "";
      const match = raw.match(/\{[\s\S]*\}/);
      if (!match) throw new Error("AI did not return valid JSON");
      const parsed = JSON.parse(match[0]);
      setResults(parsed);
      toast.success("Posts formatted for all platforms!");
    } catch (e) {
      toast.error("Format failed — " + (e?.message || "try again"));
    } finally {
      setLoading(false);
    }
  }

  function copyText(platformId, text) {
    navigator.clipboard?.writeText(text);
    setCopied(platformId);
    setTimeout(() => setCopied(null), 2000);
    toast.success("Copied!");
  }

  return (
    <AppShell>
      <CreatorContextBar current="blast" />
      <div style={{ background: T.bg, minHeight: "100vh", color: T.text }}>
        <div style={{ maxWidth: 860, margin: "0 auto", padding: "40px 24px 80px" }}>

          {/* Hero header */}
          <div style={{ marginBottom: 36, position: "relative" }}>
            <div style={{ fontSize: "0.65rem", fontFamily: "monospace", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.15em", color: T.greenDim, marginBottom: 8 }}>
              ◈ CREATOR FEATURE · ALL TIERS
            </div>
            <h1 style={{ fontFamily: "monospace", fontSize: "clamp(1.6rem,4vw,2.8rem)", fontWeight: 900, color: T.green, textShadow: `0 0 30px rgba(74,222,128,0.4)`, margin: 0, lineHeight: 1.1, marginBottom: 8 }}>
              SOCIAL BLAST
            </h1>
            <p style={{ color: T.muted, fontSize: 14, margin: 0, maxWidth: 560, lineHeight: 1.6 }}>
              Write once — AI adapts your post for every platform. Copy the text or click to open each platform directly. One voice, everywhere you need to be.
            </p>
          </div>

          {/* Platform selector */}
          <div style={{ marginBottom: 28, padding: "20px 22px", background: T.card, border: `1px solid ${T.border}`, borderRadius: 14 }}>
            <div style={{ fontSize: "0.65rem", fontFamily: "monospace", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.12em", color: T.gold, marginBottom: 14 }}>
              SELECT PLATFORMS
            </div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
              {PLATFORMS.map(p => {
                const on = selected.includes(p.id);
                return (
                  <button key={p.id}
                    onClick={() => togglePlatform(p.id)}
                    style={{
                      padding: "7px 16px", borderRadius: 99, fontSize: 12, fontWeight: 700, cursor: "pointer",
                      border: `1.5px solid ${on ? p.neon : "rgba(255,255,255,0.1)"}`,
                      background: on ? `${p.neon}15` : "transparent",
                      color: on ? p.neon : T.muted,
                      fontFamily: "monospace", letterSpacing: "0.04em",
                      transition: "all 0.15s",
                      boxShadow: on ? `0 0 10px ${p.neon}20` : "none",
                    }}
                  >
                    {p.emoji} {p.label}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Compose area */}
          <div style={{ padding: "22px", background: T.card, border: `1px solid ${T.border}`, borderRadius: 14, marginBottom: 20 }}>
            <div style={{ fontSize: "0.65rem", fontFamily: "monospace", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.12em", color: T.gold, marginBottom: 10 }}>
              YOUR POST
            </div>
            <textarea
              value={content}
              onChange={e => setContent(e.target.value)}
              placeholder="Write your message here — the AI will adapt the tone, format, and length for each platform…"
              rows={5}
              style={{
                width: "100%", padding: "14px 16px",
                background: T.input, border: `1px solid rgba(74,222,128,0.2)`,
                borderRadius: 10, fontSize: 14, lineHeight: 1.7,
                color: T.text, resize: "vertical", outline: "none",
                boxSizing: "border-box", fontFamily: "inherit",
                transition: "border-color 0.15s",
              }}
              onFocus={e => e.target.style.borderColor = T.green}
              onBlur={e => e.target.style.borderColor = "rgba(74,222,128,0.2)"}
            />
            <div style={{ marginTop: 14 }}>
              <div style={{ fontSize: "0.65rem", fontFamily: "monospace", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.12em", color: T.muted, marginBottom: 8 }}>
                LINK (OPTIONAL)
              </div>
              <input
                value={linkUrl}
                onChange={e => setLinkUrl(e.target.value)}
                placeholder="https://your-link.com"
                style={{
                  width: "100%", padding: "10px 14px",
                  background: T.input, border: `1px solid rgba(74,222,128,0.15)`,
                  borderRadius: 8, fontSize: 13, color: T.text,
                  outline: "none", boxSizing: "border-box", fontFamily: "inherit",
                }}
              />
            </div>
          </div>

          {/* Blast button */}
          <button
            onClick={generate}
            disabled={loading || !content.trim() || selected.length === 0}
            style={{
              width: "100%", padding: "16px",
              background: loading ? "rgba(74,222,128,0.15)" : "linear-gradient(135deg, #16a34a, #15803d)",
              color: T.green, border: `1.5px solid ${T.green}`,
              borderRadius: 12, fontSize: 15, fontWeight: 900,
              cursor: loading ? "default" : "pointer",
              display: "flex", alignItems: "center", justifyContent: "center", gap: 10,
              marginBottom: 32, fontFamily: "monospace", letterSpacing: "0.08em",
              boxShadow: loading ? "none" : `0 0 24px rgba(74,222,128,0.25)`,
              opacity: (!content.trim() || selected.length === 0) ? 0.5 : 1,
              transition: "all 0.2s",
            }}
          >
            {loading
              ? <><Loader size={16} style={{ animation: "spin 1s linear infinite" }} /> FORMATTING FOR {selected.length} PLATFORMS…</>
              : <><Zap size={16} /> BLAST TO {selected.length} PLATFORM{selected.length !== 1 ? "S" : ""}</>}
          </button>

          {/* Results */}
          {results && (
            <div>
              <div style={{ fontSize: "0.65rem", fontFamily: "monospace", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.12em", color: T.gold, marginBottom: 16 }}>
                ✦ FORMATTED POSTS — COPY OR CLICK TO OPEN
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(340px, 1fr))", gap: 14 }}>
                {PLATFORMS.filter(p => selected.includes(p.id) && results[p.id]).map(p => (
                  <PlatformCard
                    key={p.id}
                    platform={p}
                    result={results[p.id]}
                    linkUrl={linkUrl}
                    copied={copied}
                    onCopy={copyText}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Footer note */}
          <div style={{
            marginTop: 40, padding: "16px 20px",
            background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.08)",
            borderRadius: 12, fontSize: 13, color: T.muted,
            display: "flex", alignItems: "flex-start", gap: 10,
          }}>
            <Settings size={14} style={{ marginTop: 2, flexShrink: 0, color: T.greenDim }} />
            <div>
              Want to post directly without copying?{" "}
              <Link to="/settings" style={{ color: T.green, fontWeight: 600 }}>Connect your accounts in Settings → Social</Link>
              {" "}to enable one-click direct posting.
            </div>
          </div>

        </div>
      </div>
    </AppShell>
  );
}
