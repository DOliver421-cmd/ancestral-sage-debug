import { useEffect, useState } from "react";
import { ExternalLink, ArrowUpRight, RefreshCw } from "lucide-react";

const PREMIUM_URL = "https://waiinstitutepremiumservices.bolt.host/services";

/**
 * WAI Institute Premium Services — embedded in-site (no redirect away).
 * The external site allows framing (no X-Frame-Options / frame-ancestors on
 * its response) and our CSP frame-src allowlists that host. If the embed is
 * ever blocked (provider changes headers), a fallback panel with an open
 * button keeps the destination reachable — never a dead end.
 */
export default function PremiumServices() {
  const [blocked, setBlocked] = useState(false);
  const [loaded, setLoaded] = useState(false);

  // Detect embed blocking: if the iframe is still cross-origin-blocked,
  // onLoad may never fire; use a timeout as a soft signal plus onLoad.
  useEffect(() => {
    const t = setTimeout(() => {
      if (!loaded) setBlocked(true);
    }, 6000);
    return () => clearTimeout(t);
  }, [loaded]);

  return (
    <div className="min-h-[70vh] flex flex-col px-4 py-6 max-w-6xl mx-auto">
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div>
          <h1 className="font-heading font-bold text-xl text-ink">WAI Institute Premium Services</h1>
          <p className="text-xs text-ink/50">Embedded live from waiinstitutepremiumservices.bolt.host</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => { setBlocked(false); setLoaded(false); }}
            className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-semibold border border-ink/15 text-ink/70 hover:border-ink/50"
            data-testid="premium-reload"
          >
            <RefreshCw className="w-3.5 h-3.5" /> Reload
          </button>
          <a
            href={PREMIUM_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-bold text-white bg-[#b5651d] hover:bg-[#9a5418] transition-colors"
            data-testid="premium-open-external"
          >
            Open in new tab <ArrowUpRight className="w-3.5 h-3.5" />
          </a>
        </div>
      </div>

      <div className="relative flex-1 mt-4 min-h-[60vh]">
        {!loaded && !blocked && (
          <div className="absolute inset-0 flex items-center justify-center text-sm text-ink/40">
            Loading premium services…
          </div>
        )}
        {blocked && (
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 text-center px-6">
            <p className="text-sm text-ink/60 max-w-md">
              The embedded view could not load here. Use the button below to open
              Premium Services — it opens in a new tab so you don't lose your place.
            </p>
            <a
              href={PREMIUM_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-bold text-white bg-[#b5651d] hover:bg-[#9a5418] transition-colors"
            >
              Continue to Premium Services <ExternalLink className="w-4 h-4" />
            </a>
          </div>
        )}
        <iframe
          src={PREMIUM_URL}
          title="WAI Institute Premium Services"
          className={`w-full rounded-xl border border-ink/10 bg-white ${loaded ? "block" : "opacity-0"} min-h-[60vh]`}
          style={{ height: "72vh" }}
          onLoad={() => setLoaded(true)}
          onError={() => setBlocked(true)}
          sandbox="allow-scripts allow-same-origin allow-forms allow-popups allow-popups-to-escape-sandbox"
          referrerPolicy="strict-origin-when-cross-origin"
          data-testid="premium-embed"
        />
      </div>
    </div>
  );
}
