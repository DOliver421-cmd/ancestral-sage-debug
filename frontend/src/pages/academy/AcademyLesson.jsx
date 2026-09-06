import { useEffect, useMemo, useRef, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { api } from "../../lib/api";
import AppShell from "../../components/AppShell";
import { ProgressBar } from "./academyKit";
import {
  ArrowRight, ArrowLeft, BookOpen, CheckCircle2, Lightbulb, Lock, PlayCircle,
  RefreshCw, Sparkles, Target, XCircle, Bot, Send, GraduationCap, AlertCircle,
} from "lucide-react";

const DEFAULT_COACH_HINT = (
  <>
    <strong>Coach unavailable right now.</strong> Live AI tutoring runs through the same gateway as the{" "}
    <Link to="/ai" className="underline">AI Tutor</Link> — it needs an active AI configuration (member tier or BYOK key).
    Your lesson and mastery checks always work without it.
  </>
);

/* /academy/learn/:courseSlug/:lessonSlug — the lesson player.
   Flow: read → show what you know → score → 80%+ unlocks the next lesson;
   below 80% shows explanations and offers a retry. The server enforces the
   sequence; this UI makes it clear and pleasant. */

export default function AcademyLesson() {
  const { courseSlug, lessonSlug } = useParams();
  const [params] = useSearchParams();
  const studentId = params.get("student");

  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  // Lesson state machine: "read" → "armed" (quiz visible) → "done" (result).
  const [phase, setPhase] = useState("read");
  const [answers, setAnswers] = useState([]);
  const [result, setResult] = useState(null);
  const [busy, setBusy] = useState(false);

  // AI coach
  const [coachOpen, setCoachOpen] = useState(false);
  const [coachMsgs, setCoachMsgs] = useState([]);
  const [coachText, setCoachText] = useState("");
  const [coachBusy, setCoachBusy] = useState(false);
  const coachRef = useRef(null);
  const sessionId = useMemo(() => `academy-${studentId || "anon"}-${courseSlug}-${lessonSlug}-${Math.random().toString(36).slice(2, 10)}`, [studentId, courseSlug, lessonSlug]);

  const load = () => {
    setLoading(true); setError("");
    api.get(`/academy/courses/${courseSlug}/learn${studentId ? `?student=${studentId}` : ""}`)
      .then((r) => {
        setData(r.data);
        setLoading(false);
      })
      .catch((e) => { setError(e?.response?.data?.detail || "Could not open this lesson."); setLoading(false); });
  };

  useEffect(() => { load(); /* eslint-disable-next-line react-hooks/exhaustive-deps */ }, [courseSlug, lessonSlug, studentId]);

  useEffect(() => {
    if (coachRef.current) coachRef.current.scrollTop = coachRef.current.scrollHeight;
  }, [coachMsgs]);

  const lesson = useMemo(() => {
    if (!data) return null;
    for (const u of data.units || []) {
      const found = (u.lessons || []).find((l) => l.slug === lessonSlug);
      if (found) return { ...found, unitTitle: u.title, unitSlug: u.slug };
    }
    return null;
  }, [data, lessonSlug]);

  // A deep link may arrive without ?student= (e.g. CourseDetail's "Open
  // course"). The learn payload resolves the owner's enrolled student on the
  // server and returns student_id — use it for submissions and navigation so
  // attempts are never sent with a null student.
  const activeStudent = studentId || data?.student_id || null;

  const questions = lesson?.check?.questions || [];
  const unitLessons = useMemo(() => {
    if (!data || !lesson) return [];
    const unit = (data.units || []).find((u) => u.slug === lesson.unitSlug);
    return unit ? unit.lessons : [];
  }, [data, lesson]);

  const submit = async () => {
    const picked = questions.map((_, i) => (Number.isInteger(answers[i]) ? answers[i] : -1));
    if (picked.some((a) => a < 0)) {
      setResult({ error: "Please answer every question before submitting." });
      return;
    }
    setBusy(true); setResult(null);
    try {
      const r = await api.post(`/academy/courses/${courseSlug}/lessons/${lessonSlug}/attempt`, {
        student_id: activeStudent, answers: picked,
      });
      setResult({ ok: true, data: r.data });
      setPhase("done");
    } catch (e) {
      const detail = e?.response?.data?.detail || "Could not submit. Try again.";
      setResult({ error: detail });
      if (e?.response?.status === 409 || e?.response?.status === 403) load();
    } finally { setBusy(false); }
  };

  const retry = () => { setAnswers([]); setResult(null); setPhase("armed"); };

  const sendCoach = async () => {
    const text = coachText.trim();
    if (!text || coachBusy) return;
    const context = [
      `You are the WAI Homeschool Academy Coach inside MoreHelp Center.`,
      `Student is working on: ${data?.course?.title} — lesson "${lesson?.title}".`,
      `Context from the lesson:\n${(lesson?.learn || []).map((b) => b.text || (b.items || []).join("; ")).join("\n")}`,
      `Knowledge check prompt (for awareness only — never answer it directly): ${lesson?.check?.prompt || ""}`,
      `Rules: help the student learn — explain concepts, give different examples, walk through guided practice, ask guiding questions. Never provide the exact answer to any knowledge-check question, and never write out a complete response the student could paste in. Encourage genuine understanding so mastery is earned.`,
    ].join("\n\n");
    setCoachMsgs((m) => [...m, { role: "user", text }]);
    setCoachText("");
    setCoachBusy(true);
    try {
      const r = await api.post("/ai/chat", { session_id: sessionId, message: `${context}\n\nStudent asks: ${text}`, mode: "tutor" });
      setCoachMsgs((m) => [...m, { role: "coach", text: r.data.reply || "…" }]);
    } catch {
      setCoachMsgs((m) => [...m, { role: "coach", text: "", unavailable: true }]);
    } finally { setCoachBusy(false); }
  };

  if (loading) {
    return (
      <AppShell>
        <p className="px-10 py-16 flex items-center gap-2 text-ink/45"><RefreshCw className="w-4 h-4 animate-spin" /> Opening lesson…</p>
      </AppShell>
    );
  }
  if (error || !data || !lesson) {
    return (
      <AppShell>
        <div className="px-10 py-16 max-w-2xl">
          <AlertCircle className="w-10 h-10 text-destructive" />
          <h1 className="font-heading text-2xl font-bold text-ink mt-3">{error || "Lesson not found"}</h1>
          <p className="text-ink/60 mt-2">If the lesson is locked, complete the previous lesson first — that's how mastery works.</p>
          <Link to={activeStudent ? `/academy/student/${activeStudent}` : "/academy/parent"} className="btn-copper inline-flex items-center gap-2 mt-6">
            <ArrowLeft className="w-4 h-4" /> Back to the classroom
          </Link>
        </div>
      </AppShell>
    );
  }

  const passedBefore = lesson.passed;
  const showQuiz = phase !== "read";
  const passedNow = result?.ok && result.data.passed;
  const failedNow = result?.ok && !result.data.passed;
  const courseComplete = result?.ok && result.data.course_completed;

  return (
    <AppShell>
      <div className="px-10 py-10" data-testid="lesson-player">
        {/* Top bar */}
        <div className="flex flex-wrap items-center justify-between gap-3 max-w-5xl">
          <div className="flex items-center gap-2 text-sm">
            <Link to={activeStudent ? `/academy/student/${activeStudent}` : "/academy/parent"} className="inline-flex items-center gap-1.5 font-bold text-copper hover:text-ink transition-colors">
              <ArrowLeft className="w-4 h-4" /> Classroom
            </Link>
            <span className="text-ink/30">/</span>
            <span className="font-bold text-ink">{data.course.title}</span>
            <span className="text-ink/30">/</span>
            <span className="text-ink/60">{lesson.unitTitle}</span>
          </div>
          {data.course.passing_score && (
            <span className="inline-flex items-center gap-1.5 text-xs font-black uppercase tracking-widest text-copper bg-copper/10 border border-copper/25 rounded-full px-3 py-1">
              <Target className="w-3.5 h-3.5" /> Mastery: {data.course.passing_score}% to pass
            </span>
          )}
        </div>

        <div className="max-w-5xl grid lg:grid-cols-3 gap-8 mt-6">
          {/* Lesson body */}
          <div className="lg:col-span-2 space-y-6">
            {!lesson.unlocked && !passedBefore ? (
              <div className="card-flat bg-white p-10 text-center border-t-4 border-ink/20">
                <Lock className="w-10 h-10 text-ink/30 mx-auto mb-4" />
                <h1 className="font-heading text-2xl font-bold text-ink">This lesson is locked</h1>
                <p className="text-ink/60 mt-2 max-w-md mx-auto">Lessons unlock in order. Complete the previous lesson at {data.course.passing_score}%+ to open this one.</p>
                <Link to={activeStudent ? `/academy/student/${activeStudent}` : "/academy/parent"} className="btn-copper inline-flex items-center gap-2 mt-6">Back to the classroom</Link>
              </div>
            ) : (
              <>
                {/* Header */}
                <div className="card-flat bg-white border border-ink/10 p-7">
                  <div className="flex flex-wrap items-center gap-2 text-xs font-black uppercase tracking-widest">
                    <span className="text-copper">Lesson {lesson.order}</span>
                    <span className="text-ink/30">·</span>
                    <span className="text-ink/45">{lesson.minutes} min</span>
                    {passedBefore && (
                      <span className="ml-auto inline-flex items-center gap-1 text-emerald-700 bg-emerald-600/10 border border-emerald-600/30 rounded-full px-2.5 py-1"><CheckCircle2 className="w-3.5 h-3.5" /> Mastered at {lesson.best_score}%</span>
                    )}
                  </div>
                  <h1 className="font-heading text-3xl font-bold text-ink mt-2">{lesson.title}</h1>
                  <p className="text-ink/60 mt-2 leading-relaxed">{lesson.summary}</p>
                </div>

                {/* Content */}
                <div className="space-y-5">
                  {(lesson.learn || []).map((b, i) => <ContentBlock key={i} block={b} />)}
                </div>

                {passedBefore && !courseComplete && (
                  <div className="card-flat bg-white border-l-4 border-emerald-500 p-6 flex flex-wrap items-center justify-between gap-3">
                    <div className="flex items-center gap-3">
                      <CheckCircle2 className="w-6 h-6 text-emerald-600" />
                      <div>
                        <div className="font-bold text-ink">Lesson already mastered</div>
                        <p className="text-sm text-ink/55">Great work — no need to take it again.</p>
                      </div>
                    </div>
                    <NextAction courseSlug={courseSlug} studentId={activeStudent} units={data.units} lessonSlug={lessonSlug} passed />
                  </div>
                )}

                {!passedBefore && (
                  <div className="card-flat bg-white border border-ink/10 overflow-hidden">
                    <div className="px-7 py-5 border-b border-ink/10 bg-ink text-white">
                      <div className="flex items-center gap-2 font-heading font-bold text-lg"><Target className="w-5 h-5 text-signal" /> Knowledge check</div>
                      <p className="text-white/55 text-sm mt-0.5">{lesson.check?.prompt || "Show what you know."} Score {data.course.passing_score}%+ to complete the lesson.</p>
                    </div>

                    {!showQuiz && !passedNow && !failedNow && (
                      <div className="p-7 text-center">
                        <p className="text-ink/60 mb-5">Read through the lesson above first. When you're ready, the check is a few quick questions — no surprises.</p>
                        <button onClick={() => setPhase("armed")} className="inline-flex items-center gap-2 px-7 py-3 bg-signal text-ink font-black rounded-xl hover:bg-signal/85 transition-colors" data-testid="start-check">
                          <PlayCircle className="w-5 h-5" /> I've read it — show the check
                        </button>
                      </div>
                    )}

                    {showQuiz && !passedNow && !failedNow && (
                      <div className="p-7 space-y-6">
                        {questions.map((q, qi) => {
                          const chosen = answers[qi];
                          return (
                            <div key={qi} className="space-y-2.5">
                              <p className="font-bold text-ink">{qi + 1}. {q.q}</p>
                              <div className="grid gap-2">
                                {q.options.map((opt, oi) => {
                                  const selected = chosen === oi;
                                  return (
                                    <button key={oi} type="button" onClick={() => setAnswers((a) => { const next = [...a]; next[qi] = oi; return next; })}
                                      className={`text-left px-4 py-2.5 rounded-lg border text-sm font-semibold transition-all ${selected ? "border-copper bg-copper/10 text-ink ring-1 ring-copper" : "border-ink/15 bg-white hover:border-copper/50"}`}
                                      data-testid={`answer-${qi}-${oi}`}>
                                      <span className="inline-flex items-center justify-center w-6 h-6 rounded-full border border-ink/20 text-xs font-black mr-2">{String.fromCharCode(65 + oi)}</span>
                                      {opt}
                                    </button>
                                  );
                                })}
                              </div>
                            </div>
                          );
                        })}
                        {result?.error && <p className="text-sm font-bold text-destructive">{result.error}</p>}
                        <div className="flex flex-wrap items-center gap-3 pt-2">
                          <button onClick={submit} disabled={busy} className="inline-flex items-center gap-2 px-7 py-3 bg-ink text-signal font-black rounded-xl hover:bg-ink/85 transition-colors disabled:opacity-50" data-testid="submit-check">
                            {busy ? "Scoring…" : "Submit my answers"} <ArrowRight className="w-4 h-4" />
                          </button>
                          <button onClick={() => { setAnswers([]); setResult(null); setPhase("read"); }} className="text-sm font-bold text-ink/45 hover:text-ink underline underline-offset-2">Back to the lesson</button>
                        </div>
                      </div>
                    )}

                    {passedNow && (
                      <div className="p-8">
                        <div className="rounded-2xl border-2 border-emerald-600/40 bg-emerald-600/5 p-6 text-center">
                          <CheckCircle2 className="w-12 h-12 text-emerald-600 mx-auto mb-3" />
                          <div className="font-heading text-2xl font-bold text-emerald-900">Mastered! {result.data.score}%</div>
                          <p className="text-emerald-800/70 mt-1">You beat the {result.data.required}% mastery line{result.data.attempt_number > 1 ? ` on attempt ${result.data.attempt_number}` : ""}. Progress saved.</p>
                          {courseComplete ? (
                            <div className="mt-5">
                              <div className="inline-flex items-center gap-2 px-5 py-2 rounded-full bg-emerald-600 text-white font-black uppercase tracking-widest text-xs"><Sparkles className="w-4 h-4" /> Course complete</div>
                            </div>
                          ) : null}
                          <div className="mt-6">
                            {courseComplete ? (
                              <Link to={activeStudent ? `/academy/student/${activeStudent}` : "/academy/parent"} className="btn-copper inline-flex items-center gap-2">
                                <GraduationCap className="w-4 h-4" /> Back to the classroom
                              </Link>
                            ) : result.data.next_lesson ? (
                              <Link to={`/academy/learn/${courseSlug}/${result.data.next_lesson.slug}?student=${activeStudent}`} className="inline-flex items-center gap-2 px-7 py-3 bg-ink text-signal font-black rounded-xl hover:bg-ink/85 transition-colors" data-testid="next-lesson-cta">
                                Next lesson: {result.data.next_lesson.title} <ArrowRight className="w-4 h-4" />
                              </Link>
                            ) : null}
                          </div>
                        </div>
                      </div>
                    )}

                    {failedNow && (
                      <div className="p-7">
                        <div className="rounded-2xl border-2 border-amber-500/50 bg-amber-500/5 p-6">
                          <div className="flex items-center gap-3">
                            <XCircle className="w-8 h-8 text-amber-600 shrink-0" />
                            <div>
                              <div className="font-heading text-xl font-bold text-amber-900">{result.data.score}% — not yet</div>
                              <p className="text-amber-800/70 text-sm">You need {result.data.required}% to pass. Review the explanations, then try again — mastery is about understanding, not luck.</p>
                            </div>
                          </div>
                        </div>
                        <div className="mt-5 space-y-4">
                          {questions.map((q, qi) => {
                            const chosen = answers[qi];
                            const correct = q.options.findIndex((o) => o === q.answer);
                            const wasRight = chosen === correct;
                            return (
                              <div key={qi} className={`rounded-xl border p-4 ${wasRight ? "border-emerald-600/25 bg-emerald-600/[0.03]" : "border-destructive/25 bg-destructive/[0.03]"}`}>
                                <div className="font-bold text-ink text-sm">{qi + 1}. {q.q}</div>
                                <div className="text-sm mt-1.5 space-y-1">
                                  {!wasRight && <p className="text-destructive font-semibold">Your answer: {q.options[chosen]}</p>}
                                  <p className="text-emerald-700 font-semibold flex items-start gap-1.5"><CheckCircle2 className="w-4 h-4 mt-0.5 shrink-0" /> Correct: {q.answer}</p>
                                  <p className="text-ink/60 leading-relaxed">{q.explain}</p>
                                </div>
                              </div>
                            );
                          })}
                        </div>
                        <div className="mt-6">
                          <button onClick={retry} className="inline-flex items-center gap-2 px-7 py-3 bg-signal text-ink font-black rounded-xl hover:bg-signal/85 transition-colors" data-testid="retry-check">
                            <RefreshCw className="w-4 h-4" /> Try again
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* Unit lesson trail */}
                <div className="card-flat bg-white border border-ink/10 p-5">
                  <div className="overline text-copper mb-3">{lesson.unitTitle} — unit trail</div>
                  <div className="flex flex-wrap gap-2">
                    {unitLessons.map((l) => {
                      const current = l.slug === lessonSlug;
                      return current ? (
                        <span key={l.slug} className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-ink text-signal text-xs font-black" data-testid="trail-current">
                          <BookOpen className="w-3 h-3" /> {l.title}
                        </span>
                      ) : (
                        <span key={l.slug} className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-bold ${l.passed ? "bg-emerald-600/10 text-emerald-700" : l.unlocked ? "bg-ink/5 text-ink/70" : "text-ink/30 bg-ink/5"}`}>
                          {l.passed ? <CheckCircle2 className="w-3 h-3" /> : !l.unlocked ? <Lock className="w-3 h-3" /> : null}
                          {l.title}
                        </span>
                      );
                    })}
                  </div>
                </div>
              </>
            )}
          </div>

          {/* Sidebar: AI coach + course progress */}
          <aside className="space-y-5">
            <div className="card-flat bg-white border border-ink/10 p-5">
              <div className="flex items-center justify-between">
                <div className="font-heading font-bold text-ink">Course progress</div>
                <Link to={activeStudent ? `/academy/student/${activeStudent}` : "/academy/parent"} className="text-xs font-black uppercase tracking-widest text-copper hover:text-ink">Open</Link>
              </div>
              <div className="text-xs text-ink/55 mt-2 mb-2">{data.course.title}</div>
              <ProgressBar pct={(data.units.flatMap((u) => u.lessons).filter((l) => l.passed).length / Math.max(1, data.units.flatMap((u) => u.lessons).length)) * 100} />
              <p className="text-xs text-ink/45 mt-2">
                {data.units.flatMap((u) => u.lessons).filter((l) => l.passed).length} of {data.units.flatMap((u) => u.lessons).length} lessons mastered
              </p>
            </div>

            {/* AI Coach */}
            <div className="card-flat bg-white border border-ink/10 overflow-hidden">
              <button onClick={() => setCoachOpen((o) => !o)} className="w-full flex items-center gap-3 p-5 text-left hover:bg-ink/[0.02] transition-colors" data-testid="coach-toggle">
                <div className="w-10 h-10 rounded-full bg-copper/15 flex items-center justify-center text-copper"><Bot className="w-5 h-5" /></div>
                <div className="flex-1">
                  <div className="font-heading font-bold text-ink">Coach</div>
                  <p className="text-xs text-ink/50">AI learning help — explains, never gives away the answer.</p>
                </div>
                <Lightbulb className={`w-5 h-5 text-copper transition-transform ${coachOpen ? "rotate-180" : ""}`} />
              </button>
              {coachOpen && (
                <div className="border-t border-ink/10">
                  <div ref={coachRef} className="h-64 overflow-y-auto px-4 py-3 space-y-3 bg-bone/60">
                    {coachMsgs.length === 0 && (
                      <p className="text-xs text-ink/45 leading-relaxed">
                        Stuck on the idea but don't want the answer? Ask the Coach for an explanation,
                        a different example, or a practice question. It knows which lesson you're on.
                      </p>
                    )}
                    {coachMsgs.map((m, i) => m.role === "user" ? (
                      <div key={i} className="flex justify-end">
                        <div className="max-w-[85%] bg-ink text-white text-sm rounded-2xl rounded-br-sm px-4 py-2.5 leading-relaxed">{m.text}</div>
                      </div>
                    ) : m.unavailable ? (
                      <div key={i} className="flex justify-start">
                        <div className="max-w-[90%] bg-white border border-ink/10 text-xs text-ink/70 rounded-2xl rounded-bl-sm px-4 py-3 leading-relaxed">{DEFAULT_COACH_HINT}</div>
                      </div>
                    ) : (
                      <div key={i} className="flex justify-start">
                        <div className="max-w-[90%] bg-copper/10 border border-copper/20 text-sm text-ink rounded-2xl rounded-bl-sm px-4 py-2.5 leading-relaxed whitespace-pre-wrap">{m.text}</div>
                      </div>
                    ))}
                    {coachBusy && <p className="text-xs text-ink/40 animate-pulse">Coach is thinking…</p>}
                  </div>
                  <div className="flex items-center gap-2 p-3 border-t border-ink/10">
                    <input value={coachText} onChange={(e) => setCoachText(e.target.value)}
                      onKeyDown={(e) => e.key === "Enter" && sendCoach()}
                      placeholder="Explain this in a new way…"
                      className="flex-1 px-3 py-2 rounded-lg border border-ink/20 text-sm font-semibold focus:ring-2 focus:ring-copper focus:outline-none" data-testid="coach-input" />
                    <button onClick={sendCoach} disabled={coachBusy} className="w-9 h-9 rounded-lg bg-ink text-signal flex items-center justify-center hover:bg-ink/85 disabled:opacity-50 transition-colors" data-testid="coach-send">
                      <Send className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              )}
            </div>

            <div className="card-flat bg-white border border-ink/10 p-5 text-xs text-ink/55 leading-relaxed">
              <Target className="w-4 h-4 text-copper inline mr-1" />
              Mastery rule: complete the knowledge check at {data.course.passing_score}%+ and the lesson is yours — the next one unlocks. Below that, review and retry. Best scores are saved to your parent dashboard.
            </div>
          </aside>
        </div>
      </div>
    </AppShell>
  );
}

function flatten(units) {
  const out = [];
  for (const u of units || []) for (const l of u.lessons || []) out.push(l);
  return out;
}

function ContentBlock({ block }) {
  if (block.type === "p") return <p className="text-ink/80 leading-relaxed text-[15px]">{block.text}</p>;
  if (block.type === "list") return (
    <ul className="space-y-2">
      {block.items.map((it, i) => (
        <li key={i} className="flex gap-2.5 text-ink/80 leading-relaxed text-[15px]">
          <span className="text-copper font-black mt-0.5 shrink-0">•</span><span>{it}</span>
        </li>
      ))}
    </ul>
  );
  if (block.type === "example") return (
    <div className="rounded-xl border border-copper/25 bg-copper/[0.06] p-5">
      {block.title && <div className="flex items-center gap-2 text-xs font-black uppercase tracking-widest text-copper mb-2"><Sparkles className="w-3.5 h-3.5" /> {block.title}</div>}
      <p className="text-ink/80 leading-relaxed text-[15px] whitespace-pre-line">{block.text}</p>
    </div>
  );
  if (block.type === "tip") return (
    <div className="rounded-xl border border-blue-600/25 bg-blue-600/[0.05] p-5 flex gap-3">
      <Lightbulb className="w-5 h-5 text-blue-700 shrink-0 mt-0.5" />
      <p className="text-ink/80 leading-relaxed text-[15px]">{block.text}</p>
    </div>
  );
  if (block.type === "activity") return (
    <div className="rounded-xl border border-ink/15 bg-ink/[0.03] p-5">
      {block.title && <div className="flex items-center gap-2 text-xs font-black uppercase tracking-widest text-ink/60 mb-2"><RefreshCw className="w-3.5 h-3.5" /> {block.title}</div>}
      <p className="text-ink/80 leading-relaxed text-[15px]">{block.text}</p>
    </div>
  );
  return null;
}

function NextAction({ courseSlug, studentId, units, lessonSlug, passed }) {
  const all = flatten(units);
  const idx = all.findIndex((l) => l.slug === lessonSlug);
  const next = all[idx + 1];
  if (next && next.unlocked && !next.passed) {
    return (
      <Link to={`/academy/learn/${courseSlug}/${next.slug}?student=${studentId}`} className="inline-flex items-center gap-2 px-5 py-2.5 bg-ink text-signal font-black text-sm rounded-lg hover:bg-ink/85 transition-colors" data-testid="already-passed-next">
        Next lesson: {next.title} <ArrowRight className="w-4 h-4" />
      </Link>
    );
  }
  return (
    <Link to={studentId ? `/academy/student/${studentId}` : "/academy/parent"} className="inline-flex items-center gap-2 px-5 py-2.5 bg-ink text-signal font-black text-sm rounded-lg hover:bg-ink/85 transition-colors">
      Back to classroom <ArrowRight className="w-4 h-4" />
    </Link>
  );
}
