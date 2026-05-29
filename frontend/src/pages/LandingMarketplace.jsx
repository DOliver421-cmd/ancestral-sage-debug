import { Link } from "react-router-dom";
import {
  Heart, ArrowRight, TrendingUp,
  BookOpen, MessageSquare, Music, Users,
} from "lucide-react";
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

export default function LandingMarketplace() {
  return (
    <div className="min-h-screen bg-bone text-ink">

      <div style={{ height: 6, background: "linear-gradient(90deg,#c1121f 0 33.33%,#111 33.33% 66.66%,#0b6e4f 66.66%)" }} />

      <header className="sticky top-0 z-40" style={{ background: "linear-gradient(135deg,#2e1065,#4c1d95)", borderBottom: "3px solid var(--wai-gold)" }}>
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-3">
            <span className="text-2xl">🏛️</span>
            <div>
              <div className="overline leading-none text-amber-300">W.A.I.</div>
              <div className="font-heading font-bold text-sm leading-tight text-white">Institute</div>
            </div>
          </Link>
          <nav className="flex items-center gap-4">
            <Link to="/more" className="flex items-center gap-1.5 text-sm font-bold px-3 py-1 rounded-full transition-transform hover:scale-105" style={{ color: "#1a0b2e", background: "var(--wai-gold)" }}>
              <Heart className="w-3.5 h-3.5" /> M.O.R.E. Hub
            </Link>
            <Link to="/login" className="text-sm font-bold uppercase tracking-widest text-white/90 hover:text-white">Sign in</Link>
            <Link to="/register" className="text-sm font-bold px-4 py-2 rounded transition-transform hover:scale-105" style={{ background: "var(--wai-gold)", color: "#1a0b2e" }}>Join Us</Link>
          </nav>
        </div>
      </header>

      <div className="bg-ink text-white py-3 px-6">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2 text-sm">
          <div className="flex items-center gap-2 font-medium">
            <span className="text-lg">🐛</span>
            <span><strong>Beta Tester?</strong> Sign up → explore → report bugs → get $1. First 20 testers only.</span>
          </div>
          <div className="flex items-center gap-3 shrink-0">
            <Link to="/register" className="bg-copper hover:bg-copper/80 text-white font-bold px-4 py-1.5 rounded-lg text-xs transition-colors">
              Create Account
            </Link>
          </div>
        </div>
      </div>

      <section className="relative overflow-hidden py-32" style={{ background: "radial-gradient(900px 500px at 50% -5%, rgba(212,175,55,0.25), transparent), linear-gradient(165deg,#2e1065,#1a0a36 70%)" }}>
        <div className="absolute inset-0 pointer-events-none" style={{ opacity: 0.08, backgroundImage: "repeating-linear-gradient(45deg, var(--wai-gold) 0 2px, transparent 2px 26px)" }} />
        <div className="max-w-7xl mx-auto px-6 relative">
          <div className="text-center max-w-3xl mx-auto">
            <div className="inline-flex items-center gap-2 mb-6 px-4 py-2 rounded-full text-sm font-bold" style={{ background: "rgba(212,175,55,0.15)", border: "1px solid var(--wai-gold)", color: "var(--wai-gold-light)" }}>
              🥁 A festival of mutual aid, skill &amp; culture
            </div>
            <h1 className="font-heading text-6xl sm:text-7xl font-extrabold leading-tight mb-6 text-white">
              You're the <span style={{ color: "var(--wai-gold-light)" }}>teachers.</span><br />
              You're the <span style={{ color: "var(--wai-gold-light)" }}>makers.</span><br />
              You're the <span style={{ color: "var(--wai-gold-light)" }}>healers.</span>
            </h1>
            <p className="text-xl leading-relaxed mb-8 max-w-2xl mx-auto" style={{ color: "rgba(241,240,251,0.82)" }}>
              Our communities have always built from within — teaching each other, trading skills, showing up when systems don't.
              W.A.I. Institute exists to support what we already do. Keep your knowledge. Keep your earnings. Keep your power.
            </p>
            <div className="flex flex-wrap justify-center gap-4 mb-20">
              <Link to="/more" className="inline-flex items-center gap-2 text-lg font-bold px-6 py-3 rounded transition-transform hover:scale-105" style={{ background: "var(--wai-gold)", color: "#1a0b2e" }}>
                <Heart className="w-5 h-5" /> Enter the M.O.R.E. Hub
              </Link>
              <Link to="/supervisor/login" className="inline-flex items-center gap-2 text-lg font-bold px-6 py-3 rounded transition-transform hover:scale-105" style={{ background: "#0d7377", color: "white" }}>
                <ArrowRight className="w-5 h-5" /> Supervisor Login
              </Link>
              <Link to="/register" className="inline-flex items-center gap-2 text-lg font-bold px-6 py-3 rounded transition-transform hover:scale-105" style={{ border: "2px solid var(--wai-gold)", color: "var(--wai-gold-light)" }}>
                Join The Community <ArrowRight className="w-5 h-5" />
              </Link>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6 max-w-2xl mx-auto">
              {[
                { number: "2,847", label: "Students learning" },
                { number: "$1.2M", label: "Creator earnings" },
                { number: "340", label: "Certificates earned" },
                { number: "52", label: "Corporate contracts" },
              ].map((item) => (
                <div key={item.label} className="p-4 rounded-lg" style={{ background: "rgba(255,255,255,0.05)", border: "1px solid var(--wai-border)" }}>
                  <div className="text-3xl font-black" style={{ color: "var(--wai-gold-light)" }}>{item.number}</div>
                  <div className="text-xs mt-1" style={{ color: "rgba(241,240,251,0.6)" }}>{item.label}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-12">
            <h2 className="font-heading text-4xl font-extrabold mb-4">Explore W.A.I.</h2>
            <p className="text-ink/60 max-w-xl mx-auto">Everything starts here. Each section has a back button to return to this page.</p>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
            <Link to="/more-help-center" className="group bg-bone border border-ink/10 rounded-2xl p-6 hover:shadow-lg hover:scale-[1.02] transition-all">
              <div className="text-4xl mb-3">🤝</div>
              <h3 className="font-heading font-extrabold text-lg mb-1">MORE Help Center</h3>
              <p className="text-ink/60 text-sm leading-relaxed">Skill exchange, mutual aid, community support. Free and open to all.</p>
              <span className="inline-flex items-center gap-1 text-xs font-bold text-copper mt-3 group-hover:gap-2 transition-all">Enter hub <ArrowRight className="w-3 h-3" /></span>
            </Link>
            <Link to="/supervisor/login" className="group bg-bone border border-ink/10 rounded-2xl p-6 hover:shadow-lg hover:scale-[1.02] transition-all">
              <div className="text-4xl mb-3">📜</div>
              <h3 className="font-heading font-extrabold text-lg mb-1">Supervisor Login</h3>
              <p className="text-ink/60 text-sm leading-relaxed">Access executive controls and secure mode selection inside the centralized MORE Help Center.</p>
              <span className="inline-flex items-center gap-1 text-xs font-bold text-copper mt-3 group-hover:gap-2 transition-all">Sign in as supervisor <ArrowRight className="w-3 h-3" /></span>
            </Link>
            <Link to="/courses" className="group bg-bone border border-ink/10 rounded-2xl p-6 hover:shadow-lg hover:scale-[1.02] transition-all">
              <div className="text-4xl mb-3">📚</div>
              <h3 className="font-heading font-extrabold text-lg mb-1">Courses</h3>
              <p className="text-ink/60 text-sm leading-relaxed">Trades, AI literacy, music business, workforce readiness — start free.</p>
              <span className="inline-flex items-center gap-1 text-xs font-bold text-copper mt-3 group-hover:gap-2 transition-all">Browse courses <ArrowRight className="w-3 h-3" /></span>
            </Link>
            <Link to="/community" className="group bg-bone border border-ink/10 rounded-2xl p-6 hover:shadow-lg hover:scale-[1.02] transition-all">
              <div className="text-4xl mb-3">💬</div>
              <h3 className="font-heading font-extrabold text-lg mb-1">Community</h3>
              <p className="text-ink/60 text-sm leading-relaxed">Spotlights, stories, skill swaps, and members making moves.</p>
              <span className="inline-flex items-center gap-1 text-xs font-bold text-copper mt-3 group-hover:gap-2 transition-all">Meet the community <ArrowRight className="w-3 h-3" /></span>
            </Link>
            <Link to="/creators" className="group bg-bone border border-ink/10 rounded-2xl p-6 hover:shadow-lg hover:scale-[1.02] transition-all">
              <div className="text-4xl mb-3">✨</div>
              <h3 className="font-heading font-extrabold text-lg mb-1">Creators</h3>
              <p className="text-ink/60 text-sm leading-relaxed">70% revenue. Full ownership. Build community on your terms.</p>
              <span className="inline-flex items-center gap-1 text-xs font-bold text-copper mt-3 group-hover:gap-2 transition-all">See creators <ArrowRight className="w-3 h-3" /></span>
            </Link>
            <Link to="/plans" className="group bg-bone border border-ink/10 rounded-2xl p-6 hover:shadow-lg hover:scale-[1.02] transition-all">
              <div className="text-4xl mb-3">📋</div>
              <h3 className="font-heading font-extrabold text-lg mb-1">Plans</h3>
              <p className="text-ink/60 text-sm leading-relaxed">Free access, premium mentoring, and corporate training partnerships.</p>
              <span className="inline-flex items-center gap-1 text-xs font-bold text-copper mt-3 group-hover:gap-2 transition-all">View plans <ArrowRight className="w-3 h-3" /></span>
            </Link>
            <Link to="/internships" className="group bg-bone border border-ink/10 rounded-2xl p-6 hover:shadow-lg hover:scale-[1.02] transition-all">
              <div className="text-4xl mb-3">🎓</div>
              <h3 className="font-heading font-extrabold text-lg mb-1">Internships</h3>
              <p className="text-ink/60 text-sm leading-relaxed">Credit-eligible, community-based. Content, music, outreach, and dev.</p>
              <span className="inline-flex items-center gap-1 text-xs font-bold text-copper mt-3 group-hover:gap-2 transition-all">Apply now <ArrowRight className="w-3 h-3" /></span>
            </Link>
          </div>
        </div>
      </section>

      <section className="py-16 bg-white border-t border-b border-ink/10">
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex items-center justify-between mb-8">
            <h2 className="text-3xl font-bold flex items-center gap-2">
              <TrendingUp className="w-8 h-8 text-copper" /> Right now in our community
            </h2>
            <p className="text-sm text-ink/60 hidden sm:block">Trades · arts · music · healing · community</p>
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

      <section className="py-24 bg-ink text-white">
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
            <Link to="/register" className="inline-flex items-center gap-2 px-6 py-3 rounded-sm text-lg font-bold transition-transform hover:scale-105" style={{ background: "var(--wai-gold)", color: "#1a0b2e" }}>
              Join Us <ArrowRight className="w-5 h-5" />
            </Link>
            <Link to="/more" className="inline-flex items-center gap-2 px-6 py-3 border-2 border-amber-400 text-amber-300 font-bold hover:bg-amber-400 hover:text-ink transition-colors rounded-sm text-lg">
              <Heart className="w-5 h-5" /> Visit M.O.R.E.
            </Link>
          </div>
        </div>
      </section>

      <footer className="bg-ink/95 text-white/60 border-t border-white/10 py-12">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid md:grid-cols-4 gap-8 mb-12">
            <div>
              <span className="font-bold text-white block mb-2">W.A.I. Institute</span>
              <p className="text-sm">Building community. Supporting creators. Changing lives.</p>
            </div>
            <div>
              <h4 className="font-bold text-white mb-4">Community</h4>
              <ul className="space-y-2 text-sm">
                <li><Link to="/more" className="text-amber-400 hover:text-amber-300 font-semibold transition-colors">M.O.R.E. Help Center</Link></li>
                <li><Link to="/community" className="hover:text-white transition-colors">Stories</Link></li>
                <li><Link to="/courses" className="hover:text-white transition-colors">Music & Arts</Link></li>
                <li><Link to="/internships" className="hover:text-white transition-colors">Internships</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="font-bold text-white mb-4">For Creators</h4>
              <ul className="space-y-2 text-sm">
                <li><Link to="/register" className="hover:text-white transition-colors">Start Creating</Link></li>
                <li><Link to="/creators" className="hover:text-white transition-colors">How it works</Link></li>
                <li><Link to="/courses" className="hover:text-white transition-colors">Music & A&R Courses</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="font-bold text-white mb-4">Account</h4>
              <ul className="space-y-2 text-sm">
                <li><Link to="/login" className="hover:text-white transition-colors">Sign In</Link></li>
                <li><Link to="/register" className="hover:text-white transition-colors">Join</Link></li>
                <li><a href="mailto:poetgames3@gmail.com" className="hover:text-white transition-colors">Advertise</a></li>
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
