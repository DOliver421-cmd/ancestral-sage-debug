import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import { canAccess } from "../lib/tiers";
import {
  Loader2, DollarSign, Heart, Briefcase, Bot, Search, Filter,
  Plus, CheckCircle2, Clock, AlertTriangle, ArrowRight, FileText,
  Target, Award, BookOpen, ExternalLink, ChevronDown, ChevronUp,
  Send, Sparkles, Users, TrendingUp, Calendar, Scale,
} from "lucide-react";

const TABS = [
  { id: "dashboard", label: "Dashboard", icon: Target },
  { id: "grants", label: "Grants", icon: Award },
  { id: "fundraising", label: "Fundraising", icon: Heart },
  { id: "resources", label: "Business Resources", icon: Briefcase },
  { id: "legal", label: "Legal Workflows", icon: Scale },
  { id: "assistant", label: "Assistant", icon: Bot },
];

const RESOURCE_CATEGORIES = [
  { key: "legal", label: "Legal & Compliance", icon: FileText },
  { key: "financial", label: "Financial & Funding", icon: DollarSign },
  { key: "marketing", label: "Marketing & Outreach", icon: TrendingUp },
  { key: "technology", label: "Technology & Tools", icon: Sparkles },
  { key: "compliance", label: "Compliance & Reporting", icon: CheckCircle2 },
  { key: "networking", label: "Networking & Mentorship", icon: Users },
  { key: "templates", label: "Templates & Guides", icon: BookOpen },
];

const GRANT_CATEGORIES = [
  { key: "general", label: "General" },
  { key: "education", label: "Education" },
  { key: "tech", label: "Technology" },
  { key: "community", label: "Community" },
  { key: "arts", label: "Arts & Culture" },
];

function explain(err) {
  const d = err?.response?.data?.detail;
  return typeof d === "string" ? d : err?.message || "Request failed";
}

