/**
 * Social Publisher
 *
 * Two modes:
 *  1. AI Format — write once, AI adapts for each platform's style/limits,
 *     one-click copy + native share deep-link (zero API keys required)
 *  2. Direct Post — uses per-user OAuth tokens stored in their own profile
 *     (not Railway env vars). Users connect accounts in Settings → Social.
 */

import { useState } from "react";
import { useAuth } from "../lib/auth";
import { api } from "../lib/api";
import { toast } from "sonner";
import AppShell from "../components/AppShell";
import CreatorContextBar from "../components/CreatorContextBar";
import { Copy, ExternalLink, Sparkles, Loader, CheckCircle, Settings } from "lucide-react";
import { Link } from "react-router-dom";

const PLATFORMS = [
  {
    id: "twitter",
    label: "Twitter / X",
    limit: 280,
    color: "#000",
    bg: "#f7f7f7",
    emoji: "🐦",
    hint: "Short, punchy. Under 280 chars. Hook first.",
    shareUrl: (text) => `https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}`,
  },
  {
    id: "instagram",
    label: "Instagram",
    limit: 2200,
    color: "#c13584",
    bg: "#fdf0f7",
    emoji: "📸",
    hint: "Story-style caption. End with hashtags.",
    shareUrl: null, // Instagram has no web share URL — show copy only
  },
  {
    id: "facebook",
    label: "Facebook",
    limit: 63206,
    color: "#1877f2",
    bg: "#f0f4ff",
    emoji: "👥",
    hint: "Conversational, longer OK. Include a link or image.",
    shareUrl: (text, link) => link
      ? `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(link)}&quote=${encodeURIComponent(text)}`
      : `https://www.facebook.com/sharer/sharer.php?quote=${encodeURIComponent(text)}`,
  },
  {
    id: "tiktok",
    label: "TikTok",
    limit: 2200,
    color: "#ff0050",
    bg: "#fff0f3",
    emoji: "🎵",
    hint: "Hook in first 3 words. Energetic. Trending audio mention.",
    shareUrl: null,
  },
  {
    id: "threads",
    label: "Threads",
    limit: 500,
    color: "#000",
    bg: "#f5f5f5",
    emoji: "🧵",
    hint: "Conversational. Under 500 chars. Opinion or hot take.",
    shareUrl: (text) => `https://www.threads.net/intent/post?text=${encodeURIComponent(text)}`,
  },
  {
    id: "linkedin",
    label: "LinkedIn",
    limit: 3000,
    color: "#0077b5",
    bg: "#f0f7ff",
    emoji: "💼",
    hint: "Professional insight. Value-first. Can be longer.",
    shareUrl: (text, link) => link
      ? `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(link)}&summary=${encodeURIComponent(text)}`
      : `https://www.linkedin.com/feed/?shareActive=true&text=${encodeURIComponent(text)}`,
  },
];

function PlatformCard({ platform, result, linkUrl, copied, onCopy }) {
  const shareUrl = platform.shareUrl?.(result, linkUrl) ?? null;
  const overLimit = result.length > platform.limit;

  return (
    <div style={{
      border: `1.5px solid ${platform.color}25`,
      borderRadius: 14,
      overflow: "hidden",
      background: "#fff",
    }}>
      {/* Header */}
      <div style={{
        background: platform.bg,
        padding: "10px 16px",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        borderBottom: `1px solid ${platform.color}15`,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{ fontSize: 18 }}>{platform.emoji}</span>
          <span style={{ fontWeight: 700, fontSize: 13, color: platform.color }}>{platform.label}</span>
        </div>
        <span style={{
          fontSize: 11, fontWeight: 700,
          color: overLimit ? "#ef4444" : "#9ca3af",
        }}>
          {result.length}{platform.limit < 63206 ? `/${platform.limit}` : ""}
        </span>
      </div>

      {/* Content */}
      <div style={{ padding: "14px 16px" }}>
        <pre style={{
          whiteSpace: "pre-wrap", wordBreak: "break-word",
          fontSize: "0.88rem", lineHeight: 1.7, color: "#1a1a1a",
          margin: 0, fontFamily: "inherit", minHeight: 60,
          maxHeight: 180, overflowY: "auto",
        }}>
          {result}
        </pre>
        {overLimit && (
          <p style={{ color: "#ef4444", fontSize: 11, marginTop: 8, fontWeight: 600 }}>
            Over {platform.label} character limit — trim before posting.
          </p>
        )}
      </div>

      {/* Actions */}
      <div style={{
        padding: "10px 16px",
        borderTop: `1px solid ${platform.color}10`,
        display: "flex",
        gap: 8,
      }}>
        <button
          onClick={() => onCopy(platform.id, result)}
          style={{
            flex: 1, display: "flex", alignItems: "center", justifyContent: "center",
            gap: 6, padding: "8px", border: `1px solid ${platform.color}30`,
            borderRadius: 8, background: "transparent", color: platform.color,
            fontSize: 12, fontWeight: 600, cursor: "pointer",
          }}
        >
          {copied === platform.id
            ? <><CheckCircle size={13} /> Copied!</>
            : <><Copy size={13} /> Copy</>}
        </button>
        {shareUrl && (
          <a
            href={shareUrl}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              flex: 1, display: "flex", alignItems: "center", justifyContent: "center",
              gap: 6, padding: "8px", background: platform.color,
              color: "#fff", borderRadius: 8, fontSize: 12, fontWeight: 600,
              textDecoration: "none",
            }}
          >
            <ExternalLink size={13} /> Open {platform.label}
          </a>
        )}
      </div>
    </div>
  );
}

