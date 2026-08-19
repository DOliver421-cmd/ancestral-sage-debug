/**
 * SiteSearch — site-wide search for M.O.R.E. Help Center.
 *
 * Two exports:
 *   <SiteSearch />        — full-page search (route: /search)
 *   <SiteSearchModal />   — global command palette, opened with Ctrl/Cmd+K,
 *                           the floating button, or a window "open-site-search"
 *                           event (used by the sidebar / header search buttons).
 *
 * Both call the public backend endpoint GET /api/search?q=…
 */

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate, useSearchParams, Link } from "react-router-dom";
import { api } from "../lib/api";
import {
  Search, X, CornerDownLeft, BookOpen, FlaskConical, Video,
  Music, User, Compass, Loader2, ArrowRight, FileText, Sparkles,
} from "lucide-react";

// ── Result type icons ────────────────────────────────────────────────────────
const TYPE_ICON = {
  page: Compass,
  module: BookOpen,
  lab: FlaskConical,
  course: Video,
  product: Music,
  creator: User,
};

const TYPE_LABEL = {
  page: "Page",
  module: "Module",
  lab: "Lab",
  course: "Course",
  product: "Product",
  creator: "Creator",
};

function groupResults(results) {
  const order = ["page", "course", "module", "lab", "product", "instructor"];
  const groups = new Map();
  for (const r of results || []) {
    if (!groups.has(r.type)) groups.set(r.type, []);
    groups.get(r.type).push(r);
  }
  return order
    .filter((t) => groups.has(t))
    .map((t) => ({ type: t, items: groups.get(t).slice(0, 5) }));
}

// ── Shared hook: debounced query → results ──────────────────────────────────
export function useSiteSearch(query, { min = 2 } = {}) {
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const timer = useRef(null);

  useEffect(() => {
    clearTimeout(timer.current);
    const q = (query || "").trim();
    if (q.length < min) {
      setResults([]);
      setLoading(false);
      setSearched(false);
      return;
    }
    setLoading(true);
    timer.current = setTimeout(async () => {
      try {
        const { data } = await api.get("/search", { params: { q, limit: 8 } });
        setResults(data.results || []);
      } catch {
        setResults([]);
      } finally {
        setLoading(false);
        setSearched(true);
      }
    }, 220);
    return () => clearTimeout(timer.current);
  }, [query, min]);

  return { results, loading, searched };
}

// ── Result list (shared by page + modal) ────────────────────────────────────
export function SearchResults({ results, loading, searched, query, onPick }) {
  const groups = useMemo(() => groupResults(results), [results]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-14 text-ink/40">
        <Loader2 className="w-5 h-5 animate-spin text-copper" />
        <span className="ml-2 text-sm">Searching…</span>
      </div>
    );
  }
  if (!searched) {
    return (
      <div className="py-14 text-center text-ink/40">
        <Search className="w-6 h-6 mx-auto mb-3 opacity-40" />
        <p className="text-sm font-medium">Search the whole site</p>
        <p className="text-xs mt-1">Pages · courses · modules · labs · media · creators</p>
      </div>
    );
  }
  if (results.length === 0) {
    return (
      <div className="py-14 text-center text-ink/40">
        <p className="text-sm font-medium">No results for “{query}”</p>
        <p className="text-xs mt-1">Try a different word — like “courses”, “byok”, or “housing”.</p>
      </div>
    );
  }

  return (
    <div className="divide-y divide-ink/5">
      {groups.map((g) => {
        const Icon = TYPE_ICON[g.type] || FileText;
        return (
          <div key={g.type} className="px-2 py-2">
            <p className="px-3 pt-2 pb-1 text-[10px] font-black uppercase tracking-widest text-ink/35">
              {TYPE_LABEL[g.type] || g.type}
            </p>
            {g.items.map((r, i) => (
              <Link
                key={`${r.type}-${i}`}
                to={r.link}
                onClick={onPick}
                className="flex items-start gap-3 px-3 py-2.5 rounded-xl hover:bg-copper/10 transition-colors group"
              >
                <span className="mt-0.5 w-8 h-8 shrink-0 rounded-lg bg-copper/10 text-copper flex items-center justify-center">
                  <Icon className="w-4 h-4" />
                </span>
                <span className="min-w-0 flex-1">
                  <span className="block text-sm font-bold text-ink group-hover:text-copper transition-colors truncate">
                    {r.title}
                  </span>
                  {r.description && (
                    <span className="block text-xs text-ink/50 mt-0.5 line-clamp-2">{r.description}</span>
                  )}
                </span>
                <ArrowRight className="w-4 h-4 text-ink/20 mt-1.5 shrink-0 group-hover:text-copper transition-colors" />
              </Link>
            ))}
          </div>
        );
      })}
    </div>
  );
}

