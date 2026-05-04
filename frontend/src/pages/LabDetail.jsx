import { useEffect, useState } from "react";
import AppShell from "../components/AppShell";
import { api } from "../lib/api";
import { useParams, Link } from "react-router-dom";
import { toast } from "sonner";
import { ArrowLeft, ShieldAlert, CheckCircle2, Clock } from "lucide-react";
import Simulators from "../components/simulators";

export default function LabDetail() {
  const { slug } = useParams();
  const [lab, setLab] = useState(null);
  const [result, setResult] = useState(null);
  const [photoUrl, setPhotoUrl] = useState("");
  const [notes, setNotes] = useState("");

  const load = () => api.get(`/labs/${slug}`).then((r) => { setLab(r.data); if (r.data.my_submission?.track === "inperson") { setPhotoUrl(r.data.my_submission.photo_url || ""); setNotes(r.data.my_submission.notes || ""); } });
  useEffect(() => { load(); }, [slug]);

  const submitOnline = async (answers) => {
    try {
      const r = await api.post(`/labs/${slug}/submit`, { lab_slug: slug, answers });
      setResult(r.data);
      toast[r.data.status === "passed" ? "success" : "warning"](`${r.data.score.toFixed(0)}% — ${r.data.status.toUpperCase()}`);
      load();
    } catch { toast.error("Submission failed"); }
  };

  const submitInPerson = async () => {
    if (!photoUrl && !notes) { toast.error("Upload a photo URL or add notes"); return; }
    try {
      await api.post(`/labs/${slug}/submit`, { lab_slug: slug, photo_url: photoUrl, notes });
      toast.success("Submitted — awaiting instructor review");
      load();
    } catch { toast.error("Submission failed"); }
  };

  if (!lab) return <AppShell><div className="p-10">Loading…</div></AppShell>;
  const sub = lab.my_submission;
  const SimComp = lab.track === "online" ? Simulators[lab.simulator_type] : null;

  return (
    <AppShell>
      <div className="px-10 py-10 max-w-5xl">
        <Link to="/labs" className="inline-flex items-center gap-2 text-sm font-bold uppercase tracking-widest text-ink/60 hover:text-copper" data-testid="back-labs">
          <ArrowLeft className="w-4 h-4" /> All Labs
        </Link>

        <div className="mt-6 flex items-start justify-between gap-8">
          <div>
            <div className="overline text-copper">
              {lab.track === "online" ? "ONLINE SIMULATION" : "IN-PERSON LAB"} · {lab.hours}h · {lab.skill_points} skill points
            </div>
            <h1 className="font-heading text-4xl lg:text-5xl font-bold mt-3 leading-tight">{lab.title}</h1>
            <p className="text-ink/70 mt-4 max-w-3xl leading-relaxed">{lab.summary}</p>
          </div>
          {sub && <span className={sub.status === "passed" || sub.status === "approved" ? "badge-signal" : sub.status === "pending" ? "badge-copper" : "badge-outline"}>{sub.status.toUpperCase()}</span>}
        </div>

        <Section title="Learning Objectives" testid="obj">
          <ul className="space-y-2">{lab.objectives?.map((o, i) => <li key={i} className="flex gap-3"><span className="text-copper font-mono font-bold">{(i + 1).toString().padStart(2, "0")}</span><span>{o}</span></li>)}</ul>
        </Section>

        <div className="mt-6 bg-destructive/5 border-l-4 border-destructive p-5" data-testid="safety">
          <div className="flex items-center gap-2"><ShieldAlert className="w-5 h-5 text-destructive" /><div className="font-heading font-bold">Safety Reminders</div></div>
          <ul className="space-y-1.5 mt-3 text-sm text-ink/80">{lab.safety?.map((s, i) => <li key={i}>— {s}</li>)}</ul>
        </div>

        {lab.track === "inperson" ? (
          <>
            <Section title="Tools Required" testid="tools">
              <ul className="grid sm:grid-cols-2 gap-2 font-mono text-sm">{lab.tools?.map((t, i) => <li key={i}>— {t}</li>)}</ul>
            </Section>
            <Section title="Materials Required" testid="materials">
              <ul className="grid sm:grid-cols-2 gap-2 font-mono text-sm">{lab.materials?.map((t, i) => <li key={i}>— {t}</li>)}</ul>
            </Section>
            <Section title="Instructor Demonstration + Student Tasks" testid="steps">
              <ol className="space-y-3">{lab.steps?.map((s, i) => (
                <li key={i} className="flex gap-4 p-3 border border-ink/10"><span className="font-heading font-black text-copper">T{i + 1}</span><span>{s}</span></li>
              ))}</ol>
            </Section>
            <Section title="Skill Demonstration Rubric" testid="rubric">
              <ul className="space-y-2">{lab.rubric?.map((r, i) => <li key={i} className="flex gap-3"><CheckCircle2 className="w-5 h-5 text-copper shrink-0" /><span>{r}</span></li>)}</ul>
              <div className="mt-4 p-3 bg-signal/20 border border-signal text-sm"><strong>Pass criteria:</strong> {lab.pass_criteria}</div>
            </Section>

            <div className="mt-8 card-flat p-6">
              <div className="overline text-copper">Submit Your Work</div>
              <div className="font-heading text-xl font-bold mt-2">Upload proof + notes for instructor sign-off</div>
              <div className="mt-4 space-y-3">
                <div>
                  <label className="overline text-ink/60">Photo/Video URL</label>
                  <input value={photoUrl} onChange={(e) => setPhotoUrl(e.target.value)}
                    placeholder="https://…"
                    className="w-full mt-2 px-4 py-3 bg-white border border-ink/20 focus:border-ink focus:outline-none focus:ring-2 focus:ring-signal font-mono text-sm"
                    data-testid="input-photo-url" />
                </div>
                <div>
                  <label className="overline text-ink/60">Notes to Instructor</label>
                  <textarea value={notes} onChange={(e) => setNotes(e.target.value)} rows={4}
                    placeholder="What went well, what you learned, any challenges…"
                    className="w-full mt-2 px-4 py-3 bg-white border border-ink/20 focus:border-ink focus:outline-none focus:ring-2 focus:ring-signal"
                    data-testid="input-notes" />
                </div>
                <button onClick={submitInPerson} className="btn-primary" data-testid="btn-submit-inperson">
                  <Clock className="w-4 h-4 inline mr-2" /> Submit for Review
                </button>
                {sub?.status === "rejected" && sub.feedback && (
                  <div className="mt-4 p-3 bg-destructive/10 border border-destructive text-sm">
                    <div className="overline text-destructive">Instructor feedback</div>
                    <div className="mt-1">{sub.feedback}</div>
                  </div>
                )}
                {sub?.status === "approved" && (
                  <div className="mt-4 p-3 bg-signal/20 border border-signal text-sm">
                    <div className="overline text-ink">Approved ✓</div>
                    {sub.feedback && <div className="mt-1">{sub.feedback}</div>}
                  </div>
                )}
              </div>
            </div>
          </>
        ) : (
          <>
            <Section title="Step-by-Step" testid="steps">
              <ol className="space-y-2">{lab.steps?.map((s, i) => <li key={i} className="flex gap-3"><span className="font-mono font-bold text-copper">{i + 1}.</span><span>{s}</span></li>)}</ol>
            </Section>

            <div className="mt-8 card-flat p-6" data-testid="simulator">
              <div className="overline text-copper">Interactive Simulator</div>
              <div className="font-heading text-xl font-bold mt-2 mb-5">Auto-graded</div>
              {SimComp ? <SimComp onSubmit={submitOnline} initial={sub?.answers} /> : <div className="text-ink/60">Simulator not available.</div>}
              {result && (
                <div className={`mt-5 p-4 border ${result.status === "passed" ? "border-signal bg-signal/20" : "border-destructive bg-destructive/5"}`}>
                  <div className="font-heading text-xl font-bold">{result.score.toFixed(0)}% · {result.status.toUpperCase()}</div>
                  {result.detail && <div className="text-sm mt-1 font-mono">{result.detail}</div>}
                </div>
              )}
              {sub?.auto_score != null && !result && (
                <div className="mt-5 p-4 border border-ink/20 bg-bone">
                  <div className="font-heading font-bold">Previous score: {sub.auto_score.toFixed(0)}%</div>
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </AppShell>
  );
}

function Section({ title, testid, children }) {
  return (
    <div className="mt-6 card-flat p-6" data-testid={`section-${testid}`}>
      <h3 className="font-heading text-xl font-bold">{title}</h3>
      <div className="mt-3 text-ink/80">{children}</div>
    </div>
  );
}
