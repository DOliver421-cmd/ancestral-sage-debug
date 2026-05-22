import { Link } from "react-router-dom";
import { useEffect, useState } from "react";
import { WAI_LOGO, BRAND } from "../lib/brand";
import { Heart, Users, ArrowRight, DollarSign, Sparkles, TrendingUp, Mic } from "lucide-react";
import BugReportModal from "../components/BugReportModal";

const LIVE_ACTIVITY = [
  { user: "Maya T.", action: "just completed", subject: "Electrical Safety Module", time: "2m ago", avatar: "🎓" },
  { user: "Khalil M.", action: "enrolled in", subject: "Amara's Healing Poetry Course", time: "3m ago", avatar: "✍️" },
  { user: "DeShawn R.", action: "joined", subject: "Artist Management Fundamentals", time: "4m ago", avatar: "🎵" },
  { user: "James L.", action: "earned certificate in", subject: "AC/DC Fundamentals", time: "5m ago", avatar: "⚡" },
  { user: "Tasha W.", action: "enrolled in", subject: "A&R: Finding and Developing Talent", time: "8m ago", avatar: "🎙️" },
  { user: "Sofia M.", action: "joined premium mentoring", subject: "with Marcus Thompson (Art)", time: "12m ago", avatar: "🎨" },
  { user: "Raheem B.", action: "posted in M.O.R.E.", subject: "Need beat producer for community album", time: "15m ago", avatar: "🎚️" },
  { user: "Zara P.", action: "purchased course", subject: "Priya's Wellness & Meditation", time: "22m ago", avatar: "🧘" },
  { user: "Aisha B.", action: "shared their portfolio", subject: "Mixed Media Artwork", time: "25m ago", avatar: "📁" },
  { user: "Marcus J.", action: "became a mentor", subject: "Teaching music business + A&R", time: "31m ago", avatar: "👨‍🏫" },
];

const SPOTLIGHTS = [
  {
    name: "DeShawn Williams",
    role: "Trades Training Entrepreneur",
    story: "Built a nonprofit using our electrical curriculum. Trained 50+ young adults in his neighborhood. Got funding. Changed communities from the inside.",
    image: "👨‍💼",
    stat: "$180K training revenue",
    tag: "Creator",
  },
  {
    name: "Amara Johnson",
    role: "Poet & Healing Teacher",
    story: "Teaching trauma recovery poetry to people who survived what she survived. 342 students. Earning $8.9K/month. Built her own community — on her terms.",
    image: "✍️",
    stat: "342 students | $8.9K/mo",
    tag: "Creator",
  },
  {
    name: "Kezia Moreau",
    role: "Community Paralegal · M.O.R.E. Member",
    story: "Lost her job during a landlord dispute. Posted a need in M.O.R.E. — a paralegal helped her fight back and win. Now she teaches tenant rights to others.",
    image: "⚖️",
    stat: "Eviction dismissed | Now teaching",
    tag: "M.O.R.E.",
  },
  {
    name: "Ray Calloway",
    role: "A&R Director turned Community Educator",
    story: "Spent 12 years at a major label watching artists get robbed of their masters. Left. Built a course teaching independent artists how to own their music. 600+ students protected their work.",
    image: "🎵",
    stat: "600 artists · Masters protected",
    tag: "Creator",
  },
  {
    name: "Jamal & Renee Brooks",
    role: "Skill Swap · M.O.R.E. Members",
    story: "Jamal does taxes. Renee does childcare. They never exchanged a dollar — just posted in M.O.R.E. and found each other. This is what mutual aid looks like.",
    image: "🤝",
    stat: "Zero dollars. Real community.",
    tag: "M.O.R.E.",
  },
  {
    name: "Latoya Freeman",
    role: "Master Electrician & Mentor",
    story: "Trades apprentice turned mentor. Mentoring 8 young women entering electrical work — a field that tried to shut her out. Earning $12K/quarter. Kept her independence.",
    image: "👩‍🔧",
    stat: "8 mentees | $12K/quarter",
    tag: "Creator",
  },
];

