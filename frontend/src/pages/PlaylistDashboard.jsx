import { useState, useEffect } from "react";
import { api } from "../lib/api";
import { toast } from "sonner";
import { CheckCircle, XCircle, Clock, Plus, ExternalLink, ChevronDown, ChevronUp, Loader, RefreshCw } from "lucide-react";

const STEP_LABELS = {
  save_playlist: "Save Playlist",
  follow_playlist: "Follow Playlist",
  add_song: "Add Required Song",
  follow_profile: "Follow on Spotify",
  share: "Share",
};

const STATUS_STYLES = {
  pending: { label: "Pending", chip: "bg-amber-100 text-amber-700 border-amber-300" },
  approved: { label: "Approved ✓", chip: "bg-emerald-100 text-emerald-700 border-emerald-300" },
  rejected: { label: "Rejected", chip: "bg-red-100 text-red-600 border-red-200" },
  live: { label: "Live on Playlist", chip: "bg-blue-100 text-blue-700 border-blue-300" },
};

const GW_STATUS = {
  open: { label: "Open", dot: "bg-emerald-500", text: "text-emerald-700" },
  full: { label: "Full", dot: "bg-amber-500", text: "text-amber-700" },
  closed: { label: "Closed", dot: "bg-ink/40", text: "text-ink/50" },
};

