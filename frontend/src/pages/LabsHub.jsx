import { useEffect, useState } from "react";
import AppShell from "../components/AppShell";
import { api } from "../lib/api";
import { Link } from "react-router-dom";
import { Monitor, Hammer, Award, TrendingUp } from "lucide-react";

export default function LabsHub() {
  const [labs, setLabs] = useState([]);
  const [tab, setTab] = useState("online");
  const [comp, setComp] = useState(null);

  useEffect(() => {
    api.get("/labs").then((r) => setLabs(r.data));
    api.get("/competencies").then((r) => setComp(r.data));
  }, []);

  const filtered = labs.filter((l) => l.track === tab);
  const onlineCount = labs.filter((l) => l.track === "online").length;
  const inpersonCount = labs.filter((l) => l.track === "inperson").length;
  const passed = labs.filter((l) => ["passed", "approved"].includes(l.my_submission?.status)).length;
  const pending = labs.filter((l) => l.my_submission?.status === "pending").length;

  return (
    <AppShell>
      <div className="px-10 py-10 max-w-6xl">
        <div className="overline text-copper">Electrical Apprentice Labs</div>
        <h1 className="font-heading text-4xl font-bold mt-2">Shop-Floor Ready.</h1>
        <p className="text-ink/60 mt-2 max-w-2xl">{onlineCount} online simulations + {inpersonCount} in-person labs. Every lab awards skill points, hours, and competency badges toward apprenticeship readiness.</p>

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mt-8">
          <Stat icon={Monitor} label="Online Labs" value={onlineCount} testid="stat-online" />
          <Stat icon={Hammer} label="In-Person Labs" value={inpersonCount} testid="stat-inperson" />
          <Stat icon={Award} label="Skill Points" value={comp?.total_points ?? 0} testid="stat-points" />
          <Stat icon={TrendingUp} label="Labs Passed" value={passed} sub={pending ? `${pending} pending` : ""} testid="stat-passed" />
        </div>

        <div className="flex gap-2 mt-10" data-testid="track-tabs">
          {[["online", "Online Labs", Monitor], ["inperson", "In-Person Labs", Hammer]].map(([k, label, Icon]) => (
            <button key={k} onClick={() => setTab(k)}
              className={`flex items-center gap-2 px-5 py-3 font-bold uppercase tracking-widest text-sm border transition-all ${tab === k ? "bg-ink text-white border-ink" : "bg-white text-ink border-ink/20 hover:border-ink"}`}
              data-testid={`tab-${k}`}>
              <Icon className="w-4 h-4" /> {label}
            </button>
          ))}
        </div>

        <div className="grid md:grid-cols-2 gap-5 mt-8">
          {filtered.map((lab) => <LabCard key={lab.slug} lab={lab} />)}
        </div>
      </div>
    </AppShell>
  );
}

function LabCard({ lab }) {
  const status = lab.my_submission?.status || "not_started";
  const badge = status === "passed" || status === "approved" ? "badge-signal"
    : status === "pending" ? "badge-copper"
    : status === "failed" || status === "rejected" ? "badge-outline" : "badge-outline";
  const label = status === "not_started" ? "Not Started" : status[0].toUpperCase() + status.slice(1);
  return (
    <Link to={`/labs/${lab.slug}`} className="card-flat p-6 group" data-testid={`lab-card-${lab.slug}`}>
      <div className="flex items-start justify-between">
        <div>
          <div className="overline text-copper">
            {lab.track === "online" ? "ONLINE SIM" : "IN-PERSON"} · {lab.hours}h · {lab.skill_points}pts
          </div>
          <div className="font-heading text-xl font-bold mt-2 text-ink group-hover:text-copper transition-colors">{lab.title}</div>
        </div>
        <span className={badge}>{label}</span>
      </div>
      <p className="text-sm text-ink/70 mt-3 leading-relaxed">{lab.summary}</p>
      <div className="mt-4 flex flex-wrap gap-2">
        {lab.competencies.map((c) => <span key={c} className="text-[10px] px-2 py-1 bg-bone border border-ink/20 font-mono uppercase tracking-wider">{c}</span>)}
      </div>
    </Link>
  );
}

function Stat({ icon: Icon, label, value, sub, testid }) {
  return (
    <div className="card-flat p-5" data-testid={testid}>
      <Icon className="w-5 h-5 text-copper" />
      <div className="font-heading text-3xl font-black mt-2">{value}</div>
      <div className="overline text-ink/60 mt-1">{label}</div>
      {sub && <div className="text-xs text-copper mt-1">{sub}</div>}
    </div>
  );
}
