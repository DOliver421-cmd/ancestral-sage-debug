import { useCallback, useEffect, useMemo, useState } from "react";
import AppShell from "../../components/AppShell";
import { api, BACKEND_URL } from "../../lib/api";
import { toast } from "sonner";
import {
  Activity, Award, BadgeCheck, Brain, Gauge, HeartPulse, Loader2, Plus,
  RefreshCw, ShieldAlert, Stethoscope, Syringe, Zap,
} from "lucide-react";

const STATUS_META = {
  active: { label: "Active", cls: "bg-green-100 text-green-800" },
  in_treatment: { label: "In Treatment", cls: "bg-amber-100 text-amber-800" },
  certified: { label: "Certified", cls: "bg-emerald-600 text-white" },
  isolated: { label: "Isolated", cls: "bg-red-100 text-red-700" },
};

const TREATMENTS = [
  { key: "context_defragmentation", label: "Context Defragmentation", desc: "Reduce bloated prompt history and context pressure." },
  { key: "infinite_loop_detox", label: "Infinite-Loop Detox", desc: "Check for runaway loops and restore a clean operating state." },
  { key: "memory_prune", label: "Memory Prune", desc: "Remove redundant or corrupted memory records." },
  { key: "prompt_recalibration", label: "Prompt Recalibration", desc: "Re-ground the agent against its declared purpose." },
  { key: "stress_gauntlet", label: "Stress Readiness Check", desc: "Measure resilience before certification." },
];

function cvsColor(cvs) {
  if (cvs >= 90) return "#15803d";
  if (cvs >= 70) return "#b8860b";
  if (cvs >= 50) return "#d97706";
  return "#b91c1c";
}

function VitalBar({ label, value = 0, max = 100, icon: Icon, unit = "" }) {
  const numeric = Number(value) || 0;
  const pct = Math.max(0, Math.min(100, (numeric / max) * 100));
  return (
    <div>
      <div className="flex items-center justify-between text-xs mb-1">
        <span className="text-ink/65 font-semibold flex items-center gap-1.5">
          {Icon && <Icon className="w-3.5 h-3.5 text-copper" />} {label}
        </span>
        <span className="font-black text-ink">{numeric}{unit}</span>
      </div>
      <div className="h-2 rounded-full bg-ink/10 overflow-hidden" aria-label={`${label}: ${numeric}${unit}`}>
        <div className="h-full rounded-full transition-all duration-700" style={{ width: `${pct}%`, background: label === "Vitality (CVS)" ? cvsColor(numeric) : "#b8860b" }} />
      </div>
    </div>
  );
}

function ScoreRow({ label, value, unit = "" }) {
  const numeric = Number(value) || 0;
  const pct = Math.max(0, Math.min(100, numeric));
  return (
    <div className="flex items-center gap-3">
      <span className="w-44 text-xs font-bold text-ink/65">{label}</span>
      <div className="flex-1 h-2.5 rounded-full bg-ink/10 overflow-hidden">
        <div className="h-full rounded-full" style={{ width: `${pct}%`, background: cvsColor(numeric) }} />
      </div>
      <span className="w-16 text-right text-sm font-black text-ink">{numeric}{unit}</span>
    </div>
  );
}

