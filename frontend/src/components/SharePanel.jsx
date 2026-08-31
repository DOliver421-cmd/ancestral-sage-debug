/**
 * SharePanel — universal "share everywhere" component.
 *
 * Usage:
 *   <SharePanel url="/courses?highlight=abc123" title="My Course" />
 *   <SharePanel url="/creators/username" title="My Profile" embed />
 *
 * Props:
 *   url      — relative or absolute URL to share (relative = prepends window.origin)
 *   title    — content title for social text
 *   embed    — if true, shows an embeddable profile card snippet too
 *   compact  — if true, renders as a single icon button with popover (default: false = inline row)
 */

import { useState, useRef, useEffect } from "react";
import { Share2, Copy, Check, X, ClipboardCopy } from "lucide-react";
import { toast } from "sonner";

const PLATFORMS = [
  {
    key: "x",
    label: "X",
    icon: "𝕏",
    color: "#000",
    build: (url, title) =>
      `https://twitter.com/intent/tweet?text=${encodeURIComponent(title)}&url=${encodeURIComponent(url)}`,
  },
  {
    key: "facebook",
    label: "Facebook",
    icon: "f",
    color: "#1877f2",
    build: (url) =>
      `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(url)}`,
  },
  {
    key: "whatsapp",
    label: "WhatsApp",
    icon: "W",
    color: "#25d366",
    build: (url, title) =>
      `https://wa.me/?text=${encodeURIComponent(`${title} ${url}`)}`,
  },
  {
    key: "linkedin",
    label: "LinkedIn",
    icon: "in",
    color: "#0a66c2",
    build: (url, title) =>
      `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(url)}&title=${encodeURIComponent(title)}`,
  },
  {
    key: "threads",
    label: "Threads",
    icon: "@",
    color: "#000",
    build: (url, title) =>
      `https://www.threads.net/intent/post?text=${encodeURIComponent(`${title} ${url}`)}`,
  },
  {
    key: "email",
    label: "Email",
    icon: "✉",
    color: "#7c3aed",
    build: (url, title) =>
      `mailto:?subject=${encodeURIComponent(title)}&body=${encodeURIComponent(`${title}\n\n${url}`)}`,
  },
];

// Drive / Dropbox / any other app have no public share-intent URLs — the user
// pastes the copied link into the app they choose (or uses the native share
// sheet, which lists them automatically). Never publish to a public destination
// automatically: the user always picks the audience.

// Copy-only platforms (no share URL — require mobile app or paste workflow)
const COPY_PLATFORMS = [
  {
    key: "youtube",
    label: "YouTube Desc",
    icon: "▶",
    color: "#ff0000",
    buildText: (url, title, description) =>
      `📚 ${title} | Free on M.O.R.E. Help Center\n\n${description || "Join the community, learn real skills, and earn certificates."}\n\n👉 Enroll free: ${url}\n\n#MORE #FreeEducation #WorkforceTraining`,
  },
  {
    key: "instagram",
    label: "Instagram",
    icon: "◎",
    color: "#e1306c",
    buildText: (url, title) =>
      `${title} — free on M.O.R.E. Help Center 🎓\n\nReal skills. Real community. Real certificates.\n\nLink in bio 👉 ${url}\n\n#MORE #FreeEducation #Community`,
  },
  {
    key: "tiktok",
    label: "TikTok",
    icon: "♪",
    color: "#010101",
    buildText: (url, title) =>
      `${title} 🎓 FREE on M.O.R.E. Help Center — link in bio!\n${url}`,
  },
];

function buildAbsoluteUrl(url) {
  if (!url) return window.location.href;
  if (url.startsWith("http")) return url;
  return `${window.location.origin}${url.startsWith("/") ? "" : "/"}${url}`;
}

function buildEmbedSnippet(absUrl, title) {
  return `<a href="${absUrl}" target="_blank" rel="noopener" style="display:inline-block;padding:10px 18px;background:#c87941;color:#fff;font-weight:bold;border-radius:6px;text-decoration:none;">${title}</a>`;
}

