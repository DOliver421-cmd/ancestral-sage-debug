import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Search, Loader2, BookOpen, ShoppingBag, MessageSquare, FileText } from "lucide-react";
import AppShell from "../components/AppShell";
import BackButton from "../components/BackButton";
import { api } from "../lib/api";
import { STARTER_LIBRARY } from "../lib/contentLibrary";

/**
 * Resource Finder — one search box over everything the platform already has:
 *  - Free starter-library books (static registry, filtered client-side)
 *  - Store products / creator products (live /api/finder/search)
 *  - Community posts (live /api/finder/search)
 *
 * Every result links to where the thing actually lives. No dead ends.
 */
const KIND_META = {
  book: { icon: BookOpen, label: "Book" },
  product: { icon: ShoppingBag, label: "Product" },
  post: { icon: MessageSquare, label: "Post" },
  library: { icon: FileText, label: "Free Guide" },
};

export default function ResourceFinder() {
  const [q, setQ] = useState("");
  const [live, setLive] = useState(null);
  const [loading, setLoading] = useState(false);

  const term = q.trim().toLowerCase();

  // Static starter-library results (always instant)
  const libraryHits = useMemo(() => {
    if (!term) return [];
    return STARTER_LIBRARY.filter(b =>
      [b.title, b.subtitle, b.description, ...(b.tags || [])]
        .join(" ").toLowerCase().includes(term)
    ).slice(0, 8);
  }, [term]);

  // Live results (products + posts)
  useEffect(() => {
    if (!term) { setLive(null); return; }
    const t = setTimeout(async () => {
      setLoading(true);
      try {
        const { data } = await api.get("/finder/search", { params: { q: q.trim(), limit: 8 } });
        setLive(data.results || []);
      } catch {
        setLive([]);
      } finally {
        setLoading(false);
      }
    }, 300);
    return () => clearTimeout(t);
  }, [q, term]);

  const empty = term && !loading && libraryHits.length === 0 && (!live || live.length === 0);

  return (
    <AppShell>
      <div className="min-h-screen bg-bone">
        <div className="max-w-3xl mx-auto px-4 py-10">
          <BackButton to="/" />
          <h1 className="font-heading text-3xl font-bold text-ink mb-2">Resource Finder</h1>
          <p className="text-ink/60 mb-6">
            One search across the free library, the store, and the community.
          </p>

          <div className="relative mb-8">
            <Search size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-ink/40" />
            <input
              autoFocus
              value={q}
              onChange={e => setQ(e.target.value)}
              placeholder="Search books, products, community posts…"
              className="w-full border border-ink/15 rounded-xl pl-11 pr-4 py-3 text-sm bg-white focus:border-copper outline-none"
            />
            {loading && <Loader2 size={16} className="absolute right-4 top-1/2 -translate-y-1/2 animate-spin text-copper" />}
          </div>

          {empty && (
            <p className="text-sm text-ink/50 bg-white rounded-xl border border-ink/10 p-5">
              Nothing found for “{q}”. Try a shorter word — or ask Helper AI at <Link to="/helper" className="text-copper font-bold">/helper</Link>.
            </p>
          )}

          {/* Free starter library */}
          {libraryHits.length > 0 && (
            <section className="mb-8">
              <h2 className="overline text-copper mb-3">Free Library</h2>
              <div className="grid sm:grid-cols-2 gap-3">
                {libraryHits.map(b => (
                  <a key={b.slug} href={`/api/media/content/starter-library/${b.slug}.md`} target="_blank" rel="noreferrer"
                    className="card-flat p-4 hover:shadow-md transition-shadow">
                    <div className="font-bold text-sm text-ink">{b.title}</div>
                    <div className="text-xs text-ink/50 mt-1 line-clamp-2">{b.subtitle || b.description}</div>
                    <div className="text-[10px] uppercase tracking-wide text-ink/40 mt-2">Free · {b.readTime}</div>
                  </a>
                ))}
              </div>
            </section>
          )}

          {/* Live results */}
          {live && live.length > 0 && (
            <section>
              <h2 className="overline text-copper mb-3">Store & Community</h2>
              <ul className="bg-white rounded-xl border border-ink/10 divide-y divide-ink/5">
                {live.map((r, i) => {
                  const meta = KIND_META[r.kind] || KIND_META.product;
                  const Icon = meta.icon;
                  return (
                    <li key={`${r.kind}-${r.ref}-${i}`}>
                      <Link to={r.url} className="flex items-start gap-3 px-4 py-3 hover:bg-copper/5 transition-colors">
                        <Icon size={16} className="text-copper mt-0.5 shrink-0" />
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center gap-2">
                            <span className="font-bold text-sm text-ink truncate">{r.title}</span>
                            <span className="text-[10px] uppercase tracking-wide text-ink/40 shrink-0">{meta.label}</span>
                          </div>
                          {r.snippet && <p className="text-xs text-ink/50 mt-0.5 line-clamp-2">{r.snippet}</p>}
                        </div>
                      </Link>
                    </li>
                  );
                })}
              </ul>
            </section>
          )}

          {!term && (
            <p className="text-sm text-ink/50 bg-white rounded-xl border border-ink/10 p-5">
              Start typing to search {STARTER_LIBRARY.length} free guides, the full store catalog, and community posts — all from one place.
            </p>
          )}
        </div>
      </div>
    </AppShell>
  );
}