export default function SocialPublish() {
  const { user } = useAuth();
  const [content, setContent]       = useState("");
  const [linkUrl, setLinkUrl]       = useState("");
  const [selected, setSelected]     = useState(["twitter", "instagram", "facebook"]);
  const [results, setResults]       = useState(null);
  const [loading, setLoading]       = useState(false);
  const [copied, setCopied]         = useState(null);

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
      // Extract JSON from response
      const match = raw.match(/\{[\s\S]*\}/);
      if (!match) throw new Error("AI did not return valid JSON");
      const parsed = JSON.parse(match[0]);
      setResults(parsed);
      toast.success("Posts formatted for all platforms!");
    } catch (e) {
      toast.error("Format failed: " + (e?.message || "Try again"));
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
      <div style={{ maxWidth: 820, margin: "0 auto", padding: "40px 24px 80px" }}>

        {/* Header */}
        <div style={{ marginBottom: 32 }}>
          <div style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.15em", color: "#b5651d", marginBottom: 6 }}>
            Creator Feature · Available to all members
          </div>
          <h1 style={{ fontSize: "1.9rem", fontWeight: 900, color: "#1a1a1a", margin: 0, marginBottom: 8 }}>Social Blast</h1>
          <p style={{ color: "#6b7280", fontSize: 14, margin: 0 }}>
            Write your post once — AI reformats it for Twitter/X, Instagram, Facebook, TikTok, Threads, and LinkedIn automatically.
            No extra accounts needed. Copy the text or click to open each platform directly.
          </p>
        </div>

        {/* Platform selector */}
        <div style={{ marginBottom: 24 }}>
          <div style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.12em", color: "#6b7280", marginBottom: 10 }}>
            Select Platforms
          </div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
            {PLATFORMS.map(p => (
              <button key={p.id}
                onClick={() => togglePlatform(p.id)}
                style={{
                  padding: "8px 16px", borderRadius: 99, fontSize: 13, fontWeight: 600, cursor: "pointer",
                  border: `1.5px solid ${selected.includes(p.id) ? p.color : "#e5e7eb"}`,
                  background: selected.includes(p.id) ? p.bg : "#fff",
                  color: selected.includes(p.id) ? p.color : "#6b7280",
                  transition: "all 0.15s",
                }}
              >
                {p.emoji} {p.label}
              </button>
            ))}
          </div>
        </div>

        {/* Content input */}
        <div style={{ marginBottom: 16 }}>
          <label style={{ display: "block", fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.12em", color: "#6b7280", marginBottom: 8 }}>
            Your Post
          </label>
          <textarea
            value={content}
            onChange={e => setContent(e.target.value)}
            placeholder="Write your base post here — the AI will adapt it for each platform…"
            rows={5}
            style={{
              width: "100%", padding: "14px 16px", border: "1.5px solid #e5e7eb",
              borderRadius: 12, fontSize: 14, lineHeight: 1.7, resize: "vertical",
              outline: "none", boxSizing: "border-box", fontFamily: "inherit",
              transition: "border-color 0.15s",
            }}
            onFocus={e => e.target.style.borderColor = "#b5651d"}
            onBlur={e => e.target.style.borderColor = "#e5e7eb"}
          />
        </div>

        {/* Link */}
        <div style={{ marginBottom: 24 }}>
          <label style={{ display: "block", fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.12em", color: "#6b7280", marginBottom: 8 }}>
            Link to include (optional)
          </label>
          <input
            value={linkUrl}
            onChange={e => setLinkUrl(e.target.value)}
            placeholder="https://…"
            style={{
              width: "100%", padding: "10px 14px", border: "1.5px solid #e5e7eb",
              borderRadius: 10, fontSize: 13, outline: "none", boxSizing: "border-box", fontFamily: "inherit",
            }}
          />
        </div>

        {/* Generate button */}
        <button
          onClick={generate}
          disabled={loading || !content.trim() || selected.length === 0}
          style={{
            width: "100%", padding: "14px", background: loading ? "#9ca3af" : "#1a1a1a",
            color: "#fff", border: "none", borderRadius: 12, fontSize: 15, fontWeight: 700,
            cursor: loading ? "default" : "pointer", display: "flex", alignItems: "center",
            justifyContent: "center", gap: 8, marginBottom: 32, transition: "background 0.2s",
          }}
        >
          {loading
            ? <><Loader size={16} style={{ animation: "spin 1s linear infinite" }} /> Formatting for {selected.length} platforms…</>
            : <><Sparkles size={16} /> Format for {selected.length} Platform{selected.length !== 1 ? "s" : ""}</>}
        </button>

        {/* Results */}
        {results && (
          <div>
            <div style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.12em", color: "#6b7280", marginBottom: 16 }}>
              ✦ Formatted Posts — copy or click to open platform
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(340px, 1fr))", gap: 16 }}>
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
          background: "#f9fafb", border: "1px solid #e5e7eb",
          borderRadius: 12, fontSize: 13, color: "#6b7280",
          display: "flex", alignItems: "flex-start", gap: 10,
        }}>
          <Settings size={15} style={{ marginTop: 2, flexShrink: 0 }} />
          <div>
            Want to post directly without copying?{" "}
            <Link to="/settings" style={{ color: "#b5651d", fontWeight: 600 }}>
              Connect your own social accounts in Settings
            </Link>
            {" "}— your tokens are stored privately in your profile, not shared platform-wide.
          </div>
        </div>

        <style>{`@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }`}</style>
      </div>
    </AppShell>
  );
}
