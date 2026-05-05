import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import AppShell from "../components/AppShell";
import { LoadingState } from "../components/LoadingState";
import { api } from "../lib/api";
import { toast } from "sonner";
import { ArrowLeft, ShieldAlert, BookOpen, CheckSquare } from "lucide-react";

export default function ComplianceDetail() {
  const { slug } = useParams();
  const [mod, setMod] = useState(null);
  const [answers, setAnswers] = useState({});
  const [result, setResult] = useState(null);

  useEffect(() => { api.get(`/compliance/${slug}`).then((r) => setMod(r.data)); }, [slug]);

  const submitQuiz = async () => {
    const ordered = mod.quiz.map((_, i) => answers[i] ?? -1);
    if (ordered.includes(-1)) { toast.error("Answer every question"); return; }
    try {
      const r = await api.post(`/compliance/${slug}/quiz`, { answers: ordered });
      setResult(r.data);
      if (r.data.status === "completed") toast.success(`Passed at ${r.data.score.toFixed(0)}% — credential issued.`);
      else toast.warning(`${r.data.score.toFixed(0)}% — ${r.data.pass_pct}% required.`);
    } catch { toast.error("Submission failed"); }
  };

  if (!mod) return <LoadingState label="Compliance" />;

  return (
    <AppShell>
      <div className="px-10 py-10 max-w-4xl">
        <Link to="/compliance" className="inline-flex items-center gap-2 text-sm font-bold uppercase tracking-widest text-ink/60 hover:text-copper" data-testid="back-compliance">
          <ArrowLeft className="w-4 h-4" /> All Compliance
        </Link>
        <div className="mt-6">
          <div className="overline text-copper">COMPLIANCE · {mod.hours}h{mod.expires_months ? ` · ${mod.expires_months}mo` : ""}</div>
          <h1 className="font-heading text-4xl font-bold mt-2">{mod.title}</h1>
          <p className="text-ink/70 mt-3 max-w-3xl leading-relaxed">{mod.summary}</p>
        </div>

        <div className="bg-ink text-white p-6 mt-6">
          <div className="overline text-signal">Scripture</div>
          <div className="font-heading text-xl mt-3">"{mod.scripture.text}"</div>
          <div className="overline text-signal/80 mt-3">{mod.scripture.ref}</div>
        </div>

        <Section icon={BookOpen} title="Learning Objectives">
          <ul className="space-y-2">{mod.objectives.map((o, i) => <li key={o} className="flex gap-3"><span className="text-copper font-mono font-bold">{(i + 1).toString().padStart(2, "0")}</span><span>{o}</span></li>)}</ul>
        </Section>

        <Section icon={ShieldAlert} title="Safety Reminders" warning>
          <ul className="space-y-1.5 text-sm">{mod.safety.map((s) => <li key={s}>— {s}</li>)}</ul>
        </Section>

        <Section icon={CheckSquare} title="Tasks">
          <ol className="space-y-2">{mod.tasks.map((t, i) => <li key={t} className="flex gap-3"><span className="font-mono font-bold text-copper">{i + 1}.</span><span>{t}</span></li>)}</ol>
        </Section>

        <div className="mt-10 card-flat p-6" data-testid="quiz-section">
          <div className="overline text-copper">Certification Quiz · pass at 70%+ (LOTO 80%+)</div>
          <h2 className="font-heading text-2xl font-bold mt-2 mb-5">Test Your Knowledge</h2>
          <div className="space-y-4">
            {mod.quiz.map((q, i) => (
              <div key={q.q} className="p-4 border border-ink/10">
                <div className="font-heading font-semibold mb-3"><span className="text-copper mr-2">Q{i + 1}.</span>{q.q}</div>
                <div className="space-y-2">
                  {q.options.map((opt, j) => {
                    const isCorrect = result && j === q.answer;
                    const isSel = answers[i] === j;
                    const isWrong = result && isSel && j !== q.answer;
                    return (
                      <label key={`${q.q}-${opt}`} className={`flex items-center gap-3 p-2 border cursor-pointer ${isCorrect ? "border-signal bg-signal/20" : isWrong ? "border-destructive bg-destructive/5" : isSel ? "border-ink bg-ink/5" : "border-ink/10 hover:border-ink/40"}`} data-testid={`cq-${i}-${j}`}>
                        <input type="radio" checked={isSel || false} onChange={() => setAnswers({ ...answers, [i]: j })} className="accent-copper" />
                        <span className="text-sm">{opt}</span>
                      </label>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
          <button onClick={submitQuiz} className="btn-primary mt-5" data-testid="btn-cq-submit">Submit Quiz</button>
        </div>
      </div>
    </AppShell>
  );
}

function Section({ icon: Icon, title, children, warning }) {
  return (
    <div className="mt-6 card-flat p-6">
      <div className="flex items-center gap-3 mb-3">
        <Icon className={`w-5 h-5 ${warning ? "text-destructive" : "text-copper"}`} />
        <h3 className="font-heading text-xl font-bold">{title}</h3>
      </div>
      <div className="text-ink/80">{children}</div>
    </div>
  );
}
