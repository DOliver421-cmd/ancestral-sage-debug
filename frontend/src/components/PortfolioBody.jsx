import { BadgeCheck, Clock, Award, FlaskConical, Target, BookOpen } from "lucide-react";

export default function PortfolioBody({ data, publicView = false }) {
  const s = data.stats;

  return (
    <div className="space-y-10">
      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-6 gap-4" data-testid="portfolio-stats">
        <StatBox icon={Clock} label="Hours" value={s.hours} />
        <StatBox icon={Target} label="Skill Points" value={s.skill_points} />
        <StatBox icon={BookOpen} label="Modules" value={s.modules_completed} />
        <StatBox icon={FlaskConical} label="Labs" value={s.labs_passed} />
        <StatBox icon={BadgeCheck} label="Credentials" value={s.credentials_earned} />
        <StatBox icon={Award} label="Badges" value={s.badges_earned} highlight />
      </div>

      {/* Credentials */}
      <Section title="Credentials & Badges" count={data.credentials.length} testid="sec-credentials">
        {data.credentials.length === 0 ? <Empty msg="No credentials earned yet." /> : (
          <div className="grid md:grid-cols-2 gap-4">
            {data.credentials.map((c) => (
              <div key={c.id || c.key} className="p-4 border border-ink/10 bg-white" data-testid={`pf-cred-${c.key}`}>
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="overline text-copper">{c.category.toUpperCase()}</div>
                    <div className="font-heading font-bold text-lg mt-1">{c.name}</div>
                  </div>
                  <BadgeCheck className="w-6 h-6 text-copper shrink-0" />
                </div>
                <div className="mt-2 text-xs font-mono text-ink/60">
                  Earned {new Date(c.earned_at).toLocaleDateString()}
                  {c.expires_at && ` · Expires ${new Date(c.expires_at).toLocaleDateString()}`}
                </div>
              </div>
            ))}
          </div>
        )}
      </Section>

      {/* Competency Matrix */}
      <Section title="Competency Matrix" count={data.competencies.length} testid="sec-competencies">
        <div className="space-y-3">
          {data.competencies.map((c) => (
            <div key={c.key} className="p-4 border border-ink/10 bg-white" data-testid={`pf-comp-${c.key}`}>
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-heading font-bold">{c.name} {c.badge_earned && <span className="badge-signal ml-2">Badge</span>}</div>
                  <div className="text-sm text-ink/60">{c.description}</div>
                </div>
                <div className="font-mono font-black text-copper text-xl">{c.points}</div>
              </div>
              <div className="mt-2 w-full h-2 bg-ink/10">
                <div className="h-full bg-copper" style={{ width: `${Math.min(100, c.points)}%` }} />
              </div>
            </div>
          ))}
        </div>
      </Section>

      {/* Modules */}
      <Section title="Modules Completed" count={data.modules.length} testid="sec-modules">
        {data.modules.length === 0 ? <Empty msg="No modules completed yet." /> : (
          <div className="grid md:grid-cols-2 gap-3">
            {data.modules.map((m) => (
              <div key={m.slug} className="p-4 border border-ink/10 bg-white flex justify-between items-center" data-testid={`pf-mod-${m.slug}`}>
                <div>
                  <div className="font-heading font-bold">{m.title}</div>
                  <div className="text-xs text-ink/60 mt-1">{m.hours}h · {m.score ? `${Math.round(m.score)}%` : ""}</div>
                </div>
                <Award className="w-5 h-5 text-copper" />
              </div>
            ))}
          </div>
        )}
      </Section>

      {/* Labs */}
      <Section title="Labs Passed" count={data.labs.length} testid="sec-labs">
        {data.labs.length === 0 ? <Empty msg="No labs passed yet." /> : (
          <div className="grid md:grid-cols-2 gap-3">
            {data.labs.map((l) => (
              <div key={l.slug} className="p-4 border border-ink/10 bg-white" data-testid={`pf-lab-${l.slug}`}>
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="overline text-copper">{l.track.toUpperCase()} · {l.skill_points}pts</div>
                    <div className="font-heading font-bold mt-1">{l.title}</div>
                  </div>
                </div>
                {!publicView && l.photo_url && (
                  <a href={l.photo_url} target="_blank" rel="noreferrer" className="text-copper font-mono text-xs underline mt-2 block break-all">{l.photo_url}</a>
                )}
                {l.feedback && (
                  <div className="mt-2 p-2 bg-bone text-xs italic border-l-2 border-copper">
                    Instructor: "{l.feedback}"
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </Section>
    </div>
  );
}

function StatBox({ icon: Icon, label, value, highlight }) {
  return (
    <div className={`p-4 border ${highlight ? "bg-signal border-ink" : "bg-white border-ink/10"}`}>
      <Icon className={`w-4 h-4 ${highlight ? "text-ink" : "text-copper"}`} />
      <div className="font-heading text-2xl font-black mt-2">{value}</div>
      <div className="overline text-ink/60 text-[10px] mt-0.5">{label}</div>
    </div>
  );
}

function Section({ title, count, testid, children }) {
  return (
    <div data-testid={testid}>
      <div className="flex items-center justify-between mb-4">
        <h2 className="font-heading text-2xl font-bold">{title}</h2>
        <span className="overline text-ink/60">{count} total</span>
      </div>
      {children}
    </div>
  );
}

function Empty({ msg }) {
  return <div className="p-6 border border-dashed border-ink/20 text-center text-ink/50 text-sm">{msg}</div>;
}