// ── Full page search (route /search) ────────────────────────────────────────
export default function SiteSearch() {
  const [params, setParams] = useSearchParams();
  const navigate = useNavigate();
  const query = params.get("q") || "";
  const { results, loading, searched } = useSiteSearch(query);
  const inputRef = useRef(null);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const submit = (e) => {
    e.preventDefault();
    const q = e.target.elements.q.value.trim();
    if (q) setParams({ q });
  };

  return (
    <div className="min-h-screen bg-bone">
      <div className="border-b border-ink/10 bg-white">
        <div className="max-w-3xl mx-auto px-6 py-10">
          <Link to="/more-help-center" className="text-xs font-bold text-copper hover:underline">
            ← M.O.R.E. Help Center
          </Link>
          <h1 className="font-heading text-3xl font-bold text-ink mt-4 flex items-center gap-3">
            <span className="w-10 h-10 rounded-xl bg-ink text-signal flex items-center justify-center">
              <Search className="w-5 h-5" />
            </span>
            Search the site
          </h1>
          <p className="text-sm text-ink/55 mt-2">
            Find pages, courses, modules, labs, media, and creators — press <kbd className="px-1.5 py-0.5 bg-bone border border-ink/15 rounded text-[11px] font-bold">Ctrl K</kbd> anywhere to search.
          </p>

          <form onSubmit={submit} className="mt-6 relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-ink/35" />
            <input
              ref={inputRef}
              name="q"
              defaultValue={query}
              placeholder="Try “courses”, “byok”, “housing help”, “creator studio”…"
              className="w-full pl-12 pr-12 py-4 text-base bg-white border-2 border-ink/10 rounded-2xl text-ink placeholder-ink/35 focus:outline-none focus:border-copper shadow-sm"
            />
            <button
              type="submit"
              className="absolute right-3 top-1/2 -translate-y-1/2 btn-copper px-4 py-2 rounded-xl text-xs font-black flex items-center gap-1.5"
            >
              Search <CornerDownLeft className="w-3.5 h-3.5" />
            </button>
          </form>
        </div>
      </div>

      <div className="max-w-3xl mx-auto px-6 py-8">
        {query ? (
          <p className="text-xs text-ink/45 mb-3 font-semibold uppercase tracking-wider">
            {searched && !loading ? `${results.length} result${results.length === 1 ? "" : "s"} for “${query}”` : ""}
          </p>
        ) : null}
        <div className="bg-white border border-ink/10 rounded-2xl shadow-sm overflow-hidden">
          <SearchResults
            results={results}
            loading={loading}
            searched={searched}
            query={query}
            onPick={() => navigate(`/search?q=${encodeURIComponent(query)}`)}
          />
        </div>

        {!query && (
          <div className="mt-8 grid sm:grid-cols-2 gap-3">
            {[
              ["Free courses & modules", "/courses"],
              ["Plans & membership", "/plans"],
              ["Bring Your Own Key", "/byok"],
              ["Help with housing, legal, food", "/help-center"],
            ].map(([label, to]) => (
              <Link
                key={to}
                to={to}
                className="flex items-center justify-between bg-white border border-ink/10 rounded-xl px-4 py-3 text-sm font-bold text-ink/70 hover:border-copper/50 hover:text-copper transition-colors"
              >
                {label} <ArrowRight className="w-4 h-4" />
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// ── Global command palette ──────────────────────────────────────────────────
export function SiteSearchModal() {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [activeIdx, setActiveIdx] = useState(-1);
  const navigate = useNavigate();
  const { results, loading, searched } = useSiteSearch(query);
  const panelRef = useRef(null);
  const inputRef = useRef(null);

  const flat = useMemo(() => results, [results]);

  const openModal = useCallback(() => {
    setOpen(true);
    setQuery("");
    setActiveIdx(-1);
  }, []);

  const close = useCallback(() => setOpen(false), []);

  // Global triggers: Ctrl/Cmd+K, floating button, and window events.
  useEffect(() => {
    const onKey = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setOpen((o) => !o);
      }
      if (e.key === "Escape") setOpen(false);
    };
    const onOpenEvent = () => openModal();
    window.addEventListener("keydown", onKey);
    window.addEventListener("open-site-search", onOpenEvent);
    return () => {
      window.removeEventListener("keydown", onKey);
      window.removeEventListener("open-site-search", onOpenEvent);
    };
  }, [openModal]);

  useEffect(() => {
    if (open) setTimeout(() => inputRef.current?.focus(), 30);
  }, [open]);

  useEffect(() => {
    setActiveIdx(-1);
  }, [query]);

  if (!open) {
    return (
      <>
        <button
          onClick={openModal}
          aria-label="Search the site"
          title="Search the site (Ctrl+K)"
          className="fixed bottom-6 left-6 z-50 w-14 h-14 rounded-full shadow-2xl flex items-center justify-center transition-all hover:scale-110 focus:outline-none focus:ring-4 focus:ring-copper/30"
          style={{ background: "linear-gradient(135deg,#1B4332,#2D6A4F)", color: "#fff" }}
        >
          <Search className="w-6 h-6" />
        </button>
        {!open && <div className="pointer-events-none fixed bottom-6 left-6 z-40 opacity-0" aria-hidden />}
      </>
    );
  }

  const pick = (r) => {
    close();
    navigate(r.link);
  };

  const onEnter = (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      if (flat.length > 0) {
        const idx = activeIdx >= 0 ? activeIdx : 0;
        pick(flat[idx]);
      } else if (query.trim().length >= 2) {
        close();
        navigate(`/search?q=${encodeURIComponent(query.trim())}`);
      }
    }
  };

  return (
    <div
      className="fixed inset-0 z-[70] bg-ink/60 backdrop-blur-sm flex items-start justify-center pt-[12vh] px-4"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) close();
      }}
    >
      <div
        ref={panelRef}
        className="w-full max-w-xl bg-white rounded-2xl shadow-2xl border border-ink/10 overflow-hidden animate-fade-in"
        role="dialog"
        aria-label="Site search"
      >
        {/* Input */}
        <div className="flex items-center gap-3 px-5 py-4 border-b border-ink/10">
          <Search className="w-5 h-5 text-ink/35 shrink-0" />
          <input
            ref={inputRef}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={onEnter}
            placeholder="Search pages, courses, modules, labs, creators…"
            className="flex-1 text-base text-ink placeholder-ink/35 focus:outline-none bg-transparent"
          />
          {loading ? (
            <Loader2 className="w-4 h-4 animate-spin text-copper" />
          ) : (
            <button onClick={close} aria-label="Close search" className="text-ink/35 hover:text-ink transition-colors">
              <X className="w-5 h-5" />
            </button>
          )}
        </div>

        {/* Results */}
        <div className="max-h-[52vh] overflow-y-auto py-2" onMouseMove={() => setActiveIdx(-1)}>
          <SearchResults
            results={results}
            loading={loading}
            searched={searched}
            query={query}
            onPick={() => close()}
          />
        </div>

        {/* Footer hints */}
        <div className="flex items-center justify-between px-5 py-3 bg-ink/5 border-t border-ink/5 text-[11px] text-ink/45 font-semibold">
          <span className="flex items-center gap-1.5">
            <kbd className="px-1.5 py-0.5 bg-white border border-ink/15 rounded text-[10px] font-black">Enter</kbd> open
            <kbd className="px-1.5 py-0.5 bg-white border border-ink/15 rounded text-[10px] font-black ml-2">Esc</kbd> close
          </span>
          <span className="flex items-center gap-1">
            <Sparkles className="w-3 h-3 text-copper" />
            <Link to="/site-guide" onClick={close} className="hover:text-copper transition-colors">
              Lost? Ask the Site Guide →
            </Link>
          </span>
        </div>
      </div>
    </div>
  );
}
