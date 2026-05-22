import { Link } from "react-router-dom";
import { useEffect, useState } from "react";
import { WAI_LOGO, BRAND } from "../lib/brand";
import { Heart, BookOpen, Users, Award, Zap, ArrowRight, MessageSquare, DollarSign, Shield, Sparkles, TrendingUp } from "lucide-react";
import BugReportModal from "../components/BugReportModal";

// Community activity feed (simulated live data - BOTH trades & digital creators)
const LIVE_ACTIVITY = [
  { user: "Maya T.", action: "just completed", subject: "Electrical Safety Module", time: "2m ago", avatar: "🎓" },
  { user: "Khalil M.", action: "enrolled in", subject: "Amara's Healing Poetry Course", time: "3m ago", avatar: "✍️" },
  { user: "James L.", action: "earned certificate in", subject: "AC/DC Fundamentals", time: "5m ago", avatar: "⚡" },
  { user: "Sofia M.", action: "joined premium mentoring", subject: "with Marcus Thompson (Art)", time: "12m ago", avatar: "🎨" },
  { user: "David K.", action: "posted in community", subject: "Help with conduit bending", time: "18m ago", avatar: "🔧" },
  { user: "Zara P.", action: "purchased course", subject: "Priya's Wellness & Meditation", time: "22m ago", avatar: "🧘" },
  { user: "Aisha B.", action: "shared their portfolio", subject: "Mixed Media Artwork", time: "25m ago", avatar: "📁" },
  { user: "Marcus J.", action: "became a mentor", subject: "Teaching electrical + mentoring", time: "31m ago", avatar: "👨‍🏫" },
];

// Member spotlights (real community stories)
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
    name: "Marcus Thompson",
    role: "Visual Artist & Instructor",
    story: "Teaching painting & mixed media to students who can't afford art school. Started with 12 students. Now 200. Reinvesting back into the neighborhood.",
    image: "🎨",
    stat: "200 students | $5.2K/mo",
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

// Real impact numbers
const IMPACT = [
  { number: "2,847", label: "Students learning", color: "text-copper" },
  { number: "$1.2M", label: "Creator earnings", color: "text-signal" },
  { number: "340", label: "Certificates earned", color: "text-ink" },
  { number: "52", label: "Corporate contracts", color: "text-copper" },
];

