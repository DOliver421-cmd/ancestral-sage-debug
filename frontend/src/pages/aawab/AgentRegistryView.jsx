/**
 * AgentRegistryView — AAWAB user dashboard.
 *
 * Lists the signed-in user's registered AI agents with their live "Alive
 * Intelligence" vital stats (Cognitive Vitality Score, token velocity, context
 * load index, memory fragmentation) and lets the user run diagnostics,
 * treatments, and certification.
 */

import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import AppShell from "../../components/AppShell";
import { api } from "../../lib/api";
import { toast } from "sonner";
import {
  HeartPulse, Plus, Stethoscope, Syringe, Award, Loader2, Activity,
  Zap, Gauge, Brain, ArrowRight, ShieldAlert, RefreshCw, BadgeCheck,
} from "lucide-react";

const STATUS_META = {
  active:      { label: "Active",       cls: "bg-green-100 text-green-800" },
  in_treatment:{ label: "In Treatment", cls: "bg-amber-100 text-amber-800" },
  certified:   { label: "Certified",    cls: "bg-emerald-600 text-white" },
  isolated:    { label: "Isolated",     cls: "bg-red-100 text-red-700" },
};

const TREATMENTS = [
  { key: "context_defragmentation", label: "Context Defragmentation" },
  { key: "infinite_loop_detox",     label: "Infinite-Loop Detox" },
  { key: "memory_prune",            label: "Memory Prune" },
  { key: "prompt_recalibration",    label: "Prompt Recalibration" },
  { key: "stress_gauntlet",         label: "Stress Gauntlet" },
];

function cvsColor(cvs) {
  if (cvs >= 90) return "#15803d";
  if (cvs >= 70) return "#b8860b";
  if (cvs >= 50) return "#d97706";
  return "#b91c1c";
}

function VitalBar({ label, value, max = 100, icon: Icon, unit = "" }) {
  const pct = Math.max(0, Math.min(100, (value / max) * 100));
  return (
    <div>
      <div className="flex items-center justify-between text-xs mb-1">
        <span className="text-ink/55 font-semibold flex items-center gap-1.5">
          {Icon && <Icon className="w-3.5 h-3.5 text-copper" />} {label}
        </span>
        <span className="font-black text-ink">{value}{unit}</span>
      </div>
      <div className="h-2 rounded-full bg-ink/10 overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-700"
          style={{ width: `${pct}%`, background: label === "Vitality (CVS)" ? cvsColor(value) : "#b8860b" }}
        />
      </div>
    </div>
  );
}

