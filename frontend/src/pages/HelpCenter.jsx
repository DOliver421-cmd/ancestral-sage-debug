import { Link } from "react-router-dom";
import PublicNav from "../components/PublicNav";
import BackButton from "../components/BackButton";
import { ArrowRight, Home, Scale, Utensils, Briefcase, GraduationCap, HeartPulse } from "lucide-react";

// Public M.O.R.E. Help Center — 6 resource categories, each linking to a real
// destination (the exchange, the legal tool, the course catalog). No dead ends.
const CATEGORIES = [
  { icon: Home, title: "Housing", desc: "Help with rent, notices, and shelter resources.", to: "/more" },
  { icon: Scale, title: "Legal Help", desc: "Understand letters, bills, and legal papers in plain words.", to: "/more/litigation" },
  { icon: Utensils, title: "Food & Essentials", desc: "Connect to food, clothing, and everyday support.", to: "/more" },
  { icon: Briefcase, title: "Jobs & Training", desc: "Workforce training and job-readiness pathways.", to: "/courses" },
  { icon: GraduationCap, title: "Education", desc: "Free courses and learning for every level.", to: "/courses" },
  { icon: HeartPulse, title: "Health & Wellness", desc: "Healing, wellness, and community care.", to: "/more" },
];

export default function HelpCenter() {
  return (
    <div className="min-h-screen bg-bone">
      <PublicNav />
      <div className="max-w-6xl mx-auto px-6 py-10">
        <BackButton to="/" />
        <div className="mt-6">
          <div className="overline" style={{ color: "var(--wai-purple)" }}>M.O.R.E. Help Center</div>
          <h1 className="font-heading text-4xl font-bold text-ink mt-2">Michael Oliver Resource Exchange</h1>
          <p className="text-ink/60 mt-3 max-w-2xl">
            Ordinary people, given the right structure, take extraordinary care of each other. Find help — or offer it.
          </p>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mt-8">
          {CATEGORIES.map((c) => {
            const Icon = c.icon;
            return (
              <Link key={c.title} to={c.to} className="card-flat p-6 block" style={{ borderTop: "4px solid var(--wai-gold)" }}>
                <Icon className="w-7 h-7" style={{ color: "var(--wai-purple)" }} />
                <div className="font-heading font-bold text-ink text-lg mt-3">{c.title}</div>
                <div className="text-sm text-ink/60 mt-1">{c.desc}</div>
              </Link>
            );
          })}
        </div>
        <div className="mt-12 rounded-[28px] border border-[#e6d0ae] bg-[#fff8ee] p-8 shadow-[0_18px_45px_rgba(97,60,20,0.08)]">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <div className="overline" style={{ color: "#9d6b33" }}>Supervisor Access</div>
              <h2 className="font-heading text-3xl font-bold text-ink">Supervisor controls are part of MORE Help Center</h2>
            </div>
            <Link to="/supervisor/login" className="inline-flex items-center gap-2 rounded-full bg-[#0d7377] px-5 py-3 text-sm font-semibold text-white transition hover:bg-[#095b5e]">
              Supervisor Login <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
          <p className="mt-4 text-ink/70 max-w-2xl">
            Sign in as an executive supervisor to access secure oversight and the centralized MORE Help Center experience. There is no separate supervisor hub page.
          </p>
        </div>
      </div>
    </div>
  );
}
