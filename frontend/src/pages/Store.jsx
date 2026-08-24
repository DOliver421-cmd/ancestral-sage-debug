import { useState, useEffect, useCallback } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import AppShell from "../components/AppShell";
import { ExternalLink, ArrowRight, ShoppingBag, Loader2 } from "lucide-react";

const GUMROAD_PROFILE = "https://namoshun.gumroad.com/";

/**
 * /store — first-party catalog first: every product creators published in the
 * platform, bought through our own checkout (70/30 creator split). The external
 * Gumroad storefront stays below as a secondary venue.
 */
export default function Store() {
  const { user } = useAuth();
  const [products, setProducts] = useState(null);
  const [buying, setBuying] = useState(null);
  const [notice, setNotice] = useState(null);

  const load = useCallback(() => {
    api.get("/media/products")
      .then((r) => setProducts(Array.isArray(r.data) ? r.data : []))
      .catch(() => setProducts([]));
  }, []);
  useEffect(() => { load(); }, [load]);

  async function buy(p) {
    if (!user) { window.location.href = `/auth?returnTo=/store`; return; }
    setBuying(p.id);
    setNotice(null);
    try {
      const { data } = await api.post(`/media/products/${p.id}/checkout`);
      if (data?.already_purchased) {
        setNotice(`You already own “${p.title}” — download it from your purchases.`);
        setBuying(null);
        return;
      }
      if (data?.url) { window.location.href = data.url; return; }
      setNotice("Checkout could not start. Please try again.");
    } catch (e) {
      setNotice(e?.response?.data?.detail || "Checkout could not start. Please try again.");
    }
    setBuying(null);
  }

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

        {notice && (
          <div className="mb-6 rounded-lg border border-copper/40 bg-bone px-4 py-3 text-sm text-ink" data-testid="store-notice">
            {notice}
          </div>
        )}

        {/* ── First-party catalog — real products, real checkout ── */}
        <div className="mb-10">
          <div className="flex items-center justify-between gap-3 mb-4">
            <h2 className="font-heading text-xl font-bold text-ink flex items-center gap-2">
              <ShoppingBag className="w-5 h-5 text-copper" /> Creator Products
            </h2>
            <span className="text-[10px] font-black uppercase tracking-widest bg-green-100 text-green-800 px-2 py-0.5 rounded-full">
              Sold here · creators keep 70%
            </span>
          </div>

          {products === null && (
            <div className="text-sm text-ink/50 py-6"><Loader2 className="w-4 h-4 inline animate-spin mr-2" />Loading products…</div>
          )}

          {Array.isArray(products) && products.length === 0 ? (
            <div className="card-flat p-6 text-sm text-ink/60" data-testid="store-empty">
              No products published yet. Creators publish digital products from the Creator Studio and they appear here instantly.
            </div>
          ) : null}

          {Array.isArray(products) && products.length > 0 && (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4" data-testid="store-catalog">
              {products.map((p) => (
                <div key={p.id} className="card-flat p-5 flex flex-col">
                  <div className="overline text-ink/40">{p.product_type === "file" ? "Digital download" : (p.product_type || "Digital")}</div>
                  <div className="font-heading font-bold text-lg text-ink mt-1">{p.title}</div>
                  {p.description && <div className="text-sm text-ink/60 mt-1 flex-1" style={{ display: "-webkit-box", WebkitLineClamp: 3, WebkitBoxOrient: "vertical", overflow: "hidden" }}>{p.description}</div>}
                  <div className="text-xs text-ink/50 mt-2">by {p.seller_display_name}</div>
                  <div className="flex items-center justify-between mt-4">
                    <span className="font-heading font-black text-xl text-ink">
                      {p.price_cents > 0 ? `$${(p.price_cents / 100).toFixed(2)}` : "Free"}
                    </span>
                    <button
                      onClick={() => buy(p)}
                      disabled={buying === p.id}
                      data-testid={`buy-${p.id}`}
                      className="btn-copper text-sm px-4 py-2 disabled:opacity-60"
                    >
                      {buying === p.id ? <Loader2 className="w-4 h-4 animate-spin" /> : (p.price_cents > 0 ? "Buy" : "Get")}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* External storefront — secondary venue */}
        <div className="bg-white border border-ink/10 rounded-2xl overflow-hidden shadow-sm">
          <div className="flex items-center justify-between gap-3 px-5 py-3 border-b border-ink/10 bg-bone/60">
            <div className="text-sm font-bold text-ink flex items-center gap-2">
              NAM Oshun&apos;s Storefront
              <span className="text-[10px] font-black uppercase tracking-widest bg-green-100 text-green-800 px-2 py-0.5 rounded-full">
                External · Gumroad
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
