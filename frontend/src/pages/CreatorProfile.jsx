import { Link, useParams } from "react-router-dom";
import { useState, useEffect } from "react";
import { Heart, Instagram, ExternalLink, ShoppingBag, Music, BookOpen, Users, ArrowRight, Shield, Mic, Star, Pencil } from "lucide-react";
import { WAI_LOGO, BRAND } from "../lib/brand";
import BugReportModal from "../components/BugReportModal";
import TrackPlayer from "../components/TrackPlayer";
import SharePanel from "../components/SharePanel";
import { api } from "../lib/api";

// ── Icon helper ─────────────────────────────────────────────────────────────
function SocialIcon({ type, className }) {
  if (type === "instagram") return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/>
    </svg>
  );
  if (type === "facebook-page") return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
    </svg>
  );
  if (type === "wai") return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
    </svg>
  );
  return <ExternalLink className={className} />;
}

// Normalize a DB profile doc to match the shape the render tree expects
function dbToCreator(p) {
  return {
    slug: p.slug,
    displayName: p.display_name,
    title: p.title || "",
    tagline: p.tagline || "",
    bio: p.bio || "",
    pronouns: p.pronouns || "",
    location: p.location || "",
    avatar: p.avatar || "✨",
    bannerColor: "from-amber-900 via-amber-800 to-ink",
    accentColor: "amber",
    socials: (p.socials || []).map(s => ({ platform: s.platform, handle: s.handle, url: s.url, note: s.note })),
    moreOfferings: (p.more_offerings || []).map(o => ({ icon: o.icon, title: o.title, desc: o.desc })),
    commerce: (p.commerce || []).map(c => ({ label: c.label, desc: c.desc, url: c.url, placeholder: false })),
    waiStatus: { tier: "CREATOR", role: "Creator", since: new Date(p.created_at || Date.now()).getFullYear().toString(), bio: "" },
    _dbUserId: p.user_id,
  };
}

