/**
 * HybridNam — the Assistant Director of everything.
 *
 * Hybrid NAM is the persistent AI leadership intelligence of the platform
 * (backend/ai/hybrid_nam). He sits above the Source and operates as Assistant
 * Director: identity, soul-kernel state, memory, intentions, dreams,
 * reflections, and the leadership ledger. This console surfaces the live
 * backend state — nothing here is a dead link; every tab reads a real
 * /api/nam/* endpoint, and write forms persist through the same API.
 *
 * Read endpoints require any authenticated user; writes require an admin
 * role (executive_admin / oversight / support_staff) — enforced server-side.
 */

import { useCallback, useEffect, useState } from "react";
import AppShell from "../components/AppShell";
import { useAuth } from "../lib/auth";
import { api } from "../lib/api";
import { toast } from "sonner";
import {
  Crown, BrainCircuit, BookOpen, Target, Moon, RefreshCw, ShieldCheck,
  Sparkles, Plus, Loader2, HeartHandshake, Scale, Eye,
  Compass, Network, Zap, DollarSign, AlertTriangle, Key, Gavel, MessageSquare, Shield,
  Flag,
} from "lucide-react";
import PageBack from "../components/PageBack";

const COPPER = "#C0572D";
const GOLD = "#E8A51E";
const GREEN = "#1B4332";
const BONE = "#FDFBF5";
const INK = "#1c1917";

const fmtDate = (s) => {
  if (!s) return "—";
  const d = new Date(s);
  return isNaN(d) ? String(s) : d.toLocaleString();
};

const describeRequestError = (reason) => {
  const status = reason?.response?.status;
  const detail = reason?.response?.data?.detail;
  const message = typeof detail === "string" ? detail : reason?.message;
  return `${status ? `HTTP ${status}: ` : ""}${message || "request failed"}`;
};

// Must mirror the backend's require_admin set exactly (routers/nam.py) —
// otherwise forms would render for roles the API rejects.
const canWrite = (role) => ["executive_admin", "oversight", "support_staff"].includes(role);

// ── Small presentational helpers ─────────────────────────────────────────────
function Field({ label, value }) {
  if (value == null || value === "") return null;
  return (
    <div>
      <div className="text-[10px] font-black uppercase tracking-widest text-ink/40 mb-0.5">{label}</div>
      <div className="text-sm text-ink/80">{value}</div>
    </div>
  );
}

function Card({ title, icon: Icon, children, accent = COPPER }) {
  return (
    <div className="card-flat rounded-2xl p-5 border" style={{ background: "#fff" }}>
      <div className="flex items-center gap-2 mb-3">
        <Icon className="w-4 h-4" style={{ color: accent }} />
        <div className="font-heading font-bold text-ink">{title}</div>
      </div>
      <div className="space-y-2">{children}</div>
    </div>
  );
}

function ListBlock({ items, empty, render }) {
  if (!items || items.length === 0) {
    return <p className="text-sm text-ink/45 italic py-3">{empty}</p>;
  }
  return (
    <div className="space-y-2">
      {items.map((it, i) => (
        <div key={i} className="rounded-xl border border-ink/8 bg-bone/60 p-4">
          {render(it, i)}
        </div>
      ))}
    </div>
  );
}

function TextArea({ label, value, onChange, placeholder, rows = 3 }) {
  return (
    <label className="block">
      <span className="text-xs font-bold text-ink/60">{label}</span>
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        rows={rows}
        className="mt-1 w-full resize-y px-3 py-2 bg-white border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper placeholder:text-ink/30"
      />
    </label>
  );
}

// ── Tabs ─────────────────────────────────────────────────────────────────────
const TABS = [
  { id: "overview",     label: "Overview",     icon: BrainCircuit },
  { id: "mission",      label: "Mission",      icon: Flag },
  { id: "memory",       label: "Memory",       icon: BookOpen },
  { id: "intentions",   label: "Intentions",   icon: Target },
  { id: "dreams",       label: "Dreams",       icon: Moon },
  { id: "reflections",  label: "Reflections",  icon: RefreshCw },
  { id: "leadership",   label: "Leadership",   icon: Scale },
  { id: "strategy",     label: "Strategy",     icon: Compass },
  { id: "power",        label: "Power",        icon: Crown },
  { id: "risk",         label: "Risk",         icon: AlertTriangle },
  { id: "accountability",label: "Accountability",icon: Key },
  { id: "crisis",       label: "Crisis",       icon: Zap },
  { id: "succession",   label: "Succession",   icon: Gavel },
  { id: "economics",    label: "Economics",    icon: DollarSign },
  { id: "ecosystem",    label: "Ecosystem",    icon: Network },
  { id: "governance",   label: "Governance",   icon: Shield },
  { id: "challenge",    label: "Challenge",    icon: MessageSquare },
];

