/**
 * /resources → Legal tab — Legal Workflow Engine
 *
 * Hypothetical Lawyer v3.0 converted to React.
 * ALL existing functionality preserved: Case Type, Strategy, Evidence,
 * Calculator, Document Generator, Protection, Nuclear Options.
 *
 * 12 NEW enhancements added as workflows:
 * 1. Resource Hub bridge
 * 2. Legal Issue Navigator
 * 3. Legal Readiness Workflow
 * 4. Contract Workflow
 * 5. Grant Legal Readiness
 * 6. Fundraising Compliance
 * 7. Business Legal Setup
 * 8. Intellectual Property Workflow
 * 9. Employment/Contractor Workflow
 * 10. Dispute Preparation
 * 11. Attorney Preparation Packet
 * 12. Extended Document Generator
 */

import { useState, useCallback, useMemo, useRef, useEffect } from "react";
import { Link } from "react-router-dom";
import {
  Scale, Shield, Target, FileText, Calculator, Zap, Swords,
  ChevronRight, ChevronDown, ChevronUp, CheckCircle2, Circle,
  AlertTriangle, BookOpen, Briefcase, Heart, DollarSign, Award,
  Users, Lightbulb, Search, ArrowRight, Download, Printer,
  Clock, TrendingUp, Star, Gavel, Landmark, ShieldCheck, Lock,
  Mail, Phone, MapPin, Plus, Trash2, Eye, EyeOff, Copy, Check,
  Layers, Flag, Flame, Compass, Link as LinkIcon, Rocket,
  UserCheck, FileCheck, FolderOpen, ScrollText, ClipboardList,
  PenTool, ShieldAlert, FileWarning, Handshake, Building2, Globe,
} from "lucide-react";

/* ═══════════════════════════════════════════════════════════════════════════
   CONSTANTS
   ═══════════════════════════════════════════════════════════════════════════ */

const LEGAL_NAV_OPTIONS = [
  { key: "business", label: "Start a Business", icon: Building2 },
  { key: "contract", label: "Review a Contract", icon: FileText },
  { key: "grant", label: "Apply for a Grant", icon: Award },
  { key: "fundraise", label: "Raise Money", icon: DollarSign },
  { key: "hire", label: "Hire Someone", icon: Users },
  { key: "ip", label: "Protect Intellectual Property", icon: Shield },
  { key: "dispute", label: "Deal with a Dispute", icon: Swords },
  { key: "legal_notice", label: "Respond to a Legal Notice", icon: AlertTriangle },
  { key: "attorney", label: "Prepare for an Attorney", icon: Gavel },
  { key: "protect_org", label: "Protect an Organization", icon: ShieldCheck },
  { key: "other", label: "Other", icon: HelpCircle },
];

const READINESS_CATEGORIES = [
  { key: "entity", label: "Business/Entity Documents", icon: Building2 },
  { key: "contracts", label: "Contracts", icon: FileText },
  { key: "ownership", label: "Ownership", icon: UserCheck },
  { key: "ip", label: "Intellectual Property", icon: Shield },
  { key: "employment", label: "Employment/Contractors", icon: Users },
  { key: "licenses", label: "Licenses and Permits", icon: ClipboardList },
  { key: "compliance", label: "Compliance", icon: CheckCircle2 },
  { key: "insurance", label: "Insurance", icon: ShieldCheck },
  { key: "privacy", label: "Privacy/Website Documents", icon: Lock },
  { key: "records", label: "Records/Evidence", icon: FolderOpen },
];

const CONTRACT_TYPES = [
  { key: "client", label: "Client Agreement" },
  { key: "contractor", label: "Contractor Agreement" },
  { key: "partnership", label: "Partnership Agreement" },
  { key: "nda", label: "NDA" },
  { key: "vendor", label: "Vendor Agreement" },
  { key: "lease", label: "Lease" },
  { key: "licensing", label: "Licensing Agreement" },
  { key: "other", label: "Other" },
];

const FUNDRAISING_ACTIVITIES = [
  { key: "donation", label: "Donation Campaign" },
  { key: "crowdfunding", label: "Crowdfunding" },
  { key: "sponsorship", label: "Sponsorship" },
  { key: "event", label: "Event" },
  { key: "scholarship", label: "Scholarship Fund" },
  { key: "online", label: "Online Fundraising" },
  { key: "business", label: "Business Fundraising" },
];

const IP_TYPES = [
  { key: "book", label: "Book" },
  { key: "music", label: "Music" },
  { key: "artwork", label: "Artwork" },
  { key: "logo", label: "Logo" },
  { key: "brand", label: "Brand" },
  { key: "course", label: "Course" },
  { key: "video", label: "Video" },
  { key: "software", label: "Software" },
  { key: "website", label: "Website Content" },
  { key: "other", label: "Other" },
];

const EVIDENCE_ITEMS = [
  { key: "emails", label: "Emails / Texts from Boss", desc: "\"Tone it down.\" \"Be more assertive.\" Retaliation proof." },
  { key: "reviews", label: "Performance Reviews", desc: "\"Exceeds Expectations\" while white colleague got \"Meets\" and the promotion." },
  { key: "paystubs", label: "Pay Stubs (Side by Side)", desc: "You make $X. White coworker same title makes $X+$15K. Title VII proof." },
  { key: "bodycam", label: "Traffic Stop Records", desc: "4 stops. 0 violations. 2 searches. Dashcam/bodycam footage." },
  { key: "housing", label: "Housing Denial Letters", desc: "6 denials. Different excuses each time. White friend approved next day." },
  { key: "loan", label: "Loan Rate Comparison", desc: "Same credit score. 8.5% for you. 3.2% for white guy. $4,200 overcharge." },
  { key: "medical", label: "Medical Records", desc: "Blood pressure 160/100. Doctor notes \"chronic stress — occupational.\"" },
  { key: "termination", label: "Termination Letter", desc: "\"No cause\" RIF. But the position still exists — filled by someone else." },
  { key: "social", label: "Social Media Evidence", desc: "Screenshots of discriminatory posts by coworkers." },
  { key: "foia", label: "FOIA Responses", desc: "Requested your personnel file. They sent it. It shows the pattern." },
  { key: "witnesses", label: "Witnesses", desc: "Coworkers who saw the double standard. Names and contact info." },
  { key: "stats", label: "Statistical Evidence", desc: "75% purge rate. Four-Fifths violation. Regression analysis." },
];

const CASE_TYPES = [
  { key: "A", label: "Federal Employment", icon: Landmark, desc: "Fired/demoted from government job. RIF'd. \"Restructured.\"" },
  { key: "B", label: "Housing Discrimination", icon: MapPin, desc: "Denied rent. Redlined. Overcharged. Evicted unfairly." },
  { key: "C", label: "Criminal Justice", icon: Shield, desc: "Arrested. Stopped. Sentenced unfairly. Police brutality." },
  { key: "D", label: "Consumer Fraud", icon: DollarSign, desc: "Tariff scam. Algorithmic bias. Insurance discrimination." },
  { key: "E", label: "All of Them", icon: Zap, desc: "Universal mode. Every weapon. Auto-detects your path." },
];

function HelpCircle(props) {
  return <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><path d="M12 17h.01"/></svg>;
}

/* ═══════════════════════════════════════════════════════════════════════════
   HELPER — localStorage persistence
   ═══════════════════════════════════════════════════════════════════════════ */

function useLegalSave(key, initial) {
  const [state, setState] = useState(() => {
    try {
      const saved = localStorage.getItem(`hl_${key}`);
      return saved ? JSON.parse(saved) : initial;
    } catch { return initial; }
  });
  useEffect(() => {
    try { localStorage.setItem(`hl_${key}`, JSON.stringify(state)); } catch {}
  }, [key, state]);
  return [state, setState];
}

/* ═══════════════════════════════════════════════════════════════════════════
   MAIN COMPONENT
   ═══════════════════════════════════════════════════════════════════════════ */

const LEGAL_TABS = [
  { id: "home", label: "Home", icon: Scale },
  { id: "navigator", label: "Legal Navigator", icon: Compass },
  { id: "readiness", label: "Legal Readiness", icon: ClipboardList },
  { id: "casetype", label: "Case Type", icon: FileText },
  { id: "strategy", label: "Strategy", icon: Target },
  { id: "evidence", label: "Evidence", icon: FolderOpen },
  { id: "calculator", label: "Calculator", icon: Calculator },
  { id: "contracts", label: "Contracts", icon: Handshake },
  { id: "grants_legal", label: "Grant Legal", icon: Award },
  { id: "fundraise_compliance", label: "Fundraise Legal", icon: Heart },
  { id: "business_setup", label: "Business Setup", icon: Building2 },
  { id: "ip", label: "IP Protection", icon: Shield },
  { id: "employment", label: "Employment", icon: Users },
  { id: "dispute", label: "Dispute Prep", icon: Swords },
  { id: "attorney", label: "Attorney Prep", icon: Gavel },
  { id: "generator", label: "Documents", icon: PenTool },
  { id: "protect", label: "Protection", icon: ShieldCheck },
  { id: "nuclear", label: "Nuclear", icon: Flame },
  { id: "hub", label: "Resource Hub", icon: LinkIcon },
];

