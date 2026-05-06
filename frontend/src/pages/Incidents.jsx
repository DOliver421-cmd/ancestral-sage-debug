import { useCallback, useEffect, useState } from "react";
import AppShell from "../components/AppShell";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import { toast } from "sonner";
import { ShieldAlert, Plus } from "lucide-react";

const TYPES = ["near_miss", "first_aid", "injury", "property_damage", "safety_violation", "other"];
const SEVS = ["low", "medium", "high", "critical"];
const SEV_COLOR = { low: "badge-outline", medium: "badge-copper", high: "badge-copper", critical: "bg-destructive text-white px-2 py-0.5 text-xs font-bold uppercase" };

export default function Incidents() {
  const { user } = useAuth();
  const isStaff = user?.role === "instructor" || user?.role === "admin";
  const [list, setList] = useState([]);
  const [filter, setFilter] = useState("");
  const [form, setForm] = useState({ type: "near_miss", severity: "low", description: "", site_slug: "", photo_url: "" });
  const [showForm, setShowForm] = useState(!isStaff);

  const load = useCallback(() => {
    if (!isStaff) return Promise.resolve();
    return api.get(`/incidents${filter ? `?status=${filter}` : ""}`).then((r) => setList(r.data));
  }, [filter, isStaff]);
  useEffect(() => { load(); }, [load]);

  const submit = async () => {
    if (!form.description) { toast.error("Description required"); return; }
    try {
      await api.post("/incidents", form);
      toast.success("Incident reported");
      setForm({ type: "near_miss", severity: "low", description: "", site_slug: "", photo_url: "" });
      load();
    } catch { toast.error("Submit failed"); }
  };

  const resolve = async (id) => {
    const resolution = prompt("Resolution notes:");
    if (!resolution) return;
    try { await api.post(`/incidents/${id}/resolve`, { resolution }); toast.success("Resolved"); load(); }
    catch { toast.error("Resolve failed"); }
  };

  return (
    <AppShell>
      <div className="px-10 py-10 max-w-6xl">
        <div className="overline text-copper">Safety Reporting</div>
        <h1 className="font-heading text-4xl font-bold mt-2 flex items-center gap-3"><ShieldAlert className="w-8 h-8 text-copper" /> Incidents</h1>
        <p className="text-ink/60 mt-2 max-w-2xl">Report it, log it, fix it. Every report is auto-stamped, audit-logged, and notifies admin if severity ≥ medium.</p>

        {(showForm || !isStaff) && (
          <div className="card-flat p-6 mt-8" data-testid="incident-form">
            <div className="flex items-center gap-2 mb-4"><Plus className="w-5 h-5 text-copper" /><h3 className="font-heading text-xl font-bold">Report an incident</h3></div>
            <div className="grid sm:grid-cols-2 gap-3">
              <Select label="Type" value={form.type} options={TYPES} onChange={(v) => setForm({ ...form, type: v })} testid="inc-type" />
              <Select label="Severity" value={form.severity} options={SEVS} onChange={(v) => setForm({ ...form, severity: v })} testid="inc-sev" />
              <Input label="Site (optional)" value={form.site_slug} onChange={(v) => setForm({ ...form, site_slug: v })} testid="inc-site" />
              <Input label="Photo URL (optional)" value={form.photo_url} onChange={(v) => setForm({ ...form, photo_url: v })} testid="inc-photo" />
            </div>
            <div className="mt-3">
              <label className="overline text-ink/60">Description</label>
              <textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} rows={3}
                placeholder="What happened? What were you doing? Anything unusual?"
                className="w-full mt-1 px-3 py-2 border border-ink/20 focus:border-ink focus:outline-none focus:ring-2 focus:ring-signal text-sm"
                data-testid="inc-desc" />
            </div>
            <button onClick={submit} className="btn-primary mt-4" data-testid="btn-submit-incident">Submit Report</button>
          </div>
        )}

        {isStaff && (
          <>
            <div className="flex gap-2 mt-8 flex-wrap">
              {[["", "All"], ["open", "Open"], ["resolved", "Resolved"]].map(([k, label]) => (
                <button key={k} onClick={() => setFilter(k)}
                  className={`px-4 py-2 text-xs font-bold uppercase tracking-widest border ${filter === k ? "bg-ink text-white border-ink" : "bg-white text-ink border-ink/20"}`}
                  data-testid={`inc-filter-${k || "all"}`}>{label}</button>
              ))}
              <button onClick={() => setShowForm(!showForm)} className="btn-copper ml-auto inline-flex items-center gap-2" data-testid="btn-toggle-form">
                <Plus className="w-4 h-4" /> {showForm ? "Hide form" : "Report new"}
              </button>
            </div>

            <div className="space-y-3 mt-6">
              {list.length === 0 && <div className="card-flat p-8 text-center text-ink/50">No incidents.</div>}
              {list.map((i) => (
                <div key={i.id} className="card-flat p-5" data-testid={`incident-${i.id}`}>
                  <div className="flex items-start justify-between gap-3 flex-wrap">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="badge-ink">{i.type.replace(/_/g, " ")}</span>
                        <span className={SEV_COLOR[i.severity]}>{i.severity}</span>
                        <span className={i.status === "resolved" ? "badge-signal" : "badge-outline"}>{i.status}</span>
                      </div>
                      <div className="text-sm text-ink/80 mt-2">{i.description}</div>
                      <div className="text-xs text-ink/50 mt-2 font-mono">
                        Reported by {i.reporter?.full_name || "?"} · {new Date(i.created_at).toLocaleString()}
                        {i.site_slug && ` · ${i.site_slug}`}
                      </div>
                      {i.photo_url && <a href={i.photo_url} target="_blank" rel="noreferrer" className="text-copper text-xs font-mono break-all underline mt-1 inline-block">{i.photo_url}</a>}
                      {i.resolution && (
                        <div className="mt-2 p-2 bg-bone text-xs italic border-l-2 border-copper">Resolution: {i.resolution}</div>
                      )}
                    </div>
                    {i.status === "open" && user?.role === "admin" && (
                      <button onClick={() => resolve(i.id)} className="btn-copper text-xs" data-testid={`resolve-${i.id}`}>Resolve</button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    </AppShell>
  );
}

function Input({ label, value, onChange, testid }) {
  return (
    <label className="block">
      <span className="overline text-ink/60">{label}</span>
      <input value={value} onChange={(e) => onChange(e.target.value)}
        className="w-full mt-1 px-3 py-2 border border-ink/20 focus:border-ink focus:outline-none focus:ring-2 focus:ring-signal text-sm"
        data-testid={testid} />
    </label>
  );
}
function Select({ label, value, options, onChange, testid }) {
  return (
    <label className="block">
      <span className="overline text-ink/60">{label}</span>
      <select value={value} onChange={(e) => onChange(e.target.value)}
        className="w-full mt-1 px-3 py-2 border border-ink/20 focus:border-ink focus:outline-none focus:ring-2 focus:ring-signal text-sm"
        data-testid={testid}>
        {options.map((o) => <option key={o} value={o}>{o.replace(/_/g, " ")}</option>)}
      </select>
    </label>
  );
}
