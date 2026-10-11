import { useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { api } from "../../lib/api";
import AppShell from "../../components/AppShell";
import { errorMessage } from "./academyKit";
import {
  ArrowLeft, BookOpen, Briefcase, Folder, History, Lightbulb, Mic, Music, PenLine,
  Printer, Send, ShieldCheck, Sparkles, Trash2, Users, CheckCircle2,
} from "lucide-react";
import { AcademyFooter } from "./academyKit";
import { WAI_LOGO } from "../../lib/brand";

/* /academy/projects?student=… — the student's own work: family history,
   research, creative and performance projects, and business concepts.

   A project is private to the family account. Family members take part only if
   they want to and may stop at any time; nothing here is public, shared, or
   published unless the parent chooses to share it. */

const KIND_ICON = {
  family_history: History, research: BookOpen, creative: Music,
  performance: Mic, build: Lightbulb, business: Briefcase,
};

const PATHWAYS = [
  {
    title: "Family history",
    body: "Interview an elder, gather records, build a tree, map the migration, write the account. The steps are built into the project.",
    to: "/academy/projects",
    kind: "family_history",
  },
  {
    title: "Research to writing",
    body: "Pick a primary source, investigate it, and write it up for an audience. The Academy's social studies and literature courses supply the method.",
    to: "/academy/curriculum",
  },
  {
    title: "Creative work",
    body: "Poetry, music, visual art, or performance — built on the diasporic traditions the arts courses teach, recorded as a portfolio entry.",
    to: "/academy/curriculum",
    kind: "creative",
  },
  {
    title: "Creation to earning",
    body: "A finished project is the evidence half of a business. Turn a skill and a piece of work into a business concept, then publish it in your Academy portfolio.",
    to: "/academy/portfolio",
    kind: "business",
  },
];

export default function AcademyProjects() {
  const [params, setParams] = useSearchParams();
  const studentId = params.get("student");
  const [students, setStudents] = useState([]);
  const [projects, setProjects] = useState([]);
  const [selected, setSelected] = useState(null);
  const [kinds, setKinds] = useState({ kinds: [], family_history_steps: [] });
  const [title, setTitle] = useState("");
  const [summary, setSummary] = useState("");
  const [kind, setKind] = useState("family_history");
  const [draft, setDraft] = useState({});
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [loading, setLoading] = useState(true);

  const load = () => {
    if (!studentId) return;
    api.get(`/academy/projects?student_id=${studentId}`)
      .then((r) => setProjects(r.data.projects || []))
      .catch((e) => setError(errorMessage(e, "Could not load projects.")));
  };

  useEffect(() => {
    api.get("/academy/kinds".replace("/kinds", "/projects/kinds"))
      .then((r) => setKinds(r.data))
      .catch(() => {});
    api.get("/academy/students")
      .then((r) => setStudents((r.data?.students || []).filter((s) => s.status === "active")))
      .catch(() => {});
  }, []);

  useEffect(() => {
    setError(""); setNotice(""); setSelected(null);
    if (!studentId) { setLoading(false); return; }
    setLoading(true);
    load();
    setLoading(false);
  }, [studentId]);

  const kindLabel = (id) => kinds.kinds.find((k) => k.id === id)?.label || id;

  const chooseStudent = (id) => {
    const next = new URLSearchParams(params);
    if (id) next.set("student", id); else next.delete("student");
    setParams(next, { replace: true });
  };

  const create = async (e) => {
    e.preventDefault();
    if (!studentId || !title.trim()) { setError("Choose a student and give the project a title."); return; }
    setError("");
    try {
      const r = await api.post("/academy/projects", {
        student_id: studentId, title: title.trim(), kind,
        summary: summary.trim() || undefined,
        artifacts: kind === "family_history" ? {} : undefined,
      });
      setTitle(""); setSummary("");
      setSelected(r.data.project);
      load();
    } catch (err) {
      setError(errorMessage(err, "Could not create the project."));
    }
  };

  const saveArtifact = (stepId, value) => setDraft((d) => ({ ...d, [stepId]: value }));
  const saveStep = async (stepId) => {
    if (!selected) return;
    const artifacts = { ...(selected.artifacts || {}), [stepId]: draft[stepId] ?? selected.artifacts?.[stepId] ?? "" };
    if (!artifacts[stepId] || !artifacts[stepId].trim()) {
      setError("Write what you made or found before saving this step.");
      return;
    }
    try {
      const r = await api.patch(`/academy/projects/${selected.id}`, { artifacts });
      setSelected(r.data.project);
      load();
    } catch (err) {
      setError(errorMessage(err, "Could not save this step."));
    }
  };

  const submit = async () => {
    if (!selected) return;
    try {
      const r = await api.post(`/academy/projects/${selected.id}/submit`);
      setSelected(r.data.project);
      setNotice("Submitted. It is now a portfolio entry — print or share it from the portfolio.");
      load();
    } catch (err) {
      setError(errorMessage(err, "Could not submit the project."));
    }
  };

  const remove = async (id) => {
    if (!window.confirm("Delete this project? This cannot be undone.")) return;
    try {
      await api.delete(`/academy/projects/${id}`);
      if (selected?.id === id) setSelected(null);
      load();
    } catch (err) {
      setError(errorMessage(err, "Could not delete the project."));
    }
  };

  const student = students.find((s) => s.id === studentId);
  const openSteps = selected?.steps || [];
  const stepsDone = openSteps.filter((s) => s.done).length;

  return (
    <div className="min-h-screen bg-bone">
      <div className="no-print">
        <AppShell>
          <div className="max-w-6xl px-8 py-10">
            <Link to={studentId ? `/academy/student/${studentId}` : "/academy/parent"}
              className="inline-flex items-center gap-1.5 text-sm font-bold text-copper hover:text-ink transition-colors">
              <ArrowLeft className="w-4 h-4" /> {studentId ? "Back to the classroom" : "Back to the family dashboard"}
            </Link>

            <div className="flex items-center gap-3 mt-4">
              <Folder className="w-7 h-7 text-copper" />
              <h1 className="font-heading text-3xl font-black text-ink">Projects &amp; Portfolio</h1>
            </div>
            <p className="text-ink/60 mt-2 max-w-3xl leading-relaxed">
              Turn what a student learns into work they can show: family history, research, creative
              projects, performances, builds, and business concepts. Submitted projects become
              portfolio entries — the evidence half of a transcript.
            </p>

            <div className="mt-5 rounded-xl border border-emerald-200 bg-emerald-50/60 p-4 text-sm text-emerald-900 flex gap-3 print:hidden" data-testid="projects-privacy">
              <ShieldCheck className="w-5 h-5 shrink-0" />
              <div>
                <strong>Private to this family.</strong> Nothing here is public, shared, or published
                unless you choose to share it. Family members take part only if they want to, and may
                stop at any time.
              </div>
            </div>

            {error && (
              <div className="mt-5 card-flat p-4 text-sm font-bold text-destructive border-destructive/30 bg-destructive/5" data-testid="projects-error">
                {error}
                <button onClick={() => setError("")} className="ml-3 underline">Dismiss</button>
              </div>
            )}
            {notice && (
              <div className="mt-5 card-flat p-4 text-sm font-bold text-emerald-700 border-emerald-300 bg-emerald-50" data-testid="projects-notice">
                {notice}
              </div>
            )}

            <div className="mt-6 card-flat bg-white border border-ink/10 p-6">
              <label className="block text-sm font-bold text-ink mb-1" htmlFor="project-student">Which student?</label>
              <select id="project-student" value={studentId || ""} data-testid="projects-student-select"
                onChange={(e) => chooseStudent(e.target.value)}
                className="w-full border-2 border-ink/15 rounded-lg px-3 py-2.5 text-sm bg-white">
                <option value="">Choose a student…</option>
                {students.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
              </select>
              {students.length === 0 && (
                <p className="text-sm text-ink/55 mt-3">
                  No student profiles yet.{" "}
                  <Link to="/academy/parent" className="font-bold text-copper underline">Add one from the Family Dashboard</Link>.
                </p>
              )}
            </div>

            {studentId && (
              <div className="grid lg:grid-cols-5 gap-6 mt-6">
                {/* Project list + create */}
                <div className="lg:col-span-2 space-y-4">
                  <form onSubmit={create} className="card-flat bg-white border border-ink/10 p-6 space-y-4">
                    <div className="font-heading font-bold text-ink">Start a project</div>
                    <div>
                      <label className="block text-sm font-bold text-ink mb-1">Type</label>
                      <select value={kind} onChange={(e) => setKind(e.target.value)} data-testid="project-kind"
                        className="w-full border-2 border-ink/15 rounded-lg px-3 py-2.5 text-sm bg-white">
                        {(kinds.kinds.length ? kinds.kinds : [{ id: "family_history", label: "Family history" }]).map((k) => (
                          <option key={k.id} value={k.id}>{k.label}</option>
                        ))}
                      </select>
                      <p className="text-xs text-ink/55 mt-1">
                        {kinds.kinds.find((k) => k.id === kind)?.desc || "Collect family history, records, and stories."}
                      </p>
                    </div>
                    <div>
                      <label className="block text-sm font-bold text-ink mb-1">Title</label>
                      <input value={title} onChange={(e) => setTitle(e.target.value)}
                        placeholder="Our family's move from Georgia"
                        data-testid="project-title"
                        className="w-full border-2 border-ink/15 rounded-lg px-3 py-2.5 text-sm" />
                    </div>
                    <div>
                      <label className="block text-sm font-bold text-ink mb-1">One-line summary (optional)</label>
                      <input value={summary} onChange={(e) => setSummary(e.target.value)}
                        placeholder="Interviews, records, and the story of one generation."
                        className="w-full border-2 border-ink/15 rounded-lg px-3 py-2.5 text-sm" />
                    </div>
                    <button type="submit" data-testid="project-create"
                      className="btn-copper w-full inline-flex items-center justify-center gap-2">
                      <Sparkles className="w-4 h-4" /> Create project
                    </button>
                  </form>

                  <div className="card-flat bg-white border border-ink/10">
                    <div className="px-5 py-4 border-b border-ink/10 text-xs font-bold uppercase tracking-widest text-ink/50">
                      {student ? `${student.name}'s projects` : "Projects"} ({projects.length})
                    </div>
                    {projects.length === 0 ? (
                      <p className="px-5 py-6 text-sm text-ink/55">No projects yet. Start with a family history project.</p>
                    ) : (
                      <div className="divide-y divide-ink/5">
                        {projects.map((p) => {
                          const Icon = KIND_ICON[p.kind] || Folder;
                          return (
                            <button key={p.id} onClick={() => setSelected(p)}
                              className={`w-full text-left px-5 py-4 hover:bg-ink/[0.02] transition-colors ${selected?.id === p.id ? "bg-copper/10" : ""}`}>
                              <div className="flex items-start gap-3">
                                <Icon className="w-4 h-4 text-copper mt-0.5 shrink-0" />
                                <div className="min-w-0">
                                  <div className="font-bold text-ink text-sm truncate">{p.title}</div>
                                  <div className="text-xs text-ink/50">
                                    {p.kind_label} · {p.status === "submitted" ? "in portfolio" : p.progress_pct + "%"}
                                    {p.steps_completed ? ` · ${p.steps_completed}/${p.steps?.length} steps` : ""}
                                  </div>
                                </div>
                              </div>
                            </button>
                          );
                        })}
                      </div>
                    )}
                  </div>
                </div>

                {/* Detail */}
                <div className="lg:col-span-3">
                  {!selected ? (
                    <div className="card-flat bg-white border border-ink/10 p-8 text-center">
                      <PenLine className="w-8 h-8 text-copper mx-auto" />
                      <div className="font-heading font-bold text-ink mt-3">Choose or start a project</div>
                      <p className="text-sm text-ink/55 mt-2">
                        A family history project walks through the whole pathway: interviews, records, a tree, a map, and a written account.
                      </p>
                      <div className="grid sm:grid-cols-2 gap-3 mt-6 text-left">
                        {PATHWAYS.map((p) => (
                          <div key={p.title} className="rounded-xl border border-ink/10 p-4">
                            <div className="font-bold text-ink text-sm">{p.title}</div>
                            <p className="text-xs text-ink/55 mt-1 leading-relaxed">{p.body}</p>
                            {p.to !== "/academy/projects" && (
                              <Link to={p.to} className="text-xs font-bold text-copper underline mt-2 inline-block">
                                {p.to === "/academy/portfolio" ? "Open the portfolio" : "Browse the curriculum"}
                              </Link>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  ) : (
                    <div className="card-flat bg-white border border-ink/10 p-6" data-testid="project-detail">
                      <div className="flex items-start justify-between gap-4">
                        <div>
                          <div className="text-xs font-bold uppercase tracking-widest text-copper">{kindLabel(selected.kind)}</div>
                          <h2 className="font-heading text-xl font-black text-ink mt-1">{selected.title}</h2>
                          {selected.summary && <p className="text-sm text-ink/60 mt-1">{selected.summary}</p>}
                        </div>
                        <button onClick={() => remove(selected.id)} title="Delete project"
                          className="text-ink/40 hover:text-destructive transition-colors">
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>

                      {openSteps.length > 0 && (
                        <div className="mt-4 text-xs font-bold text-ink/50">
                          {stepsDone} of {openSteps.length} steps complete
                        </div>
                      )}

                      {openSteps.length > 0 ? (
                        <ol className="mt-3 space-y-4">
                          {openSteps.map((s, i) => (
                            <li key={s.id} className={`rounded-xl border p-4 ${s.done ? "border-emerald-300 bg-emerald-50/50" : "border-ink/10"}`}
                              data-testid={`step-${s.id}`}>
                              <div className="flex items-start gap-3">
                                <div className={`w-6 h-6 rounded-full shrink-0 grid place-items-center text-xs font-black ${s.done ? "bg-emerald-600 text-white" : "bg-ink/10 text-ink/60"}`}>
                                  {s.done ? <CheckCircle2 className="w-4 h-4" /> : i + 1}
                                </div>
                                <div className="min-w-0 flex-1">
                                  <div className="font-bold text-ink text-sm">{s.title}</div>
                                  <p className="text-xs text-ink/60 mt-1 leading-relaxed">{s.prompt}</p>
                                  <div className="mt-3">
                                    <label className="block text-[11px] font-bold uppercase tracking-wider text-ink/45">
                                      {s.artifact}
                                    </label>
                                    <textarea
                                      value={draft[s.id] ?? selected.artifacts?.[s.id] ?? ""}
                                      onChange={(e) => saveArtifact(s.id, e.target.value)}
                                      onBlur={() => saveStep(s.id)}
                                      rows={3}
                                      placeholder="What you made, found, or wrote…"
                                      className="mt-1 w-full border-2 border-ink/15 rounded-lg px-3 py-2 text-sm"
                                      data-testid={`artifact-${s.id}`}
                                    />
                                    {s.done && <div className="text-[11px] font-bold text-emerald-700 mt-1">Saved</div>}
                                  </div>
                                </div>
                              </div>
                            </li>
                          ))}
                        </ol>
                      ) : (
                        <p className="text-sm text-ink/55 mt-4">
                          This project type has no fixed steps — use the notes below to record the work, then submit it when it is ready.
                        </p>
                      )}

                      <div className="mt-4">
                        <label className="block text-[11px] font-bold uppercase tracking-wider text-ink/45">Notes</label>
                        <textarea value={selected.notes || ""} onChange={(e) => setSelected({ ...selected, notes: e.target.value })}
                          onBlur={async () => {
                            try { const r = await api.patch(`/academy/projects/${selected.id}`, { notes: selected.notes }); setSelected(r.data.project); }
                            catch (err) { setError(errorMessage(err, "Could not save notes.")); }
                          }}
                          rows={3} placeholder="Anything you want the record to show…"
                          className="mt-1 w-full border-2 border-ink/15 rounded-lg px-3 py-2 text-sm" />
                      </div>

                      <div className="flex flex-wrap gap-3 mt-5">
                        <button onClick={submit} disabled={selected.status === "submitted"}
                          data-testid="project-submit"
                          className="btn-copper inline-flex items-center gap-2 disabled:opacity-40">
                          <Send className="w-4 h-4" />
                          {selected.status === "submitted" ? "Submitted" : "Submit for the portfolio"}
                        </button>
                        <Link to={studentId ? `/academy/portfolio?student=${studentId}` : "/academy/portfolio"}
                          className="inline-flex items-center gap-2 text-sm font-bold text-copper hover:text-ink">
                          <Folder className="w-4 h-4" /> Open the portfolio
                        </Link>
                        <Link to={studentId ? `/academy/portfolio?student=${studentId}` : "/academy/portfolio"}
                          className="inline-flex items-center gap-2 text-sm font-bold text-ink hover:text-copper">
                          <Sparkles className="w-4 h-4" /> Publish the work in your portfolio
                        </Link>
                      </div>
                      {selected.status !== "submitted" && openSteps.length > 0 && (
                        <p className="text-xs text-ink/45 mt-2">
                          Add the work for every step before submitting.
                        </p>
                      )}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
          <AcademyFooter />
        </AppShell>
      </div>
    </div>
  );
}
