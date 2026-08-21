import { useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { BookOpen, ChevronLeft, RotateCcw, Layers, Sparkles } from "lucide-react";
import { STORY, START_NODE, TOTAL_NODES } from "../story/vonnsSaga";

const SAVE_KEY = "vonns_saga_v1";

// ── Palette (Melantonia: deep purple + gold) ────────────────────────────────
const C = {
  bg0: "#0d0721",
  bg1: "#1a1033",
  panel: "rgba(255,255,255,0.045)",
  panelLine: "rgba(233,180,97,0.22)",
  gold: "#E8A51E",
  goldSoft: "#f5c96b",
  purple: "#b78aff",
  ink: "#f3ecff",
  muted: "#b8a8d9",
  dim: "#8a78b5",
};

const serif = `'Georgia', 'Times New Roman', serif`;

function loadSave() {
  try {
    const raw = localStorage.getItem(SAVE_KEY);
    if (!raw) return null;
    const s = JSON.parse(raw);
    if (!s || !STORY[s.nodeId]) return null;
    return s;
  } catch {
    return null;
  }
}

function persist(s) {
  try {
    localStorage.setItem(SAVE_KEY, JSON.stringify(s));
  } catch {
    /* storage unavailable — play without saving */
  }
}

function SceneMedia({ media }) {
  if (!media) return null;
  return (
    <div className="mb-7 space-y-3" aria-label="Scene media">
      {media.image && (
        <figure>
          <img
            src={media.image.src}
            alt={media.image.alt || "Vonns Saga scene artwork"}
            className="w-full rounded-xl"
            style={{ border: `1px solid ${C.panelLine}`, maxHeight: 520, objectFit: "cover" }}
          />
          {media.image.caption && (
            <figcaption className="mt-2 text-xs text-center" style={{ color: C.muted }}>
              {media.image.caption}
            </figcaption>
          )}
        </figure>
      )}
      {media.audio && (
        <div className="rounded-xl p-3" style={{ background: C.panel, border: `1px solid ${C.panelLine}` }}>
          <div className="text-[10px] font-black uppercase tracking-[0.2em] mb-2" style={{ color: C.gold }}>
            {media.audio.label || "Resonance"}
          </div>
          <audio controls preload="none" src={media.audio.src} className="w-full" aria-label={media.audio.label || "Scene music"} />
        </div>
      )}
    </div>
  );
}

function Paragraph({ text, kind }) {
  if (kind === "poem") {
    return (
      <div className="my-1 text-center" style={{ fontSize: 17, lineHeight: 1.65, color: C.ink }}>
        {text === "" ? "\u00A0" : text}
      </div>
    );
  }
  if (kind === "interstitial") {
    const isSignal = /SIGNAL|INTENSIFY|LOVE RESONANCE|THE SIGNAL|COLLISION|ALIGNMENT|HARVEST/i.test(text);
    return (
      <div
        className="my-1"
        style={{
          fontFamily: "'Courier New', monospace",
          fontSize: 15,
          letterSpacing: isSignal ? "0.28em" : "0.12em",
          textTransform: isSignal ? "uppercase" : "none",
          color: isSignal ? C.goldSoft : C.muted,
          textAlign: "center",
        }}
      >
        {text === "" ? "\u00A0" : text}
      </div>
    );
  }
  return (
    <p className="mb-4" style={{ fontSize: 17, lineHeight: 1.8, color: C.ink }}>
      {text}
    </p>
  );
}

export default function VonnsSaga() {
  const [state, setState] = useState(() => {
    const saved = loadSave();
    return (
      saved || {
        nodeId: START_NODE,
        items: [],
        visited: [],
        strands: [],
      }
    );
  });
  const [fresh, setFresh] = useState(false); // used to animate on explicit restart
  const node = STORY[state.nodeId] || STORY[START_NODE];
  const topRef = useRef(null);

  const isEnd = node.kind === "end";

  // Progress: how many of the tapestry's scenes this Keeper has witnessed
  const progress = useMemo(() => {
    const seen = new Set([...state.visited, state.nodeId]);
    return Math.min(100, Math.round((seen.size / TOTAL_NODES) * 100));
  }, [state.visited, state.nodeId]);

  useEffect(() => {
    persist(state);
  }, [state]);

  useEffect(() => {
    if (topRef.current) topRef.current.scrollIntoView({ behavior: "auto", block: "start" });
  }, [state.nodeId, fresh]);

  const choose = (to) => {
    setState((s) => {
      const next = STORY[to];
      const items = next?.item && !s.items.includes(next.item) ? [...s.items, next.item] : s.items;
      const strands = next?.kind === "end" && !s.strands.some((x) => x.id === to)
        ? [...s.strands, { id: to, title: next.end.title, tagline: next.end.tagline, heldAt: Date.now() }]
        : s.strands;
      return { nodeId: to, items, visited: [...s.visited, s.nodeId], strands };
    });
  };

  const goBack = () => {
    setState((s) => {
      if (s.visited.length === 0) return s;
      const prev = s.visited[s.visited.length - 1];
      return { ...s, nodeId: prev, visited: s.visited.slice(0, -1) };
    });
  };

  const restart = () => {
    if (window.confirm("Begin a new life in the tapestry? This strand's path will be reset — held strands remain in the registry.")) {
      setState({ nodeId: START_NODE, items: [], visited: [], strands: state.strands });
      setFresh((f) => !f);
    }
  };

  const startOver = () => {
    setState({ nodeId: START_NODE, items: [], visited: [], strands: [] });
    setFresh((f) => !f);
  };

  const key = `${state.nodeId}-${fresh}`;

  return (
    <div
      className="min-h-screen"
      style={{
        background: `radial-gradient(1200px 800px at 15% -10%, rgba(183,138,255,0.16), transparent 60%), radial-gradient(1000px 700px at 110% 20%, rgba(232,165,30,0.10), transparent 55%), linear-gradient(160deg, ${C.bg0} 0%, ${C.bg1} 55%, ${C.bg0} 100%)`,
        color: C.ink,
      }}
    >
      {/* ── Header ─────────────────────────────────────────────────── */}
      <header
        className="sticky top-0 z-20 backdrop-blur-md"
        style={{ background: "rgba(13,7,33,0.82)", borderBottom: `1px solid ${C.panelLine}` }}
      >
        <div className="max-w-3xl mx-auto px-5 py-3 flex items-center justify-between gap-3">
          <div className="flex items-center gap-2.5 min-w-0">
            <span
              className="flex items-center justify-center rounded-lg shrink-0"
              style={{ background: C.panel, border: `1px solid ${C.panelLine}`, width: 34, height: 34 }}
            >
              <BookOpen className="w-4 h-4" style={{ color: C.gold }} />
            </span>
            <div className="min-w-0">
              <div className="font-black uppercase tracking-[0.22em] text-[11px]" style={{ color: C.gold }}>
                Vonns Saga
              </div>
              <div className="text-[11px] truncate" style={{ color: C.muted }}>
                A living history · every life is real
              </div>
            </div>
          </div>
          <div className="flex items-center gap-1.5 shrink-0">
            <Link
              to="/"
              className="px-3 py-1.5 rounded-md text-xs font-bold transition-colors hover:opacity-80"
              style={{ background: C.panel, border: `1px solid ${C.panelLine}`, color: C.muted }}
            >
              Exit
            </Link>
            {state.visited.length > 0 && (
              <button
                onClick={goBack}
                className="flex items-center gap-1 px-3 py-1.5 rounded-md text-xs font-bold transition-colors hover:opacity-80"
                style={{ background: C.panel, border: `1px solid ${C.panelLine}`, color: C.ink }}
              >
                <ChevronLeft className="w-3.5 h-3.5" /> Back
              </button>
            )}
            <button
              onClick={restart}
              className="flex items-center gap-1 px-3 py-1.5 rounded-md text-xs font-bold transition-colors hover:opacity-80"
              style={{ background: C.panel, border: `1px solid ${C.panelLine}`, color: C.ink }}
            >
              <RotateCcw className="w-3.5 h-3.5" /> New life
            </button>
          </div>
        </div>

        {/* Progress + registry strip */}
        <div className="max-w-3xl mx-auto px-5 pb-3 flex items-center gap-3">
          <div className="flex-1 h-1.5 rounded-full overflow-hidden" style={{ background: C.panel }}>
            <div
              className="h-full rounded-full transition-all duration-700"
              style={{ width: `${progress}%`, background: `linear-gradient(90deg, ${C.gold}, ${C.purple})` }}
            />
          </div>
          <div className="text-[10px] font-black uppercase tracking-widest shrink-0" style={{ color: C.dim }}>
            Tapestry {progress}%
          </div>
        </div>
      </header>

      {/* ── Strand Registry ───────────────────────────────────────── */}
      {state.strands.length > 0 && (
        <div className="max-w-3xl mx-auto px-5 pt-4">
          <div
            className="rounded-xl px-4 py-3"
            style={{ background: C.panel, border: `1px solid ${C.panelLine}` }}
          >
            <div className="flex items-center gap-2 mb-2">
              <Layers className="w-3.5 h-3.5" style={{ color: C.gold }} />
              <span className="text-[10px] font-black uppercase tracking-[0.2em]" style={{ color: C.gold }}>
                Strands held · {state.strands.length}
              </span>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {state.strands.map((st) => (
                <span
                  key={st.id}
                  className="text-[11px] font-semibold px-2 py-1 rounded-full"
                  style={{ background: "rgba(232,165,30,0.12)", border: "1px solid rgba(232,165,30,0.35)", color: C.goldSoft }}
                >
                  {st.title}
                </span>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ── Scene ──────────────────────────────────────────────────── */}
      <main
        className="max-w-3xl mx-auto px-5 py-8"
        ref={topRef}
        tabIndex={-1}
        aria-live="polite"
        aria-label="Vonns Saga scene"
      >
        <div key={key} className="vs-fade">
          {/* Part / chapter */}
          <div className="mb-5">
            <div className="text-[11px] font-black uppercase tracking-[0.25em]" style={{ color: C.purple }}>
              {node.part}
            </div>
            {node.chapter && (
              <div className="text-[11px] mt-1 uppercase tracking-[0.18em]" style={{ color: C.dim }}>
                {node.chapter}
              </div>
            )}
          </div>

          {/* Title */}
          <h1
            className="text-3xl sm:text-4xl font-bold leading-tight mb-5"
            style={{ fontFamily: serif, color: C.ink }}
          >
            {node.title}
          </h1>

          {/* Quote */}
          {node.quote && (
            <blockquote
              className="border-l-2 pl-4 mb-6 italic"
              style={{ borderColor: C.gold, color: C.goldSoft, fontSize: 15.5, lineHeight: 1.7 }}
            >
              {node.quote}
            </blockquote>
          )}

          {/* Optional artwork and music are data-driven per scene; no media is fabricated when a node has none. */}
          <SceneMedia media={node.media} />

          {/* Body */}
          <div className="mb-7">
            {node.text.map((p, i) => (
              <Paragraph key={i} text={p} kind={node.kind} />
            ))}
          </div>

          {/* Item gained */}
          {node.item && (
            <div
              className="inline-flex items-center gap-2 rounded-full px-3.5 py-1.5 mb-7 text-xs font-bold"
              style={{ background: "rgba(183,138,255,0.12)", border: "1px solid rgba(183,138,255,0.4)", color: C.purple }}
            >
              <Sparkles className="w-3.5 h-3.5" />
              Resonance held: {node.item}
            </div>
          )}

          {/* Collected items (journey-wide) */}
          {state.items.length > 0 && node.kind !== "end" && (
            <div className="mb-7">
              <div className="text-[10px] font-black uppercase tracking-[0.2em] mb-2" style={{ color: C.dim }}>
                Carried on this life
              </div>
              <div className="flex flex-wrap gap-1.5">
                {state.items.map((it) => (
                  <span
                    key={it}
                    className="text-[11px] font-semibold px-2 py-1 rounded-full"
                    style={{ background: C.panel, border: "1px solid rgba(255,255,255,0.14)", color: C.muted }}
                  >
                    {it}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Choices / strand card */}
          {!isEnd ? (
            <div className="mt-2">
              <div className="text-[10px] font-black uppercase tracking-[0.2em] mb-2.5" style={{ color: C.dim }}>
                Choose a life
              </div>
              <div className="flex flex-col gap-2.5">
                {node.choices.map((ch, i) => (
                  <button
                    key={i}
                    onClick={() => choose(ch.to)}
                    className="vs-choice group text-left rounded-xl px-5 py-4 transition-all duration-200 hover:-translate-y-0.5"
                    style={{
                      background: C.panel,
                      border: `1px solid ${C.panelLine}`,
                    }}
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <div className="font-bold" style={{ fontSize: 15.5, color: C.ink }}>
                          {ch.label}
                        </div>
                        {ch.note && (
                          <div className="mt-1" style={{ fontSize: 12.5, color: C.muted }}>
                            {ch.note}
                          </div>
                        )}
                      </div>
                      <span
                        className="shrink-0 mt-0.5 font-black"
                        style={{ color: C.gold, fontSize: 16, opacity: 0.85 }}
                      >
                        →
                      </span>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div
              className="rounded-2xl p-6 sm:p-8 text-center"
              style={{
                background: "linear-gradient(150deg, rgba(232,165,30,0.10), rgba(183,138,255,0.08))",
                border: `1.5px solid ${C.gold}`,
                boxShadow: "0 10px 40px rgba(232,165,30,0.12)",
              }}
            >
              <div className="text-[10px] font-black uppercase tracking-[0.3em] mb-3" style={{ color: C.gold }}>
                {node.end?.title ?? "Strand held"}
              </div>
              <div className="italic mb-4" style={{ fontFamily: serif, fontSize: 17, color: C.goldSoft }}>
                {node.end?.tagline}
              </div>
              <div className="text-xs mb-5" style={{ color: C.muted }}>
                This life is real — and held. In another dimension, Vonn chose differently, and that life is just as real.
              </div>
              <div className="flex flex-wrap justify-center gap-2.5">
                <button
                  onClick={restart}
                  className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-black transition-opacity hover:opacity-85"
                  style={{ background: C.gold, color: "#1a1033" }}
                >
                  <RotateCcw className="w-4 h-4" /> Hold another life
                </button>
                {state.visited.length > 0 && (
                  <button
                    onClick={goBack}
                    className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-black transition-opacity hover:opacity-85"
                    style={{ background: C.panel, border: `1px solid ${C.panelLine}`, color: C.ink }}
                  >
                    <ChevronLeft className="w-4 h-4" /> Back to the choice
                  </button>
                )}
                <button
                  onClick={startOver}
                  className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-bold transition-opacity hover:opacity-85"
                  style={{ background: "transparent", border: `1px solid ${C.panelLine}`, color: C.muted }}
                >
                  Reset the whole tapestry
                </button>
              </div>
            </div>
          )}
        </div>

        {/* ── Footer / disclaimer ──────────────────────────────────── */}
        <footer className="mt-12 pt-6" style={{ borderTop: `1px solid ${C.panelLine}` }}>
          <div className="text-[11px] leading-relaxed" style={{ color: C.dim }}>
            <span className="font-black uppercase tracking-widest" style={{ color: C.purple }}>
              Disclaimer
            </span>{" "}
            — This work is a piece of fiction. All characters, organizations, technologies, events, and
            entities — real or imagined — are used in a fictional manner. Any resemblance to actual
            persons, living or dead, or actual events, institutions, or systems is purely coincidental.
            Nothing in this series is intended to represent, depict, or comment on real individuals or
            real organizations. This is a science-fiction narrative.
          </div>
          <div className="mt-3 text-[11px]" style={{ color: C.dim }}>
            Vonns Saga · written by Nam Oshun · built into the M.O.R.E. tapestry · © NAM Oshun Edutainment LLC
          </div>
        </footer>
      </main>

      <style>{`
        .vs-fade { animation: vsFade 0.55s ease both; }
        @keyframes vsFade {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .vs-choice:hover { border-color: ${C.gold} !important; background: rgba(232,165,30,0.08) !important; }
        .vs-choice:hover span { opacity: 1 !important; }
        @media (prefers-reduced-motion: reduce) {
          .vs-fade { animation: none; }
          .vs-choice { transition: none !important; }
        }
      `}</style>
    </div>
  );
}