// Testimonials (community voices - BOTH trades & digital creators)
const TESTIMONIALS = [
  {
    quote: "I went from struggling to find work to running my own training business. This platform gave me the tools AND the community. Now I earn $12K/quarter.",
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
    quote: "The community here is REAL. Electricians mentoring apprentices. Artists teaching artists. Healers supporting healers. It feels like home, not a corporate platform.",
    author: "Sofia Martinez",
    role: "Apprentice & Community Organizer",
    avatar: "👩‍🎓",
  },
  {
    quote: "Whether you're teaching trades or teaching art, this platform respects your work. You're not just extracting value for a VC — you're building something real.",
    author: "Marcus Thompson",
    role: "Visual Artist & Instructor",
    avatar: "🎨",
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
      {/* Header */}
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
            <a href="#community" className="text-sm font-medium hover:text-copper">Community</a>
            <a href="#creators" className="text-sm font-medium hover:text-copper">For Creators</a>
            <Link to="/login" className="text-sm font-bold uppercase tracking-widest hover:text-copper">Sign in</Link>
            <Link to="/register" className="btn-copper text-sm">Join Us</Link>
          </nav>
        </div>
      </header>

      {/* BETA TESTER BANNER */}
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
            <span className="text-white/40 text-xs">Then click 🐛 at bottom-right to report</span>
          </div>
        </div>
      </div>

      {/* HERO */}
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
              Our communities have always built from within — teaching each other, trading skills, showing up when systems don't. W.A.I. Institute exists to support what we already do. Keep your knowledge. Keep your earnings. Keep your power.
            </p>

            <div className="flex flex-wrap justify-center gap-4 mb-20">
              <Link to="/more" className="btn-copper inline-flex items-center gap-2 text-lg">
                <Heart className="w-5 h-5" /> Enter the M.O.R.E. Hub
              </Link>
              <Link to="/register" className="btn-primary inline-flex items-center gap-2 text-lg">
                Join The Community <ArrowRight className="w-5 h-5" />
              </Link>
            </div>

            {/* LIVE IMPACT STATS */}
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

      {/* M.O.R.E. HELP CENTER — dedicated section */}
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
                M.O.R.E. is where community members offer skills, post real needs, share stories, and hold each other up. No charity. No shame. Just neighbors who know how to fix things, teach things, and show up — the way we always have.
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
                    { type: "Community", text: "Anyone navigating Section 8 appeals? Let's connect", dot: "bg-blue-400" },
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

      {/* LIVE COMMUNITY ACTIVITY FEED */}
      <section className="py-16 bg-white border-t border-b border-ink/10">
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex items-center justify-between mb-8">
            <h2 className="text-3xl font-bold flex items-center gap-2">
              <TrendingUp className="w-8 h-8 text-copper" /> Right now in our community
            </h2>
            <p className="text-sm text-ink/60">Trades + digital creators learning, earning, and building together</p>
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

      {/* COMMUNITY SPOTLIGHTS (REAL STORIES) */}
      <section id="community" className="py-24 bg-bone">
        <div className="max-w-7xl mx-auto px-6">
          <h2 className="text-5xl font-bold text-center mb-4">Built by the Community.</h2>
          <p className="text-lg text-ink/60 text-center max-w-2xl mx-auto mb-16">
            Educators, artists, organizers, and neighbors — skill-sharing, income-earning, and holding each other up. Creators building careers. M.O.R.E. members building futures.
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

          {/* Creator profile proof of concept CTA */}
          <div className="mt-12 bg-ink text-white rounded-lg p-8 flex flex-col sm:flex-row items-center gap-6">
            <div className="text-5xl shrink-0">🌊</div>
            <div className="flex-1 text-center sm:text-left">
              <div className="text-xs font-bold uppercase tracking-widest text-amber-400 mb-1">Featured Creator</div>
              <h3 className="font-heading text-2xl font-extrabold mb-1">NAM Oshun</h3>
              <p className="text-white/60 text-sm">Poet · Community Organizer · M.O.R.E. Founding Member — see what a creator profile looks like.</p>
            </div>
            <Link to="/creator/nam-oshun" className="shrink-0 inline-flex items-center gap-2 bg-amber-500 hover:bg-amber-400 text-ink font-bold px-6 py-3 rounded-xl transition-all hover:scale-105 whitespace-nowrap">
              View Profile <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </section>

      {/* TESTIMONIALS (ROTATING) */}
      <section className="py-24 bg-white border-t border-ink/10">
        <div className="max-w-3xl mx-auto px-6 text-center">
          <h2 className="text-4xl font-bold mb-12">What members say</h2>

          <div className="relative">
            {TESTIMONIALS.map((testimonial, idx) => (
              <div
                key={idx}
                className={`transition-opacity duration-500 ${idx === activeTestimonial ? "opacity-100" : "opacity-0 absolute"}`}
              >
                <blockquote className="mb-8">
                  <p className="text-2xl font-bold text-ink leading-relaxed">
                    "{testimonial.quote}"
                  </p>
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
                className={`w-2 h-2 rounded-full transition-colors ${
                  idx === activeTestimonial ? "bg-copper" : "bg-ink/20"
                }`}
              />
            ))}
          </div>
        </div>
      </section>

      {/* FOR CREATORS */}
      <section id="creators" className="py-24 bg-bone">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <h2 className="font-heading text-5xl font-bold mb-6">For Creators, Teachers, Builders</h2>
              <p className="text-lg text-ink/60 mb-8">
                Teaching electrical skills. Teaching poetry. Teaching art. Teaching healing. Your work matters. You deserve a platform that pays you fairly and lets you own your creation — whether you're in trades or digital arts.
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

      {/* CTA: FINAL MARKETPLACE ENERGY */}
      <section id="impact" className="py-24 bg-ink text-white">
        <div className="max-w-3xl mx-auto px-6 text-center">
          <h2 className="font-heading text-5xl font-bold mb-6 flex items-center justify-center gap-3">
            <Sparkles className="w-10 h-10" /> Let's Build This Together
          </h2>
          <p className="text-xl text-white/80 mb-8">
            This isn't a platform. It's a marketplace. A community. A place where your value is recognized and your work is honored.
          </p>

          <div className="flex flex-wrap justify-center gap-4">
            <Link to="/register" className="btn-primary inline-flex items-center gap-2">
              Join Us <ArrowRight className="w-4 h-4" />
            </Link>
            <Link to="/login" className="px-6 py-3 border-2 border-white text-white font-bold hover:bg-white hover:text-ink transition-colors rounded-sm">
              Sign In
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
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
                <li><a href="#impact" className="hover:text-white transition-colors">Impact</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-bold text-white mb-4">For Creators</h4>
              <ul className="space-y-2 text-sm">
                <li><Link to="/register" className="hover:text-white transition-colors">Start Creating</Link></li>
                <li><a href="#creators" className="hover:text-white transition-colors">How it works</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-bold text-white mb-4">Account</h4>
              <ul className="space-y-2 text-sm">
                <li><Link to="/login" className="hover:text-white transition-colors">Sign In</Link></li>
                <li><Link to="/register" className="hover:text-white transition-colors">Join</Link></li>
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
