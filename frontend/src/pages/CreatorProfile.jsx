import { Link, useParams } from "react-router-dom";
import { useState, useEffect } from "react";
import { Heart, Instagram, ExternalLink, ShoppingBag, Music, BookOpen, Users, ArrowRight, Shield, Mic, Star, Pencil } from "lucide-react";
import { WAI_LOGO, BRAND } from "../lib/brand";
import BugReportModal from "../components/BugReportModal";
import TrackPlayer from "../components/TrackPlayer";
import SharePanel from "../components/SharePanel";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";

// ── Creator registry (proof of concept — one creator hardcoded, architecture is slug-based) ──
const CREATORS = {
  "nam-oshun": {
    slug: "nam-oshun",
    displayName: "NAM Oshun",
    legalName: "Delon Oliver",
    title: "Poet · Spoken Word Artist · Community Organizer",
    tagline: "Words that heal. Community that holds.",
    bio: `NAM Oshun is a poet, spoken word artist, and community builder whose work lives at the intersection of healing, Black identity, and mutual aid. Drawing from Yoruba spiritual tradition — Oshun as the orisha of rivers, love, and abundance — NAM's art is a practice of pouring into the community and watching it flow back.

From open mics to community workshops, from the page to the stage, NAM writes and performs to remind people: your story is not a burden. It is the bridge.`,
    pronouns: "he/him",
    location: "Florida, USA",
    avatar: "🌊",
    bannerColor: "from-amber-900 via-amber-800 to-ink",
    accentColor: "amber",

    // Social links — artist-facing only
    socials: [
      {
        platform: "Instagram",
        handle: "@namoshun",
        url: "https://www.instagram.com/namoshun",
        icon: "instagram",
        color: "bg-gradient-to-br from-purple-500 to-pink-500",
      },
      {
        platform: "Poets Got To Eat Too",
        handle: "Facebook Page",
        url: "https://www.facebook.com/",
        icon: "facebook-page",
        color: "bg-blue-600",
        note: "Poetry community & event announcements",
      },
      {
        platform: "S.O.U.P. Society Of Unified Poets",
        handle: "Facebook Page",
        url: "https://www.facebook.com/",
        icon: "facebook-page",
        color: "bg-blue-700",
        note: "Spoken word collective · Open to all poets",
      },
    ],

    // What they offer in M.O.R.E. skill exchange
    moreOfferings: [
      { icon: "✍️", title: "Writing Workshops", desc: "Healing through poetry. Free to M.O.R.E. community members by request." },
      { icon: "🎤", title: "Open Mic Coaching", desc: "Stage presence, breath work, delivery — in person or virtual." },
      { icon: "🌱", title: "Community Organizing", desc: "Strategy, space-holding, facilitation for community-based orgs." },
    ],

    // Store / merch / products
    commerce: [
      { label: "WAI-Institute Courses", desc: "Community development and healing arts curriculum", url: "/store", placeholder: false },
      { label: "The Ghost Producer × Publisher Prime", desc: "Interactive music & publishing empire — no sign-in required", url: "/ghost-producer", placeholder: false },
      { label: "Creators Sanctuary", desc: "The hub for all WAI creators — community, courses, healing arts, music", url: "/tools/creators-sanctuary.html", placeholder: false },
      { label: "Sage Oracle (DJEDI)", desc: "Kemetic AI guide — wisdom, social strategy, publishing, legal navigation", url: "/tools/djedi-oracle.html", placeholder: false },
      { label: "Electrical Courses", desc: "Circuit design, wiring, solar, safety — trade skills AI tutor", url: "/tools/electrical-courses.html", placeholder: false },
      { label: "Media Strategist", desc: "Campaign builder, press releases, pitch decks, analytics intelligence", url: "/tools/media-strategist.html", placeholder: false },
      { label: "Publisher Prime", desc: "Book publishing, marketing, ISBN guide, contract review — full empire", url: "/tools/publisher-prime.html", placeholder: false },
    ],

    // WAI-Institute creator status
    waiStatus: {
      tier: "BASIC",
      role: "Community Creator",
      since: "2026",
      bio: "Founding member of the M.O.R.E. Help Center. Co-architect of the Oliver Guardian community protection system.",
    },

    // Peer connection — rendered as a community link section
    _peerNote: "NAM Oshun and Royal Black Falcon have been brothers in this work since the beginning. Two poets. One mission: remind the community of what it already knows.",
    _peerSlug: "royal-black-falcon",
    _peerName: "Royal Black Falcon",
    _peerAvatar: "🦅",
    _peerTitle: "Poet · Spoken Word Artist · Cultural Warrior",

    // Ecosystem (non-artist — not shown on page but documented for handoff)
    _ecosystemNotes: `
NAM's broader network feeds users INTO WAI-Institute. These are NOT artist pages and should NOT appear on this profile,
but they are community pipelines:
- NAM TECH → tech arm of the ecosystem; drives student referrals
- Happy Mouth Mobile Kitchen → community food & wellness → M.O.R.E. skill exchange
- Wurk.Gang. Network → employment/labor → M.O.R.E. job board
- The Khmetic Mindset → Afrocentric philosophy community → cultural pipeline
- A-105 Radio → Black media → WAI-Institute outreach channel
- Black.Art.After.Dark → Black arts collective → creator pipeline for WAI marketplace
- Tha U Music Enterprise → music/creative industry → creator pipeline
- Black Pride WW3® → community solidarity → M.O.R.E. users
- K.O.S.M.O.S. → community org → M.O.R.E. partner org
- NEW BLACK PANTHER PARTY KENTUCKY CHAPTER → community org → M.O.R.E. community
Reconfiguration strategy: Each of these groups gets a ONE-LINE bio posted in their Facebook descriptions
pointing to wai-institute.org and the M.O.R.E. Hub. They become feeder communities.
    `,
  },

  // ── Royal Black Falcon — Kamau Baruti ───────────────────────────────────────
  "royal-black-falcon": {
    slug: "royal-black-falcon",
    displayName: "Royal Black Falcon",
    legalName: "Kamau Baruti",
    title: "Poet · Spoken Word Artist · Cultural Warrior",
    tagline: "The falcon sees from height, dives with intention, and lands exactly where it means to.",
    bio: `Kamau Baruti carries two names that say everything.

Kamau — Kikuyu for the quiet warrior. Not quiet because he has nothing to say. Quiet because he has learned that a warrior chooses when to move. Baruti — gunpowder. Not the explosion. The force that makes things fly.

The Royal Black Falcon is what happens when those two truths take the stage. A spoken word artist whose work lives at the razor edge between poetry and prophecy — sharply political when the moment demands it, achingly personal when the truth requires vulnerability. The falcon does not circle aimlessly. It soars to see clearly, then descends with precision.

Performing across stages, schools, living rooms, and sacred spaces, Kamau writes and delivers poetry that reminds people: Blackness has always been regal, sophisticated, and sovereign — not in spite of struggle, but rooted in something older than the struggle ever was.

He is a griot in the tradition that doesn't need to announce itself. The ancestors already know his name.`,
    pronouns: "he/him",
    location: "USA",
    avatar: "🦅",
    bannerColor: "from-blue-950 via-indigo-900 to-slate-900",
    accentColor: "indigo",

    socials: [
      {
        platform: "Instagram",
        handle: "@royalblackfalcon",
        url: "https://www.instagram.com/royalblackfalcon",
        icon: "instagram",
        color: "bg-gradient-to-br from-indigo-600 to-blue-700",
        note: "Poetry drops, stage moments, and movement",
      },
      {
        platform: "Facebook",
        handle: "Royal Black Falcon",
        url: "https://www.facebook.com/",
        icon: "facebook-page",
        color: "bg-blue-800",
        note: "Events, community, and spoken word announcements",
      },
      {
        platform: "WAI-Institute",
        handle: "Community Poet",
        url: "/register",
        icon: "wai",
        color: "bg-gradient-to-br from-amber-600 to-amber-700",
        note: "Invited to the platform by NAM Oshun · M.O.R.E. community voice",
      },
    ],

    moreOfferings: [
      {
        icon: "🦅",
        title: "Youth Poetry Workshops",
        desc: "Teaching young people — especially Black youth — to find their voice and trust it. Schools, rec centers, community orgs. Free through M.O.R.E.",
      },
      {
        icon: "✊🏿",
        title: "Cultural History Through Verse",
        desc: "Spoken word sessions tracing Black history, African origins, and the radical power of naming yourself. For organizations, classrooms, and communities.",
      },
      {
        icon: "🎤",
        title: "Stage Presence Coaching",
        desc: "For poets who are ready to step in front of the room. Breath, stillness, delivery, timing. The craft behind the thunder.",
      },
    ],

    commerce: [
      {
        label: "Join WAI-Institute",
        desc: "The platform where creators like Kamau teach, build, and connect with community.",
        url: "/register",
        placeholder: false,
      },
    ],

    waiStatus: {
      tier: "BASIC",
      role: "Community Poet",
      since: "2026",
      bio: "Invited to WAI-Institute by Executive Director NAM Oshun. Recognized as a founding voice of the M.O.R.E. poetry community.",
    },

    // Connection to NAM Oshun
    _peerNote: "Royal Black Falcon and NAM Oshun have been brothers in this work since the beginning. Two poets. One mission: remind the community of what it already knows.",
    _peerSlug: "nam-oshun",
    _peerName: "NAM Oshun",
    _peerAvatar: "🌊",
    _peerTitle: "Poet · Community Organizer · M.O.R.E. Founding Member",
  },

  // ── Nova Highborn — Ebony Oliver ─────────────────────────────────────────────
  "nova-highborn": {
    slug: "nova-highborn",
    displayName: "Nova Highborn",
    legalName: "Ebony Oliver",
    title: "Visual Artist · Poet · Artist Mentor · Digital Creator",
    tagline: "Something new is rising. That something is me.",
    bio: `Nova Highborn is what happens when a girl who was taught she was ordinary decides she never was.

Ebony Oliver came up watching the elders — her uncle NAM Oshun pouring words into audiences that needed them, her family building and creating and organizing when no one came to help. She learned early: you make your own door.

As Nova Highborn, she brings that inheritance into a new generation's language. Visual art that speaks before it's explained. Poetry that arrives like light through a crack. Digital content that makes her community feel seen on screens that have historically looked past them.

Nova is not emerging. She is already here. She is just letting you catch up.`,
    pronouns: "she/her",
    location: "Florida, USA",
    avatar: "✨",
    bannerColor: "from-emerald-900 via-teal-800 to-ink",
    accentColor: "emerald",

    socials: [
      {
        platform: "Instagram",
        handle: "@novahighborn",
        url: "https://www.instagram.com/",
        icon: "instagram",
        color: "bg-gradient-to-br from-emerald-500 to-teal-600",
        note: "Art drops, poetry, and what's on her mind",
      },
      {
        platform: "WAI-Institute",
        handle: "Community Creator",
        url: "/register",
        icon: "wai",
        color: "bg-gradient-to-br from-amber-500 to-amber-600",
        note: "Connect in the M.O.R.E. community",
      },
    ],

    playlistCuration: {
      enabled: true,
      headline: "Get Your Song on Nova's Playlist",
      desc: "Nova Highborn curates Spotify playlists for independent Black artists. Free gateway placements available — complete 5 simple steps and your song gets reviewed.",
      submitPath: "/playlist/nova-highborn/submit",
      dashboardPath: "/playlist/dashboard",
    },

    moreOfferings: [
      {
        icon: "🎨",
        title: "Visual Art for Community Orgs",
        desc: "Flyers, graphics, social media assets, event visuals — made by the community, for the community. Free through M.O.R.E. by request.",
      },
      {
        icon: "📱",
        title: "Content Creation Coaching",
        desc: "Teaching community members and small businesses how to show up powerfully on social media without selling their soul to algorithms.",
      },
      {
        icon: "✍️",
        title: "Youth Creative Workshops",
        desc: "Poetry and visual art for young people who don't see themselves reflected in mainstream art education. Especially for young Black girls.",
      },
      {
        icon: "🎯",
        title: "Artist Mentorship",
        desc: "1-on-1 mentoring for independent artists: vocal development, performance presence, branding, social media strategy, and navigating the music industry without losing yourself. All virtual.",
      },
    ],

    commerce: [
      {
        label: "Join WAI-Institute",
        desc: "Connect with Nova and other creators building on their own terms.",
        url: "/register",
        placeholder: false,
      },
    ],

    waiStatus: {
      tier: "BASIC",
      role: "Staff · Artist Mentor",
      since: "2026",
      bio: "WAI-Institute staff. Artist Mentor. Curator. Visual artist and poet building her own legacy inside the ecosystem her family helped create.",
    },

    _peerNote: "NAM Oshun watched Nova grow into her voice — and then watched her surpass the student stage entirely. She doesn't need to inherit the legacy. She's building her own.",
    _peerSlug: "nam-oshun",
    _peerName: "NAM Oshun",
    _peerAvatar: "🌊",
    _peerTitle: "Poet · Community Organizer · M.O.R.E. Founding Member",
  },

  // ── Vonn Oshun ────────────────────────────────────────────────────────────────
  "vonn-oshun": {
    slug: "vonn-oshun",
    displayName: "Vonn Oshun",
    title: "Recording Artist · Vocalist · Spiritual Sound Architect",
    tagline: "The voice carries what words alone cannot hold.",
    bio: `Vonn Oshun is a vocalist and recording artist whose work sits at the convergence of ancestral memory and modern sound. Drawing from the lineage of Oshun — Yoruba orisha of rivers, sweetness, and emotional truth — Vonn channels something older than genre into every track.

Her music is not simply heard. It moves through you. The original voice recordings carry the full weight of lived experience: breath, vibration, the catches and sustains that AI has not yet learned to fake. Alongside these, Vonn releases AI-assisted versions of selected tracks — created in collaboration with Suno — not to replace the human voice, but to explore the distance between the two.

That space between is where the conversation lives.

Vonn is a core artist in the WAI-Institute ecosystem and a living demonstration of what it looks like when an artist owns the full stack: her voice, her publishing, her platform, and her narrative.`,
    pronouns: "she/her",
    location: "Florida, USA",
    avatar: "🌊",
    bannerColor: "from-violet-950 via-purple-900 to-ink",
    accentColor: "violet",

    socials: [
      {
        platform: "Instagram",
        handle: "@vonnoshun",
        url: "https://www.instagram.com/",
        icon: "instagram",
        color: "bg-gradient-to-br from-purple-500 to-violet-700",
        note: "Music drops, visuals, and the work behind the work",
      },
    ],

    moreOfferings: [
      { icon: "🎤", title: "Vocal Coaching", desc: "One-on-one sessions for artists learning to trust and develop their voice. Technique meets spirit." },
      { icon: "🎵", title: "Session Vocals", desc: "Original vocal features and collaborations for independent artists in the M.O.R.E. network." },
      { icon: "🔊", title: "AI-Voice Consultation", desc: "Guidance on how to use AI voice tools ethically — and how to make sure your original always leads." },
    ],

    commerce: [],

    waiStatus: {
      tier: "BASIC",
      role: "Recording Artist · Community Creator",
      since: "2026",
      bio: "Vocalist and sound architect. Demonstrating artist-owned publishing in the WAI-Institute ecosystem.",
    },

    // Tracks — original voice + Suno AI version pairs
    tracks: [
      {
        id: "track-001",
        title: "On How to Work with AI",
        artist: "Vonn Oshun",
        // Replace these URLs with real Suno/CDN URLs when available
        original_url: null,
        ai_url: null,
        tags: ["spoken word", "AI", "education"],
      },
    ],

    _peerNote: "Vonn Oshun brings what no API can replicate — the voice that lived through it.",
    _peerSlug: "nam-oshun",
    _peerName: "NAM Oshun",
    _peerAvatar: "🌊",
    _peerTitle: "Poet · Community Organizer · M.O.R.E. Founding Member",
  },
};

const PLACEHOLDER_CREATOR = {
  displayName: "Creator Profile",
  title: "WAI-Institute Community Creator",
  tagline: "Coming soon.",
  bio: "This creator profile is not yet published.",
  avatar: "🌟",
  bannerColor: "from-ink via-ink/90 to-ink",
  socials: [],
  moreOfferings: [],
  commerce: [],
  waiStatus: null,
};

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
  const { user } = useAuth();
  const [dbProfile, setDbProfile] = useState(undefined); // undefined = loading, null = not found

  useEffect(() => {
    api.get(`/creator/profile/${slug}`)
      .then(r => setDbProfile(r.data.profile))
      .catch(() => setDbProfile(null));
  }, [slug]);

  // While fetching, check hardcoded registry as instant fallback
  const hardcoded = CREATORS[slug] || null;

  // Still loading from backend
  if (dbProfile === undefined && !hardcoded) {
    return (
      <div className="min-h-screen bg-bone flex items-center justify-center">
        <div className="text-ink/40 text-sm">Loading profile…</div>
      </div>
    );
  }

  const creator = dbProfile ? dbToCreator(dbProfile) : hardcoded;

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
