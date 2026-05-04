import { useEffect, useState } from "react";
import AppShell from "../components/AppShell";
import { api, BACKEND_URL, getToken } from "../lib/api";
import { toast } from "sonner";
import PortfolioBody from "../components/PortfolioBody";
import { Share2, Download, Globe, Lock } from "lucide-react";

export default function Portfolio() {
  const [data, setData] = useState(null);
  const [bio, setBio] = useState("");
  const [publishing, setPublishing] = useState(false);
  const token = getToken();

  const load = () => api.get("/portfolio/me").then((r) => { setData(r.data); setBio(r.data.bio || ""); });
  useEffect(() => { load(); }, []);

  const publish = async (shouldPublish) => {
    setPublishing(true);
    try {
      await api.post("/portfolio/publish", { bio, publish: shouldPublish });
      toast.success(shouldPublish ? "Portfolio published" : "Portfolio set private");
      load();
    } catch { toast.error("Failed to update"); }
    setPublishing(false);
  };

  if (!data) return <AppShell><div className="p-10">Loading…</div></AppShell>;
  const shareUrl = data.share_slug ? `${window.location.origin}/p/${data.share_slug}` : null;

  return (
    <AppShell>
      <div className="px-10 py-10 max-w-6xl">
        <div className="overline text-copper">Workforce-Ready Portfolio</div>
        <h1 className="font-heading text-4xl font-bold mt-2">Your Proof of Work.</h1>
        <p className="text-ink/60 mt-2 max-w-2xl">Every module, lab, evaluation, and badge — in one employer-ready view. Export as PDF or publish a shareable link.</p>

        {/* Publish panel */}
        <div className="card-flat p-6 mt-8" data-testid="publish-panel">
          <div className="flex items-center justify-between gap-4 flex-wrap">
            <div>
              <div className="font-heading text-xl font-bold flex items-center gap-3">
                {data.share_slug ? <Globe className="w-5 h-5 text-copper" /> : <Lock className="w-5 h-5 text-ink/50" />}
                {data.share_slug ? "Public" : "Private"}
              </div>
              {shareUrl && (
                <div className="mt-2 font-mono text-xs text-copper break-all" data-testid="share-url">{shareUrl}</div>
              )}
            </div>
            <div className="flex gap-2 flex-wrap">
              <a href={`${BACKEND_URL}/api/portfolio/export.pdf?token=${token}`} target="_blank" rel="noreferrer"
                className="btn-primary inline-flex items-center gap-2" data-testid="btn-export-pdf">
                <Download className="w-4 h-4" /> Export PDF
              </a>
              {data.share_slug ? (
                <>
                  <button onClick={() => { navigator.clipboard.writeText(shareUrl); toast.success("Link copied"); }} className="btn-copper inline-flex items-center gap-2" data-testid="btn-copy-link">
                    <Share2 className="w-4 h-4" /> Copy Link
                  </button>
                  <button onClick={() => publish(false)} disabled={publishing} className="btn-ghost" data-testid="btn-unpublish">Set Private</button>
                </>
              ) : (
                <button onClick={() => publish(true)} disabled={publishing} className="btn-copper inline-flex items-center gap-2" data-testid="btn-publish">
                  <Globe className="w-4 h-4" /> Publish
                </button>
              )}
            </div>
          </div>

          <div className="mt-4">
            <label className="overline text-ink/60">About You (optional bio, 1-2 sentences)</label>
            <textarea value={bio} onChange={(e) => setBio(e.target.value)} rows={2} maxLength={200}
              placeholder="e.g., Second-year apprentice focused on residential wiring and off-grid solar."
              className="w-full mt-2 px-3 py-2 border border-ink/20 focus:border-ink focus:outline-none focus:ring-2 focus:ring-signal text-sm"
              data-testid="input-bio" />
            <div className="text-xs text-ink/50 mt-1">{bio.length}/200</div>
          </div>
        </div>

        <div className="mt-10">
          <PortfolioBody data={data} />
        </div>
      </div>
    </AppShell>
  );
}
