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
  { id: "memory",       label: "Memory",       icon: BookOpen },
  { id: "intentions",   label: "Intentions",   icon: Target },
  { id: "dreams",       label: "Dreams",       icon: Moon },
  { id: "reflections",  label: "Reflections",  icon: RefreshCw },
  { id: "leadership",   label: "Leadership",   icon: Scale },
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

  const [busy, setBusy] = useState(false);
  const [loadErrors, setLoadErrors] = useState([]);

  // Write-form state
  const [memForm, setMemForm] = useState({ memory_type: "semantic", content: "", importance: 0.5 });
  const [intForm, setIntForm] = useState({ objective: "", target_date: "", owner: "Hybrid NAM", leadership_context: "" });
  const [dreamForm, setDreamForm] = useState({ open_questions: "", creative_ideas: "", organizational_challenges: "" });
  const [refForm, setRefForm] = useState({ event_type: "general", event_description: "", expectation: "", reality: "", importance: 0.5 });
  const [leadForm, setLeadForm] = useState({ description: "", actor: "Jamil", purpose: "", beneficiary: "user" });
  const [leadResult, setLeadResult] = useState(null);

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
    ];
    const results = await Promise.allSettled(endpoints.map(([, path]) => api.get(path).then((r) => r.data)));
    const values = results.map((result, index) => {
      if (result.status === "fulfilled") return result.value;
      return endpoints[index][2];
    });
    setLoadErrors(results.flatMap((result, index) => (
      result.status === "rejected" ? [`${endpoints[index][0]}: ${describeRequestError(result.reason)}`] : []
    )));
    const [id, st, con, mem, ints, dr, ref, led] = values;
    setIdentity(id);
    setState(st);
    setConstitution(con);
    setMemories(mem?.memories || []);
    setIntentions(ints?.intentions || []);
    setDreams(dr?.dreams || []);
    setReflections(ref?.reflections || []);
    setLedger(led?.ledger || []);
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

  const body = (
    <div className={embedded ? "h-full overflow-y-auto bg-bone" : "bg-bone"} style={embedded ? {} : { minHeight: "100vh" }}>
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8">
        <PageBack to="/admin" label="Admin" />
        {/* ── Header ── */}
        <div className="rounded-2xl p-6 mb-6 text-white"
          style={{ background: `linear-gradient(135deg, ${GREEN}, #2D6A4F)` }}>
          <div className="flex items-center gap-3 flex-wrap">
            <span className="text-3xl">🌑</span>
            <div>
              <div className="text-[10px] font-black uppercase tracking-widest" style={{ color: GOLD }}>Assistant Director · The Source remains untouched</div>
              <h1 className="font-heading text-2xl font-bold tracking-tight">Hybrid NAM</h1>
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
