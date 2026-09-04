import { useState, useEffect, useCallback } from "react";
import { Link } from "react-router-dom";
import AppShell from "../components/AppShell";
import { api } from "../lib/api";
import {
  AlertCircle,
  ArrowLeft,
  Check,
  Flag,
  Loader2,
  RefreshCw,
  Shield,
  Trash2,
  X,
} from "lucide-react";
import { toast } from "sonner";

const TABS = [
  { key: "queue", label: "Review Queue", icon: Shield },
  { key: "flags", label: "Flags", icon: Flag },
  { key: "appeals", label: "Appeals", icon: AlertCircle },
];

function formatDate(value) {
  return value ? new Date(value).toLocaleDateString() : "Unknown";
}

function QueueCard({ item, onApprove, onReject, busy }) {
  const type = item.content_type || item.type;
  return (
    <div className="px-6 py-4 flex items-start gap-4">
      <Shield className="w-4 h-4 text-copper shrink-0 mt-0.5" />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-sm font-bold capitalize">{type}</span>
          <span className="badge-outline">{item.category || item.violation_category || "review"}</span>
        </div>
        <p className="text-sm text-ink/75 mt-2 whitespace-pre-wrap">{item.preview || item.content || item.description || item.title}</p>
        {item.moderation_note && <div className="text-xs text-ink/50 mt-2">Oliver: {item.moderation_note}</div>}
        <div className="text-xs text-ink/30 mt-1">
          ID: {item.id} {item.author_name ? `- ${item.author_name}` : ""} - {formatDate(item.created_at)}
        </div>
      </div>
      <div className="flex gap-2 shrink-0">
        <button
          onClick={() => onApprove(type, item.id)}
          disabled={busy}
          className="btn-primary text-xs flex items-center gap-1 disabled:opacity-50"
        >
          <Check className="w-3.5 h-3.5" /> Approve
        </button>
        <button
          onClick={() => onReject(type, item.id)}
          disabled={busy}
          className="btn-ghost text-xs flex items-center gap-1 disabled:opacity-50"
        >
          <X className="w-3.5 h-3.5" /> Reject
        </button>
      </div>
    </div>
  );
}

