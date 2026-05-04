import { useEffect, useState } from "react";
import AppShell from "../components/AppShell";
import { api } from "../lib/api";
import { Link } from "react-router-dom";

export default function ModulesList() {
  const [modules, setModules] = useState([]);
  const [progress, setProgress] = useState([]);
  useEffect(() => {
    api.get("/modules").then((r) => setModules(r.data));
    api.get("/progress/me").then((r) => setProgress(r.data)).catch(() => {});
  }, []);
  const bySlug = Object.fromEntries(progress.map((p) => [p.module_slug, p]));

  return (
    <AppShell>
      <div className="px-10 py-10 max-w-6xl">
        <div className="overline text-copper">The Curriculum</div>
        <h1 className="font-heading text-4xl font-bold mt-2">Camper-to-Classroom · 12 Projects</h1>
        <p className="text-ink/60 mt-2 max-w-2xl">From first PPE fitting to final commissioning. Complete each module with a 70%+ quiz score to earn training hours toward your certificate.</p>

        <div className="grid md:grid-cols-2 gap-5 mt-10">
          {modules.map((m) => {
            const p = bySlug[m.slug];
            const badge = p?.status === "completed" ? "badge-signal" : p?.status === "in_progress" ? "badge-copper" : "badge-outline";
            const label = p?.status === "completed" ? "Completed" : p?.status === "in_progress" ? "In Progress" : "Not Started";
            return (
              <Link to={`/modules/${m.slug}`} key={m.slug} className="card-flat p-6 group" data-testid={`mod-card-${m.slug}`}>
                <div className="flex items-start justify-between">
                  <div className="font-heading text-xs font-black text-copper">MODULE {m.order.toString().padStart(2, "0")}</div>
                  <span className={badge}>{label}</span>
                </div>
                <div className="font-heading text-xl font-bold mt-3 text-ink group-hover:text-copper transition-colors">{m.title}</div>
                <p className="text-sm text-ink/70 mt-3 leading-relaxed">{m.summary}</p>
                <div className="mt-5 flex gap-4 text-xs overline text-ink/60">
                  <span>{m.hours}h</span>
                  <span>{m.tasks.length} tasks</span>
                  <span>{m.quiz?.length || 0} quiz</span>
                </div>
              </Link>
            );
          })}
        </div>
      </div>
    </AppShell>
  );
}
