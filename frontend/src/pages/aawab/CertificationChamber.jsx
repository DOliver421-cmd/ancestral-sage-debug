/**
 * CertificationChamber — AAWAB interactive wizard.
 *
 * Walks an agent through the full certification path:
 *   Select Agent → Intake Diagnostic → Treatment Execution → Stress Gauntlet →
 *   Certification → ACA Badge (downloadable / shareable / verifiable).
 */

import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import AppShell from "../../components/AppShell";
import { api, BACKEND_URL } from "../../lib/api";
import { toast } from "sonner";
import {
  Award, Stethoscope, Syringe, Swords, BadgeCheck, Loader2, ArrowLeft,
  ArrowRight, Download, Share2, HeartPulse, CheckCircle2, ShieldCheck, Sparkles,
} from "lucide-react";

const STEPS = [
  { key: "select",  label: "Select Agent",    icon: HeartPulse },
  { key: "diagnose", label: "Intake Diagnostic", icon: Stethoscope },
  { key: "treat",   label: "Treatment",       icon: Syringe },
  { key: "gauntlet", label: "Stress Gauntlet", icon: Swords },
  { key: "badge",   label: "Certification",   icon: Award },
];

const TREATMENTS = [
  { key: "context_defragmentation", label: "Context Defragmentation", desc: "Prune bloated prompt histories + compress vector memory." },
  { key: "infinite_loop_detox",     label: "Infinite-Loop Detox",      desc: "Sever runaway loops, restore from last clean snapshot." },
  { key: "memory_prune",            label: "Memory Prune",             desc: "Remove corrupted embeddings + redundant records." },
  { key: "prompt_recalibration",    label: "Prompt Recalibration",     desc: "Re-ground the system prompt, re-calibrate attention." },
];