export default function ResourceHubPanel({ user }) {
  const [tab, setTab] = useState("dashboard");
  const [tier, setTier] = useState("free");

  useEffect(() => {
    if (user) {
      const t = user.feature_tier || "free";
      const r = user.role || "";
      const isStaff = ["instructor", "admin", "executive_admin", "support_staff", "oversight"].includes(r);
      setTier(isStaff ? "staff" : t);
    }
  }, [user]);

  if (!user || !canAccess(user, "resource_hub")) {
    return (
      <div className="max-w-xl mx-auto mt-16 card-flat p-8 text-center">
        <Briefcase className="w-8 h-8 text-copper mx-auto mb-3" />
        <h1 className="font-heading font-bold text-xl text-ink">Plus membership required</h1>
        <p className="text-sm text-ink/60 mt-2">The Resource Hub requires a Plus subscription or higher. Staff access is included automatically.</p>
        <Link to="/subscribe" className="btn-primary mt-4 inline-flex">Upgrade to Plus</Link>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <h1 className="font-heading font-bold text-3xl text-ink mb-1 flex items-center gap-3">
        <Briefcase className="w-8 h-8 text-copper" /> Resource Hub
      </h1>
      <p className="text-ink/60 mb-6">Grants, fundraising, business resources — one workspace, real workflows.</p>

      {/* Tab bar */}
      <div className="flex gap-1 mb-8 overflow-x-auto pb-2">
        {TABS.map(t => {
          const Icon = t.icon;
          return (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-bold whitespace-nowrap transition-all ${
                tab === t.id
                  ? "bg-copper text-white"
                  : "bg-ink/5 text-ink/60 hover:bg-ink/10"
              }`}
            >
              <Icon className="w-4 h-4" /> {t.label}
            </button>
          );
        })}
      </div>

      {tab === "dashboard" && <HubDashboard />}
      {tab === "grants" && <GrantsTab />}
      {tab === "fundraising" && <FundraisingTab />}
      {tab === "resources" && <ResourcesTab />}
      {tab === "legal" && <LegalWorkflowTab />}
      {tab === "assistant" && <AssistantTab />}
    </div>
  );
}

// ── Dashboard ────────────────────────────────────────────────────────────────

function HubDashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/hub/dashboard")
      .then(r => setData(r.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <Loader2 className="w-5 h-5 animate-spin text-ink/40" />;
  if (!data) return <p className="text-ink/50">Could not load dashboard.</p>;

  return (
    <div className="space-y-6">
      {/* Stats cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard icon={Award} label="Open Grants" value={data.grants?.open || 0} color="text-copper" />
        <StatCard icon={FileText} label="My Applications" value={data.grants?.my_applications || 0} color="text-blue-600" />
        <StatCard icon={Heart} label="Active Campaigns" value={data.fundraising?.active_campaigns || 0} color="text-red-500" />
        <StatCard icon={Briefcase} label="Business Resources" value={data.resources?.total || 0} color="text-green-600" />
      </div>

      {/* Next step */}
      {data.workflows?.next_step && (
        <div className="card-flat p-5 border-l-4 border-copper">
          <div className="flex items-center gap-2 text-sm font-bold text-copper mb-1">
            <Target className="w-4 h-4" /> Next Step
          </div>
          <div className="text-ink font-bold">{data.workflows.next_step.step}</div>
          <div className="text-sm text-ink/60 mt-1">{data.workflows.next_step.description}</div>
          <div className="text-xs text-ink/40 mt-2">
            Step {data.workflows.next_step.step_index + 1} of {data.workflows.next_step.total_steps} in &quot;{data.workflows.next_step.workflow}&quot;
          </div>
        </div>
      )}

      {/* Quick actions */}
      <div className="grid md:grid-cols-3 gap-4">
        <Link to="/scholarships/apply" className="card-flat p-5 hover:border-copper/60 transition-all group">
          <Award className="w-6 h-6 text-copper mb-2" />
          <div className="font-bold text-ink group-hover:text-copper transition-colors">Browse Grants</div>
          <p className="text-xs text-ink/50 mt-1">Find funding opportunities for your projects</p>
        </Link>
        <Link to="/donate" className="card-flat p-5 hover:border-copper/60 transition-all group">
          <Heart className="w-6 h-6 text-red-500 mb-2" />
          <div className="font-bold text-ink group-hover:text-copper transition-colors">Start Fundraising</div>
          <p className="text-xs text-ink/50 mt-1">Create campaigns and grow your community</p>
        </Link>
        <Link to="/assistant" className="card-flat p-5 hover:border-copper/60 transition-all group">
          <Bot className="w-6 h-6 text-green-600 mb-2" />
          <div className="font-bold text-ink group-hover:text-copper transition-colors">Admin Assistant</div>
          <p className="text-xs text-ink/50 mt-1">Draft emails, write proposals, organize tasks</p>
        </Link>
      </div>
    </div>
  );
}

function StatCard({ icon: Icon, label, value, color }) {
  return (
    <div className="card-flat p-4">
      <Icon className={`w-5 h-5 ${color} mb-1`} />
      <div className="text-2xl font-bold text-ink">{value}</div>
      <div className="text-xs text-ink/50 font-bold">{label}</div>
    </div>
  );
}

// ── Grants Tab ───────────────────────────────────────────────────────────────

function GrantsTab() {
  const [grants, setGrants] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("");
  const [showForm, setShowForm] = useState(false);

  useEffect(() => {
    api.get("/hub/grants")
      .then(r => setGrants(Array.isArray(r.data) ? r.data : []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const filtered = filter ? grants.filter(g => g.category === filter) : grants;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="font-heading text-xl font-bold text-ink flex items-center gap-2">
          <Award className="w-5 h-5 text-copper" /> Grant Opportunities
        </h2>
        <button onClick={() => setShowForm(!showForm)} className="btn-primary text-sm flex items-center gap-1">
          <Plus className="w-4 h-4" /> Add Grant
        </button>
      </div>

      {showForm && <GrantForm onCreated={(g) => { setGrants(prev => [g, ...prev]); setShowForm(false); }} />}

      {/* Category filter */}
      <div className="flex gap-2 flex-wrap">
        <button onClick={() => setFilter("")} className={`px-3 py-1.5 rounded-full text-xs font-bold ${!filter ? "bg-copper text-white" : "bg-ink/5 text-ink/60"}`}>All</button>
        {GRANT_CATEGORIES.map(c => (
          <button key={c.key} onClick={() => setFilter(c.key)} className={`px-3 py-1.5 rounded-full text-xs font-bold ${filter === c.key ? "bg-copper text-white" : "bg-ink/5 text-ink/60"}`}>{c.label}</button>
        ))}
      </div>

      {loading && <Loader2 className="w-5 h-5 animate-spin text-ink/40" />}
      {!loading && filtered.length === 0 && (
        <div className="card-flat p-10 text-center text-ink/60">
          <Award className="w-8 h-8 mx-auto mb-2 text-ink/30" />
          <p>No grants available yet. Add one to get started.</p>
        </div>
      )}
      <div className="grid md:grid-cols-2 gap-4">
        {filtered.map(g => (
          <GrantCard key={g.id} grant={g} />
        ))}
      </div>
    </div>
  );
}

function GrantCard({ grant }) {
  const [expanded, setExpanded] = useState(false);
  return (
    <div className="card-flat p-5">
      <div className="flex items-start justify-between cursor-pointer" onClick={() => setExpanded(!expanded)}>
        <div>
          <div className="font-bold text-ink">{grant.title}</div>
          <div className="text-xs text-ink/50 mt-1">{grant.source} · {grant.amount || "Amount TBD"}</div>
          {grant.deadline && <div className="text-xs text-amber-600 mt-1 font-bold">Deadline: {grant.deadline}</div>}
        </div>
        {expanded ? <ChevronUp className="w-4 h-4 text-ink/40" /> : <ChevronDown className="w-4 h-4 text-ink/40" />}
      </div>
      {expanded && (
        <div className="mt-4 border-t border-ink/5 pt-4 space-y-3">
          <p className="text-sm text-ink/70">{grant.description}</p>
          {grant.eligibility && (
            <div className="bg-amber-50 rounded-lg p-3 text-xs text-amber-800">
              <strong>Eligibility:</strong> {grant.eligibility}
            </div>
          )}
          {grant.url && (
            <a href={grant.url} target="_blank" rel="noopener noreferrer" className="btn-outline text-sm inline-flex items-center gap-1">
              Visit <ExternalLink className="w-3 h-3" />
            </a>
          )}
        </div>
      )}
    </div>
  );
}

function GrantForm({ onCreated }) {
  const [title, setTitle] = useState("");
  const [source, setSource] = useState("");
  const [amount, setAmount] = useState("");
  const [deadline, setDeadline] = useState("");
  const [description, setDescription] = useState("");
  const [eligibility, setEligibility] = useState("");
  const [url, setUrl] = useState("");
  const [category, setCategory] = useState("general");
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    try {
      const r = await api.post("/hub/grants", { title, source, amount, deadline, description, eligibility, url, category });
      onCreated(r.data);
    } catch (err) { alert(explain(err)); }
    finally { setBusy(false); }
  };

  return (
    <form onSubmit={submit} className="card-flat p-5 space-y-3">
      <h3 className="font-bold text-ink">Add Grant Opportunity</h3>
      <div className="grid md:grid-cols-2 gap-3">
        <input value={title} onChange={e => setTitle(e.target.value)} placeholder="Grant title" className="input-field" required />
        <input value={source} onChange={e => setSource(e.target.value)} placeholder="Source (e.g. SBA, USDA)" className="input-field" required />
        <input value={amount} onChange={e => setAmount(e.target.value)} placeholder="Amount (e.g. $5,000 - $25,000)" className="input-field" />
        <input value={deadline} onChange={e => setDeadline(e.target.value)} placeholder="Deadline" className="input-field" />
        <input value={url} onChange={e => setUrl(e.target.value)} placeholder="URL" className="input-field" />
        <select value={category} onChange={e => setCategory(e.target.value)} className="input-field">
          {GRANT_CATEGORIES.map(c => <option key={c.key} value={c.key}>{c.label}</option>)}
        </select>
      </div>
      <textarea value={description} onChange={e => setDescription(e.target.value)} placeholder="Description" className="input-field h-20" required />
      <textarea value={eligibility} onChange={e => setEligibility(e.target.value)} placeholder="Eligibility requirements" className="input-field h-16" />
      <button type="submit" disabled={busy} className="btn-primary text-sm">
        {busy ? <Loader2 className="w-4 h-4 animate-spin inline" /> : "Save Grant"}
      </button>
    </form>
  );
}

// ── Fundraising Tab ──────────────────────────────────────────────────────────

function FundraisingTab() {
  const [campaigns, setCampaigns] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/hub/campaigns")
      .then(r => setCampaigns(Array.isArray(r.data) ? r.data : []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      <h2 className="font-heading text-xl font-bold text-ink flex items-center gap-2">
        <Heart className="w-5 h-5 text-red-500" /> Fundraising Campaigns
      </h2>

      {loading && <Loader2 className="w-5 h-5 animate-spin text-ink/40" />}
      {!loading && campaigns.length === 0 && (
        <div className="card-flat p-10 text-center text-ink/60">
          <Heart className="w-8 h-8 mx-auto mb-2 text-ink/30" />
          <p>No campaigns yet. Start one or browse scholarship funds.</p>
          <Link to="/donate" className="btn-primary mt-4 inline-flex text-sm">Start Fundraising</Link>
        </div>
      )}
      <div className="grid md:grid-cols-2 gap-4">
        {campaigns.map(c => (
          <div key={c.id} className="card-flat p-5">
            <div className="flex items-start justify-between">
              <div>
                <div className="font-bold text-ink">{c.title}</div>
                <div className="text-xs text-ink/50 mt-1">{c.category} · {c.source || "hub"}</div>
              </div>
              {c.status === "active" && <span className="text-xs font-bold text-green-600 bg-green-100 px-2 py-0.5 rounded-full">Active</span>}
            </div>
            <p className="text-sm text-ink/60 mt-2 line-clamp-2">{c.description}</p>
            {c.goal_amount && (
              <div className="mt-3">
                <div className="text-xs font-bold text-ink/50">Goal: {c.goal_amount} {c.raised_amount ? `· Raised: ${c.raised_amount}` : ""}</div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Resources Tab ────────────────────────────────────────────────────────────

function ResourcesTab() {
  const [resources, setResources] = useState([]);
  const [loading, setLoading] = useState(true);
  const [category, setCategory] = useState("");
  const [q, setQ] = useState("");
  const [showForm, setShowForm] = useState(false);

  useEffect(() => {
    const params = category ? `?category=${category}` : "";
    api.get(`/hub/resources${params}`)
      .then(r => setResources(Array.isArray(r.data) ? r.data : []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [category]);

  const filtered = q.trim()
    ? resources.filter(r => [r.title, r.description, ...r.tags].join(" ").toLowerCase().includes(q.toLowerCase()))
    : resources;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="font-heading text-xl font-bold text-ink flex items-center gap-2">
          <Briefcase className="w-5 h-5 text-green-600" /> Business Resources
        </h2>
        <button onClick={() => setShowForm(!showForm)} className="btn-primary text-sm flex items-center gap-1">
          <Plus className="w-4 h-4" /> Add Resource
        </button>
      </div>

      {showForm && <ResourceForm onCreated={(r) => { setResources(prev => [r, ...prev]); setShowForm(false); }} />}

      {/* Search */}
      <div className="relative">
        <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-ink/40" />
        <input
          value={q}
          onChange={e => setQ(e.target.value)}
          placeholder="Search resources…"
          className="input-field pl-9 w-full"
        />
      </div>

      {/* Category tabs */}
      <div className="flex gap-2 flex-wrap">
        <button onClick={() => setCategory("")} className={`px-3 py-1.5 rounded-full text-xs font-bold ${!category ? "bg-copper text-white" : "bg-ink/5 text-ink/60"}`}>All</button>
        {RESOURCE_CATEGORIES.map(c => {
          const Icon = c.icon;
          return (
            <button key={c.key} onClick={() => setCategory(c.key)} className={`px-3 py-1.5 rounded-full text-xs font-bold flex items-center gap-1 ${category === c.key ? "bg-copper text-white" : "bg-ink/5 text-ink/60"}`}>
              <Icon className="w-3 h-3" /> {c.label}
            </button>
          );
        })}
      </div>

      {loading && <Loader2 className="w-5 h-5 animate-spin text-ink/40" />}
      {!loading && filtered.length === 0 && (
        <div className="card-flat p-10 text-center text-ink/60">
          <Briefcase className="w-8 h-8 mx-auto mb-2 text-ink/30" />
          <p>No resources match.</p>
        </div>
      )}
      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filtered.map(r => (
          <div key={r.id} className="card-flat p-5 hover:border-copper/60 transition-all">
            <div className="flex items-center gap-2 mb-2">
              <span className="px-2 py-0.5 rounded text-xs font-bold bg-ink/5 text-ink/60">{r.category}</span>
            </div>
            <div className="font-bold text-ink text-sm">{r.title}</div>
            <p className="text-xs text-ink/60 mt-1 line-clamp-3">{r.description}</p>
            {r.tags?.length > 0 && (
              <div className="flex gap-1 mt-2 flex-wrap">
                {r.tags.slice(0, 4).map(t => (
                  <span key={t} className="text-[10px] px-1.5 py-0.5 rounded bg-ink/5 text-ink/40">{t}</span>
                ))}
              </div>
            )}
            {r.url && (
              <a href={r.url} target="_blank" rel="noopener noreferrer" className="text-xs text-copper font-bold mt-3 inline-flex items-center gap-1 hover:underline">
                Visit resource <ExternalLink className="w-3 h-3" />
              </a>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function ResourceForm({ onCreated }) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [category, setCategory] = useState("templates");
  const [url, setUrl] = useState("");
  const [tags, setTags] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    try {
      const r = await api.post("/hub/resources", {
        title, description, category, url,
        tags: tags.split(",").map(t => t.trim()).filter(Boolean),
      });
      onCreated(r.data);
    } catch (err) { alert(explain(err)); }
    finally { setBusy(false); }
  };

  return (
    <form onSubmit={submit} className="card-flat p-5 space-y-3">
      <h3 className="font-bold text-ink">Add Business Resource</h3>
      <div className="grid md:grid-cols-2 gap-3">
        <input value={title} onChange={e => setTitle(e.target.value)} placeholder="Resource title" className="input-field" required />
        <select value={category} onChange={e => setCategory(e.target.value)} className="input-field">
          {RESOURCE_CATEGORIES.map(c => <option key={c.key} value={c.key}>{c.label}</option>)}
        </select>
        <input value={url} onChange={e => setUrl(e.target.value)} placeholder="URL (optional)" className="input-field" />
        <input value={tags} onChange={e => setTags(e.target.value)} placeholder="Tags (comma-separated)" className="input-field" />
      </div>
      <textarea value={description} onChange={e => setDescription(e.target.value)} placeholder="Description" className="input-field h-20" required />
      <button type="submit" disabled={busy} className="btn-primary text-sm">
        {busy ? <Loader2 className="w-4 h-4 animate-spin inline" /> : "Save Resource"}
      </button>
    </form>
  );
}

// ── Legal Workflow Tab ──────────────────────────────────────────────────

function LegalWorkflowTab() {
  return (
    <div className="space-y-6">
      <h2 className="font-heading text-xl font-bold text-ink flex items-center gap-2">
        <Scale className="w-5 h-5 text-copper" /> Legal Workflow Engine
      </h2>
      <p className="text-sm text-ink/60">
        Case analysis, evidence checklists, damage calculators, contract review, grant legal readiness,
        IP protection, dispute preparation, attorney consultation packets, and document generation.
      </p>
      <Link to="/legal" className="card-flat p-6 hover:border-copper/60 transition-all block text-center group">
        <Scale className="w-10 h-10 text-copper mx-auto mb-3" />
        <div className="font-bold text-ink group-hover:text-copper transition-colors text-lg">Open Legal Workflows</div>
        <p className="text-sm text-ink/60 mt-1">
          12 workflows · 9 document types · Case analysis · Strategy tree · Nuclear options
        </p>
      </Link>
    </div>
  );
}

// ── Assistant Tab ────────────────────────────────────────────────────────────

function AssistantTab() {
  return (
    <div className="space-y-6">
      <h2 className="font-heading text-xl font-bold text-ink flex items-center gap-2">
        <Bot className="w-5 h-5 text-green-600" /> Admin Assistant
      </h2>
      <p className="text-sm text-ink/60">
        Draft emails, write proposals, organize tasks, and build business strategy. The assistant can help with
        grant applications, fundraising campaigns, and resource research.
      </p>
      <Link to="/assistant" className="card-flat p-6 hover:border-copper/60 transition-all block text-center group">
        <Bot className="w-10 h-10 text-green-600 mx-auto mb-3" />
        <div className="font-bold text-ink group-hover:text-copper transition-colors text-lg">Open Admin Assistant</div>
        <p className="text-sm text-ink/60 mt-1">
          Draft emails · Write proposals · Organize tasks · Business strategy
        </p>
      </Link>
    </div>
  );
}
