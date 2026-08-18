import { useState, useEffect } from "react";
import PublicNav from "../components/PublicNav";
import BackButton from "../components/BackButton";
import { api } from "../lib/api";
import { toast } from "sonner";

const TABS = [
  { key: "applications", label: "📋 Applications" },
  { key: "awards", label: "🏅 Awards & Milestones" },
  { key: "pledges", label: "🤝 Pledges" },
  { key: "funds", label: "💰 Funds" },
];

const APP_STATUS = ["submitted", "under_review", "approved", "denied", "matched", "all"];
const fmtUsd = (c) => "$" + ((c || 0) / 100).toLocaleString(undefined, { maximumFractionDigits: 0 });

export default function AdminScholarships() {
  const [tab, setTab] = useState("applications");
  const [apps, setApps] = useState([]);
  const [awards, setAwards] = useState([]);
  const [pledges, setPledges] = useState([]);
  const [funds, setFunds] = useState([]);
  const [filter, setFilter] = useState("submitted");
  const [note, setNote] = useState({});
  const [newFund, setNewFund] = useState({ title: "", category: "", description: "", goal_cents: 25000 });

  async function loadApps() {
    const r = await api.get("/scholarships/admin/applications", { params: { status: filter } });
    setApps(r.data.applications || []);
  }
  async function loadAll() {
    api.get("/scholarships/admin/awards").then((r) => setAwards(r.data.awards || [])).catch(() => {});
    api.get("/scholarships/admin/pledges").then((r) => setPledges(r.data.pledges || [])).catch(() => {});
    api.get("/scholarships/funds").then((r) => setFunds(r.data.funds || [])).catch(() => {});
  }

  useEffect(() => { if (tab === "applications") loadApps(); }, [tab, filter]);
  useEffect(() => { loadAll(); }, []);

  async function review(appId, status) {
    try {
      await api.patch(`/scholarships/admin/applications/${appId}`, { status, note: note[appId] || "" });
      toast.success(status === "approved" ? "Approved — matched to a pledge if one is waiting." : "Updated.");
      setNote((n) => ({ ...n, [appId]: "" }));
      loadApps(); loadAll();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Update failed.");
    }
  }

  async function verify(awardId, milestoneId, verified) {
    try {
      await api.patch(`/scholarships/admin/awards/${awardId}/milestones/${milestoneId}`, { verified });
      toast.success(verified ? "Milestone verified — funds release against progress." : "Reopened.");
      loadAll();
    } catch (e) {
      toast.error("Milestone update failed.");
    }
  }

  async function createFund() {
    try {
      await api.post("/scholarships/admin/funds", newFund);
      toast.success("Fund created.");
      setNewFund({ title: "", category: "", description: "", goal_cents: 25000 });
      loadAll();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Could not create fund.");
    }
  }

  return (
    <div style={{ background: "#faf9f7", minHeight: "100dvh" }}>
      <PublicNav />
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-10">
        <BackButton to="/admin" />
        <div className="mt-6">
          <div className="overline text-copper">Scholarship Committee</div>
          <h1 className="font-heading text-3xl font-black text-ink mt-1">Sponsor-a-Scholarship admin.</h1>
          <p className="text-ink/60 mt-2 text-sm max-w-2xl leading-relaxed">
            Review applications, match approved scholars to paid pledges, verify milestones so funds release against
            real progress, and manage funds. Every action is audited.
          </p>
        </div>

        {/* TABS */}
        <div className="flex gap-2 flex-wrap mt-6">
          {TABS.map((t) => (
            <button key={t.key} onClick={() => setTab(t.key)}
              className={`text-xs font-bold px-4 py-2 rounded-full border transition-colors ${tab === t.key ? "bg-ink text-bone border-ink" : "border-ink/20 text-ink/60 hover:border-ink/40"}`}>
              {t.label}
            </button>
          ))}
        </div>

        {/* APPLICATIONS */}
        {tab === "applications" && (
          <>
            <div className="flex gap-2 flex-wrap mt-5">
              {APP_STATUS.map((s) => (
                <button key={s} onClick={() => setFilter(s)}
                  className={`text-[11px] font-bold px-3 py-1 rounded-full border ${filter === s ? "bg-copper text-white border-copper" : "border-ink/20 text-ink/50"}`}>
                  {s}
                </button>
              ))}
            </div>
            <div className="space-y-4 mt-5">
              {apps.length === 0 && <p className="text-sm text-ink/40 py-10 text-center">No applications in this state.</p>}
              {apps.map((a) => (
                <div key={a.id} className="rounded-2xl p-5" style={{ background: "#fff", border: "1px solid #eee7db" }}>
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="font-heading font-extrabold text-ink">{a.applicant_name}</div>
                    <span className="text-[11px] font-bold px-2.5 py-1 rounded-full" style={{ background: "#fef3c7", color: "#8a5a00" }}>{a.fund_title}</span>
                  </div>
                  <div className="text-xs text-ink/50 mt-1">{a.applicant_email} · submitted {new Date(a.created_at).toLocaleDateString()}</div>
                  <div className="grid md:grid-cols-3 gap-3 mt-3">
                    <div className="rounded-xl p-3 text-xs leading-relaxed text-ink/75" style={{ background: "#faf9f7" }}>
                      <div className="font-extrabold uppercase tracking-wide text-[10px]" style={{ color: "#92400e" }}>Need</div>
                      {a.need_statement}
                    </div>
                    <div className="rounded-xl p-3 text-xs leading-relaxed text-ink/75" style={{ background: "#faf9f7" }}>
                      <div className="font-extrabold uppercase tracking-wide text-[10px]" style={{ color: "#92400e" }}>Community</div>
                      {a.contribution}
                    </div>
                    <div className="rounded-xl p-3 text-xs leading-relaxed text-ink/75" style={{ background: "#faf9f7" }}>
                      <div className="font-extrabold uppercase tracking-wide text-[10px]" style={{ color: "#92400e" }}>Goal</div>
                      {a.goal}
                    </div>
                  </div>
                  <div className="flex flex-wrap items-center gap-2 mt-4">
                    <input value={note[a.id] || ""} onChange={(e) => setNote((n) => ({ ...n, [a.id]: e.target.value }))} placeholder="Committee note (optional)"
                      className="flex-1 min-w-[180px] text-xs rounded-lg px-3 py-2 border" style={{ borderColor: "#ddd3c0" }} />
                    <button onClick={() => review(a.id, "under_review")} className="text-xs font-bold px-3 py-2 rounded-lg" style={{ background: "#fef3c7", color: "#8a5a00" }}>Mark under review</button>
                    <button onClick={() => review(a.id, "approved")} className="text-xs font-bold px-3 py-2 rounded-lg" style={{ background: "#d1fae5", color: "#065f46" }}>Approve & match →</button>
                    <button onClick={() => review(a.id, "denied")} className="text-xs font-bold px-3 py-2 rounded-lg" style={{ background: "#fee2e2", color: "#b91c1c" }}>Deny</button>
                  </div>
                </div>
              ))}
            </div>
          </>
        )}

        {/* AWARDS */}
        {tab === "awards" && (
          <div className="space-y-4 mt-6">
            {awards.length === 0 && <p className="text-sm text-ink/40 py-10 text-center">No awards yet. Approve an application to create one.</p>}
            {awards.map((a) => {
              const ms = a.milestones || [];
              const done = ms.filter((m) => m.status === "verified").length;
              return (
                <div key={a.id} className="rounded-2xl p-5" style={{ background: "#fff", border: "1px solid #eee7db" }}>
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div>
                      <div className="font-heading font-extrabold text-ink">{a.applicant_name || "Scholar"}</div>
                      <div className="text-xs text-ink/50">Goal: {a.recipient_goal || "—"} · {a.status} · {fmtUsd(a.amount_cents)}</div>
                    </div>
                    <span className="text-[11px] font-bold px-2.5 py-1 rounded-full" style={{ background: done === ms.length && ms.length ? "#d1fae5" : "#fef3c7", color: done === ms.length && ms.length ? "#065f46" : "#8a5a00" }}>
                      {done}/{ms.length} milestones verified
                    </span>
                  </div>
                  <div className="mt-3 space-y-2">
                    {ms.map((m) => (
                      <div key={m.id} className="flex flex-wrap items-center justify-between gap-2 rounded-lg px-3 py-2" style={{ background: "#faf9f7" }}>
                        <span className="text-sm text-ink/80">{m.status === "verified" ? "✅" : "⏳"} {m.title}</span>
                        {m.status !== "verified" ? (
                          <button onClick={() => verify(a.id, m.id, true)} className="text-[11px] font-bold px-3 py-1.5 rounded-lg" style={{ background: "#d1fae5", color: "#065f46" }}>Verify milestone</button>
                        ) : (
                          <button onClick={() => verify(a.id, m.id, false)} className="text-[11px] font-bold px-3 py-1.5 rounded-lg" style={{ background: "#eee", color: "#444" }}>Reopen</button>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* PLEDGES */}
        {tab === "pledges" && (
          <div className="mt-6 rounded-2xl overflow-hidden" style={{ background: "#fff", border: "1px solid #eee7db" }}>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr style={{ background: "#faf9f7" }}>
                    {["Sponsor", "Tier", "Amount", "Status", "Date"].map((h) => (
                      <th key={h} className="text-left px-4 py-3 text-xs uppercase tracking-wide text-ink/50 font-bold">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {pledges.map((p) => (
                    <tr key={p.id} className="border-t" style={{ borderColor: "#f0eadf" }}>
                      <td className="px-4 py-3 text-ink/80">{p.sponsor_name}<div className="text-[11px] text-ink/40">{p.sponsor_email}</div></td>
                      <td className="px-4 py-3 text-ink/70">{p.tier}</td>
                      <td className="px-4 py-3 font-bold text-ink">{fmtUsd(p.amount_cents)}</td>
                      <td className="px-4 py-3"><span className="text-[11px] font-bold px-2.5 py-1 rounded-full" style={{ background: p.status === "paid" ? "#d1fae5" : p.status === "matched" ? "#dbeafe" : p.status === "committed" ? "#dbeafe" : "#fef3c7", color: "#444" }}>{p.status}</span></td>
                      <td className="px-4 py-3 text-ink/50">{new Date(p.created_at).toLocaleDateString()}</td>
                    </tr>
                  ))}
                  {pledges.length === 0 && <tr><td colSpan={5} className="px-4 py-8 text-center text-ink/40 text-sm">No pledges yet.</td></tr>}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* FUNDS */}
        {tab === "funds" && (
          <div className="mt-6">
            <div className="grid md:grid-cols-2 gap-5">
              <div className="rounded-2xl p-5" style={{ background: "#fff", border: "1px solid #eee7db" }}>
                <h3 className="font-heading font-extrabold text-ink">Create a fund</h3>
                <input value={newFund.title} onChange={(e) => setNewFund({ ...newFund, title: e.target.value })} placeholder="Fund title"
                  className="mt-3 w-full text-sm rounded-lg px-3 py-2 border" style={{ borderColor: "#ddd3c0" }} />
                <input value={newFund.category} onChange={(e) => setNewFund({ ...newFund, category: e.target.value })} placeholder="Category (e.g. workforce-arts)"
                  className="mt-2 w-full text-sm rounded-lg px-3 py-2 border" style={{ borderColor: "#ddd3c0" }} />
                <textarea rows={2} value={newFund.description} onChange={(e) => setNewFund({ ...newFund, description: e.target.value })} placeholder="What this fund covers"
                  className="mt-2 w-full text-sm rounded-lg px-3 py-2 border resize-none" style={{ borderColor: "#ddd3c0" }} />
                <input type="number" value={newFund.goal_cents} onChange={(e) => setNewFund({ ...newFund, goal_cents: Number(e.target.value) })} placeholder="Goal (cents)"
                  className="mt-2 w-full text-sm rounded-lg px-3 py-2 border" style={{ borderColor: "#ddd3c0" }} />
                <button onClick={createFund} className="mt-3 text-xs font-bold px-4 py-2 rounded-lg" style={{ background: "#1f2933", color: "#fff" }}>Create fund</button>
              </div>
              <div className="space-y-3">
                {funds.map((f) => (
                  <div key={f.id} className="rounded-2xl p-4" style={{ background: "#fff", border: "1px solid #eee7db" }}>
                    <div className="flex justify-between gap-2">
                      <div className="font-bold text-sm text-ink">{f.title}</div>
                      <span className="text-[11px] font-bold" style={{ color: "#8a5a00" }}>{fmtUsd(f.raised_cents || 0)} / {fmtUsd(f.goal_cents)}</span>
                    </div>
                    <div className="h-2 rounded-full mt-2" style={{ background: "#eee7db" }}>
                      <div className="h-2 rounded-full" style={{ width: Math.min(100, Math.round(((f.raised_cents || 0) / Math.max(f.goal_cents, 1)) * 100)) + "%", background: "#E8A51E" }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
