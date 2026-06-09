import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import AppShell from "../components/AppShell";
import { LoadingState } from "../components/LoadingState";
import { api, BACKEND_URL } from "../lib/api";
import { useAuth } from "../lib/auth";
import { toast } from "sonner";
import { BookOpen, ShieldAlert, Wrench, CheckSquare, FileImage, Sparkles, ArrowLeft, ArrowRight, Award, LayoutList } from "lucide-react";

export default function ModuleView() {
  const { slug } = useParams();
  const [mod, setMod] = useState(null);
  const [allModules, setAllModules] = useState([]);
  const [progress, setProgress] = useState(null);
  const [answers, setAnswers] = useState({});
  const [result, setResult] = useState(null);
  const [loadFailed, setLoadFailed] = useState(false);
  const { user } = useAuth();

  useEffect(() => {
    fetch(`${BACKEND_URL}/api/modules/${slug}`)
      .then((r) => r.ok ? r.json() : null)
      .then((data) => { if (data) setMod(data); else setLoadFailed(true); })
      .catch(() => setLoadFailed(true));
    fetch(`${BACKEND_URL}/api/modules`)
      .then((r) => r.ok ? r.json() : [])
      .then((data) => setAllModules(Array.isArray(data) ? data : []))
      .catch(() => {});
    if (user) {
      api.post("/progress/start", { module_slug: slug }).then((r) => setProgress(r.data)).catch(() => {});
    }
  }, [slug, user]);

  // Next module in sequence (by order, skipping current)
  const nextModule = allModules
    .filter((m) => m.slug !== slug)
    .sort((a, b) => a.order - b.order)
    .find((m) => (mod?.order ?? 0) < m.order) || null;

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

  if (loadFailed) return (
    <AppShell>
      <div className="px-10 py-20 text-center max-w-lg mx-auto">
        <BookOpen className="w-10 h-10 text-ink/20 mx-auto mb-4" />
        <h2 className="font-heading text-2xl font-bold mb-2">Module not found</h2>
        <p className="text-ink/60 mb-6">This module couldn't be loaded. It may have moved or there's a connection issue.</p>
        <Link to="/modules" className="btn-copper inline-flex items-center gap-2">
          <LayoutList className="w-4 h-4" /> Back to Curriculum
        </Link>
      </div>
    </AppShell>
  );
  if (!mod) return <LoadingState label="Module" />;

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

        {/* Video and diagram — render only when backend provides URLs */}
        {(mod.video_url || mod.diagram_url) && (
          <div className="grid md:grid-cols-2 gap-4 mt-8">
            {mod.video_url ? (
              <div className="card-flat aspect-video overflow-hidden" data-testid="video-player">
                <iframe
                  src={mod.video_url}
                  title={`${mod.title} — lesson video`}
                  className="w-full h-full"
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                  allowFullScreen
                />
              </div>
            ) : null}
            {mod.diagram_url ? (
              <div className="card-flat aspect-video overflow-hidden flex items-center justify-center bg-ink/5" data-testid="diagram-viewer">
                <img
                  src={mod.diagram_url}
                  alt={`${mod.title} — wiring diagram`}
                  className="max-w-full max-h-full object-contain"
                />
              </div>
            ) : null}
          </div>
        )}

        {/* Content sections */}
        <Section icon={BookOpen} title="Learning Objectives" testid="section-objectives">
          <ul className="space-y-2">{mod.objectives.map((o, i) => <li key={o} className="flex gap-3"><span className="text-copper font-bold font-mono">{(i + 1).toString().padStart(2, "0")}</span><span>{o}</span></li>)}</ul>
        </Section>

        <Section icon={ShieldAlert} title="Safety Requirements" testid="section-safety" warning>
          <ul className="space-y-2">{mod.safety.map((s) => <li key={s} className="flex gap-3"><span className="text-destructive font-bold">!</span><span>{s}</span></li>)}</ul>
        </Section>

        <Section icon={Wrench} title="Tools & Materials" testid="section-tools">
          <ul className="grid sm:grid-cols-2 gap-2">{mod.tools.map((t) => <li key={t} className="font-mono text-sm">— {t}</li>)}</ul>
        </Section>

        <Section icon={CheckSquare} title="Skill Demonstration Tasks" testid="section-tasks">
          <ol className="space-y-3">{mod.tasks.map((t, i) => (
            <li key={t} className="flex gap-4 p-3 border border-ink/10">
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
              <div key={q.q} className="card-flat p-5">
                <div className="font-heading font-semibold mb-3"><span className="text-copper mr-2">Q{i + 1}.</span>{q.q}</div>
                <div className="space-y-2">
                  {q.options.map((opt, j) => {
                    const isCorrect = result && j === q.answer;
                    const isSelected = answers[i] === j;
                    const isWrong = result && isSelected && j !== q.answer;
                    return (
                      <label key={`${q.q}-${opt}`} className={`flex items-center gap-3 p-3 border cursor-pointer transition-colors ${isCorrect ? "border-signal bg-signal/20" : isWrong ? "border-destructive bg-destructive/5" : isSelected ? "border-ink bg-ink/5" : "border-ink/10 hover:border-ink/40"}`} data-testid={`q-${i}-opt-${j}`}>
                        <input type="radio" name={`q-${i}`} checked={isSelected || false} onChange={() => setAnswers({ ...answers, [i]: j })} className="accent-copper" />
                        <span className="text-sm">{opt}</span>
                      </label>
                    );
                  })}
                </div>
              </div>
            ))}
            {user
              ? <button onClick={submitQuiz} className="btn-primary" data-testid="btn-submit-quiz">Submit Quiz</button>
              : <Link to="/register" className="btn-primary" data-testid="btn-submit-quiz">Sign up to take quiz</Link>}
            {result?.status === "completed" && (
              <div className="mt-6 p-5 rounded-xl border border-signal/30 bg-signal/5 space-y-3" data-testid="completion-panel">
                <div className="flex items-center gap-2 font-heading font-bold text-signal">
                  <Award className="w-5 h-5" /> Module Complete — {result.score?.toFixed(0)}%
                </div>
                <div className="flex flex-wrap gap-3">
                  <Link to="/certificates" className="btn-copper inline-flex items-center gap-2" data-testid="btn-view-cert">
                    <Award className="w-4 h-4" /> View Certificate
                  </Link>
                  {nextModule ? (
                    <Link to={`/modules/${nextModule.slug}`} className="btn-primary inline-flex items-center gap-2" data-testid="btn-next-module">
                      Next: {nextModule.title} <ArrowRight className="w-4 h-4" />
                    </Link>
                  ) : (
                    <Link to="/dashboard" className="btn-primary inline-flex items-center gap-2">
                      Back to Dashboard <ArrowRight className="w-4 h-4" />
                    </Link>
                  )}
                  <Link to="/modules" className="inline-flex items-center gap-2 text-sm font-bold text-ink/60 hover:text-copper px-3 py-2">
                    <LayoutList className="w-4 h-4" /> All Modules
                  </Link>
                </div>
              </div>
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
