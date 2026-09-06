import { useState, useEffect } from "react";
import { api } from "../../lib/api";
import { useAuth } from "../../lib/auth";
import AppShell from "../../components/AppShell";

export default function SimulationDashboard() {
  const { user } = useAuth();
  const [tab, setTab] = useState("runs");
  const [runs, setRuns] = useState([]);
  const [profiles, setProfiles] = useState([]);
  const [scenarios, setScenarios] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = async () => {
    setLoading(true);
    setError("");
    try {
      const [runsRes, profilesRes, scenariosRes, analyticsRes] = await Promise.all([
        api.get("/simulation/runs"),
        api.get("/simulation/profiles"),
        api.get("/simulation/scenarios"),
        api.get("/simulation/analytics/comparison"),
      ]);
      setRuns(runsRes.data?.runs || []);
      setProfiles(profilesRes.data?.profiles || []);
      setScenarios(scenariosRes.data?.scenarios || []);
      setAnalytics(analyticsRes.data?.analytics || analyticsRes.data);
    } catch (err) {
      setError("Could not load simulation data.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [load]);

  return (
    <AppShell>
      <div className="px-10 py-10 max-w-6xl">
        <div className="overline text-copper">Simulation Lab</div>
        <h1 className="font-heading text-4xl font-bold text-ink mt-1">Student/Instructor Simulation Lab</h1>
        <p className="text-ink/60 mt-2 max-w-2xl">
          Controlled behavioral simulation for platform testing, metrics baselines, educational research, and planning.
          All simulated accounts are internal and do not appear as real learners in public views.
        </p>

        {error && (
          <div className="mt-6 p-4 rounded-xl border border-destructive/30 bg-destructive/5 text-destructive text-sm font-semibold">
            {error} <button onClick={load} className="ml-auto underline font-bold">Retry</button>
          </div>
        )}

        <div className="flex gap-2 mt-8 border-b border-ink/10">
          {["runs", "profiles", "scenarios", "analytics"].map((t) => (
            <button key={t} onClick={() => setTab(t)}
              className={`px-4 py-2 text-sm font-black uppercase tracking-wider ${tab === t ? "border-b-2 border-copper text-copper" : "text-ink/50 hover:text-ink"}`}>
              {t}
            </button>
          ))}
        </div>

        {loading && <p className="text-ink/45 py-16">Loading simulation lab…</p>}

        {!loading && tab === "runs" && (
          <div className="mt-6 space-y-4">
            <RunCreator onCreated={load} scenarios={scenarios} profiles={profiles} />
            {runs.length === 0 && <p className="text-ink/50 text-sm">No simulation runs yet.</p>}
            {runs.map((run) => (
              <div key={run.id} className="card-flat bg-white border border-ink/10 p-6 flex items-start justify-between gap-4">
                <div>
                  <div className="font-heading text-lg font-bold text-ink">{run.name}</div>
                  <div className="text-xs text-ink/50 mt-1">{run.description}</div>
                  <div className="flex gap-3 mt-2 text-xs font-bold text-ink/60">
                    <span>Scenario: {run.scenario_id}</span>
                    <span>Status: {run.status}</span>
                    <span>Events: {run.event_count}</span>
                    <span>Profiles: {run.profile_ids.length}</span>
                  </div>
                </div>
                <div className="flex gap-2 shrink-0">
                  {run.status === "draft" && <RunStarter runId={run.id} onDone={load} />}
                  {run.status === "running" && <RunStopper runId={run.id} onDone={load} />}
                  <button onClick={load} className="px-3 py-1.5 text-xs font-bold border border-ink/15 rounded hover:border-copper hover:text-copper">Refresh</button>
                </div>
              </div>
            ))}
          </div>
        )}

        {!loading && tab === "profiles" && (
          <div className="mt-6 grid sm:grid-cols-2 gap-4">
            {profiles.map((p) => (
              <div key={p.id} className="card-flat bg-white border border-ink/10 p-6">
                <div className="font-heading text-lg font-bold text-ink">{p.name}</div>
                <div className="text-xs font-black uppercase tracking-wider text-copper mt-1">{p.type}</div>
                <div className="text-xs text-ink/60 mt-2">{p.description}</div>
                <div className="text-[10px] font-mono text-ink/40 mt-2">key: {p.profile_key}</div>
              </div>
            ))}
            {profiles.length === 0 && <p className="text-ink/50 text-sm">No profiles loaded.</p>}
          </div>
        )}

        {!loading && tab === "scenarios" && (
          <div className="mt-6 space-y-4">
            {scenarios.map((s) => (
              <div key={s.id} className="card-flat bg-white border border-ink/10 p-6">
                <div className="font-heading text-lg font-bold text-ink">{s.name}</div>
                <div className="text-xs text-ink/50 font-mono">{s.id}</div>
                <div className="text-sm text-ink/70 mt-2">{s.description}</div>
                <div className="text-xs text-ink/50 mt-2">Config: {JSON.stringify(s.config)}</div>
              </div>
            ))}
          </div>
        )}

        {!loading && tab === "analytics" && analytics && (
          <div className="mt-6 space-y-4">
            <div className="grid sm:grid-cols-4 gap-4">
              <div className="card-flat bg-white border border-ink/10 p-6 text-center">
                <div className="font-heading text-3xl font-black text-ink">{analytics.real_events ?? 0}</div>
                <div className="text-xs font-bold text-ink/50 uppercase tracking-wider">Real Events</div>
              </div>
              <div className="card-flat bg-white border border-ink/10 p-6 text-center">
                <div className="font-heading text-3xl font-black text-copper">{analytics.simulated_events ?? 0}</div>
                <div className="text-xs font-bold text-ink/50 uppercase tracking-wider">Simulated Events</div>
              </div>
              <div className="card-flat bg-white border border-ink/10 p-6 text-center">
                <div className="font-heading text-3xl font-black text-ink">{analytics.real_completed_runs ?? 0}</div>
                <div className="text-xs font-bold text-ink/50 uppercase tracking-wider">Completed Runs</div>
              </div>
              <div className="card-flat bg-white border border-ink/10 p-6 text-center">
                <div className="font-heading text-3xl font-black text-ink">{analytics.simulated_student_profiles ?? 0}</div>
                <div className="text-xs font-bold text-ink/50 uppercase tracking-wider">Simulated Students</div>
              </div>
            </div>
            <p className="text-xs text-ink/50">Comparison analytics isolate simulation from real users. Use this to establish baselines and measure gaps.</p>
          </div>
        )}
      </div>
    </AppShell>
  );
}

function RunCreator({ onCreated, scenarios, profiles }) {
  const [name, setName] = useState("");
  const [scenarioId, setScenarioId] = useState(scenarios[0]?.id || "");
  const [profileIds, setProfileIds] = useState([]);
  const [courseSlugs, setCourseSlugs] = useState("multiplication-division-fractions-grade-4");
  const [creating, setCreating] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setCreating(true);
    try {
      const r = await api.post("/simulation/runs", {
        name,
        description: "",
        scenario_id: scenarioId,
        profile_ids: profileIds,
        course_slugs: courseSlugs.split(",").map((s) => s.trim()).filter(Boolean),
        config: {},
      });
      await api.post(`/simulation/runs/${r.data.run.id}/start`);
      onCreated();
    } catch (err) {
      alert("Failed to create/start run: " + (err?.response?.data?.detail || err.message));
    } finally {
      setCreating(false);
    }
  };

  return (
    <form onSubmit={submit} className="card-flat bg-white border border-ink/10 p-6 space-y-4">
      <div className="font-heading text-xl font-bold text-ink">New Simulation Run</div>
      <label className="block">
        <span className="text-[11px] font-bold uppercase tracking-wide text-ink/50">Run Name</span>
        <input required value={name} onChange={(e) => setName(e.target.value)} className="mt-1 w-full px-3 py-2.5 rounded-lg border border-ink/20 text-sm font-semibold" placeholder="e.g. Baseline Run 1" />
      </label>
      <label className="block">
        <span className="text-[11px] font-bold uppercase tracking-wide text-ink/50">Scenario</span>
        <select value={scenarioId} onChange={(e) => setScenarioId(e.target.value)} className="mt-1 w-full px-3 py-2.5 rounded-lg border border-ink/20 text-sm font-semibold">
          {scenarios.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
        </select>
      </label>
      <label className="block">
        <span className="text-[11px] font-bold uppercase tracking-wide text-ink/50">Profiles (comma-separated IDs)</span>
        <input value={profileIds.join(",")} onChange={(e) => setProfileIds(e.target.value.split(",").map((s) => s.trim()).filter(Boolean))} className="mt-1 w-full px-3 py-2.5 rounded-lg border border-ink/20 text-sm font-mono" placeholder={profiles.map((p) => p.id).join(",")} />
      </label>
      <label className="block">
        <span className="text-[11px] font-bold uppercase tracking-wide text-ink/50">Course Slugs (comma-separated)</span>
        <input value={courseSlugs} onChange={(e) => setCourseSlugs(e.target.value)} className="mt-1 w-full px-3 py-2.5 rounded-lg border border-ink/20 text-sm font-mono" />
      </label>
      <button type="submit" disabled={creating} className="px-6 py-2.5 bg-signal text-ink font-black rounded-lg hover:bg-signal/85 disabled:opacity-50">
        {creating ? "Starting…" : "Create & Start Run"}
      </button>
    </form>
  );
}

function RunStarter({ runId, onDone }) {
  const [starting, setStarting] = useState(false);
  const start = async () => {
    setStarting(true);
    try {
      await api.post(`/simulation/runs/${runId}/start`);
      onDone();
    } catch (err) {
      alert("Failed to start run.");
    } finally {
      setStarting(false);
    }
  };
  return (
    <button onClick={start} disabled={starting} className="px-3 py-1.5 text-xs font-bold bg-signal text-ink rounded hover:bg-signal/85 disabled:opacity-50">
      {starting ? "Starting…" : "Start"}
    </button>
  );
}

function RunStopper({ runId, onDone }) {
  const [stopping, setStopping] = useState(false);
  const stop = async () => {
    setStopping(true);
    try {
      await api.post(`/simulation/runs/${runId}/stop`);
      onDone();
    } catch (err) {
      alert("Failed to stop run.");
    } finally {
      setStopping(false);
    }
  };
  return (
    <button onClick={stop} disabled={stopping} className="px-3 py-1.5 text-xs font-bold border-2 border-destructive text-destructive rounded hover:bg-destructive/5 disabled:opacity-50">
      {stopping ? "Stopping…" : "Stop"}
    </button>
  );
}