const MUSIC_COURSES = [
  { icon: "🎵", title: "Artist Management Fundamentals", desc: "Contracts, royalties, touring logistics, and team building. Build an artist's career on their terms — not the label's." },
  { icon: "🎙️", title: "A&R: Finding & Developing Talent", desc: "Artist & Repertoire from the inside. How to spot, sign, and develop artists without extracting from them." },
  { icon: "📻", title: "Radio & Media Promotion", desc: "From community radio to streaming playlists. Get your music heard without a major label machine running it." },
  { icon: "🎤", title: "Performance & Stage Presence", desc: "The craft behind the live show. Breath, movement, crowd connection — delivered by working performers." },
  { icon: "🎚️", title: "Music Production for Creatives", desc: "DAWs, beat building, arrangement. The technical foundation that makes your musical vision real." },
  { icon: "💰", title: "Music Business & Publishing", desc: "Licensing, sync deals, PRO registration, owning your masters. Knowledge the industry never wanted you to have." },
];

const FEATURED_CREATORS = [
  {
    slug: "nam-oshun",
    name: "NAM Oshun",
    role: "Poet · Community Organizer",
    bio: "Founding voice of the M.O.R.E. Help Center. Words that heal. Community that holds.",
    avatar: "🌊",
    palette: "from-amber-900 via-amber-800 to-ink",
    badge: "Founding Member",
  },
  {
    slug: "royal-black-falcon",
    name: "Royal Black Falcon",
    role: "Poet · Cultural Warrior",
    bio: "The falcon soars to see clearly, then descends with precision. A griot in the tradition that doesn't need to announce itself.",
    avatar: "🦅",
    palette: "from-blue-950 via-indigo-900 to-slate-900",
    badge: "Community Poet",
  },
  {
    slug: "nova-highborn",
    name: "Nova Highborn",
    role: "Visual Artist · Digital Creator",
    bio: "Something new is rising. Visual art that speaks before it's explained. Poetry that arrives like light.",
    avatar: "✨",
    palette: "from-emerald-900 via-teal-800 to-ink",
    badge: "Emerging Creator",
  },
];

const IMPACT = [
  { number: "2,847", label: "Students learning", color: "text-copper" },
  { number: "$1.2M", label: "Creator earnings", color: "text-signal" },
  { number: "340", label: "Certificates earned", color: "text-ink" },
  { number: "52", label: "Corporate contracts", color: "text-copper" },
];

const TESTIMONIALS = [
  {
    quote: "My grandmother taught herbs. My mother taught sewing. I teach electrical. We've always trained each other — this platform just lets me do it at scale and get paid for it.",
    author: "Elena Rodriguez",
    role: "Master Electrician & Mentor",
    avatar: "👩‍🔧",
  },
  {
    quote: "As a poet teaching healing work, I finally found a platform that doesn't extract from creators. I keep 70%, I own my content, and my students are real.",
    author: "Amara Johnson",
    role: "Poet & Healing Teacher",
    avatar: "✍️",
  },
  {
    quote: "I spent twelve years watching labels rob artists of their masters. I built a course to stop that cycle. Six hundred artists now own their work. That's the platform I needed.",
    author: "Ray Calloway",
    role: "A&R Director turned Educator",
    avatar: "🎵",
  },
  {
    quote: "The community here is REAL. Electricians mentoring apprentices. Artists teaching artists. Healers supporting healers. It feels like home, not a corporate platform.",
    author: "Sofia Martinez",
    role: "Apprentice & Community Organizer",
    avatar: "👩‍🎓",
  },
];

