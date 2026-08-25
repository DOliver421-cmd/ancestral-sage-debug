import { useEffect } from "react";
import { ExternalLink, ArrowUpRight } from "lucide-react";

const PREMIUM_URL = "https://waiinstitutepremiumservices.bolt.host/services";

/**
 * WAI Institute Premium Services — direct redirect subpage.
 * The nav item lands here, and this page sends the visitor straight to
 * the premium services site so they never lose the destination behind a
 * frame. If the redirect is blocked, the button below still gets them there.
 */
export default function PremiumServices() {
  useEffect(() => {
    window.location.replace(PREMIUM_URL);
  }, []);

  return (
    <div className="min-h-[60vh] flex flex-col items-center justify-center gap-4 px-6 py-16 text-center">
      <p className="text-2xl font-black text-ink font-heading">WAI Institute Premium Services</p>
      <p className="text-sm text-ink/55 max-w-md">
        Opening the premium services site — you'll be taken straight there.
      </p>
      <a
        href={PREMIUM_URL}
        target="_blank"
        rel="noopener noreferrer"
        className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-bold text-white bg-[#b5651d] hover:bg-[#9a5418] transition-colors"
        data-testid="premium-open-external"
      >
        Continue to Premium Services <ExternalLink className="w-4 h-4" />
      </a>
      <p className="text-xs text-ink/50 flex items-center gap-1.5">
        Not redirected automatically? Open
        <a href={PREMIUM_URL} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-0.5 text-[#b5651d] font-semibold hover:underline">
          waiinstitutepremiumservices.bolt.host <ArrowUpRight className="w-3 h-3" />
        </a>
        directly.
      </p>
    </div>
  );
}
