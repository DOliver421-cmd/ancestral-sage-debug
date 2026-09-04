import { useState } from "react";
import { Link } from "react-router-dom";
import PublicNav from "../components/PublicNav";
import BackButton from "../components/BackButton";
import { api } from "../lib/api";
import { Search, Sparkles, ArrowRight, BookOpen, FileText, Tag, Compass } from "lucide-react";

const TYPE_LABEL = {
  guide: "Guide",
  policy: "Policy",
  product: "Product",
  feature: "Feature",
  answer: "Knowledge",
  resource: "Resource",
};

const TYPE_COLOR = {
  guide: "#047857",
  policy: "#b45309",
  product: "#1d4ed8",
  feature: "#6d28d9",
  answer: "#be185d",
  resource: "#0f766e",
};

export default function KnowledgeFinder() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [upgrade, setUpgrade] = useState(null);
  const [searched, setSearched] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const doSearch = async (e, term) => {
    e?.preventDefault();
    const q = (term ?? query).trim();
    if (!q) return;
    setBusy(true);
    setError("");
    try {
      const { data } = await api.get(`/ai/knowledge/search?q=${encodeURIComponent(q)}`);
      setResults(data.results || []);
      setUpgrade(data.upgrade_prompt || null);
      setSearched(true);
    } catch {
      setError("Search is temporarily unavailable. Please try again in a moment.");
      setResults([]);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="min-h-screen bg-bone">
      <PublicNav />
      <div className="max-w-5xl mx-auto px-6 py-10">
        <BackButton to="/" />
        <div className="mt-6">
          <div className="overline text-copper mb-2 flex items-center gap-2">
            <Compass className="w-4 h-4" /> Knowledge Finder
          </div>
          <h1 className="font-heading text-4xl font-bold text-ink mt-2">
            Search the platform — without AI
          </h1>
          <p className="text-ink/60 mt-3 max-w-2xl">
            Find lessons, tools, resources, courses, policies, and answers from the platform's
            indexed knowledge. Free for everyone, no account required, no AI involved — it's a
            direct search of what the platform actually offers.
          </p>
        </div>

        {/* Search box */}
        <form onSubmit={doSearch} className="mt-8 flex gap-3">
          <div className="flex-1 relative">
            <Search className="w-5 h-5 absolute left-4 top-1/2 -translate-y-1/2 text-ink/40" />
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Try “music production”, “refunds”, “courses”, “byok”…"
              className="w-full rounded-xl border-2 border-ink/10 bg-white pl-12 pr-4 py-3.5 text-ink placeholder:text-ink/35 focus:outline-none focus:border-copper"
              maxLength={300}
            />
          </div>
          <button
            type="submit"
            disabled={busy || !query.trim()}
            className="px-6 py-3 rounded-xl font-bold text-sm uppercase tracking-widest text-white bg-ink hover:bg-ink/85 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {busy ? "Searching…" : "Search"}
          </button>
        </form>

        {error && <p className="mt-4 text-sm text-red-700">{error}</p>}

        {/* Results */}
        {searched && !busy && (
          <div className="mt-8">
            {results.length === 0 ? (
              <div className="rounded-2xl border border-ink/10 bg-white p-8 text-center">
                <p className="text-ink/70">
                  No matches in the knowledge base for “{query}”.
                </p>
                <p className="text-ink/50 text-sm mt-2">
                  Try different words, or search the Help Center for human support.
                </p>
                {upgrade && (
                  <div className="mt-6 rounded-xl bg-amber-50 border border-amber-300 p-4 text-sm text-amber-900 text-left">
                    <Sparkles className="w-4 h-4 inline mr-1 -mt-0.5" />
                    {upgrade}
                  </div>
                )}
              </div>
            ) : (
              <>
                <div className="flex items-center justify-between mb-4">
                  <p className="text-sm text-ink/50">
                    {results.length} result{results.length !== 1 ? "s" : ""} for “{query}”
                  </p>
                </div>
                <ul className="space-y-3">
                  {results.map((r, i) => (
                    <li key={i}>
                      <Link
                        to={r.route || "/"}
                        className="group block rounded-2xl border border-ink/10 bg-white p-5 hover:border-copper hover:shadow-md transition-all"
                      >
                        <div className="flex items-center gap-3">
                          <span
                            className="inline-flex items-center gap-1.5 text-[11px] font-black uppercase tracking-wider px-2 py-0.5 rounded-full text-white"
                            style={{ background: TYPE_COLOR[r.type] || "#6b7280" }}
                          >
                            {r.type === "guide" ? <BookOpen className="w-3 h-3" /> : <FileText className="w-3 h-3" />}
                            {TYPE_LABEL[r.type] || r.type}
                          </span>
                          <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-ink/40 uppercase tracking-wider">
                            <Tag className="w-3 h-3" /> {r.category || "platform"}
                          </span>
                        </div>
                        <h3 className="font-heading font-bold text-lg text-ink mt-2 group-hover:text-copper transition-colors">
                          {r.title}
                        </h3>
                        {r.snippet && (
                          <p className="text-sm text-ink/60 mt-1 line-clamp-2">{r.snippet}</p>
                        )}
                        {r.route && (
                          <span className="inline-flex items-center gap-1 text-sm text-copper font-semibold mt-2">
                            {r.route} <ArrowRight className="w-3.5 h-3.5" />
                          </span>
                        )}
                      </Link>
                    </li>
                  ))}
                </ul>
                {upgrade && (
                  <div className="mt-6 rounded-xl bg-amber-50 border border-amber-300 p-4 text-sm text-amber-900">
                    <Sparkles className="w-4 h-4 inline mr-1 -mt-0.5" />
                    {upgrade}
                    <Link to="/byok" className="font-bold underline ml-2 hover:text-amber-700">
                      Unlock AI →
                    </Link>
                  </div>
                )}
              </>
            )}
          </div>
        )}

        {/* Suggested topics for first-time visitors */}
        {!searched && (
          <div className="mt-10">
            <p className="text-xs font-black uppercase tracking-widest text-ink/40 mb-3">
              Try searching for
            </p>
            <div className="flex flex-wrap gap-2">
              {["Courses", "BYOK", "Refund policy", "Certificates", "Music", "Scholarships", "Community", "Tiers"].map((t) => (
                <button
                  key={t}
                  onClick={() => { setQuery(t); doSearch(null, t); }}
                  className="px-4 py-2 rounded-full border border-ink/15 bg-white text-sm text-ink/70 hover:border-copper hover:text-copper transition-colors"
                >
                  {t}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
