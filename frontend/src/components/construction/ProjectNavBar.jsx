import { useState } from "react";
import { Menu, BarChart3, RefreshCw, Users, HardHat, Activity } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { constructionApi } from "@/lib/construction-pm";

const PHASES = [
  { key: "pre_con", label: "Pre-Con & Estimating", icon: HardHat },
  { key: "construction", label: "Construction & Field Tracking", icon: BarChart3 },
  { key: "turnover", label: "Turnover & Closeout", icon: Activity },
];

export default function ProjectNavBar({ project, onPhaseChange, onRefresh }) {
  const [switcherOpen, setSwitcherOpen] = useState(false);
  const [syncStatus, setSyncStatus] = useState("synced");

  const handleRefresh = async () => {
    setSyncStatus("syncing");
    try {
      await onRefresh();
      setSyncStatus("synced");
    } catch {
      setSyncStatus("error");
      setTimeout(() => setSyncStatus("synced"), 2000);
    }
  };

  const phase = PHASES.find((p) => p.key === project?.current_phase) || PHASES[0];
  const PhaseIcon = phase.icon;

  return (
    <div className="bg-white border-b border-ink/10 sticky top-0 z-20">
      <div className="max-w-7xl mx-auto px-6 py-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-copper/10 flex items-center justify-center text-copper font-bold">
              <HardHat className="w-5 h-5" />
            </div>
            <div>
              <div className="font-bold text-sm text-ink">Electrical Project Management</div>
              <div className="text-xs text-ink/50">M.O.R.E. Help Center · Labor Engine</div>
            </div>
          </div>

          <div className="flex items-center gap-2 flex-1 md:flex-auto max-w-md">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setSwitcherOpen(!switcherOpen)}
              className="w-full justify-between text-sm"
            >
              <span className="truncate mr-2">
                {project ? `${project.job_number} — ${project.client_name}` : "Select a project"}
              </span>
              <Menu className={`w-4 h-4 transition-transform ${switcherOpen ? "rotate-180" : ""}`} />
            </Button>
            {switcherOpen && project && (
              <div className="absolute right-0 mt-2 w-64 bg-white border border-ink/10 rounded-xl shadow-lg py-2 z-50">
                <div className="px-3 py-2 text-xs font-bold text-ink/40 uppercase tracking-wider">Job #{project.job_number}</div>
                <div className="px-3 py-2 text-sm text-ink">{project.client_name}</div>
                <Separator orientation="horizontal" className="my-2" />
                <div className="px-3 py-1 text-sm text-ink/70">{project.site_address || "No site address"}</div>
                <div className="px-3 py-1 text-sm text-ink/70">Contract: ${Number(project.contract_value || 0).toLocaleString()}</div>
              </div>
            )}
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-ink/10 text-xs">
              <span className={`w-2 h-2 rounded-full ${syncStatus === "synced" ? "bg-green-500" : syncStatus === "syncing" ? "bg-amber-500 animate-pulse" : "bg-red-500"}`} />
              <span className="font-medium text-ink/70 capitalize">{syncStatus}</span>
            </div>
            <Button size="sm" icon onClick={handleRefresh} className="h-8 w-8 p-0" title="Refresh sync">
              <RefreshCw className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* Phase tabs */}
        <div className="mt-4 flex gap-1 overflow-x-auto pb-2">
          {PHASES.map((p) => {
            const PhaseIcon = p.icon;
            const active = project?.current_phase === p.key;
            return (
              <button
                key={p.key}
                onClick={() => onPhaseChange?.(p.key)}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors border ${
                  active
                    ? "border-copper bg-copper/5 text-copper"
                    : "border-transparent text-ink/60 hover:bg-ink/5 hover:border-ink/10"
                }`}
              >
                <PhaseIcon className="w-4 h-4" />
                {p.label}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
