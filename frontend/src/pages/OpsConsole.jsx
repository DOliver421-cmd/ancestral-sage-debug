import { useState, useEffect, useCallback } from "react";
import AppShell from "../components/AppShell";
import PageBack from "../components/PageBack";
import { api } from "../lib/api";
import { toast } from "sonner";

// ══════════════════════════════════════════════════════════════════════════
// OPS CONSOLE — executive control over notifications, email, and platform
// health. Three panels over systems that already run the site; nothing here
// is decorative. Every action hits a real /api/ops/* endpoint (executive_admin
// only, enforced server-side).
// ══════════════════════════════════════════════════════════════════════════

const ROLES = ["student", "trial_pass", "instructor", "support_staff", "oversight", "admin", "executive_admin"];
const TIERS = ["free", "member", "plus", "pro", "patron", "executive"];
const KINDS = ["info", "success", "warning", "error"];

const KIND_STYLES = {
  info: "bg-blue-50 text-blue-700 border-blue-200",
  success: "bg-green-50 text-green-700 border-green-200",
  warning: "bg-amber-50 text-amber-700 border-amber-200",
  error: "bg-red-50 text-red-700 border-red-200",
};

export default function OpsConsole() {
  const [tab, setTab] = useState("notify");

  return (
    <AppShell>
      <PageBack />
      <div className="max-w-5xl mx-auto px-4 py-6">
        <h1 className="font-heading font-bold text-2xl text-ink">Ops Console</h1>
        <p className="text-sm text-ink/60 mt-1">
          Operational control for notifications, email delivery, and platform health.
          Executive access only.
        </p>

        <div className="flex gap-2 mt-5 mb-6 flex-wrap">
          {[
            ["notify", "🔔 Notifications"],
            ["email", "✉️ Email"],
            ["health", "🩺 Health & Audit"],
          ].map(([k, label]) => (
            <button
              key={k}
              onClick={() => setTab(k)}
              className={`px-4 py-2 rounded-lg text-sm font-medium border transition ${
                tab === k ? "bg-ink text-paper border-ink" : "bg-white text-ink border-ink/15 hover:border-ink/40"
              }`}
            >
              {label}
            </button>
          ))}
        </div>

        {tab === "notify" && <NotifyPanel />}
        {tab === "email" && <EmailPanel />}
        {tab === "health" && <HealthPanel />}
      </div>
    </AppShell>
  );
}

/* ── Notifications ─────────────────────────────────────────────────────── */

