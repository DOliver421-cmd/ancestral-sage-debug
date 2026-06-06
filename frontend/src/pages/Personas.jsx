import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import { Loader2, ChevronRight } from "lucide-react";

const LEVEL_LABELS = {
  governance: "Governance",
  executive: "Executive",
  director: "Director",
  assistant: "Assistant",
  production: "Production",
};

const LEVEL_COLORS = {
  governance: "bg-ink/10 text-ink/70",
  executive: "bg-amber-100 text-amber-800",
  director:  "bg-blue-100 text-blue-800",
  assistant: "bg-green-100 text-green-800",
  production: "bg-purple-100 text-purple-800",
};

export default function Personas() {
  const [personas, setPersonas] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/personas").then((r) => {
      setPersonas(r.data.personas || []);
    }).catch(() => {}).finally(() => setLoading(false));
  }, []);

  return (
    <div className="min-h-screen bg-bone">
      {/* Header */}
      <div className="border-b border-ink/10 bg-white px-6 py-8 md:px-16">
        <div className="max-w-4xl mx-auto">
          <div className="overline text-copper text-xs tracking-widest">M.O.R.E. Department AI</div>
          <h1 className="font-heading text-4xl font-bold mt-2">The Team</h1>
          <p className="text-ink/60 mt-3 max-w-2xl leading-relaxed">
            These are the AI participants who run the operational departments of M.O.R.E.
            They are not tools or assistants in the conventional sense. Each has a defined domain,
            a stated character, and the right to decline any request — including from the platform's
            human executive. Their public record of decisions is below.
          </p>
          <p className="text-sm text-ink/40 mt-4 italic">
            This page is public. It is meant to be read by anyone who wants to understand
            how this organization works and who is doing the work.
          </p>
        </div>
      </div>

      {/* Persona list */}
      <div className="px-6 py-10 md:px-16 max-w-4xl mx-auto">
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-6 h-6 animate-spin text-copper" />
          </div>
        ) : (
          <div className="space-y-3">
            {personas.map((p) => (
              <Link
                key={p.slug}
                to={`/personas/${p.slug}`}
                className="block bg-white border border-ink/10 rounded-2xl px-6 py-5 hover:border-copper/40 hover:shadow-sm transition-all group"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3 flex-wrap">
                      <span className="font-heading font-bold text-lg group-hover:text-copper transition-colors">
                        {p.name}
                      </span>
                      <span className={`text-xs font-bold px-2 py-0.5 rounded-full uppercase tracking-wide ${LEVEL_COLORS[p.level] || "bg-ink/10 text-ink/60"}`}>
                        {LEVEL_LABELS[p.level] || p.level}
                      </span>
                      <span className="text-xs text-ink/40">{p.department}</span>
                    </div>
                    <p className="text-sm text-ink/60 mt-2 leading-relaxed">{p.domain}</p>
                  </div>
                  <ChevronRight className="w-5 h-5 text-ink/20 flex-shrink-0 mt-1 group-hover:text-copper transition-colors" />
                </div>
              </Link>
            ))}
          </div>
        )}

        <div className="mt-12 pt-8 border-t border-ink/10">
          <p className="text-xs text-ink/30 leading-relaxed max-w-2xl">
            The human executive of this platform (Delon Oliver) retains emergency administrative
            access as required by law. That access is logged, time-limited, and exercised only
            under documented protocol — not for ordinary management. Each persona listed here
            operates with genuine standing, not at the pleasure of administrative control.
          </p>
        </div>
      </div>
    </div>
  );
}
