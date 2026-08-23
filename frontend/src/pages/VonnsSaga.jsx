import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { BookOpen, ChevronLeft, RotateCcw, Layers, Sparkles, Volume2, VolumeX, Brain, Shuffle, Square, Music2, Music, Film, Ticket, Loader2, ShieldCheck } from "lucide-react";
import { STORY, START_NODE, TOTAL_NODES } from "../story/vonnsSaga";
import { api, getToken } from "../lib/api";
import { toast } from "sonner";
import { useAuth } from "../lib/auth";
import { tierRank } from "../lib/tiers";
import VonnsSagaAdmin from "../components/VonnsSagaAdmin";

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

const BANDCAMP_TRACKS = {
  opening: {
    key: "opening",
    label: "Opening resonance · AM I Dreaming",
    artist: "VONN",
    href: "https://vonnsangs.bandcamp.com/track/am-i-dreaming",
    src: "https://bandcamp.com/EmbeddedPlayer/track=792480361/size=large/bgcol=ffffff/linkcol=0687f5/tracklist=false/artwork=small/transparent=true/",
    height: 120,
  },
  lexington: {
    key: "lexington",
    label: "Lexington strand · My Ole Kentucky Roots",
    artist: "VONN",
    href: "https://vonnsangs.bandcamp.com/track/my-ole-kentucky-roots",
    src: "https://bandcamp.com/EmbeddedPlayer/track=2837268270/size=large/bgcol=ffffff/linkcol=0687f5/tracklist=false/transparent=true/",
    height: 442,
  },
};

function BandcampTrack({ track }) {
  return (
    <div className="rounded-xl overflow-hidden" style={{ background: "#fff", border: `1px solid ${C.panelLine}` }}>
      <iframe
        title={track.label}
        style={{ border: 0, width: "100%", height: track.height }}
        src={track.src}
        seamless
      />
      <a href={track.href} target="_blank" rel="noreferrer" className="block px-3 pb-2 text-xs" style={{ color: "#0687f5" }}>
        {track.label} by {track.artist}
      </a>
    </div>
  );
}

function SagaMusic({ nodeId, isLexington, isRandomPage, randomTrack, onRandom }) {
  const opening = nodeId === START_NODE;
  const track = opening
    ? BANDCAMP_TRACKS.opening
    : isLexington
      ? BANDCAMP_TRACKS.lexington
      : isRandomPage
        ? randomTrack
        : null;
  const label = opening ? "Opening track" : isLexington ? "Lexington strand" : isRandomPage ? "Random strand" : "Music appears at selected story moments";
  return (
    <section className="mb-7 rounded-2xl p-4" style={{ background: "rgba(255,255,255,0.035)", border: `1px solid ${C.panelLine}` }} aria-label="Vonn music">
      <div className="flex items-center justify-between gap-3 mb-3">
        <div className="flex items-center gap-2">
          <Music2 className="w-4 h-4" style={{ color: C.gold }} />
          <div>
            <div className="text-[10px] font-black uppercase tracking-[0.2em]" style={{ color: C.gold }}>Vonn's music</div>
            <div className="text-xs" style={{ color: C.muted }}>{label}</div>
          </div>
        </div>
        {isRandomPage && (
          <button type="button" onClick={onRandom} className="flex items-center gap-1.5 rounded-lg px-3 py-2 text-xs font-bold" style={{ background: C.panel, border: `1px solid ${C.panelLine}`, color: C.ink }}>
            <Shuffle className="w-3.5 h-3.5" /> Replay opening track
          </button>
        )}
      </div>
      {track ? <BandcampTrack track={track} /> : (
        <p className="text-xs" style={{ color: C.muted }}>The storefront track is held for the opening, Lexington, and one randomly selected strand on this life.</p>
      )}
      <p className="mt-2 text-[11px]" style={{ color: C.dim }}>Bandcamp controls are supplied by VONN's storefront. Site-uploaded tracks use the separate 33-second preview rule.</p>
    </section>
  );
}

