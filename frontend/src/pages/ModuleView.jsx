import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import AppShell from "../components/AppShell";
import { api } from "../lib/api";
import { toast } from "sonner";
import { BookOpen, ShieldAlert, Wrench, CheckSquare, FileImage, Sparkles, ArrowLeft } from "lucide-react";

export default function ModuleView() {
  const { slug } = useParams();
  const [mod, setMod] = useState(null);
  const [progress, setProgress] = useState(null);
  const [answers, setAnswers] = useState({});
  const [result, setResult] = useState(null);

  useEffect(() => {
    api.get(`/modules/${slug}`).then((r) => setMod(r.data));
    api.post("/progress/start", { module_slug: slug }).then((r) => setProgress(r.data)).catch(() => {});
  }, [slug]);

  const submitQuiz = async () => {
    if (!mod) return;
    const ordered = mod.quiz.map((_, i) => answers[i] ?? -1);
    if (ordered.includes(-1)) { toast.error("Answer every question"); return; }
    try {
      const r = await api.post("/progress/quiz", { module_slug: slug, answers: ordered });
      setResult(r.data);
      if (r.data.status === "completed") {
        toast.success(`Passed with ${r.data.score.toFixed(0)}%! Certificate unlocked.`);
      } else {
        toast.warning(`${r.data.score.toFixed(0)}% — 70% required to pass. Review and try again.`);
      }
    } catch (e) {
      toast.error("Quiz submission failed");
    }
  };

  if (!mod) return <AppShell><div className="p-10">Loading…</div></AppShell>;

  return (
    <AppShell>
      <div className="px-10 py-10 max-w-5xl">
        <Link to="/modules" className="inline-flex items-center gap-2 text-sm font-bold uppercase tracking-widest text-ink/60 hover:text-copper" data-testid="back-modules">
          <ArrowLeft className="w-4 h-4" /> All Modules
        </Link>

        <div className="mt-6 flex items-start justify-between gap-8">
          <div>
            <div className="overline text-copper">Module {mod.order.toString().padStart(2, "0")} · {mod.hours} hours</div>
            <h1 className="font-heading text-4xl lg:text-5xl font-bold mt-3 leading-tight">{mod.title}</h1>
            <p className="text-ink/70 mt-4 max-w-3xl leading-relaxed">{mod.summary}</p>
          </div>
          <span className={progress?.status === "completed" ? "badge-signal" : "badge-copper"}>
            {progress?.status === "completed" ? "Completed" : "In Progress"}
          </span>
        </div>

        {/* Scripture tie-in */}
        <div className="bg-ink text-white p-6 mt-8" data-testid="scripture-card">
          <div className="overline text-signal">Scripture Tie-In</div>
          <div className="font-heading text-xl mt-3 leading-snug">"{mod.scripture.text}"</div>
          <div className="overline text-signal/80 mt-3">{mod.scripture.ref}</div>
        </div>

        {/* Video/image placeholders */}
        <div className="grid md:grid-cols-2 gap-4 mt-8">
          <div className="card-flat aspect-video flex flex-col items-center justify-center bg-ink/5" data-testid="video-placeholder">
            <FileImage className="w-10 h-10 text-ink/30" />
            <div className="overline text-ink/50 mt-3">Lesson Video</div>
            <div className="text-xs text-ink/40 mt-1">Instructor upload pending</div>
          </div>
          <div className="card-flat aspect-video flex flex-col items-center justify-center bg-ink/5" data-testid="diagram-placeholder">
            <FileImage className="w-10 h-10 text-ink/30" />
            <div className="overline text-ink/50 mt-3">Wiring Diagram</div>
            <div className="text-xs text-ink/40 mt-1">Reference drawing</div>
          </div>
        </div>

        {/* Content sections */}
        <Section icon={BookOpen} title="Learning Objectives" testid="section-objectives">
          <ul className="space-y-2">{mod.objectives.map((o, i) => <li key={i} className="flex gap-3"><span className="text-copper font-bold font-mono">{(i + 1).toString().padStart(2, "0")}</span><span>{o}</span></li>)}</ul>
        </Section>

        <Section icon={ShieldAlert} title="Safety Requirements" testid="section-safety" warning>
          <ul className="space-y-2">{mod.safety.map((s, i) => <li key={i} className="flex gap-3"><span className="text-destructive font-bold">!</span><span>{s}</span></li>)}</ul>
        </Section>

        <Section icon={Wrench} title="Tools & Materials" testid="section-tools">
          <ul className="grid sm:grid-cols-2 gap-2">{mod.tools.map((t, i) => <li key={i} className="font-mono text-sm">— {t}</li>)}</ul>
        </Section>

        <Section icon={CheckSquare} title="Skill Demonstration Tasks" testid="section-tasks">
          <ol className="space-y-3">{mod.tasks.map((t, i) => (
            <li key={i} className="flex gap-4 p-3 border border-ink/10">
              <span className="font-heading font-black text-copper">T{i + 1}</span>
              <span>{t}</span>
            </li>
          ))}</ol>
          <div className="mt-4 text-xs text-ink/60">Upload photo evidence to your instructor for sign-off.</div>
        </Section>

        {/* Quiz */}
        <div className="mt-10">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-heading text-2xl font-bold flex items-center gap-3"><Sparkles className="w-5 h-5 text-copper" /> Mastery Quiz</h2>
            {result && <span className={result.status === "completed" ? "badge-signal" : "badge-copper"}>{result.score.toFixed(0)}% · {result.correct}/{result.total}</span>}
          </div>
          <div className="space-y-5" data-testid="quiz-section">
            {mod.quiz.map((q, i) => (
              <div key={i} className="card-flat p-5">
                <div className="font-heading font-semibold mb-3"><span className="text-copper mr-2">Q{i + 1}.</span>{q.q}</div>
                <div className="space-y-2">
                  {q.options.map((opt, j) => {
                    const isCorrect = result && j === q.answer;
                    const isSelected = answers[i] === j;
                    const isWrong = result && isSelected && j !== q.answer;
                    return (
                      <label key={j} className={`flex items-center gap-3 p-3 border cursor-pointer transition-colors ${isCorrect ? "border-signal bg-signal/20" : isWrong ? "border-destructive bg-destructive/5" : isSelected ? "border-ink bg-ink/5" : "border-ink/10 hover:border-ink/40"}`} data-testid={`q-${i}-opt-${j}`}>
                        <input type="radio" name={`q-${i}`} checked={isSelected || false} onChange={() => setAnswers({ ...answers, [i]: j })} className="accent-copper" />
                        <span className="text-sm">{opt}</span>
                      </label>
                    );
                  })}
                </div>
              </div>
            ))}
            <button onClick={submitQuiz} className="btn-primary" data-testid="btn-submit-quiz">Submit Quiz</button>
            {result?.status === "completed" && (
              <Link to="/certificates" className="btn-copper ml-3 inline-block" data-testid="btn-view-cert">View Certificate</Link>
            )}
          </div>
        </div>
      </div>
    </AppShell>
  );
}

function Section({ icon: Icon, title, testid, children, warning }) {
  return (
    <div className="mt-8 card-flat p-6" data-testid={testid}>
      <div className="flex items-center gap-3 mb-4">
        <Icon className={`w-5 h-5 ${warning ? "text-destructive" : "text-copper"}`} />
        <h3 className="font-heading text-xl font-bold">{title}</h3>
      </div>
      <div className="text-ink/80">{children}</div>
    </div>
  );
}
