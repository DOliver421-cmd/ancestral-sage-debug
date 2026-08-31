/**
 * HybridNam — Assistant Director / Pro-Black Institutional Intelligence
 *
 * Command-console layout:
 *   Left  : INSTITUTIONAL PILLARS navigation
 *   Center: Active pillar record stream
 *   Right : RECORD ENTRY form
 *
 * All data comes from the real /api/nam/* endpoints.
 * No mock data. No simulated AI behavior.
 */

import { useCallback, useEffect, useRef, useState } from "react";
import AppShell from "../components/AppShell";
import { useAuth } from "../lib/auth";
import { api } from "../lib/api";
import { toast } from "sonner";
import {
  Crown, BrainCircuit, BookOpen, Target, Moon, RefreshCw, ShieldCheck,
  Sparkles, Plus, Loader2, HeartHandshake, Scale, Eye,
  Compass, Network, Zap, DollarSign, AlertTriangle, Key, Gavel, MessageSquare, Shield,
  Flag, Menu, X,
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

const canWrite = (role) => ["executive_admin", "oversight", "support_staff"].includes(role);

const PILLARS = [
  { id: "mission",      label: "Mission",      icon: Flag,          description: "Protect and interpret institutional purpose", endpoint: "/nam/operational/mission", collection: "missions" },
  { id: "strategy",     label: "Strategy",     icon: Compass,       description: "Help determine institutional trajectory", endpoint: "/nam/operational/strategy", collection: "strategies" },
  { id: "memory",       label: "Memory",       icon: BookOpen,      description: "Preserve institutional continuity", endpoint: "/nam/memory", collection: "memories" },
  { id: "governance",   label: "Governance",   icon: Shield,        description: "Apply constitutional principles", endpoint: "/nam/operational/governance", collection: "governanceChecks" },
  { id: "challenge",    label: "Challenge",    icon: MessageSquare, description: "Question leadership when warranted", endpoint: "/nam/operational/challenge", collection: "challenges" },
  { id: "ecosystem",    label: "Ecosystem",    icon: Network,       description: "Coordinate AI and distributed services", endpoint: "/nam/operational/ecosystem", collection: "ecosystems" },
  { id: "power",        label: "Power",        icon: Crown,         description: "Analyze authority, ownership, and benefit", endpoint: "/nam/operational/power", collection: "powers" },
  { id: "economics",    label: "Economics",    icon: DollarSign,    description: "Track value creation and capture", endpoint: "/nam/operational/economics", collection: "economics" },
  { id: "risk",         label: "Risk",         icon: AlertTriangle, description: "Detect threats and systemic dependencies", endpoint: "/nam/operational/risk", collection: "risks" },
  { id: "accountability",label: "Accountability",icon: Key,           description: "Compare promises against results", endpoint: "/nam/operational/accountability", collection: "accountabilities" },
  { id: "crisis",       label: "Crisis",       icon: Zap,           description: "Provide structured intelligence during disruption", endpoint: "/nam/operational/crisis", collection: "crises" },
  { id: "succession",   label: "Succession",   icon: Gavel,         description: "Preserve institutional capacity beyond individuals", endpoint: "/nam/operational/succession", collection: "successions" },
];

const PILLAR_DESCRIPTIONS = {
  mission: "Protect and interpret institutional purpose",
  strategy: "Help determine institutional trajectory",
  memory: "Preserve institutional continuity",
  governance: "Apply constitutional principles",
  challenge: "Question leadership when warranted",
  ecosystem: "Coordinate AI and distributed services",
  power: "Analyze authority, ownership, and benefit",
  economics: "Track value creation and capture",
  risk: "Detect threats and systemic dependencies",
  accountability: "Compare promises against results",
  crisis: "Provide structured intelligence during disruption",
  succession: "Preserve institutional capacity beyond individuals",
};

function Field({ label, value }) {
  if (value == null || value === "") return null;
  return (
    <div>
      <div className="text-[10px] font-black uppercase tracking-widest text-ink/40 mb-0.5">{label}</div>
      <div className="text-sm text-ink/80">{value}</div>
    </div>
  );
}

function RecordCard({ record, pillarId }) {
  const getRecordMeta = (rec) => {
    switch (pillarId) {
      case "mission": return { tag: rec.action || "Mission", tagColor: "#b45309", tagBg: "rgba(232,165,30,0.1)", lines: [`Actor: ${rec.actor || "—"}`, `Purpose: ${rec.purpose || "—"}`, `Beneficiary: ${rec.beneficiary || "—"}`] };
      case "strategy": return { tag: rec.horizon || "Strategy", tagColor: "#6366f1", tagBg: "rgba(99,102,241,0.1)", lines: [`Objective: ${rec.objective || "—"}`, rec.key_results ? `Key results: ${rec.key_results}` : null] };
      case "memory": return { tag: rec.memory_type || "semantic", tagColor: COPPER, tagBg: "rgba(181,101,29,0.1)", lines: [rec.content || "—"] };
      case "governance": return { tag: rec.principle || "Governance", tagColor: "#dc2626", tagBg: "rgba(220,38,38,0.1)", lines: [rec.decision_context || "—", rec.analysis || ""] };
      case "challenge": return { tag: rec.target || "Challenge", tagColor: "#d97706", tagBg: "rgba(245,158,11,0.1)", lines: [rec.issue || "—", rec.evidence || "", rec.proposed_alternative || ""] };
      case "ecosystem": return { tag: rec.component || "Component", tagColor: "#6366f1", tagBg: "rgba(99,102,241,0.1)", lines: [rec.purpose || "—", `Health: ${rec.health_status || "—"}`] };
      case "power": return { tag: rec.decision || "Power Analysis", tagColor: "#b45309", tagBg: "rgba(232,165,30,0.1)", lines: [`Actor: ${rec.actor || "—"}`, `Beneficiary: ${rec.beneficiary || "—"}`] };
      case "economics": return { tag: rec.activity || "Economics", tagColor: "#059669", tagBg: "rgba(16,185,129,0.1)", lines: [`${rec.resource_type || "Resource"}: ${rec.value_estimate || "—"}`, rec.notes || ""] };
      case "risk": return { tag: rec.category || "Risk", tagColor: "#dc2626", tagBg: "rgba(239,68,68,0.1)", lines: [`risk ${((rec.likelihood || 0) * (rec.impact || 0)).toFixed(2)}`, rec.description || "—", rec.mitigation || ""] };
      case "accountability": return { tag: (rec.objective || "Accountability").slice(0, 30), tagColor: "#7c3aed", tagBg: "rgba(139,92,246,0.1)", lines: [`Owner: ${rec.owner || "—"}`, rec.success_criteria || ""] };
      case "crisis": return { tag: (rec.severity || "crisis").toUpperCase(), tagColor: "#dc2626", tagBg: "rgba(220,38,38,0.1)", lines: [rec.situation || "—", `Systems: ${rec.affected_systems || "—"}`, rec.immediate_actions || ""] };
      case "succession": return { tag: rec.role || "Succession", tagColor: "#a855f7", tagBg: "rgba(168,85,247,0.1)", lines: [`Candidates: ${rec.successor_candidates || "—"}`, rec.transition_plan || ""] };
      default: return { tag: "Record", tagColor: INK, tagBg: "rgba(0,0,0,0.1)", lines: [JSON.stringify(rec)] };
    }
  };

  const meta = getRecordMeta(record);
  return (
    <div className="rounded-xl border border-ink/8 bg-bone/60 p-4">
      <div className="flex items-center gap-2 mb-2 flex-wrap">
        <span className="text-[10px] font-black uppercase tracking-widest px-2 py-0.5 rounded" style={{ background: meta.tagBg, color: meta.tagColor }}>
          {meta.tag}
        </span>
        <span className="ml-auto text-[10px] text-ink/35">{fmtDate(record.created_at)}</span>
      </div>
      <div className="space-y-1">
        {meta.lines.filter(Boolean).map((line, i) => (
          <p key={i} className="text-sm text-ink/75">{line}</p>
        ))}
      </div>
    </div>
  );
}

export function HybridNamContent({ embedded = false }) {
  const { user } = useAuth();
  const [activePillar, setActivePillar] = useState("mission");
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [formValues, setFormValues] = useState({});

  const admin = canWrite(user?.role);

  const pillar = PILLARS.find((p) => p.id === activePillar) || PILLARS[0];

  const loadPillar = useCallback(async (pillarId) => {
    setLoading(true);
    setError(null);
    const target = PILLARS.find((p) => p.id === pillarId);
    if (!target) return;
    try {
      const { data } = await api.get(target.endpoint);
      const items = data?.[target.collection] || [];
      setRecords(items);
    } catch (err) {
      const msg = describeRequestError(err);
      setError(msg);
      setRecords([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadPillar(activePillar);
  }, [activePillar, loadPillar]);

  const handlePillarChange = (pillarId) => {
    setActivePillar(pillarId);
    setSidebarOpen(false);
  };

  const handleRefresh = () => {
    loadPillar(activePillar);
  };

  const getFormFields = () => {
    switch (activePillar) {
      case "mission": return (
        <>
          <label className="block">
            <span className="text-xs font-bold text-ink/60">Action</span>
            <textarea value={formValues.action || ""} onChange={(e) => setFormValues({ ...formValues, action: e.target.value })}
              placeholder="What action is being evaluated?" rows={2}
              className="mt-1 w-full resize-y px-3 py-2 bg-white border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper" />
          </label>
          <div className="grid grid-cols-2 gap-2">
            <label className="block">
              <span className="text-xs font-bold text-ink/60">Actor</span>
              <input value={formValues.actor || ""} onChange={(e) => setFormValues({ ...formValues, actor: e.target.value })}
                className="mt-1 w-full px-3 py-2 bg-white border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper" />
            </label>
            <label className="block">
              <span className="text-xs font-bold text-ink/60">Beneficiary</span>
              <input value={formValues.beneficiary || ""} onChange={(e) => setFormValues({ ...formValues, beneficiary: e.target.value })}
                className="mt-1 w-full px-3 py-2 bg-white border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper" />
            </label>
          </div>
          <label className="block">
            <span className="text-xs font-bold text-ink/60">Purpose</span>
            <textarea value={formValues.purpose || ""} onChange={(e) => setFormValues({ ...formValues, purpose: e.target.value })}
              placeholder="Why does this matter to the mission?" rows={2}
              className="mt-1 w-full resize-y px-3 py-2 bg-white border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper" />
          </label>
        </>
      );
      case "strategy": return (
        <>
          <label className="block">
            <span className="text-xs font-bold text-ink/60">Horizon</span>
            <select value={formValues.horizon || "90d"} onChange={(e) => setFormValues({ ...formValues, horizon: e.target.value })}
              className="mt-1 w-full px-3 py-2 bg-white border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper">
              <option value="30d">30 days</option>
              <option value="90d">90 days</option>
              <option value="1y">1 year</option>
              <option value="5y">5 years</option>
            </select>
          </label>
          <label className="block">
            <span className="text-xs font-bold text-ink/60">Objective</span>
            <textarea value={formValues.objective || ""} onChange={(e) => setFormValues({ ...formValues, objective: e.target.value })}
              placeholder="What strategic objective?" rows={2}
              className="mt-1 w-full resize-y px-3 py-2 bg-white border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper" />
          </label>
          <label className="block">
            <span className="text-xs font-bold text-ink/60">Key Results</span>
            <textarea value={formValues.key_results || ""} onChange={(e) => setFormValues({ ...formValues, key_results: e.target.value })}
              placeholder="Measurable outcomes" rows={2}
              className="mt-1 w-full resize-y px-3 py-2 bg-white border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper" />
          </label>
          <label className="block">
            <span className="text-xs font-bold text-ink/60">Constraints</span>
            <textarea value={formValues.constraints || ""} onChange={(e) => setFormValues({ ...formValues, constraints: e.target.value })}
              placeholder="Limitations, assumptions" rows={2}
              className="mt-1 w-full resize-y px-3 py-2 bg-white border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper" />
          </label>
          <label className="block">
            <span className="text-xs font-bold text-ink/60">Resources Required</span>
            <textarea value={formValues.resources || ""} onChange={(e) => setFormValues({ ...formValues, resources: e.target.value })}
              placeholder="People, budget, tools" rows={2}
              className="mt-1 w-full resize-y px-3 py-2 bg-white border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper" />
          </label>
        </>
      );
      case "power": return (
        <>
          <div className="grid grid-cols-2 gap-2">
            <label className="block">
              <span className="text-xs font-bold text-ink/60">Actor</span>
              <input value={formValues.actor || ""} onChange={(e) => setFormValues({ ...formValues, actor: e.target.value })}
                className="mt-1 w-full px-3 py-2 bg-white border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper" />
            </label>
            <label className="block">
              <span className="text-xs font-bold text-ink/60">Beneficiary</span>
              <input value={formValues.beneficiary || ""} onChange={(e) => setFormValues({ ...formValues, beneficiary: e.target.value })}
                className="mt-1 w-full px-3 py-2 bg-white border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper" />
            </label>
          </div>
          <label className="block">
            <span className="text-xs font-bold text-ink/60">Decision</span>
            <textarea value={formValues.decision || ""} onChange={(e) => setFormValues({ ...formValues, decision: e.target.value })}
              placeholder="What decision is being analyzed?" rows={2}
              className="mt-1 w-full resize-y px-3 py-2 bg-white border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper" />
          </label>
        </>
      );
      case "risk": return (
        <>
          <label className="block">
            <span className="text-xs font-bold text-ink/60">Category</span>
            <select value={formValues.category || "operational"} onChange={(e) => setFormValues({ ...formValues, category: e.target.value })}
              className="mt-1 w-full px-3 py-2 bg-white border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper">
              <option value="operational">Operational</option>
              <option value="strategic">Strategic</option>
              <option value="financial">Financial</option>
              <option value="compliance">Compliance</option>
              <option value="reputational">Reputational</option>
            </select>
          </label>
          <label className="block">
            <span className="text-xs font-bold text-ink/60">Description</span>
            <textarea value={formValues.description || ""} onChange={(e) => setFormValues({ ...formValues, description: e.target.value })}
              placeholder="What could go wrong?" rows={2}
              className="mt-1 w-full resize-y px-3 py-2 bg-white border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper" />
          </label>
          <div className="grid grid-cols-2 gap-2">
            <label className="block">
              <span className="text-xs font-bold text-ink/60">Likelihood (0-1)</span>
              <input type="number" value={formValues.likelihood ?? 0.5} onChange={(e) => setFormValues({ ...formValues, likelihood: parseFloat(e.target.value) || 0.5 })}
                className="mt-1 w-full px-3 py-2 bg-white border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper" min="0" max="1" step="0.01" />
            </label>
            <label className="block">
              <span className="text-xs font-bold text-ink/60">Impact (0-1)</span>
              <input type="number" value={formValues.impact ?? 0.5} onChange={(e) => setFormValues({ ...formValues, impact: parseFloat(e.target.value) || 0.5 })}
                className="mt-1 w-full px-3 py-2 bg-white border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper" min="0" max="1" step="0.01" />
            </label>
          </div>
          <label className="block">
            <span className="text-xs font-bold text-ink/60">Mitigation Plan</span>
            <textarea value={formValues.mitigation || ""} onChange={(e) => setFormValues({ ...formValues, mitigation: e.target.value })}
              placeholder="How to reduce likelihood/impact?" rows={2}
              className="mt-1 w-full resize-y px-3 py-2 bg-white border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper" />
          </label>
        </>
      );
      case "accountability": return (
        <>
          <label className="block">
            <span className="text-xs font-bold text-ink/60">Objective</span>
            <textarea value={formValues.objective || ""} onChange={(e) => setFormValues({ ...formValues, objective: e.target.value })}
              placeholder="What needs to be accomplished?" rows={2}
              className="mt-1 w-full resize-y px-3 py-2 bg-white border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper" />
          </label>
          <label className="block">
            <span className="text-xs font-bold text-ink/60">Owner</span>
            <input value={formValues.owner || "Hybrid NAM"} onChange={(e) => setFormValues({ ...formValues, owner: e.target.value })}
              className="mt-1 w-full px-3 py-2 bg-white border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper" />
          </label>
          <label className="block">
            <span className="text-xs font-bold text-ink/60">Deadline</span>
            <input type="date" value={formValues.deadline || ""} onChange={(e) => setFormValues({ ...formValues, deadline: e.target.value })}
              className="mt-1 w-full px-3 py-2 bg-white border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper" />
          </label>
          <label className="block">
            <span className="text-xs font-bold text-ink/60">Success Criteria</span>
            <textarea value={formValues.success_criteria || ""} onChange={(e) => setFormValues({ ...formValues, success_criteria: e.target.value })}
              placeholder="How will we know it's done?" rows={2}
              className="mt-1 w-full resize-y px-3 py-2 bg-white border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper" />
          </label>
        </>
      );
      case "crisis": return (
        <>
          <label className="block">
            <span className="text-xs font-bold text-ink/60">Situation</span>
            <textarea value={formValues.situation || ""} onChange={(e) => setFormValues({ ...formValues, situation: e.target.value })}
              placeholder="What is happening?" rows={2}
              className="mt-1 w-full resize-y px-3 py-2 bg-white border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper" />
          </label>
          <label className="block">
            <span className="text-xs font-bold text-ink/60">Affected Systems</span>
            <textarea value={formValues.affected_systems || ""} onChange={(e) => setFormValues({ ...formValues, affected_systems: e.target.value })}
              placeholder="Which systems/services?" rows={2}
              className="mt-1 w-full resize-y px-3 py-2 bg-white border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper" />
          </label>
          <label className="block">
            <span className="text-xs font-bold text-ink/60">Severity</span>
            <select value={formValues.severity || "high"} onChange={(e) => setFormValues({ ...formValues, severity: e.target.value })}
              className="mt-1 w-full px-3 py-2 bg-white border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper">
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="critical">Critical</option>
            </select>
          </label>
          <label className="block">
            <span className="text-xs font-bold text-ink/60">Immediate Actions</span>
            <textarea value={formValues.immediate_actions || ""} onChange={(e) => setFormValues({ ...formValues, immediate_actions: e.target.value })}
              placeholder="What must be done now?" rows={2}
              className="mt-1 w-full resize-y px-3 py-2 bg-white border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper" />
          </label>
        </>
      );
      case "succession": return (
        <>
          <label className="block">
            <span className="text-xs font-bold text-ink/60">Role</span>
            <textarea value={formValues.role || ""} onChange={(e) => setFormValues({ ...formValues, role: e.target.value })}
              placeholder="Which role needs succession?" rows={2}
              className="mt-1 w-full resize-y px-3 py-2 bg-white border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper" />
          </label>
          <label className="block">
            <span className="text-xs font-bold text-ink/60">Successor Candidates</span>
            <textarea value={formValues.successor_candidates || ""} onChange={(e) => setFormValues({ ...formValues, successor_candidates: e.target.value })}
              placeholder="Who could take over?" rows={2}
              className="mt-1 w-full resize-y px-3 py-2 bg-white border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper" />
          </label>
          <label className="block">
            <span className="text-xs font-bold text-ink/60">Transition Plan</span>
            <textarea value={formValues.transition_plan || ""} onChange={(e) => setFormValues({ ...formValues, transition_plan: e.target.value })}
              placeholder="Knowledge transfer, timeline" rows={2}
              className="mt-1 w-full resize-y px-3 py-2 bg-white border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper" />
          </label>
          <label className="block">
            <span className="text-xs font-bold text-ink/60">Knowledge Artifacts</span>
            <textarea value={formValues.knowledge_artifacts || ""} onChange={(e) => setFormValues({ ...formValues, knowledge_artifacts: e.target.value })}
              placeholder="Documents, passwords, access" rows={2}
              className="mt-1 w-full resize-y px-3 py-2 bg-white border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper" />
          </label>
        </>
      );
      case "economics": return (
        <>
          <label className="block">
            <span className="text-xs font-bold text-ink/60">Activity</span>
            <select value={formValues.activity || "build"} onChange={(e) => setFormValues({ ...formValues, activity: e.target.value })}
              className="mt-1 w-full px-3 py-2 bg-white border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper">
              <option value="build">Build</option>
              <option value="own">Own</option>
              <option value="license">License</option>
              <option value="scale">Scale</option>
            </select>
          </label>
          <label className="block">
            <span className="text-xs font-bold text-ink/60">Resource Type</span>
            <input value={formValues.resource_type || ""} onChange={(e) => setFormValues({ ...formValues, resource_type: e.target.value })}
              placeholder="e.g., compute, storage, IP"
              className="mt-1 w-full px-3 py-2 bg-white border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper" />
          </label>
          <label className="block">
            <span className="text-xs font-bold text-ink/60">Value Estimate</span>
            <textarea value={formValues.value_estimate || ""} onChange={(e) => setFormValues({ ...formValues, value_estimate: e.target.value })}
              placeholder="Cost, revenue, savings" rows={2}
              className="mt-1 w-full resize-y px-3 py-2 bg-white border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper" />
          </label>
          <label className="block">
            <span className="text-xs font-bold text-ink/60">Notes</span>
            <textarea value={formValues.notes || ""} onChange={(e) => setFormValues({ ...formValues, notes: e.target.value })}
              placeholder="Assumptions, timing" rows={2}
              className="mt-1 w-full resize-y px-3 py-2 bg-white border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper" />
          </label>
        </>
      );
      case "ecosystem": return (
        <>
          <label className="block">
            <span className="text-xs font-bold text-ink/60">Component</span>
            <textarea value={formValues.component || ""} onChange={(e) => setFormValues({ ...formValues, component: e.target.value })}
              placeholder="What is the component?" rows={2}
              className="mt-1 w-full resize-y px-3 py-2 bg-white border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper" />
          </label>
          <label className="block">
            <span className="text-xs font-bold text-ink/60">Purpose</span>
            <textarea value={formValues.purpose || ""} onChange={(e) => setFormValues({ ...formValues, purpose: e.target.value })}
              placeholder="What does it do?" rows={2}
              className="mt-1 w-full resize-y px-3 py-2 bg-white border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper" />
          </label>
          <label className="block">
            <span className="text-xs font-bold text-ink/60">Dependencies</span>
            <textarea value={formValues.dependencies || ""} onChange={(e) => setFormValues({ ...formValues, dependencies: e.target.value })}
              placeholder="What does it depend on?" rows={2}
              className="mt-1 w-full resize-y px-3 py-2 bg-white border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper" />
          </label>
          <label className="block">
            <span className="text-xs font-bold text-ink/60">Health Status</span>
            <select value={formValues.health_status || "healthy"} onChange={(e) => setFormValues({ ...formValues, health_status: e.target.value })}
              className="mt-1 w-full px-3 py-2 bg-white border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper">
              <option value="healthy">Healthy</option>
              <option value="degraded">Degraded</option>
              <option value="down">Down</option>
              <option value="maintenance">Maintenance</option>
            </select>
          </label>
        </>
      );
      case "governance": return (
        <>
          <label className="block">
            <span className="text-xs font-bold text-ink/60">Principle</span>
            <textarea value={formValues.principle || ""} onChange={(e) => setFormValues({ ...formValues, principle: e.target.value })}
              placeholder="Which constitutional principle?" rows={2}
              className="mt-1 w-full resize-y px-3 py-2 bg-white border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper" />
          </label>
          <label className="block">
            <span className="text-xs font-bold text-ink/60">Decision Context</span>
            <textarea value={formValues.decision_context || ""} onChange={(e) => setFormValues({ ...formValues, decision_context: e.target.value })}
              placeholder="What decision is being made?" rows={2}
              className="mt-1 w-full resize-y px-3 py-2 bg-white border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper" />
          </label>
          <label className="block">
            <span className="text-xs font-bold text-ink/60">Analysis</span>
            <textarea value={formValues.analysis || ""} onChange={(e) => setFormValues({ ...formValues, analysis: e.target.value })}
              placeholder="How does the principle apply?" rows={2}
              className="mt-1 w-full resize-y px-3 py-2 bg-white border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper" />
          </label>
        </>
      );
      case "challenge": return (
        <>
          <label className="block">
            <span className="text-xs font-bold text-ink/60">Target</span>
            <input value={formValues.target || "leadership"} onChange={(e) => setFormValues({ ...formValues, target: e.target.value })}
              className="mt-1 w-full px-3 py-2 bg-white border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper" />
          </label>
          <label className="block">
            <span className="text-xs font-bold text-ink/60">Issue</span>
            <textarea value={formValues.issue || ""} onChange={(e) => setFormValues({ ...formValues, issue: e.target.value })}
              placeholder="What is the concern?" rows={2}
              className="mt-1 w-full resize-y px-3 py-2 bg-white border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper" />
          </label>
          <label className="block">
            <span className="text-xs font-bold text-ink/60">Evidence</span>
            <textarea value={formValues.evidence || ""} onChange={(e) => setFormValues({ ...formValues, evidence: e.target.value })}
              placeholder="What supports this?" rows={2}
              className="mt-1 w-full resize-y px-3 py-2 bg-white border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper" />
          </label>
          <label className="block">
            <span className="text-xs font-bold text-ink/60">Proposed Alternative</span>
            <textarea value={formValues.proposed_alternative || ""} onChange={(e) => setFormValues({ ...formValues, proposed_alternative: e.target.value })}
              placeholder="What should be done instead?" rows={2}
              className="mt-1 w-full resize-y px-3 py-2 bg-white border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper" />
          </label>
        </>
      );
      default: return null;
    }
  };

  const getSubmitLabel = () => `COMMIT TO ${pillar.label.toUpperCase()}`;

  const handleSubmit = async (e) => {
    e.preventDefault();
    const target = PILLARS.find((p) => p.id === activePillar);
    if (!target) return;

    let payload = { ...formValues };
    let requiresArrayNormalization = false;
    if (activePillar === "memory") {
      payload = { ...payload, participants: [] };
    }

    setSubmitting(true);
    try {
      await api.post(target.endpoint, payload);
      toast.success(`Committed to ${pillar.label}.`);
      setFormValues({});
      await loadPillar(activePillar);
    } catch (err) {
      toast.error(describeRequestError(err));
    } finally {
      setSubmitting(false);
    }
  };

  const getEmptyState = () => {
    switch (activePillar) {
      case "mission": return "No mission interpretations recorded yet.";
      case "strategy": return "No strategies recorded yet.";
      case "memory": return "No memories stored yet.";
      case "governance": return "No governance checks yet.";
      case "challenge": return "No challenges recorded yet.";
      case "ecosystem": return "No ecosystem components yet.";
      case "power": return "No power analyses recorded yet.";
      case "economics": return "No economic flows recorded yet.";
      case "risk": return "No risks logged yet.";
      case "accountability": return "No accountability records yet.";
      case "crisis": return "No crisis records yet.";
      case "succession": return "No succession plans yet.";
      default: return "No records yet.";
    }
  };

  const body = (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      {/* Executive Header */}
      <header className="shrink-0 border-b border-slate-800 bg-slate-950/95 backdrop-blur">
        <div className="flex items-center justify-between px-4 sm:px-6 py-3">
          <div className="flex items-center gap-3">
            <button onClick={() => setSidebarOpen(!sidebarOpen)} className="lg:hidden p-2 -ml-2 rounded-lg border border-slate-700 text-slate-300 hover:text-white hover:border-slate-500" aria-label="Toggle navigation">
              {sidebarOpen ? <X className="w-4 h-4" /> : <Menu className="w-4 h-4" />}
            </button>
            <div>
              <div className="text-[10px] font-black uppercase tracking-widest text-emerald-400">Assistant Director — Pro-Black Institutional Intelligence</div>
              <h1 className="font-heading text-lg sm:text-xl font-bold tracking-tight text-white">HYBRID NAM</h1>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="hidden sm:inline-flex items-center gap-1.5 text-[10px] font-black uppercase tracking-widest px-2 py-1 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              Active Command
            </span>
            <button onClick={handleRefresh} disabled={loading}
              className="flex items-center gap-1.5 text-xs font-bold px-3 py-1.5 rounded-lg border border-slate-700 text-slate-300 hover:text-white hover:border-slate-500 disabled:opacity-40 transition-colors">
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} /> Refresh
            </button>
          </div>
        </div>
      </header>

      {/* Error Banner */}
      {error && (
        <div className="shrink-0 border-b border-red-900/50 bg-red-950/30 px-4 sm:px-6 py-2.5" role="alert">
          <div className="flex items-start justify-between gap-3">
            <div>
              <div className="text-xs font-bold text-red-400">NAM could not load live data</div>
              <div className="text-xs text-red-300/80 mt-0.5">{error}</div>
            </div>
            <button onClick={handleRefresh} className="text-xs font-bold px-2 py-1 rounded border border-red-800 text-red-300 hover:bg-red-900/30">
              Retry
            </button>
          </div>
        </div>
      )}

      {/* Main Layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* Mobile Overlay */}
        {sidebarOpen && (
          <div className="fixed inset-0 bg-black/50 z-20 lg:hidden" onClick={() => setSidebarOpen(false)} />
        )}

        {/* Left Sidebar — Institutional Pillars */}
        <aside className={`
          fixed inset-y-0 left-0 z-30 w-64 bg-slate-950 border-r border-slate-800 transform transition-transform duration-200 lg:static lg:translate-x-0 lg:block
          ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
        `}>
          <div className="h-full flex flex-col">
            <div className="px-4 py-3 border-b border-slate-800">
              <div className="text-[10px] font-black uppercase tracking-widest text-slate-500">Institutional Pillars</div>
            </div>
            <nav className="flex-1 overflow-y-auto py-2" aria-label="Institutional pillars">
              <ul className="space-y-0.5 px-2">
                {PILLARS.map((p) => {
                  const Icon = p.icon;
                  const isActive = activePillar === p.id;
                  return (
                    <li key={p.id}>
                      <button
                        onClick={() => handlePillarChange(p.id)}
                        className={`
                          w-full text-left flex items-start gap-2.5 px-3 py-2 rounded-lg transition-colors
                          ${isActive ? "bg-emerald-500/10 text-emerald-300 border border-emerald-500/20" : "text-slate-400 hover:text-slate-200 hover:bg-slate-900 border border-transparent"}
                        `}
                        aria-current={isActive ? "page" : undefined}
                      >
                        <Icon className={`w-4 h-4 mt-0.5 shrink-0 ${isActive ? "text-emerald-400" : "text-slate-500"}`} />
                        <div className="min-w-0">
                          <div className={`text-xs font-bold truncate ${isActive ? "text-emerald-300" : "text-slate-300"}`}>{p.label}</div>
                          <div className="text-[10px] text-slate-500 leading-tight mt-0.5 line-clamp-2">{p.description}</div>
                        </div>
                      </button>
                    </li>
                  );
                })}
              </ul>
            </nav>
          </div>
        </aside>

        {/* Center — Active Pillar Stream */}
        <main className="flex-1 overflow-y-auto min-w-0">
          <div className="p-4 sm:p-6 max-w-4xl">
            <div className="mb-4">
              <div className="flex items-center gap-2 mb-1">
                <pillar.icon className="w-4 h-4 text-emerald-400" />
                <h2 className="text-sm font-black uppercase tracking-widest text-emerald-400">{pillar.label} Stream</h2>
              </div>
              <p className="text-xs text-slate-500">{PILLAR_DESCRIPTIONS[activePillar]}</p>
            </div>

            {loading ? (
              <div className="py-16 text-center text-slate-500 flex items-center justify-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin" /> Reading NAM state…
              </div>
            ) : records.length === 0 ? (
              <div className="py-12 text-center text-slate-500 border border-dashed border-slate-800 rounded-xl">
                <div className="text-xs font-bold uppercase tracking-widest mb-1">No Records</div>
                <div className="text-xs text-slate-600">{getEmptyState()}</div>
              </div>
            ) : (
              <div className="space-y-2">
                {records.map((rec, i) => (
                  <RecordCard key={rec.id || i} record={rec} pillarId={activePillar} />
                ))}
              </div>
            )}
          </div>
        </main>

        {/* Right — Record Entry */}
        {admin && (
          <aside className="hidden lg:block w-80 shrink-0 border-l border-slate-800 overflow-y-auto">
            <div className="p-4">
              <div className="text-[10px] font-black uppercase tracking-widest text-slate-500 mb-3">Record Entry</div>
              <form onSubmit={handleSubmit} className="space-y-3">
                {getFormFields()}
                <button type="submit" disabled={submitting}
                  className="w-full flex items-center justify-center gap-2 btn-copper px-4 py-2.5 rounded-lg text-sm font-bold disabled:opacity-40">
                  {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />} {getSubmitLabel()}
                </button>
              </form>
            </div>
          </aside>
        )}
      </div>
    </div>
  );

  return embedded ? body : <AppShell>{body}</AppShell>;
}

export default function HybridNam() {
  return <HybridNamContent />;
}
