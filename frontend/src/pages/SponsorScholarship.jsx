import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import PublicNav from "../components/PublicNav";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import { toast } from "sonner";

const TIERS = [
  {
    key: "full",
    icon: "🏆",
    title: "Full Scholarship",
    invest: "Fully covers a recipient's program, course, or material needs for an entire cycle.",
    impact: "Complete financial relief — the recipient focuses entirely on growth and mastery.",
    suggest: 25000,
    accent: "#92400e",
  },
  {
    key: "partial",
    icon: "🔑",
    title: "Partial Scholarship",
    invest: "Targets specific hurdles — exam fees, software licenses, textbooks, or single-month milestones.",
    impact: "Unblocks critical bottlenecks for learners in urgent need of targeted support.",
    suggest: 5000,
    accent: "#8a5a00",
  },
  {
    key: "collective",
    icon: "🤝",
    title: "Collective (Multiple Recipients)",
    invest: "Custom or tiered bulk funding for corporations, foundations, or high-impact patrons.",
    impact: "Funds an entire cohort of learners in a discipline — tech, trades, or the creative arts.",
    suggest: 100000,
    accent: "#7c3aed",
  },
];

const STATUS_LABEL = {
  pending: { text: "Awaiting payment", color: "#b45309", bg: "#fef3c7" },
  committed: { text: "Pledge recorded — office follow-up", color: "#1d4ed8", bg: "#dbeafe" },
  paid: { text: "Paid — awaiting match", color: "#065f46", bg: "#d1fae5" },
  matched: { text: "Matched to a scholar", color: "#1e40af", bg: "#dbeafe" },
};

function fmtUsd(cents) {
  return "$" + ((cents || 0) / 100).toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 2 });
}

