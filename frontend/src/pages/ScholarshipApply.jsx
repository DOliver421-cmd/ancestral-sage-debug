import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import PublicNav from "../components/PublicNav";
import BackButton from "../components/BackButton";
import { api } from "../lib/api";
import { toast } from "sonner";

const STATUS = {
  submitted: { text: "Submitted", color: "#1d4ed8", bg: "#dbeafe" },
  under_review: { text: "Under review", color: "#8a5a00", bg: "#fef3c7" },
  approved: { text: "Approved — awaiting match", color: "#065f46", bg: "#d1fae5" },
  matched: { text: "Matched to a sponsor", color: "#1e40af", bg: "#dbeafe" },
  denied: { text: "Not selected", color: "#b91c1c", bg: "#fee2e2" },
};

export default function ScholarshipApply() {
  const [funds, setFunds] = useState([]);
  const [apps, setApps] = useState([]);
  const [fundId, setFundId] = useState("");
  const [need, setNeed] = useState("");
  const [contribution, setContribution] = useState("");
  const [goal, setGoal] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function load() {
    api.get("/scholarships/funds").then((r) => setFunds(r.data.funds || [])).catch(() => {});
    api.get("/scholarships/applications/me").then((r) => setApps(r.data.applications || [])).catch(() => {});
  }

  useEffect(() => { load(); }, []);

  async function submit() {
    if (!fundId) return toast.error("Choose a scholarship fund.");
    setSubmitting(true);
    try {
      await api.post("/scholarships/apply", { fund_id: fundId, need_statement: need, contribution, goal });
      toast.success("Application received — the committee reviews in order.");
      setFundId(""); setNeed(""); setContribution(""); setGoal("");
      load();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Could not submit your application.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div style={{ background: "#faf9f7", minHeight: "100dvh" }}>
      <PublicNav />
      <div className="max-w-4xl mx-auto px-4 sm:px-6 py-10">
        <BackButton to="/sponsor" />
        <div className="mt-6">
          <div className="overline text-copper">Scholarship Application</div>
          <h1 className="font-heading text-3xl font-black text-ink mt-2">Apply for a scholarship.</h1>
          <p className="text-ink/60 mt-2 max-w-2xl text-sm leading-relaxed">
            One active application per fund. The review committee — platform administrators and community elders —
            scores applications on financial need, dedication to growth, and community contribution. You'll be
            notified at every step.
          </p>
        </div>

        <div className="grid lg:grid-cols-5 gap-6 mt-8">
          {/* FORM */}
          <div className="lg:col-span-3 rounded-2xl p-6" style={{ background: "#fff", border: "1px solid #eee7db" }}>
            <h2 className="font-heading font-extrabold text-lg text-ink">Your application</h2>
            <label className="block text-xs font-bold text-ink/70 mt-4">
              Which fund are you applying to?
              <select value={fundId} onChange={(e) => setFundId(e.target.value)}
                className="mt-1 w-full rounded-lg px-3 py-2.5 text-sm border" style={{ borderColor: "#ddd3c0", background: "#faf9f7" }}>
                <option value="">Select a fund…</option>
                {funds.map((f) => <option key={f.id} value={f.id}>{f.title}</option>)}
              </select>
            </label>
            <label className="block text-xs font-bold text-ink/70 mt-4">
              What is your financial need? (a few sentences)
              <textarea rows={3} value={need} onChange={(e) => setNeed(e.target.value)} placeholder="What would this scholarship unlock for you — and why can't you cover it alone?"
                className="mt-1 w-full rounded-lg px-3 py-2.5 text-sm border resize-none" style={{ borderColor: "#ddd3c0", background: "#faf9f7" }} />
            </label>
            <label className="block text-xs font-bold text-ink/70 mt-4">
              How do you contribute to your community?
              <textarea rows={3} value={contribution} onChange={(e) => setContribution(e.target.value)} placeholder="Mentorship, art, labor, care, organizing — the work you do for others."
                className="mt-1 w-full rounded-lg px-3 py-2.5 text-sm border resize-none" style={{ borderColor: "#ddd3c0", background: "#faf9f7" }} />
            </label>
            <label className="block text-xs font-bold text-ink/70 mt-4">
              What is your goal?
              <textarea rows={2} value={goal} onChange={(e) => setGoal(e.target.value)} placeholder="A certification, a tool, a course, a studio — the milestone you'll reach."
                className="mt-1 w-full rounded-lg px-3 py-2.5 text-sm border resize-none" style={{ borderColor: "#ddd3c0", background: "#faf9f7" }} />
            </label>
            <button onClick={submit} disabled={submitting}
              className="mt-5 font-bold text-sm px-8 py-3 rounded-xl disabled:opacity-50" style={{ background: "#E8A51E", color: "#0a0a0a" }}>
              {submitting ? "Submitting…" : "Submit application"}
            </button>
          </div>

          {/* STATUS */}
          <div className="lg:col-span-2">
            <h2 className="font-heading font-extrabold text-lg text-ink mb-3">My applications</h2>
            <div className="space-y-3">
              {apps.length === 0 && (
                <p className="text-sm text-ink/40 rounded-2xl p-5" style={{ background: "#fff", border: "1px dashed #ddd3c0" }}>
                  No applications yet. Pick a fund and tell us your story.
                </p>
              )}
              {apps.map((a) => {
                const s = STATUS[a.status] || { text: a.status, color: "#444", bg: "#eee" };
                return (
                  <div key={a.id} className="rounded-2xl p-4" style={{ background: "#fff", border: "1px solid #eee7db" }}>
                    <div className="font-bold text-sm text-ink">{a.fund_title || "Fund"}</div>
                    <span className="inline-block mt-2 text-xs font-bold px-3 py-1 rounded-full" style={{ background: s.bg, color: s.color }}>{s.text}</span>
                    {a.review_note && <p className="text-xs text-ink/60 mt-2">{a.review_note}</p>}
                    <div className="text-[11px] text-ink/40 mt-2">{new Date(a.created_at).toLocaleDateString()}</div>
                  </div>
                );
              })}
            </div>
            <div className="rounded-2xl p-4 mt-4 text-xs text-ink/60 leading-relaxed" style={{ background: "#fef3c7", border: "1px solid #fde68a" }}>
              💡 Know someone who'd fund this? Send them to the{" "}
              <Link to="/sponsor" className="font-bold underline" style={{ color: "#8a5a00" }}>Sponsor a Scholarship</Link> page.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
