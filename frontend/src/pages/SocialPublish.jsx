import { useState, useEffect } from "react";
import { useAuth } from "../lib/auth";
import { api } from "../lib/api";
import { toast } from "sonner";
import { Instagram, Facebook, ExternalLink, CheckCircle, XCircle, Loader, Send, Link as LinkIcon } from "lucide-react";

const PLATFORMS = [
  {
    id: "facebook",
    label: "Facebook Page",
    icon: Facebook,
    color: "bg-blue-600",
    textColor: "text-blue-600",
    borderColor: "border-blue-200",
    bgColor: "bg-blue-50",
    oauthNote: "Requires FB_APP_ID + FB_APP_SECRET in Railway environment.",
  },
  {
    id: "instagram",
    label: "Instagram",
    icon: Instagram,
    color: "bg-gradient-to-br from-purple-500 to-pink-500",
    textColor: "text-pink-600",
    borderColor: "border-pink-200",
    bgColor: "bg-pink-50",
    oauthNote: "Uses same Meta credentials as Facebook. Image required for posts.",
  },
  {
    id: "twitter",
    label: "Twitter / X",
    icon: ExternalLink,
    color: "bg-black",
    textColor: "text-black",
    borderColor: "border-ink/20",
    bgColor: "bg-ink/5",
    oauthNote: "Requires TWITTER_API_KEY + TWITTER_API_SECRET in Railway environment.",
  },
  {
    id: "tiktok",
    label: "TikTok",
    icon: ExternalLink,
    color: "bg-gradient-to-br from-black to-pink-900",
    textColor: "text-pink-800",
    borderColor: "border-pink-300",
    bgColor: "bg-pink-50",
    oauthNote: "Requires TIKTOK_CLIENT_KEY + TIKTOK_CLIENT_SECRET. Video posts only.",
  },
];