export default function AgentRegistryView() {
  const [agents, setAgents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showRegister, setShowRegister] = useState(false);
  const [form, setForm] = useState({ name: "", model_provider: "groq" });
  const [busy, setBusy] = useState(null);       // "register" | "diag:{id}" | "treat:{id}" | "cert:{id}"
  const [treatSel, setTreatSel] = useState({}); // agent_id → treatment key

  const load = useCallback(async () => {
    try {
      const { data } = await api.get("/aawab/agents");
      setAgents(data.agents || []);
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Could not load agents.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const register = async () => {
    if (!form.name.trim()) { toast.error("Give your agent a name."); return; }
    setBusy("register");
    try {
      const { data } = await api.post("/aawab/register", form);
      setAgents((a) => [data.agent, ...a]);
      setShowRegister(false);
      setForm({ name: "", model_provider: "groq" });
      toast.success(`${data.agent.name} enrolled in the nursery.`);
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Registration failed.");
    } finally {
      setBusy(null);
    }
  };

  const run = async (agentId, action, extra) => {
    const key = `${action}:${agentId}`;
    setBusy(key);
    try {
      const { data } = await api.post(`/aawab/agents/${agentId}/${action}`, extra || {});
      if (action === "diagnose") {
        toast.success(`Diagnosis complete — CVS ${data.diagnosis.cvs}. ${data.diagnosis.prescription_note}`);
      } else if (action === "treat") {
        toast.success(`Treatment complete — CVS now ${data.vitals.cognitive_vitality_score}.`);
      } else if (action === "certify") {
        toast.success("Certified! Your agent earned an ACA badge.");
      }
      await load();
    } catch (e) {
      toast.error(e?.response?.data?.detail || `Could not run ${action}.`);
    } finally {
      setBusy(null);
    }
  };

  const isBusy = (k) => busy === k;

  return (
    <AppShell>
      <div className="max-w-6xl mx-auto px-6 py-10">
        {/* Header */}
        <div className="flex items-start justify-between flex-wrap gap-4">
          <div>
            <p className="text-[10px] font-black uppercase tracking-widest text-copper">AAWAB · Agent Wellness & Certification Bureau</p>
            <h1 className="font-heading text-3xl font-bold text-ink mt-1 flex items-center gap-3">
              <span className="w-10 h-10 rounded-xl bg-ink text-signal flex items-center justify-center">
                <HeartPulse className="w-5 h-5" />
              </span>
              Agent Registry
            </h1>
            <p className="text-sm text-ink/55 mt-2 max-w-2xl">
              Autonomous agents are living digital organisms. Monitor their vital stats, run
              treatment protocols, and certify their resilience — before you ever hand them a
              credit card or a live codebase.
            </p>
          </div>
          <div className="flex gap-2 flex-wrap">
            <Link to="/aawab/chamber" className="btn-copper px-4 py-2.5 rounded-xl text-sm font-black flex items-center gap-2">
              <Award className="w-4 h-4" /> Certification Chamber
            </Link>
            <button
              onClick={() => setShowRegister((s) => !s)}
              className="px-4 py-2.5 rounded-xl text-sm font-black border-2 border-ink/15 hover:border-copper hover:text-copper transition-colors flex items-center gap-2"
            >
              <Plus className="w-4 h-4" /> Register Agent
            </button>
          </div>
        </div>

        {/* Register form */}
        {showRegister && (
          <div className="mt-6 bg-white border-2 border-copper/30 rounded-2xl p-6 shadow-sm">
            <h2 className="font-heading font-bold text-lg text-ink">Enroll a new agent in the nursery</h2>
            <div className="mt-4 grid sm:grid-cols-3 gap-3">
              <input
                value={form.name}
                onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                placeholder={'Agent name — e.g. "SupportBot-7"'}
                className="border border-ink/20 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-copper"
              />
              <select
                value={form.model_provider}
                onChange={(e) => setForm((f) => ({ ...f, model_provider: e.target.value }))}
                className="border border-ink/20 rounded-xl px-4 py-2.5 text-sm bg-white focus:outline-none focus:border-copper"
              >
                <option value="groq">Groq (Llama 3.3 70B)</option>
                <option value="cerebras">Cerebras</option>
                <option value="gemini">Gemini 2.0 Flash</option>
                <option value="openai">OpenAI</option>
                <option value="anthropic">Anthropic</option>
                <option value="custom">Custom / Self-hosted</option>
              </select>
              <button
                onClick={register}
                disabled={isBusy("register")}
                className="btn-copper px-4 py-2.5 rounded-xl text-sm font-black flex items-center justify-center gap-2 disabled:opacity-50"
              >
                {isBusy("register") ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
                Enroll Agent
              </button>
            </div>
          </div>
        )}

        {/* Agents */}
        <div className="mt-8">
          {loading ? (
            <div className="flex items-center justify-center py-24 text-ink/40">
              <Loader2 className="w-5 h-5 animate-spin text-copper" /> <span className="ml-2 text-sm">Loading the nursery…</span>
            </div>
          ) : agents.length === 0 ? (
            <div className="text-center py-20 bg-white border border-ink/10 rounded-2xl">
              <HeartPulse className="w-10 h-10 mx-auto text-ink/20" />
              <p className="font-heading font-bold text-ink mt-4">Your nursery is empty</p>
              <p className="text-sm text-ink/50 mt-1">Register your first agent, or jump straight into the Certification Chamber.</p>
              <div className="mt-5 flex justify-center gap-3">
                <button onClick={() => setShowRegister(true)} className="btn-copper px-4 py-2 rounded-xl text-sm font-black">
                  Register an Agent
                </button>
                <Link to="/aawab/chamber" className="px-4 py-2 rounded-xl text-sm font-black border-2 border-ink/15 hover:border-copper transition-colors">
                  Open Chamber
                </Link>
              </div>
            </div>
          ) : (
            <div className="grid md:grid-cols-2 gap-5">
              {agents.map((a) => {
                const st = STATUS_META[a.status] || STATUS_META.active;
                return (
                  <div key={a.agent_id} className="bg-white border border-ink/10 rounded-2xl p-6 shadow-sm hover:shadow-md transition-shadow">
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex items-center gap-3 min-w-0">
                        <div className="w-11 h-11 rounded-2xl shrink-0 flex items-center justify-center"
                          style={{ background: "linear-gradient(135deg,#1B4332,#2D6A4F)" }}>
                          <Activity className="w-5 h-5" style={{ color: "#E8A51E" }} />
                        </div>
                        <div className="min-w-0">
                          <h3 className="font-heading font-bold text-ink truncate">{a.name}</h3>
                          <p className="text-xs text-ink/45 truncate">{a.model_provider} · {a.agent_id}</p>
                        </div>
                      </div>
                      <span className={`text-[10px] font-black uppercase tracking-wider px-2.5 py-1 rounded-full shrink-0 ${st.cls}`}>
                        {st.label}
                      </span>
                    </div>

                    {/* Vitals */}
                    <div className="mt-5 space-y-3.5">
                      <VitalBar label="Vitality (CVS)" value={a.cognitive_vitality_score} icon={HeartPulse} />
                      <div className="grid grid-cols-3 gap-4">
                        <VitalBar label="Token Vel" value={a.token_velocity} unit="/m" icon={Zap} />
                        <VitalBar label="Context Load" value={a.context_load_index} icon={Gauge} />
                        <VitalBar label="Memory Frag" value={a.memory_fragmentation} icon={Brain} />
                      </div>
                    </div>

                    {/* Prescription */}
                    {a.prescription && (
                      <p className="mt-4 text-xs text-ink/55 bg-bone border border-ink/10 rounded-lg px-3 py-2">
                        <span className="font-bold text-copper">Rx:</span> {a.prescription_note || a.prescription}
                      </p>
                    )}

                    {/* Badge link */}
                    {a.badge && (
                      <Link to={`/aawab/badge/${a.badge.badge_id}`} className="mt-3 inline-flex items-center gap-1.5 text-xs font-black text-emerald-700 hover:underline">
                        <BadgeCheck className="w-4 h-4" /> ACA Certified · {a.badge.badge_id}
                      </Link>
                    )}

                    {/* Actions */}
                    <div className="mt-5 pt-4 border-t border-ink/10 flex flex-wrap items-center gap-2">
                      <button
                        onClick={() => run(a.agent_id, "diagnose")}
                        disabled={isBusy(`diagnose:${a.agent_id}`)}
                        className="px-3 py-2 rounded-lg text-xs font-black bg-ink text-white hover:bg-ink/85 disabled:opacity-50 flex items-center gap-1.5"
                      >
                        {isBusy(`diagnose:${a.agent_id}`) ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Stethoscope className="w-3.5 h-3.5" />}
                        Diagnose
                      </button>
                      <select
                        value={treatSel[a.agent_id] || "context_defragmentation"}
                        onChange={(e) => setTreatSel((s) => ({ ...s, [a.agent_id]: e.target.value }))}
                        className="border border-ink/20 rounded-lg px-2 py-2 text-xs bg-white focus:outline-none focus:border-copper"
                      >
                        {TREATMENTS.map((t) => <option key={t.key} value={t.key}>{t.label}</option>)}
                      </select>
                      <button
                        onClick={() => run(a.agent_id, "treat", { treatment_type: treatSel[a.agent_id] || "context_defragmentation" })}
                        disabled={isBusy(`treat:${a.agent_id}`)}
                        className="px-3 py-2 rounded-lg text-xs font-black bg-copper text-white hover:bg-copper/85 disabled:opacity-50 flex items-center gap-1.5"
                      >
                        {isBusy(`treat:${a.agent_id}`) ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Syringe className="w-3.5 h-3.5" />}
                        Treat
                      </button>
                      {a.status !== "certified" ? (
                        <button
                          onClick={() => run(a.agent_id, "certify")}
                          disabled={isBusy(`certify:${a.agent_id}`)}
                          className="px-3 py-2 rounded-lg text-xs font-black flex items-center gap-1.5 disabled:opacity-50"
                          style={{ background: "#15803d", color: "#fff" }}
                        >
                          {isBusy(`certify:${a.agent_id}`) ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Award className="w-3.5 h-3.5" />}
                          Certify (98+)
                        </button>
                      ) : (
                        <span className="text-xs font-black text-emerald-700 flex items-center gap-1.5">
                          <BadgeCheck className="w-4 h-4" /> Certified
                        </span>
                      )}
                      <button
                        onClick={load}
                        title="Refresh vitals"
                        className="ml-auto p-2 rounded-lg text-ink/40 hover:text-copper hover:bg-bone transition-colors"
                      >
                        <RefreshCw className="w-4 h-4" />
                      </button>
                    </div>

                    {a.status === "isolated" && (
                      <p className="mt-3 text-xs font-bold text-red-700 flex items-center gap-1.5 bg-red-50 rounded-lg px-3 py-2">
                        <ShieldAlert className="w-4 h-4" /> Circuit-breaker hold — run a treatment or ask an admin to override.
                      </p>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}