function NotifyPanel() {
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [link, setLink] = useState("");
  const [kind, setKind] = useState("info");
  const [roles, setRoles] = useState([]);
  const [tiers, setTiers] = useState([]);
  const [busy, setBusy] = useState(false);
  const [campaigns, setCampaigns] = useState([]);
  const [lastSent, setLastSent] = useState(null);

  const loadCampaigns = useCallback(async () => {
    try {
      const r = await api.get("/ops/notifications/delivery");
      setCampaigns(r.data.campaigns || []);
    } catch {
      /* non-fatal */
    }
  }, []);

  useEffect(() => { loadCampaigns(); }, [loadCampaigns]);

  const toggle = (list, setList, v) =>
    setList(list.includes(v) ? list.filter((x) => x !== v) : [...list, v]);

  const send = async () => {
    if (!title.trim() || !body.trim()) { toast.error("Title and message are required."); return; }
    setBusy(true);
    try {
      const r = await api.post("/ops/notifications/send", {
        title: title.trim(), body: body.trim(), kind,
        link: link.trim() || null, target_roles: roles, target_tiers: tiers,
      });
      setLastSent(r.data);
      toast.success(`Sent to ${r.data.sent} user${r.data.sent === 1 ? "" : "s"}.`);
      setTitle(""); setBody(""); setLink("");
      loadCampaigns();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Send failed.");
    } finally { setBusy(false); }
  };

  const testSelf = async () => {
    setBusy(true);
    try {
      await api.post("/ops/notifications/test");
      toast.success("Test notification sent to your own bell.");
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Test failed.");
    } finally { setBusy(false); }
  };

  return (
    <div className="grid md:grid-cols-2 gap-6">
      <div className="card-flat p-5">
        <h2 className="font-heading font-semibold text-lg">Compose notification</h2>
        <p className="text-xs text-ink/50 mt-1">Delivered to each selected user's bell. No email involved.</p>

        <label className="block text-xs font-medium text-ink/70 mt-4">Title</label>
        <input className="w-full mt-1 rounded-lg border border-ink/15 px-3 py-2 text-sm" maxLength={120}
          value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Maintenance window" />

        <label className="block text-xs font-medium text-ink/70 mt-3">Message</label>
        <textarea className="w-full mt-1 rounded-lg border border-ink/15 px-3 py-2 text-sm" rows={4} maxLength={2000}
          value={body} onChange={(e) => setBody(e.target.value)} placeholder="What should users know?" />

        <label className="block text-xs font-medium text-ink/70 mt-3">In-app link (optional)</label>
        <input className="w-full mt-1 rounded-lg border border-ink/15 px-3 py-2 text-sm"
          value={link} onChange={(e) => setLink(e.target.value)} placeholder="/store" />

        <label className="block text-xs font-medium text-ink/70 mt-3">Kind</label>
        <div className="flex gap-2 mt-1">
          {KINDS.map((k) => (
            <button key={k} onClick={() => setKind(k)}
              className={`px-3 py-1.5 rounded-lg text-xs border capitalize ${kind === k ? KIND_STYLES[k] : "border-ink/15 text-ink/50"}`}>
              {k}
            </button>
          ))}
        </div>

        <div className="grid grid-cols-2 gap-4 mt-4">
          <div>
            <p className="text-xs font-medium text-ink/70">Roles</p>
            <div className="flex flex-wrap gap-1.5 mt-1.5">
              {ROLES.map((r) => (
                <button key={r} onClick={() => toggle(roles, setRoles, r)}
                  className={`px-2 py-1 rounded-md text-[11px] border ${roles.includes(r) ? "bg-ink text-paper border-ink" : "border-ink/15 text-ink/60"}`}>
                  {r}
                </button>
              ))}
            </div>
          </div>
          <div>
            <p className="text-xs font-medium text-ink/70">Tiers</p>
            <div className="flex flex-wrap gap-1.5 mt-1.5">
              {TIERS.map((t) => (
                <button key={t} onClick={() => toggle(tiers, setTiers, t)}
                  className={`px-2 py-1 rounded-md text-[11px] border ${tiers.includes(t) ? "bg-ink text-paper border-ink" : "border-ink/15 text-ink/60"}`}>
                  {t}
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="flex gap-2 mt-5">
          <button onClick={send} disabled={busy}
            className="btn-primary px-4 py-2 text-sm disabled:opacity-50">
            {busy ? "Sending…" : "Send to segment"}
          </button>
          <button onClick={testSelf} disabled={busy}
            className="px-4 py-2 text-sm rounded-lg border border-ink/20 text-ink/70 hover:border-ink/50">
            Test on myself
          </button>
        </div>
        {lastSent && (
          <p className="text-xs text-ink/50 mt-3">
            Last send: <b>{lastSent.sent}</b> recipients
            {lastSent.segment?.tiers?.length ? ` · tiers: ${lastSent.segment.tiers.join(", ")}` : ""}
            {lastSent.segment?.roles?.length ? ` · roles: ${lastSent.segment.roles.join(", ")}` : ""}
          </p>
        )}
      </div>

      <div className="card-flat p-5">
        <div className="flex items-center justify-between">
          <h2 className="font-heading font-semibold text-lg">Delivery log</h2>
          <button onClick={loadCampaigns} className="text-xs text-ink/50 hover:text-ink">refresh</button>
        </div>
        {campaigns.length === 0 ? (
          <p className="text-sm text-ink/40 mt-4">No notifications sent yet from the console.</p>
        ) : (
          <div className="mt-3 space-y-2 max-h-[420px] overflow-y-auto">
            {campaigns.map((c, i) => (
              <div key={i} className="border border-ink/10 rounded-lg p-3">
                <div className="flex items-center justify-between gap-2">
                  <span className={`text-[11px] px-2 py-0.5 rounded-full border capitalize ${KIND_STYLES[c.kind] || KIND_STYLES.info}`}>
                    {c.kind}
                  </span>
                  <span className="text-[11px] text-ink/40">{(c.created_at || "").slice(0, 16).replace("T", " ")}</span>
                </div>
                <p className="text-sm font-medium mt-1.5">{c.title}</p>
                <p className="text-xs text-ink/50 mt-0.5">
                  {c.recipients} sent · {c.read} read ({c.recipients ? Math.round((c.read / c.recipients) * 100) : 0}%)
                </p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

/* ── Email ─────────────────────────────────────────────────────────────── */

function EmailPanel() {
  const [status, setStatus] = useState(null);
  const [to, setTo] = useState("");
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState(null);

  const load = useCallback(async () => {
    try { setStatus((await api.get("/ops/email/status")).data); } catch { /* non-fatal */ }
  }, []);
  useEffect(() => { load(); }, [load]);

  const sendTest = async () => {
    setBusy(true); setResult(null);
    try {
      const r = await api.post("/ops/email/test", { to_email: to.trim() });
      setResult({ ok: true, via: r.data.delivered_via });
      toast.success(`Delivered via ${r.data.delivered_via}.`);
    } catch (e) {
      setResult({ ok: false, msg: e?.response?.data?.detail || "Send failed." });
      toast.error(e?.response?.data?.detail || "Send failed.");
    } finally { setBusy(false); }
  };

  return (
    <div className="grid md:grid-cols-2 gap-6">
      <div className="card-flat p-5">
        <h2 className="font-heading font-semibold text-lg">Delivery chain</h2>
        <p className="text-xs text-ink/50 mt-1">
          Password resets, purchase receipts, and admin alerts go out through this chain.
          Keys live in Railway — never in this page.
        </p>
        {!status ? (
          <p className="text-sm text-ink/40 mt-4">Loading…</p>
        ) : (
          <div className="mt-4 space-y-2">
            {status.chain.map((p) => (
              <div key={p.provider} className="flex items-center justify-between border border-ink/10 rounded-lg px-3 py-2.5">
                <div>
                  <p className="text-sm font-medium">{p.provider}</p>
                  <p className="text-[11px] text-ink/40 font-mono">{p.detail || "not set"}</p>
                </div>
                <span className={`text-xs px-2 py-1 rounded-full border ${p.configured ? KIND_STYLES.success : KIND_STYLES.error}`}>
                  {p.configured ? "configured" : "missing"}
                </span>
              </div>
            ))}
            <p className="text-xs text-ink/50 mt-2">
              Active provider: <b>{status.primary || "none — email is down"}</b>
              {status.notify_to ? ` · alerts to ${status.notify_to}` : ""}
            </p>
          </div>
        )}
      </div>

      <div className="card-flat p-5">
        <h2 className="font-heading font-semibold text-lg">Send a test email</h2>
        <p className="text-xs text-ink/50 mt-1">Exercises the real production chain. Send it to yourself.</p>
        <input className="w-full mt-3 rounded-lg border border-ink/15 px-3 py-2 text-sm" type="email"
          value={to} onChange={(e) => setTo(e.target.value)} placeholder="you@example.com" />
        <button onClick={sendTest} disabled={busy || !to.trim()}
          className="btn-primary px-4 py-2 text-sm mt-3 disabled:opacity-50">
          {busy ? "Sending…" : "Send test"}
        </button>
        {result && (
          <p className={`text-xs mt-3 ${result.ok ? "text-green-700" : "text-red-700"}`}>
            {result.ok ? `Delivered via ${result.via}.` : result.msg}
          </p>
        )}
      </div>
    </div>
  );
}

/* ── Health & audit ────────────────────────────────────────────────────── */

function HealthPanel() {
  const [data, setData] = useState(null);
  const [loaded, setLoaded] = useState(false);

  const load = useCallback(async () => {
    setLoaded(false);
    try { setData((await api.get("/ops/console")).data); }
    catch (e) { toast.error(e?.response?.data?.detail || "Console load failed."); }
    finally { setLoaded(true); }
  }, []);
  useEffect(() => { load(); }, [load]);

  if (!loaded) return <p className="text-sm text-ink/40">Loading console…</p>;
  if (!data) return null;

  const Section = ({ title, children }) => (
    <div className="card-flat p-5">
      <h2 className="font-heading font-semibold text-lg mb-3">{title}</h2>
      {children}
    </div>
  );

  const ErrorNote = ({ section }) =>
    section?.error ? <p className="text-xs text-red-600">Section error: {section.error}</p> : null;

  const d = data.fcc_denials || {};
  const a = data.audit || {};
  const g = data.gateway || {};
  const p = data.platform || {};

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <p className="text-xs text-ink/40">Snapshot at {(data.generated_at || "").slice(0, 19).replace("T", " ")} · v{data.version}</p>
        <button onClick={load} className="text-xs text-ink/50 hover:text-ink">refresh</button>
      </div>

      <div className="grid md:grid-cols-3 gap-4">
        <div className="card-flat p-4">
          <p className="text-xs text-ink/50">Users</p>
          <p className="text-2xl font-bold mt-1">{p.users?.active ?? "—"}</p>
          <p className="text-[11px] text-ink/40">active of {p.users?.total ?? "—"} total</p>
        </div>
        <div className="card-flat p-4">
          <p className="text-xs text-ink/50">AI providers live</p>
          <p className="text-2xl font-bold mt-1">{g.active_providers ?? "—"}</p>
          <p className="text-[11px] text-ink/40">{g.error ? "gateway status unavailable" : "via the LLM gateway"}</p>
        </div>
        <div className="card-flat p-4">
          <p className="text-xs text-ink/50">Access denials (all time)</p>
          <p className="text-2xl font-bold mt-1">{d.total ?? "—"}</p>
          <p className="text-[11px] text-ink/40">{d.last_7d ?? "—"} in the last 7 days</p>
        </div>
      </div>

      <Section title="Top denied paths">
        <ErrorNote section={d} />
        {d.top?.length ? (
          <table className="w-full text-sm">
            <thead><tr className="text-left text-xs text-ink/40 border-b border-ink/10">
              <th className="py-1.5">Path</th><th>Reason</th><th className="text-right">Count</th>
            </tr></thead>
            <tbody>
              {d.top.map((t, i) => (
                <tr key={i} className="border-b border-ink/5">
                  <td className="py-1.5 font-mono text-xs">{t.path}</td>
                  <td className="text-xs">{t.reason}</td>
                  <td className="text-right text-xs">{t.count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : <p className="text-sm text-ink/40">No denials recorded.</p>}
      </Section>

      <div className="grid md:grid-cols-2 gap-5">
        <Section title={`Audit trail (${a.total ?? "—"} events)`}>
          <ErrorNote section={a} />
          <div className="space-y-1.5 max-h-72 overflow-y-auto">
            {(a.tail || []).map((t, i) => (
              <div key={i} className="text-xs border-b border-ink/5 pb-1.5">
                <span className="font-medium">{t.action}</span>
                <span className="text-ink/40"> · {t.actor_id ? `actor ${String(t.actor_id).slice(0, 8)}` : "system"}</span>
                <span className="text-ink/30"> · {(t.at || "").slice(0, 16).replace("T", " ")}</span>
              </div>
            ))}
            {!a.tail?.length && <p className="text-sm text-ink/40">No events.</p>}
          </div>
        </Section>

        <Section title={`Exec audit (${data.exec_audit?.total ?? "—"} events)`}>
          <ErrorNote section={data.exec_audit} />
          <div className="space-y-1.5 max-h-72 overflow-y-auto">
            {(data.exec_audit?.tail || []).map((t, i) => (
              <div key={i} className="text-xs border-b border-ink/5 pb-1.5">
                <span className="font-medium">{t.action || t.control || "event"}</span>
                <span className="text-ink/30"> · {(t.created_at || t.at || "").slice(0, 16).replace("T", " ")}</span>
              </div>
            ))}
            {!data.exec_audit?.tail?.length && <p className="text-sm text-ink/40">No events.</p>}
          </div>
        </Section>
      </div>

      <Section title="Collections">
        <ErrorNote section={data.collections} />
        <div className="flex flex-wrap gap-1.5">
          {(data.collections || []).map((c, i) => (
            <span key={i} className="text-[11px] border border-ink/10 rounded-md px-2 py-1 text-ink/60">
              {c.collection} <b className="text-ink">{c.count ?? "?"}</b>
            </span>
          ))}
        </div>
      </Section>
    </div>
  );
}