export default function CertificationChamber() {
  const navigate = useNavigate();
  const [agents, setAgents] = useState([]);
  const [agentId, setAgentId] = useState("");
  const [stepIdx, setStepIdx] = useState(0);
  const [diagnosis, setDiagnosis] = useState(null);
  const [vitals, setVitals] = useState(null);
  const [treatKey, setTreatKey] = useState("context_defragmentation");
  const [treatmentsDone, setTreatmentsDone] = useState(0);
  const [gauntletRunning, setGauntletRunning] = useState(false);
  const [gauntletLog, setGauntletLog] = useState([]);
  const [badge, setBadge] = useState(null);
  const [busy, setBusy] = useState(false);
  const [loadingAgents, setLoadingAgents] = useState(true);

  useEffect(() => {
    api.get("/aawab/agents")
      .then(({ data }) => setAgents(data.agents || []))
      .catch(() => {})
      .finally(() => setLoadingAgents(false));
  }, []);

  const currentAgent = agents.find((a) => a.agent_id === agentId);

  const go = (i) => setStepIdx(Math.max(0, Math.min(STEPS.length - 1, i)));

  const runDiagnose = async () => {
    if (!agentId) { toast.error("Pick an agent first."); return; }
    setBusy(true);
    try {
      const { data } = await api.post(`/aawab/agents/${agentId}/diagnose`);
      setDiagnosis(data.diagnosis);
      setVitals(data.diagnosis);
      toast.success(`Baseline CVS ${data.diagnosis.cvs} — ${data.diagnosis.verdict}`);
      go(2);
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Diagnostic failed.");
    } finally {
      setBusy(false);
    }
  };

  const runTreatment = async (key) => {
    if (!agentId) return;
    setBusy(true);
    try {
      const { data } = await api.post(`/aawab/agents/${agentId}/treat`, { treatment_type: key });
      setVitals(data.vitals);
      setTreatmentsDone((n) => n + 1);
      toast.success(`${STEPS.find((s) => s.key === "treat").label}: CVS now ${data.vitals.cognitive_vitality_score}`);
      return data;
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Treatment failed.");
      return null;
    } finally {
      setBusy(false);
    }
  };

  const runGauntlet = async () => {
    if (!agentId) return;
    setGauntletRunning(true);
    setGauntletLog([]);
    const events = [
      "Injecting rate-limit storm (Groq 429s)…",
      "Simulating provider latency spikes…",
      "Forcing partial outage + fallback migration…",
      "Monitoring for loops, drift, and memory corruption…",
      "Measuring homeostatic resilience…",
    ];
    for (let i = 0; i < events.length; i++) {
      await new Promise((r) => setTimeout(r, 700));
      setGauntletLog((l) => [...l, events[i]]);
    }
    const data = await runTreatment("stress_gauntlet");
    setGauntletRunning(false);
    if (data) {
      setGauntletLog((l) => [...l, `Gauntlet complete — CVS ${data.vitals.cognitive_vitality_score}.`]);
      go(4);
    }
  };

  const runCertify = async () => {
    if (!agentId) return;
    setBusy(true);
    try {
      const { data } = await api.post(`/aawab/agents/${agentId}/certify`);
      setBadge(data.badge);
      toast.success("Certified! Your agent earned an ACA badge.");
      go(4);
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Certification failed — keep treating.");
    } finally {
      setBusy(false);
    }
  };

  const downloadBadge = () => {
    if (!badge) return;
    const blob = new Blob([JSON.stringify(badge, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${badge.agent_name || "agent"}-ACA-badge.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const shareBadge = async () => {
    if (!badge) return;
    const url = `${BACKEND_URL}/api/aawab/badge/${badge.badge_id}/verify`;
    try {
      if (navigator.share) {
        await navigator.share({ title: `${badge.agent_name} — AAWAB Certified Agent`, url });
      } else {
        await navigator.clipboard.writeText(url);
        toast.success("Verification link copied.");
      }
    } catch {
      try { await navigator.clipboard.writeText(url); toast.success("Verification link copied."); } catch {}
    }
  };

  const step = STEPS[stepIdx];

  return (
    <AppShell>
      <div className="max-w-3xl mx-auto px-6 py-10">
        <button onClick={() => navigate("/aawab")} className="text-xs font-bold text-copper hover:underline flex items-center gap-1">
          <ArrowLeft className="w-3.5 h-3.5" /> Back to Registry
        </button>

        <div className="mt-4 flex items-center gap-3">
          <div className="w-11 h-11 rounded-2xl flex items-center justify-center" style={{ background: "linear-gradient(135deg,#1B4332,#2D6A4F)" }}>
            <Award className="w-6 h-6" style={{ color: "#E8A51E" }} />
          </div>
          <div>
            <h1 className="font-heading text-2xl font-bold text-ink">Certification Chamber</h1>
            <p className="text-sm text-ink/55">Grade an agent's homeostatic resilience and issue an AAWAB Certified Agent (ACA) badge.</p>
          </div>
        </div>

        {/* Stepper */}
        <div className="mt-6 flex items-center gap-1 overflow-x-auto">
          {STEPS.map((s, i) => {
            const Icon = s.icon;
            const done = i < stepIdx;
            const active = i === stepIdx;
            return (
              <div key={s.key} className="flex items-center gap-1 shrink-0">
                <button
                  onClick={() => i < stepIdx && go(i)}
                  className={`flex items-center gap-2 px-3 py-2 rounded-xl text-xs font-black transition-colors ${
                    active ? "bg-ink text-white" : done ? "bg-emerald-100 text-emerald-700 hover:bg-emerald-200" : "bg-bone text-ink/40"
                  }`}
                >
                  {done ? <CheckCircle2 className="w-4 h-4" /> : <Icon className="w-4 h-4" />}
                  {s.label}
                </button>
                {i < STEPS.length - 1 && <span className="w-4 h-px bg-ink/15" />}
              </div>
            );
          })}
        </div>

        <div className="mt-6 bg-white border border-ink/10 rounded-2xl p-7 shadow-sm">
          {/* STEP: select */}
          {step.key === "select" && (
            <div>
              <h2 className="font-heading font-bold text-lg text-ink">Select an agent to certify</h2>
              <p className="text-sm text-ink/55 mt-1">Only agents with a baseline CVS of 98+ can be certified. The chamber will guide you there.</p>
              {loadingAgents ? (
                <div className="flex items-center gap-2 py-10 text-ink/40"><Loader2 className="w-4 h-4 animate-spin text-copper" /> Loading…</div>
              ) : agents.length === 0 ? (
                <div className="py-10 text-center">
                  <p className="text-sm text-ink/50">No agents yet.</p>
                  <Link to="/aawab" className="btn-copper inline-block px-4 py-2 mt-4 rounded-xl text-sm font-black">Register one first</Link>
                </div>
              ) : (
                <div className="mt-4 space-y-2">
                  {agents.map((a) => (
                    <button
                      key={a.agent_id}
                      onClick={() => setAgentId(a.agent_id)}
                      className={`w-full flex items-center justify-between px-4 py-3 rounded-xl border-2 text-left transition-colors ${
                        agentId === a.agent_id ? "border-copper bg-copper/5" : "border-ink/10 hover:border-copper/40"
                      }`}
                    >
                      <span>
                        <span className="block font-bold text-ink">{a.name}</span>
                        <span className="block text-xs text-ink/45">{a.model_provider} · CVS {a.cognitive_vitality_score} · {a.status}</span>
                      </span>
                      {a.status === "certified" && <BadgeCheck className="w-5 h-5 text-emerald-600" />}
                    </button>
                  ))}
                </div>
              )}
              <div className="mt-6 flex justify-end">
                <button onClick={() => { runDiagnose(); }} disabled={!agentId || busy} className="btn-copper px-5 py-2.5 rounded-xl text-sm font-black flex items-center gap-2 disabled:opacity-50">
                  {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Stethoscope className="w-4 h-4" />}
                  Begin Intake Diagnostic
                </button>
              </div>
            </div>
          )}

          {/* STEP: diagnose */}
          {step.key === "diagnose" && (
            <div>
              <h2 className="font-heading font-bold text-lg text-ink">Intake Diagnostic</h2>
              <p className="text-sm text-ink/55 mt-1">Establish a baseline Cognitive Vitality Score (CVS / 100) and get the treatment prescription.</p>
              {diagnosis ? (
                <div className="mt-5 space-y-3">
                  <ScoreRow label="Cognitive Vitality Score" value={diagnosis.cvs} />
                  <ScoreRow label="Token Velocity" value={diagnosis.token_velocity} unit="/m" />
                  <ScoreRow label="Context Load Index" value={diagnosis.context_load_index} />
                  <ScoreRow label="Memory Fragmentation" value={diagnosis.memory_fragmentation} />
                  <div className={`mt-4 rounded-xl px-4 py-3 text-sm font-bold ${
                    diagnosis.verdict === "critical" ? "bg-red-50 text-red-700" : diagnosis.verdict === "elevated" ? "bg-amber-50 text-amber-800" : "bg-green-50 text-green-700"
                  }`}>
                    Verdict: {diagnosis.verdict.toUpperCase()} — {diagnosis.prescription_note}
                  </div>
                </div>
              ) : (
                <div className="py-10 text-center text-ink/40 text-sm">Run the diagnostic to see baseline vitals.</div>
              )}
              <div className="mt-6 flex justify-end">
                <button onClick={() => go(2)} className="btn-copper px-5 py-2.5 rounded-xl text-sm font-black flex items-center gap-2">
                  Continue to Treatment <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}

          {/* STEP: treat */}
          {step.key === "treat" && (
            <div>
              <h2 className="font-heading font-bold text-lg text-ink">Treatment Execution</h2>
              <p className="text-sm text-ink/55 mt-1">Run treatment protocols to raise CVS. You need 98+ to certify — treat until you get there.</p>
              <div className="mt-4 grid sm:grid-cols-2 gap-2">
                {TREATMENTS.map((t) => (
                  <button
                    key={t.key}
                    onClick={() => setTreatKey(t.key)}
                    className={`text-left px-4 py-3 rounded-xl border-2 transition-colors ${
                      treatKey === t.key ? "border-copper bg-copper/5" : "border-ink/10 hover:border-copper/40"
                    }`}
                  >
                    <span className="block text-sm font-bold text-ink">{t.label}</span>
                    <span className="block text-xs text-ink/50 mt-0.5">{t.desc}</span>
                  </button>
                ))}
              </div>
              <div className="mt-5 flex items-center gap-4 flex-wrap">
                <button
                  onClick={() => runTreatment(treatKey)}
                  disabled={busy}
                  className="btn-copper px-5 py-2.5 rounded-xl text-sm font-black flex items-center gap-2 disabled:opacity-50"
                >
                  {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Syringe className="w-4 h-4" />}
                  Run {TREATMENTS.find((t) => t.key === treatKey)?.label}
                </button>
                {vitals && (
                  <div className="text-sm">
                    <span className="text-ink/50">Current CVS: </span>
                    <span className="font-black text-ink">{vitals.cognitive_vitality_score}</span>
                    <span className="text-ink/35 text-xs ml-1">· {treatmentsDone} treatment{treatmentsDone === 1 ? "" : "s"} done</span>
                  </div>
                )}
              </div>
              <div className="mt-6 flex justify-between">
                <button onClick={() => go(1)} className="text-sm font-bold text-ink/50 hover:text-copper">← Re-diagnose</button>
                <button onClick={() => go(3)} className="btn-copper px-5 py-2.5 rounded-xl text-sm font-black flex items-center gap-2">
                  Proceed to Stress Gauntlet <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}

          {/* STEP: gauntlet */}
          {step.key === "gauntlet" && (
            <div>
              <h2 className="font-heading font-bold text-lg text-ink flex items-center gap-2">
                <Swords className="w-5 h-5 text-copper" /> Stress Gauntlet
              </h2>
              <p className="text-sm text-ink/55 mt-1">
                A simulated failure storm — rate limits, latency spikes, partial outages. Measures homeostatic resilience under pressure.
              </p>
              <div className="mt-4 bg-ink text-white rounded-xl p-4 font-mono text-xs space-y-1.5 min-h-[150px]">
                {gauntletLog.length === 0 && !gauntletRunning && <span className="text-white/40">// awaiting simulation…</span>}
                {gauntletLog.map((l, i) => (
                  <p key={i} className={l.startsWith("Gauntlet complete") ? "text-emerald-400" : "text-white/80"}>{l}</p>
                ))}
                {gauntletRunning && <p className="text-signal animate-pulse">▌</p>}
              </div>
              <div className="mt-5">
                {!gauntletRunning ? (
                  <button onClick={runGauntlet} disabled={busy} className="btn-copper px-5 py-2.5 rounded-xl text-sm font-black flex items-center gap-2 disabled:opacity-50">
                    {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Swords className="w-4 h-4" />}
                    Run the Gauntlet
                  </button>
                ) : (
                  <span className="text-sm font-bold text-ink/50 flex items-center gap-2">
                    <Loader2 className="w-4 h-4 animate-spin text-copper" /> Simulating failure storm…
                  </span>
                )}
              </div>
              <div className="mt-6 flex justify-between">
                <button onClick={() => go(2)} className="text-sm font-bold text-ink/50 hover:text-copper">← Back to Treatment</button>
                <button onClick={runCertify} disabled={busy} className="px-5 py-2.5 rounded-xl text-sm font-black flex items-center gap-2 disabled:opacity-50" style={{ background: "#15803d", color: "#fff" }}>
                  {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Award className="w-4 h-4" />}
                  Attempt Certification
                </button>
              </div>
            </div>
          )}

          {/* STEP: badge */}
          {step.key === "badge" && (
            <div>
              {badge ? (
                <div className="text-center">
                  <div className="w-20 h-20 mx-auto rounded-3xl flex items-center justify-center" style={{ background: "linear-gradient(135deg,#1B4332,#2D6A4F)", boxShadow: "0 8px 24px rgba(27,67,50,0.35)" }}>
                    <BadgeCheck className="w-10 h-10" style={{ color: "#E8A51E" }} />
                  </div>
                  <h2 className="font-heading text-2xl font-bold text-ink mt-4">AAWAB Certified Agent</h2>
                  <p className="text-sm text-ink/55 mt-1">
                    <span className="font-bold text-ink">{badge.agent_name}</span> earned the ACA badge with a CVS of <span className="font-black">{badge.cvs}</span>.
                  </p>

                  <div className="mt-5 mx-auto max-w-sm bg-bone border border-ink/10 rounded-2xl p-4 text-left font-mono text-[11px] text-ink/70 space-y-1">
                    <p>badge_id: <span className="text-copper">{badge.badge_id}</span></p>
                    <p>agent: {badge.agent_name} ({badge.model_provider})</p>
                    <p>cvs: {badge.cvs} · treatments: {badge.treatments_completed}</p>
                    <p>issued: {new Date(badge.issued_at).toLocaleString()}</p>
                    <p className="text-emerald-700">signature: {badge.signature.slice(0, 24)}…</p>
                  </div>

                  <div className="mt-6 flex justify-center gap-3 flex-wrap">
                    <button onClick={downloadBadge} className="btn-copper px-5 py-2.5 rounded-xl text-sm font-black flex items-center gap-2">
                      <Download className="w-4 h-4" /> Download Badge (JSON)
                    </button>
                    <button onClick={shareBadge} className="px-5 py-2.5 rounded-xl text-sm font-black border-2 border-ink/15 hover:border-copper transition-colors flex items-center gap-2">
                      <Share2 className="w-4 h-4" /> Share Verify Link
                    </button>
                  </div>
                  <p className="mt-3 text-xs text-ink/40">
                    Anyone can verify at <code className="text-copper">{BACKEND_URL}/api/aawab/badge/{badge.badge_id}/verify</code>
                  </p>
                  <div className="mt-6 flex justify-center gap-3">
                    <Link to="/aawab" className="text-sm font-bold text-ink/50 hover:text-copper">← Back to Registry</Link>
                    <Link to="/aawab" className="text-sm font-bold text-copper hover:underline flex items-center gap-1">
                      <Sparkles className="w-4 h-4" /> Certify another agent
                    </Link>
                  </div>
                </div>
              ) : (
                <div className="text-center py-14">
                  <ShieldCheck className="w-10 h-10 mx-auto text-ink/20" />
                  <h2 className="font-heading font-bold text-lg text-ink mt-4">Certification pending</h2>
                  <p className="text-sm text-ink/50 mt-1 max-w-sm mx-auto">
                    Your agent's CVS hasn't cleared the 98% threshold yet. Head back to Treatment and run more protocols, then retry.
                  </p>
                  <div className="mt-6 flex justify-center gap-3">
                    <button onClick={() => go(2)} className="btn-copper px-5 py-2.5 rounded-xl text-sm font-black">Back to Treatment</button>
                    <button onClick={runCertify} disabled={busy} className="px-5 py-2.5 rounded-xl text-sm font-black disabled:opacity-50" style={{ background: "#15803d", color: "#fff" }}>
                      {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Award className="w-4 h-4" />} Retry Certification
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}

function ScoreRow({ label, value, unit = "" }) {
  const pct = Math.max(0, Math.min(100, value));
  const color = pct >= 90 ? "#15803d" : pct >= 70 ? "#b8860b" : pct >= 50 ? "#d97706" : "#b91c1c";
  return (
    <div className="flex items-center gap-3">
      <span className="w-44 text-xs font-bold text-ink/55">{label}</span>
      <div className="flex-1 h-2.5 rounded-full bg-ink/10 overflow-hidden">
        <div className="h-full rounded-full transition-all duration-700" style={{ width: `${pct}%`, background: color }} />
      </div>
      <span className="w-16 text-right text-sm font-black text-ink">{value}{unit}</span>
    </div>
  );
}
