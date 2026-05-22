import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { api } from "../lib/api";
import { toast } from "sonner";
import { CheckCircle, ExternalLink, Music, ArrowRight, Loader, Send, Heart } from "lucide-react";
import { WAI_LOGO, BRAND } from "../lib/brand";
import BugReportModal from "../components/BugReportModal";

// Gateway steps in order — must match backend GATEWAY_STEPS
const STEPS = [
  {
    id: "save_playlist",
    icon: "💾",
    label: "Save the Playlist",
    desc: "Open the playlist on Spotify and click the heart icon to save it to your library.",
    urlKey: "playlist_spotify_url",
    urlLabel: "Open Playlist on Spotify",
  },
  {
    id: "follow_playlist",
    icon: "❤️",
    label: "Follow the Playlist",
    desc: "On the playlist page, click 'Follow' so you stay connected as it grows.",
    urlKey: "playlist_spotify_url",
    urlLabel: "Open Playlist on Spotify",
  },
  {
    id: "add_song",
    icon: "➕",
    label: "Add the Required Song",
    desc: "Open this specific song on Spotify and add it to your library or one of your playlists.",
    urlKey: "target_song_url",
    urlLabel: "Open Required Song on Spotify",
    nameKey: "target_song_name",
  },
  {
    id: "follow_profile",
    icon: "🎤",
    label: "Follow the Curator on Spotify",
    desc: "Open the curator's Spotify profile and click Follow.",
    urlKey: "curator_spotify_url",
    urlLabel: "Open Curator's Spotify Profile",
  },
  {
    id: "share",
    icon: "📤",
    label: "Share the Playlist",
    desc: "Share the playlist link on Instagram, Twitter, Facebook, or TikTok — then paste your post URL below.",
    urlKey: "playlist_spotify_url",
    urlLabel: "Copy Playlist Link",
    needsShareUrl: true,
  },
];

const GENRES = [
  "Hip-Hop / Rap", "R&B / Soul", "Afrobeats", "Gospel / Christian",
  "Jazz", "Blues", "Neo Soul", "Trap", "Drill", "Reggae / Dancehall",
  "Latin", "Pop", "Indie", "Electronic", "Other",
];