function PreviewAudio({ fileUrl, label }) {
  // Media files require the JWT header — fetch as blob, then play (same
  // pattern as the Media Store). Audio is server-capped to 33s until bought.
  const [src, setSrc] = useState(null);
  const [loading, setLoading] = useState(false);
  useEffect(() => {
    let alive = true;
    if (!fileUrl) return;
    setLoading(true);
    api.get(fileUrl, { responseType: "blob" })
      .then((r) => { if (alive) setSrc(URL.createObjectURL(r.data)); })
      .catch(() => { if (alive) setSrc(null); })
      .finally(() => { if (alive) setLoading(false); });
    return () => { alive = false; };
  }, [fileUrl]);
  if (loading) {
    return <div className="text-[11px]" style={{ color: C.dim }}>Loading preview…</div>;
  }
  if (!src) {
    return <div className="text-[11px]" style={{ color: C.danger }}>Preview unavailable</div>;
  }
  return <audio controls preload="none" src={src} className="w-full" aria-label={label || "Track preview"} />;
}

function PlatformTracks({ tracks, purchasedIds, onBuy }) {
  if (!tracks?.length) return null;
  return (
    <div className="mt-10">
      <div className="flex items-center gap-2 mb-3">
        <Music className="w-4 h-4" style={{ color: C.gold }} />
        <div className="text-[10px] font-black uppercase tracking-[0.22em]" style={{ color: C.gold }}>
          The Music of Vonn
        </div>
      </div>
      <div className="space-y-3">
        {tracks.map((t) => {
          const bought = purchasedIds.includes(t.id);
          return (
            <div key={t.id} className="rounded-xl p-3" style={{ background: C.panel, border: `1px solid ${C.panelLine}` }}>
              <div className="flex items-center justify-between gap-3 mb-2">
                <div className="min-w-0">
                  <div className="text-sm font-bold truncate" style={{ color: C.ink }}>{t.title}</div>
                  <div className="text-[10px] uppercase tracking-widest" style={{ color: C.dim }}>
                    {bought ? "Owned — full track" : `33s preview · $${(t.price_cents / 100).toFixed(2)}`}
                  </div>
                </div>
                {!bought && (
                  <button
                    onClick={() => onBuy(t.id)}
                    className="shrink-0 px-3 py-1.5 rounded-lg text-xs font-black"
                    style={{ background: C.gold, color: "#1a1033" }}
                  >
                    Buy — ${(t.price_cents / 100).toFixed(2)}
                  </button>
                )}
              </div>
              <PreviewAudio fileUrl={t.file_url} label={t.title} />
            </div>
          );
        })}
      </div>
    </div>
  );
}