export default function AgentRegistryView() {
  const [agents, setAgents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [showRegister, setShowRegister] = useState(false);
  const [form, setForm] = useState({ name: "", model_provider: "groq" });
  const [busy, setBusy] = useState(null);
  const [treatSel, setTreatSel] = useState({});
  const [certAgentId, setCertAgentId] = useState("");
  const [diagnosis, setDiagnosis] = useState(null);
  const [vitals, setVitals] = useState(null);
  const [treatmentCount, setTreatmentCount] = useState(0);
  const [badge, setBadge] = useState(null);
  const [actionError, setActionError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setLoadError("");
    try {
      const { data } = await api.get("/aawab/agents");
      const nextAgents = data.agents || [];
      setAgents(nextAgents);
      setCertAgentId((current) => current || nextAgents[0]?.agent_id || "");
    } catch (e) {
      const message = e?.response?.data?.detail || "The AAWAB service could not load agent data.";
      setLoadError(message);
      toast.error(message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const selectedAgent = useMemo(
    () => agents.find((agent) => agent.agent_id === certAgentId),
    [agents, certAgentId],
  );

  const register = async () => {
    if (!form.name.trim()) {
      toast.error("Give your agent a name.");
      return;
    }
    setBusy("register");
    try {
      const { data } = await api.post("/aawab/register", { ...form, name: form.name.trim() });
      setAgents((current) => [data.agent, ...current]);
      setCertAgentId(data.agent.agent_id);
      setShowRegister(false);
      setForm({ name: "", model_provider: "groq" });
      toast.success(`${data.agent.name} was registered.`);
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Registration failed.");
    } finally {
      setBusy(null);
    }
  };

  const runAgentAction = async (agentId, action, extra = {}) => {
    const key = `${action}:${agentId}`;
    setActionError("");
    setBusy(key);
    try {
      const { data } = await api.post(`/aawab/agents/${agentId}/${action}`, extra);
      if (action === "diagnose") toast.success(`Diagnostic complete. CVS ${data.diagnosis.cvs}.`);
      if (action === "treat") toast.success(`Treatment complete. CVS ${data.vitals.cognitive_vitality_score}.`);
      if (action === "certify") toast.success("Certification complete.");
      await load();
      return data;
    } catch (e) {
      const message = e?.response?.data?.detail || `Could not run ${action}.`;
      setActionError(message);
      toast.error(message);
      return null;
    } finally {
      setBusy(null);
    }
  };

  const runDiagnosis = async () => {
    if (!certAgentId) {
      toast.error("Select an agent first.");
      return;
    }
    const data = await runAgentAction(certAgentId, "diagnose");
    if (data?.diagnosis) {
      setDiagnosis(data.diagnosis);
      setVitals(data.diagnosis);
      setBadge(null);
    }
  };

  const runTreatment = async () => {
    if (!certAgentId) {
      toast.error("Select an agent first.");
      return;
    }
    const treatmentType = treatSel[certAgentId] || "context_defragmentation";
    const data = await runAgentAction(certAgentId, "treat", { treatment_type: treatmentType });
    if (data?.vitals) {
      setVitals(data.vitals);
      setTreatmentCount((count) => count + 1);
    }
  };

  const runCertification = async () => {
    if (!certAgentId) {
      toast.error("Select an agent first.");
      return;
    }
    const data = await runAgentAction(certAgentId, "certify");
    if (data?.badge) setBadge(data.badge);
  };

  const downloadBadge = () => {
    if (!badge) return;
    const blob = new Blob([JSON.stringify(badge, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${badge.agent_name || "agent"}-ACA-badge.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const shareBadge = async () => {
    if (!badge) return;
    const verifyUrl = `${BACKEND_URL}/api/aawab/badge/${badge.badge_id}/verify`;
    try {
      if (navigator.share) await navigator.share({ title: `${badge.agent_name} — AAWAB Certified Agent`, url: verifyUrl });
      else {
        await navigator.clipboard.writeText(verifyUrl);
        toast.success("Verification link copied.");
      }
    } catch {
      toast.error("The verification link could not be shared.");
    }
  };

  const isBusy = (key) => busy === key;

  return (
    <AppShell>
      <div className="max-w-6xl mx-auto px-6 py-10">
        <div className="flex items-start justify-between flex-wrap gap-4">
          <div>
            <p className="text-[10px] font-black uppercase tracking-widest text-copper">AAWAB · Agent Wellness & Certification Bureau</p>
            <h1 className="font-heading text-3xl font-bold text-ink mt-1 flex items-center gap-3">
              <span className="w-10 h-10 rounded-xl bg-ink text-signal flex items-center justify-center"><HeartPulse className="w-5 h-5" /></span>
              Agent Registry
            </h1>
            <p className="text-sm text-ink/65 mt-2 max-w-2xl">
              Register an agent, inspect its recorded vitals, apply a treatment, and certify it from this page. This is the single AAWAB workflow; every result stays visible with the action that produced it.
            </p>
          </div>
          <button onClick={() => setShowRegister((open) => !open)} className="btn-copper px-4 py-2.5 rounded-xl text-sm font-black flex items-center gap-2">
            <Plus className="w-4 h-4" /> Register Agent
          </button>
        </div>

        {showRegister && (
          <section className="mt-6 bg-white border-2 border-copper/30 rounded-2xl p-6 shadow-sm" aria-labelledby="register-heading">
            <h2 id="register-heading" className="font-heading font-bold text-lg text-ink">Register an agent</h2>
            <div className="mt-4 grid sm:grid-cols-3 gap-3">
              <input aria-label="Agent name" value={form.name} onChange={(e) => setForm((current) => ({ ...current, name: e.target.value }))} placeholder="Agent name" className="border border-ink/20 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-copper" />
              <select aria-label="Model provider" value={form.model_provider} onChange={(e) => setForm((current) => ({ ...current, model_provider: e.target.value }))} className="border border-ink/20 rounded-xl px-4 py-2.5 text-sm bg-white focus:outline-none focus:border-copper">
                <option value="groq">Groq</option>
                <option value="cerebras">Cerebras</option>
                <option value="gemini">Gemini</option>
                <option value="openai">OpenAI</option>
                <option value="anthropic">Anthropic</option>
                <option value="custom">Custom / Self-hosted</option>
              </select>
              <button onClick={register} disabled={isBusy("register")} className="btn-copper px-4 py-2.5 rounded-xl text-sm font-black flex items-center justify-center gap-2 disabled:opacity-50">
                {isBusy("register") ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />} Save Agent
              </button>
            </div>
          </section>
        )}

        {loadError && (
          <section className="mt-6 rounded-2xl border-2 border-red-200 bg-red-50 p-5" role="alert">
            <div className="flex items-start gap-3">
              <ShieldAlert className="w-5 h-5 text-red-700 shrink-0 mt-0.5" />
              <div>
                <h2 className="font-heading font-bold text-red-900">AAWAB data is unavailable</h2>
                <p className="text-sm text-red-800 mt-1">{loadError}</p>
                <button onClick={load} className="mt-3 inline-flex items-center gap-2 px-3 py-2 rounded-lg bg-red-700 text-white text-xs font-black"><RefreshCw className="w-3.5 h-3.5" /> Retry</button>
              </div>
            </div>
          </section>
        )}

        <section className="mt-8" aria-labelledby="agents-heading">
          <div className="flex items-center justify-between gap-3 mb-4">
            <h2 id="agents-heading" className="font-heading text-xl font-bold text-ink">Registered agents</h2>
            <button onClick={load} title="Refresh registered agents" className="p-2 rounded-lg text-ink/55 hover:text-copper hover:bg-bone"><RefreshCw className="w-4 h-4" /></button>
          </div>
          {loading ? (
            <div className="flex items-center justify-center py-20 text-ink/55"><Loader2 className="w-5 h-5 animate-spin text-copper" /><span className="ml-2 text-sm">Loading agent data…</span></div>
          ) : !loadError && agents.length === 0 ? (
            <div className="text-center py-16 bg-white border border-ink/10 rounded-2xl">
              <HeartPulse className="w-10 h-10 mx-auto text-ink/30" />
              <p className="font-heading font-bold text-ink mt-4">No agents registered</p>
              <p className="text-sm text-ink/60 mt-1">Register an agent above to begin the wellness and certification workflow.</p>
            </div>
          ) : (
            <div className="grid md:grid-cols-2 gap-5">
              {agents.map((agent) => {
                const status = STATUS_META[agent.status] || STATUS_META.active;
                const treatment = treatSel[agent.agent_id] || "context_defragmentation";
                return (
                  <article key={agent.agent_id} className="bg-white border border-ink/10 rounded-2xl p-6 shadow-sm">
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex items-center gap-3 min-w-0">
                        <div className="w-11 h-11 rounded-2xl shrink-0 flex items-center justify-center" style={{ background: "linear-gradient(135deg,#1B4332,#2D6A4F)" }}><Activity className="w-5 h-5" style={{ color: "#E8A51E" }} /></div>
                        <div className="min-w-0"><h3 className="font-heading font-bold text-ink truncate">{agent.name}</h3><p className="text-xs text-ink/55 truncate">{agent.model_provider} · {agent.agent_id}</p></div>
                      </div>
                      <span className={`text-[10px] font-black uppercase tracking-wider px-2.5 py-1 rounded-full shrink-0 ${status.cls}`}>{status.label}</span>
                    </div>
                    <div className="mt-5 space-y-3.5">
                      <VitalBar label="Vitality (CVS)" value={agent.cognitive_vitality_score} icon={HeartPulse} />
                      <div className="grid grid-cols-3 gap-4"><VitalBar label="Token Vel" value={agent.token_velocity} unit="/m" icon={Zap} /><VitalBar label="Context Load" value={agent.context_load_index} icon={Gauge} /><VitalBar label="Memory Frag" value={agent.memory_fragmentation} icon={Brain} /></div>
                    </div>
                    {agent.prescription && <p className="mt-4 text-xs text-ink/65 bg-bone border border-ink/10 rounded-lg px-3 py-2"><span className="font-bold text-copper">Rx:</span> {agent.prescription_note || agent.prescription}</p>}
                    {agent.badge && <span className="mt-3 inline-flex items-center gap-1.5 text-xs font-black text-emerald-700"><BadgeCheck className="w-4 h-4" /> ACA Certified · {agent.badge.badge_id}</span>}
                    <div className="mt-5 pt-4 border-t border-ink/10 flex flex-wrap items-center gap-2">
                      <button onClick={() => runAgentAction(agent.agent_id, "diagnose")} disabled={isBusy(`diagnose:${agent.agent_id}`)} className="px-3 py-2 rounded-lg text-xs font-black bg-ink text-white disabled:opacity-50 flex items-center gap-1.5">{isBusy(`diagnose:${agent.agent_id}`) ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Stethoscope className="w-3.5 h-3.5" />} Diagnose</button>
                      <select aria-label={`Treatment for ${agent.name}`} value={treatment} onChange={(e) => setTreatSel((current) => ({ ...current, [agent.agent_id]: e.target.value }))} className="border border-ink/20 rounded-lg px-2 py-2 text-xs bg-white focus:outline-none focus:border-copper">{TREATMENTS.map((item) => <option key={item.key} value={item.key}>{item.label}</option>)}</select>
                      <button onClick={() => runAgentAction(agent.agent_id, "treat", { treatment_type: treatment })} disabled={isBusy(`treat:${agent.agent_id}`)} className="px-3 py-2 rounded-lg text-xs font-black bg-copper text-white disabled:opacity-50 flex items-center gap-1.5">{isBusy(`treat:${agent.agent_id}`) ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Syringe className="w-3.5 h-3.5" />} Treat</button>
                      {agent.status !== "certified" && <button onClick={() => runAgentAction(agent.agent_id, "certify")} disabled={isBusy(`certify:${agent.agent_id}`)} className="px-3 py-2 rounded-lg text-xs font-black bg-green-700 text-white disabled:opacity-50 flex items-center gap-1.5">{isBusy(`certify:${agent.agent_id}`) ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Award className="w-3.5 h-3.5" />} Certify</button>}
                    </div>
                    {agent.status === "isolated" && <p className="mt-3 text-xs font-bold text-red-700 flex items-center gap-1.5 bg-red-50 rounded-lg px-3 py-2"><ShieldAlert className="w-4 h-4" /> Circuit-breaker hold. Treat or request an admin override.</p>}
                  </article>
                );
              })}
            </div>
          )}
        </section>

        {actionError && (
          <section className="mt-6 rounded-2xl border-2 border-red-200 bg-red-50 p-5" role="alert">
            <div className="flex items-start gap-3">
              <ShieldAlert className="w-5 h-5 text-red-700 shrink-0 mt-0.5" />
              <div>
                <h2 className="font-heading font-bold text-red-900">AAWAB action was not completed</h2>
                <p className="text-sm text-red-800 mt-1">{actionError}</p>
              </div>
            </div>
          </section>
        )}

        <section className="mt-10 bg-white border-2 border-ink/10 rounded-2xl p-6 shadow-sm" aria-labelledby="certification-heading">
          <div className="flex items-start justify-between gap-4 flex-wrap">
            <div><p className="text-[10px] font-black uppercase tracking-widest text-copper">Single-page workflow</p><h2 id="certification-heading" className="font-heading text-2xl font-bold text-ink mt-1">Diagnose, treat, certify</h2><p className="text-sm text-ink/65 mt-1 max-w-2xl">The certification controls stay here with the registry. No second page is required to complete the task.</p></div>
            <select aria-label="Agent to certify" value={certAgentId} onChange={(e) => { setCertAgentId(e.target.value); setDiagnosis(null); setVitals(null); setBadge(null); setTreatmentCount(0); }} disabled={agents.length === 0} className="border-2 border-ink/15 rounded-xl px-3 py-2.5 text-sm bg-white focus:outline-none focus:border-copper"><option value="">Select agent</option>{agents.map((agent) => <option key={agent.agent_id} value={agent.agent_id}>{agent.name} · CVS {agent.cognitive_vitality_score}</option>)}</select>
          </div>

          <div className="mt-6 grid lg:grid-cols-3 gap-4">
            <div className="border border-ink/10 rounded-xl p-4"><p className="text-xs font-black uppercase tracking-widest text-ink/55">1 · Baseline</p><p className="text-sm text-ink/75 mt-2">Read the agent's current recorded vitals before changing anything.</p><button onClick={runDiagnosis} disabled={!certAgentId || busy} className="mt-4 btn-copper px-4 py-2 rounded-lg text-xs font-black flex items-center gap-2 disabled:opacity-50">{busy === `diagnose:${certAgentId}` ? <Loader2 className="w-4 h-4 animate-spin" /> : <Stethoscope className="w-4 h-4" />} Run Diagnostic</button></div>
            <div className="border border-ink/10 rounded-xl p-4"><p className="text-xs font-black uppercase tracking-widest text-ink/55">2 · Treatment</p><p className="text-sm text-ink/75 mt-2">Choose the protocol yourself, run it, then review the updated CVS.</p><select aria-label="Certification treatment" value={treatSel[certAgentId] || "context_defragmentation"} onChange={(e) => setTreatSel((current) => ({ ...current, [certAgentId]: e.target.value }))} disabled={!certAgentId} className="mt-4 w-full border border-ink/20 rounded-lg px-2 py-2 text-xs bg-white">{TREATMENTS.map((item) => <option key={item.key} value={item.key}>{item.label}</option>)}</select><button onClick={runTreatment} disabled={!certAgentId || busy} className="mt-2 bg-copper text-white px-4 py-2 rounded-lg text-xs font-black flex items-center gap-2 disabled:opacity-50">{busy === `treat:${certAgentId}` ? <Loader2 className="w-4 h-4 animate-spin" /> : <Syringe className="w-4 h-4" />} Apply Treatment</button></div>
            <div className="border border-ink/10 rounded-xl p-4"><p className="text-xs font-black uppercase tracking-widest text-ink/55">3 · Human approval</p><p className="text-sm text-ink/75 mt-2">Certification is a separate human-triggered action and may fail if the recorded CVS is below the threshold.</p><button onClick={runCertification} disabled={!certAgentId || busy} className="mt-4 bg-green-700 text-white px-4 py-2 rounded-lg text-xs font-black flex items-center gap-2 disabled:opacity-50">{busy === `certify:${certAgentId}` ? <Loader2 className="w-4 h-4 animate-spin" /> : <Award className="w-4 h-4" />} Attempt Certification</button></div>
          </div>

          {(diagnosis || vitals) && <div className="mt-6 bg-bone border border-ink/10 rounded-xl p-5"><h3 className="font-heading font-bold text-ink">Recorded result for {selectedAgent?.name || "selected agent"}</h3><div className="mt-4 space-y-3"><ScoreRow label="Cognitive Vitality Score" value={vitals?.cognitive_vitality_score ?? diagnosis?.cvs} /><ScoreRow label="Token Velocity" value={vitals?.token_velocity ?? diagnosis?.token_velocity} unit="/m" /><ScoreRow label="Context Load Index" value={vitals?.context_load_index ?? diagnosis?.context_load_index} /><ScoreRow label="Memory Fragmentation" value={vitals?.memory_fragmentation ?? diagnosis?.memory_fragmentation} /></div><p className="mt-4 text-xs text-ink/65">{diagnosis?.prescription_note || "Review the recorded values before attempting certification."} · {treatmentCount} treatment{treatmentCount === 1 ? "" : "s"} run in this workflow.</p></div>}

          {badge && <div className="mt-6 border-2 border-emerald-200 bg-emerald-50 rounded-xl p-5"><div className="flex items-start gap-3"><BadgeCheck className="w-7 h-7 text-emerald-700 shrink-0" /><div><h3 className="font-heading font-bold text-emerald-900">AAWAB Certified Agent</h3><p className="text-sm text-emerald-800 mt-1">{badge.agent_name} earned the ACA badge with a CVS of {badge.cvs}.</p><p className="text-xs text-emerald-800 mt-2 font-mono">Badge ID: {badge.badge_id}</p><div className="mt-4 flex flex-wrap gap-2"><button onClick={downloadBadge} className="px-3 py-2 rounded-lg bg-emerald-700 text-white text-xs font-black">Download Badge JSON</button><button onClick={shareBadge} className="px-3 py-2 rounded-lg border border-emerald-700 text-emerald-800 text-xs font-black">Share Verify Link</button></div></div></div></div>}
        </section>
      </div>
    </AppShell>
  );
}