export default function SharePanel({ url, title = "Check this out", description = "", embed = false, compact = false, trigger = null }) {
  const [open, setOpen] = useState(false);
  const [copied, setCopied] = useState(false);
  const [embedCopied, setEmbedCopied] = useState(false);
  const [copiedPlatform, setCopiedPlatform] = useState(null);
  const [openUp, setOpenUp] = useState(true);
  const panelRef = useRef(null);

  const absUrl = buildAbsoluteUrl(url);

  useEffect(() => {
    if (!open) return;
    function handleClick(e) {
      if (panelRef.current && !panelRef.current.contains(e.target)) setOpen(false);
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [open]);

  function nativeShare() {
    const shareData = { title, text: `${title} — WAI Institute & M.O.R.E. Help Center`, url: absUrl };
    if (navigator.share) {
      navigator.share(shareData)
        .then(() => setOpen(false))
        .catch((err) => {
          // User closed the sheet — leave the panel open so they can pick another way.
          if (err && err.name === "AbortError") return;
          copyLink();
          toast.info("Link copied — paste it into Email, Drive, Dropbox, or any app you choose.");
        });
      return;
    }
    // No native sheet (some desktop browsers) — copy the link; the user pastes
    // it into the app they choose. Never publish anywhere automatically.
    copyLink();
    toast.info("Link copied — paste it into Email, Drive, Dropbox, or any app you choose.");
  }

  function copyLink() {
    navigator.clipboard?.writeText(absUrl).then(() => {
      setCopied(true);
      toast.success("Link copied!");
      setTimeout(() => setCopied(false), 2000);
    }).catch(() => {
      prompt("Copy this link:", absUrl);
    });
  }

  function copyEmbed() {
    const snippet = buildEmbedSnippet(absUrl, title);
    navigator.clipboard?.writeText(snippet).then(() => {
      setEmbedCopied(true);
      toast.success("Embed code copied!");
      setTimeout(() => setEmbedCopied(false), 2000);
    }).catch(() => {
      prompt("Copy embed code:", snippet);
    });
  }

  function openPlatform(platform) {
    window.open(platform.build(absUrl, title), "_blank", "noopener,width=600,height=500");
  }

  function copyCaptionForPlatform(platform) {
    const text = platform.buildText(absUrl, title, description);
    navigator.clipboard?.writeText(text).then(() => {
      setCopiedPlatform(platform.key);
      toast.success(`${platform.label} caption copied — paste it in!`);
      setTimeout(() => setCopiedPlatform(null), 2500);
    }).catch(() => {
      prompt(`Copy this ${platform.label} caption:`, text);
    });
  }

  function toggleOpen(e) {
    // Open upward when there is room above the trigger, otherwise downward
    // (hero/share buttons near the top of the viewport would clip otherwise).
    const r = e.currentTarget.getBoundingClientRect();
    setOpenUp((r.top || 0) > 320);
    setOpen(v => !v);
  }

  if (compact) {
    return (
      <div ref={panelRef} style={{ position: "relative", display: "inline-block" }}>
        {trigger ? (
          <span onClick={toggleOpen} style={{ display: "inline-flex", cursor: "pointer" }}>{trigger}</span>
        ) : (
          <button
            onClick={toggleOpen}
            title="Share"
            className="p-2 text-ink/40 hover:text-copper transition-colors"
          >
            <Share2 className="w-4 h-4" />
          </button>
        )}
        {open && (
          <div style={{
            position: "absolute", right: 0, zIndex: 200,
            top: openUp ? undefined : "calc(100% + 6px)",
            bottom: openUp ? "calc(100% + 6px)" : undefined,
            background: "white", border: "1px solid #e5e7eb", borderRadius: 12,
            boxShadow: "0 8px 32px rgba(0,0,0,0.12)", padding: "12px 14px",
            width: 250, display: "flex", flexDirection: "column", gap: 8,
          }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 2 }}>
              <span style={{ fontSize: 12, fontWeight: 700, color: "#374151", textTransform: "uppercase", letterSpacing: "0.05em" }}>Share</span>
              <button onClick={() => setOpen(false)} style={{ background: "none", border: "none", cursor: "pointer", color: "#9ca3af", padding: 0 }}>
                <X style={{ width: 14, height: 14 }} />
              </button>
            </div>
            <PanelBody
              absUrl={absUrl} title={title} embed={embed}
              copied={copied} embedCopied={embedCopied} copiedPlatform={copiedPlatform}
              nativeShare={nativeShare}
              copyLink={copyLink} copyEmbed={copyEmbed} openPlatform={openPlatform}
              copyCaptionForPlatform={copyCaptionForPlatform}
            />
          </div>
        )}
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
      <PanelBody
        absUrl={absUrl} title={title} embed={embed}
        copied={copied} embedCopied={embedCopied} copiedPlatform={copiedPlatform}
        nativeShare={nativeShare}
        copyLink={copyLink} copyEmbed={copyEmbed} openPlatform={openPlatform}
        copyCaptionForPlatform={copyCaptionForPlatform}
      />
    </div>
  );
}

function PanelBody({ absUrl, title, embed, copied, embedCopied, copiedPlatform, nativeShare, copyLink, copyEmbed, openPlatform, copyCaptionForPlatform }) {
  return (
    <>
      {/* Native share first — OS sheet lists Email, Drive, Dropbox, Messages, and
          every installed app. The user picks the audience; nothing is shared
          publicly by default. */}
      <button
        onClick={nativeShare}
        title="Share with your apps (Email, Drive, Dropbox, Messages…)"
        style={{
          background: "#1B4332", color: "#fff", border: "none", borderRadius: 8,
          padding: "8px 10px", cursor: "pointer", fontSize: 12, fontWeight: 800,
          display: "flex", alignItems: "center", gap: 6, width: "100%",
        }}
      >
        <Share2 style={{ width: 14, height: 14 }} />
        Share with your apps — Email, Drive, Dropbox…
      </button>
      <div style={{ fontSize: 10, color: "#9ca3af", fontWeight: 600, marginTop: -2 }}>
        You choose the audience. Nothing is shared publicly by default.
      </div>

      {/* Copy link row */}
      <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
        <input
          readOnly
          value={absUrl}
          style={{ flex: 1, fontSize: 11, padding: "5px 8px", borderRadius: 6, border: "1px solid #e5e7eb", color: "#6b7280", background: "#f9fafb", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}
          onFocus={e => e.target.select()}
        />
        <button
          onClick={copyLink}
          style={{ background: copied ? "#16a34a" : "#c87941", color: "#fff", border: "none", borderRadius: 6, padding: "5px 10px", cursor: "pointer", fontSize: 11, fontWeight: 700, display: "flex", alignItems: "center", gap: 4, flexShrink: 0 }}
        >
          {copied ? <Check style={{ width: 12, height: 12 }} /> : <Copy style={{ width: 12, height: 12 }} />}
          {copied ? "Copied" : "Copy"}
        </button>
      </div>

      {/* Share-link platforms (open in new tab) */}
      <div style={{ fontSize: 10, color: "#9ca3af", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.05em" }}>Share link</div>
      <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
        {PLATFORMS.map(p => (
          <button
            key={p.key}
            onClick={() => openPlatform(p)}
            title={`Share on ${p.label}`}
            style={{
              background: p.color, color: "#fff", border: "none", borderRadius: 6,
              padding: "5px 10px", cursor: "pointer", fontSize: 11, fontWeight: 700,
              display: "flex", alignItems: "center", gap: 4,
            }}
          >
            <span style={{ fontWeight: 900 }}>{p.icon}</span> {p.label}
          </button>
        ))}
      </div>

      {/* Copy-caption platforms (YouTube, Instagram, TikTok) */}
      <div style={{ fontSize: 10, color: "#9ca3af", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.05em", marginTop: 2 }}>Copy caption / description</div>
      <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
        {COPY_PLATFORMS.map(p => {
          const isCopied = copiedPlatform === p.key;
          return (
            <button
              key={p.key}
              onClick={() => copyCaptionForPlatform(p)}
              title={`Copy ${p.label} caption`}
              style={{
                background: isCopied ? "#16a34a" : p.color, color: "#fff", border: "none", borderRadius: 6,
                padding: "5px 10px", cursor: "pointer", fontSize: 11, fontWeight: 700,
                display: "flex", alignItems: "center", gap: 4,
              }}
            >
              {isCopied ? <Check style={{ width: 11, height: 11 }} /> : <ClipboardCopy style={{ width: 11, height: 11 }} />}
              {isCopied ? "Copied!" : p.label}
            </button>
          );
        })}
      </div>

      {/* Embed code (profile/page embeds) */}
      {embed && (
        <div style={{ borderTop: "1px solid #f3f4f6", paddingTop: 8 }}>
          <div style={{ fontSize: 11, color: "#9ca3af", marginBottom: 4 }}>Embed on any site</div>
          <button
            onClick={copyEmbed}
            style={{ fontSize: 11, color: embedCopied ? "#16a34a" : "#c87941", fontWeight: 700, background: "none", border: "1px solid currentColor", borderRadius: 6, padding: "4px 10px", cursor: "pointer", display: "flex", alignItems: "center", gap: 4 }}
          >
            {embedCopied ? <Check style={{ width: 11, height: 11 }} /> : <Copy style={{ width: 11, height: 11 }} />}
            {embedCopied ? "Embed Copied" : "Copy Embed Code"}
          </button>
        </div>
      )}
    </>
  );
}
