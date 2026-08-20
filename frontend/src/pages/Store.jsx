import { Link } from "react-router-dom";
import AppShell from "../components/AppShell";
import { ExternalLink, ArrowRight } from "lucide-react";

const GUMROAD_PROFILE = "https://namoshun.gumroad.com/";

export default function Store() {
  return (
    <AppShell>
      <div className="p-8 max-w-6xl mx-auto">
        <div className="mb-6">
          <h1 className="font-heading text-3xl font-bold text-ink mb-2">M.O.R.E. Store</h1>
          <p className="text-ink/60">
            Support the mission. Every purchase goes straight to the M.O.R.E. Help Center and the community.
          </p>
        </div>

        {/* Membership & donation links */}
        <div className="flex flex-wrap gap-3 mb-8">
          <Link
            to="/subscribe"
            className="inline-flex items-center gap-2 bg-ink text-white text-sm font-bold px-4 py-2 rounded-lg hover:bg-ink/80 transition-colors"
          >
            Memberships <ArrowRight className="w-4 h-4" />
          </Link>
          <Link
            to="/donate"
            className="inline-flex items-center gap-2 border-2 border-ink/20 hover:border-ink font-bold text-sm px-4 py-2 rounded-lg transition-colors text-ink"
          >
            Make a Donation <ArrowRight className="w-4 h-4" />
          </Link>
        </div>

        {/* Gumroad storefront — live commerce until Lemon Squeezy approval */}
        <div className="bg-white border border-ink/10 rounded-2xl overflow-hidden shadow-sm">
          <div className="flex items-center justify-between gap-3 px-5 py-3 border-b border-ink/10 bg-bone/60">
            <div className="text-sm font-bold text-ink flex items-center gap-2">
              NAM Oshun&apos;s Storefront
              <span className="text-[10px] font-black uppercase tracking-widest bg-green-100 text-green-800 px-2 py-0.5 rounded-full">
                Live · Gumroad
              </span>
            </div>
            <a
              href={GUMROAD_PROFILE}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1.5 text-xs font-bold text-copper hover:text-copper/70 transition-colors"
            >
              Open in new tab <ExternalLink className="w-3.5 h-3.5" />
            </a>
          </div>
          <iframe
            src={GUMROAD_PROFILE}
            title="NAM Oshun Gumroad storefront"
            className="w-full h-[75vh] min-h-[600px] border-0"
            loading="lazy"
            referrerPolicy="no-referrer-when-downgrade"
            allow="payment"
          />
        </div>

        <p className="text-xs text-ink/40 mt-4">
          Digital products and media are available now. Physical merchandise is not yet available.
        </p>
      </div>
    </AppShell>
  );
}
