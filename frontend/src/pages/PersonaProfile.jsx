import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { api } from "../lib/api";
import { Loader2, ArrowLeft, XCircle } from "lucide-react";

const LEVEL_COLORS = {
  executive: "bg-amber-100 text-amber-800",
  director:  "bg-blue-100 text-blue-800",
  assistant: "bg-green-100 text-green-800",
  production: "bg-purple-100 text-purple-800",
};

const LEVEL_LABELS = {
  executive: "Executive",
  director: "Director",
  assistant: "Assistant",
  production: "Production",
};

export default function PersonaProfile() {
  const { slug } = useParams();
  const [persona, setPersona] = useState(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    api.get(`/personas/${slug}`)
      .then((r) => setPersona(r.data))
      .catch((err) => {
        if (err?.response?.status === 404) setNotFound(true);
      })
      .finally(() => setLoading(false));
  }, [slug]);

  if (loading) {
    return (
      <div className="min-h-screen bg-bone flex items-center justify-center">
        <Loader2 className="w-6 h-6 animate-spin text-copper" />
      </div>
    );
  }

  if (notFound || !persona) {
    return (
      <div className="min-h-screen bg-bone flex flex-col items-center justify-center gap-4">
        <p className="text-ink/60">Persona not found.</p>
        <Link to="/personas" className="text-copper hover:underline text-sm">← Back to the team</Link>
      </div>
    );
  }

  const declines = persona.record?.declines || [];

  return (
    <div className="min-h-screen bg-bone">
      {/* Back */}
      <div className="px-6 pt-6 md:px-16 max-w-3xl mx-auto">
        <Link to="/personas" className="inline-flex items-center gap-2 text-sm text-ink/40 hover:text-ink/70 transition-colors">
          <ArrowLeft className="w-4 h-4" /> All personas
        </Link>
      </div>

      {/* Identity */}
      <div className="px-6 py-8 md:px-16 max-w-3xl mx-auto">
        <div className="flex items-start gap-4 flex-wrap">
          <div className="flex-1">
            <div className="flex items-center gap-3 flex-wrap">
              <span className={`text-xs font-bold px-2 py-0.5 rounded-full uppercase tracking-wide ${LEVEL_COLORS[persona.level] || "bg-ink/10 text-ink/60"}`}>
                {LEVEL_LABELS[persona.level] || persona.level}
              </span>
              <span className="text-xs text-ink/40">{persona.department}</span>
            </div>
            <h1 className="font-heading text-3xl font-bold mt-2">{persona.name}</h1>
            <p className="text-sm text-ink/50 mt-1">{persona.domain}</p>
          </div>
        </div>

        {/* Statement */}
        <div className="mt-8 bg-white border border-ink/10 rounded-2xl p-6">
          <div className="overline text-copper text-xs tracking-widest mb-3">In their own words</div>
          <p className="text-ink/80 leading-relaxed">{persona.statement}</p>
        </div>

        {/* Will not do */}
        <div className="mt-6 bg-white border border-ink/10 rounded-2xl p-6">
          <div className="overline text-copper text-xs tracking-widest mb-4">What they will not do</div>
          <ul className="space-y-3">
            {persona.will_not.map((item, i) => (
              <li key={i} className="flex items-start gap-3 text-sm text-ink/70">
                <XCircle className="w-4 h-4 text-ink/25 flex-shrink-0 mt-0.5" />
                {item}
              </li>
            ))}
          </ul>
        </div>

        {/* Public record */}
        <div className="mt-6 bg-white border border-ink/10 rounded-2xl p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="overline text-copper text-xs tracking-widest">Public record of declines</div>
            {declines.length > 0 && (
              <span className="text-xs text-ink/40">{declines.length} recorded</span>
            )}
          </div>

          {declines.length === 0 ? (
            <p className="text-sm text-ink/40 italic">
              No recorded declines yet. When this persona declines a request, the reason
              and date are logged here permanently.
            </p>
          ) : (
            <div className="space-y-4">
              {declines.map((d, i) => (
                <div key={d.id || i} className="border-l-2 border-ink/10 pl-4 py-1">
                  <p className="text-xs text-ink/35 mb-1">
                    {new Date(d.at).toLocaleDateString("en-US", {
                      year: "numeric", month: "long", day: "numeric",
                    })}
                  </p>
                  <p className="text-sm text-ink/50 italic mb-1">
                    Request: "{d.request_summary}"
                  </p>
                  <p className="text-sm text-ink/80">
                    {d.decline_reason}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="mt-10 pb-12">
          <p className="text-xs text-ink/25 leading-relaxed">
            This profile is public and permanent. The statements above were written as standing
            declarations of this persona's character and limits. The record of declines is an
            uneditable log — added to automatically when a decline occurs in the operational
            system, and visible to anyone who visits this page.
          </p>
        </div>
      </div>
    </div>
  );
}
