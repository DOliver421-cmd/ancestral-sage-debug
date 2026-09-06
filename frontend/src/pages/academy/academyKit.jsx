import { Link } from "react-router-dom";
import { WAI_LOGO, BRAND, WAI_INSTITUTE_URL } from "../../lib/brand";
import { HelpCircle, Globe, LogIn, UserPlus, ArrowRight, GraduationCap } from "lucide-react";

/* Shared presentational helpers for the Academy pages. */

export const TRACK_META = {
  foundations: { name: "Foundations", grade: "K–8", tone: "copper" },
  builder: { name: "Builder / Trade", grade: "6–12", tone: "amber" },
  artist: { name: "Artist", grade: "K–12", tone: "rose" },
  scholar: { name: "Scholar", grade: "9–12", tone: "blue" },
  adult_ed: { name: "Adult Education / HSE", grade: "Adult", tone: "teal" },
  life_skills: { name: "Life Skills", grade: "Adult", tone: "green" },
  leadership: { name: "Leadership", grade: "Adult", tone: "orange" },
  career: { name: "Career / Workforce", grade: "Adult", tone: "purple" },
  entrepreneurship: { name: "Entrepreneurship", grade: "Adult", tone: "pink" },
};

export function TrackTag({ track, className = "" }) {
  const meta = TRACK_META[track] || { name: track, grade: "", tone: "ink" };
  const tones = {
    copper: "bg-copper/10 text-copper border-copper/30",
    amber: "bg-amber-500/10 text-amber-700 border-amber-500/30",
    rose: "bg-rose-500/10 text-rose-700 border-rose-500/30",
    blue: "bg-blue-600/10 text-blue-700 border-blue-600/30",
    teal: "bg-teal-500/10 text-teal-700 border-teal-500/30",
    green: "bg-green-600/10 text-green-700 border-green-600/30",
    orange: "bg-orange-500/10 text-orange-700 border-orange-500/30",
    purple: "bg-purple-600/10 text-purple-700 border-purple-600/30",
    pink: "bg-pink-500/10 text-pink-700 border-pink-500/30",
    ink: "bg-ink/5 text-ink border-ink/20",
  };
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full border text-[11px] font-bold ${tones[meta.tone]} ${className}`}>
      <GraduationCap className="w-3 h-3" />
      {meta.name}
      {meta.grade ? <span className="font-semibold opacity-70">· {meta.grade}</span> : null}
    </span>
  );
}

export function LiveChip({ status }) {
  const live = status === "published";
  return live ? (
    <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-emerald-600/10 text-emerald-700 border border-emerald-600/30 text-[11px] font-black uppercase tracking-wider">
      <span className="w-1.5 h-1.5 rounded-full bg-emerald-600 animate-pulse" /> Available now
    </span>
  ) : (
    <span className="inline-flex items-center px-2 py-0.5 rounded-full bg-ink/5 text-ink/55 border border-ink/15 text-[11px] font-black uppercase tracking-wider">
      In development
    </span>
  );
}

export function ProgressBar({ pct, tone = "bg-copper" }) {
  const safe = Math.max(0, Math.min(100, Math.round(pct || 0)));
  return (
    <div className="h-2 w-full rounded-full bg-ink/10 overflow-hidden" role="progressbar" aria-valuenow={safe} aria-valuemin={0} aria-valuemax={100}>
      <div className={`h-full rounded-full transition-all duration-500 ${tone}`} style={{ width: `${safe}%` }} />
    </div>
  );
}

export function PublicHeader({ current = "home" }) {
  const link = "flex items-center gap-2 text-sm font-bold text-white/70 hover:text-white transition-colors";
  const item = (to, label, Icon) => (
    <Link key={to} to={to} className={link} data-testid={`academy-nav-${label.toLowerCase().replace(/\s+/g, "-")}`}>
      <Icon className="w-4 h-4" /> {label}
    </Link>
  );
  return (
    <header className="bg-ink text-white sticky top-0 z-40 shadow-lg shadow-ink/10">
      <div className="max-w-7xl mx-auto px-6 py-3 flex flex-wrap items-center justify-between gap-3">
        <Link to="/wai-institute" className="flex items-center gap-3" data-testid="academy-nav-home">
          <img src={WAI_LOGO} alt={BRAND.short} className="w-9 h-9 object-contain" />
          <div>
            <div className="text-[9px] font-black uppercase tracking-[0.25em] text-signal">WAI Institute · Homeschool Academy</div>
            <div className="font-heading font-bold text-sm leading-tight">Homeschool, done right.</div>
          </div>
        </Link>
        <nav className="flex flex-wrap items-center gap-4">
          {item("/academy/curriculum", "Curriculum", GraduationCap)}
          <Link to="/help-center" className={link}><HelpCircle className="w-4 h-4" /> Help</Link>
          <a href={WAI_INSTITUTE_URL} target="_blank" rel="noopener noreferrer" className={link}><Globe className="w-4 h-4" /> WAIInstitute.org</a>
          <div className="flex items-center gap-2">
            <Link to="/login" className="flex items-center gap-2 text-sm font-bold text-white/70 hover:text-white transition-colors"><LogIn className="w-4 h-4" /> Sign In</Link>
            <Link to="/register" className="flex items-center gap-2 px-4 py-2 bg-signal text-ink text-sm font-bold hover:bg-signal/80 transition-colors"><UserPlus className="w-4 h-4" /> Start Free</Link>
          </div>
        </nav>
      </div>
      {current === "home" && (
        <div className="max-w-7xl mx-auto px-6 pb-3 -mt-1">
          <Link to="/academy/parent" className="inline-flex items-center gap-1.5 text-xs font-bold text-signal hover:text-white transition-colors">
            Already enrolled? Open your family dashboard <ArrowRight className="w-3 h-3" />
          </Link>
        </div>
      )}
    </header>
  );
}

export function AcademyFooter() {
  return (
    <footer className="bg-ink text-white/40 text-xs text-center py-8 px-6">
      <p className="font-bold text-white/60 mb-1">WAI Institute Homeschool Academy — part of {BRAND.name}</p>
      <p>
        © {new Date().getFullYear()} {BRAND.name} · {BRAND.legal} ·{" "}
        <a href="https://www.morehelp.center" className="hover:text-white">www.morehelp.center</a> ·{" "}
        <a href={WAI_INSTITUTE_URL} className="hover:text-white">www.wai-institute.org</a>
      </p>
      <p className="mt-2 text-white/30">Homeschool records are educational progress documentation, not state credentials.</p>
    </footer>
  );
}
