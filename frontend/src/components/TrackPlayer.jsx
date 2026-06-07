import { useRef, useState, useEffect, useCallback } from "react";
import { Play, Pause, Volume2, VolumeX, Music } from "lucide-react";

/**
 * TrackPlayer — glitch-free audio player for original + AI version tracks.
 *
 * Design decisions that prevent blink/glitch:
 * - Two hidden <audio> elements are mounted ONCE and never removed from the DOM.
 * - Version switching pauses the old element, syncs position, then plays the new one.
 * - src is set imperatively via ref so React never remounts the audio elements.
 * - preload="auto" on both elements so version switching is near-instant.
 */
export default function TrackPlayer({ track, accentColor = "amber" }) {
  const origRef = useRef(null);
  const aiRef   = useRef(null);

  const [version,   setVersion]   = useState("original"); // "original" | "ai"
  const [playing,   setPlaying]   = useState(false);
  const [muted,     setMuted]     = useState(false);
  const [progress,  setProgress]  = useState(0);   // 0–100
  const [duration,  setDuration]  = useState(0);
  const [loaded,    setLoaded]    = useState({ original: false, ai: false });

  const active  = version === "original" ? origRef : aiRef;
  const passive = version === "original" ? aiRef   : origRef;

  // Set srcs once on mount
  useEffect(() => {
    if (origRef.current && track.original_url) {
      origRef.current.src = track.original_url;
      origRef.current.load();
    }
    if (aiRef.current && track.ai_url) {
      aiRef.current.src = track.ai_url;
      aiRef.current.load();
    }
  }, [track.original_url, track.ai_url]);

  const syncProgress = useCallback(() => {
    const el = active.current;
    if (!el || !el.duration) return;
    setProgress((el.currentTime / el.duration) * 100);
    setDuration(el.duration);
  }, [active]);

  useEffect(() => {
    const el = active.current;
    if (!el) return;
    el.addEventListener("timeupdate", syncProgress);
    el.addEventListener("ended", () => { setPlaying(false); setProgress(0); });
    return () => {
      el.removeEventListener("timeupdate", syncProgress);
    };
  }, [active, syncProgress]);

  const togglePlay = () => {
    const el = active.current;
    if (!el) return;
    if (playing) {
      el.pause();
      setPlaying(false);
    } else {
      el.play().catch(() => {});
      setPlaying(true);
    }
  };

  const toggleVersion = () => {
    const from = active.current;
    const to   = passive.current;
    if (!from || !to) return;

    const pos = from.currentTime;
    const wasPlaying = playing;

    from.pause();

    // Sync position to new version (clamp to its duration)
    to.currentTime = Math.min(pos, to.duration || 0);
    to.muted = muted;

    if (wasPlaying) {
      to.play().catch(() => {});
    }

    setVersion(v => v === "original" ? "ai" : "original");
  };

  const seek = (e) => {
    const el = active.current;
    if (!el || !el.duration) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const pct  = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
    el.currentTime = pct * el.duration;
    setProgress(pct * 100);
  };

  const toggleMute = () => {
    const el = active.current;
    if (!el) return;
    el.muted = !muted;
    setMuted(m => !m);
  };

  const fmt = (s) => {
    if (!s || isNaN(s)) return "0:00";
    const m = Math.floor(s / 60);
    const sec = Math.floor(s % 60);
    return `${m}:${sec.toString().padStart(2, "0")}`;
  };

  const hasAI = Boolean(track.ai_url);
  const accent = accentColor === "amber" ? "#d97706" : accentColor === "indigo" ? "#6366f1" : "#d97706";

  return (
    <div className="bg-white border border-ink/10 rounded-2xl overflow-hidden shadow-sm hover:shadow-md transition-shadow">

      {/* Hidden audio elements — never unmounted */}
      <audio ref={origRef} preload="auto" style={{ display: "none" }}
        onCanPlay={() => setLoaded(l => ({ ...l, original: true }))} />
      <audio ref={aiRef}   preload="auto" style={{ display: "none" }}
        onCanPlay={() => setLoaded(l => ({ ...l, ai: true }))} />

      <div className="p-4">
        {/* Track header */}
        <div className="flex items-center gap-3 mb-3">
          <button
            onClick={togglePlay}
            className="w-11 h-11 rounded-full flex items-center justify-center shrink-0 text-white transition-transform active:scale-95"
            style={{ background: accent }}
            aria-label={playing ? "Pause" : "Play"}
          >
            {playing
              ? <Pause className="w-4 h-4 fill-white" />
              : <Play  className="w-4 h-4 fill-white ml-0.5" />}
          </button>

          <div className="flex-1 min-w-0">
            <div className="font-heading font-bold text-sm truncate">{track.title}</div>
            {track.artist && (
              <div className="text-ink/50 text-xs">{track.artist}</div>
            )}
          </div>

          <button onClick={toggleMute} className="p-1.5 text-ink/30 hover:text-ink/60 transition-colors">
            {muted ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
          </button>
        </div>

        {/* Seek bar */}
        <div
          className="h-1.5 bg-ink/8 rounded-full cursor-pointer mb-2 relative overflow-hidden"
          onClick={seek}
        >
          <div
            className="absolute inset-y-0 left-0 rounded-full transition-none"
            style={{ width: `${progress}%`, background: accent }}
          />
        </div>

        {/* Time */}
        <div className="flex justify-between text-xs text-ink/40 mb-3">
          <span>{fmt(active.current?.currentTime)}</span>
          <span>{fmt(duration)}</span>
        </div>

        {/* Version toggle — only shown if track has an AI version */}
        {hasAI && (
          <div className="flex items-center gap-1 bg-ink/4 rounded-xl p-1">
            <button
              onClick={() => version !== "original" && toggleVersion()}
              className="flex-1 text-xs font-bold py-1.5 px-3 rounded-lg transition-all"
              style={version === "original"
                ? { background: "#fff", color: accent, boxShadow: "0 1px 3px rgba(0,0,0,0.08)" }
                : { color: "rgba(0,0,0,0.4)" }}
            >
              🎤 Original Voice
            </button>
            <button
              onClick={() => version !== "ai" && toggleVersion()}
              className="flex-1 text-xs font-bold py-1.5 px-3 rounded-lg transition-all"
              style={version === "ai"
                ? { background: "#fff", color: accent, boxShadow: "0 1px 3px rgba(0,0,0,0.08)" }
                : { color: "rgba(0,0,0,0.4)" }}
            >
              🤖 AI Version
            </button>
          </div>
        )}

        {/* Genre / tags */}
        {track.tags?.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mt-3">
            {track.tags.map(t => (
              <span key={t} className="text-xs px-2 py-0.5 bg-ink/5 text-ink/50 rounded-full">{t}</span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
