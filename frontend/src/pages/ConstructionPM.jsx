import { useState, useEffect } from "react";
import { constructionApi } from "@/lib/construction-pm";
import ProjectNavBar from "@/components/construction/ProjectNavBar";
import EstimatorGrid from "@/components/construction/EstimatorGrid";
import TakeoffCanvas from "@/components/construction/TakeoffCanvas";
import FieldLogForm from "@/components/construction/FieldLogForm";
import EVMDashboard from "@/components/construction/EVMDashboard";
import { toast } from "sonner";

export default function ConstructionPM() {
  const [projects, setProjects] = useState([]);
  const [selected, setSelected] = useState(null);
  const [estimate, setEstimate] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    constructionApi.listProjects().then((r) => {
      setProjects(r.data.projects || []);
      if (r.data.projects?.length && !selected) setSelected(r.data.projects[0]);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  const [blueprints, setBlueprints] = useState([]);

  useEffect(() => {
    if (!selected) return;
    constructionApi.getTakeoff(selected.id).then((r) => {
      setEstimate(r.data.estimate || null);
      setBlueprints(r.data.blueprints || []);
    }).catch(() => {});
  }, [selected]);

  const handleCreateProject = async () => {
    const job = window.prompt("Job number (e.g., E-2026-001):");
    if (!job) return;
    const client = window.prompt("Client name:");
    if (!client) return;
    try {
      const r = await constructionApi.createProject({ job_number: job, client_name: client, current_phase: "pre_con" });
      setProjects((prev) => [r.data, ...prev]);
      setSelected(r.data);
      toast.success("Project created");
    } catch (e) {
      toast.error(`Create failed: ${e?.response?.data?.detail || e?.message || "unknown error"}`);
    }
  };

  if (loading) return <div className="p-12 text-ink font-heading">Loading Electrical Project Management…</div>;

  return (
    <div className="min-h-screen bg-bone text-ink">
      <ProjectNavBar project={selected} />

      <div className="max-w-7xl mx-auto px-6 py-8">
        {!selected && (
          <div className="bg-white border border-ink/10 rounded-xl p-12 text-center">
            <div className="w-12 h-12 rounded-full bg-copper/10 flex items-center justify-center mx-auto mb-4 text-copper font-bold">
              🔌
            </div>
            <h2 className="font-bold text-xl text-ink mb-2">No electrical projects yet</h2>
            <p className="text-ink/60 mb-6">Create your first project to begin estimating, tracking field labor, and running EVM.</p>
            <ButtonCta onClick={handleCreateProject} />
          </div>
        )}

        {selected && (
          <>
            <div className="grid lg:grid-cols-12 gap-8">
              {/* Left column: estimating + field logging */}
              <div className="lg:col-span-7 space-y-8">
                <EstimatorGrid projectId={selected.id} estimate={estimate} onEstimateChange={setEstimate} />
                <FieldLogForm projectId={selected.id} items={estimate?.line_items || []} onLogSubmit={() => constructionApi.getTakeoff(selected.id).then((r) => setEstimate(r.data.estimate || null))} />
              </div>

              {/* Right column: takeoff canvas + EVM */}
              <div className="lg:col-span-5 space-y-8">
                <TakeoffCanvas blueprints={blueprints} selectedSheet={blueprints[0]?.sheet_number} />
                <EVMDashboard projectId={selected.id} />
              </div>
            </div>

            {/* Bottom: blueprint upload */}
            <div className="mt-8 bg-white border border-ink/10 rounded-xl p-6">
              <h3 className="font-bold text-lg text-ink mb-4">Blueprint Storage</h3>
              <p className="text-xs text-ink/60 mb-4">Upload PDF/CAD plan sets. Sheets are indexed by sheet number for the takeoff canvas overlay.</p>
              <div className="flex gap-3">
                <input id="bp-upload" type="file" accept=".pdf,.dwg,.dxf" className="sr-only" />
                <Button size="sm" onClick={() => document.getElementById("bp-upload")?.click()}>
                  Upload Blueprint Sheet
                </Button>
                <span className="text-xs text-ink/50 ml-auto">Sheets: {blueprints.length}</span>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

function ButtonCta({ onClick }) {
  return (
    <button onClick={onClick} className="inline-flex items-center gap-2 bg-copper text-white font-bold px-6 py-3 rounded-xl hover:bg-copper/90 transition-colors">
      Create Project
    </button>
  );
}