export default function PlaylistSubmit() {
  const { slug } = useParams();
  const [phase, setPhase] = useState("loading");
  const [gateways, setGateways] = useState([]);
  const [selectedGateway, setSelectedGateway] = useState(null);
  const [submissionId, setSubmissionId] = useState(null);
  const [stepsCompleted, setStepsCompleted] = useState({});
  const [allComplete, setAllComplete] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [shareUrl, setShareUrl] = useState("");
  const [reviewNote, setReviewNote] = useState(null);
  const [form, setForm] = useState({
    artist_name: "",
    artist_email: "",
    artist_spotify_url: "",
    song_title: "",
    song_spotify_url: "",
    genre: "",
  });

  useEffect(() => {
    (async () => {
      try {
        const { data } = await api.get(`/api/playlist/gateways/${slug}`);
        const open = (data.gateways || []);
        setGateways(open);
        if (open.length === 0) setPhase("closed");
        else if (open.length === 1) { setSelectedGateway(open[0]); setPhase("form"); }
        else setPhase("choose");
      } catch {
        setPhase("error");
      }
    })();
  }, [slug]);

  const selectGateway = (gw) => { setSelectedGateway(gw); setPhase("form"); };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const { data } = await api.post("/api/playlist/submit", {
        gateway_id: selectedGateway._id,
        ...form,
      });
      setSubmissionId(data.submission_id);
      setStepsCompleted(Object.fromEntries(STEPS.map((s) => [s.id, false])));
      setPhase("steps");
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Submission failed — try again.");
    } finally {
      setSubmitting(false);
    }
  };

  const markDone = async (stepId) => {
    if (stepId === "share" && !shareUrl.trim()) {
      toast.error("Paste your share post URL first, then mark this step done.");
      return;
    }
    try {
      const { data } = await api.post("/api/playlist/complete-step", {
        submission_id: submissionId,
        step: stepId,
        share_url: stepId === "share" ? shareUrl : "",
      });
      setStepsCompleted(data.steps_completed);
      setAllComplete(data.all_steps_complete);
      if (data.all_steps_complete) {
        toast.success("All steps done! Nova will review your submission.");
        setPhase("done");
      }
    } catch {
      toast.error("Couldn't save that step — try again.");
    }
  };

  const completedCount = Object.values(stepsCompleted).filter(Boolean).length;

  return (
    <div className="min-h-screen bg-bone text-ink">
      {/* Nav */}
      <header className="border-b border-ink/10 bg-bone sticky top-0 z-40">
        <div className="max-w-3xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2">
            <img src={WAI_LOGO} alt="W.A.I." className="w-9 h-9 object-contain" style={{ mixBlendMode: "multiply" }} />
            <span className="font-heading font-bold text-sm hidden sm:block">{BRAND.name}</span>
          </Link>
          <div className="flex items-center gap-3">
            <Link to={`/creator/${slug}`} className="text-xs font-bold text-emerald-700 border border-emerald-300 px-3 py-1.5 rounded-full hover:border-emerald-500 transition-colors">
              ← Creator Profile
            </Link>
          </div>
        </div>
      </header>

      <div className="max-w-xl mx-auto px-6 py-12">

        {/* ── Loading ─────────────────────────────── */}
        {phase === "loading" && (
          <div className="flex items-center justify-center py-24 gap-3 text-ink/40">
            <Loader className="w-5 h-5 animate-spin" />
            <span>Loading submission form…</span>
          </div>
        )}

        {/* ── Error ───────────────────────────────── */}
        {phase === "error" && (
          <div className="text-center py-20">
            <div className="text-5xl mb-4">😔</div>
            <h2 className="font-heading text-2xl font-bold mb-2">Couldn't load gateways</h2>
            <p className="text-ink/60 mb-6">Check the URL or try again in a moment.</p>
            <Link to={`/creator/${slug}`} className="inline-flex items-center gap-2 bg-ink text-white font-bold px-6 py-3 rounded-xl">Back to Profile</Link>
          </div>
        )}

        {/* ── Closed ──────────────────────────────── */}
        {phase === "closed" && (
          <div className="text-center py-20">
            <div className="text-5xl mb-4">🎵</div>
            <h2 className="font-heading text-2xl font-bold mb-2">No Open Gateways Right Now</h2>
            <p className="text-ink/60 mb-2">All playlist spots are currently full or paused.</p>
            <p className="text-ink/50 text-sm mb-6">Check back soon — spots open up as playlists cycle.</p>
            <Link to={`/creator/${slug}`} className="inline-flex items-center gap-2 border-2 border-ink text-ink font-bold px-6 py-3 rounded-xl hover:bg-ink hover:text-white transition-all">
              Back to Profile
            </Link>
          </div>
        )}

        {/* ── Choose gateway ──────────────────────── */}
        {phase === "choose" && (
          <div>
            <div className="text-emerald-700 text-xs uppercase tracking-widest font-bold mb-2">Choose a Playlist</div>
            <h1 className="font-heading text-3xl font-extrabold mb-2">Submit Your Song</h1>
            <p className="text-ink/60 text-sm mb-8">Multiple playlists are open. Choose the one that fits your sound.</p>
            <div className="space-y-4">
              {gateways.map((gw) => (
                <button
                  key={gw._id}
                  onClick={() => selectGateway(gw)}
                  className="w-full text-left p-6 bg-white border-2 border-ink/10 hover:border-emerald-400 rounded-2xl transition-all group"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="font-heading font-extrabold text-lg">{gw.playlist_name}</div>
                      <div className="text-ink/50 text-sm mt-1">{gw.filled_slots} of {gw.max_slots} spots filled · {5} steps required</div>
                      {gw.notes && <div className="text-ink/60 text-xs mt-2 italic">{gw.notes}</div>}
                    </div>
                    <ArrowRight className="w-5 h-5 text-ink/30 group-hover:text-emerald-600 transition-colors shrink-0" />
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* ── Submission form ─────────────────────── */}
        {phase === "form" && selectedGateway && (
          <div>
            <div className="text-emerald-700 text-xs uppercase tracking-widest font-bold mb-2">Free Placement</div>
            <h1 className="font-heading text-3xl font-extrabold mb-1">Submit Your Song</h1>
            <p className="text-ink/60 text-sm mb-1">Playlist: <strong className="text-ink">{selectedGateway.playlist_name}</strong></p>
            <p className="text-ink/50 text-xs mb-6">{selectedGateway.filled_slots} of {selectedGateway.max_slots} spots filled · Complete all 5 gateway steps after submitting</p>

            {selectedGateway.notes && (
              <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-4 mb-6 text-sm text-emerald-800">
                <strong>Note from Nova:</strong> {selectedGateway.notes}
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-ink/60 mb-1.5 uppercase tracking-wider">Artist Name *</label>
                  <input required value={form.artist_name} onChange={(e) => setForm({ ...form, artist_name: e.target.value })}
                    placeholder="Your artist name"
                    className="w-full px-3 py-2.5 border border-ink/20 rounded-lg text-sm bg-white focus:outline-none focus:border-emerald-500" />
                </div>
                <div>
                  <label className="block text-xs font-bold text-ink/60 mb-1.5 uppercase tracking-wider">Email *</label>
                  <input required type="email" value={form.artist_email} onChange={(e) => setForm({ ...form, artist_email: e.target.value })}
                    placeholder="you@email.com"
                    className="w-full px-3 py-2.5 border border-ink/20 rounded-lg text-sm bg-white focus:outline-none focus:border-emerald-500" />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-ink/60 mb-1.5 uppercase tracking-wider">Your Spotify Artist Profile Link *</label>
                <input required value={form.artist_spotify_url} onChange={(e) => setForm({ ...form, artist_spotify_url: e.target.value })}
                  placeholder="https://open.spotify.com/artist/..."
                  className="w-full px-3 py-2.5 border border-ink/20 rounded-lg text-sm bg-white focus:outline-none focus:border-emerald-500" />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-ink/60 mb-1.5 uppercase tracking-wider">Song Title *</label>
                  <input required value={form.song_title} onChange={(e) => setForm({ ...form, song_title: e.target.value })}
                    placeholder="Track name"
                    className="w-full px-3 py-2.5 border border-ink/20 rounded-lg text-sm bg-white focus:outline-none focus:border-emerald-500" />
                </div>
                <div>
                  <label className="block text-xs font-bold text-ink/60 mb-1.5 uppercase tracking-wider">Genre *</label>
                  <select required value={form.genre} onChange={(e) => setForm({ ...form, genre: e.target.value })}
                    className="w-full px-3 py-2.5 border border-ink/20 rounded-lg text-sm bg-white focus:outline-none focus:border-emerald-500">
                    <option value="">Select genre…</option>
                    {GENRES.map((g) => <option key={g}>{g}</option>)}
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-ink/60 mb-1.5 uppercase tracking-wider">Spotify Song Link *</label>
                <input required value={form.song_spotify_url} onChange={(e) => setForm({ ...form, song_spotify_url: e.target.value })}
                  placeholder="https://open.spotify.com/track/..."
                  className="w-full px-3 py-2.5 border border-ink/20 rounded-lg text-sm bg-white focus:outline-none focus:border-emerald-500" />
                <p className="text-xs text-ink/40 mt-1">Right-click your song on Spotify → Share → Copy link</p>
              </div>

              <div className="bg-ink/5 border border-ink/10 rounded-xl p-4 text-xs text-ink/60 leading-relaxed">
                After submitting, you'll complete <strong>5 gateway steps</strong> — save playlist, follow playlist, add a required song, follow Nova on Spotify, and share the playlist. All 5 must be done for your song to be reviewed.
              </div>

              <button type="submit" disabled={submitting}
                className="w-full py-3 bg-emerald-700 hover:bg-emerald-600 text-white font-bold rounded-xl flex items-center justify-center gap-2 transition-colors disabled:opacity-50">
                {submitting ? <><Loader className="w-4 h-4 animate-spin" /> Submitting…</> : <><Send className="w-4 h-4" /> Submit Song — Continue to Gateway Steps</>}
              </button>
            </form>
          </div>
        )}

        {/* ── Gateway steps ───────────────────────── */}
        {phase === "steps" && selectedGateway && (
          <div>
            <div className="text-emerald-700 text-xs uppercase tracking-widest font-bold mb-2">Gateway Steps</div>
            <h1 className="font-heading text-3xl font-extrabold mb-2">Complete All 5 Steps</h1>
            <p className="text-ink/60 text-sm mb-2">
              Do each step on Spotify, then click "I Did This" to mark it complete.
              Nova reviews your song only after all 5 are done.
            </p>

            {/* Progress bar */}
            <div className="mb-8">
              <div className="flex items-center justify-between text-xs text-ink/50 mb-1.5">
                <span>{completedCount} of 5 steps complete</span>
                <span>{Math.round((completedCount / 5) * 100)}%</span>
              </div>
              <div className="w-full h-2 bg-ink/10 rounded-full overflow-hidden">
                <div
                  className="h-full bg-emerald-500 rounded-full transition-all duration-500"
                  style={{ width: `${(completedCount / 5) * 100}%` }}
                />
              </div>
            </div>

            <div className="space-y-4">
              {STEPS.map((step, idx) => {
                const done = stepsCompleted[step.id];
                const url = selectedGateway[step.urlKey];
                const songName = step.nameKey ? selectedGateway[step.nameKey] : null;

                return (
                  <div
                    key={step.id}
                    className={`border-2 rounded-2xl p-5 transition-all ${done ? "border-emerald-300 bg-emerald-50" : "border-ink/10 bg-white"}`}
                  >
                    <div className="flex items-start gap-4">
                      <div className={`w-9 h-9 rounded-full flex items-center justify-center shrink-0 text-sm font-black ${done ? "bg-emerald-500 text-white" : "bg-ink/10 text-ink/60"}`}>
                        {done ? <CheckCircle className="w-5 h-5" /> : idx + 1}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className={`font-bold text-base ${done ? "text-emerald-800 line-through opacity-60" : "text-ink"}`}>{step.label}</div>
                        <p className="text-ink/60 text-sm mt-0.5 leading-relaxed">{step.desc}</p>
                        {songName && (
                          <p className="text-xs text-emerald-700 font-bold mt-1">Required song: {songName}</p>
                        )}

                        {!done && (
                          <div className="mt-3 space-y-2">
                            {url && (
                              <a href={url} target="_blank" rel="noopener noreferrer"
                                className="inline-flex items-center gap-1.5 text-xs font-bold text-emerald-700 hover:text-emerald-600 border border-emerald-300 px-3 py-1.5 rounded-lg transition-colors">
                                <ExternalLink className="w-3 h-3" /> {step.urlLabel}
                              </a>
                            )}
                            {step.needsShareUrl && (
                              <div className="mt-2">
                                <input
                                  value={shareUrl}
                                  onChange={(e) => setShareUrl(e.target.value)}
                                  placeholder="Paste your share post URL here (Instagram, Twitter, etc.)"
                                  className="w-full px-3 py-2 border border-ink/20 rounded-lg text-xs bg-white focus:outline-none focus:border-emerald-500"
                                />
                              </div>
                            )}
                            <button
                              onClick={() => markDone(step.id)}
                              className="inline-flex items-center gap-1.5 text-xs font-bold bg-emerald-700 hover:bg-emerald-600 text-white px-3 py-1.5 rounded-lg transition-colors"
                            >
                              <CheckCircle className="w-3 h-3" /> I Did This
                            </button>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* ── Done ────────────────────────────────── */}
        {phase === "done" && (
          <div className="text-center py-12">
            <div className="text-7xl mb-6">🎶</div>
            <div className="text-emerald-700 text-xs uppercase tracking-widest font-bold mb-3">You're in the queue</div>
            <h1 className="font-heading text-4xl font-extrabold mb-4">All 5 Steps Complete.</h1>
            <p className="text-ink/70 text-base leading-relaxed mb-2 max-w-sm mx-auto">
              Nova will review your submission and reach out if your song makes it onto the playlist.
            </p>
            <p className="text-ink/40 text-sm mb-8">Keep streaming the playlist — it helps your chances.</p>
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              {selectedGateway?.playlist_spotify_url && (
                <a href={selectedGateway.playlist_spotify_url} target="_blank" rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 bg-emerald-700 hover:bg-emerald-600 text-white font-bold px-6 py-3 rounded-xl transition-colors">
                  <Music className="w-4 h-4" /> Stream the Playlist
                </a>
              )}
              <Link to={`/creator/${slug}`}
                className="inline-flex items-center gap-2 border-2 border-ink text-ink font-bold px-6 py-3 rounded-xl hover:bg-ink hover:text-white transition-all">
                Back to Profile
              </Link>
            </div>
          </div>
        )}

      </div>

      <BugReportModal />
    </div>
  );
}