export default function SocialPublish() {
  const { user } = useAuth();
  const [connected, setConnected] = useState({});
  const [selected, setSelected] = useState([]);
  const [content, setContent] = useState("");
  const [imageUrl, setImageUrl] = useState("");
  const [linkUrl, setLinkUrl] = useState("");
  const [publishing, setPublishing] = useState(false);
  const [results, setResults] = useState(null);
  const [loadingAccounts, setLoadingAccounts] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const { data } = await api.get("/api/social/connected-accounts");
        setConnected(data.connected || {});
      } catch {
        // not critical
      } finally {
        setLoadingAccounts(false);
      }
    })();
  }, []);

  const togglePlatform = (id) => {
    if (!connected[id]) return; // can't select unconnected
    setSelected((prev) =>
      prev.includes(id) ? prev.filter((p) => p !== id) : [...prev, id]
    );
  };

  const publish = async () => {
    if (!content.trim()) { toast.error("Write something first"); return; }
    if (selected.length === 0) { toast.error("Select at least one platform"); return; }
    setPublishing(true);
    setResults(null);
    try {
      const { data } = await api.post("/api/social/publish", {
        content,
        platforms: selected,
        image_url: imageUrl || null,
        link_url: linkUrl || null,
      });
      setResults(data);
      if (data.status === "success") toast.success("Posted to all platforms!");
      else if (data.status === "partial") toast.warning("Posted to some platforms — check results below.");
      else toast.error("All platforms failed — see results below.");
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Publish failed");
    } finally {
      setPublishing(false);
    }
  };

  const charCount = content.length;
  const twitterSelected = selected.includes("twitter");
  const overLimit = twitterSelected && charCount > 280;

  return (
    <div className="max-w-2xl mx-auto px-6 py-10">
      <div className="mb-8">
        <div className="text-copper text-xs uppercase tracking-widest font-bold mb-1">One post. All platforms.</div>
        <h1 className="font-heading text-3xl font-extrabold mb-2">Social Publisher</h1>
        <p className="text-ink/60 text-sm">Write once, publish to all your connected social media accounts simultaneously.</p>
      </div>

      {/* Platform selector */}
      <div className="mb-6">
        <h2 className="font-bold text-sm mb-3 text-ink/70 uppercase tracking-wider">Your Platforms</h2>
        {loadingAccounts ? (
          <div className="flex items-center gap-2 text-ink/40 text-sm py-4"><Loader className="w-4 h-4 animate-spin" /> Loading connected accounts…</div>
        ) : (
          <div className="grid grid-cols-2 gap-3">
            {PLATFORMS.map(({ id, label, icon: Icon, color, textColor, borderColor, bgColor, oauthNote }) => {
              const isConnected = !!connected[id];
              const isSelected = selected.includes(id);
              return (
                <button
                  key={id}
                  onClick={() => isConnected ? togglePlatform(id) : toast.info(`Connect ${label} first — ${oauthNote}`)}
                  className={`flex items-center gap-3 p-4 rounded-xl border-2 transition-all text-left ${
                    isSelected
                      ? `${borderColor} ${bgColor}`
                      : isConnected
                      ? "border-ink/10 bg-white hover:border-ink/30"
                      : "border-dashed border-ink/15 bg-white/50 opacity-60"
                  }`}
                >
                  <div className={`w-9 h-9 rounded-lg ${color} flex items-center justify-center shrink-0`}>
                    <Icon className="w-4 h-4 text-white" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className={`font-bold text-sm ${isSelected ? textColor : "text-ink"}`}>{label}</div>
                    {isConnected ? (
                      <div className="text-xs text-ink/50">{connected[id]?.account_name || "Connected"}</div>
                    ) : (
                      <div className="text-xs text-ink/40">Not connected</div>
                    )}
                  </div>
                  {isSelected && <CheckCircle className={`w-4 h-4 shrink-0 ${textColor}`} />}
                </button>
              );
            })}
          </div>
        )}
        <p className="text-xs text-ink/40 mt-3">
          To connect a platform, go to <strong>Settings → Social Accounts</strong>. Platform credentials must be configured by your admin in Railway.
        </p>
      </div>

      {/* Content editor */}
      <div className="mb-4">
        <div className="flex items-center justify-between mb-2">
          <label className="font-bold text-sm text-ink/70 uppercase tracking-wider">Your Post</label>
          <span className={`text-xs font-bold ${overLimit ? "text-red-500" : "text-ink/40"}`}>{charCount}{twitterSelected ? "/280" : ""}</span>
        </div>
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder="What's happening in the community?"
          className={`w-full px-4 py-3 border-2 rounded-xl text-sm bg-white focus:outline-none focus:border-copper transition-colors h-32 resize-none ${overLimit ? "border-red-300" : "border-ink/20"}`}
        />
      </div>

      {/* Optional fields */}
      <div className="grid grid-cols-2 gap-3 mb-6">
        <div>
          <label className="block text-xs font-bold text-ink/60 mb-1.5 uppercase tracking-wider">Image URL (optional)</label>
          <input
            value={imageUrl}
            onChange={(e) => setImageUrl(e.target.value)}
            placeholder="https://..."
            className="w-full px-3 py-2 border border-ink/20 rounded-lg text-xs bg-white focus:outline-none focus:border-copper"
          />
          <p className="text-xs text-ink/35 mt-1">Required for Instagram.</p>
        </div>
        <div>
          <label className="block text-xs font-bold text-ink/60 mb-1.5 uppercase tracking-wider">Link URL (optional)</label>
          <input
            value={linkUrl}
            onChange={(e) => setLinkUrl(e.target.value)}
            placeholder="https://..."
            className="w-full px-3 py-2 border border-ink/20 rounded-lg text-xs bg-white focus:outline-none focus:border-copper"
          />
          <p className="text-xs text-ink/35 mt-1">Attached to Facebook post.</p>
        </div>
      </div>

      {/* Publish button */}
      <button
        onClick={publish}
        disabled={publishing || selected.length === 0 || !content.trim() || overLimit}
        className="w-full py-3 px-4 bg-ink text-white font-bold rounded-xl flex items-center justify-center gap-2 hover:bg-ink/80 disabled:opacity-40 transition-colors"
      >
        {publishing ? <><Loader className="w-4 h-4 animate-spin" /> Publishing…</> : <><Send className="w-4 h-4" /> Publish to {selected.length || "0"} Platform{selected.length !== 1 ? "s" : ""}</>}
      </button>

      {/* Results */}
      {results && (
        <div className="mt-6 space-y-2">
          <h3 className="font-bold text-sm text-ink/70 uppercase tracking-wider mb-3">Results</h3>
          {Object.entries(results.published || {}).map(([platform, result]) => (
            <div key={platform} className="flex items-center gap-3 p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-sm">
              <CheckCircle className="w-4 h-4 text-emerald-600 shrink-0" />
              <span className="font-bold capitalize">{platform}</span>
              <span className="text-ink/60">{result.post_id ? `Post ID: ${result.post_id}` : result.note || "Posted"}</span>
            </div>
          ))}
          {Object.entries(results.errors || {}).map(([platform, error]) => (
            <div key={platform} className="flex items-center gap-3 p-3 bg-red-50 border border-red-200 rounded-xl text-sm">
              <XCircle className="w-4 h-4 text-red-500 shrink-0" />
              <span className="font-bold capitalize">{platform}</span>
              <span className="text-ink/60">{error}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
