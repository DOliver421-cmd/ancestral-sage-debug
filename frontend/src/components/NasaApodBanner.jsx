import { useEffect, useState } from "react";
import { api } from "../lib/api";
import { Sparkles, ExternalLink, Image as ImageIcon, Loader2, Rocket } from "lucide-react";

export default function NasaApodBanner() {
  const [apod, setApod] = useState(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");

  useEffect(() => {
    api.get("/nasa/apod")
      .then((r) => setApod(r.data))
      .catch((e) => setErr(e?.response?.data?.detail || e.message || "Could not load observatory feed"))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <section className="max-w-7xl mx-auto px-6 py-10">
        <div className="card-flat p-8 flex items-center gap-3 text-ink/50">
          <Loader2 className="w-5 h-5 animate-spin" /> Loading Virtual Observatory…
        </div>
      </section>
    );
  }
  if (err || !apod) return null;

  const isVideo = apod.media_type === "video";
  return (
    <section className="max-w-7xl mx-auto px-6 py-10" data-testid="nasa-apod-banner">
      <div className="flex items-center gap-2 mb-3">
        <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-ink text-signal text-xs font-black uppercase tracking-widest">
          <Rocket className="w-3.5 h-3.5" /> Virtual Observatory
        </span>
        <span className="text-xs font-bold text-ink/40">{apod.date}</span>
        {apod.copyright && <span className="text-xs text-ink/40">© {apod.copyright}</span>}
      </div>
      <div className="card-flat overflow-hidden grid md:grid-cols-[1.35fr_1fr] gap-0">
        <div className="bg-ink/5 min-h-[280px] flex items-center justify-center overflow-hidden">
          {isVideo ? (
            <iframe
              title={apod.title}
              src={apod.url}
              className="w-full h-[280px] md:h-full min-h-[280px]"
              allowFullScreen
              loading="lazy"
            />
          ) : (
            <img src={apod.hdurl || apod.url} alt={apod.title} className="w-full h-full object-cover" loading="lazy" />
          )}
        </div>
        <div className="p-6 flex flex-col">
          <div className="flex items-start gap-2 mb-2">
            {isVideo ? <ExternalLink className="w-5 h-5 text-copper shrink-0 mt-0.5" /> : <ImageIcon className="w-5 h-5 text-copper shrink-0 mt-0.5" />}
            <h3 className="font-heading text-xl font-bold text-ink leading-tight">{apod.title}</h3>
          </div>
          <p className="text-sm text-ink/60 leading-relaxed line-clamp-[10]">{apod.explanation}</p>
          <div className="mt-4 flex flex-wrap gap-2">
            {!isVideo && apod.hdurl && (
              <a href={apod.hdurl} target="_blank" rel="noopener noreferrer" className="btn-outline text-xs inline-flex items-center gap-1.5">
                Open full image <ExternalLink className="w-3.5 h-3.5" />
              </a>
            )}
            {isVideo && (
              <a href={apod.url} target="_blank" rel="noopener noreferrer" className="btn-outline text-xs inline-flex items-center gap-1.5">
                Watch on source <ExternalLink className="w-3.5 h-3.5" />
              </a>
            )}
            <a href="https://apod.nasa.gov/apod/astropix.html" target="_blank" rel="noopener noreferrer" className="text-xs font-bold text-copper hover:text-ink inline-flex items-center gap-1 px-3 py-2">
              <Sparkles className="w-3.5 h-3.5" /> NASA APOD
            </a>
          </div>
          <p className="text-[11px] text-ink/35 mt-4">Powered by your NASA API key — cached 24h, key never leaves the server. Use in lessons via Video Studio.</p>
        </div>
      </div>
    </section>
  );
}
