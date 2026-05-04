import { useEffect, useState } from "react";
import AppShell from "../components/AppShell";
import { api } from "../lib/api";
import { Link } from "react-router-dom";
import { useAuth } from "../lib/auth";
import { ArrowRight, Award, BookOpen, Clock, Flame } from "lucide-react";

const DAILY_VERSES = [
  { ref: "Proverbs 22:29", text: "Do you see someone skilled in their work? They will serve before kings." },
  { ref: "Colossians 3:23", text: "Whatever you do, work at it with all your heart, as working for the Lord." },
  { ref: "Isaiah 40:31", text: "Those who hope in the Lord will renew their strength." },
  { ref: "Philippians 4:13", text: "I can do all this through him who gives me strength." },
  { ref: "2 Timothy 2:15", text: "Be diligent to present yourself approved to God, a worker who does not need to be ashamed." },
];

export default function StudentDashboard() {
  const { user } = useAuth();
  const [modules, setModules] = useState([]);
  const [progress, setProgress] = useState([]);
  const [certs, setCerts] = useState([]);

  useEffect(() => {
    api.get("/modules").then((r) => setModules(r.data));
    api.get("/progress/me").then((r) => setProgress(r.data));
    api.get("/certificates/me").then((r) => setCerts(r.data));
  }, []);

  const verse = DAILY_VERSES[new Date().getDate() % DAILY_VERSES.length];
  const completed = progress.filter((p) => p.status === "completed").length;
  const hours = progress.filter((p) => p.status === "completed").reduce((a, p) => a + (p.hours_logged || 0), 0);
  const pct = modules.length ? Math.round((completed / modules.length) * 100) : 0;
  const progressBySlug = Object.fromEntries(progress.map((p) => [p.module_slug, p]));
  const nextModule = modules.find((m) => progressBySlug[m.slug]?.status !== "completed");

  return (
    <AppShell>
      <div className="px-10 py-10 max-w-6xl">
        <div className="flex items-end justify-between mb-10">
          <div>
            <div className="overline text-copper">Apprentice</div>
            <h1 className="font-heading text-4xl font-bold mt-2">Welcome back, {user?.full_name?.split(" ")[0]}.</h1>
            <p className="text-ink/60 mt-2">Your tools, your associate, your progress — all in one shop.</p>
          </div>
          {nextModule && (
            <Link to={`/modules/${nextModule.slug}`} className="btn-primary inline-flex items-center gap-2" data-testid="btn-continue">
              Continue {nextModule.order.toString().padStart(2, "0")} <ArrowRight className="w-4 h-4" />
            </Link>
          )}
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-5 mb-10">
          <StatCard icon={BookOpen} label="Modules Completed" value={`${completed}/${modules.length || 12}`} testid="stat-modules" />
          <StatCard icon={Clock} label="Training Hours" value={hours} testid="stat-hours" />
          <StatCard icon={Award} label="Certificates Earned" value={certs.length} testid="stat-certs" />
          <StatCard icon={Flame} label="Progress" value={`${pct}%`} testid="stat-progress" accent />
        </div>

        {/* Progress bar */}
        <div className="card-flat p-6 mb-10" data-testid="progress-bar">
          <div className="flex justify-between items-center mb-3">
            <div className="overline text-ink/60">Camper-to-Classroom Path</div>
            <div className="font-mono text-sm font-semibold">{completed} of {modules.length || 12} projects</div>
          </div>
          <div className="w-full h-3 bg-ink/10">
            <div className="h-full bg-copper transition-all duration-500" style={{ width: `${pct}%` }} />
          </div>
        </div>

        {/* Modules grid + devotional */}
        <div className="grid lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="font-heading text-2xl font-bold">Your Curriculum</h2>
              <Link to="/modules" className="text-sm font-bold text-copper uppercase tracking-widest" data-testid="link-all-modules">View all →</Link>
            </div>
            {modules.slice(0, 6).map((m) => {
              const p = progressBySlug[m.slug];
              const state = p?.status === "completed" ? "Completed" : p?.status === "in_progress" ? "In Progress" : "Not Started";
              const badge = p?.status === "completed" ? "badge-signal" : p?.status === "in_progress" ? "badge-copper" : "badge-outline";
              return (
                <Link key={m.slug} to={`/modules/${m.slug}`} className="card-flat p-5 flex items-center justify-between group" data-testid={`module-${m.slug}`}>
                  <div className="flex items-center gap-5">
                    <div className="w-12 h-12 bg-ink text-signal font-heading font-black text-xl flex items-center justify-center">
                      {m.order.toString().padStart(2, "0")}
                    </div>
                    <div>
                      <div className="font-heading font-bold text-ink group-hover:text-copper transition-colors">{m.title}</div>
                      <div className="text-xs text-ink/60 mt-1">{m.hours}h • {m.competencies.length} competencies</div>
                    </div>
                  </div>
                  <span className={badge}>{state}</span>
                </Link>
              );
            })}
          </div>

          <aside className="space-y-6">
            <div className="bg-ink text-white p-6" data-testid="devotional-card">
              <div className="overline text-signal">Today's Devotional</div>
              <div className="font-heading text-lg font-semibold mt-4 leading-snug">"{verse.text}"</div>
              <div className="mt-4 text-xs text-white/60 uppercase tracking-widest">{verse.ref}</div>
              <div className="mt-6 pt-6 border-t border-white/10">
                <div className="overline text-signal">Reflect</div>
                <div className="text-sm text-white/80 mt-2 leading-relaxed">Whose trade will serve your neighborhood today? Pick up a tool and practice one skill before class.</div>
              </div>
            </div>

            <div className="card-flat p-6">
              <div className="overline text-copper">Upcoming</div>
              {nextModule ? (
                <>
                  <div className="font-heading font-bold mt-2">{nextModule.title}</div>
                  <div className="text-sm text-ink/60 mt-1">{nextModule.hours} hours • {nextModule.tasks.length} tasks</div>
                  <Link to={`/modules/${nextModule.slug}`} className="btn-copper mt-4 inline-block text-xs" data-testid="btn-start-next">Open Module</Link>
                </>
              ) : <div className="text-sm text-ink/60 mt-2">All modules complete. Claim your capstone certificate.</div>}
            </div>
          </aside>
        </div>
      </div>
    </AppShell>
  );
}

function StatCard({ icon: Icon, label, value, testid, accent }) {
  return (
    <div className={`card-flat p-6 ${accent ? "bg-signal border-ink" : ""}`} data-testid={testid}>
      <Icon className={`w-5 h-5 ${accent ? "text-ink" : "text-copper"}`} />
      <div className="font-heading text-3xl font-black mt-3 text-ink">{value}</div>
      <div className="overline text-ink/60 mt-1">{label}</div>
    </div>
  );
}
