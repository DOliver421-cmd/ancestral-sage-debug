import { useState, useEffect, useCallback } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import { MEMBERSHIP_PLANS, TRIAL_PLAN } from "../lib/plans";
import AppShell from "../components/AppShell";
import { ExternalLink, ArrowRight, ShoppingBag, Loader2, Zap, Check, AlertTriangle, BookOpen, Download } from "lucide-react";
import { STARTER_LIBRARY } from "../lib/contentLibrary";

const GUMROAD_PROFILE = "https://namoshun.gumroad.com/";

/**
 * /store — everything for sale, on one page, one click from checkout:
 *   1. The $3 all-access trial
 *   2. Membership tiers (bought directly here — no detour through /plans)
 *   3. Creator products (our own catalog; creators keep 70%)
 *   4. The external Gumroad storefront, clearly labeled
 */
export default function Store() {
  const { user } = useAuth();
  const [isStore, setIsStore] = useState(false);
  const [products, setProducts] = useState(null);
  const [catalogError, setCatalogError] = useState(null);
  const [buying, setBuying] = useState(null);
  const [notice, setNotice] = useState(null);
  const [noticeIsError, setNoticeIsError] = useState(false);

  const load = useCallback(() => {
    setCatalogError(null);
    api.get("/media/products")
      .then((r) => setProducts(Array.isArray(r.data) ? r.data : []))
      .catch(() => {
        setProducts([]);
        setCatalogError("The product catalog could not be loaded right now. Please refresh in a moment.");
      });
  }, []);
  useEffect(() => { load(); }, [load]);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    setIsStore(params.get("view") === "store");
  }, []);

  async function checkout(productKey, label) {
    if (!user) { window.location.href = `/auth?returnTo=/store`; return; }
    setBuying(productKey);
    setNotice(null);
    try {
      const { data } = await api.post("/payments/checkout", { product_key: productKey, quantity: 1 });
      if (data?.url) { window.location.href = data.url; return; }
      showFail("Checkout could not start. Please try again in a moment.");
    } catch (e) {
      const detail = e?.response?.data?.detail || "";
      if (e?.response?.status === 501 || /not configured/i.test(detail)) {
        setNotice("Payments are being set up. Membership checkout will be available soon. In the meantime, explore the free features or contact support.");
        setNoticeIsError(false);
      } else {
        showFail(detail || `Could not start checkout for ${label}. Please try again.`);
      }
    }
    setBuying(null);
  }

  function showFail(msg) {
    setNotice(msg);
    setNoticeIsError(true);
  }

  async function buyProduct(p) {
    if (!user) { window.location.href = `/auth?returnTo=/store`; return; }
    setBuying(p.id);
    setNotice(null);
    try {
      const { data } = await api.post(`/media/products/${p.id}/checkout`);
      if (data?.already_purchased) {
        setNotice(`You already own “${p.title}” — download it from your purchases.`);
        setNoticeIsError(false);
        setBuying(null);
        return;
      }
      if (data?.url) { window.location.href = data.url; return; }
      showFail("Checkout could not start. Please try again in a moment.");
    } catch (e) {
      const detail = e?.response?.data?.detail || "";
      if (e?.response?.status === 501 || /not configured/i.test(detail)) {
        setNotice("Payments are being configured. Digital products will be available for purchase soon.");
        setNoticeIsError(false);
      } else {
        showFail(detail || "Checkout could not start. Please try again.");
      }
    }
    setBuying(null);
  }

  const paidPlans = MEMBERSHIP_PLANS.filter((p) => p.key !== "free");
  const freePlan = MEMBERSHIP_PLANS.find((p) => p.key === "free");
  const trial = TRIAL_PLAN;

  return (
    <AppShell>
      <div className="p-8 max-w-6xl mx-auto">
        <div className="mb-6">
          <h1 className="font-heading text-3xl font-bold text-ink mb-2">M.O.R.E. Store</h1>
          <p className="text-ink/60">
            Everything for sale, on one page. One click to checkout.
          </p>
        </div>

        {notice && (
          <div
            className={`mb-6 rounded-lg border px-4 py-3 text-sm ${noticeIsError ? "border-destructive/40 bg-destructive/5 text-destructive" : "border-copper/40 bg-bone text-ink"}`}
            data-testid="store-notice"
          >
            {notice}
          </div>
        )}

        {/* ── 1. $3 Trial ── */}
        {trial && (
          <div className="mt-2 mb-8 rounded-2xl p-6 flex flex-col sm:flex-row items-center gap-5"
            style={{ background: "linear-gradient(135deg,#1B4332,#2D6A4F)", border: "2px solid #E8A51E" }}>
            <div className="flex items-center gap-3 shrink-0">
              <Zap style={{ fontSize: 30, color: "#E8A51E" }} />
              <div>
                <div className="font-heading font-black text-2xl text-signal">{trial.name || "$3 All-Access Trial"}</div>
                <div className="text-white/70 text-sm">${trial.price} one-time · everything through Pro</div>
              </div>
            </div>
            <div className="flex-1 text-sm text-white/80 leading-relaxed hidden sm:block">
              Unlock Creator Studio, Ghost Producer, every course, and AI-ready tools for 3 days. Reverts automatically — never auto-charges.
            </div>
            <button
              onClick={() => checkout(trial.key, trial.name)}
              disabled={buying === trial.key}
              data-testid="buy-trial"
              className="shrink-0 font-black text-sm px-6 py-3 rounded-xl whitespace-nowrap disabled:opacity-60"
              style={{ background: "#E8A51E", color: "#0a0a0a" }}
            >
              {buying === trial.key ? <Loader2 className="w-4 h-4 animate-spin" /> : `Buy the $3 Trial`}
            </button>
          </div>
        )}

        {/* ── 2. Membership tiers ── */}
        <div className="mb-10">
          <div className="flex items-center justify-between gap-3 mb-4">
            <h2 className="font-heading text-xl font-bold text-ink">Memberships</h2>
            <span className="text-[10px] font-black uppercase tracking-widest bg-green-100 text-green-800 px-2 py-0.5 rounded-full">
              One click to checkout
            </span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4" data-testid="store-memberships">
            {paidPlans.map((p) => (
              <div key={p.key} className="card-flat p-5 flex flex-col">
                <div className="overline text-ink/40">{p.name}</div>
                <div className="flex items-end gap-1 mt-1">
                  <span className="font-heading font-black text-3xl text-ink">${p.price}</span>
                  <span className="text-ink/50 text-sm mb-1">{p.period}</span>
                </div>
                <div className="text-sm text-ink/60 mt-1">{p.tagline}</div>
                <ul className="space-y-1.5 mt-3 flex-1">
                  {p.features.slice(0, 3).map((f) => (
                    <li key={f} className="flex items-start gap-2 text-xs text-ink/80">
                      <Check className="w-3.5 h-3.5 text-copper mt-0.5 shrink-0" /> {f}
                    </li>
                  ))}
                </ul>
                <button
                  onClick={() => checkout(p.key, p.name)}
                  disabled={buying === p.key}
                  data-testid={`buy-${p.key}`}
                  className="btn-copper text-sm mt-4 disabled:opacity-60"
                >
                  {buying === p.key ? <Loader2 className="w-4 h-4 animate-spin" /> : `Buy ${p.name} — $${p.price}/mo`}
                </button>
              </div>
            ))}
            {freePlan && (
              <div className="card-flat p-5 flex flex-col border-dashed">
                <div className="overline text-ink/40">{freePlan.name}</div>
                <div className="flex items-end gap-1 mt-1">
                  <span className="font-heading font-black text-3xl text-ink">Free</span>
                </div>
                <div className="text-sm text-ink/60 mt-1">{freePlan.tagline}</div>
                <ul className="space-y-1.5 mt-3 flex-1">
                  {freePlan.features.slice(0, 3).map((f) => (
                    <li key={f} className="flex items-start gap-2 text-xs text-ink/80">
                      <Check className="w-3.5 h-3.5 text-copper mt-0.5 shrink-0" /> {f}
                    </li>
                  ))}
                </ul>
                {!user ? (
                  <Link to="/register" className="btn-primary text-sm mt-4 text-center" data-testid="register-free">
                    Start Free
                  </Link>
                ) : (
                  <div className="text-xs text-ink/40 mt-4 text-center">You're on this tier or higher</div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* ── 3. Creator products ── */}
        <div className="mb-10">
          <div className="flex items-center justify-between gap-3 mb-4">
            <h2 className="font-heading text-xl font-bold text-ink flex items-center gap-2">
              <ShoppingBag className="w-5 h-5 text-copper" /> Creator Products
            </h2>
            <span className="text-[10px] font-black uppercase tracking-widest bg-green-100 text-green-800 px-2 py-0.5 rounded-full">
              Sold here · creators keep 70%
            </span>
          </div>

          {catalogError && (
            <div className="card-flat p-6 text-sm text-destructive flex items-center gap-2" data-testid="store-catalog-error">
              <AlertTriangle className="w-4 h-4 shrink-0" /> {catalogError}
            </div>
          )}

          {!catalogError && products === null && (
            <div className="text-sm text-ink/50 py-6"><Loader2 className="w-4 h-4 inline animate-spin mr-2" />Loading products…</div>
          )}

          {!catalogError && Array.isArray(products) && products.length === 0 && (
            <div className="card-flat p-6 text-sm text-ink/60" data-testid="store-empty">
              No creator products published yet. Creators publish digital products from the Creator Studio and they appear here instantly.
            </div>
          )}

          {!catalogError && Array.isArray(products) && products.length > 0 && (
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
                      onClick={() => buyProduct(p)}
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

        {/* ── 5. Free Starter Library ── */}
        {!isStore && (
        <div className="mb-10">
          <div className="flex items-center justify-between gap-3 mb-4">
            <h2 className="font-heading text-xl font-bold text-ink flex items-center gap-2">
              <BookOpen className="w-5 h-5 text-copper" /> Free Starter Library
            </h2>
            <span className="text-[10px] font-black uppercase tracking-widest bg-green-100 text-green-800 px-2 py-0.5 rounded-full">
              Read now · no purchase needed
            </span>
          </div>
          <p className="text-sm text-ink/60 mb-6">
            Practical guides on ownership, AI, community funding, and building real things. Free to read — no account required.
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {STARTER_LIBRARY.map((book) => (
              <div key={book.slug} className="card-flat p-5 flex flex-col">
                <div className="overline text-ink/40">{book.priceLabel}</div>
                <div className="font-heading font-bold text-lg text-ink mt-1">{book.title}</div>
                <div className="text-sm text-ink/60 mt-1">{book.subtitle}</div>
                {book.description && (
                  <div className="text-sm text-ink/60 mt-2 flex-1" style={{ display: "-webkit-box", WebkitLineClamp: 3, WebkitBoxOrient: "vertical", overflow: "hidden" }}>
                    {book.description}
                  </div>
                )}
                <div className="flex items-center justify-between mt-4 pt-3 border-t border-ink/10">
                  <div className="flex items-center gap-2 text-xs text-ink/50">
                    <span className="flex items-center gap-1">
                      <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                      {book.readTime}
                    </span>
                  </div>
                  <a
                    href={`/api/media/content/starter-library/${book.slug}.md`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1.5 text-xs font-bold text-copper hover:text-copper/80 transition-colors"
                  >
                    Read <Download className="w-3 h-3" />
                  </a>
                </div>
              </div>
            ))}
          </div>
        </div>
        )}

        {/* ── 4. External storefront — secondary venue ── */}
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

        {/* ── Store view: show paid items first, then free library below them ── */}
        {isStore && (
          <div className="mt-10">
            <div className="flex items-center justify-between gap-3 mb-4">
              <h2 className="font-heading text-xl font-bold text-ink flex items-center gap-2">
                <BookOpen className="w-5 h-5 text-copper" /> Free Starter Library
              </h2>
              <span className="text-[10px] font-black uppercase tracking-widest bg-green-100 text-green-800 px-2 py-0.5 rounded-full">
                Read now · no purchase needed
              </span>
            </div>
            <p className="text-sm text-ink/60 mb-6">
              Practical guides on ownership, AI, community funding, and building real things. Free to read — no account required.
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {STARTER_LIBRARY.map((book) => (
                <div key={book.slug} className="card-flat p-5 flex flex-col">
                  <div className="overline text-ink/40">{book.priceLabel}</div>
                  <div className="font-heading font-bold text-lg text-ink mt-1">{book.title}</div>
                  <div className="text-sm text-ink/60 mt-1">{book.subtitle}</div>
                  {book.description && (
                    <div className="text-sm text-ink/60 mt-2 flex-1" style={{ display: "-webkit-box", WebkitLineClamp: 3, WebkitBoxOrient: "vertical", overflow: "hidden" }}>
                      {book.description}
                    </div>
                  )}
                  <div className="flex items-center justify-between mt-4 pt-3 border-t border-ink/10">
                    <div className="flex items-center gap-2 text-xs text-ink/50">
                      <span className="flex items-center gap-1">
                        <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                        {book.readTime}
                      </span>
                    </div>
                    <a
                      href={`/api/media/content/starter-library/${book.slug}.md`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1.5 text-xs font-bold text-copper hover:text-copper/80 transition-colors"
                    >
                      Read <Download className="w-3 h-3" />
                    </a>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        <p className="text-xs text-ink/40 mt-4">
          Digital products and memberships are available now. Physical merchandise is not yet available.
        </p>
      </div>
    </AppShell>
  );
}