export default function LandingMarketplace() {
  const [activeTestimonial, setActiveTestimonial] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setActiveTestimonial((prev) => (prev + 1) % TESTIMONIALS.length);
    }, 6000);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="min-h-screen bg-bone text-ink">

      {/* ── Header ─────────────────────────────────────────────────────── */}
      <header className="border-b border-ink/10 bg-bone sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-3">
            <img src={WAI_LOGO} alt="W.A.I." className="w-12 h-12 object-contain" style={{ mixBlendMode: "multiply" }} />
            <div>
              <div className="overline text-copper leading-none">{BRAND.short}</div>
              <div className="font-heading font-bold text-sm leading-tight">{BRAND.name}</div>
            </div>
          </Link>
          <nav className="flex items-center gap-4">
            <Link to="/more" className="flex items-center gap-1.5 text-sm font-bold text-amber-600 hover:text-amber-500 border border-amber-300 hover:border-amber-500 px-3 py-1 rounded-full transition-colors">
              <Heart className="w-3.5 h-3.5" /> M.O.R.E. Hub
            </Link>
            <a href="#community" className="text-sm font-medium hover:text-copper hidden sm:block">Community</a>
            <a href="#music" className="text-sm font-medium hover:text-copper hidden sm:block">Music & Arts</a>
            <a href="#creators" className="text-sm font-medium hover:text-copper hidden sm:block">For Creators</a>
            <Link to="/login" className="text-sm font-bold uppercase tracking-widest hover:text-copper">Sign in</Link>
            <Link to="/register" className="btn-copper text-sm">Join Us</Link>
          </nav>
        </div>
      </header>

      {/* ── Beta tester banner ──────────────────────────────────────────── */}
      <div className="bg-ink text-white py-3 px-6">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2 text-sm">
          <div className="flex items-center gap-2 font-medium">
            <span className="text-lg">🐛</span>
            <span><strong>Beta Tester?</strong> Sign up → explore → report bugs → get $1. First 20 testers only.</span>
          </div>
          <div className="flex items-center gap-3 shrink-0">
            <Link to="/register" className="bg-copper hover:bg-copper/80 text-white font-bold px-4 py-1.5 rounded-lg text-xs transition-colors">
              Step 1: Create Account
            </Link>
            <span className="text-white/40 text-xs hidden sm:inline">Then click 🐛 at bottom-right to report</span>
          </div>
        </div>
      </div>

      {/* ── Hero ───────────────────────────────────────────────────────── */}
      <section className="relative overflow-hidden bg-gradient-to-b from-bone via-copper/5 to-bone/50 py-32">
        <div className="absolute inset-0 grid-paper opacity-10 pointer-events-none" />
        <div className="max-w-7xl mx-auto px-6 relative">
          <div className="text-center max-w-3xl mx-auto">
            <div className="inline-flex items-center gap-2 mb-6 px-4 py-2 bg-copper/10 border border-copper text-copper rounded-full text-sm font-bold">
              <Sparkles className="w-4 h-4" /> Mutual Aid · Skill Exchange · Community Power
            </div>
            <h1 className="font-heading text-6xl sm:text-7xl font-extrabold leading-tight mb-6">
              You're the <span className="text-copper">teachers.</span><br />
              You're the <span className="text-copper">makers.</span><br />
              You're the <span className="text-copper">healers.</span>
            </h1>
            <p className="text-xl text-ink/70 leading-relaxed mb-8 max-w-2xl mx-auto">
              Our communities have always built from within — teaching each other, trading skills, showing up when systems don't.
              W.A.I. Institute exists to support what we already do. Keep your knowledge. Keep your earnings. Keep your power.
            </p>
            <div className="flex flex-wrap justify-center gap-4 mb-20">
              <Link to="/more" className="btn-copper inline-flex items-center gap-2 text-lg">
                <Heart className="w-5 h-5" /> Enter the M.O.R.E. Hub
              </Link>
              <Link to="/register" className="btn-primary inline-flex items-center gap-2 text-lg">
                Join The Community <ArrowRight className="w-5 h-5" />
              </Link>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6 max-w-2xl mx-auto">
              {IMPACT.map((item) => (
                <div key={item.label} className="p-4 bg-white/50 border border-ink/10 rounded-lg backdrop-blur">
                  <div className={`text-3xl font-black ${item.color}`}>{item.number}</div>
                  <div className="text-xs text-ink/60 mt-1">{item.label}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ── Who This Is For ────────────────────────────────────────────── */}
      <section className="py-20 bg-copper text-white">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-12">
            <p className="text-white/70 text-xs uppercase tracking-widest font-bold mb-3">Our people. Our platform.</p>
            <h2 className="font-heading text-4xl sm:text-5xl font-extrabold leading-tight mb-4">
              This is not for everyone.<br />It's for us.
            </h2>
            <p className="text-white/80 max-w-2xl mx-auto text-base leading-relaxed">
              Black creators. Indigenous artists. Working-class teachers. Healers who learned from their grandmothers.
              Poets who performed in barbershops before anyone gave them a stage.
              The communities that built everything — and were written out of the ownership.
            </p>
          </div>
          <div className="grid md:grid-cols-3 gap-8 text-center">
            {[
              {
                icon: "🌍",
                title: "Black & BIPOC Creators",
                body: "Platforms built to extract from us don't deserve our content. This one was built by us, designed around our communities, and structured so we keep what we earn.",
              },
              {
                icon: "🤝",
                title: "Working-Class Community",
                body: "Trades workers. Caregivers. Neighborhood organizers. The people who hold communities together without recognition. You're teachers. This platform pays you like it.",
              },
              {
                icon: "🎵",
                title: "Artists, Poets & Musicians",
                body: "From the open mic to the recording studio. From spoken word to A&R. The music and arts industry has extracted from our culture for generations. Here, we own our work.",
              },
            ].map(({ icon, title, body }) => (
              <div key={title} className="bg-white/10 border border-white/20 rounded-2xl p-8">
                <div className="text-5xl mb-4">{icon}</div>
                <h3 className="font-heading font-extrabold text-xl mb-3">{title}</h3>
                <p className="text-white/75 text-sm leading-relaxed">{body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── M.O.R.E. Help Center ───────────────────────────────────────── */}
      <section className="py-20 bg-ink text-white" id="more">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <div className="inline-flex items-center gap-2 mb-5 px-3 py-1.5 bg-amber-500/20 border border-amber-400/30 rounded-full text-amber-400 text-xs font-bold uppercase tracking-wider">
                <Heart className="w-3.5 h-3.5" /> Public · Always Free · No Login Required to Browse
              </div>
              <h2 className="font-heading text-5xl font-extrabold leading-tight mb-5">
                The M.O.R.E.<br />Help Center
              </h2>
              <p className="text-lg text-white/80 leading-relaxed mb-3">
                <span className="text-white font-semibold">Michael Oliver Resource Exchange.</span> Named after the disability rights organizer who said that society creates barriers — and that it's society's job to remove them.
              </p>
              <p className="text-base text-white/60 leading-relaxed mb-8">
                M.O.R.E. is where community members offer skills, post real needs, share stories, and hold each other up.
                No charity. No shame. Just neighbors who know how to fix things, teach things, and show up — the way we always have.
              </p>
              <div className="grid grid-cols-2 gap-3 mb-8">
                {[
                  { icon: "🤝", label: "Skill Exchange", sub: "Offer what you know. Ask for what you need." },
                  { icon: "🏠", label: "Housing + Jobs", sub: "Real leads from people who know real people." },
                  { icon: "⚖️", label: "Legal Plain Language", sub: "Your rights, explained in words you can act on." },
                  { icon: "🛡️", label: "Safe & Moderated", sub: "Oliver Guardian reviews every post. No exploitation." },
                ].map(({ icon, label, sub }) => (
                  <div key={label} className="bg-white/5 border border-white/10 rounded-xl p-4">
                    <div className="text-2xl mb-2">{icon}</div>
                    <div className="text-white font-semibold text-sm mb-1">{label}</div>
                    <div className="text-white/50 text-xs leading-relaxed">{sub}</div>
                  </div>
                ))}
              </div>
              <div className="flex flex-wrap gap-3">
                <Link to="/more" className="inline-flex items-center gap-2 bg-amber-500 hover:bg-amber-400 text-ink font-bold px-6 py-3 rounded-xl transition-all hover:scale-105">
                  <Heart className="w-4 h-4" /> Enter the M.O.R.E. Hub
                </Link>
                <Link to="/register" className="inline-flex items-center gap-2 border-2 border-white/20 text-white hover:border-white font-semibold px-6 py-3 rounded-xl transition-colors">
                  Join to Post <ArrowRight className="w-4 h-4" />
                </Link>
              </div>
            </div>
            <div className="space-y-4">
              <div className="bg-white/5 border border-white/10 rounded-2xl p-6">
                <div className="text-xs text-amber-400 font-bold uppercase tracking-widest mb-3">From the Community</div>
                <blockquote className="text-white/80 text-sm leading-relaxed italic mb-3">
                  "I needed someone to help me read my lease before I signed it. A paralegal student in M.O.R.E. sat with me for an hour. They found two clauses that would have cost me thousands."
                </blockquote>
                <div className="text-white/40 text-xs">— Community member, Tampa</div>
              </div>
              <div className="bg-white/5 border border-white/10 rounded-2xl p-6">
                <div className="text-xs text-amber-400 font-bold uppercase tracking-widest mb-3">Skill Exchange</div>
                <blockquote className="text-white/80 text-sm leading-relaxed italic mb-3">
                  "I know how to do taxes. I needed help moving furniture. We never exchanged a dollar. That's M.O.R.E."
                </blockquote>
                <div className="text-white/40 text-xs">— Community member, Orlando</div>
              </div>
              <div className="bg-white/5 border border-white/10 rounded-2xl p-6">
                <div className="text-xs text-emerald-400 font-bold uppercase tracking-widest mb-3">What's Live Right Now</div>
                <div className="space-y-2.5">
                  {[
                    { type: "Skill Offer", text: "Free graphic design help for small businesses", dot: "bg-emerald-400" },
                    { type: "Need", text: "Looking for childcare swap — I cook, you watch", dot: "bg-amber-400" },
                    { type: "Music", text: "Need a beat producer for community album — no budget, rev share", dot: "bg-purple-400" },
                  ].map(({ type, text, dot }) => (
                    <div key={text} className="flex items-start gap-3 text-xs text-white/60">
                      <span className={`w-2 h-2 rounded-full ${dot} mt-1 shrink-0`} />
                      <span><span className="text-white/80 font-semibold">{type}:</span> {text}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Live Activity Feed ─────────────────────────────────────────── */}
      <section className="py-16 bg-white border-t border-b border-ink/10">
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex items-center justify-between mb-8">
            <h2 className="text-3xl font-bold flex items-center gap-2">
              <TrendingUp className="w-8 h-8 text-copper" /> Right now in our community
            </h2>
            <p className="text-sm text-ink/60 hidden sm:block">Trades · arts · music · healing · community — all learning together</p>
          </div>
          <div className="space-y-3 max-w-2xl">
            {LIVE_ACTIVITY.map((activity, idx) => (
              <div key={idx} className="p-4 border border-ink/10 rounded-lg hover:border-copper/30 transition-colors flex items-center gap-4">
                <span className="text-3xl">{activity.avatar}</span>
                <div className="flex-1">
                  <p className="text-sm">
                    <strong>{activity.user}</strong> {activity.action} <span className="text-copper font-bold">{activity.subject}</span>
                  </p>
                  <p className="text-xs text-ink/40 mt-1">{activity.time}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Community Spotlights ───────────────────────────────────────── */}
      <section id="community" className="py-24 bg-bone">
        <div className="max-w-7xl mx-auto px-6">
          <h2 className="text-5xl font-bold text-center mb-4">Built by the Community.</h2>
          <p className="text-lg text-ink/60 text-center max-w-2xl mx-auto mb-16">
            Educators, artists, organizers, and neighbors — skill-sharing, income-earning, and holding each other up.
          </p>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {SPOTLIGHTS.map((member) => (
              <div key={member.name} className="bg-white border border-ink/10 rounded-lg p-8 hover:shadow-lg transition-shadow">
                <div className="flex items-center justify-between mb-4">
                  <span className="text-5xl">{member.image}</span>
                  {member.tag === "M.O.R.E." ? (
                    <span className="text-xs font-bold px-2.5 py-1 rounded-full bg-amber-100 text-amber-700 border border-amber-300">M.O.R.E.</span>
                  ) : (
                    <span className="text-xs font-bold px-2.5 py-1 rounded-full bg-copper/10 text-copper border border-copper/30">Creator</span>
                  )}
                </div>
                <h3 className="text-2xl font-bold mb-1">{member.name}</h3>
                <p className="text-sm text-copper font-bold mb-4">{member.role}</p>
                <p className="text-ink/70 mb-6">{member.story}</p>
                <div className={`p-3 rounded border ${member.tag === "M.O.R.E." ? "bg-amber-50 border-amber-200" : "bg-copper/10 border-copper/20"}`}>
                  <p className={`text-sm font-bold ${member.tag === "M.O.R.E." ? "text-amber-700" : "text-copper"}`}>{member.stat}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Music & Arts Industry ─────────────────────────────────────── */}
      <section id="music" className="py-24 bg-gradient-to-br from-ink via-ink/95 to-ink/90 text-white">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-14">
            <div className="inline-flex items-center gap-2 mb-5 px-3 py-1.5 bg-amber-500/20 border border-amber-400/30 rounded-full text-amber-400 text-xs font-bold uppercase tracking-wider">
              <Mic className="w-3.5 h-3.5" /> Music · Arts · Culture · Business
            </div>
            <h2 className="font-heading text-5xl font-extrabold mb-5 leading-tight">
              Music. Art. Culture. Business.<br />
              <span className="text-amber-400">On our terms.</span>
            </h2>
            <p className="text-white/70 max-w-2xl mx-auto text-base leading-relaxed">
              The industry has been extracting from our communities since there was an industry.
              We're building the other side — where artists own their masters, managers work for their artists,
              and knowledge doesn't cost you your soul.
            </p>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5 mb-14">
            {MUSIC_COURSES.map(({ icon, title, desc }) => (
              <div key={title} className="bg-white/5 border border-white/10 hover:border-amber-400/30 rounded-2xl p-6 transition-all group">
                <div className="text-4xl mb-4">{icon}</div>
                <h3 className="font-heading font-extrabold text-lg mb-2 text-white group-hover:text-amber-300 transition-colors">{title}</h3>
                <p className="text-white/55 text-sm leading-relaxed mb-4">{desc}</p>
                <Link to="/register" className="inline-flex items-center gap-1.5 text-xs font-bold text-amber-400 hover:text-amber-300 transition-colors">
                  Start learning <ArrowRight className="w-3 h-3" />
                </Link>
              </div>
            ))}
          </div>
          <div className="bg-white/5 border border-white/10 rounded-2xl p-8 flex flex-col sm:flex-row items-center gap-6 text-center sm:text-left">
            <div className="text-5xl">🎵</div>
            <div className="flex-1">
              <h3 className="font-heading font-extrabold text-xl mb-1">Are you in the music industry?</h3>
              <p className="text-white/60 text-sm leading-relaxed">
                A&R directors, managers, promoters, producers, engineers — bring your knowledge here.
                Teach what the industry didn't want you to share. Keep 70%.
              </p>
            </div>
            <Link to="/register" className="shrink-0 inline-flex items-center gap-2 bg-amber-500 hover:bg-amber-400 text-ink font-bold px-6 py-3 rounded-xl transition-all hover:scale-105 whitespace-nowrap">
              Become a Creator <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </section>

      {/* ── Featured Creators ─────────────────────────────────────────── */}
      <section className="py-20 bg-bone border-t border-ink/10">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-12">
            <p className="text-copper text-xs uppercase tracking-widest font-bold mb-2">Real People. Real Community.</p>
            <h2 className="font-heading text-4xl font-extrabold mb-3">Meet the Creators</h2>
            <p className="text-ink/60 max-w-xl mx-auto text-sm">
              These are not stock photos. These are the people building this with us.
              Click their profiles. See what's possible.
            </p>
          </div>
          <div className="grid md:grid-cols-3 gap-6 mb-8">
            {FEATURED_CREATORS.map((c) => (
              <Link
                key={c.slug}
                to={`/creator/${c.slug}`}
                className="group block rounded-2xl overflow-hidden border border-ink/10 hover:shadow-xl transition-all hover:scale-[1.02]"
              >
                <div className={`bg-gradient-to-br ${c.palette} p-8 text-white text-center`}>
                  <div className="text-6xl mb-3">{c.avatar}</div>
                  <div className="font-heading font-extrabold text-2xl leading-none mb-1">{c.name}</div>
                  <div className="text-white/60 text-xs mb-3">{c.role}</div>
                  <span className="inline-block px-3 py-1 bg-amber-500/20 border border-amber-400/30 text-amber-300 text-xs font-bold rounded-full">{c.badge}</span>
                </div>
                <div className="bg-white p-5">
                  <p className="text-ink/70 text-sm leading-relaxed mb-3">{c.bio}</p>
                  <span className="inline-flex items-center gap-1.5 text-xs font-bold text-copper group-hover:text-copper/80 transition-colors">
                    View Profile <ArrowRight className="w-3 h-3" />
                  </span>
                </div>
              </Link>
            ))}
          </div>
          <div className="text-center">
            <Link to="/register" className="inline-flex items-center gap-2 border-2 border-ink text-ink font-bold px-6 py-3 rounded-xl hover:bg-ink hover:text-white transition-all">
              Claim Your Creator Profile <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </section>

      {/* ── Testimonials ──────────────────────────────────────────────── */}
      <section className="py-24 bg-white border-t border-ink/10">
        <div className="max-w-3xl mx-auto px-6 text-center">
          <h2 className="text-4xl font-bold mb-12">What members say</h2>
          <div className="relative min-h-[200px]">
            {TESTIMONIALS.map((testimonial, idx) => (
              <div
                key={idx}
                className={`transition-opacity duration-500 ${idx === activeTestimonial ? "opacity-100" : "opacity-0 absolute inset-0"}`}
              >
                <blockquote className="mb-8">
                  <p className="text-2xl font-bold text-ink leading-relaxed">"{testimonial.quote}"</p>
                </blockquote>
                <div className="flex items-center justify-center gap-4">
                  <span className="text-5xl">{testimonial.avatar}</span>
                  <div className="text-left">
                    <p className="font-bold text-lg">{testimonial.author}</p>
                    <p className="text-sm text-ink/60">{testimonial.role}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
          <div className="flex justify-center gap-2 mt-12">
            {TESTIMONIALS.map((_, idx) => (
              <button
                key={idx}
                onClick={() => setActiveTestimonial(idx)}
                className={`w-2 h-2 rounded-full transition-colors ${idx === activeTestimonial ? "bg-copper" : "bg-ink/20"}`}
              />
            ))}
          </div>
        </div>
      </section>

      {/* ── For Creators ──────────────────────────────────────────────── */}
      <section id="creators" className="py-24 bg-bone">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <h2 className="font-heading text-5xl font-bold mb-6">For Creators, Teachers, Builders</h2>
              <p className="text-lg text-ink/60 mb-8">
                Whether you teach electrical work, music business, healing arts, or spoken word — your knowledge has value.
                You deserve a platform that pays you fairly and lets you own your creation.
              </p>
              <div className="space-y-4">
                <div className="flex gap-4">
                  <DollarSign className="w-6 h-6 text-copper flex-shrink-0 mt-1" />
                  <div>
                    <h4 className="font-bold">70% revenue goes to you</h4>
                    <p className="text-sm text-ink/60">Every month. On the 1st. No negotiations, no surprises.</p>
                  </div>
                </div>
                <div className="flex gap-4">
                  <Heart className="w-6 h-6 text-copper flex-shrink-0 mt-1" />
                  <div>
                    <h4 className="font-bold">You own your content forever</h4>
                    <p className="text-sm text-ink/60">We don't own it. We can't sell it. You control everything.</p>
                  </div>
                </div>
                <div className="flex gap-4">
                  <Users className="w-6 h-6 text-copper flex-shrink-0 mt-1" />
                  <div>
                    <h4 className="font-bold">Build community on your terms</h4>
                    <p className="text-sm text-ink/60">No algorithm games. No shadow bans. Direct connection with your students.</p>
                  </div>
                </div>
              </div>
              <Link to="/register" className="btn-primary mt-8 inline-flex items-center gap-2">
                Become A Creator <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
            <div className="bg-gradient-to-br from-copper/10 to-copper/5 border border-copper/20 rounded-lg p-12">
              <h4 className="font-bold text-lg mb-8">Creator Example</h4>
              <div className="space-y-6">
                <div>
                  <div className="flex justify-between mb-2">
                    <span className="text-sm font-bold">100 students</span>
                    <span className="text-sm text-copper font-bold">@ $29.99/mo</span>
                  </div>
                  <div className="text-3xl font-black text-copper">$2,100</div>
                  <div className="text-xs text-ink/60 mt-1">Your monthly income (after we take 30%)</div>
                </div>
                <div className="border-t border-copper/20 pt-6">
                  <p className="text-sm text-ink/60">Scale to 500 students → $10,500/month. 1000 students → $21K/month.</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Grow With Us ──────────────────────────────────────────────── */}
      <section className="py-20 bg-amber-50 border-t border-amber-200">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-12">
            <p className="text-amber-700 text-xs uppercase tracking-widest font-bold mb-2">Opportunities</p>
            <h2 className="font-heading text-4xl font-extrabold mb-3">Grow With Us</h2>
            <p className="text-ink/60 max-w-xl mx-auto text-sm">WAI-Institute is building something real. We need real people to build it with us.</p>
          </div>
          <div className="grid md:grid-cols-3 gap-6">
            <div className="bg-white rounded-2xl border border-amber-200 p-8">
              <div className="text-4xl mb-4">🎓</div>
              <h3 className="font-heading font-extrabold text-xl mb-2">Internships</h3>
              <p className="text-ink/60 text-sm leading-relaxed mb-5">
                Community-based internships in content creation, community organizing, music marketing, platform development,
                and M.O.R.E. coordination. Credit available. Real work. Real mentorship.
              </p>
              <Link to="/internships" className="inline-flex items-center gap-1.5 text-sm font-bold text-amber-700 hover:text-amber-600 transition-colors">
                Learn more <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
            <div className="bg-white rounded-2xl border border-amber-200 p-8">
              <div className="text-4xl mb-4">📢</div>
              <h3 className="font-heading font-extrabold text-xl mb-2">Advertise With Us</h3>
              <p className="text-ink/60 text-sm leading-relaxed mb-5">
                Reach Black creators, artists, musicians, and community builders. Ethical advertising only —
                no surveillance, no data mining. Sponsors who align with community values only.
              </p>
              <a href="mailto:ads@wai-institute.org" className="inline-flex items-center gap-1.5 text-sm font-bold text-amber-700 hover:text-amber-600 transition-colors">
                Contact us <ArrowRight className="w-3.5 h-3.5" />
              </a>
            </div>
            <div className="bg-white rounded-2xl border border-amber-200 p-8">
              <div className="text-4xl mb-4">🤝</div>
              <h3 className="font-heading font-extrabold text-xl mb-2">Community Partnerships</h3>
              <p className="text-ink/60 text-sm leading-relaxed mb-5">
                Organizations, nonprofits, community groups, and collectives — partner with WAI-Institute to bring
                M.O.R.E. resources, courses, and creator tools to your community.
              </p>
              <a href="mailto:partners@wai-institute.org" className="inline-flex items-center gap-1.5 text-sm font-bold text-amber-700 hover:text-amber-600 transition-colors">
                Partner with us <ArrowRight className="w-3.5 h-3.5" />
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* ── Final CTA ─────────────────────────────────────────────────── */}
      <section id="impact" className="py-24 bg-ink text-white">
        <div className="max-w-3xl mx-auto px-6 text-center">
          <p className="text-white/50 text-xs uppercase tracking-widest font-bold mb-4">Ubuntu · Mutual Aid · Community Power</p>
          <h2 className="font-heading text-5xl font-bold mb-6 leading-tight">
            We are because<br />we are together.
          </h2>
          <p className="text-xl text-white/80 mb-8 leading-relaxed">
            Our communities have always known how to build. We've always known how to teach. We've always known how to hold each other up.
            This platform exists to support what we already do — and make sure we get paid for it.
          </p>
          <div className="flex flex-wrap justify-center gap-4">
            <Link to="/register" className="btn-primary inline-flex items-center gap-2 text-lg">
              Join Us <ArrowRight className="w-5 h-5" />
            </Link>
            <Link to="/more" className="inline-flex items-center gap-2 px-6 py-3 border-2 border-amber-400 text-amber-300 font-bold hover:bg-amber-400 hover:text-ink transition-colors rounded-sm text-lg">
              <Heart className="w-5 h-5" /> Visit M.O.R.E.
            </Link>
          </div>
        </div>
      </section>

      {/* ── Footer ────────────────────────────────────────────────────── */}
      <footer className="bg-ink/95 text-white/60 border-t border-white/10 py-12">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid md:grid-cols-4 gap-8 mb-12">
            <div>
              <div className="flex items-center gap-2 mb-4">
                <img src={WAI_LOGO} alt="W.A.I." className="w-8 h-8 object-contain" style={{ mixBlendMode: "screen" }} />
                <span className="font-bold text-white">{BRAND.short}</span>
              </div>
              <p className="text-sm">Building community. Supporting creators. Changing lives.</p>
            </div>
            <div>
              <h4 className="font-bold text-white mb-4">Community</h4>
              <ul className="space-y-2 text-sm">
                <li><Link to="/more" className="text-amber-400 hover:text-amber-300 font-semibold transition-colors">M.O.R.E. Help Center</Link></li>
                <li><a href="#community" className="hover:text-white transition-colors">Stories</a></li>
                <li><a href="#music" className="hover:text-white transition-colors">Music & Arts</a></li>
                <li><Link to="/internships" className="hover:text-white transition-colors">Internships</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="font-bold text-white mb-4">For Creators</h4>
              <ul className="space-y-2 text-sm">
                <li><Link to="/register" className="hover:text-white transition-colors">Start Creating</Link></li>
                <li><a href="#creators" className="hover:text-white transition-colors">How it works</a></li>
                <li><a href="#music" className="hover:text-white transition-colors">Music & A&R Courses</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-bold text-white mb-4">Account</h4>
              <ul className="space-y-2 text-sm">
                <li><Link to="/login" className="hover:text-white transition-colors">Sign In</Link></li>
                <li><Link to="/register" className="hover:text-white transition-colors">Join</Link></li>
                <li><a href="mailto:ads@wai-institute.org" className="hover:text-white transition-colors">Advertise</a></li>
              </ul>
            </div>
          </div>
          <div className="border-t border-white/10 pt-8 text-sm text-center">
            <p>&copy; 2026 WAI Institute. Built by community, for community.</p>
          </div>
        </div>
      </footer>

      <BugReportModal />
    </div>
  );
}