export default function LegalWorkflows() {
  const [tab, setTab] = useLegalSave("active_tab", "home");
  const [savedIndicator, setSavedIndicator] = useState(false);

  const showSave = useCallback(() => {
    setSavedIndicator(true);
    setTimeout(() => setSavedIndicator(false), 2000);
  }, []);

  return (
    <div className="min-h-screen bg-[#0a0a0a]">
      {/* Header */}
      <div className="bg-gradient-to-r from-[#0f3460] to-[#e94560] px-4 py-5 text-center border-b-2 border-[#ffd700] sticky top-0 z-50">
        <h1 className="text-[#ffd700] text-xl md:text-2xl font-bold uppercase tracking-widest">
          ⚖️ Hypothetical Lawyer — Legal Workflow Engine
        </h1>
        <p className="text-[#a0a0a0] text-xs mt-1">
          Pro Bono — Zero Cost — 100% To The Victims — Every Dollar To The Reparations Trust
        </p>
      </div>

      {/* Nav bar */}
      <div className="bg-[#1a1a2e] border-b border-[#0f3460] px-2 py-2 overflow-x-auto">
        <div className="flex gap-1 min-w-max justify-center">
          {LEGAL_TABS.map(t => {
            const Icon = t.icon;
            return (
              <button
                key={t.id}
                onClick={() => setTab(t.id)}
                className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-[11px] font-bold uppercase tracking-wider transition-all whitespace-nowrap ${
                  tab === t.id
                    ? "bg-[#e94560] text-white shadow-lg shadow-[#e94560]/30"
                    : "bg-[#16213e] text-[#a0a0a0] hover:bg-[#0f3460] hover:text-white"
                }`}
              >
                <Icon className="w-3.5 h-3.5" /> {t.label}
              </button>
            );
          })}
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-4 py-6">
        {tab === "home" && <LegalHome setTab={setTab} />}
        {tab === "navigator" && <LegalNavigator setTab={setTab} />}
        {tab === "readiness" && <LegalReadiness showSave={showSave} />}
        {tab === "casetype" && <CaseTypeSection showSave={showSave} />}
        {tab === "strategy" && <StrategySection />}
        {tab === "evidence" && <EvidenceSection showSave={showSave} />}
        {tab === "calculator" && <CalculatorSection />}
        {tab === "contracts" && <ContractWorkflow showSave={showSave} />}
        {tab === "grants_legal" && <GrantLegalReadiness />}
        {tab === "fundraise_compliance" && <FundraiseCompliance />}
        {tab === "business_setup" && <BusinessLegalSetup />}
        {tab === "ip" && <IPWorkflow />}
        {tab === "employment" && <EmploymentWorkflow />}
        {tab === "dispute" && <DisputePrep />}
        {tab === "attorney" && <AttorneyPrepPacket />}
        {tab === "generator" && <DocumentGenerator />}
        {tab === "protect" && <ProtectionSection />}
        {tab === "nuclear" && <NuclearSection />}
        {tab === "hub" && <ResourceHubBridge />}
      </div>

      {/* Save indicator */}
      {savedIndicator && (
        <div className="fixed bottom-5 right-5 bg-green-600 text-white px-4 py-2 rounded-xl font-bold z-50 animate-pulse">
          ✅ PROGRESS SAVED
        </div>
      )}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   1. HOME
   ═══════════════════════════════════════════════════════════════════════════ */

function LegalHome({ setTab }) {
  return (
    <div className="space-y-6">
      <div className="bg-[#1a1a2e] border border-[#0f3460] rounded-2xl p-6">
        <h2 className="text-[#ffd700] text-lg font-bold uppercase tracking-wider border-b border-[#e94560] pb-3 mb-4">
          🚨 WELCOME — THIS IS YOUR WEAPON
        </h2>
        <p className="text-[#a0a0a0] text-sm leading-relaxed mb-3">
          You're not just suing for what happened to you. You're suing for every person who lives like this every single day.
          Every traffic stop. Every denied promotion. Every apartment you couldn't rent. Every loan that cost more.
        </p>
        <p className="text-[#eaeaea] text-sm font-bold mb-3">
          The law is on your side. The data is on your side. The history is on your side.
        </p>
        <p className="text-[#a0a0a0] text-sm leading-relaxed">
          This tool gives you EVERYTHING: strategy, evidence checklists, damage calculators, document generators,
          legal readiness workflows, contract review, grant compliance, and nuclear options.{" "}
          <strong className="text-green-400">Everything works offline. Zero internet needed. Save your progress.</strong>
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          { n: "12", l: "Legal Workflows" },
          { n: "9", l: "Document Types" },
          { n: "6", l: "Causes of Action" },
          { n: "10", l: "Readiness Areas" },
        ].map(s => (
          <div key={s.l} className="bg-[#16213e] border border-[#0f3460] rounded-xl p-4 text-center">
            <div className="text-[#ffd700] text-xl font-bold">{s.n}</div>
            <div className="text-[#a0a0a0] text-xs mt-1">{s.l}</div>
          </div>
        ))}
      </div>

      {/* Quick actions */}
      <div className="grid md:grid-cols-3 gap-4">
        <button onClick={() => setTab("navigator")} className="bg-gradient-to-br from-[#e94560] to-[#0f3460] text-white border-none rounded-xl p-5 font-bold uppercase tracking-wider text-sm hover:scale-105 transition-transform shadow-lg">
          🚀 START HERE — Legal Navigator
        </button>
        <button onClick={() => setTab("calculator")} className="bg-gradient-to-br from-green-600 to-green-800 text-white border-none rounded-xl p-5 font-bold uppercase tracking-wider text-sm hover:scale-105 transition-transform">
          💰 CALCULATE YOUR DAMAGES
        </button>
        <button onClick={() => setTab("generator")} className="bg-gradient-to-br from-blue-600 to-blue-800 text-white border-none rounded-xl p-5 font-bold uppercase tracking-wider text-sm hover:scale-105 transition-transform">
          📝 GENERATE DOCUMENTS
        </button>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   2. LEGAL ISSUE NAVIGATOR
   ═══════════════════════════════════════════════════════════════════════════ */

function LegalNavigator({ setTab }) {
  const [selected, setSelected] = useState(null);

  const ROUTES = {
    business: "business_setup",
    contract: "contracts",
    grant: "grants_legal",
    fundraise: "fundraise_compliance",
    hire: "employment",
    ip: "ip",
    dispute: "dispute",
    legal_notice: "dispute",
    attorney: "attorney",
    protect_org: "readiness",
    other: "casetype",
  };

  return (
    <div className="space-y-6">
      <div className="bg-[#1a1a2e] border border-[#0f3460] rounded-2xl p-6">
        <h2 className="text-[#ffd700] text-lg font-bold uppercase tracking-wider border-b border-[#e94560] pb-3 mb-4">
          🧭 LEGAL ISSUE NAVIGATOR
        </h2>
        <p className="text-[#a0a0a0] text-sm mb-4">What are you trying to accomplish?</p>

        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {LEGAL_NAV_OPTIONS.map(opt => {
            const Icon = opt.icon;
            const active = selected === opt.key;
            return (
              <button
                key={opt.key}
                onClick={() => setSelected(opt.key)}
                className={`bg-[#16213e] border-2 rounded-xl p-4 text-left transition-all cursor-pointer hover:border-[#e94560] ${
                  active ? "border-[#ffd700] bg-[#ffd700]/10" : "border-[#0f3460]"
                }`}
              >
                <Icon className={`w-5 h-5 mb-2 ${active ? "text-[#ffd700]" : "text-[#e94560]"}`} />
                <div className="text-[#eaeaea] text-sm font-bold">{opt.label}</div>
              </button>
            );
          })}
        </div>

        {selected && (
          <div className="mt-6 bg-[#16213e] border border-green-500 rounded-xl p-5 text-center">
            <p className="text-green-400 font-bold mb-3">Recommended workflow: {LEGAL_NAV_OPTIONS.find(o => o.key === selected)?.label}</p>
            <button
              onClick={() => setTab(ROUTES[selected] || "casetype")}
              className="bg-gradient-to-r from-[#e94560] to-[#0f3460] text-white px-6 py-3 rounded-xl font-bold uppercase tracking-wider hover:scale-105 transition-transform"
            >
              Go to Workflow →
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   3. LEGAL READINESS WORKFLOW
   ═══════════════════════════════════════════════════════════════════════════ */

function LegalReadiness({ showSave }) {
  const [checks, setChecks] = useLegalSave("readiness", {});

  const toggle = (cat, item) => {
    setChecks(prev => {
      const next = { ...prev };
      const key = `${cat}:${item}`;
      next[key] = !next[key];
      return next;
    });
    showSave();
  };

  const items = {
    entity: ["Articles of Incorporation / LLC Operating Agreement", "EIN Letter", "Board Resolution / Operating Agreement", "Registered Agent Documentation"],
    contracts: ["Client agreements signed", "Vendor agreements signed", "Contractor agreements signed", "NDA templates ready"],
    ownership: ["Ownership documentation (stock certificates, membership units)", "Shareholder/Member agreement", "Cap table current"],
    ip: ["Trademark applications filed", "Copyright registrations", "Patent searches complete", "IP assignment agreements signed"],
    employment: ["Employment agreements for all staff", "Independent contractor agreements", "Non-compete/non-solicitation agreements", "I-9 verification complete"],
    licenses: ["Business license current", "Professional licenses current", "Industry-specific permits", "Zoning compliance verified"],
    compliance: ["Annual report filed", "Tax filings current", "Regulatory compliance audit complete", "ADA compliance verified"],
    insurance: ["General liability insurance", "Professional liability insurance", "Workers' compensation", "Cyber liability insurance"],
    privacy: ["Privacy policy published", "Terms of service published", "Cookie consent mechanism", "Data processing agreements"],
    records: ["Financial records organized", "Meeting minutes documented", "Key correspondence archived", "Evidence preservation started"],
  };

  const total = Object.values(items).flat().length;
  const done = Object.values(checks).filter(Boolean).length;
  const pct = total > 0 ? Math.round((done / total) * 100) : 0;

  return (
    <div className="space-y-6">
      <div className="bg-[#1a1a2e] border border-[#0f3460] rounded-2xl p-6">
        <h2 className="text-[#ffd700] text-lg font-bold uppercase tracking-wider border-b border-[#e94560] pb-3 mb-4">
          📋 LEGAL READINESS WORKFLOW
        </h2>

        {/* Progress bar */}
        <div className="bg-[#16213e] rounded-full h-6 overflow-hidden mb-3">
          <div
            className="h-full bg-gradient-to-r from-[#e94560] to-[#ffd700] rounded-full flex items-center justify-center text-[11px] font-bold text-black transition-all"
            style={{ width: `${pct}%` }}
          >
            {pct}%
          </div>
        </div>
        <p className="text-center text-[#ffd700] font-bold text-sm">{done} of {total} items complete</p>

        <div className="mt-6 space-y-4">
          {READINESS_CATEGORIES.map(cat => {
            const catItems = items[cat.key] || [];
            const catDone = catItems.filter((_, i) => checks[`${cat.key}:${i}`]).length;
            const CatIcon = cat.icon;
            return (
              <div key={cat.key} className="bg-[#16213e] border border-[#0f3460] rounded-xl p-4">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <CatIcon className="w-4 h-4 text-[#e94560]" />
                    <span className="text-[#eaeaea] font-bold text-sm">{cat.label}</span>
                  </div>
                  <span className="text-xs text-[#a0a0a0]">{catDone}/{catItems.length}</span>
                </div>
                <div className="space-y-2">
                  {catItems.map((item, i) => {
                    const checked = !!checks[`${cat.key}:${i}`];
                    return (
                      <button
                        key={i}
                        onClick={() => toggle(cat.key, i)}
                        className="w-full flex items-start gap-3 text-left p-2 rounded-lg hover:bg-[#0f3460]/30 transition-colors"
                      >
                        {checked ? (
                          <CheckCircle2 className="w-5 h-5 text-green-400 flex-shrink-0 mt-0.5" />
                        ) : (
                          <Circle className="w-5 h-5 text-[#0f3460] flex-shrink-0 mt-0.5" />
                        )}
                        <span className={`text-xs ${checked ? "text-green-400 line-through" : "text-[#a0a0a0]"}`}>{item}</span>
                      </button>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   4. CASE TYPE (existing functionality preserved)
   ═══════════════════════════════════════════════════════════════════════════ */

function CaseTypeSection({ showSave }) {
  const [selectedCase, setSelectedCase] = useState("");
  const [caseData, setCaseData] = useLegalSave("case", { name: "", facts: "", target: "", date: "", proof: [] });
  const [result, setResult] = useState(null);

  const processCase = () => {
    if (!caseData.facts) { alert("Please describe what happened to you."); return; }
    const causes = [];
    let damages = "";
    if (selectedCase === "A" || selectedCase === "E") {
      causes.push("Title VII Disparate Treatment (42 U.S.C. § 2000e-2)");
      causes.push("CSRA Prohibited Personnel Practice (5 U.S.C. § 2302(b))");
      causes.push("42 U.S.C. § 1985(3) Conspiracy");
    }
    if (selectedCase === "B" || selectedCase === "E") {
      causes.push("Fair Housing Act (42 U.S.C. § 3604)");
      causes.push("Disparate Impact under Inclusive Communities");
    }
    if (selectedCase === "C" || selectedCase === "E") {
      causes.push("42 U.S.C. § 1983 — 4th Amendment Violation");
      causes.push("Qualified Immunity Challenge (Malley v. Briggs)");
    }
    if (selectedCase === "D" || selectedCase === "E") {
      causes.push("State UDAAP Consumer Fraud");
      causes.push("Tariff Refund Scheme (166B)");
    }
    setResult({ caseType: selectedCase, ...caseData, causes, damages });
    showSave();
  };

  return (
    <div className="space-y-6">
      <div className="bg-[#1a1a2e] border border-[#0f3460] rounded-2xl p-6">
        <h2 className="text-[#ffd700] text-lg font-bold uppercase tracking-wider border-b border-[#e94560] pb-3 mb-4">
          📋 SELECT YOUR CASE TYPE
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {CASE_TYPES.map(ct => {
            const Icon = ct.icon;
            return (
              <button key={ct.key} onClick={() => { setSelectedCase(ct.key); setResult(null); }}
                className={`bg-[#16213e] border-2 rounded-xl p-4 text-left transition-all hover:border-[#e94560] ${
                  selectedCase === ct.key ? "border-[#ffd700] bg-[#ffd700]/10" : "border-[#0f3460]"
                }`}>
                <Icon className={`w-5 h-5 mb-2 ${selectedCase === ct.key ? "text-[#ffd700]" : "text-[#e94560]"}`} />
                <div className="text-[#eaeaea] text-sm font-bold">{ct.label}</div>
                <p className="text-[#a0a0a0] text-xs mt-1">{ct.desc}</p>
              </button>
            );
          })}
        </div>

        {selectedCase && (
          <div className="mt-6 space-y-4">
            <InputField label="Your Name (or 'Anonymous')" value={caseData.name} onChange={v => setCaseData(p => ({...p, name: v}))} placeholder="Enter name or 'Anonymous'" />
            <InputField label="What Happened To You?" textarea value={caseData.facts} onChange={v => setCaseData(p => ({...p, facts: v}))} placeholder="Describe in plain English..." />
            <InputField label="Agency / Company / Landlord Name" value={caseData.target} onChange={v => setCaseData(p => ({...p, target: v}))} />
            <InputField label="Date It Happened" type="date" value={caseData.date} onChange={v => setCaseData(p => ({...p, date: v}))} />
            <button onClick={processCase} className="bg-gradient-to-r from-green-600 to-green-800 text-white px-6 py-3 rounded-xl font-bold uppercase tracking-wider text-sm hover:scale-105 transition-transform">
              ⚡ ANALYZE MY CASE
            </button>
          </div>
        )}

        {result && (
          <div className="mt-6 bg-[#16213e] border-2 border-green-500 rounded-xl p-5">
            <h3 className="text-green-400 font-bold mb-3">✅ CASE ANALYSIS COMPLETE</h3>
            <div className="text-[#a0a0a0] text-sm space-y-2">
              <p><strong className="text-[#eaeaea]">Case Type:</strong> {result.caseType}</p>
              <p><strong className="text-[#eaeaea]">Plaintiff:</strong> {result.name || "Anonymous"}</p>
              <p><strong className="text-[#eaeaea]">Defendant:</strong> {result.target || "Unknown"}</p>
              <p className="mt-3 text-green-400 font-bold">CAUSES OF ACTION:</p>
              <ul className="list-disc pl-5 space-y-1">{result.causes.map((c, i) => <li key={i}>{c}</li>)}</ul>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   5. STRATEGY (existing functionality preserved)
   ═══════════════════════════════════════════════════════════════════════════ */

function StrategySection() {
  const steps = [
    { title: "STEP 1: ADMINISTRATIVE EXHAUSTION (Days 1-45)", color: "border-blue-500", content: "File EEOC Intake + MSPB Appeal simultaneously. This forces their hand. They MUST respond or you auto-win the right to sue." },
    { title: "STEP 2: JOIN THE CLASS (Days 15-30)", color: "border-green-500", content: "File Motion to Intervene in the class action. You disappear into thousands of names. They can't target what they can't find." },
    { title: "STEP 3: DISCOVERY — FORCE THEM TO TALK (Days 30-90)", color: "border-[#ffd700]", content: "Serve Interrogatories. Demand the roster. Demand the algorithm. Demand the emails. They WILL try to hide — that hiding IS the evidence." },
    { title: "STEP 4: DEFEAT EVERY DEFENSE (Ongoing)", color: "border-[#e94560]", content: "They'll use 5 defenses. Here's how you kill each one: Unitary Executive, Partisan Changeover, Anti-Discrimination Restorative, Failure to Exhaust, Inferior Officers." },
    { title: "STEP 5: TRIAL — JURY INSTRUCTIONS THAT WIN", color: "border-[#e94560]", content: "Don't let them confuse the jury. Use targeted jury instructions about policy effects, statistical evidence, and pretext." },
    { title: "STEP 6: JUDGMENT & REPARATIONS", color: "border-[#ffd700]", content: "When you win, every dollar goes to the Class Civil Rights Reparations Trust. 85% to victims. 15% to fund the NEXT case." },
  ];

  return (
    <div className="space-y-6">
      <div className="bg-[#1a1a2e] border border-[#0f3460] rounded-2xl p-6">
        <h2 className="text-[#ffd700] text-lg font-bold uppercase tracking-wider border-b border-[#e94560] pb-3 mb-4">
          🎯 WINNING STRATEGY TREE
        </h2>
        <div className="space-y-3">
          {steps.map((step, i) => (
            <StrategyNode key={i} step={step} />
          ))}
        </div>
      </div>
    </div>
  );
}

function StrategyNode({ step }) {
  const [open, setOpen] = useState(false);
  return (
    <div className={`bg-[#16213e] border-l-4 ${step.color} rounded-r-xl p-4 cursor-pointer hover:bg-[#0f3460]/50 transition-colors`} onClick={() => setOpen(!open)}>
      <div className="flex items-center justify-between">
        <h4 className="text-[#eaeaea] text-sm font-bold">{step.title}</h4>
        {open ? <ChevronUp className="w-4 h-4 text-[#a0a0a0]" /> : <ChevronDown className="w-4 h-4 text-[#a0a0a0]" />}
      </div>
      {open && <p className="text-[#a0a0a0] text-xs mt-3 pl-4 border-l-2 border-[#0f3460]">{step.content}</p>}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   6. EVIDENCE CHECKLIST (existing functionality preserved)
   ═══════════════════════════════════════════════════════════════════════════ */

function EvidenceSection({ showSave }) {
  const [checked, setChecked] = useLegalSave("evidence", {});

  const toggle = (key) => {
    setChecked(prev => ({ ...prev, [key]: !prev[key] }));
    showSave();
  };

  const total = EVIDENCE_ITEMS.length;
  const done = EVIDENCE_ITEMS.filter(e => checked[e.key]).length;
  const pct = total > 0 ? Math.round((done / total) * 100) : 0;

  return (
    <div className="space-y-6">
      <div className="bg-[#1a1a2e] border border-[#0f3460] rounded-2xl p-6">
        <h2 className="text-[#ffd700] text-lg font-bold uppercase tracking-wider border-b border-[#e94560] pb-3 mb-4">
          📁 EVIDENCE CHECKLIST
        </h2>
        <p className="text-[#a0a0a0] text-sm mb-4">Every checkmark makes your case stronger. Save your progress.</p>

        <div className="bg-[#16213e] rounded-full h-5 overflow-hidden mb-3">
          <div className="h-full bg-gradient-to-r from-[#e94560] to-green-400 rounded-full flex items-center justify-center text-[10px] font-bold text-black transition-all" style={{ width: `${pct}%` }}>
            {pct}%
          </div>
        </div>
        <p className="text-center text-[#ffd700] font-bold text-sm mb-4">{done} of {total} pieces collected</p>

        <div className="grid md:grid-cols-2 gap-3">
          {EVIDENCE_ITEMS.map(item => {
            const active = !!checked[item.key];
            return (
              <button key={item.key} onClick={() => toggle(item.key)}
                className={`flex items-start gap-3 p-4 rounded-xl border-2 text-left transition-all ${
                  active ? "border-green-500 bg-green-500/10" : "border-[#0f3460] bg-[#16213e] hover:border-[#e94560]"
                }`}>
                <div className={`w-7 h-7 rounded-full border-2 flex items-center justify-center flex-shrink-0 text-sm ${
                  active ? "bg-green-500 border-green-500 text-white" : "border-[#0f3460] text-transparent"
                }`}>{active ? "✓" : "☐"}</div>
                <div>
                  <div className={`text-sm font-bold ${active ? "text-green-400" : "text-[#eaeaea]"}`}>{item.label}</div>
                  <p className="text-[11px] text-[#a0a0a0] mt-1">{item.desc}</p>
                </div>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   7. CALCULATOR (existing functionality preserved)
   ═══════════════════════════════════════════════════════════════════════════ */

function CalculatorSection() {
  const [fields, setFields] = useState({ salary: "", years: "", retire: "", current: "", loan: "", housing: "", emotional: "" });

  const update = (k, v) => setFields(p => ({ ...p, [k]: v }));

  const salary = parseFloat(fields.salary) || 0;
  const years = parseFloat(fields.years) || 0;
  const retire = parseFloat(fields.retire) || 0;
  const current = parseFloat(fields.current) || 0;
  const loan = parseFloat(fields.loan) || 0;
  const housing = parseFloat(fields.housing) || 0;
  const emotional = parseFloat(fields.emotional) || 0;

  const backPay = (salary - current) * years;
  const frontPay = salary * retire;
  const pensionLoss = salary * 0.01 * 1.1 * years * 12;
  const tspLoss = salary * 0.05 * years * 1.07;
  const total = backPay + frontPay + pensionLoss + tspLoss + loan + housing + emotional;

  const fmt = (n) => "$" + n.toLocaleString("en-US", { maximumFractionDigits: 0 });

  return (
    <div className="space-y-6">
      <div className="bg-[#1a1a2e] border border-[#0f3460] rounded-2xl p-6">
        <h2 className="text-[#ffd700] text-lg font-bold uppercase tracking-wider border-b border-[#e94560] pb-3 mb-4">
          📊 DAMAGES CALCULATOR
        </h2>

        <div className="grid md:grid-cols-2 gap-4">
          <InputField label="Your Annual Salary" type="number" value={fields.salary} onChange={v => update("salary", v)} placeholder="e.g. 85000" />
          <InputField label="Years of Employment" type="number" value={fields.years} onChange={v => update("years", v)} placeholder="e.g. 10" />
          <InputField label="Years Until Retirement" type="number" value={fields.retire} onChange={v => update("retire", v)} placeholder="e.g. 20" />
          <InputField label="Current Salary" type="number" value={fields.current} onChange={v => update("current", v)} placeholder="e.g. 45000" />
          <InputField label="Loan Interest Overcharge ($)" type="number" value={fields.loan} onChange={v => update("loan", v)} placeholder="e.g. 4200" />
          <InputField label="Housing Overcharges ($)" type="number" value={fields.housing} onChange={v => update("housing", v)} placeholder="e.g. 24000" />
          <InputField label="Emotional Distress" type="number" value={fields.emotional} onChange={v => update("emotional", v)} placeholder="e.g. 50000" />
        </div>

        {total > 0 && (
          <div className="mt-6 bg-[#16213e] border-2 border-green-500 rounded-xl p-5 text-center">
            <h3 className="text-green-400 font-bold mb-2">💰 YOUR TOTAL RECOVERY ESTIMATE</h3>
            <div className="text-[#ffd700] text-3xl font-bold">{fmt(total)}</div>
            <div className="grid grid-cols-3 md:grid-cols-6 gap-2 mt-4">
              {[
                { v: backPay, l: "Back Pay", c: "text-green-400" },
                { v: frontPay, l: "Front Pay", c: "text-blue-400" },
                { v: pensionLoss, l: "Pension", c: "text-[#ffd700]" },
                { v: tspLoss, l: "TSP Loss", c: "text-[#e94560]" },
                { v: loan + housing, l: "Overcharges", c: "text-red-400" },
                { v: emotional, l: "Emotional", c: "text-purple-400" },
              ].map(d => (
                <div key={d.l} className="bg-[#1a1a2e] rounded-lg p-2">
                  <div className={`font-bold text-xs ${d.c}`}>{fmt(d.v)}</div>
                  <div className="text-[10px] text-[#a0a0a0]">{d.l}</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   8. CONTRACT WORKFLOW
   ═══════════════════════════════════════════════════════════════════════════ */

function ContractWorkflow({ showSave }) {
  const [contractType, setContractType] = useState("");
  const [step, setStep] = useState(0);
  const [data, setData] = useState({ parties: "", purpose: "", terms: "", concerns: "" });

  const steps = ["Identify Contract Type", "Gather Information", "Review Key Terms", "Flag Questions", "Prepare Next Steps"];

  return (
    <div className="space-y-6">
      <div className="bg-[#1a1a2e] border border-[#0f3460] rounded-2xl p-6">
        <h2 className="text-[#ffd700] text-lg font-bold uppercase tracking-wider border-b border-[#e94560] pb-3 mb-4">
          🤝 CONTRACT WORKFLOW
        </h2>

        {/* Step indicator */}
        <div className="flex items-center gap-1 mb-6 overflow-x-auto pb-2">
          {steps.map((s, i) => (
            <div key={i} className="flex items-center">
              <div className={`px-3 py-1.5 rounded-full text-xs font-bold whitespace-nowrap ${
                i <= step ? "bg-[#e94560] text-white" : "bg-[#16213e] text-[#a0a0a0]"
              }`}>{s}</div>
              {i < steps.length - 1 && <ChevronRight className="w-3 h-3 text-[#a0a0a0] mx-1" />}
            </div>
          ))}
        </div>

        {step === 0 && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {CONTRACT_TYPES.map(ct => (
              <button key={ct.key} onClick={() => { setContractType(ct.key); setStep(1); }}
                className={`bg-[#16213e] border-2 rounded-xl p-4 text-left transition-all hover:border-[#e94560] ${
                  contractType === ct.key ? "border-[#ffd700]" : "border-[#0f3460]"
                }`}>
                <div className="text-[#eaeaea] text-sm font-bold">{ct.label}</div>
              </button>
            ))}
          </div>
        )}

        {step === 1 && (
          <div className="space-y-4">
            <InputField label="Parties Involved" value={data.parties} onChange={v => setData(p => ({...p, parties: v}))} placeholder="Who are the parties?" />
            <InputField label="Purpose of Contract" value={data.purpose} onChange={v => setData(p => ({...p, purpose: v}))} placeholder="What is this contract for?" />
            <div className="flex gap-3">
              <button onClick={() => setStep(0)} className="px-4 py-2 bg-[#16213e] text-[#a0a0a0] rounded-xl text-sm">← Back</button>
              <button onClick={() => setStep(2)} className="px-4 py-2 bg-[#e94560] text-white rounded-xl text-sm font-bold">Next →</button>
            </div>
          </div>
        )}

        {step === 2 && (
          <div className="space-y-4">
            <InputField label="Key Terms" textarea value={data.terms} onChange={v => setData(p => ({...p, terms: v}))} placeholder="What are the key terms you see?" />
            <div className="flex gap-3">
              <button onClick={() => setStep(1)} className="px-4 py-2 bg-[#16213e] text-[#a0a0a0] rounded-xl text-sm">← Back</button>
              <button onClick={() => setStep(3)} className="px-4 py-2 bg-[#e94560] text-white rounded-xl text-sm font-bold">Next →</button>
            </div>
          </div>
        )}

        {step === 3 && (
          <div className="space-y-4">
            <InputField label="Questions / Concerns" textarea value={data.concerns} onChange={v => setData(p => ({...p, concerns: v}))} placeholder="What concerns you about this contract?" />
            <div className="bg-[#16213e] border border-amber-500 rounded-xl p-4">
              <p className="text-amber-400 text-sm font-bold mb-2">⚠️ Questions for Counsel:</p>
              <ul className="text-[#a0a0a0] text-xs space-y-1 list-disc pl-4">
                <li>Is this contract enforceable in my jurisdiction?</li>
                <li>Are there hidden obligations or liability exposure?</li>
                <li>What happens if the other party breaches?</li>
                <li>Are the termination provisions favorable?</li>
                <li>Is indemnification adequate?</li>
              </ul>
            </div>
            <div className="flex gap-3">
              <button onClick={() => setStep(2)} className="px-4 py-2 bg-[#16213e] text-[#a0a0a0] rounded-xl text-sm">← Back</button>
              <button onClick={() => setStep(4)} className="px-4 py-2 bg-[#e94560] text-white rounded-xl text-sm font-bold">Next →</button>
            </div>
          </div>
        )}

        {step === 4 && (
          <div className="bg-[#16213e] border border-green-500 rounded-xl p-5">
            <h3 className="text-green-400 font-bold mb-3">✅ Contract Review Complete</h3>
            <p className="text-[#a0a0a0] text-sm">Your Contract Review Checklist has been prepared. Key questions for counsel are flagged above. Recommended next steps:</p>
            <ul className="text-[#a0a0a0] text-sm space-y-1 mt-3 list-disc pl-4">
              <li>Present this checklist to a qualified attorney</li>
              <li>Request redline edits for any flagged concerns</li>
              <li>Negotiate terms before signing</li>
              <li>Keep a signed copy with your records</li>
            </ul>
            <button onClick={() => { setStep(0); setContractType(""); }} className="mt-4 px-4 py-2 bg-[#e94560] text-white rounded-xl text-sm font-bold">Start New Contract Review</button>
          </div>
        )}
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   9. GRANT LEGAL READINESS
   ═══════════════════════════════════════════════════════════════════════════ */

function GrantLegalReadiness() {
  const [grant, setGrant] = useState("");
  const [checks, setChecks] = useState({});
  const items = [
    "Organization documentation (articles, bylaws)", "Tax-exempt status (501(c)(3) or equivalent)",
    "Required certifications", "Authorized representative information",
    "Financial statements", "Board resolution for grant acceptance",
    "Compliance with grant conditions", "Reporting capability",
  ];
  const done = items.filter((_, i) => checks[i]).length;
  const pct = Math.round((done / items.length) * 100);

  return (
    <div className="bg-[#1a1a2e] border border-[#0f3460] rounded-2xl p-6 space-y-4">
      <h2 className="text-[#ffd700] text-lg font-bold uppercase tracking-wider border-b border-[#e94560] pb-3">
        🏆 GRANT LEGAL READINESS
      </h2>
      <InputField label="Grant Name" value={grant} onChange={setGrant} placeholder="e.g. USDA Community Facilities Grant" />
      <div className="bg-[#16213e] rounded-full h-5 overflow-hidden">
        <div className="h-full bg-gradient-to-r from-[#e94560] to-[#ffd700] rounded-full flex items-center justify-center text-[10px] font-bold text-black transition-all" style={{ width: `${pct}%` }}>{pct}%</div>
      </div>
      <div className="space-y-2">
        {items.map((item, i) => (
          <button key={i} onClick={() => setChecks(p => ({...p, [i]: !p[i]}))}
            className="w-full flex items-center gap-3 text-left p-3 rounded-lg hover:bg-[#16213e] transition-colors">
            {checks[i] ? <CheckCircle2 className="w-5 h-5 text-green-400" /> : <Circle className="w-5 h-5 text-[#0f3460]" />}
            <span className={`text-sm ${checks[i] ? "text-green-400" : "text-[#a0a0a0]"}`}>{item}</span>
          </button>
        ))}
      </div>
      <Link to="/resources" className="text-[#e94560] text-sm font-bold hover:underline inline-flex items-center gap-1">
        ← Back to Resource Hub Grants
      </Link>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   10. FUNDRAISING COMPLIANCE
   ═══════════════════════════════════════════════════════════════════════════ */

function FundraiseCompliance() {
  const [activity, setActivity] = useState("");
  const [checks, setChecks] = useState({});
  const items = [
    "Registration requirements for your state", "Donor disclosure obligations",
    "Financial reporting requirements", "Tax implications for donations",
    "Platform terms of service compliance", "Privacy policy for donor data",
    "Refund/cancellation policy", "Anti-money laundering compliance",
  ];
  const done = items.filter((_, i) => checks[i]).length;
  const pct = Math.round((done / items.length) * 100);

  return (
    <div className="bg-[#1a1a2e] border border-[#0f3460] rounded-2xl p-6 space-y-4">
      <h2 className="text-[#ffd700] text-lg font-bold uppercase tracking-wider border-b border-[#e94560] pb-3">
        💝 FUNDRAISING COMPLIANCE
      </h2>
      <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
        {FUNDRAISING_ACTIVITIES.map(fa => (
          <button key={fa.key} onClick={() => setActivity(fa.key)}
            className={`p-3 rounded-xl text-sm font-bold border-2 transition-all ${
              activity === fa.key ? "border-[#ffd700] bg-[#ffd700]/10 text-[#ffd700]" : "border-[#0f3460] bg-[#16213e] text-[#a0a0a0]"
            }`}>{fa.label}</button>
        ))}
      </div>
      {activity && (
        <>
          <div className="bg-[#16213e] rounded-full h-5 overflow-hidden">
            <div className="h-full bg-gradient-to-r from-red-500 to-green-400 rounded-full flex items-center justify-center text-[10px] font-bold text-black transition-all" style={{ width: `${pct}%` }}>{pct}%</div>
          </div>
          <div className="space-y-2">
            {items.map((item, i) => (
              <button key={i} onClick={() => setChecks(p => ({...p, [i]: !p[i]}))}
                className="w-full flex items-center gap-3 text-left p-3 rounded-lg hover:bg-[#16213e] transition-colors">
                {checks[i] ? <CheckCircle2 className="w-5 h-5 text-green-400" /> : <Circle className="w-5 h-5 text-[#0f3460]" />}
                <span className={`text-sm ${checks[i] ? "text-green-400" : "text-[#a0a0a0]"}`}>{item}</span>
              </button>
            ))}
          </div>
        </>
      )}
      <Link to="/resources" className="text-[#e94560] text-sm font-bold hover:underline inline-flex items-center gap-1">
        ← Back to Resource Hub Fundraising
      </Link>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   11. BUSINESS LEGAL SETUP
   ═══════════════════════════════════════════════════════════════════════════ */

function BusinessLegalSetup() {
  const [step, setStep] = useState(0);
  const steps = ["Business Idea", "Entity", "Ownership", "Agreements", "Compliance", "Records", "Ongoing"];
  const checklists = {
    0: ["Define business purpose", "Research market and competition", "Identify target customers", "Create business plan"],
    1: ["Choose entity type (LLC, Corp, Sole Prop)", "File formation documents", "Get EIN from IRS", "Draft operating agreement"],
    2: ["Define ownership percentages", "Document capital contributions", "Create shareholder/member agreement", "Set up cap table"],
    3: ["Draft client agreements", "Draft vendor agreements", "Draft employment/contractor agreements", "Create NDA templates"],
    4: ["Business license application", "Professional licenses", "Industry-specific permits", "Zoning compliance"],
    5: ["Organize financial records", "Set up bookkeeping system", "Document meeting minutes", "Archive key correspondence"],
    6: ["Annual report filing schedule", "Tax filing deadlines", "Insurance renewal dates", "License renewal dates"],
  };

  const items = checklists[step] || [];
  const [checks, setChecks] = useState({});

  return (
    <div className="bg-[#1a1a2e] border border-[#0f3460] rounded-2xl p-6 space-y-4">
      <h2 className="text-[#ffd700] text-lg font-bold uppercase tracking-wider border-b border-[#e94560] pb-3">
        🏢 BUSINESS LEGAL SETUP
      </h2>
      <div className="flex gap-1 overflow-x-auto pb-2">
        {steps.map((s, i) => (
          <button key={i} onClick={() => setStep(i)}
            className={`px-3 py-1.5 rounded-full text-xs font-bold whitespace-nowrap transition-all ${
              i === step ? "bg-[#e94560] text-white" : "bg-[#16213e] text-[#a0a0a0]"
            }`}>{s}</button>
        ))}
      </div>
      <div className="space-y-2">
        {items.map((item, i) => (
          <button key={i} onClick={() => setChecks(p => ({...p, [`${step}:${i}`]: !p[`${step}:${i}`]}))}
            className="w-full flex items-center gap-3 text-left p-3 rounded-lg hover:bg-[#16213e] transition-colors">
            {checks[`${step}:${i}`] ? <CheckCircle2 className="w-5 h-5 text-green-400" /> : <Circle className="w-5 h-5 text-[#0f3460]" />}
            <span className={`text-sm ${checks[`${step}:${i}`] ? "text-green-400" : "text-[#a0a0a0]"}`}>{item}</span>
          </button>
        ))}
      </div>
      <div className="flex gap-3">
        {step > 0 && <button onClick={() => setStep(s => s - 1)} className="px-4 py-2 bg-[#16213e] text-[#a0a0a0] rounded-xl text-sm">← Previous</button>}
        {step < steps.length - 1 && <button onClick={() => setStep(s => s + 1)} className="px-4 py-2 bg-[#e94560] text-white rounded-xl text-sm font-bold">Next →</button>}
      </div>
      <Link to="/resources" className="text-[#e94560] text-sm font-bold hover:underline inline-flex items-center gap-1">
        ← Back to Resource Hub Business Resources
      </Link>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   12. IP WORKFLOW
   ═══════════════════════════════════════════════════════════════════════════ */

function IPWorkflow() {
  const [ipType, setIpType] = useState("");
  const [step, setStep] = useState(0);
  const steps = ["Identify Asset", "Establish Ownership", "Preserve Evidence", "Licensing/Usage", "Protection Options", "Next Steps"];

  return (
    <div className="bg-[#1a1a2e] border border-[#0f3460] rounded-2xl p-6 space-y-4">
      <h2 className="text-[#ffd700] text-lg font-bold uppercase tracking-wider border-b border-[#e94560] pb-3">
        🛡️ INTELLECTUAL PROPERTY WORKFLOW
      </h2>
      <div className="flex gap-1 overflow-x-auto pb-2">
        {steps.map((s, i) => (
          <button key={i} onClick={() => setStep(i)}
            className={`px-3 py-1.5 rounded-full text-xs font-bold whitespace-nowrap ${i === step ? "bg-[#e94560] text-white" : "bg-[#16213e] text-[#a0a0a0]"}`}>{s}</button>
        ))}
      </div>
      {step === 0 && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-2">
          {IP_TYPES.map(ip => (
            <button key={ip.key} onClick={() => { setIpType(ip.key); setStep(1); }}
              className={`p-3 rounded-xl text-sm font-bold border-2 ${ipType === ip.key ? "border-[#ffd700] bg-[#ffd700]/10 text-[#ffd700]" : "border-[#0f3460] bg-[#16213e] text-[#a0a0a0]"}`}>{ip.label}</button>
          ))}
        </div>
      )}
      {step === 1 && (
        <div className="space-y-3">
          <p className="text-[#a0a0a0] text-sm">Who created this work? Who owns it?</p>
          <InputField label="Creator(s)" placeholder="Names of creators" />
          <InputField label="Owner(s)" placeholder="Legal owner(s) of the IP" />
          <InputField label="Creation Date" type="date" />
          <InputField label="Description of the work" textarea placeholder="Describe the intellectual property..." />
          <div className="flex gap-3">
            <button onClick={() => setStep(0)} className="px-4 py-2 bg-[#16213e] text-[#a0a0a0] rounded-xl text-sm">← Back</button>
            <button onClick={() => setStep(2)} className="px-4 py-2 bg-[#e94560] text-white rounded-xl text-sm font-bold">Next →</button>
          </div>
        </div>
      )}
      {step === 2 && (
        <div className="space-y-3">
          <p className="text-[#a0a0a0] text-sm">Document your evidence of creation and ownership.</p>
          <div className="space-y-2">
            {["Drafts and version history", "Timestamps of creation", "Publication records", "Registration certificates", "Screenshots with metadata"].map((item, i) => (
              <div key={i} className="flex items-center gap-3 p-3 bg-[#16213e] rounded-lg">
                <Circle className="w-4 h-4 text-[#0f3460]" />
                <span className="text-[#a0a0a0] text-sm">{item}</span>
              </div>
            ))}
          </div>
          <div className="flex gap-3">
            <button onClick={() => setStep(1)} className="px-4 py-2 bg-[#16213e] text-[#a0a0a0] rounded-xl text-sm">← Back</button>
            <button onClick={() => setStep(3)} className="px-4 py-2 bg-[#e94560] text-white rounded-xl text-sm font-bold">Next →</button>
          </div>
        </div>
      )}
      {step >= 3 && (
        <div className="space-y-3">
          <p className="text-[#a0a0a0] text-sm">
            {step === 3 && "How do you want to license or share this work?"}
            {step === 4 && "What protection options do you want to pursue?"}
            {step === 5 && "Your IP protection checklist is ready. Next steps:"}
          </p>
          {step === 5 && (
            <ul className="text-[#a0a0a0] text-sm space-y-1 list-disc pl-4">
              <li>File copyright registration with the US Copyright Office</li>
              <li>Consider trademark registration for brand elements</li>
              <li>Document all creation evidence in a secure location</li>
              <li>Consult an IP attorney for enforcement options</li>
            </ul>
          )}
          <div className="flex gap-3">
            <button onClick={() => setStep(s => s - 1)} className="px-4 py-2 bg-[#16213e] text-[#a0a0a0] rounded-xl text-sm">← Back</button>
            {step < 5 && <button onClick={() => setStep(s => s + 1)} className="px-4 py-2 bg-[#e94560] text-white rounded-xl text-sm font-bold">Next →</button>}
          </div>
        </div>
      )}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   13. EMPLOYMENT WORKFLOW
   ═══════════════════════════════════════════════════════════════════════════ */

function EmploymentWorkflow() {
  const [empType, setEmpType] = useState("");
  const checks = [
    "Employee or contractor classification", "Written agreement drafted",
    "Compensation terms defined", "Confidentiality agreement", "IP ownership assignment",
    "Job responsibilities documented", "Termination provisions", "Benefits and insurance",
  ];
  const [checked, setChecked] = useState({});
  const done = checks.filter((_, i) => checked[i]).length;

  return (
    <div className="bg-[#1a1a2e] border border-[#0f3460] rounded-2xl p-6 space-y-4">
      <h2 className="text-[#ffd700] text-lg font-bold uppercase tracking-wider border-b border-[#e94560] pb-3">
        👥 EMPLOYMENT / CONTRACTOR WORKFLOW
      </h2>
      <div className="flex gap-3">
        <button onClick={() => setEmpType("employee")} className={`px-6 py-3 rounded-xl text-sm font-bold border-2 ${empType === "employee" ? "border-[#ffd700] bg-[#ffd700]/10 text-[#ffd700]" : "border-[#0f3460] bg-[#16213e] text-[#a0a0a0]"}`}>Employee</button>
        <button onClick={() => setEmpType("contractor")} className={`px-6 py-3 rounded-xl text-sm font-bold border-2 ${empType === "contractor" ? "border-[#ffd700] bg-[#ffd700]/10 text-[#ffd700]" : "border-[#0f3460] bg-[#16213e] text-[#a0a0a0]"}`}>Independent Contractor</button>
      </div>
      {empType && (
        <div className="space-y-2">
          {checks.map((item, i) => (
            <button key={i} onClick={() => setChecked(p => ({...p, [i]: !p[i]}))}
              className="w-full flex items-center gap-3 text-left p-3 rounded-lg hover:bg-[#16213e] transition-colors">
              {checked[i] ? <CheckCircle2 className="w-5 h-5 text-green-400" /> : <Circle className="w-5 h-5 text-[#0f3460]" />}
              <span className={`text-sm ${checked[i] ? "text-green-400" : "text-[#a0a0a0]"}`}>{item}</span>
            </button>
          ))}
          <div className="bg-[#16213e] border border-amber-500 rounded-xl p-4 mt-4">
            <p className="text-amber-400 text-sm font-bold">Hiring Legal Checklist: {done}/{checks.length} complete</p>
          </div>
        </div>
      )}
      <Link to="/resources" className="text-[#e94560] text-sm font-bold hover:underline inline-flex items-center gap-1">
        ← Back to Resource Hub
      </Link>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   14. DISPUTE PREPARATION
   ═══════════════════════════════════════════════════════════════════════════ */

function DisputePrep() {
  const [data, setData] = useState({ what: "", who: "", dates: "", communications: "", documents: "", witnesses: "", financial: "", outcome: "", deadlines: "" });
  const update = (k, v) => setData(p => ({...p, [k]: v}));
  const filled = Object.values(data).filter(Boolean).length;
  const total = Object.keys(data).length;

  return (
    <div className="bg-[#1a1a2e] border border-[#0f3460] rounded-2xl p-6 space-y-4">
      <h2 className="text-[#ffd700] text-lg font-bold uppercase tracking-wider border-b border-[#e94560] pb-3">
        ⚔️ DISPUTE PREPARATION
      </h2>
      <div className="grid md:grid-cols-2 gap-4">
        <InputField label="What Happened?" textarea value={data.what} onChange={v => update("what", v)} placeholder="Describe the dispute..." />
        <InputField label="Who Was Involved?" value={data.who} onChange={v => update("who", v)} placeholder="Names and roles" />
        <InputField label="Dates" value={data.dates} onChange={v => update("dates", v)} placeholder="Key dates" />
        <InputField label="Communications" textarea value={data.communications} onChange={v => update("communications", v)} placeholder="Emails, texts, letters..." />
        <InputField label="Documents" textarea value={data.documents} onChange={v => update("documents", v)} placeholder="Contracts, receipts, records..." />
        <InputField label="Witnesses" value={data.witnesses} onChange={v => update("witnesses", v)} placeholder="Names and contact info" />
        <InputField label="Financial Impact" value={data.financial} onChange={v => update("financial", v)} placeholder="Dollar amounts" />
        <InputField label="Desired Outcome" value={data.outcome} onChange={v => update("outcome", v)} placeholder="What do you want?" />
        <InputField label="Important Deadlines" value={data.deadlines} onChange={v => update("deadlines", v)} placeholder="Statute of limitations, filing deadlines" />
      </div>
      {filled > 3 && (
        <div className="bg-[#16213e] border border-green-500 rounded-xl p-4">
          <p className="text-green-400 font-bold text-sm">DISPUTE SUMMARY — {filled}/{total} fields completed</p>
          <p className="text-[#a0a0a0] text-xs mt-2">Your dispute information is saved locally. Generate a Dispute Timeline document from the Documents tab.</p>
        </div>
      )}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   15. ATTORNEY PREPARATION PACKET
   ═══════════════════════════════════════════════════════════════════════════ */

function AttorneyPrepPacket() {
  const [packet, setPacket] = useState({ summary: "", parties: "", timeline: "", facts: "", evidence: "", missing: "", documents: "", financial: "", questions: "", outcome: "", dates: "" });
  const update = (k, v) => setPacket(p => ({...p, [k]: v}));
  const filled = Object.values(packet).filter(Boolean).length;

  return (
    <div className="bg-[#1a1a2e] border border-[#0f3460] rounded-2xl p-6 space-y-4">
      <h2 className="text-[#ffd700] text-lg font-bold uppercase tracking-wider border-b border-[#e94560] pb-3">
        📦 ATTORNEY CONSULTATION PACKET
      </h2>
      <p className="text-[#a0a0a0] text-sm">Fill in everything you know. This becomes your consultation packet — print it and bring it to your attorney.</p>
      <div className="grid md:grid-cols-2 gap-4">
        <InputField label="Case/Issue Summary" textarea value={packet.summary} onChange={v => update("summary", v)} placeholder="Brief summary of your situation..." />
        <InputField label="Parties Involved" value={packet.parties} onChange={v => update("parties", v)} placeholder="Names, roles, relationships" />
        <InputField label="Timeline" textarea value={packet.timeline} onChange={v => update("timeline", v)} placeholder="Key dates and events in order..." />
        <InputField label="Key Facts" textarea value={packet.facts} onChange={v => update("facts", v)} placeholder="Important facts..." />
        <InputField label="Evidence Available" textarea value={packet.evidence} onChange={v => update("evidence", v)} placeholder="What evidence do you have?" />
        <InputField label="Missing Evidence" textarea value={packet.missing} onChange={v => update("missing", v)} placeholder="What evidence do you need?" />
        <InputField label="Relevant Documents" textarea value={packet.documents} onChange={v => update("documents", v)} placeholder="Contracts, letters, records..." />
        <InputField label="Financial/Damage Info" value={packet.financial} onChange={v => update("financial", v)} placeholder="Dollar amounts, losses" />
        <InputField label="Questions for Attorney" textarea value={packet.questions} onChange={v => update("questions", v)} placeholder="What do you want to ask?" />
        <InputField label="Desired Outcome" value={packet.outcome} onChange={v => update("outcome", v)} placeholder="What result do you want?" />
        <InputField label="Important Dates/Deadlines" value={packet.dates} onChange={v => update("dates", v)} placeholder="Statute of limitations, court dates" />
      </div>
      {filled > 5 && (
        <div className="bg-[#16213e] border border-green-500 rounded-xl p-4 text-center">
          <p className="text-green-400 font-bold">Packet {filled}/11 fields complete — Generate the Attorney Consultation Packet from Documents tab</p>
        </div>
      )}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   16. DOCUMENT GENERATOR (existing + 9 new types)
   ═══════════════════════════════════════════════════════════════════════════ */

function DocumentGenerator() {
  const [docType, setDocType] = useState("eeoc");
  const [output, setOutput] = useState("");
  const [fields, setFields] = useState({ name: "", employer: "", date: new Date().toISOString().split("T")[0], facts: "", amount: "" });

  const DOC_TYPES = [
    { key: "eeoc", label: "EEOC Complaint" },
    { key: "mspb", label: "MSPB Appeal" },
    { key: "motion", label: "Motion to Compel" },
    { key: "complaint", label: "Federal Complaint" },
    { key: "demand", label: "Demand Letter" },
    { key: "settlement", label: "Settlement Demand" },
    { key: "attorney_q", label: "Attorney Question Sheet" },
    { key: "readiness_check", label: "Legal Readiness Checklist" },
    { key: "contract_check", label: "Contract Review Checklist" },
    { key: "grant_check", label: "Grant Legal Readiness" },
    { key: "fundraise_check", label: "Fundraising Compliance" },
    { key: "business_check", label: "Business Legal Checklist" },
    { key: "ip_inv", label: "IP Inventory" },
    { key: "dispute_timeline", label: "Dispute Timeline" },
    { key: "attorney_packet", label: "Attorney Consultation Packet" },
  ];

  const generate = () => {
    const n = fields.name || "John Doe";
    const e = fields.employer || "United States of America";
    const d = fields.date;
    const f = fields.facts || "Facts to be detailed.";
    const docs = {
      eeoc: `EEOC CHARGE OF DISCRIMINATION\n\nCharging Party: ${n}\nRespondent: ${e}\nDate: ${d}\n\nI. STATEMENT OF FACTS\n${f}\n\nII. LEGAL BASIS\nTitle VII of the Civil Rights Act of 1964 (42 U.S.C. § 2000e et seq.)\n\nIII. REQUESTED RELIEF\n1. Cessation of discriminatory practices\n2. Back pay with interest\n3. Reinstatement\n4. Compensatory and punitive damages\n\nSignature: ____________________\nDate: ${d}`,
      mspb: `MSPB APPEAL — PROHIBITED PERSONNEL PRACTICE\n\nAppellant: ${n}\nAgency: ${e}\nDate of Action: ${d}\n\n${f}\n\nII. PROHIBITED PERSONNEL PRACTICE\n5 U.S.C. § 2302(b) violations\n\nIII. REQUESTED RELIEF\n1. Reversal of removal\n2. Reinstatement with back pay\n\nSignature: ____________________\nDate: ${d}`,
      motion: `MOTION TO COMPEL PRODUCTION\n\nCase No.: ___\nPlaintiff: ${n}\nDefendant: ${e}\n\n${f}\n\nREQUESTED: Compel production within 14 days.\n\nSignature: ____________________\nDate: ${d}`,
      complaint: `UNITED STATES DISTRICT COURT\n\n${n}, Plaintiff v. ${e}, Defendant\n\nCOMPLAINT FOR CIVIL RIGHTS VIOLATIONS\n\n${f}\n\nPRAYER FOR RELIEF:\nA. Declaratory judgment\nB. Compensatory damages\nC. Punitive damages\nD. Reinstatement\nE. Attorney fees\n\nRespectfully submitted,\n${n}, Pro Se\nDate: ${d}`,
      demand: `DEMAND LETTER\n\nTo: ${e}\nFrom: ${n}\nDate: ${d}\n\n${f}\n\nDEMANDS:\n1. Full back pay with interest\n2. Reinstatement\n3. Independent monitor\n4. Algorithmic audits\n\nFailure to respond within 30 days will result in federal action.\n\nSincerely,\n${n}`,
      settlement: `SETTLEMENT DEMAND\n\nTo: ${e}\nFrom: ${n}\nDate: ${d}\n\nDamages: ${fields.amount || "$0"}\n\n${f}\n\nDEMANDS:\n1. Full back pay with compounding interest\n2. Mandatory reinstatement\n3. Independent judicial monitor\n4. Class Civil Rights Reparations Trust\n\nSincerely,\n${n}`,
      attorney_q: `ATTORNEY QUESTION SHEET\n\nPrepared by: ${n}\nDate: ${d}\n\n${f}\n\nQUESTIONS:\n1. What is the strongest cause of action?\n2. What is the statute of limitations?\n3. What evidence is needed?\n4. What are the likely damages?\n5. Should I join a class action?\n6. What are the costs and fee arrangements?\n7. What are the risks of litigation?\n8. What is the expected timeline?\n9. Are there alternatives to litigation?\n10. What should I do immediately to protect my rights?`,
      readiness_check: `LEGAL READINESS CHECKLIST\n\nPrepared by: ${n}\nDate: ${d}\n\n${f}\n\nCATEGORIES:\n☐ Business/Entity Documents\n☐ Contracts\n☐ Ownership\n☐ Intellectual Property\n☐ Employment/Contractors\n☐ Licenses and Permits\n☐ Compliance\n☐ Insurance\n☐ Privacy/Website\n☐ Records/Evidence`,
      contract_check: `CONTRACT REVIEW CHECKLIST\n\nReviewed by: ${n}\nDate: ${d}\n\n${f}\n\nREVIEW ITEMS:\n☐ Parties identified\n☐ Scope of work defined\n☐ Payment terms clear\n☐ Termination provisions fair\n☐ Liability limitations adequate\n☐ Confidentiality included\n☐ IP ownership assigned\n☐ Dispute resolution defined\n☐ Governing law identified\n☐ Insurance requirements clear\n\nQUESTIONS FOR COUNSEL:\n1. Is this enforceable?\n2. What are the hidden obligations?\n3. What happens on breach?\n4. Are indemnification provisions fair?`,
      grant_check: `GRANT LEGAL READINESS CHECKLIST\n\nGrant: ${fields.amount || "TBD"}\nApplicant: ${n}\nDate: ${d}\n\n${f}\n\n☐ Organization documentation\n☐ Tax-exempt status\n☐ Required certifications\n☐ Authorized representative info\n☐ Financial statements\n☐ Board resolution\n☐ Compliance verification\n☐ Reporting capability`,
      fundraise_check: `FUNDRAISING COMPLIANCE CHECKLIST\n\nActivity: ${fields.amount || "TBD"}\nOperator: ${n}\nDate: ${d}\n\n${f}\n\n☐ Registration requirements\n☐ Donor disclosure obligations\n☐ Financial reporting requirements\n☐ Tax implications\n☐ Platform compliance\n☐ Privacy policy\n☐ Refund policy\n☐ AML compliance`,
      business_check: `BUSINESS LEGAL CHECKLIST\n\nBusiness: ${fields.amount || "TBD"}\nOwner: ${n}\nDate: ${d}\n\n${f}\n\n☐ Entity formation\n☐ EIN obtained\n☐ Operating agreement\n☐ Ownership documented\n☐ Client agreements\n☐ Vendor agreements\n☐ Employment agreements\n☐ Licenses obtained\n☐ Insurance secured\n☐ Privacy policy\n☐ Financial records organized\n☐ Tax compliance`,
      ip_inv: `IP INVENTORY\n\nOwner: ${n}\nDate: ${d}\n\n${f}\n\nASSET LIST:\n☐ Registered trademarks\n☐ Copyright registrations\n☐ Patent applications\n☐ Trade secrets documented\n☐ License agreements\n☐ IP assignment agreements\n\nPROTECTION STATUS:\n☐ Evidence preserved\n☐ Registration filed\n☐ Monitoring active\n☐ Enforcement plan ready`,
      dispute_timeline: `DISPUTE TIMELINE\n\nPrepared by: ${n}\nDate: ${d}\n\n${f}\n\nTIMELINE:\n[Date] — [Event]\n[Date] — [Event]\n[Date] — [Event]\n\nEVIDENCE CHECKLIST:\n☐ Communications\n☐ Documents\n☐ Witness statements\n☐ Financial records\n\nMISSING INFORMATION:\n[Items to obtain]\n\nRECOMMENDED NEXT STEPS:\n[Actions to take]`,
      attorney_packet: `ATTORNEY CONSULTATION PACKET\n\nPrepared by: ${n}\nDate: ${d}\n\nSUMMARY:\n${f}\n\nPARTIES: [List parties]\nTIMELINE: [Key dates]\nFACTS: [Key facts]\nEVIDENCE: [Available]\nMISSING: [What's needed]\nDOCUMENTS: [Relevant docs]\nFINANCIAL: [Damages]\nQUESTIONS: [For attorney]\nOUTCOME: [Desired result]\nDEADLIMITS: [Critical dates]`,
    };
    setOutput(docs[docType] || "Document type not found.");
  };

  return (
    <div className="bg-[#1a1a2e] border border-[#0f3460] rounded-2xl p-6 space-y-4">
      <h2 className="text-[#ffd700] text-lg font-bold uppercase tracking-wider border-b border-[#e94560] pb-3">
        📝 DOCUMENT GENERATOR
      </h2>

      <div className="flex gap-1 overflow-x-auto pb-2 flex-wrap">
        {DOC_TYPES.map(dt => (
          <button key={dt.key} onClick={() => { setDocType(dt.key); setOutput(""); }}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold whitespace-nowrap ${docType === dt.key ? "bg-[#e94560] text-white" : "bg-[#16213e] text-[#a0a0a0]"}`}>{dt.label}</button>
        ))}
      </div>

      <div className="grid md:grid-cols-2 gap-4">
        <InputField label="Your Name" value={fields.name} onChange={v => setFields(p => ({...p, name: v}))} placeholder="John Doe" />
        <InputField label="Other Party / Agency" value={fields.employer} onChange={v => setFields(p => ({...p, employer: v}))} placeholder="Agency / Company" />
        <InputField label="Date" type="date" value={fields.date} onChange={v => setFields(p => ({...p, date: v}))} />
        <InputField label="Amount / Reference" value={fields.amount} onChange={v => setFields(p => ({...p, amount: v}))} placeholder="e.g. $763,200" />
      </div>
      <InputField label="Facts / Description" textarea value={fields.facts} onChange={v => setFields(p => ({...p, facts: v}))} placeholder="Describe what happened..." />

      <div className="flex gap-3">
        <button onClick={generate} className="bg-gradient-to-r from-green-600 to-green-800 text-white px-6 py-3 rounded-xl font-bold uppercase tracking-wider text-sm hover:scale-105 transition-transform">
          ⚡ GENERATE DOCUMENT
        </button>
        {output && (
          <button onClick={() => { navigator.clipboard.writeText(output); }} className="px-4 py-2 bg-[#16213e] text-[#a0a0a0] rounded-xl text-sm font-bold hover:bg-[#0f3460]">
            📋 Copy
          </button>
        )}
      </div>

      {output && (
        <div className="bg-[#16213e] border-2 border-[#ffd700] rounded-xl p-5 max-h-96 overflow-y-auto">
          <pre className="text-[#a0a0a0] text-xs font-mono whitespace-pre-wrap leading-relaxed">{output}</pre>
        </div>
      )}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   17. PROTECTION (existing functionality preserved)
   ═══════════════════════════════════════════════════════════════════════════ */

function ProtectionSection() {
  const [shield, setShield] = useState("retal");
  const shields = [
    { key: "retal", label: "Retaliation Defense" },
    { key: "anon", label: "Anonymity" },
    { key: "data", label: "Data Protection" },
    { key: "whistle", label: "Whistleblower" },
  ];

  return (
    <div className="bg-[#1a1a2e] border border-[#0f3460] rounded-2xl p-6 space-y-4">
      <h2 className="text-[#ffd700] text-lg font-bold uppercase tracking-wider border-b border-[#e94560] pb-3">
        🛡️ PERSONAL PROTECTION SHIELD
      </h2>
      <div className="flex gap-2 flex-wrap">
        {shields.map(s => (
          <button key={s.key} onClick={() => setShield(s.key)}
            className={`px-4 py-2 rounded-lg text-xs font-bold ${shield === s.key ? "bg-[#e94560] text-white" : "bg-[#16213e] text-[#a0a0a0]"}`}>{s.label}</button>
        ))}
      </div>
      {shield === "retal" && (
        <div className="bg-[#16213e] rounded-xl p-5 space-y-3">
          <h3 className="text-[#eaeaea] font-bold">IF THEY RETALIATE — USE THIS</h3>
          <ol className="text-[#a0a0a0] text-sm space-y-2 list-decimal pl-5">
            <li><strong className="text-green-400">File with OSC Immediately</strong> — Office of Special Counsel, free, online, 10 minutes.</li>
            <li><strong className="text-green-400">They Get a STAY OF REMOVAL</strong> — They CANNOT fire you while OSC investigates.</li>
            <li><strong className="text-green-400">Use OSC Finding in Court</strong> — Automatic attorney fees + compensatory damages.</li>
          </ol>
        </div>
      )}
      {shield === "anon" && (
        <div className="bg-[#16213e] rounded-xl p-5 space-y-3">
          <h3 className="text-[#eaeaea] font-bold">FILE UNDER PSEUDONYM</h3>
          <p className="text-[#a0a0a0] text-sm">FRCP Rule 5.2 allows anonymous filing when there's fear of retaliation.</p>
          <div className="bg-[#0a0a0a] rounded-lg p-3 text-xs text-[#a0a0a0] font-mono">
            "Plaintiff requests permission to proceed under pseudonym pursuant to FRCP Rule 5.2. Public filing would expose Plaintiff to immediate retaliation."
          </div>
        </div>
      )}
      {shield === "data" && (
        <div className="bg-[#16213e] rounded-xl p-5 space-y-3">
          <h3 className="text-[#eaeaea] font-bold">PROTECT YOUR DATA</h3>
          <ul className="text-[#a0a0a0] text-sm space-y-1">
            <li>🔒 Use encrypted email (ProtonMail)</li>
            <li>🔒 Never use your real phone number</li>
            <li>🔒 Redact SSN, birthdate, financials</li>
            <li>🔒 Save everything to USB, not cloud</li>
            <li>🔒 Use privacy-focused browser</li>
          </ul>
        </div>
      )}
      {shield === "whistle" && (
        <div className="bg-[#16213e] rounded-xl p-5 space-y-3">
          <h3 className="text-[#eaeaea] font-bold">WHISTLEBLOWER PROTECTION</h3>
          <ul className="text-[#a0a0a0] text-sm space-y-1">
            <li>✅ Automatic stay of removal</li>
            <li>✅ Attorney fees paid by government</li>
            <li>✅ Compensatory damages</li>
            <li>✅ Punitive damages</li>
            <li>✅ Reinstatement with back pay</li>
          </ul>
        </div>
      )}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   18. NUCLEAR OPTIONS (existing functionality preserved)
   ═══════════════════════════════════════════════════════════════════════════ */

function NuclearSection() {
  const [selected, setSelected] = useState(null);
  const options = [
    { key: "partisan", label: "THE PARTISAN PRETEXT KILLER", desc: "Find ANY white coworker who shared your politics but wasn't fired." },
    { key: "algorithm", label: "THE ALGORITHM AUDIT TRAP", desc: "Force them to reveal their screening algorithm. Prove bias mathematically." },
    { key: "state", label: "THE STATE COURT PINCER", desc: "File in multiple state courts simultaneously. Different laws. Uncapped damages." },
    { key: "westfall", label: "WESTFALL ACT SCOPE CHALLENGE", desc: "Strip government immunity. Go after INDIVIDUALS." },
    { key: "tariff", label: "TARIFF CONSUMER FRAUD", desc: "$166B refund scam. Sue the corporations. Class action." },
    { key: "history", label: "THE HISTORICAL FRAMEWORK", desc: "Vagrancy Laws → No Cause RIFs. Poll Taxes → Credit Score Proxies." },
  ];

  const details = {
    partisan: "Find ANY coworker who shared your exact political views but was NOT fired. In deposition, ask: \"Isn't it true that [they] supported every policy the administration enacted — yet remains employed while I was terminated?\" They CANNOT answer without admitting race was the factor.",
    algorithm: "File Motion Compelling Production of the Screening Algorithm. Hire a data scientist to run shadow testing: create 10,000 synthetic profiles, change ONLY the race indicator, run through the system. If Black profiles flagged at higher rate → mathematical proof of violation.",
    state: "File in state court simultaneously with federal court. California (uncapped damages), New York (lower burden of proof), Illinois (protects against credit score proxies). Two fronts forces two defenses.",
    westfall: "Challenge the Westfall Act certification that agents were \"acting within scope.\" Present evidence that actions violated clearly established constitutional boundaries. Strip government protection → restore individual liability → their personal assets are on the line.",
    tariff: "The Supreme Court ruled the tariffs were illegal → $166B refund owed. Corporations kept the money. File a state consumer fraud class action. If class is 10 million people = $16,600 per person.",
    history: "Draw direct parallels: Vagrancy Laws (1865) → \"No cause\" RIF terminations. Poll Taxes (1890s) → Credit score / ZIP code proxies. G.I. Bill (1944) → Competitive service \"merit\" excluding minority experience. The Jury Sees: This isn't new. It's the same playbook.",
  };

  return (
    <div className="bg-[#1a1a2e] border border-[#0f3460] rounded-2xl p-6 space-y-4">
      <h2 className="text-[#ffd700] text-lg font-bold uppercase tracking-wider border-b border-[#e94560] pb-3">
        💣 NUCLEAR OPTIONS
      </h2>
      <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
        {options.map(opt => (
          <button key={opt.key} onClick={() => setSelected(opt.key)}
            className={`bg-[#16213e] border-2 rounded-xl p-4 text-left transition-all hover:border-[#e94560] ${
              selected === opt.key ? "border-[#ffd700] bg-[#ffd700]/10" : "border-[#0f3460]"
            }`}>
            <div className="text-[#eaeaea] text-sm font-bold">{opt.label}</div>
            <p className="text-[#a0a0a0] text-xs mt-1">{opt.desc}</p>
          </button>
        ))}
      </div>
      {selected && (
        <div className="bg-[#16213e] border border-[#e94560] rounded-xl p-5">
          <h3 className="text-[#ffd700] font-bold mb-3">{options.find(o => o.key === selected)?.label}</h3>
          <p className="text-[#a0a0a0] text-sm leading-relaxed">{details[selected]}</p>
        </div>
      )}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   19. RESOURCE HUB BRIDGE
   ═══════════════════════════════════════════════════════════════════════════ */

function ResourceHubBridge() {
  return (
    <div className="space-y-6">
      <div className="bg-[#1a1a2e] border border-[#0f3460] rounded-2xl p-6">
        <h2 className="text-[#ffd700] text-lg font-bold uppercase tracking-wider border-b border-[#e94560] pb-3 mb-4">
          📚 RESOURCE HUB
        </h2>
        <p className="text-[#a0a0a0] text-sm mb-4">
          Your legal workflows connect directly to the Resource Hub. When a legal task identifies a grant, fundraising need, or business resource — you go there.
        </p>
        <div className="grid md:grid-cols-2 gap-4">
          <Link to="/resources" className="bg-[#16213e] border border-[#0f3460] rounded-xl p-5 hover:border-[#e94560] transition-all group block">
            <Award className="w-6 h-6 text-[#ffd700] mb-2" />
            <div className="font-bold text-[#eaeaea] group-hover:text-[#ffd700] transition-colors">Grants</div>
            <p className="text-xs text-[#a0a0a0] mt-1">Browse and apply for grants. Track your applications.</p>
          </Link>
          <Link to="/resources" className="bg-[#16213e] border border-[#0f3460] rounded-xl p-5 hover:border-[#e94560] transition-all group block">
            <Heart className="w-6 h-6 text-red-400 mb-2" />
            <div className="font-bold text-[#eaeaea] group-hover:text-[#ffd700] transition-colors">Fundraising</div>
            <p className="text-xs text-[#a0a0a0] mt-1">Create campaigns and grow your community support.</p>
          </Link>
          <Link to="/resources" className="bg-[#16213e] border border-[#0f3460] rounded-xl p-5 hover:border-[#e94560] transition-all group block">
            <Briefcase className="w-6 h-6 text-green-400 mb-2" />
            <div className="font-bold text-[#eaeaea] group-hover:text-[#ffd700] transition-colors">Business Resources</div>
            <p className="text-xs text-[#a0a0a0] mt-1">Legal, financial, marketing, tech, compliance resources.</p>
          </Link>
          <Link to="/resources" className="bg-[#16213e] border border-[#0f3460] rounded-xl p-5 hover:border-[#e94560] transition-all group block">
            <Bot className="w-6 h-6 text-blue-400 mb-2" />
            <div className="font-bold text-[#eaeaea] group-hover:text-[#ffd700] transition-colors">Assistant</div>
            <p className="text-xs text-[#a0a0a0] mt-1">Draft emails, write proposals, organize tasks.</p>
          </Link>
        </div>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   SHARED INPUT COMPONENT
   ═══════════════════════════════════════════════════════════════════════════ */

function InputField({ label, textarea, type = "text", value, onChange, placeholder }) {
  const cls = "w-full px-4 py-3 bg-[#16213e] border-2 border-[#0f3460] rounded-xl text-[#eaeaea] text-sm outline-none transition-colors focus:border-[#e94560]";
  return (
    <div>
      <label className="block text-[#ffd700] font-bold text-xs mb-1.5">{label}</label>
      {textarea ? (
        <textarea value={value} onChange={e => onChange(e.target.value)} placeholder={placeholder}
          className={`${cls} min-h-[100px] resize-y`} />
      ) : (
        <input type={type} value={value} onChange={e => onChange(e.target.value)} placeholder={placeholder}
          className={cls} />
      )}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   IMPORTS USED IN JSX BUT NOT IN lucide-react
   ═══════════════════════════════════════════════════════════════════════════ */
import { Bot } from "lucide-react";
