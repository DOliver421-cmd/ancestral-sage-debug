import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import PublicNav from "../components/PublicNav";
import BackButton from "../components/BackButton";
import { api } from "../lib/api";

// Fallback list — only entries with real profile pages in the hardcoded registry.
// Nova Highborn was removed: no DB profile and no hardcoded entry → caused 404s.
const FALLBACK_CREATORS = [
  { slug: "nam-oshun", displayName: "NAM Oshun", title: "Poet · Community Organizer", bio: "Founding voice of the M.O.R.E. Help Center. Words that heal. Community that holds.", avatar: "🌊" },
  { slug: "royal-black-falcon", displayName: "Royal Black Falcon", title: "Poet · Cultural Warrior", bio: "A griot in the tradition that doesn't need to announce itself.", avatar: "🦅" },
];

export default function Creators() {
  const [creators, setCreators] = useState(null);

  useEffect(() => {
    api.get("/creator/profiles/public")
      .then(r => setCreators(r.data.profiles || []))
      .catch(() => setCreators([]));
  }, []);

  const list = creators && creators.length > 0 ? creators : (creators === null ? null : FALLBACK_CREATORS);

  return (
    <div className="min-h-screen bg-bone">
      <PublicNav />
      <div className="max-w-5xl mx-auto px-6 py-10">
        <BackButton to="/" />
        <div className="mt-6">
          <div className="overline text-copper">Creators & Partners</div>
          <h1 className="font-heading text-4xl font-bold text-ink mt-2">The voices of the movement</h1>
          <p className="text-ink/60 mt-3 max-w-2xl">Poets, artists, and builders who own their work and lift the community with it.</p>
        </div>

        {list === null ? (
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-8">
            {[1, 2].map(i => (
              <div key={i} className="card-flat p-6 animate-pulse">
                <div className="w-12 h-12 rounded-full bg-ink/10 mx-auto" />
                <div className="h-4 bg-ink/10 rounded mt-3 mx-auto w-3/4" />
                <div className="h-3 bg-ink/5 rounded mt-2 mx-auto w-1/2" />
              </div>
            ))}
          </div>
        ) : list.length === 0 ? (
          <div className="text-center py-16 border border-dashed border-copper/30 rounded-2xl mt-8">
            <p className="text-ink/50 mb-4">No creator profiles published yet.</p>
            <Link to="/register" className="btn-primary inline-flex items-center gap-2">
              Become a Creator
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-8">
            {list.map((c) => (
              <Link key={c.slug} to={`/creator/${c.slug}`} className="card-flat p-6 block text-center hover:border-copper transition-colors">
                <div style={{ fontSize: 48 }}>{c.avatar || "🎨"}</div>
                <div className="font-heading font-bold text-ink text-lg mt-2">{c.displayName || c.name}</div>
                <div className="overline text-copper mt-1">{c.title || c.role}</div>
                <div className="text-sm text-ink/60 mt-2 line-clamp-3">{c.bio}</div>
                <div className="text-sm font-bold text-copper mt-3">View Profile →</div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
