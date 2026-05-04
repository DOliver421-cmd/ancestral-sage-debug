import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import AppShell from "../components/AppShell";
import { api } from "../lib/api";
import { ShieldCheck, Clock } from "lucide-react";

export default function ComplianceList() {
  const [mods, setMods] = useState([]);
  useEffect(() => { api.get("/compliance").then((r) => setMods(r.data)); }, []);
  return (
    <AppShell>
      <div className="px-10 py-10 max-w-6xl">
        <div className="overline text-copper">Compliance Tracks</div>
        <h1 className="font-heading text-4xl font-bold mt-2 flex items-center gap-3"><ShieldCheck className="w-8 h-8 text-copper" /> OSHA / NFPA / PPE / LOTO</h1>
        <p className="text-ink/60 mt-2 max-w-2xl">Required compliance training. Some certifications expire — keep them current.</p>
        <div className="grid md:grid-cols-2 gap-5 mt-10">
          {mods.map((m) => {
            const p = m.my_progress;
            const badge = p?.status === "completed" ? "badge-signal" : "badge-outline";
            return (
              <Link key={m.slug} to={`/compliance/${m.slug}`} className="card-flat p-6 group" data-testid={`comp-mod-${m.slug}`}>
                <div className="flex items-start justify-between">
                  <div className="overline text-copper">COMPLIANCE · {m.hours}h{m.expires_months ? ` · ${m.expires_months}mo expiry` : ""}</div>
                  <span className={badge}>{p?.status === "completed" ? "Completed" : "Not Started"}</span>
                </div>
                <div className="font-heading text-xl font-bold mt-3 group-hover:text-copper transition-colors">{m.title}</div>
                <p className="text-sm text-ink/70 mt-2 leading-relaxed">{m.summary}</p>
                {p?.expires_at && (
                  <div className="mt-3 text-xs text-ink/60 flex items-center gap-2"><Clock className="w-3 h-3" /> Expires {new Date(p.expires_at).toLocaleDateString()}</div>
                )}
              </Link>
            );
          })}
        </div>
      </div>
    </AppShell>
  );
}
