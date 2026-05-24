import { Link } from "react-router-dom";
import PublicNav from "../components/PublicNav";
import BackButton from "../components/BackButton";

// Public creators index → existing /creator/:slug profile pages (real route).
// Emoji avatars are placeholders; real representation/photos are the user's call.
const CREATORS = [
  { slug: "nam-oshun", name: "NAM Oshun", role: "Poet · Community Organizer", bio: "Founding voice of the M.O.R.E. Help Center. Words that heal. Community that holds.", avatar: "🌊" },
  { slug: "royal-black-falcon", name: "Royal Black Falcon", role: "Poet · Cultural Warrior", bio: "A griot in the tradition that doesn't need to announce itself.", avatar: "🦅" },
  { slug: "nova-highborn", name: "Nova Highborn", role: "Visual Artist · Digital Creator", bio: "Visual art that speaks before it's explained. Poetry that arrives like light.", avatar: "✨" },
];

export default function Creators() {
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
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-8">
          {CREATORS.map((c) => (
            <Link key={c.slug} to={`/creator/${c.slug}`} className="card-flat p-6 block text-center">
              <div style={{ fontSize: 48 }}>{c.avatar}</div>
              <div className="font-heading font-bold text-ink text-lg mt-2">{c.name}</div>
              <div className="overline text-copper mt-1">{c.role}</div>
              <div className="text-sm text-ink/60 mt-2">{c.bio}</div>
              <div className="text-sm font-bold text-copper mt-3">View Profile →</div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
