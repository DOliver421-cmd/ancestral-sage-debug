import { Link } from "react-router-dom";
import PublicNav from "../components/PublicNav";
import BackButton from "../components/BackButton";
import { Zap, Cpu, Music, HardHat } from "lucide-react";

// Public course catalog. Marketing showcase that funnels to /register (new) and
// /modules (existing members). Tags mark what's free vs member-tier.
const TRACKS = [
  { icon: Zap, title: "Electrical & Trades", desc: "Hands-on workforce training toward real, skilled-trade careers.", tag: "Free + Member" },
  { icon: Cpu, title: "AI & Tech Literacy", desc: "Practical AI and digital skills — open to everyone, no barrier.", tag: "Free" },
  { icon: Music, title: "Arts & Music Business", desc: "Own your craft: rights, royalties, performance, production.", tag: "Member" },
  { icon: HardHat, title: "Workforce Readiness", desc: "Resume, interview, certifications, and on-ramps to work.", tag: "Free" },
];

export default function Courses() {
  return (
    <div className="min-h-screen bg-bone">
      <PublicNav />
      <div className="max-w-6xl mx-auto px-6 py-10">
        <BackButton to="/" />
        <div className="mt-6">
          <div className="overline text-copper">Courses</div>
          <h1 className="font-heading text-4xl font-bold text-ink mt-2">Learn a trade. Build a future.</h1>
          <p className="text-ink/60 mt-3 max-w-2xl">
            Start free, earn your way up. Many courses are open to everyone; deeper tracks unlock with membership.
          </p>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-8">
          {TRACKS.map((t) => {
            const Icon = t.icon;
            return (
              <div key={t.title} className="card-flat p-6">
                <div className="flex items-center justify-between">
                  <Icon className="w-7 h-7 text-copper" />
                  <span className="badge-signal">{t.tag}</span>
                </div>
                <div className="font-heading font-bold text-ink text-lg mt-3">{t.title}</div>
                <div className="text-sm text-ink/60 mt-1">{t.desc}</div>
                <Link to="/register" className="btn-copper text-sm inline-block mt-4">Start Learning</Link>
              </div>
            );
          })}
        </div>
        <div className="text-center mt-8">
          <Link to="/modules" className="text-sm font-bold text-copper">Already a member? Go to your curriculum →</Link>
        </div>
      </div>
    </div>
  );
}
