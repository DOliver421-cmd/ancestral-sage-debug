import { useEffect, useState } from "react";

// The avatar "wears the user's face." The chosen photo is stored client-side
// (localStorage) so it works with no backend write; falls back to /sovereign.svg
// if present in /public, then to initials. The always-on amber dot = "busy /
// working, call his attention."
export const SOVEREIGN_AVATAR_KEY = "sovereign_avatar_url";

export function getSovereignAvatar() {
  try {
    return localStorage.getItem(SOVEREIGN_AVATAR_KEY) || "";
  } catch {
    return "";
  }
}

export default function SovereignAvatar({ size = 48, busy = true, name = "The Sovereign", className = "" }) {
  const [src, setSrc] = useState(() => getSovereignAvatar() || "/sovereign.svg");
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    const sync = () => {
      setFailed(false);
      setSrc(getSovereignAvatar() || "/sovereign.svg");
    };
    window.addEventListener("storage", sync);
    window.addEventListener("sovereign-avatar-changed", sync);
    return () => {
      window.removeEventListener("storage", sync);
      window.removeEventListener("sovereign-avatar-changed", sync);
    };
  }, []);

  const initials = (name || "?")
    .split(" ")
    .map((w) => w[0])
    .filter(Boolean)
    .slice(0, 2)
    .join("")
    .toUpperCase();

  const dot = (
    <span
      className="wai-busy-dot absolute"
      style={{ right: 0, bottom: 0 }}
      title="Always working — call his attention"
    />
  );

  return (
    <div className={`relative inline-flex shrink-0 ${className}`} style={{ width: size, height: size }}>
      {src && !failed ? (
        <img
          src={src}
          alt={name}
          onError={() => setFailed(true)}
          className="rounded-full object-cover"
          style={{ width: size, height: size, border: "2px solid var(--wai-gold)" }}
        />
      ) : (
        <div
          className="rounded-full flex items-center justify-center font-heading font-black"
          style={{
            width: size,
            height: size,
            background: "var(--wai-purple)",
            color: "var(--wai-gold-light)",
            border: "2px solid var(--wai-gold)",
            fontSize: Math.round(size * 0.36),
          }}
        >
          {initials}
        </div>
      )}
      {busy && dot}
    </div>
  );
}