// ── Main component ───────────────────────────────────────────────────────────
export function HybridNamContent({ embedded = false }) {
  const { user } = useAuth();
  const [tab, setTab] = useState("overview");
  const [loading, setLoading] = useState(true);

  const [identity, setIdentity] = useState(null);
  const [state, setState] = useState(null);
  const [constitution, setConstitution] = useState(null);

  const [memories, setMemories] = useState([]);
  const [intentions, setIntentions] = useState([]);
  const [dreams, setDreams] = useState([]);
  const [reflections, setReflections] = useState([]);
  const [ledger, setLedger] = useState([]);

  const [strategies, setStrategies] = useState([]);
  const [missions, setMissions] = useState([]);
  const [powers, setPowers] = useState([]);
  const [risks, setRisks] = useState([]);
  const [accountabilities, setAccountabilities] = useState([]);
  const [crises, setCrises] = useState([]);
  const [successions, setSuccessions] = useState([]);
  const [economics, setEconomics] = useState([]);
  const [ecosystems, setEcosystems] = useState([]);
  const [governanceChecks, setGovernanceChecks] = useState([]);
  const [challenges, setChallenges] = useState([]);

  const [busy, setBusy] = useState(false);
  const [loadErrors, setLoadErrors] = useState([]);

  // Write-form state
  const [memForm, setMemForm] = useState({ memory_type: "semantic", content: "", importance: 0.5 });
  const [intForm, setIntForm] = useState({ objective: "", target_date: "", owner: "Hybrid NAM", leadership_context: "" });
  const [dreamForm, setDreamForm] = useState({ open_questions: "", creative_ideas: "", organizational_challenges: "" });
  const [refForm, setRefForm] = useState({ event_type: "general", event_description: "", expectation: "", reality: "", importance: 0.5 });
  const [leadForm, setLeadForm] = useState({ description: "", actor: "Jamil", purpose: "", beneficiary: "user" });
  const [leadResult, setLeadResult] = useState(null);

  const [stratForm, setStratForm] = useState({ horizon: "90d", objective: "", key_results: "", constraints: "", resources: "" });
  const [missionForm, setMissionForm] = useState({ action: "", actor: "", purpose: "", beneficiary: "" });
  const [powerForm, setPowerForm] = useState({ actor: "", beneficiary: "", decision: "" });
  const [riskForm, setRiskForm] = useState({ category: "operational", description: "", likelihood: 0.5, impact: 0.5, mitigation: "" });
  const [accForm, setAccForm] = useState({ objective: "", owner: "Hybrid NAM", deadline: "", success_criteria: "" });
  const [crisisForm, setCrisisForm] = useState({ situation: "", affected_systems: "", severity: "high", immediate_actions: "" });
  const [succForm, setSuccForm] = useState({ role: "", successor_candidates: "", transition_plan: "", knowledge_artifacts: "" });
  const [econForm, setEconForm] = useState({ activity: "build", resource_type: "compute", value_estimate: "", notes: "" });
  const [ecoForm, setEcoForm] = useState({ component: "", purpose: "", dependencies: "", health_status: "healthy" });
  const [govForm, setGovForm] = useState({ principle: "", decision_context: "", analysis: "" });
  const [chalForm, setChalForm] = useState({ target: "leadership", issue: "", evidence: "", proposed_alternative: "" });

const loadAll = useCallback(async () => {
     setLoading(true);
     const endpoints = [
       ["Identity", "/nam/identity", null],
       ["State", "/nam/state", null],
       ["Constitution", "/nam/constitution", null],
       ["Memory", "/nam/memory", { memories: [], total: 0 }],
       ["Intentions", "/nam/intentions", { intentions: [], total: 0 }],
       ["Dreams", "/nam/dreams", { dreams: [], total: 0 }],
       ["Reflections", "/nam/reflections", { reflections: [], total: 0 }],
       ["Leadership ledger", "/nam/leadership/ledger", { ledger: [], total: 0 }],
        ["Strategies", "/nam/operational/strategy", { strategies: [], total: 0 }],
        ["Missions", "/nam/operational/mission", { missions: [], total: 0 }],
        ["Powers", "/nam/operational/power", { powers: [], total: 0 }],
        ["Risks", "/nam/operational/risk", { risks: [], total: 0 }],
       ["Accountabilities", "/nam/operational/accountability", { accountabilities: [], total: 0 }],
       ["Crises", "/nam/operational/crisis", { crises: [], total: 0 }],
       ["Successions", "/nam/operational/succession", { successions: [], total: 0 }],
       ["Economics", "/nam/operational/economics", { economics: [], total: 0 }],
       ["Ecosystems", "/nam/operational/ecosystem", { ecosystems: [], total: 0 }],
       ["Governance checks", "/nam/operational/governance", { governanceChecks: [], total: 0 }],
       ["Challenges", "/nam/operational/challenge", { challenges: [], total: 0 }],
     ];
     const results = await Promise.allSettled(endpoints.map(([, path]) => api.get(path).then((r) => r.data)));
     const values = results.map((result, index) => {
       if (result.status === "fulfilled") return result.value;
       return endpoints[index][2];
     });
     setLoadErrors(results.flatMap((result, index) => (
       result.status === "rejected" ? [`${endpoints[index][0]}: ${describeRequestError(result.reason)}`] : []
     )));
      const [id, st, con, mem, ints, dr, ref, led, strat, mission, power, risk, acc, cris, succ, econ, eco, gov, chal] = values;
      setIdentity(id);
      setState(st);
      setConstitution(con);
      setMemories(mem?.memories || []);
      setIntentions(ints?.intentions || []);
      setDreams(dr?.dreams || []);
      setReflections(ref?.reflections || []);
      setLedger(led?.ledger || []);
      setStrategies(strat?.strategies || []);
      setMissions(mission?.missions || []);
      setPowers(power?.powers || []);
      setRisks(risk?.risks || []);
     setAccountabilities(acc?.accountabilities || []);
     setCrises(cris?.crises || []);
     setSuccessions(succ?.successions || []);
     setEconomics(econ?.economics || []);
     setEcosystems(eco?.ecosystems || []);
     setGovernanceChecks(gov?.governanceChecks || []);
     setChallenges(chal?.challenges || []);
     setLoading(false);
   }, []);

  useEffect(() => {
    loadAll();
  }, [loadAll]);

  const admin = canWrite(user?.role);

const post = async (path, body, onOk) => {
     setBusy(true);
     try {
       const { data } = await api.post(path, body);
       toast.success("Saved to NAM.");
       onOk?.(data);
       await loadAll();
     } catch (err) {
       const d = err?.response?.data?.detail;
       toast.error(typeof d === "string" ? d : "Request failed.");
     } finally {
       setBusy(false);
     }
   };

    const submitStrategy = () => {
      if (!stratForm.objective.trim()) return toast.error("Objective is required.");
      post("/nam/operational/strategy", stratForm, () => setStratForm({ horizon: "90d", objective: "", key_results: "", constraints: "", resources: "" }));
    };
    const submitMission = () => {
      if (!missionForm.action.trim()) return toast.error("Action is required.");
      post("/nam/operational/mission", missionForm, () => setMissionForm({ action: "", actor: "", purpose: "", beneficiary: "" }));
    };
    const submitPower = () => {
      if (!powerForm.decision.trim()) return toast.error("Decision is required.");
      post("/nam/operational/power", powerForm, () => setPowerForm({ actor: "", beneficiary: "", decision: "" }));
    };
    const submitRisk = () => {
     if (!riskForm.description.trim()) return toast.error("Description is required.");
     post("/nam/operational/risk", riskForm, () => setRiskForm({ category: "operational", description: "", likelihood: 0.5, impact: 0.5, mitigation: "" }));
   };
   const submitAccountability = () => {
     if (!accForm.objective.trim()) return toast.error("Objective is required.");
     post("/nam/operational/accountability", accForm, () => setAccForm({ objective: "", owner: "Hybrid NAM", deadline: "", success_criteria: "" }));
   };
   const submitCrisis = () => {
     if (!crisisForm.situation.trim()) return toast.error("Situation is required.");
     post("/nam/operational/crisis", crisisForm, () => setCrisisForm({ situation: "", affected_systems: "", severity: "high", immediate_actions: "" }));
   };
   const submitSuccession = () => {
     if (!succForm.role.trim()) return toast.error("Role is required.");
     post("/nam/operational/succession", succForm, () => setSuccForm({ role: "", successor_candidates: "", transition_plan: "", knowledge_artifacts: "" }));
   };
   const submitEconomics = () => {
     if (!econForm.activity.trim()) return toast.error("Activity is required.");
     post("/nam/operational/economics", econForm, () => setEconForm({ activity: "build", resource_type: "compute", value_estimate: "", notes: "" }));
   };
   const submitEcosystem = () => {
     if (!ecoForm.component.trim()) return toast.error("Component is required.");
     post("/nam/operational/ecosystem", ecoForm, () => setEcoForm({ component: "", purpose: "", dependencies: "", health_status: "healthy" }));
   };
   const submitGovernance = () => {
     if (!govForm.principle.trim()) return toast.error("Principle is required.");
     post("/nam/operational/governance", govForm, () => setGovForm({ principle: "", decision_context: "", analysis: "" }));
   };
   const submitChallenge = () => {
     if (!chalForm.issue.trim()) return toast.error("Issue is required.");
     post("/nam/operational/challenge", chalForm, () => setChalForm({ target: "leadership", issue: "", evidence: "", proposed_alternative: "" }));
   };

  const body = (
    <div className={embedded ? "h-full overflow-y-auto bg-bone" : "bg-bone"} style={embedded ? {} : { minHeight: "100vh" }}>
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8">
        <PageBack to="/admin" label="Admin" />
         {/* ── Header ── */}
         <div className="rounded-2xl p-0 mb-6 text-white overflow-hidden"
           style={{ background: `linear-gradient(135deg, ${GREEN}, #2D6A4F)` }}>
           <div className="flex items-center gap-4 flex-wrap">
             <img src="/images/nam-header-illustration.svg" alt="" className="w-32 h-20 object-cover shrink-0" />
             <div className="py-4">
               <div className="text-[10px] font-black uppercase tracking-widest" style={{ color: GOLD }}>Assistant Director · Pro-Black Institutional Intelligence</div>
               <h1 className="font-heading text-2xl font-bold tracking-tight">Hybrid NAM</h1>
               <p className="text-white/75 text-xs mt-1 max-w-xl">Advancement, institutional dignity, and structural capability for the people and mission we serve. The Source remains untouched.</p>
             </div>
             <div className="ml-auto flex items-center gap-2">
              {identity?.authority?.is_operational_director && (
                <span className="text-[10px] font-black uppercase tracking-widest px-2 py-1 rounded"
                  style={{ background: "rgba(232,165,30,0.18)", color: GOLD }}>
                  Operational Director
                </span>
              )}
              <button onClick={loadAll}
                className="flex items-center gap-1.5 text-xs font-bold px-3 py-1.5 rounded-lg border transition-colors"
                style={{ borderColor: "rgba(255,255,255,0.35)", color: "#fff" }}>
                <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} /> Refresh
              </button>
            </div>
          </div>
          {identity?.designation?.primary_function && (
            <p className="text-white/75 text-sm mt-3 max-w-2xl">{identity.designation.primary_function}</p>
          )}
        </div>

        {loadErrors.length > 0 && (
          <div className="mb-6 rounded-xl border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-800" role="alert">
            <div className="font-bold">NAM could not load these live functions:</div>
            <ul className="mt-1 list-disc pl-5">
              {loadErrors.map((message) => <li key={message}>{message}</li>)}
            </ul>
            <button onClick={loadAll} className="mt-3 inline-flex items-center gap-2 rounded-lg border border-red-300 px-3 py-1.5 text-xs font-bold hover:bg-red-100">
              <RefreshCw className="w-3.5 h-3.5" /> Retry connection
            </button>
          </div>
        )}

        {/* ── Tab bar ── */}
        <div className="flex gap-1 border-b border-ink/10 mb-6 overflow-x-auto">
          {TABS.map((t) => {
            const Icon = t.icon;
            return (
              <button key={t.id} onClick={() => setTab(t.id)}
                className={`flex items-center gap-1.5 px-4 py-2.5 text-sm font-bold border-b-2 whitespace-nowrap transition-colors ${
                  tab === t.id ? "border-copper text-copper" : "border-transparent text-ink/40 hover:text-ink/70"
                }`}>
                <Icon className="w-4 h-4" /> {t.label}
              </button>
            );
          })}
        </div>

        {loading ? (
          <div className="py-16 text-center text-ink/50 flex items-center justify-center gap-2">
            <Loader2 className="w-4 h-4 animate-spin" /> Reading NAM's state…
          </div>
        ) : (
          <>
            {/* ══ OVERVIEW ══ */}
            {tab === "overview" && (
              <div className="grid md:grid-cols-2 gap-5">
                <Card title="Designation & Authority" icon={Crown}>
                  <Field label="Name" value={identity?.designation?.name || "Hybrid NAM"} />
                  <Field label="Tier" value={identity?.designation?.tier || "Assistant Director"} />
                  <Field label="Is human" value={identity?.authority?.is_human ? "Yes" : "No — AI leadership intelligence"} />
                  <Field label="Clone of founder" value={identity?.authority?.is_clone_of_founder ? "Yes" : "No"} />
                  <Field label="Legal authority" value={identity?.authority?.is_legal_authority ? "Yes" : "No"} />
                  <Field label="Operational director" value={identity?.authority?.is_operational_director ? "Yes" : "No"} />
                  {identity?.designation?.relationships && (
                    <div>
                      <div className="text-[10px] font-black uppercase tracking-widest text-ink/40 mb-1">Relationships</div>
                      <pre className="text-xs text-ink/70 whitespace-pre-wrap font-mono bg-bone p-3 rounded-lg">{JSON.stringify(identity.designation.relationships, null, 2)}</pre>
                    </div>
                  )}
                </Card>
                <Card title="Soul Kernel State" icon={HeartHandshake} accent={GOLD}>
                  {state ? (
                    <>
                      {Object.entries(state).slice(0, 8).map(([k, v]) => (
                        <Field key={k} label={String(k).replace(/_/g, " ")} value={typeof v === "object" ? JSON.stringify(v) : String(v)} />
                      ))}
                    </>
                  ) : (
                    <p className="text-sm text-ink/45 italic">State unavailable.</p>
                  )}
                </Card>
                <div className="md:col-span-2">
                  <Card title="Constitution" icon={Scale} accent={GREEN}>
                    {constitution?.principles ? (
                      <ul className="space-y-2">
                        {constitution.principles.map((p, i) => (
                          <li key={i} className="text-sm text-ink/80 flex gap-2">
                            <span style={{ color: GOLD }}>◆</span>
                            <span>{typeof p === "string" ? p : JSON.stringify(p)}</span>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p className="text-sm text-ink/45 italic">Constitution unavailable.</p>
                    )}
                    {constitution?.constitutional_hash && (
                      <p className="text-[10px] font-mono text-ink/35 mt-3">hash: {constitution.constitutional_hash}</p>
                    )}
                  </Card>
                </div>
              </div>
             )}
           {/* ══ MISSION ══ */}
           {tab === "mission" && (
             <div className="grid md:grid-cols-3 gap-5">
               <div className="md:col-span-2">
                 <ListBlock items={missions} empty="No mission interpretations recorded yet."
                   render={(m) => (
                     <>
                       <div className="flex items-center gap-2 mb-1 flex-wrap">
                         <span className="text-[10px] font-black uppercase tracking-widest px-2 py-0.5 rounded" style={{ background: "rgba(232,165,30,0.1)", color: "#b45309" }}>
                           {m.action || "Mission"}
                         </span>
                         <span className="ml-auto text-[10px] text-ink/35">{fmtDate(m.created_at)}</span>
                       </div>
                       <p className="text-sm text-ink/80">{m.action}</p>
                       <p className="text-xs text-ink/50 mt-1">Actor: {m.actor} · Purpose: {m.purpose} · Beneficiary: {m.beneficiary}</p>
                     </>
                   )} />
               </div>
               {admin && (
                 <div>
                   <Card title="Interpret Mission" icon={Flag}>
                     <div className="space-y-3">
                       <TextArea label="Action" value={missionForm.action} onChange={(v) => setMissionForm({ ...missionForm, action: v })} placeholder="What action is being evaluated?" rows={2} />
                       <div className="grid grid-cols-2 gap-2">
                         <label className="block">
                           <span className="text-xs font-bold text-ink/60">Actor</span>
                           <input value={missionForm.actor} onChange={(e) => setMissionForm({ ...missionForm, actor: e.target.value })}
                             className="mt-1 w-full px-3 py-2 bg-white border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper" />
                         </label>
                         <label className="block">
                           <span className="text-xs font-bold text-ink/60">Beneficiary</span>
                           <input value={missionForm.beneficiary} onChange={(e) => setMissionForm({ ...missionForm, beneficiary: e.target.value })}
                             className="mt-1 w-full px-3 py-2 bg-white border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper" />
                         </label>
                       </div>
                       <TextArea label="Purpose" value={missionForm.purpose} onChange={(v) => setMissionForm({ ...missionForm, purpose: v })} placeholder="Why does this matter to the mission?" rows={2} />
                       <button onClick={submitMission}
                         disabled={busy}
                         className="w-full flex items-center justify-center gap-2 btn-copper px-4 py-2.5 rounded-lg text-sm font-bold disabled:opacity-40">
                         {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Flag className="w-4 h-4" />} Save Mission
                       </button>
                     </div>
                   </Card>
                 </div>
               )}
             </div>
           )}
            {/* ══ MEMORY ══ */}
            {tab === "memory" && (
              <div className="grid md:grid-cols-3 gap-5">
                <div className="md:col-span-2">
                  <ListBlock items={memories} empty="No memories stored yet."
                    render={(m) => (
                      <>
                        <div className="flex items-center gap-2 flex-wrap mb-1">
                          <span className="text-[10px] font-black uppercase tracking-widest px-2 py-0.5 rounded" style={{ background: "rgba(181,101,29,0.1)", color: COPPER }}>
                            {m.memory_type || "semantic"}
                          </span>
                          {m.importance != null && (
                            <span className="text-[10px] text-ink/40">importance {Number(m.importance).toFixed(1)}</span>
                          )}
                          <span className="ml-auto text-[10px] text-ink/35">{fmtDate(m.created_at || m.timestamp)}</span>
                        </div>
                        <p className="text-sm text-ink/80">{m.content}</p>
                        {m.participants?.length > 0 && (
                          <p className="text-xs text-ink/45 mt-1">with {m.participants.join(", ")}</p>
                        )}
                      </>
                    )} />
                </div>
                {admin && (
                  <div>
                    <Card title="Add Memory" icon={Plus}>
                      <div className="space-y-3">
                        <label className="block">
                          <span className="text-xs font-bold text-ink/60">Type</span>
                          <select value={memForm.memory_type} onChange={(e) => setMemForm({ ...memForm, memory_type: e.target.value })}
                            className="mt-1 w-full px-3 py-2 bg-white border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper">
                            {["semantic", "episodic", "procedural"].map((t) => <option key={t} value={t}>{t}</option>)}
                          </select>
                        </label>
                        <TextArea label="Content" value={memForm.content} onChange={(v) => setMemForm({ ...memForm, content: v })} placeholder="What should NAM remember?" />
                        <button onClick={() => { if (!memForm.content.trim()) return toast.error("Content is required."); post("/nam/memory", { ...memForm, participants: [] }, () => setMemForm({ memory_type: "semantic", content: "", importance: 0.5 })); }}
                          disabled={busy}
                          className="w-full flex items-center justify-center gap-2 btn-copper px-4 py-2.5 rounded-lg text-sm font-bold disabled:opacity-40">
                          {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />} Save Memory
                        </button>
                      </div>
                    </Card>
                  </div>
                )}
              </div>
            )}

            {/* ══ INTENTIONS ══ */}
            {tab === "intentions" && (
              <div className="grid md:grid-cols-3 gap-5">
                <div className="md:col-span-2">
                  <ListBlock items={intentions} empty="No intentions set. NAM is waiting for direction."
                    render={(i) => (
                      <>
                        <div className="flex items-center gap-2 mb-1 flex-wrap">
                          <Target className="w-3.5 h-3.5" style={{ color: COPPER }} />
                          <span className="text-sm font-bold text-ink">{i.objective}</span>
                          <span className="ml-auto text-[10px] text-ink/40">{fmtDate(i.target_date)}</span>
                        </div>
                        {i.owner && <p className="text-xs text-ink/45">owner: {i.owner}</p>}
                        {i.leadership_context && <p className="text-xs text-ink/50 mt-1">{i.leadership_context}</p>}
                        {i.dependencies?.length > 0 && (
                          <p className="text-xs text-ink/45 mt-1">depends on: {i.dependencies.join(", ")}</p>
                        )}
                      </>
                    )} />
                </div>
                {admin && (
                  <div>
                    <Card title="Set Intention" icon={Target}>
                      <div className="space-y-3">
                        <TextArea label="Objective" value={intForm.objective} onChange={(v) => setIntForm({ ...intForm, objective: v })} placeholder="What should NAM be working toward?" rows={2} />
                        <label className="block">
                          <span className="text-xs font-bold text-ink/60">Target date</span>
                          <input type="date" value={intForm.target_date} onChange={(e) => setIntForm({ ...intForm, target_date: e.target.value })}
                            className="mt-1 w-full px-3 py-2 bg-white border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper" />
                        </label>
                        <TextArea label="Leadership context" value={intForm.leadership_context} onChange={(v) => setIntForm({ ...intForm, leadership_context: v })} placeholder="Why this matters" rows={2} />
                        <button onClick={() => { if (!intForm.objective.trim()) return toast.error("Objective is required."); post("/nam/intentions", intForm, () => setIntForm({ objective: "", target_date: "", owner: "Hybrid NAM", leadership_context: "" })); }}
                          disabled={busy}
                          className="w-full flex items-center justify-center gap-2 btn-copper px-4 py-2.5 rounded-lg text-sm font-bold disabled:opacity-40">
                          {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Target className="w-4 h-4" />} Set Intention
                        </button>
                      </div>
                    </Card>
                  </div>
                )}
              </div>
            )}

            {/* ══ DREAMS ══ */}
            {tab === "dreams" && (
              <div className="grid md:grid-cols-3 gap-5">
                <div className="md:col-span-2">
                  <ListBlock items={dreams} empty="No dreams yet. Give NAM something to dream about."
                    render={(d) => (
                      <>
                        <div className="flex items-center gap-2 mb-1">
                          <Moon className="w-3.5 h-3.5" style={{ color: COPPER }} />
                          <span className="text-[10px] font-black uppercase tracking-widest text-ink/40">{fmtDate(d.created_at || d.timestamp)}</span>
                        </div>
                        {d.summary && <p className="text-sm text-ink/80">{d.summary}</p>}
                        {d.open_questions?.length > 0 && (
                          <div className="mt-2"><div className="text-[10px] font-black uppercase tracking-widest text-ink/40 mb-1">Open questions</div>
                            <ul className="list-disc list-inside text-xs text-ink/60">{d.open_questions.map((q, i) => <li key={i}>{q}</li>)}</ul></div>
                        )}
                        {d.creative_ideas?.length > 0 && (
                          <div className="mt-2"><div className="text-[10px] font-black uppercase tracking-widest text-ink/40 mb-1">Creative ideas</div>
                            <ul className="list-disc list-inside text-xs text-ink/60">{d.creative_ideas.map((q, i) => <li key={i}>{q}</li>)}</ul></div>
                        )}
                      </>
                    )} />
                </div>
                {admin && (
                  <div>
                    <Card title="Give NAM a Dream" icon={Moon}>
                      <div className="space-y-3">
                        <TextArea label="Open questions" value={dreamForm.open_questions} onChange={(v) => setDreamForm({ ...dreamForm, open_questions: v })} placeholder="One per line — what's unresolved?" rows={2} />
                        <TextArea label="Creative ideas" value={dreamForm.creative_ideas} onChange={(v) => setDreamForm({ ...dreamForm, creative_ideas: v })} placeholder="One per line" rows={2} />
                        <TextArea label="Organizational challenges" value={dreamForm.organizational_challenges} onChange={(v) => setDreamForm({ ...dreamForm, organizational_challenges: v })} placeholder="One per line" rows={2} />
                        <button onClick={() => {
                          const toArr = (s) => s.split("\n").map((x) => x.trim()).filter(Boolean);
                          if (!toArr(dreamForm.open_questions).length && !toArr(dreamForm.creative_ideas).length && !toArr(dreamForm.organizational_challenges).length)
                            return toast.error("Add at least one line.");
                          post("/nam/dream", {
                            open_questions: toArr(dreamForm.open_questions),
                            creative_ideas: toArr(dreamForm.creative_ideas),
                            organizational_challenges: toArr(dreamForm.organizational_challenges),
                          }, () => setDreamForm({ open_questions: "", creative_ideas: "", organizational_challenges: "" }));
                        }}
                          disabled={busy}
                          className="w-full flex items-center justify-center gap-2 btn-copper px-4 py-2.5 rounded-lg text-sm font-bold disabled:opacity-40">
                          {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Moon className="w-4 h-4" />} Generate Dream
                        </button>
                      </div>
                    </Card>
                  </div>
                )}
              </div>
            )}

            {/* ══ REFLECTIONS ══ */}
            {tab === "reflections" && (
              <div className="grid md:grid-cols-3 gap-5">
                <div className="md:col-span-2">
                  <ListBlock items={reflections} empty="No reflections recorded."
                    render={(r) => (
                      <>
                        <div className="flex items-center gap-2 mb-1 flex-wrap">
                          <span className="text-[10px] font-black uppercase tracking-widest px-2 py-0.5 rounded" style={{ background: "rgba(181,101,29,0.1)", color: COPPER }}>
                            {r.event?.type || r.event_type || "general"}
                          </span>
                          <span className="ml-auto text-[10px] text-ink/35">{fmtDate(r.created_at || r.timestamp)}</span>
                        </div>
                        <p className="text-sm text-ink/80">{r.event?.description || r.event_description}</p>
                        {r.lesson && <p className="text-xs text-ink/50 mt-1">lesson: {typeof r.lesson === "string" ? r.lesson : JSON.stringify(r.lesson)}</p>}
                      </>
                    )} />
                </div>
                {admin && (
                  <div>
                    <Card title="Record Reflection" icon={RefreshCw}>
                      <div className="space-y-3">
                        <TextArea label="Event" value={refForm.event_description} onChange={(v) => setRefForm({ ...refForm, event_description: v })} placeholder="What happened?" rows={2} />
                        <TextArea label="Expectation" value={refForm.expectation} onChange={(v) => setRefForm({ ...refForm, expectation: v })} placeholder="What did you expect?" rows={2} />
                        <TextArea label="Reality" value={refForm.reality} onChange={(v) => setRefForm({ ...refForm, reality: v })} placeholder="What actually happened?" rows={2} />
                        <button onClick={() => { if (!refForm.event_description.trim()) return toast.error("Describe the event."); post("/nam/reflect", refForm, () => setRefForm({ event_type: "general", event_description: "", expectation: "", reality: "", importance: 0.5 })); }}
                          disabled={busy}
                          className="w-full flex items-center justify-center gap-2 btn-copper px-4 py-2.5 rounded-lg text-sm font-bold disabled:opacity-40">
                          {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />} Save Reflection
                        </button>
                      </div>
                    </Card>
                  </div>
                )}
              </div>
            )}

            {/* ══ LEADERSHIP ══ */}
            {tab === "leadership" && (
              <div className="grid md:grid-cols-3 gap-5">
                <div className="md:col-span-2">
                  <Card title="Leadership Ledger" icon={Scale} accent={GREEN}>
                    <ListBlock items={ledger} empty="The ledger is empty — no decisions logged yet."
                      render={(l) => (
                        <>
                          <div className="flex items-center gap-2 mb-1 flex-wrap">
                            <span className="text-[10px] font-black uppercase tracking-widest px-2 py-0.5 rounded" style={{ background: "rgba(27,67,50,0.1)", color: GREEN }}>
                              {l.verdict || l.decision || "reviewed"}
                            </span>
                            <span className="ml-auto text-[10px] text-ink/35">{fmtDate(l.created_at || l.timestamp)}</span>
                          </div>
                          <p className="text-sm text-ink/80">{l.action?.description || l.description}</p>
                          {l.reasoning && <p className="text-xs text-ink/50 mt-1">{typeof l.reasoning === "string" ? l.reasoning : JSON.stringify(l.reasoning)}</p>}
                        </>
                      )} />
                  </Card>
                </div>
                <div className="space-y-5">
                  <Card title="Evaluate an Action" icon={ShieldCheck} accent={GREEN}>
                    <div className="space-y-3">
                      <TextArea label="Action" value={leadForm.description} onChange={(v) => setLeadForm({ ...leadForm, description: v })} placeholder="What is being proposed?" rows={2} />
                      <TextArea label="Purpose" value={leadForm.purpose} onChange={(v) => setLeadForm({ ...leadForm, purpose: v })} placeholder="Why?" rows={2} />
                      <div className="grid grid-cols-2 gap-2">
                        <label className="block">
                          <span className="text-xs font-bold text-ink/60">Actor</span>
                          <input value={leadForm.actor} onChange={(e) => setLeadForm({ ...leadForm, actor: e.target.value })}
                            className="mt-1 w-full px-3 py-2 bg-white border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper" />
                        </label>
                        <label className="block">
                          <span className="text-xs font-bold text-ink/60">Beneficiary</span>
                          <input value={leadForm.beneficiary} onChange={(e) => setLeadForm({ ...leadForm, beneficiary: e.target.value })}
                            className="mt-1 w-full px-3 py-2 bg-white border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper" />
                        </label>
                      </div>
                      <div className="flex gap-2">
                        <button onClick={() => { if (!leadForm.description.trim()) return toast.error("Describe the action."); post("/nam/leadership/review", leadForm, (d) => setLeadResult(d)); }}
                          disabled={busy}
                          className="flex-1 flex items-center justify-center gap-2 px-3 py-2.5 rounded-lg text-sm font-bold border border-ink/20 hover:border-copper transition-colors disabled:opacity-40">
                          <Eye className="w-4 h-4" /> Review
                        </button>
                        {admin && (
                          <button onClick={() => { if (!leadForm.description.trim()) return toast.error("Describe the action."); post("/nam/leadership/evaluate", leadForm, (d) => setLeadResult(d?.evaluation)); }}
                            disabled={busy}
                            className="flex-1 flex items-center justify-center gap-2 btn-copper px-3 py-2.5 rounded-lg text-sm font-bold disabled:opacity-40">
                            {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Scale className="w-4 h-4" />} Log Decision
                          </button>
                        )}
                      </div>
                    </div>
                  </Card>
                  {leadResult && (
                    <Card title="NAM's Verdict" icon={Scale} accent={GOLD}>
                      <pre className="text-xs font-mono whitespace-pre-wrap bg-bone p-3 rounded-lg text-ink/75">{JSON.stringify(leadResult, null, 2)}</pre>
                    </Card>
                  )}
                </div>
              </div>
)}
           {/* ══ STRATEGY ══ */}
           {tab === "strategy" && (
             <div className="grid md:grid-cols-3 gap-5">
               <div className="md:col-span-2">
                 <ListBlock items={strategies} empty="No strategies recorded yet."
                   render={(s) => (
                     <>
                       <div className="flex items-center gap-2 mb-1 flex-wrap">
                         <span className="text-[10px] font-black uppercase tracking-widest px-2 py-0.5 rounded" style={{ background: "rgba(0,0,0,0.1)", color: "#6366f1" }}>
                           {s.horizon}
                         </span>
                         {s.importance != null && (
                           <span className="text-[10px] text-ink/40">importance {Number(s.importance).toFixed(1)}</span>
                         )}
                         <span className="ml-auto text-[10px] text-ink/35">{fmtDate(s.created_at)}</span>
                       </div>
                       <p className="text-sm text-ink/80">{s.objective}</p>
                       {s.key_results && (
                         <p className="text-xs text-ink/50 mt-1">Key results: {s.key_results}</p>
                       )}
                     </>
                   )} />
               </div>
               {admin && (
                 <div>
                   <Card title="Record Strategy" icon={Compass}>
                     <div className="space-y-3">
                       <label className="block">
                         <span className="text-xs font-bold text-ink/60">Horizon</span>
                         <select value={stratForm.horizon} onChange={(e) => setStratForm({ ...stratForm, horizon: e.target.value })}
                           className="mt-1 w-full px-3 py-2 bg-white border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper">
                           <option value="30d">30 days</option>
                           <option value="90d">90 days</option>
                           <option value="1y">1 year</option>
                           <option value="5y">5 years</option>
                         </select>
                       </label>
                       <TextArea label="Objective" value={stratForm.objective} onChange={(v) => setStratForm({ ...stratForm, objective: v })} placeholder="What strategic objective?" rows={2} />
                       <TextArea label="Key Results" value={stratForm.key_results} onChange={(v) => setStratForm({ ...stratForm, key_results: v })} placeholder="Measurable outcomes" rows={2} />
                       <TextArea label="Constraints" value={stratForm.constraints} onChange={(v) => setStratForm({ ...stratForm, constraints: v })} placeholder="Limitations, assumptions" rows={2} />
                       <TextArea label="Resources Required" value={stratForm.resources} onChange={(v) => setStratForm({ ...stratForm, resources: v })} placeholder="People, budget, tools" rows={2} />
                       <button onClick={submitStrategy}
                         disabled={busy}
                         className="w-full flex items-center justify-center gap-2 btn-copper px-4 py-2.5 rounded-lg text-sm font-bold disabled:opacity-40">
                         {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Compass className="w-4 h-4" />} Save Strategy
                       </button>
                     </div>
                   </Card>
                 </div>
               )}
             </div>
            )}
            {/* ══ POWER ══ */}
            {tab === "power" && (
              <div className="grid md:grid-cols-3 gap-5">
                <div className="md:col-span-2">
                  <ListBlock items={powers} empty="No power analyses recorded yet."
                    render={(p) => (
                      <>
                        <div className="flex items-center gap-2 mb-1 flex-wrap">
                          <span className="text-[10px] font-black uppercase tracking-widest px-2 py-0.5 rounded" style={{ background: "rgba(232,165,30,0.1)", color: "#b45309" }}>
                            {p.decision || "Power Analysis"}
                          </span>
                          <span className="ml-auto text-[10px] text-ink/35">{fmtDate(p.created_at)}</span>
                        </div>
                        <p className="text-sm text-ink/80">Actor: {p.actor} · Beneficiary: {p.beneficiary}</p>
                        {p.decision && (
                          <p className="text-xs text-ink/50 mt-1">Decision: {p.decision}</p>
                        )}
                      </>
                    )} />
                </div>
                {admin && (
                  <div>
                    <Card title="Analyze Power" icon={Crown}>
                      <div className="space-y-3">
                        <div className="grid grid-cols-2 gap-2">
                          <label className="block">
                            <span className="text-xs font-bold text-ink/60">Actor</span>
                            <input value={powerForm.actor} onChange={(e) => setPowerForm({ ...powerForm, actor: e.target.value })}
                              className="mt-1 w-full px-3 py-2 bg-white border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper" />
                          </label>
                          <label className="block">
                            <span className="text-xs font-bold text-ink/60">Beneficiary</span>
                            <input value={powerForm.beneficiary} onChange={(e) => setPowerForm({ ...powerForm, beneficiary: e.target.value })}
                              className="mt-1 w-full px-3 py-2 bg-white border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper" />
                          </label>
                        </div>
                        <TextArea label="Decision" value={powerForm.decision} onChange={(v) => setPowerForm({ ...powerForm, decision: v })} placeholder="What decision is being analyzed?" rows={2} />
                        <button onClick={submitPower}
                          disabled={busy}
                          className="w-full flex items-center justify-center gap-2 btn-copper px-4 py-2.5 rounded-lg text-sm font-bold disabled:opacity-40">
                          {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Crown className="w-4 h-4" />} Save Power
                        </button>
                      </div>
                    </Card>
                  </div>
                )}
              </div>
            )}
            {/* ══ RISK ══ */}
           {tab === "risk" && (
             <div className="grid md:grid-cols-3 gap-5">
               <div className="md:col-span-2">
                 <ListBlock items={risks} empty="No risks logged yet."
                   render={(r) => (
                     <>
                       <div className="flex items-center gap-2 mb-1 flex-wrap">
                         <span className="text-[10px] font-black uppercase tracking-widest px-2 py-0.5 rounded" style={{ background: "rgba(239,68,68,0.1)", color: "#dc2626" }}>
                           {r.category}
                         </span>
                         <span className="text-[10px] text-ink/40">risk {Number(r.likelihood * r.impact).toFixed(2)}</span>
                         <span className="ml-auto text-[10px] text-ink/35">{fmtDate(r.created_at)}</span>
                       </div>
                       <p className="text-sm text-ink/80">{r.description}</p>
                       {r.mitigation && (
                         <p className="text-xs text-ink/50 mt-1">Mitigation: {r.mitigation}</p>
                       )}
                     </>
                   )} />
               </div>
               {admin && (
                 <div>
                   <Card title="Log Risk" icon={AlertTriangle}>
                     <div className="space-y-3">
                       <label className="block">
                         <span className="text-xs font-bold text-ink/60">Category</span>
                         <select value={riskForm.category} onChange={(e) => setRiskForm({ ...riskForm, category: e.target.value })}
                           className="mt-1 w-full px-3 py-2 bg-white border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper">
                           <option value="operational">Operational</option>
                           <option value="strategic">Strategic</option>
                           <option value="financial">Financial</option>
                           <option value="compliance">Compliance</option>
                           <option value="reputational">Reputational</option>
                         </select>
                       </label>
                       <TextArea label="Description" value={riskForm.description} onChange={(v) => setRiskForm({ ...riskForm, description: v })} placeholder="What could go wrong?" rows={2} />
                       <div className="grid grid-cols-2 gap-2">
                         <label className="block">
                           <span className="text-xs font-bold text-ink/60">Likelihood (0-1)</span>
                           <input type="number" value={riskForm.likelihood} onChange={(e) => setRiskForm({ ...riskForm, likelihood: parseFloat(e.target.value) || 0.5 })}
                             className="mt-1 w-full px-3 py-2 bg-white border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper" min="0" max="1" step="0.01" />
                         </label>
                         <label className="block">
                           <span className="text-xs font-bold text-ink/60">Impact (0-1)</span>
                           <input type="number" value={riskForm.impact} onChange={(e) => setRiskForm({ ...riskForm, impact: parseFloat(e.target.value) || 0.5 })}
                             className="mt-1 w-full px-3 py-2 bg-white border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper" min="0" max="1" step="0.01" />
                         </label>
                       </div>
                       <TextArea label="Mitigation Plan" value={riskForm.mitigation} onChange={(v) => setRiskForm({ ...riskForm, mitigation: v })} placeholder="How to reduce likelihood/impact?" rows={2} />
                       <button onClick={submitRisk}
                         disabled={busy}
                         className="w-full flex items-center justify-center gap-2 btn-copper px-4 py-2.5 rounded-lg text-sm font-bold disabled:opacity-40">
                         {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <AlertTriangle className="w-4 h-4" />} Save Risk
                       </button>
                     </div>
                   </Card>
                 </div>
               )}
             </div>
           )}
           {/* ══ ACCOUNTABILITY ══ */}
           {tab === "accountability" && (
             <div className="grid md:grid-cols-3 gap-5">
               <div className="md:col-span-2">
                 <ListBlock items={accountabilities} empty="No accountability records yet."
                   render={(a) => (
                     <>
                       <div className="flex items-center gap-2 mb-1 flex-wrap">
                         <span className="text-[10px] font-black uppercase tracking-widest px-2 py-0.5 rounded" style={{ background: "rgba(139,92,246,0.1)", color: "#7c3aed" }}>
                           {a.objective.slice(0, 30)}...
                         </span>
                         <span className="ml-auto text-[10px] text-ink/35">{fmtDate(a.deadline)}</span>
                       </div>
                       <p className="text-sm text-ink/80">Owner: {a.owner}</p>
                       {a.success_criteria && (
                         <p className="text-xs text-ink/50 mt-1">Success: {a.success_criteria}</p>
                       )}
                     </>
                   )} />
               </div>
               {admin && (
                 <div>
                   <Card title="Set Accountability" icon={Key}>
                     <div className="space-y-3">
                       <TextArea label="Objective" value={accForm.objective} onChange={(v) => setAccForm({ ...accForm, objective: v })} placeholder="What needs to be accomplished?" rows={2} />
                       <label className="block">
                         <span className="text-xs font-bold text-ink/60">Owner</span>
                         <input value={accForm.owner} onChange={(e) => setAccForm({ ...accForm, owner: e.target.value })}
                           className="mt-1 w-full px-3 py-2 bg-white border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper" />
                       </label>
                       <label className="block">
                         <span className="text-xs font-bold text-ink/60">Deadline</span>
                         <input type="date" value={accForm.deadline} onChange={(e) => setAccForm({ ...accForm, deadline: e.target.value })}
                           className="mt-1 w-full px-3 py-2 bg-white border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper" />
                       </label>
                       <TextArea label="Success Criteria" value={accForm.success_criteria} onChange={(v) => setAccForm({ ...accForm, success_criteria: v })} placeholder="How will we know it's done?" rows={2} />
                       <button onClick={submitAccountability}
                         disabled={busy}
                         className="w-full flex items-center justify-center gap-2 btn-copper px-4 py-2.5 rounded-lg text-sm font-bold disabled:opacity-40">
                         {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Key className="w-4 h-4" />} Save Accountability
                       </button>
                     </div>
                   </Card>
                 </div>
               )}
             </div>
           )}
           {/* ══ CRISIS ══ */}
           {tab === "crisis" && (
             <div className="grid md:grid-cols-3 gap-5">
               <div className="md:col-span-2">
                 <ListBlock items={crises} empty="No crisis records yet."
                   render={(c) => (
                     <>
                       <div className="flex items-center gap-2 mb-1 flex-wrap">
                         <span className="text-[10px] font-black uppercase tracking-widest px-2 py-0.5 rounded" style={{ background: "rgba(220,38,38,0.1)", color: "#dc2626" }}>
                           {c.severity.toUpperCase()}
                         </span>
                         <span className="ml-auto text-[10px] text-ink/35">{fmtDate(c.created_at)}</span>
                       </div>
                       <p className="text-sm text-ink/80">{c.situation}</p>
                       {c.affected_systems && (
                         <p className="text-xs text-ink/50 mt-1">Systems: {c.affected_systems}</p>
                       )}
                       {c.immediate_actions && (
                         <p className="text-xs text-ink/50 mt-1">Actions: {c.immediate_actions}</p>
                       )}
                     </>
                   )} />
               </div>
               {admin && (
                 <div>
                   <Card title="Log Crisis" icon={Zap}>
                     <div className="space-y-3">
                       <TextArea label="Situation" value={crisisForm.situation} onChange={(v) => setCrisisForm({ ...crisisForm, situation: v })} placeholder="What is happening?" rows={2} />
                       <TextArea label="Affected Systems" value={crisisForm.affected_systems} onChange={(v) => setCrisisForm({ ...crisisForm, affected_systems: v })} placeholder="Which systems/services?" rows={2} />
                       <label className="block">
                         <span className="text-xs font-bold text-ink/60">Severity</span>
                         <select value={crisisForm.severity} onChange={(e) => setCrisisForm({ ...crisisForm, severity: e.target.value })}
                           className="mt-1 w-full px-3 py-2 bg-white border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper">
                           <option value="low">Low</option>
                           <option value="medium">Medium</option>
                           <option value="high">High</option>
                           <option value="critical">Critical</option>
                         </select>
                       </label>
                       <TextArea label="Immediate Actions" value={crisisForm.immediate_actions} onChange={(v) => setCrisisForm({ ...crisisForm, immediate_actions: v })} placeholder="What must be done now?" rows={2} />
                       <button onClick={submitCrisis}
                         disabled={busy}
                         className="w-full flex items-center justify-center gap-2 btn-copper px-4 py-2.5 rounded-lg text-sm font-bold disabled:opacity-40">
                         {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Zap className="w-4 h-4" />} Save Crisis
                       </button>
                     </div>
                   </Card>
                 </div>
               )}
             </div>
           )}
           {/* ══ SUCCESSION ══ */}
           {tab === "succession" && (
             <div className="grid md:grid-cols-3 gap-5">
               <div className="md:col-span-2">
                 <ListBlock items={successions} empty="No succession plans yet."
                   render={(s) => (
                     <>
                       <div className="flex items-center gap-2 mb-1 flex-wrap">
                         <span className="text-[10px] font-black uppercase tracking-widest px-2 py-0.5 rounded" style={{ background: "rgba(168,85,247,0.1)", color: "#a855f7" }}>
                           {s.role}
                         </span>
                         <span className="ml-auto text-[10px] text-ink/35">{fmtDate(s.created_at)}</span>
                       </div>
                       <p className="text-sm text-ink/80">Candidates: {s.successor_candidates}</p>
                       {s.transition_plan && (
                         <p className="text-xs text-ink/50 mt-1">Plan: {s.transition_plan}</p>
                       )}
                     </>
                   )} />
               </div>
               {admin && (
                 <div>
                   <Card title="Plan Succession" icon={Gavel}>
                     <div className="space-y-3">
                       <TextArea label="Role" value={succForm.role} onChange={(v) => setSuccForm({ ...succForm, role: v })} placeholder="Which role needs succession?" rows={2} />
                       <TextArea label="Successor Candidates" value={succForm.successor_candidates} onChange={(v) => setSuccForm({ ...succForm, successor_candidates: v })} placeholder="Who could take over?" rows={2} />
                       <TextArea label="Transition Plan" value={succForm.transition_plan} onChange={(v) => setSuccForm({ ...succForm, transition_plan: v })} placeholder="Knowledge transfer, timeline" rows={2} />
                       <TextArea label="Knowledge Artifacts" value={succForm.knowledge_artifacts} onChange={(v) => setSuccForm({ ...succForm, knowledge_artifacts: v })} placeholder="Documents, passwords, access" rows={2} />
                       <button onClick={submitSuccession}
                         disabled={busy}
                         className="w-full flex items-center justify-center gap-2 btn-copper px-4 py-2.5 rounded-lg text-sm font-bold disabled:opacity-40">
                         {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Gavel className="w-4 h-4" />} Save Succession
                       </button>
                     </div>
                   </Card>
                 </div>
               )}
             </div>
           )}
           {/* ══ ECONOMICS ══ */}
           {tab === "economics" && (
             <div className="grid md:grid-cols-3 gap-5">
               <div className="md:col-span-2">
                 <ListBlock items={economics} empty="No economic flows recorded yet."
                   render={(e) => (
                     <>
                       <div className="flex items-center gap-2 mb-1 flex-wrap">
                         <span className="text-[10px] font-black uppercase tracking-widest px-2 py-0.5 rounded" style={{ background: "rgba(16,185,129,0.1)", color: "#059669" }}>
                           {e.activity}
                         </span>
                         <span className="ml-auto text-[10px] text-ink/35">{fmtDate(e.created_at)}</span>
                       </div>
                       <p className="text-sm text-ink/80">{e.resource_type}: {e.value_estimate}</p>
                       {e.notes && (
                         <p className="text-xs text-ink/50 mt-1">Notes: {e.notes}</p>
                       )}
                     </>
                   )} />
               </div>
               {admin && (
                 <div>
                   <Card title="Record Economic Flow" icon={DollarSign}>
                     <div className="space-y-3">
                       <label className="block">
                         <span className="text-xs font-bold text-ink/60">Activity</span>
                         <select value={econForm.activity} onChange={(e) => setEconForm({ ...econForm, activity: e.target.value })}
                           className="mt-1 w-full px-3 py-2 bg-white border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper">
                           <option value="build">Build</option>
                           <option value="own">Own</option>
                           <option value="license">License</option>
                           <option value="scale">Scale</option>
                         </select>
                       </label>
                       <TextArea label="Resource Type" value={econForm.resource_type} onChange={(v) => setEconForm({ ...econForm, resource_type: v })} placeholder="e.g., compute, storage, IP" rows={2} />
                       <TextArea label="Value Estimate" value={econForm.value_estimate} onChange={(v) => setEconForm({ ...econForm, value_estimate: v })} placeholder="Cost, revenue, savings" rows={2} />
                       <TextArea label="Notes" value={econForm.notes} onChange={(v) => setEconForm({ ...econForm, notes: v })} placeholder="Assumptions, timing" rows={2} />
                       <button onClick={submitEconomics}
                         disabled={busy}
                         className="w-full flex items-center justify-center gap-2 btn-copper px-4 py-2.5 rounded-lg text-sm font-bold disabled:opacity-40">
                         {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <DollarSign className="w-4 h-4" />} Save Economics
                       </button>
                     </div>
                   </Card>
                 </div>
               )}
             </div>
           )}
           {/* ══ ECOSYSTEM ══ */}
           {tab === "ecosystem" && (
             <div className="grid md:grid-cols-3 gap-5">
               <div className="md:col-span-2">
                 <ListBlock items={ecosystems} empty="No ecosystem components yet."
                   render={(e) => (
                     <>
                       <div className="flex items-center gap-2 mb-1 flex-wrap">
                         <span className="text-[10px] font-black uppercase tracking-widest px-2 py-0.5 rounded" style={{ background: "rgba(99,102,241,0.1)", color: "#6366f1" }}>
                           {e.component}
                         </span>
                         <span className="ml-auto text-[10px] text-ink/35">{fmtDate(e.created_at)}</span>
                       </div>
                       <p className="text-sm text-ink/80">{e.purpose}</p>
                       {e.health_status && (
                         <p className="text-xs text-ink/50 mt-1">Health: {e.health_status}</p>
                       )}
                     </>
                   )} />
               </div>
               {admin && (
                 <div>
                   <Card title="Log Ecosystem Component" icon={Network}>
                     <div className="space-y-3">
                       <TextArea label="Component" value={ecoForm.component} onChange={(v) => setEcoForm({ ...ecoForm, component: v })} placeholder="What is the component?" rows={2} />
                       <TextArea label="Purpose" value={ecoForm.purpose} onChange={(v) => setEcoForm({ ...ecoForm, purpose: v })} placeholder="What does it do?" rows={2} />
                       <TextArea label="Dependencies" value={ecoForm.dependencies} onChange={(v) => setEcoForm({ ...ecoForm, dependencies: v })} placeholder="What does it depend on?" rows={2} />
                       <label className="block">
                         <span className="text-xs font-bold text-ink/60">Health Status</span>
                         <select value={ecoForm.health_status} onChange={(e) => setEcoForm({ ...ecoForm, health_status: e.target.value })}
                           className="mt-1 w-full px-3 py-2 bg-white border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper">
                           <option value="healthy">Healthy</option>
                           <option value="degraded">Degraded</option>
                           <option value="down">Down</option>
                           <option value="maintenance">Maintenance</option>
                         </select>
                       </label>
                       <button onClick={submitEcosystem}
                         disabled={busy}
                         className="w-full flex items-center justify-center gap-2 btn-copper px-4 py-2.5 rounded-lg text-sm font-bold disabled:opacity-40">
                         {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Network className="w-4 h-4" />} Save Ecosystem
                       </button>
                     </div>
                   </Card>
                 </div>
               )}
             </div>
           )}
           {/* ══ GOVERNANCE ══ */}
           {tab === "governance" && (
             <div className="grid md:grid-cols-3 gap-5">
               <div className="md:col-span-2">
                 <ListBlock items={governanceChecks} empty="No governance checks yet."
                   render={(g) => (
                     <>
                       <div className="flex items-center gap-2 mb-1 flex-wrap">
                         <span className="text-[10px] font-black uppercase tracking-widest px-2 py-0.5 rounded" style={{ background: "rgba(220,38,38,0.1)", color: "#dc2626" }}>
                           {g.principle}
                         </span>
                         <span className="ml-auto text-[10px] text-ink/35">{fmtDate(g.created_at)}</span>
                       </div>
                       <p className="text-sm text-ink/80">{g.decision_context}</p>
                       {g.analysis && (
                         <p className="text-xs text-ink/50 mt-1">Analysis: {g.analysis}</p>
                       )}
                     </>
                   )} />
               </div>
               {admin && (
                 <div>
                   <Card title="Record Governance Check" icon={Shield}>
                     <div className="space-y-3">
                       <TextArea label="Principle" value={govForm.principle} onChange={(v) => setGovForm({ ...govForm, principle: v })} placeholder="Which constitutional principle?" rows={2} />
                       <TextArea label="Decision Context" value={govForm.decision_context} onChange={(v) => setGovForm({ ...govForm, decision_context: v })} placeholder="What decision is being made?" rows={2} />
                       <TextArea label="Analysis" value={govForm.analysis} onChange={(v) => setGovForm({ ...govForm, analysis: v })} placeholder="How does the principle apply?" rows={2} />
                       <button onClick={submitGovernance}
                         disabled={busy}
                         className="w-full flex items-center justify-center gap-2 btn-copper px-4 py-2.5 rounded-lg text-sm font-bold disabled:opacity-40">
                         {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Shield className="w-4 h-4" />} Save Governance Check
                       </button>
                     </div>
                   </Card>
                 </div>
               )}
             </div>
           )}
           {/* ══ CHALLENGE ══ */}
           {tab === "challenge" && (
             <div className="grid md:grid-cols-3 gap-5">
               <div className="md:col-span-2">
                 <ListBlock items={challenges} empty="No challenges recorded yet."
                   render={(c) => (
                     <>
                       <div className="flex items-center gap-2 mb-1 flex-wrap">
                         <span className="text-[10px] font-black uppercase tracking-widest px-2 py-0.5 rounded" style={{ background: "rgba(245,158,11,0.1)", color: "#d97706" }}>
                           {c.target}
                         </span>
                         <span className="ml-auto text-[10px] text-ink/35">{fmtDate(c.created_at)}</span>
                       </div>
                       <p className="text-sm text-ink/80">{c.issue}</p>
                       {c.evidence && (
                         <p className="text-xs text-ink/50 mt-1">Evidence: {c.evidence}</p>
                       )}
                       {c.proposed_alternative && (
                         <p className="text-xs text-ink/50 mt-1">Alternative: {c.proposed_alternative}</p>
                       )}
                     </>
                   )} />
               </div>
               {admin && (
                 <div>
                   <Card title="Log Challenge" icon={MessageSquare}>
                     <div className="space-y-3">
                       <TextArea label="Target" value={chalForm.target} onChange={(v) => setChalForm({ ...chalForm, target: v })} placeholder="Who/what is being challenged?" rows={2} />
                       <TextArea label="Issue" value={chalForm.issue} onChange={(v) => setChalForm({ ...chalForm, issue: v })} placeholder="What is the concern?" rows={2} />
                       <TextArea label="Evidence" value={chalForm.evidence} onChange={(v) => setChalForm({ ...chalForm, evidence: v })} placeholder="What supports this?" rows={2} />
                       <TextArea label="Proposed Alternative" value={chalForm.proposed_alternative} onChange={(v) => setChalForm({ ...chalForm, proposed_alternative: v })} placeholder="What should be done instead?" rows={2} />
                       <button onClick={submitChallenge}
                         disabled={busy}
                         className="w-full flex items-center justify-center gap-2 btn-copper px-4 py-2.5 rounded-lg text-sm font-bold disabled:opacity-40">
                         {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <MessageSquare className="w-4 h-4" />} Save Challenge
                       </button>
                     </div>
                   </Card>
                 </div>
               )}
</div>
            )}
           </>
        )}
       </div>
     </div>
   );

  return embedded ? body : <AppShell>{body}</AppShell>;
}

export default function HybridNam() {
  return <HybridNamContent />;
}
