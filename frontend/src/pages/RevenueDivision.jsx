import { useEffect, useState } from "react";
import AppShell from "../components/AppShell";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import { DollarSign, Key, Shield, BookOpen, Clock, Users, FileText, Building, Plus, X, Check, Copy, ExternalLink, RefreshCw } from "lucide-react";
import { toast } from "sonner";

export default function RevenueDivision() {
  const { user } = useAuth();
  const [tab, setTab] = useState("keys");
  const [keys, setKeys] = useState([]);
  const [tiers, setTiers] = useState({});
  const [showCreateKey, setShowCreateKey] = useState(false);
  const [newKeyLabel, setNewKeyLabel] = useState("");
  const [newKeyTier, setNewKeyTier] = useState("free");
  const [newKeyResult, setNewKeyResult] = useState(null);
  const [busy, setBusy] = useState(false);
  const [freshKey, setFreshKey] = useState(null);
  const [revokeTarget, setRevokeTarget] = useState(null);

  const [licenses, setLicenses] = useState([]);
  const [publicCourses, setPublicCourses] = useState([]);

  const [compliance, setCompliance] = useState(null);
  const [associateFilter, setAssociateFilter] = useState("");

  const [workspaces, setWorkspaces] = useState([]);
  const [wsName, setWsName] = useState("");

  const [resume, setResume] = useState(null);

  useEffect(() => {
    loadKeys();
    api.get("/revenue/api-keys/tiers").then(r => setTiers(r.data.tiers || {})).catch(() => {});
    api.get("/revenue/courses/public").then(r => setPublicCourses(r.data.courses || [])).catch(() => {});
    api.get("/revenue/courses/my-licenses").then(r => setLicenses(r.data.licenses || [])).catch(() => {});
    loadWorkspaces();
    loadResume();
  }, []);

  const loadKeys = async () => {
    try { const r = await api.get("/revenue/api-keys"); setKeys(r.data.keys || []); } catch {}
  };

  const loadWorkspaces = async () => {
    if (user?.role === "admin" || user?.role === "executive_admin") {
      try { const r = await api.get("/revenue/sovereign/workspaces"); setWorkspaces(r.data.workspaces || []); } catch {}
    }
  };

  const loadResume = async () => {
    try { const r = await api.get("/revenue/resume/preview"); setResume(r.data); } catch {}
  };

  const loadCompliance = async () => {
    setBusy(true);
    try {
      const r = await api.get(`/revenue/employer/compliance?associate=${associateFilter}`);
      setCompliance(r.data);
    } catch { toast.error("Failed to load compliance data."); }
    finally { setBusy(false); }
  };

  const createKey = async (e) => {
    e.preventDefault();
    try {
      const r = await api.post("/revenue/api-keys", { label: newKeyLabel, tier: newKeyTier });
      setFreshKey(r.data.key);
      setNewKeyResult(r.data);
      setShowCreateKey(false);
      setNewKeyLabel("");
      loadKeys();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Failed to create key");
    }
  };

  const revokeKey = async (hash) => {
    try {
      await api.delete(`/revenue/api-keys/${hash}`);
      toast.success("Key revoked.");
      setRevokeTarget(null);
      loadKeys();
    } catch { toast.error("Failed to revoke key."); }
  };

  const createLicense = async (e) => {
    e.preventDefault();
    const form = e.target;
    try {
      const r = await api.post("/revenue/courses/license", {
        organization: form.org.value,
        course_slugs: Array.from(form.querySelectorAll("[name=courses]:checked")).map(c => c.value),
        seats: parseInt(form.seats.value) || 1,
      });
      toast.success(`License created: ${r.data.license_id.slice(0, 8)}...`);
      const lic = await api.get("/revenue/courses/my-licenses");
      setLicenses(lic.data.licenses || []);
    } catch (err) { toast.error(err?.response?.data?.detail || "License failed."); }
  };

  const createWorkspace = async (e) => {
    e.preventDefault();
    try {
      await api.post("/revenue/sovereign/workspace", { name: wsName, member_ids: [] });
      toast.success("Workspace created.");
      setWsName("");
      loadWorkspaces();
    } catch (err) { toast.error(err?.response?.data?.detail || "Failed."); }
  };

  const TabBtn = ({ id, icon: Icon, children }) => (
    <button
      onClick={() => setTab(id)}
      className={`px-4 py-2 text-sm font-bold border-b-2 inline-flex items-center gap-2 transition-colors ${
        tab === id ? "border-copper text-ink" : "border-transparent text-ink/50 hover:text-ink"
      }`}
    ><Icon className="w-4 h-4" /> {children}</button>
  );

  return (
    <AppShell>
      <div className="px-10 py-10 max-w-6xl">
        <div className="flex items-center gap-3 mb-2">
          <DollarSign className="w-6 h-6 text-copper" />
          <span className="overline text-copper">Revenue Division</span>
        </div>
        <h1 className="font-heading text-4xl font-bold">AI Revenue Operations</h1>
        <p className="text-ink/60 mt-2">API keys, credential verification, course licensing, compliance tracking, Sovereign workspaces, and resume builder.</p>

        {/* Tabs */}
        <div className="mt-8 flex gap-1 border-b border-ink/10 overflow-x-auto" role="tablist">
          <TabBtn id="keys" icon={Key}>API Keys</TabBtn>
          <TabBtn id="verify" icon={Shield}>Verification</TabBtn>
          <TabBtn id="courses" icon={BookOpen}>Course Licensing</TabBtn>
          <TabBtn id="compliance" icon={Clock}>Compliance</TabBtn>
          <TabBtn id="sovereign" icon={Users}>Sovereign Seats</TabBtn>
          <TabBtn id="resume" icon={FileText}>Resume Builder</TabBtn>
        </div>

        {/* ── API KEYS ──────────────────────────────────────────────────────────── */}
        {tab === "keys" && (
          <div className="mt-6 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="font-heading text-xl font-bold">Your API Keys</h2>
              <button onClick={() => { setShowCreateKey(true); setFreshKey(null); }} className="btn-primary inline-flex items-center gap-2 text-sm">
                <Plus className="w-4 h-4" /> Create Key
              </button>
            </div>

            {/* Tier info */}
            {Object.keys(tiers).length > 0 && (
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                {Object.entries(tiers).map(([tier, cfg]) => (
                  <div key={tier} className="bg-white rounded-xl border border-ink/10 p-4 text-center">
                    <p className="text-xs font-bold uppercase text-ink/50">{tier}</p>
                    <p className="text-lg font-bold font-mono text-ink mt-1">{(cfg.requests_per_hour || 0).toLocaleString()}/hr</p>
                    <p className="text-xs text-ink/50">{(cfg.max_tokens_per_call || 0).toLocaleString()} tokens max</p>
                  </div>
                ))}
              </div>
            )}

            {/* Create key form */}
            {showCreateKey && (
              <form onSubmit={createKey} className="bg-white rounded-xl border border-ink/10 p-5 space-y-4">
                <h3 className="font-heading font-bold">New API Key</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs text-ink/50 uppercase mb-1">Label</label>
                    <input required value={newKeyLabel} onChange={e => setNewKeyLabel(e.target.value)}
                      className="w-full px-3 py-2 border border-ink/20 rounded-lg text-sm" placeholder="My App" />
                  </div>
                  <div>
                    <label className="block text-xs text-ink/50 uppercase mb-1">Tier</label>
                    <select value={newKeyTier} onChange={e => setNewKeyTier(e.target.value)}
                      className="w-full px-3 py-2 border border-ink/20 rounded-lg text-sm">
                      {Object.keys(tiers).map(t => <option key={t} value={t}>{t}</option>)}
                    </select>
                  </div>
                </div>
                <div className="flex gap-3">
                  <button type="submit" className="btn-primary text-sm">Generate Key</button>
                  <button type="button" onClick={() => setShowCreateKey(false)} className="text-sm text-ink/50 hover:text-ink">Cancel</button>
                </div>
              </form>
            )}

            {/* Fresh key display */}
            {freshKey && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-4">
                <p className="text-xs font-bold text-yellow-700 uppercase">Save this key — it will never be shown again</p>
                <div className="flex items-center gap-2 mt-2">
                  <code className="flex-1 px-3 py-2 bg-white border border-yellow-300 rounded text-sm font-mono break-all">{freshKey}</code>
                  <button onClick={() => { navigator.clipboard.writeText(freshKey); toast.success("Copied!"); }}
                    className="px-3 py-2 bg-yellow-100 rounded-lg hover:bg-yellow-200"><Copy className="w-4 h-4" /></button>
                </div>
              </div>
            )}

            {/* Key list */}
            {keys.length > 0 && (
              <div className="bg-white rounded-xl border border-ink/10 overflow-hidden">
                {keys.map(k => (
                  <div key={k.key_hash} className="flex items-center justify-between p-4 border-b border-ink/10 last:border-0">
                    <div>
                      <p className="font-medium text-ink text-sm">{k.label}</p>
                      <p className="text-xs text-ink/50 font-mono">{k.key_hash.slice(0, 16)}... · {k.tier} · {k.usage_count || 0} calls</p>
                    </div>
                    {k.active ? (
                      <button onClick={() => setRevokeTarget(k)}
                        className="text-xs text-destructive hover:text-destructive/80">Revoke</button>
                    ) : (
                      <span className="text-xs text-ink/30">Revoked</span>
                    )}
                  </div>
                ))}
              </div>
            )}

            {keys.length === 0 && !showCreateKey && (
              <div className="text-center py-12 text-ink/50">
                <Key className="w-12 h-12 mx-auto mb-4 opacity-30" />
                <p>No API keys yet. Create one to get started.</p>
              </div>
            )}
          </div>
        )}

        {/* ── CREDENTIAL VERIFICATION ──────────────────────────────────────────── */}
        {tab === "verify" && (
          <div className="mt-6 space-y-6">
            <div className="bg-white rounded-xl border border-ink/10 p-6">
              <h2 className="font-heading text-xl font-bold flex items-center gap-2"><Shield className="w-5 h-5 text-copper" /> Verify a Credential</h2>
              <p className="text-sm text-ink/60 mt-1">Enter a verification code to check a candidate's credential.</p>
              <form className="mt-4 flex gap-3" onSubmit={async (e) => {
                e.preventDefault();
                const code = e.target.code.value.trim();
                if (!code) return;
                try {
                  const r = await api.post("/revenue/verify-credential", { verification_code: code });
                  toast.success(`✅ Valid: ${r.data.credential} — ${r.data.holder}`);
                  e.target.code.value = "";
                } catch (err) {
                  toast.error(err?.response?.data?.detail || "Credential not found");
                }
              }}>
                <input name="code" required placeholder="Enter verification code"
                  className="flex-1 px-4 py-2 border border-ink/20 rounded-lg text-sm" />
                <button type="submit" className="btn-primary text-sm flex items-center gap-2"><Shield className="w-4 h-4" /> Verify</button>
              </form>
            </div>

            {user?.role !== "student" && (
              <div className="bg-white rounded-xl border border-ink/10 p-6">
                <h2 className="font-heading text-xl font-bold flex items-center gap-2"><Building className="w-5 h-5 text-copper" /> Batch Verify</h2>
                <p className="text-sm text-ink/60 mt-1">Verify multiple codes at once (comma-separated). Instructor+.</p>
                <form className="mt-4 flex gap-3" onSubmit={async (e) => {
                  e.preventDefault();
                  const codes = e.target.codes.value.trim();
                  if (!codes) return;
                  try {
                    const r = await api.get(`/revenue/employer/verify-batch?codes=${encodeURIComponent(codes)}`);
                    toast.success(`${r.data.valid}/${r.data.total} valid`);
                  } catch (err) { toast.error("Batch verify failed."); }
                }}>
                  <input name="codes" required placeholder="CODE1, CODE2, CODE3"
                    className="flex-1 px-4 py-2 border border-ink/20 rounded-lg text-sm" />
                  <button type="submit" className="btn-primary text-sm">Verify Batch</button>
                </form>
              </div>
            )}

            <div className="bg-ink/5 rounded-xl p-6 text-center">
              <p className="text-sm text-ink/50">Employers: Use the public API to batch-verify credentials at scale.</p>
              <p className="text-xs text-ink/30 mt-1">POST /api/revenue/verify-credential with {"{\"verification_code\": \"...\"}"}</p>
            </div>
          </div>
        )}

        {/* ── COURSE LICENSING ─────────────────────────────────────────────────── */}
        {tab === "courses" && (
          <div className="mt-6 grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-white rounded-xl border border-ink/10 p-6">
              <h2 className="font-heading text-xl font-bold flex items-center gap-2"><BookOpen className="w-5 h-5 text-copper" /> License Courses</h2>
              <p className="text-sm text-ink/60 mt-1">License WAI curriculum for your organization.</p>
              <form onSubmit={createLicense} className="mt-4 space-y-4">
                <div>
                  <label className="block text-xs text-ink/50 uppercase mb-1">Organization</label>
                  <input name="org" required className="w-full px-3 py-2 border border-ink/20 rounded-lg text-sm" placeholder="Your Company, Inc." />
                </div>
                <div>
                  <label className="block text-xs text-ink/50 uppercase mb-1">Seats</label>
                  <input name="seats" type="number" min="1" max="1000" defaultValue="5"
                    className="w-full px-3 py-2 border border-ink/20 rounded-lg text-sm" />
                </div>
                <div>
                  <p className="text-xs text-ink/50 uppercase mb-2">Select Courses</p>
                  {publicCourses.length > 0 ? (
                    <div className="space-y-2 max-h-48 overflow-y-auto">
                      {publicCourses.map(c => (
                        <label key={c.slug} className="flex items-center gap-3 text-sm cursor-pointer">
                          <input type="checkbox" name="courses" value={c.slug} className="rounded border-ink/30 text-copper" />
                          <span>{c.title} <span className="text-ink/40">({c.hours}h)</span></span>
                        </label>
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-ink/50 italic">Loading courses...</p>
                  )}
                </div>
                <button type="submit" className="btn-primary text-sm w-full">Create License</button>
              </form>
            </div>

            <div className="bg-white rounded-xl border border-ink/10 p-6">
              <h2 className="font-heading text-xl font-bold flex items-center gap-2"><Building className="w-5 h-5 text-copper" /> Your Licenses</h2>
              {licenses.length > 0 ? (
                <div className="mt-4 space-y-3">
                  {licenses.map(l => (
                    <div key={l.license_id} className="p-3 bg-ink/5 rounded-lg">
                      <p className="font-medium text-sm">{l.organization}</p>
                      <p className="text-xs text-ink/50 mt-0.5">{l.seats} seats · {l.course_slugs?.length || 0} courses · {l.active ? "Active" : "Inactive"}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-ink/50 mt-4">No active licenses.</p>
              )}
            </div>
          </div>
        )}

        {/* ── COMPLIANCE HOURS ──────────────────────────────────────────────────── */}
        {tab === "compliance" && (
          <div className="mt-6 space-y-4">
            <div className="bg-white rounded-xl border border-ink/10 p-6">
              <h2 className="font-heading text-xl font-bold flex items-center gap-2"><Clock className="w-5 h-5 text-copper" /> Compliance Hours Dashboard</h2>
              <p className="text-sm text-ink/60 mt-1">Track apprentice compliance hours by cohort. Instructor+.</p>
              <div className="flex gap-3 mt-4">
                <input value={associateFilter} onChange={e => setAssociateFilter(e.target.value)}
                  placeholder="Filter by cohort (optional)" className="flex-1 px-4 py-2 border border-ink/20 rounded-lg text-sm" />
                <button onClick={loadCompliance} disabled={busy} className="btn-primary text-sm flex items-center gap-2">
                  {busy ? <RefreshCw className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />} Load
                </button>
              </div>
            </div>

            {compliance && (
              <div className="grid grid-cols-3 gap-4">
                <div className="bg-white rounded-xl border border-ink/10 p-5 text-center">
                  <p className="text-xs text-ink/50 uppercase">Apprentices</p>
                  <p className="text-2xl font-bold font-mono text-ink">{compliance.total_apprentices}</p>
                </div>
                <div className="bg-white rounded-xl border border-ink/10 p-5 text-center">
                  <p className="text-xs text-ink/50 uppercase">Total Hours</p>
                  <p className="text-2xl font-bold font-mono text-ink">{compliance.total_hours}</p>
                </div>
                <div className="bg-white rounded-xl border border-ink/10 p-5 text-center">
                  <p className="text-xs text-ink/50 uppercase">Avg Hours</p>
                  <p className="text-2xl font-bold font-mono text-ink">{compliance.average_hours}</p>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ── SOVEREIGN WORKSPACES ──────────────────────────────────────────────── */}
        {tab === "sovereign" && (
          <div className="mt-6 space-y-4">
            <div className="bg-white rounded-xl border border-ink/10 p-6">
              <h2 className="font-heading text-xl font-bold flex items-center gap-2"><Users className="w-5 h-5 text-copper" /> Sovereign AI Workspaces</h2>
              <p className="text-sm text-ink/60 mt-1">Multi-user Sovereign AI with shared memory per workspace. Admin+.</p>
              <form onSubmit={createWorkspace} className="mt-4 flex gap-3">
                <input value={wsName} onChange={e => setWsName(e.target.value)} required
                  placeholder="Workspace name" className="flex-1 px-4 py-2 border border-ink/20 rounded-lg text-sm" />
                <button type="submit" className="btn-primary text-sm flex items-center gap-2"><Plus className="w-4 h-4" /> Create</button>
              </form>
            </div>

            {workspaces.length > 0 && (
              <div className="bg-white rounded-xl border border-ink/10 overflow-hidden">
                {workspaces.map(ws => (
                  <div key={ws.workspace_id} className="p-4 border-b border-ink/10 last:border-0 flex items-center justify-between">
                    <div>
                      <p className="font-medium text-ink">{ws.name}</p>
                      <p className="text-xs text-ink/50">{ws.member_ids?.length || 0} members · Created {ws.created_at ? new Date(ws.created_at).toLocaleDateString() : ""}</p>
                    </div>
                    <span className="text-xs text-ink/30 font-mono">{ws.workspace_id?.slice(0, 8)}...</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* ── RESUME BUILDER ────────────────────────────────────────────────────── */}
        {tab === "resume" && (
          <div className="mt-6 space-y-4">
            <div className="bg-white rounded-xl border border-ink/10 p-6">
              <h2 className="font-heading text-xl font-bold flex items-center gap-2"><FileText className="w-5 h-5 text-copper" /> AI Resume Builder</h2>
              <p className="text-sm text-ink/60 mt-1">Auto-generated resume from your portfolio and credentials.</p>
            </div>

            {resume && (
              <div className="bg-white rounded-xl border border-ink/10 p-6">
                <div className="border-b border-ink/10 pb-4 mb-4">
                  <p className="text-xl font-bold text-ink">{resume.name || "Your Name"}</p>
                  <p className="text-sm text-ink/50">{resume.email}</p>
                </div>

                {resume.portfolio_bio && (
                  <div className="mb-4">
                    <p className="text-xs font-bold text-ink/50 uppercase mb-1">Summary</p>
                    <p className="text-sm text-ink/70">{resume.portfolio_bio}</p>
                  </div>
                )}

                <div className="mb-4">
                  <p className="text-xs font-bold text-ink/50 uppercase mb-2">Credentials ({resume.credentials?.length || 0})</p>
                  {resume.credentials?.length > 0 ? (
                    <div className="space-y-2">
                      {resume.credentials.map((c, i) => (
                        <div key={i} className="flex items-center gap-3 text-sm p-2 bg-ink/5 rounded-lg">
                          <Check className="w-4 h-4 text-green-600 shrink-0" />
                          <span className="text-ink/80">{c.title}</span>
                          <span className="text-xs text-ink/40 ml-auto">{c.issued_at ? new Date(c.issued_at).toLocaleDateString() : ""}</span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-ink/50 italic">No credentials yet.</p>
                  )}
                </div>

                {resume.portfolio_projects?.length > 0 && (
                  <div>
                    <p className="text-xs font-bold text-ink/50 uppercase mb-2">Projects ({resume.portfolio_projects.length})</p>
                    <div className="space-y-2">
                      {resume.portfolio_projects.map((p, i) => (
                        <div key={i} className="text-sm p-2 bg-ink/5 rounded-lg">
                          <p className="font-medium text-ink">{p.title || p.name || `Project ${i + 1}`}</p>
                          <p className="text-xs text-ink/50">{p.description || ""}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <div className="mt-6 pt-4 border-t border-ink/10">
                  <button className="btn-primary text-sm flex items-center gap-2" onClick={() => {
                    const win = window.open("", "_blank");
                    if (win) {
                      win.document.write(`<html><head><title>Resume - ${resume.name}</title></head><body><pre>${JSON.stringify(resume, null, 2)}</pre></body></html>`);
                      win.document.close();
                    }
                  }}>
                    <ExternalLink className="w-4 h-4" /> Preview Full Resume
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {revokeTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
          <div className="bg-white rounded-2xl p-6 max-w-sm w-full shadow-xl">
            <p className="font-bold text-ink text-sm mb-1">Revoke API key?</p>
            <p className="text-xs text-ink/60 mb-4">"{revokeTarget.label}" — this cannot be undone.</p>
            <div className="flex gap-2 justify-end">
              <button onClick={() => setRevokeTarget(null)} className="text-sm px-4 py-2 text-ink/60 hover:text-ink">Cancel</button>
              <button onClick={() => revokeKey(revokeTarget.key_hash)}
                className="text-sm font-bold bg-destructive hover:bg-destructive/90 text-white px-4 py-2 rounded-lg">
                Revoke Key
              </button>
            </div>
          </div>
        </div>
      )}
    </AppShell>
  );
}