export default function SponsorScholarship() {
  const { user, loading } = useAuth();
  const [funds, setFunds] = useState([]);
  const [pledges, setPledges] = useState([]);
  const [awards, setAwards] = useState([]);
  const [tier, setTier] = useState("partial");
  const [amount, setAmount] = useState("50");
  const [dedication, setDedication] = useState("");
  const [fundId, setFundId] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState(null);

  useEffect(() => {
    api.get("/scholarships/funds").then((r) => setFunds(r.data.funds || [])).catch(() => {});
    if (user) {
      api.get("/scholarships/sponsor/mine")
        .then((r) => { setPledges(r.data.pledges || []); setAwards(r.data.awards || []); })
        .catch(() => {});
    }
  }, [user]);

  function pickTier(t) {
    setTier(t.key);
    setAmount(String(t.suggest / 100));
  }

  async function pledge() {
    const cents = Math.round(parseFloat(amount || "0") * 100);
    if (!cents || cents < 500) return toast.error("Minimum sponsorship is $5.00");
    setSubmitting(true);
    try {
      const res = await api.post("/scholarships/pledge", {
        tier, amount_cents: cents, dedication, fund_id: fundId,
      });
      if (res.data.url) {
        window.location.href = res.data.url;
        return;
      }
      setResult(res.data);
      toast.success("Pledge recorded — thank you!");
      if (user) {
        const r2 = await api.get("/scholarships/sponsor/mine");
        setPledges(r2.data.pledges || []);
      }
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Could not record your pledge.");
    } finally {
      setSubmitting(false);
    }
  }

  const progress = (f) => Math.min(100, Math.round(((f.raised_cents || 0) / Math.max(f.goal_cents, 1)) * 100));

  return (
    <div style={{ background: "#faf9f7", minHeight: "100dvh" }}>
      <PublicNav />

      {/* HERO */}
      <section className="relative overflow-hidden" style={{ background: "linear-gradient(160deg,#0d0a06 0%,#241a08 55%,#0d1a0a 100%)", color: "#fff" }}>
        <div className="max-w-5xl mx-auto px-4 sm:px-6 py-14 sm:py-20">
          <div className="overline" style={{ color: "#E8A51E" }}>Sponsor a Scholarship · Milestone-Based Giving</div>
          <h1 className="font-heading font-black mt-3" style={{ fontSize: "clamp(1.9rem, 5vw, 3.2rem)", lineHeight: 1.1 }}>
            Empower the Next Wave of Innovators, Creators, and Leaders
          </h1>
          <p className="mt-4 max-w-2xl leading-relaxed" style={{ color: "rgba(255,255,255,0.7)", fontSize: "1rem" }}>
            Turn your resources into lifelong transformation through the M.O.R.E. Scholarship Initiative. Every day,
            talented people in the M.O.R.E. network are one step away from their goals — held back only by financial
            friction. Whether it's tools, certification fees, or tuition, your sponsorship bridges the gap between
            potential and achievement. <strong style={{ color: "#fff" }}>And it's fully transparent:</strong> funds release
            only as recipients hit verified milestones.
          </p>
          <div className="flex flex-wrap gap-3 mt-8">
            <a href="#tiers" className="inline-flex items-center gap-2 font-bold text-sm px-6 py-3 rounded-xl" style={{ background: "#E8A51E", color: "#0a0a0a" }}>
              Become a Sponsor Today
            </a>
            <Link to="/scholarships/apply" className="inline-flex items-center gap-2 font-bold text-sm px-6 py-3 rounded-xl border" style={{ borderColor: "rgba(255,255,255,0.25)", color: "rgba(255,255,255,0.9)" }}>
              Need a scholarship? Apply →
            </Link>
          </div>
        </div>
      </section>

      {/* LIVE FUNDS */}
      <section className="py-12 px-4 sm:px-6" style={{ background: "#fff" }}>
        <div className="max-w-5xl mx-auto">
          <div className="overline text-copper mb-2">Open Funds · Live Progress</div>
          <h2 className="font-heading font-black text-2xl text-ink">Where your sponsorship goes</h2>
          <div className="grid md:grid-cols-3 gap-4 mt-6">
            {funds.map((f) => (
              <div key={f.id} className="rounded-2xl p-5" style={{ background: "#faf9f7", border: "1px solid #eee7db" }}>
                <div className="font-heading font-extrabold text-ink">{f.title}</div>
                <p className="text-xs text-ink/60 mt-2 leading-relaxed">{f.description}</p>
                <div className="mt-3 h-2 rounded-full" style={{ background: "#eee7db" }}>
                  <div className="h-2 rounded-full" style={{ width: progress(f) + "%", background: "#E8A51E" }} />
                </div>
                <div className="flex justify-between text-xs mt-1.5 font-bold">
                  <span style={{ color: "#8a5a00" }}>{fmtUsd(f.raised_cents || 0)} raised</span>
                  <span className="text-ink/50">of {fmtUsd(f.goal_cents)}</span>
                </div>
                <button
                  onClick={() => { setFundId(f.id); document.getElementById("pledge").scrollIntoView({ behavior: "smooth" }); }}
                  className="mt-3 w-full text-xs font-bold py-2 rounded-lg"
                  style={{ background: "#1f2933", color: "#fff" }}>
                  Sponsor this fund →
                </button>
              </div>
            ))}
            {funds.length === 0 && <p className="text-sm text-ink/40">Funds are being seeded — check back shortly.</p>}
          </div>
        </div>
      </section>

      {/* TIERS */}
      <section id="tiers" className="py-12 px-4 sm:px-6" style={{ background: "#faf9f7" }}>
        <div className="max-w-5xl mx-auto">
          <div className="overline text-copper mb-2">Choose Your Impact Level</div>
          <h2 className="font-heading font-black text-2xl text-ink mb-6">Three ways to open doors</h2>
          <div className="grid md:grid-cols-3 gap-4">
            {TIERS.map((t) => (
              <button key={t.key} onClick={() => pickTier(t)}
                className="text-left rounded-2xl p-6 transition-all"
                style={{
                  background: tier === t.key ? "#fff" : "#f3efe7",
                  border: tier === t.key ? "2px solid " + t.accent : "1px solid #eee7db",
                  boxShadow: tier === t.key ? "0 12px 32px rgba(0,0,0,0.10)" : "none",
                  cursor: "pointer",
                }}>
                <div style={{ fontSize: 26 }}>{t.icon}</div>
                <div className="font-heading font-extrabold text-ink mt-2" style={{ fontSize: "1.05rem" }}>{t.title}</div>
                <p className="text-xs text-ink/60 mt-2 leading-relaxed"><strong>Investment:</strong> {t.invest}</p>
                <p className="text-xs text-ink/60 mt-1 leading-relaxed"><strong>Impact:</strong> {t.impact}</p>
                <div className="text-[11px] font-bold mt-3" style={{ color: t.accent }}>Suggested: {fmtUsd(t.suggest)} · tap to select</div>
              </button>
            ))}
          </div>

          {/* PLEDGE FORM */}
          <div id="pledge" className="rounded-2xl p-6 sm:p-8 mt-8" style={{ background: "#fff", border: "1px solid #eee7db" }}>
            <h3 className="font-heading font-extrabold text-xl text-ink">Make your pledge</h3>
            {!loading && !user && (
              <div className="rounded-xl p-4 mt-4 text-sm" style={{ background: "#fef3c7", border: "1px solid #fde68a" }}>
                Create a free account to sponsor — it keeps your pledge, receipts, and scholar updates in one place.
                <div className="flex gap-2 mt-3">
                  <Link to="/register" className="text-xs font-bold px-4 py-2 rounded-lg" style={{ background: "#E8A51E", color: "#0a0a0a" }}>Join free</Link>
                  <Link to="/login" className="text-xs font-bold px-4 py-2 rounded-lg border" style={{ borderColor: "#d6c9a8", color: "#8a5a00" }}>Sign in</Link>
                </div>
              </div>
            )}
            {user && (
              <>
                <div className="grid sm:grid-cols-3 gap-4 mt-5">
                  <label className="block text-xs font-bold text-ink/70">
                    Amount (USD)
                    <input type="number" min="5" value={amount} onChange={(e) => setAmount(e.target.value)}
                      className="mt-1 w-full rounded-lg px-3 py-2.5 text-sm border"
                      style={{ borderColor: "#ddd3c0", background: "#faf9f7" }} />
                  </label>
                  <label className="block text-xs font-bold text-ink/70">
                    Fund (optional — general pool if empty)
                    <select value={fundId} onChange={(e) => setFundId(e.target.value)}
                      className="mt-1 w-full rounded-lg px-3 py-2.5 text-sm border"
                      style={{ borderColor: "#ddd3c0", background: "#faf9f7" }}>
                      <option value="">General scholarship pool</option>
                      {funds.map((f) => <option key={f.id} value={f.id}>{f.title}</option>)}
                    </select>
                  </label>
                  <label className="block text-xs font-bold text-ink/70">
                    Dedication / naming (optional)
                    <input value={dedication} onChange={(e) => setDedication(e.target.value)} placeholder="In honor of…"
                      className="mt-1 w-full rounded-lg px-3 py-2.5 text-sm border"
                      style={{ borderColor: "#ddd3c0", background: "#faf9f7" }} />
                  </label>
                </div>
                <button onClick={pledge} disabled={submitting}
                  className="mt-5 w-full sm:w-auto font-bold text-sm px-8 py-3.5 rounded-xl disabled:opacity-50"
                  style={{ background: "#E8A51E", color: "#0a0a0a" }}>
                  {submitting ? "Opening secure checkout…" : `Sponsor ${fmtUsd(Math.round(parseFloat(amount || "0") * 100)) || ""} now`}
                </button>
                <p className="text-[11px] text-ink/40 mt-2">Secure checkout via Lemon Squeezy. Funds release to recipients only as verified milestones are met.</p>
              </>
            )}
          </div>

          {/* WHY PARTNER */}
          <div className="grid md:grid-cols-3 gap-4 mt-8">
            {[
              ["Direct Connection", "Bypass bureaucratic red tape. Know the category, progress, and milestones of the community you uplift."],
              ["Workforce Pipeline", "Connect with emerging talent in your industry and help cultivate the workforce of tomorrow."],
              ["Verified Integrity", "Milestone-based disbursement — your funds release only as recipients hit genuine educational and professional checkpoints."],
            ].map(([t, b]) => (
              <div key={t} className="rounded-2xl p-5" style={{ background: "#fff", border: "1px solid #eee7db" }}>
                <div className="font-heading font-extrabold text-ink">{t}</div>
                <p className="text-sm text-ink/70 mt-2 leading-relaxed">{b}</p>
              </div>
            ))}
          </div>

          {/* TOOL LINK */}
          <div className="rounded-2xl p-5 mt-8 flex flex-col sm:flex-row sm:items-center gap-3" style={{ background: "#1f2933", color: "#fff" }}>
            <div className="flex-1">
              <div className="font-heading font-extrabold">Tell impact stories in video — free, in your browser</div>
              <p className="text-xs mt-1" style={{ color: "rgba(255,255,255,0.65)" }}>The Video Presentation Builder turns images and a script into a narrated WebM — built for sponsor impact reports and applicant spotlights. Nothing is uploaded; it runs 100% on your device.</p>
            </div>
            <Link to="/studio/video-presenter" className="text-xs font-bold px-5 py-2.5 rounded-lg shrink-0 text-center" style={{ background: "#E8A51E", color: "#0a0a0a" }}>Open the builder →</Link>
          </div>
        </div>
      </section>

      {/* SPONSOR DASHBOARD */}
      {user && (pledges.length > 0 || awards.length > 0) && (
        <section className="py-12 px-4 sm:px-6" style={{ background: "#fff" }}>
          <div className="max-w-5xl mx-auto">
            <h2 className="font-heading font-black text-2xl text-ink mb-1">Your sponsorship dashboard</h2>
            <p className="text-sm text-ink/60 mb-6">Every pledge and every matched scholar, with live milestone progress.</p>
            <div className="space-y-4">
              {awards.map((a) => {
                const ms = a.milestones || [];
                const done = ms.filter((m) => m.status === "verified").length;
                return (
                  <div key={a.id} className="rounded-2xl p-5" style={{ background: "#faf9f7", border: "1px solid #eee7db" }}>
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div className="font-heading font-extrabold text-ink">{a.recipient_goal || "Matched scholar"}</div>
                      <span className="text-xs font-bold px-3 py-1 rounded-full" style={{ background: "#d1fae5", color: "#065f46" }}>Matched · {fmtUsd(a.amount_cents)}</span>
                    </div>
                    <div className="mt-3 space-y-2">
                      {ms.map((m) => (
                        <div key={m.id} className="flex items-center gap-2 text-sm">
                          <span>{m.status === "verified" ? "✅" : "⏳"}</span>
                          <span className={m.status === "verified" ? "text-ink/80" : "text-ink/50"}>{m.title}</span>
                        </div>
                      ))}
                    </div>
                    <div className="mt-2 text-xs font-bold" style={{ color: "#8a5a00" }}>{done}/{ms.length} milestones verified</div>
                  </div>
                );
              })}
              {pledges.map((p) => {
                const s = STATUS_LABEL[p.status] || { text: p.status, color: "#444", bg: "#eee" };
                return (
                  <div key={p.id} className="flex flex-wrap items-center justify-between gap-2 rounded-2xl p-4" style={{ background: "#faf9f7", border: "1px solid #eee7db" }}>
                    <div>
                      <div className="font-bold text-ink text-sm">{fmtUsd(p.amount_cents)} — {TIERS.find((t) => t.key === p.tier)?.title || p.tier}</div>
                      <div className="text-xs text-ink/50">{new Date(p.created_at).toLocaleDateString()}</div>
                    </div>
                    <span className="text-xs font-bold px-3 py-1 rounded-full" style={{ background: s.bg, color: s.color }}>{s.text}</span>
                  </div>
                );
              })}
            </div>
          </div>
        </section>
      )}

      {/* GRACE RESULT */}
      {result && result.grace && (
        <div className="max-w-5xl mx-auto px-4 pb-12">
          <div className="rounded-2xl p-5 text-sm" style={{ background: "#dbeafe", border: "1px solid #bfdbfe", color: "#1e40af" }}>
            ✅ {result.message}
          </div>
        </div>
      )}
    </div>
  );
}