export default function CreatorProfile() {
  const { slug } = useParams();
  const [dbProfile, setDbProfile] = useState(undefined); // undefined = loading, null = not found

  useEffect(() => {
    api.get(`/creator/profile/${slug}`)
      .then(r => setDbProfile(r.data.profile))
      .catch(() => setDbProfile(null));
  }, [slug]);

  if (dbProfile === undefined) {
    return (
      <div className="min-h-screen bg-bone flex items-center justify-center">
        <div className="text-ink/40 text-sm">Loading profile…</div>
      </div>
    );
  }

  const creator = dbProfile ? dbToCreator(dbProfile) : null;

  if (!creator) {
    return (
      <div className="min-h-screen bg-bone flex flex-col items-center justify-center gap-6 text-ink">
        <div className="text-6xl">🌊</div>
        <h1 className="font-heading text-3xl font-bold">Creator not found</h1>
        <p className="text-ink/60">This profile doesn't exist yet — or will soon.</p>
        <Link to="/more" className="inline-flex items-center gap-2 bg-amber-500 hover:bg-amber-400 text-ink font-bold px-6 py-3 rounded-xl transition-all">
          <Heart className="w-4 h-4" /> Visit M.O.R.E. Hub
        </Link>
      </div>
    );
  }

  // is_owner is set by the backend based on the JWT — never trust user_id from the response
  const isOwner = dbProfile && dbProfile.is_owner === true;

  return (
    <div className="min-h-screen bg-bone text-ink">

      {/* Top nav */}
      <header className="border-b border-ink/10 bg-bone sticky top-0 z-40">
        <div className="max-w-5xl mx-auto px-6 py-3 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2">
            <img src={WAI_LOGO} alt="W.A.I." className="w-9 h-9 object-contain" style={{ mixBlendMode: "multiply" }} />
            <span className="font-heading font-bold text-sm hidden sm:block">{BRAND.name}</span>
          </Link>
          <div className="flex items-center gap-3">
            {isOwner && (
              <Link
                to={`/creator/profile/edit`}
                className="flex items-center gap-1.5 text-xs font-bold text-copper border border-copper/40 hover:border-copper px-3 py-1.5 rounded-full transition-colors"
              >
                <Pencil className="w-3 h-3" /> Edit Profile
              </Link>
            )}
            <Link to="/more" className="flex items-center gap-1.5 text-xs font-bold text-amber-700 hover:text-amber-600 border border-amber-300 hover:border-amber-500 px-3 py-1.5 rounded-full transition-colors">
              <Heart className="w-3 h-3" /> M.O.R.E. Hub
            </Link>
            <Link to="/register" className="text-xs font-bold bg-ink text-white px-4 py-1.5 rounded-full hover:bg-ink/80 transition-colors">
              Join Free
            </Link>
          </div>
        </div>
      </header>

      {/* Hero banner */}
      <div className={`bg-gradient-to-br ${creator.bannerColor} text-white`}>
        <div className="max-w-5xl mx-auto px-6 py-16">
          <div className="flex flex-col sm:flex-row items-start sm:items-end gap-6">
            {/* Avatar */}
            <div className="w-28 h-28 rounded-full bg-white/10 border-4 border-white/20 flex items-center justify-center text-6xl shrink-0 shadow-2xl">
              {creator.avatar}
            </div>

            {/* Identity */}
            <div className="flex-1">
              <div className="text-white/60 text-sm font-medium mb-1 uppercase tracking-widest">{creator.pronouns} · {creator.location}</div>
              <h1 className="font-heading text-5xl sm:text-6xl font-extrabold leading-none mb-2 tracking-tight">
                {creator.displayName}
              </h1>
              <p className="text-white/80 text-base font-medium mb-3">{creator.title}</p>
              <p className="text-white/60 text-sm italic">"{creator.tagline}"</p>
            </div>

            {/* WAI badge */}
            {creator.waiStatus && (
              <div className="shrink-0 bg-white/10 border border-white/20 rounded-2xl px-5 py-4 text-right">
                <div className="text-white/50 text-xs uppercase tracking-widest mb-1">WAI-Institute</div>
                <div className="text-white font-bold text-sm">{creator.waiStatus.role}</div>
                <div className="text-amber-300 text-xs font-bold mt-0.5">{creator.waiStatus.tier} Member</div>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-6 py-12 space-y-12">

        {/* Bio + socials */}
        <div className="grid lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2">
            <h2 className="font-heading font-extrabold text-2xl mb-4">About</h2>
            {creator.bio.split("\n\n").map((para, i) => (
              <p key={i} className="text-ink/70 leading-relaxed mb-4 text-base">{para.trim()}</p>
            ))}
          </div>

          {/* Social links */}
          <div>
            <h2 className="font-heading font-extrabold text-2xl mb-4">Connect</h2>
            <div className="space-y-3">
              {creator.socials.map((s) => (
                <a
                  key={s.platform}
                  href={s.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-3 p-3 bg-white rounded-xl border border-ink/10 hover:border-amber-300 hover:shadow-sm transition-all group"
                >
                  <div className={`w-10 h-10 rounded-lg ${s.color} flex items-center justify-center shrink-0`}>
                    <SocialIcon type={s.icon} className="w-5 h-5 text-white" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="font-bold text-sm truncate">{s.platform}</div>
                    <div className="text-ink/50 text-xs">{s.handle}</div>
                    {s.note && <div className="text-ink/40 text-xs mt-0.5 leading-tight">{s.note}</div>}
                  </div>
                  <ExternalLink className="w-3.5 h-3.5 text-ink/30 group-hover:text-amber-500 transition-colors shrink-0" />
                </a>
              ))}

              {/* WAI profile link */}
              <Link
                to="/register"
                className="flex items-center gap-3 p-3 bg-amber-50 rounded-xl border border-amber-200 hover:border-amber-400 hover:shadow-sm transition-all group"
              >
                <div className="w-10 h-10 rounded-lg bg-amber-500 flex items-center justify-center shrink-0">
                  <img src={WAI_LOGO} alt="WAI" className="w-6 h-6 object-contain" style={{ mixBlendMode: "multiply" }} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="font-bold text-sm text-amber-800">WAI-Institute Profile</div>
                  <div className="text-amber-700/60 text-xs">Join to connect & collaborate</div>
                </div>
                <ArrowRight className="w-3.5 h-3.5 text-amber-400 group-hover:text-amber-600 transition-colors shrink-0" />
              </Link>
            </div>
          </div>
        </div>

        {/* Share this profile */}
        <div className="bg-amber-50 border border-amber-200 rounded-2xl p-6">
          <h2 className="font-heading font-extrabold text-xl mb-1">Share This Profile</h2>
          <p className="text-ink/50 text-sm mb-4">Copy a link, share to social, or embed anywhere.</p>
          <SharePanel
            url={`/creators/${creator.slug}`}
            title={`${creator.displayName} — WAI-Institute Creator`}
            embed
          />
        </div>

        {/* M.O.R.E. Skill Offerings */}
        {creator.moreOfferings.length > 0 && (
          <div>
            <div className="flex items-center gap-3 mb-6">
              <div className="w-8 h-8 rounded-full bg-amber-100 border border-amber-300 flex items-center justify-center">
                <Heart className="w-4 h-4 text-amber-600" />
              </div>
              <div>
                <h2 className="font-heading font-extrabold text-2xl leading-none">M.O.R.E. Skill Exchange</h2>
                <p className="text-ink/50 text-sm">What {creator.displayName} offers the community — free through the M.O.R.E. Help Center</p>
              </div>
            </div>

            <div className="grid md:grid-cols-3 gap-4">
              {creator.moreOfferings.map((offering) => (
                <div key={offering.title} className="bg-white border-2 border-amber-100 hover:border-amber-300 rounded-2xl p-6 transition-colors">
                  <div className="text-4xl mb-3">{offering.icon}</div>
                  <h3 className="font-heading font-bold text-lg mb-2">{offering.title}</h3>
                  <p className="text-ink/60 text-sm leading-relaxed mb-4">{offering.desc}</p>
                  <Link to="/more" className="inline-flex items-center gap-1.5 text-xs font-bold text-amber-700 hover:text-amber-600 transition-colors">
                    Request in M.O.R.E. <ArrowRight className="w-3 h-3" />
                  </Link>
                </div>
              ))}
            </div>

            <div className="mt-4 p-4 bg-amber-50 border border-amber-200 rounded-xl flex items-center gap-3">
              <Shield className="w-5 h-5 text-amber-600 shrink-0" />
              <p className="text-amber-800 text-sm">
                All skill exchange requests go through the M.O.R.E. Help Center and are protected by Oliver Guardian.
                No money changes hands — this is community exchange.
              </p>
            </div>
          </div>
        )}

        {/* Music tracks — shown when creator has tracks with at least one URL */}
        {creator.tracks?.filter(t => t.original_url || t.ai_url).length > 0 && (
          <div>
            <div className="flex items-center gap-3 mb-6">
              <div className="w-8 h-8 rounded-full bg-violet-100 border border-violet-300 flex items-center justify-center">
                <Music className="w-4 h-4 text-violet-600" />
              </div>
              <div>
                <h2 className="font-heading font-extrabold text-2xl leading-none">Music</h2>
                <p className="text-ink/50 text-sm">Original voice recordings + AI-assisted versions — toggle between them</p>
              </div>
            </div>
            <div className="grid sm:grid-cols-2 gap-4">
              {creator.tracks.filter(t => t.original_url || t.ai_url).map(track => (
                <TrackPlayer key={track.id} track={track} accentColor={creator.accentColor} />
              ))}
            </div>
          </div>
        )}

        {/* Playlist curation gateway — shown when creator has it enabled */}
        {creator.playlistCuration?.enabled && (
          <div className="bg-gradient-to-br from-emerald-950 via-teal-900 to-ink text-white rounded-2xl overflow-hidden">
            <div className="p-8">
              <div className="text-xs font-bold uppercase tracking-widest text-emerald-400 mb-3">🎵 Playlist Curation</div>
              <h2 className="font-heading text-2xl font-extrabold mb-3 leading-tight">{creator.playlistCuration.headline}</h2>
              <p className="text-white/70 text-sm leading-relaxed mb-6">{creator.playlistCuration.desc}</p>
              <div className="grid sm:grid-cols-3 gap-3 mb-6 text-xs text-white/60">
                {[
                  { icon: "✅", text: "Save the playlist" },
                  { icon: "❤️", text: "Follow the playlist" },
                  { icon: "➕", text: "Add required song" },
                  { icon: "🎤", text: "Follow on Spotify" },
                  { icon: "📤", text: "Share the playlist" },
                  { icon: "🎶", text: "Get reviewed & placed" },
                ].map(({ icon, text }) => (
                  <div key={text} className="flex items-center gap-2 bg-white/5 rounded-lg px-3 py-2">
                    <span>{icon}</span><span>{text}</span>
                  </div>
                ))}
              </div>
              <Link
                to={creator.playlistCuration.submitPath}
                className="inline-flex items-center gap-2 bg-emerald-500 hover:bg-emerald-400 text-ink font-bold px-6 py-3 rounded-xl transition-all hover:scale-105"
              >
                Submit Your Song — Free <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          </div>
        )}

        {/* Store / Merch / Commerce */}
        <div>
          <div className="flex items-center gap-3 mb-6">
            <div className="w-8 h-8 rounded-full bg-ink/10 flex items-center justify-center">
              <ShoppingBag className="w-4 h-4 text-ink" />
            </div>
            <div>
              <h2 className="font-heading font-extrabold text-2xl leading-none">Work & Offerings</h2>
              <p className="text-ink/50 text-sm">Books, workshops, courses, and ways to support the work</p>
            </div>
          </div>

          <div className="grid md:grid-cols-3 gap-4">
            {creator.commerce.map((item) => (
              <div key={item.label} className={`bg-white rounded-2xl border-2 p-6 flex flex-col ${item.placeholder ? "border-ink/10 opacity-75" : "border-ink/10 hover:border-amber-300 transition-colors"}`}>
                <div className="flex items-start justify-between mb-3">
                  <h3 className="font-heading font-bold text-base">{item.label}</h3>
                  {item.placeholder && (
                    <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-ink/5 text-ink/40 border border-ink/10 whitespace-nowrap ml-2">Coming Soon</span>
                  )}
                </div>
                <p className="text-ink/60 text-sm leading-relaxed flex-1 mb-4">{item.desc}</p>
                {item.placeholder ? (
                  <div className="text-xs text-ink/30 italic">Available soon</div>
                ) : (
                  <Link to={item.url} className="inline-flex items-center gap-1.5 text-sm font-bold text-ink hover:text-amber-700 transition-colors">
                    View <ArrowRight className="w-3.5 h-3.5" />
                  </Link>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Peer connection — shows when _peerNote exists (Royal Black Falcon ↔ NAM Oshun) */}
        {creator._peerNote && creator._peerSlug && (
          <div className="bg-gradient-to-br from-indigo-950 via-blue-900 to-slate-900 text-white rounded-2xl p-8">
            <div className="text-xs font-bold uppercase tracking-widest text-amber-400 mb-4">Community · Brotherhood · The Work</div>
            <div className="grid sm:grid-cols-2 gap-6 items-center">
              <div>
                <p className="text-white/80 text-base leading-relaxed italic mb-6">
                  "{creator._peerNote}"
                </p>
                <p className="text-white/50 text-sm">
                  Two poets. One mission. Separate stages, same root.
                </p>
              </div>
              <div className="flex flex-col gap-3">
                <div className="text-white/40 text-xs uppercase tracking-widest mb-1">Also in the M.O.R.E. community</div>
                <Link
                  to={`/creator/${creator._peerSlug}`}
                  className="flex items-center gap-4 bg-white/5 border border-white/10 hover:border-amber-400/40 rounded-2xl p-4 transition-all group"
                >
                  <div className="w-12 h-12 rounded-full bg-amber-500/20 border-2 border-amber-400/30 flex items-center justify-center text-2xl shrink-0">
                    {creator._peerAvatar}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="font-heading font-extrabold text-white text-base leading-none mb-1">{creator._peerName}</div>
                    <div className="text-white/50 text-xs">{creator._peerTitle}</div>
                  </div>
                  <ArrowRight className="w-4 h-4 text-white/30 group-hover:text-amber-400 transition-colors shrink-0" />
                </Link>
              </div>
            </div>
          </div>
        )}

        {/* Creator as proof of concept callout */}
        <div className="bg-gradient-to-br from-ink to-ink/90 text-white rounded-2xl overflow-hidden">
          <div className="grid lg:grid-cols-2 gap-0">
            <div className="p-8">
              <div className="text-xs font-bold uppercase tracking-widest text-amber-400 mb-3">Proof of Concept</div>
              <h2 className="font-heading text-3xl font-extrabold mb-4 leading-tight">
                Your artist profile<br />lives here too.
              </h2>
              <p className="text-white/70 text-sm leading-relaxed mb-6">
                Every creator, poet, musician, organizer, and healer in the WAI-Institute community can have a public-facing profile like this one — linking your store, your social media, your M.O.R.E. offerings, all in one place. No algorithm. No extraction. Your page, your terms.
              </p>
              <Link to="/register" className="inline-flex items-center gap-2 bg-amber-500 hover:bg-amber-400 text-ink font-bold px-6 py-3 rounded-xl transition-all hover:scale-105">
                Claim Your Profile <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
            <div className="bg-white/5 border-l border-white/10 p-8 flex flex-col justify-center">
              <div className="space-y-4">
                {[
                  { icon: "🌐", text: "One link for everything — social, store, skills" },
                  { icon: "🤝", text: "Integrated with M.O.R.E. skill exchange" },
                  { icon: "🛡️", text: "Protected by Oliver Guardian" },
                  { icon: "🆓", text: "Free for all community members — always" },
                ].map(({ icon, text }) => (
                  <div key={text} className="flex items-center gap-3 text-sm text-white/70">
                    <span className="text-xl shrink-0">{icon}</span>
                    <span>{text}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

      </div>

      {/* Footer */}
      <footer className="border-t border-ink/10 bg-white mt-12 py-8">
        <div className="max-w-5xl mx-auto px-6 flex flex-col sm:flex-row items-center justify-between gap-4 text-sm text-ink/50">
          <div className="flex items-center gap-2">
            <img src={WAI_LOGO} alt="WAI" className="w-6 h-6 object-contain" style={{ mixBlendMode: "multiply" }} />
            <span>{BRAND.name} · Community Creator Profile</span>
          </div>
          <div className="flex items-center gap-4">
            <Link to="/more" className="hover:text-amber-600 transition-colors font-medium">M.O.R.E. Hub</Link>
            <Link to="/register" className="hover:text-ink transition-colors">Join Free</Link>
            <Link to="/login" className="hover:text-ink transition-colors">Sign In</Link>
          </div>
        </div>
      </footer>

      <BugReportModal />
    </div>
  );
}