export default function PlaylistDashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [expandedSub, setExpandedSub] = useState(null);
  const [expandedGw, setExpandedGw] = useState(null);
  const [showCreate, setShowCreate] = useState(false);
  const [reviewNote, setReviewNote] = useState("");
  const [reviewTarget, setReviewTarget] = useState(null);
  const [toggling, setToggling] = useState(null);

  const [newGw, setNewGw] = useState({
    playlist_name: "",
    playlist_spotify_url: "",
    curator_spotify_url: "",
    target_song_name: "",
    target_song_url: "",
    max_slots: 2,
    notes: "",
    curator_slug: "nova-highborn",
  });

  const load = async () => {
    try {
      const { data: d } = await api.get("/api/playlist/dashboard");
      setData(d);
      if (d.gateways.length > 0 && expandedGw === null) {
        setExpandedGw(d.gateways[0]._id);
      }
    } catch {
      toast.error("Couldn't load dashboard");
    } finally {
      setLoading(false);
    }
  };

  // eslint-disable-next-line react-hooks/exhaustive-deps -- intentional: load once on mount
  useEffect(() => { load(); }, []);

  const createGateway = async (e) => {
    e.preventDefault();
    try {
      await api.post("/api/playlist/gateway/create", newGw);
      toast.success("Gateway created!");
      setShowCreate(false);
      setNewGw({ ...newGw, playlist_name: "", playlist_spotify_url: "", target_song_name: "", target_song_url: "", notes: "" });
      load();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Couldn't create gateway");
    }
  };

  const approve = async (subId) => {
    try {
      await api.post("/api/playlist/approve", { submission_id: subId, note: reviewNote });
      toast.success("Approved! Add their song to your playlist.");
      setReviewTarget(null);
      setReviewNote("");
      load();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Couldn't approve");
    }
  };

  const reject = async (subId) => {
    try {
      await api.post("/api/playlist/reject", { submission_id: subId, note: reviewNote });
      toast.success("Submission rejected.");
      setReviewTarget(null);
      setReviewNote("");
      load();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Couldn't reject");
    }
  };

  const toggleGateway = async (gwId) => {
    setToggling(gwId);
    try {
      await api.patch(`/api/playlist/gateway/${gwId}/status`);
      load();
    } catch {
      toast.error("Couldn't update gateway status");
    } finally {
      setToggling(null);
    }
  };

  if (loading) return (
    <div className="flex items-center justify-center py-24 gap-3 text-ink/40">
      <Loader className="w-5 h-5 animate-spin" /> Loading dashboard…
    </div>
  );

  return (
    <div className="max-w-3xl mx-auto px-6 py-10">

      {/* Header */}
      <div className="flex items-start justify-between mb-8">
        <div>
          <div className="text-emerald-700 text-xs uppercase tracking-widest font-bold mb-1">Playlist Curation</div>
          <h1 className="font-heading text-3xl font-extrabold">Your Dashboard</h1>
          {data && (
            <p className="text-ink/50 text-sm mt-1">
              {data.open_gateways} gateway{data.open_gateways !== 1 ? "s" : ""} open ·
              {" "}{data.total_submissions} submissions ·
              {" "}{data.total_approved} approved
            </p>
          )}
        </div>
        <div className="flex items-center gap-2">
          <button onClick={load} className="p-2 text-ink/40 hover:text-ink border border-ink/10 rounded-lg transition-colors">
            <RefreshCw className="w-4 h-4" />
          </button>
          <button
            onClick={() => setShowCreate(!showCreate)}
            className="flex items-center gap-2 bg-emerald-700 hover:bg-emerald-600 text-white font-bold text-sm px-4 py-2 rounded-xl transition-colors"
          >
            <Plus className="w-4 h-4" /> New Gateway
          </button>
        </div>
      </div>

      {/* Create gateway form */}
      {showCreate && (
        <form onSubmit={createGateway} className="bg-emerald-50 border-2 border-emerald-200 rounded-2xl p-6 mb-8 space-y-4">
          <h2 className="font-heading font-extrabold text-lg text-emerald-800">Create New Gateway</h2>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-bold text-emerald-800/70 mb-1.5">Playlist Name *</label>
              <input required value={newGw.playlist_name} onChange={(e) => setNewGw({ ...newGw, playlist_name: e.target.value })}
                placeholder="e.g. Nova's Vibes Vol. 2"
                className="w-full px-3 py-2 border border-emerald-300 rounded-lg text-sm bg-white focus:outline-none focus:border-emerald-500" />
            </div>
            <div>
              <label className="block text-xs font-bold text-emerald-800/70 mb-1.5">Max Slots *</label>
              <input required type="number" min="1" max="20" value={newGw.max_slots}
                onChange={(e) => setNewGw({ ...newGw, max_slots: parseInt(e.target.value) })}
                className="w-full px-3 py-2 border border-emerald-300 rounded-lg text-sm bg-white focus:outline-none focus:border-emerald-500" />
              <p className="text-xs text-emerald-700/60 mt-0.5">How many artists can be placed</p>
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-emerald-800/70 mb-1.5">Playlist Spotify URL *</label>
            <input required value={newGw.playlist_spotify_url} onChange={(e) => setNewGw({ ...newGw, playlist_spotify_url: e.target.value })}
              placeholder="https://open.spotify.com/playlist/..."
              className="w-full px-3 py-2 border border-emerald-300 rounded-lg text-sm bg-white focus:outline-none focus:border-emerald-500" />
          </div>

          <div>
            <label className="block text-xs font-bold text-emerald-800/70 mb-1.5">Your Spotify Profile URL *</label>
            <input required value={newGw.curator_spotify_url} onChange={(e) => setNewGw({ ...newGw, curator_spotify_url: e.target.value })}
              placeholder="https://open.spotify.com/user/..."
              className="w-full px-3 py-2 border border-emerald-300 rounded-lg text-sm bg-white focus:outline-none focus:border-emerald-500" />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-bold text-emerald-800/70 mb-1.5">Required Song Name *</label>
              <input required value={newGw.target_song_name} onChange={(e) => setNewGw({ ...newGw, target_song_name: e.target.value })}
                placeholder="Song title artists must add"
                className="w-full px-3 py-2 border border-emerald-300 rounded-lg text-sm bg-white focus:outline-none focus:border-emerald-500" />
            </div>
            <div>
              <label className="block text-xs font-bold text-emerald-800/70 mb-1.5">Required Song Spotify URL *</label>
              <input required value={newGw.target_song_url} onChange={(e) => setNewGw({ ...newGw, target_song_url: e.target.value })}
                placeholder="https://open.spotify.com/track/..."
                className="w-full px-3 py-2 border border-emerald-300 rounded-lg text-sm bg-white focus:outline-none focus:border-emerald-500" />
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-emerald-800/70 mb-1.5">Note for Artists (optional)</label>
            <input value={newGw.notes} onChange={(e) => setNewGw({ ...newGw, notes: e.target.value })}
              placeholder="e.g. Looking for R&B and Neo Soul only · No explicit content"
              className="w-full px-3 py-2 border border-emerald-300 rounded-lg text-sm bg-white focus:outline-none focus:border-emerald-500" />
          </div>

          <div className="flex gap-3">
            <button type="submit" className="flex-1 bg-emerald-700 hover:bg-emerald-600 text-white font-bold py-2.5 rounded-xl transition-colors">
              Create Gateway
            </button>
            <button type="button" onClick={() => setShowCreate(false)} className="px-4 border border-emerald-300 text-emerald-800 font-bold rounded-xl hover:bg-emerald-100 transition-colors text-sm">
              Cancel
            </button>
          </div>
        </form>
      )}

      {/* Gateway list */}
      {(!data || data.gateways.length === 0) ? (
        <div className="text-center py-16 bg-white border border-ink/10 rounded-2xl">
          <div className="text-5xl mb-4">🎵</div>
          <h2 className="font-heading text-xl font-bold mb-2">No gateways yet</h2>
          <p className="text-ink/50 text-sm mb-4">Create your first gateway to start accepting artist submissions.</p>
          <button onClick={() => setShowCreate(true)} className="inline-flex items-center gap-2 bg-emerald-700 text-white font-bold px-6 py-3 rounded-xl hover:bg-emerald-600 transition-colors">
            <Plus className="w-4 h-4" /> Create First Gateway
          </button>
        </div>
      ) : (
        <div className="space-y-5">
          {data.gateways.map((gw) => {
            const gwStatus = GW_STATUS[gw.status] || GW_STATUS.closed;
            const isExpanded = expandedGw === gw._id;

            return (
              <div key={gw._id} className="bg-white border border-ink/10 rounded-2xl overflow-hidden">
                {/* Gateway header */}
                <div
                  className="flex items-center justify-between p-5 cursor-pointer hover:bg-ink/2 transition-colors"
                  onClick={() => setExpandedGw(isExpanded ? null : gw._id)}
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <div className={`w-2.5 h-2.5 rounded-full shrink-0 ${gwStatus.dot}`} />
                    <div className="min-w-0">
                      <div className="font-heading font-extrabold text-base truncate">{gw.playlist_name}</div>
                      <div className="text-xs text-ink/50 mt-0.5">
                        {gw.filled_slots}/{gw.max_slots} filled ·
                        {" "}{gw.pending_count} pending ·
                        {" "}{gw.approved_count} approved ·
                        <span className={gwStatus.text}> {gwStatus.label}</span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 shrink-0 ml-3">
                    <button
                      onClick={(e) => { e.stopPropagation(); toggleGateway(gw._id); }}
                      disabled={toggling === gw._id}
                      className={`text-xs font-bold px-3 py-1.5 rounded-lg border transition-colors ${
                        gw.status === "open"
                          ? "border-ink/20 text-ink/60 hover:border-red-300 hover:text-red-600"
                          : "border-emerald-300 text-emerald-700 hover:bg-emerald-50"
                      }`}
                    >
                      {toggling === gw._id ? <Loader className="w-3 h-3 animate-spin" /> : gw.status === "open" ? "Close" : "Open"}
                    </button>
                    {gw.playlist_spotify_url && (
                      <a href={gw.playlist_spotify_url} target="_blank" rel="noopener noreferrer"
                        onClick={(e) => e.stopPropagation()}
                        className="p-1.5 text-ink/30 hover:text-emerald-600 border border-ink/10 rounded-lg transition-colors">
                        <ExternalLink className="w-3.5 h-3.5" />
                      </a>
                    )}
                    {isExpanded ? <ChevronUp className="w-4 h-4 text-ink/40" /> : <ChevronDown className="w-4 h-4 text-ink/40" />}
                  </div>
                </div>

                {/* Submissions */}
                {isExpanded && (
                  <div className="border-t border-ink/10">
                    {gw.submissions.length === 0 ? (
                      <div className="px-5 py-8 text-center text-ink/40 text-sm">No submissions yet.</div>
                    ) : (
                      <div className="divide-y divide-ink/5">
                        {gw.submissions.map((sub) => {
                          const statusStyle = STATUS_STYLES[sub.status] || STATUS_STYLES.pending;
                          const isReviewing = reviewTarget === sub._id;
                          const completedSteps = Object.values(sub.steps_completed || {}).filter(Boolean).length;

                          return (
                            <div key={sub._id} className="p-5">
                              <div className="flex items-start justify-between gap-3 mb-3">
                                <div className="min-w-0">
                                  <div className="font-bold text-sm">{sub.artist_name}</div>
                                  <div className="text-ink/50 text-xs">{sub.song_title} · {sub.genre}</div>
                                  <div className="text-ink/40 text-xs mt-0.5">{sub.artist_email}</div>
                                </div>
                                <span className={`text-xs font-bold px-2.5 py-1 rounded-full border shrink-0 ${statusStyle.chip}`}>
                                  {statusStyle.label}
                                </span>
                              </div>

                              {/* Step completion badges */}
                              <div className="flex flex-wrap gap-1.5 mb-3">
                                {Object.entries(sub.steps_completed || {}).map(([step, done]) => (
                                  <span
                                    key={step}
                                    className={`text-xs px-2 py-0.5 rounded-full font-medium ${done ? "bg-emerald-100 text-emerald-700" : "bg-ink/5 text-ink/40"}`}
                                  >
                                    {done ? "✓" : "○"} {STEP_LABELS[step] || step}
                                  </span>
                                ))}
                              </div>

                              {/* Links */}
                              <div className="flex flex-wrap gap-2 mb-3">
                                {sub.song_spotify_url && (
                                  <a href={sub.song_spotify_url} target="_blank" rel="noopener noreferrer"
                                    className="inline-flex items-center gap-1 text-xs font-bold text-emerald-700 border border-emerald-300 px-2.5 py-1 rounded-lg hover:bg-emerald-50 transition-colors">
                                    <ExternalLink className="w-3 h-3" /> Listen on Spotify
                                  </a>
                                )}
                                {sub.artist_spotify_url && (
                                  <a href={sub.artist_spotify_url} target="_blank" rel="noopener noreferrer"
                                    className="inline-flex items-center gap-1 text-xs text-ink/50 border border-ink/15 px-2.5 py-1 rounded-lg hover:border-ink/30 transition-colors">
                                    <ExternalLink className="w-3 h-3" /> Artist Profile
                                  </a>
                                )}
                                {sub.share_url && (
                                  <a href={sub.share_url} target="_blank" rel="noopener noreferrer"
                                    className="inline-flex items-center gap-1 text-xs text-ink/50 border border-ink/15 px-2.5 py-1 rounded-lg hover:border-ink/30 transition-colors">
                                    <ExternalLink className="w-3 h-3" /> Share Post
                                  </a>
                                )}
                              </div>

                              {completedSteps < 5 && sub.status === "pending" && (
                                <p className="text-xs text-amber-600 mb-2">⚠ {completedSteps}/5 steps completed — artist is still working through the gateway.</p>
                              )}

                              {/* Review actions */}
                              {sub.status === "pending" && (
                                <>
                                  {!isReviewing ? (
                                    <div className="flex gap-2">
                                      <button onClick={() => setReviewTarget(sub._id)}
                                        className="text-xs font-bold text-emerald-700 border border-emerald-300 px-3 py-1.5 rounded-lg hover:bg-emerald-50 transition-colors">
                                        Review & Decide
                                      </button>
                                    </div>
                                  ) : (
                                    <div className="bg-ink/3 border border-ink/10 rounded-xl p-4 mt-2">
                                      <label className="block text-xs font-bold text-ink/60 mb-2">Note (optional — artist won't see this)</label>
                                      <input value={reviewNote} onChange={(e) => setReviewNote(e.target.value)}
                                        placeholder="e.g. Great track, adding Friday. / Sound doesn't fit this playlist."
                                        className="w-full px-3 py-2 border border-ink/20 rounded-lg text-xs bg-white focus:outline-none focus:border-emerald-500 mb-3" />
                                      <div className="flex gap-2">
                                        <button onClick={() => approve(sub._id)}
                                          className="flex items-center gap-1.5 text-xs font-bold bg-emerald-700 hover:bg-emerald-600 text-white px-4 py-2 rounded-lg transition-colors">
                                          <CheckCircle className="w-3.5 h-3.5" /> Approve
                                        </button>
                                        <button onClick={() => reject(sub._id)}
                                          className="flex items-center gap-1.5 text-xs font-bold bg-red-50 text-red-600 border border-red-200 hover:bg-red-100 px-4 py-2 rounded-lg transition-colors">
                                          <XCircle className="w-3.5 h-3.5" /> Reject
                                        </button>
                                        <button onClick={() => { setReviewTarget(null); setReviewNote(""); }}
                                          className="text-xs text-ink/40 hover:text-ink px-3 py-2 transition-colors">
                                          Cancel
                                        </button>
                                      </div>
                                    </div>
                                  )}
                                </>
                              )}

                              {sub.curator_note && (
                                <p className="text-xs text-ink/40 italic mt-2">Note: {sub.curator_note}</p>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
