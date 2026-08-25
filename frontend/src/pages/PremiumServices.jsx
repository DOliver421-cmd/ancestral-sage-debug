import { ExternalLink, Store, CreditCard, Globe, ShieldCheck, Sparkles, ArrowUpRight } from "lucide-react";

const PREMIUM_URL = "https://waiinstitutepremiumservices.bolt.host/";

const CHIPS = [
  { icon: Store, label: "Stripe-integrated premium store" },
  { icon: CreditCard, label: "Payments-as-a-Service for platforms & creators" },
  { icon: ShieldCheck, label: "Secure checkout & fulfillment" },
];

export default function PremiumServices() {
  return (
    <div className="min-h-full">
      {/* ── Hero ─────────────────────────────────────────────────────────── */}
      <div className="relative overflow-hidden bg-gradient-to-br from-[#1a1033] via-[#0d0721] to-[#1B4332] text-white">
        <div
          className="absolute inset-0 opacity-20"
          style={{
            background:
              "radial-gradient(800px 300px at 20% -10%, rgba(232,165,30,0.35), transparent 60%), radial-gradient(600px 260px at 85% 10%, rgba(183,138,255,0.25), transparent 60%)",
          }}
        />
        <div className="relative max-w-5xl mx-auto px-6 py-14 sm:py-16">
          <p className="inline-flex items-center gap-2 text-xs font-bold uppercase tracking-[0.2em] text-[#E8A51E] mb-3">
            <Sparkles className="w-4 h-4" /> WAI-Institute Ecosystem
          </p>
          <h1 className="text-3xl sm:text-5xl font-black leading-tight mb-4">
            Premium Services
          </h1>
          <p className="max-w-2xl text-white/80 text-sm sm:text-base leading-relaxed mb-6">
            The full WAI-Institute premium experience — our Stripe-integrated store and the
            payments ecosystem we built to help other platforms and creators accept payments,
            sell products, and grow their own revenue streams.
          </p>
          <div className="flex flex-wrap gap-3">
            {CHIPS.map(({ icon: Icon, label }) => (
              <span
                key={label}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-full text-xs font-semibold border border-[#E8A51E]/30 bg-[#E8A51E]/10 text-[#f5c96b]"
              >
                <Icon className="w-3.5 h-3.5" /> {label}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* ── Embedded premium services site ──────────────────────────────── */}
      <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8">
        <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
          <h2 className="text-lg font-bold text-[#1a1a1a]">Live experience</h2>
          <a
            href={PREMIUM_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold text-white bg-[#b5651d] hover:bg-[#9a5418] transition-colors"
            data-testid="premium-open-external"
          >
            Open in new tab <ExternalLink className="w-4 h-4" />
          </a>
        </div>

        <div className="bg-white rounded-xl border border-[#b5651d]/20 shadow-sm overflow-hidden">
          <iframe
            src={PREMIUM_URL}
            title="WAI-Institute Premium Services"
            className="w-full border-0"
            style={{ height: "min(1400px, 78vh)" }}
            loading="lazy"
            allow="payment; clipboard-write"
            referrerPolicy="no-referrer-when-downgrade"
            data-testid="premium-iframe"
          />
        </div>

        <p className="mt-3 text-xs text-[#1a1a1a]/50 flex items-center gap-1.5">
          <Globe className="w-3.5 h-3.5 shrink-0" />
          If the page doesn't render inside the frame, use “Open in new tab” above — it opens
          directly at{" "}
          <a
            href={PREMIUM_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-0.5 text-[#b5651d] font-semibold hover:underline"
          >
            waiinstitutepremiumservices.bolt.host <ArrowUpRight className="w-3 h-3" />
          </a>
        </p>
      </div>
    </div>
  );
}