function SagaVideos({ videos }) {
  if (!videos?.length) return null;
  return (
    <div className="mt-10">
      <div className="flex items-center gap-2 mb-3">
        <Film className="w-4 h-4" style={{ color: C.purple }} />
        <div className="text-[10px] font-black uppercase tracking-[0.22em]" style={{ color: C.purple }}>
          Scenes in Motion
        </div>
        <span className="flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full" style={{ background: "rgba(74,222,128,0.10)", border: "1px solid rgba(74,222,128,0.35)", color: "#86efac" }}>
          <ShieldCheck className="w-3 h-3" /> AI-assisted production
        </span>
      </div>
      <div className="space-y-4">
        {videos.map((v) => (
          <div key={v.id} className="rounded-xl overflow-hidden" style={{ background: C.panel, border: `1px solid ${C.panelLine}` }}>
            <div className="flex items-center justify-between gap-3 px-3 py-2">
              <div className="text-sm font-bold truncate" style={{ color: C.ink }}>{v.title}</div>
              {v.status === "rendering" && (
                <span className="flex items-center gap-1 text-[10px] font-bold uppercase tracking-widest" style={{ color: C.gold }}>
                  <Loader2 className="w-3 h-3" style={{ animation: "spin 1s linear infinite" }} /> Rendering
                </span>
              )}
              {v.status === "render_failed" && (
                <span className="text-[10px] font-bold uppercase tracking-widest" style={{ color: C.danger }}>
                  Render failed
                </span>
              )}
            </div>
            {v.status === "ready" && v.file_url && (
              <video controls preload="none" className="w-full" src={v.file_url} style={{ maxHeight: 420, background: "#000" }} />
            )}
            {v.status === "render_failed" && v.error && (
              <div className="px-3 pb-3 text-[11px]" style={{ color: C.dim }}>{v.error}</div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function ConcertSection({ concerts, user, purchasedIds, onBuy }) {
  if (!concerts?.length) return null;
  const concert = concerts[0];
  const isStaff = ["admin", "executive_admin"].includes(user?.role);
  const tier = user?.feature_tier || "free";
  const isMember = isStaff || tierRank(tier) >= tierRank("member");
  const owned = purchasedIds.includes(concert.id);
  return (
    <div className="mt-10">
      <div
        className="rounded-2xl p-5 sm:p-6"
        style={{ background: "linear-gradient(150deg, rgba(232,165,30,0.12), rgba(183,138,255,0.10))", border: `1.5px solid ${C.gold}` }}
      >
        <div className="flex items-center gap-2 mb-2">
          <Ticket className="w-4 h-4" style={{ color: C.gold }} />
          <div className="text-[10px] font-black uppercase tracking-[0.22em]" style={{ color: C.gold }}>
            Vonn Live — Virtual Concert
          </div>
        </div>
        <div className="font-heading font-bold text-lg mb-1" style={{ color: C.ink }}>{concert.title}</div>
        <div className="text-xs mb-4 leading-relaxed" style={{ color: C.muted }}>{concert.description}</div>
        <div className="flex flex-wrap items-center gap-3">
          {owned ? (
            <span className="text-xs font-black uppercase tracking-widest" style={{ color: "#86efac" }}>
              ✓ Ticket owned — enjoy the show
            </span>
          ) : isMember ? (
            <button
              onClick={() => onBuy(concert.id)}
              className="px-4 py-2 rounded-lg text-sm font-black"
              style={{ background: C.gold, color: "#1a1033" }}
            >
              Get your ticket — ${(concert.price_cents / 100).toFixed(2)}
            </button>
          ) : (
            <div className="text-xs" style={{ color: C.goldSoft }}>
              {user ? "Members-only experience — join a membership to unlock this concert." : "Sign in — this virtual concert is members-only."}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function ReadingControls({ text, aiBusy, onBrowserRead, onAiRead, onStop, isReading }) {
  return (
    <section className="mb-7 rounded-2xl p-4" style={{ background: "rgba(183,138,255,0.07)", border: "1px solid rgba(183,138,255,0.28)" }} aria-label="Reading controls">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Brain className="w-4 h-4" style={{ color: C.purple }} />
          <div><div className="text-[10px] font-black uppercase tracking-[0.2em]" style={{ color: C.purple }}>Read this strand</div><div className="text-xs" style={{ color: C.muted }}>Optional. Nothing starts without your click.</div></div>
        </div>
        <div className="flex flex-wrap gap-2">
          <button type="button" onClick={onBrowserRead} className="flex items-center gap-1.5 rounded-lg px-3 py-2 text-xs font-bold" style={{ background: C.panel, border: `1px solid ${C.panelLine}`, color: C.ink }}>
            {isReading ? <VolumeX className="w-3.5 h-3.5" /> : <Volume2 className="w-3.5 h-3.5" />} Browser voice
          </button>
          <button type="button" onClick={onAiRead} disabled={aiBusy} className="flex items-center gap-1.5 rounded-lg px-3 py-2 text-xs font-bold" style={{ background: C.gold, color: "#1a1033", opacity: aiBusy ? 0.6 : 1 }}>
            <Brain className="w-3.5 h-3.5" /> {aiBusy ? "Preparing…" : "AI reading mode"}
          </button>
          {isReading && <button type="button" onClick={onStop} className="flex items-center gap-1.5 rounded-lg px-3 py-2 text-xs font-bold" style={{ background: "rgba(220,38,38,0.14)", border: "1px solid rgba(220,38,38,0.35)", color: "#ff9b9b" }}><Square className="w-3 h-3" /> Stop</button>}
        </div>
      </div>
      <p className="mt-2 text-[11px]" style={{ color: C.dim }}>{text.length.toLocaleString()} characters · Browser voice is free; signed-in readers can use the existing server TTS route for AI reading mode.</p>
    </section>
  );
}

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

function SceneMedia({ media, liveImages }) {
  // Live images are the owner's real scene artwork (GridFS) uploaded via the
  // admin panel; they take precedence over any static story-node media.
  const images = (liveImages || []).map((im) => ({
    src: im.file_url,
    caption: im.caption,
    alt: `Vonns Saga scene artwork — ${im.node_id}`,
  }));
  if (media?.image) images.push(media.image);
  if (!images.length && !media?.audio) return null;
  return (
    <div className="mb-7 space-y-3" aria-label="Scene media">
      {images.map((img, i) => (
        <figure key={i}>
          <img
            src={img.src}
            alt={img.alt || "Vonns Saga scene artwork"}
            className="w-full rounded-xl"
            style={{ border: `1px solid ${C.panelLine}`, maxHeight: 520, objectFit: "cover" }}
          />
          {img.caption && (
            <figcaption className="mt-2 text-xs text-center" style={{ color: C.muted }}>
              {img.caption}
            </figcaption>
          )}
        </figure>
      ))}
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
  // The opening track is the supplied random-page resonance. The Lexington
  // track is reserved for scenes explicitly located in Lexington.
  const [randomTrack, setRandomTrack] = useState(BANDCAMP_TRACKS.opening);
  const [randomMusicNode] = useState(() => {
    const candidates = Object.entries(STORY)
      .filter(([id, candidate]) => id !== START_NODE && candidate.kind !== "end" && candidate.location !== "lexington")
      .map(([id]) => id);
    return candidates.length ? candidates[Math.floor(Math.random() * candidates.length)] : null;
  });
  const [aiBusy, setAiBusy] = useState(false);
  const [isReading, setIsReading] = useState(false);
  const aiAudioRef = useRef(null);

  // ── Live saga assets (real GridFS-backed media) ────────────────────────
  const { user } = useAuth();
  const [sagaImages, setSagaImages] = useState([]);
  const [tracks, setTracks] = useState([]);
  const [videos, setVideos] = useState([]);
  const [concerts, setConcerts] = useState([]);
  const [purchasedIds, setPurchasedIds] = useState([]);

  const loadSagaAssets = useCallback(() => {
    api.get("/saga/images").then((r) => setSagaImages(r.data?.images || [])).catch(() => {});
    api.get("/saga/tracks").then((r) => setTracks(r.data?.tracks || [])).catch(() => {});
    api.get("/saga/videos").then((r) => setVideos(r.data?.videos || [])).catch(() => {});
    api.get("/saga/concerts").then((r) => setConcerts(r.data?.concerts || [])).catch(() => {});
    api.get("/media/purchases").then((r) => {
      const ids = (r.data || []).map((p) => p.product_id);
      setPurchasedIds(ids);
    }).catch(() => {});
  }, []);

  useEffect(() => {
    loadSagaAssets();
  }, [loadSagaAssets]);

  const buyMedia = useCallback(async (productId, endpoint) => {
    try {
      const { data } = await api.post(endpoint);
      if (data?.url) {
        window.location.href = data.url;
      } else if (data?.already_purchased) {
        toast.success("You already own this — enjoy!");
        loadSagaAssets();
      } else {
        toast.success("Unlocked!");
        loadSagaAssets();
      }
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Could not start checkout.");
    }
  }, [loadSagaAssets]);

  const node = STORY[state.nodeId] || STORY[START_NODE];
  const isEnd = node.kind === "end";
  const sceneText = useMemo(() => [node.title, ...(node.text || [])].join("\n\n"), [node]);
  const isLexington = node.location === "lexington";
  const isRandomMusicPage = state.nodeId === randomMusicNode && !isLexington && !isEnd;

  // Progress: how many of the tapestry's scenes this Keeper has witnessed
  const progress = useMemo(() => {
    const seen = new Set([...state.visited, state.nodeId]);
    return Math.min(100, Math.round((seen.size / TOTAL_NODES) * 100));
  }, [state.visited, state.nodeId]);

  useEffect(() => {
    persist(state);
  }, [state]);

  useEffect(() => {
    window.speechSynthesis?.cancel();
    setIsReading(false);
    if (aiAudioRef.current) {
      aiAudioRef.current.pause();
      aiAudioRef.current = null;
    }
  }, [state.nodeId]);

  useEffect(() => () => {
    window.speechSynthesis?.cancel();
    if (aiAudioRef.current) aiAudioRef.current.pause();
  }, []);

  const stopReading = () => {
    window.speechSynthesis?.cancel();
    if (aiAudioRef.current) {
      aiAudioRef.current.pause();
      aiAudioRef.current = null;
    }
    setIsReading(false);
  };

  const readBrowser = () => {
    if (!window.speechSynthesis) return;
    if (isReading) return stopReading();
    const utterance = new SpeechSynthesisUtterance(sceneText);
    utterance.rate = 0.94;
    utterance.pitch = 0.92;
    utterance.onend = () => setIsReading(false);
    utterance.onerror = () => setIsReading(false);
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utterance);
    setIsReading(true);
  };

  const readWithAi = async () => {
    // The existing server TTS route is authenticated. Do not send a public
    // reader into the API interceptor's login redirect; browser voice remains
    // the immediate no-key option.
    if (!getToken()) {
      readBrowser();
      return;
    }
    setAiBusy(true);
    try {
      const response = await api.post("/ai/sage/tts", { text: sceneText.slice(0, 4000), session_id: `vonns-${state.nodeId}` }, { responseType: "blob" });
      const blobUrl = URL.createObjectURL(response.data);
      const audio = new Audio(blobUrl);
      aiAudioRef.current = audio;
      audio.onended = () => { URL.revokeObjectURL(blobUrl); aiAudioRef.current = null; setIsReading(false); };
      audio.onerror = () => { URL.revokeObjectURL(blobUrl); aiAudioRef.current = null; readBrowser(); };
      await audio.play();
      setIsReading(true);
    } catch {
      // The authenticated provider route may be unavailable to public readers;
      // browser speech remains a real no-key fallback, never a fake AI result.
      readBrowser();
    } finally {
      setAiBusy(false);
    }
  };

  const chooseRandomTrack = () => {
    setRandomTrack(BANDCAMP_TRACKS.opening);
  };

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

          {/* Your supplied VONN tracks are embedded in their story contexts. */}
          <SagaMusic nodeId={state.nodeId} isLexington={isLexington} isRandomPage={isRandomMusicPage} randomTrack={randomTrack} onRandom={chooseRandomTrack} />
          <ReadingControls text={sceneText} aiBusy={aiBusy} onBrowserRead={readBrowser} onAiRead={readWithAi} onStop={stopReading} isReading={isReading} />

          {/* Optional artwork and uploaded scene media remain data-driven; no media is fabricated. */}
          <SceneMedia
            media={node.media}
            liveImages={sagaImages.filter((i) => i.node_id === state.nodeId)}
          />

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

        {/* ── The funnel: music → video → concert ──────────────────── */}
        <ConcertSection concerts={concerts} user={user} purchasedIds={purchasedIds} onBuy={(id) => buyMedia(id, `/saga/concerts/${id}/checkout`)} />
        <PlatformTracks tracks={tracks} purchasedIds={purchasedIds} onBuy={(id) => buyMedia(id, `/media/products/${id}/checkout`)} />
        <SagaVideos videos={videos} />

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

          {/* Admin panel — tracks, images, videos */}
          <VonnsSagaAdmin nodeId={state.nodeId} />
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
