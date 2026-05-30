import { useEffect, useState } from "react";
import AppShell from "../components/AppShell";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import { Link } from "react-router-dom";
import { Lock, Zap } from "lucide-react";

export default function ModulesList() {
  const { user } = useAuth();
  const [modules, setModules] = useState([]);
  const [progress, setProgress] = useState([]);
  useEffect(() => {
    api.get("/modules").then((r) => setModules(r.data));
    if (user) {
      api.get("/progress/me").then((r) => setProgress(r.data)).catch(() => {});
    }
  }, [user]);
  const bySlug = Object.fromEntries(progress.map((p) => [p.module_slug, p]));

  return (
    <AppShell>
      <div className="px-10 py-10 max-w-6xl">
        <div className="overline text-copper">The Curriculum</div>
        <h1 className="font-heading text-4xl font-bold mt-2">Camper-to-Classroom</h1>
        <p className="text-ink/60 mt-2 max-w-2xl">Start with free intro modules — no sign-up needed. Enroll to unlock the full 12-module program and earn your certificate.</p>

        <div className="grid md:grid-cols-2 gap-5 mt-10">
          {modules.map((m) => {
            const p = bySlug[m.slug];
            const isFree = m.free;
            const isLocked = !isFree && !user;
            const badge = p?.status === "completed" ? "badge-signal" : p?.status === "in_progress" ? "badge-copper" : isFree ? "badge-signal" : "badge-outline";
            const label = p?.status === "completed" ? "Completed" : p?.status === "in_progress" ? "In Progress" : isFree ? "FREE" : user ? "Not Started" : "Enroll to Unlock";
            return (
              <Link to={isLocked ? "/register" : `/modules/${m.slug}`} key={m.slug} className="card-flat p-6 group relative" data-testid={`mod-card-${m.slug}`}>
                {isLocked && (
                  <div className="absolute inset-0 bg-white/60 backdrop-blur-[1px] rounded-2xl z-10 flex items-center justify-center">
                    <div className="text-center">
                      <Lock className="w-6 h-6 text-ink/30 mx-auto mb-2" />
                      <div className="text-sm font-bold text-ink/50">Sign up to unlock</div>
                    </div>
                  </div>
                )}
                <div className="flex items-start justify-between">
                  <div className="font-heading text-xs font-black text-copper">{isFree ? "FREE INTRO" : `MODULE ${m.order.toString().padStart(2, "0")}`}</div>
                  <span className={`${badge} flex items-center gap-1`}>
                    {isFree && <Zap className="w-3 h-3" />}{label}
                  </span>
                </div>
                <div className="font-heading text-xl font-bold mt-3 text-ink group-hover:text-copper transition-colors">{m.title}</div>
                <p className="text-sm text-ink/70 mt-3 leading-relaxed">{m.summary}</p>
                <div className="mt-5 flex gap-4 text-xs overline text-ink/60">
                  <span>{m.hours}h</span>
                  <span>{m.tasks.length} tasks</span>
                  {m.points && <span className="text-amber-600">+{m.points} pts</span>}
                  {m.leads_to && <span className="text-copper">Leads into full program</span>}
                </div>
              </Link>
            );
          })}
        </div>
      </div>
    </AppShell>
  );
}