export default function MoreAdmin() {
  const [activeTab, setActiveTab] = useState("queue");
  const [queue, setQueue] = useState({ posts: [], needs: [], appeals: [], posts_total: 0, needs_total: 0, appeals_total: 0 });
  const [flags, setFlags] = useState([]);
  const [flagTotal, setFlagTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [purging, setPurging] = useState(false);
  const [confirmPurge, setConfirmPurge] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [queueR, flagsR] = await Promise.all([
        api.get("/more/admin/queue"),
        api.get("/more/admin/flags"),
      ]);
      setQueue({
        posts: queueR.data.posts || [],
        needs: queueR.data.needs || [],
        appeals: queueR.data.appeals || [],
        posts_total: queueR.data.posts_total || 0,
        needs_total: queueR.data.needs_total || 0,
        appeals_total: queueR.data.appeals_total || 0,
      });
      setFlags(flagsR.data.flags || []);
      setFlagTotal(flagsR.data.total || 0);
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Could not load moderation tools");
    } finally {
      setLoading(false);
    }
  }, []);

  const approve = async (type, id) => {
    if (!["post", "need"].includes(type)) return;
    setActingId(id);
    try {
      await api.post(`/more/admin/queue/${type}/${id}/approve`);
      toast.success("Content approved");
      await load();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Approval failed");
    } finally {
      setActingId(null);
    }
  };

  const reject = async (type, id) => {
    if (!["post", "need"].includes(type)) return;
    const reason = window.prompt("Optional rejection note") || "";
    setActingId(id);
    try {
      await api.post(`/more/admin/queue/${type}/${id}/reject`, null, { params: { reason } });
      toast.success("Content rejected");
      await load();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Rejection failed");
    } finally {
      setActingId(null);
    }
  };

  const doPurge = async () => {
    setConfirmPurge(false);
    setPurging(true);
    try {
      const r = await api.post("/more/purge");
      const { posts, chats, flags: f } = r.data.purged;
      toast.success(`Purged: ${posts} posts, ${chats} chats, ${f} flags`);
      await load();
    } catch {
      toast.error("Purge failed");
    } finally {
      setPurging(false);
    }
  };

  useEffect(() => { load(); }, [load]);

  const reviewItems = [...(queue.posts || []), ...(queue.needs || [])];
  const reviewTotal = queue.posts_total + queue.needs_total;

  return (
    <AppShell>
      <div className="max-w-5xl mx-auto px-6 py-10">
        <div className="flex items-center gap-4 mb-8">
          <Link to="/more" className="text-ink/50 hover:text-ink transition-colors">
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div className="flex-1">
            <h1 className="font-heading text-3xl font-extrabold">M.O.R.E. Admin</h1>
            <p className="text-ink/50 text-sm mt-1">Review held content, flags, appeals, and purge expired items</p>
          </div>
          <div className="flex gap-3">
            <button onClick={load} className="btn-ghost text-sm flex items-center gap-2">
              <RefreshCw className="w-4 h-4" /> Refresh
            </button>
            <button
              onClick={() => setConfirmPurge(true)}
              disabled={purging}
              className="btn-primary text-sm flex items-center gap-2 disabled:opacity-50"
            >
              {purging ? <Loader2 className="w-4 h-4 animate-spin" /> : <Trash2 className="w-4 h-4" />}
              Run Purge
            </button>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-4 mb-8">
          {[
            { label: "Review Queue", value: reviewTotal, icon: Shield, color: "text-copper" },
            { label: "Pending Flags", value: flagTotal, icon: Flag, color: "text-red-500" },
            { label: "Appeals", value: queue.appeals_total, icon: AlertCircle, color: "text-signal" },
          ].map(s => (
            <div key={s.label} className="card-flat p-5">
              <div className={`${s.color} mb-1`}><s.icon className="w-5 h-5" /></div>
              <div className="font-heading text-2xl font-black">{s.value}</div>
              <div className="overline text-xs text-ink/50 mt-1">{s.label}</div>
            </div>
          ))}
        </div>

        <div className="flex gap-2 mb-4 flex-wrap">
          {TABS.map(({ key, label, icon: Icon }) => (
            <button
              key={key}
              onClick={() => setActiveTab(key)}
              className={`flex items-center gap-2 px-4 py-2 text-sm font-bold border ${activeTab === key ? "bg-ink text-white border-ink" : "bg-white text-ink border-ink/20 hover:border-ink"}`}
            >
              <Icon className="w-4 h-4" /> {label}
            </button>
          ))}
        </div>

        <div className="card-flat">
          {loading ? (
            <div className="flex justify-center py-10">
              <Loader2 className="w-5 h-5 animate-spin text-copper" />
            </div>
          ) : activeTab === "queue" ? (
            reviewItems.length === 0 ? (
              <div className="text-center py-10 text-ink/40 text-sm">No held posts or needs waiting for review.</div>
            ) : (
              <div className="divide-y divide-ink/5">
                {reviewItems.map(item => (
                  <QueueCard key={`${item.content_type}-${item.id}`} item={item} onApprove={approve} onReject={reject} busy={actingId === item.id} />
                ))}
              </div>
            )
          ) : activeTab === "flags" ? (
            flags.length === 0 ? (
              <div className="text-center py-10 text-ink/40 text-sm">No pending flags.</div>
            ) : (
              <div className="divide-y divide-ink/5">
                {flags.map(f => (
                  <div key={f.id} className="px-6 py-4 flex items-start gap-4">
                    <Flag className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium capitalize">{f.target_type} flagged</div>
                      <div className="text-xs text-ink/50 mt-0.5">{f.reason}</div>
                      <div className="text-xs text-ink/30 mt-1">ID: {f.target_id}</div>
                    </div>
                    <div className="text-xs text-ink/40 shrink-0">{formatDate(f.created_at)}</div>
                  </div>
                ))}
              </div>
            )
          ) : queue.appeals.length === 0 ? (
            <div className="text-center py-10 text-ink/40 text-sm">No pending appeals.</div>
          ) : (
            <div className="divide-y divide-ink/5">
              {queue.appeals.map(a => (
                <div key={a.id} className="px-6 py-4">
                  <div className="text-sm font-bold">Appeal for {a.content_type || a.target_type || "content"}</div>
                  <p className="text-sm text-ink/75 mt-2 whitespace-pre-wrap">{a.preview || a.appeal_text || a.reason || "No appeal text provided."}</p>
                  <div className="text-xs text-ink/30 mt-2">ID: {a.id} - {formatDate(a.created_at)}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
      {confirmPurge && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-sm p-6">
            <h2 className="font-heading font-bold text-lg text-slate-900 mb-2">Run Manual Purge</h2>
            <p className="text-sm text-slate-600 mb-6">This deletes all expired content now. This cannot be undone.</p>
            <div className="flex justify-end gap-3">
              <button onClick={doPurge} disabled={purging} className="text-sm px-4 py-2 rounded-lg bg-red-600 text-white font-bold hover:bg-red-700 disabled:opacity-50">
                {purging ? "Purging..." : "Run Purge"}
              </button>
            </div>
          </div>
        </div>
      )}
    </AppShell>
  );
}

