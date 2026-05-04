import { useEffect, useState } from "react";
import AppShell from "../components/AppShell";
import { api, BACKEND_URL } from "../lib/api";
import { BadgeCheck, Shield, Award, Star, Download, ExternalLink, Clock } from "lucide-react";

const CAT_ICON = { level: Award, skill: Star, compliance: Shield, capstone: BadgeCheck };
const CAT_COLOR = {
  level: "bg-ink text-white",
  skill: "bg-copper text-white",
  compliance: "bg-signal text-ink",
  capstone: "bg-ink text-signal border-2 border-signal",
};

export default function Credentials() {
  const [data, setData] = useState(null);
  const [tab, setTab] = useState("earned");
  useEffect(() => { api.get("/credentials/me").then((r) => setData(r.data)); }, []);

  if (!data) return <AppShell><div className="p-10">Loading…</div></AppShell>;

  return (
    <AppShell>
      <div className="px-10 py-10 max-w-6xl">
        <div className="overline text-copper">Digital Credentials</div>
        <h1 className="font-heading text-4xl font-bold mt-2 flex items-center gap-3"><BadgeCheck className="w-8 h-8 text-copper" /> Your Credential Wallet</h1>
        <p className="text-ink/60 mt-2 max-w-2xl">OpenBadges-compatible micro-credentials. Share them on LinkedIn, your resume, or any badge-aware platform.</p>

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mt-8">
          <Stat label="Earned" value={data.earned.length} />
          <Stat label="Available" value={data.available.length} />
          <Stat label="Active" value={data.earned.filter((e) => !e.expired).length} />
          <Stat label="Expiring Soon" value={data.earned.filter((e) => e.expires_at && !e.expired).length} />
        </div>

        <div className="flex gap-2 mt-8" data-testid="cred-tabs">
          {[["earned", `Earned (${data.earned.length})`], ["available", `Available (${data.available.length})`]].map(([k, label]) => (
            <button key={k} onClick={() => setTab(k)}
              className={`px-5 py-3 text-sm font-bold uppercase tracking-widest border transition-all ${tab === k ? "bg-ink text-white border-ink" : "bg-white text-ink border-ink/20 hover:border-ink"}`}
              data-testid={`cred-tab-${k}`}>{label}</button>
          ))}
        </div>

        <div className="grid md:grid-cols-2 gap-5 mt-6">
          {(tab === "earned" ? data.earned : data.available).map((c) => (
            <BadgeCard key={c.key} cred={c} earned={tab === "earned"} />
          ))}
          {tab === "earned" && data.earned.length === 0 && (
            <div className="md:col-span-2 card-flat p-12 text-center">
              <BadgeCheck className="w-12 h-12 text-ink/30 mx-auto" />
              <div className="font-heading text-xl font-bold mt-4">No credentials yet</div>
              <div className="text-sm text-ink/60 mt-2">Pass modules or labs to auto-earn your first badge.</div>
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}

function BadgeCard({ cred, earned }) {
  const Icon = CAT_ICON[cred.category] || BadgeCheck;
  const colorCls = CAT_COLOR[cred.category] || "bg-ink text-white";
  return (
    <div className={`card-flat p-6 ${earned ? "" : "opacity-70"}`} data-testid={`badge-${cred.key}`}>
      <div className="flex items-start gap-4">
        <div className={`w-16 h-16 flex items-center justify-center ${colorCls} shrink-0`}>
          <Icon className="w-8 h-8" strokeWidth={2} />
        </div>
        <div className="flex-1">
          <div className="overline text-copper">{cred.category.toUpperCase()}</div>
          <div className="font-heading text-lg font-bold mt-1">{cred.name}</div>
          <div className="text-sm text-ink/70 mt-1 leading-relaxed">{cred.description}</div>
        </div>
      </div>

      <div className="mt-4 text-xs text-ink/60">
        <span className="overline">Evidence:</span> <span className="ml-1">{cred.evidence}</span>
      </div>

      {earned ? (
        <div className="mt-4 pt-4 border-t border-ink/10 flex flex-wrap items-center gap-3 text-xs">
          <span className="badge-signal">Earned</span>
          <span className="font-mono text-ink/70">
            <Clock className="w-3 h-3 inline mr-1" /> {new Date(cred.earned_at).toLocaleDateString()}
          </span>
          {cred.expires_at && (
            <span className={`font-mono ${cred.expired ? "text-destructive" : "text-ink/70"}`}>
              {cred.expired ? "Expired" : "Expires"} {new Date(cred.expires_at).toLocaleDateString()}
            </span>
          )}
          <a href={`${BACKEND_URL}/api/credentials/${cred.key}/manifest.json`} target="_blank" rel="noreferrer"
            className="ml-auto inline-flex items-center gap-1 text-copper font-bold uppercase tracking-widest hover:underline"
            data-testid={`manifest-${cred.key}`}>
            <ExternalLink className="w-3 h-3" /> OpenBadges
          </a>
          <a href={`${BACKEND_URL}/api/credentials/assertion/${cred.id}.json`} target="_blank" rel="noreferrer"
            className="inline-flex items-center gap-1 text-copper font-bold uppercase tracking-widest hover:underline"
            data-testid={`assertion-${cred.key}`}>
            <Download className="w-3 h-3" /> Assertion
          </a>
        </div>
      ) : (
        <div className="mt-4 pt-4 border-t border-ink/10">
          <span className="badge-outline">Not yet earned</span>
        </div>
      )}
    </div>
  );
}

function Stat({ label, value }) {
  return (
    <div className="card-flat p-5">
      <div className="font-heading text-3xl font-black">{value}</div>
      <div className="overline text-ink/60 mt-1">{label}</div>
    </div>
  );
}
