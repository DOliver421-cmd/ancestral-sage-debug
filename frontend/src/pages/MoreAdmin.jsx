import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import AppShell from "../components/AppShell";
import { api } from "../lib/api";
import { Flag, Trash2, RefreshCw, ArrowLeft, Loader2, Shield } from "lucide-react";
import { toast } from "sonner";

export default function MoreAdmin() {
  const [flags, setFlags] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [purging, setPurging] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const r = await api.get("/more/admin/flags");
      setFlags(r.data.flags || []);
      setTotal(r.data.total || 0);
    } catch {
      toast.error("Could not load flags");
    } finally {
      setLoading(false);
    }
  };

  const purge = async () => {
    if (!window.confirm("Run manual purge? This deletes all expired content now.")) return;
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

  useEffect(() => { load(); }, []);

  return (
    <AppShell>
      <div className="max-w-4xl mx-auto px-6 py-10">
        <div className="flex items-center gap-4 mb-8">
          <Link to="/more" className="text-ink/50 hover:text-ink transition-colors">
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div className="flex-1">
            <h1 className="font-heading text-3xl font-extrabold">M.O.R.E. Admin</h1>
            <p className="text-ink/50 text-sm mt-1">Content flags and manual purge controls</p>
          </div>
          <div className="flex gap-3">
            <button onClick={load} className="btn-ghost text-sm flex items-center gap-2">
              <RefreshCw className="w-4 h-4" /> Refresh
            </button>
            <button
              onClick={purge}
              disabled={purging}
              className="btn-primary text-sm flex items-center gap-2 disabled:opacity-50"
            >
              {purging ? <Loader2 className="w-4 h-4 animate-spin" /> : <Trash2 className="w-4 h-4" />}
              Run Purge
            </button>
          </div>
        </div>

        {/* Stats bar */}
        <div className="grid grid-cols-3 gap-4 mb-8">
          {[
            { label: "Pending Flags", value: total, icon: Flag, color: "text-red-500" },
            { label: "Auto-Purge Cycle", value: "30d / 60m", icon: Trash2, color: "text-copper" },
            { label: "AI Moderator", value: "Active", icon: Shield, color: "text-signal" },
          ].map(s => (
            <div key={s.label} className="card-flat p-5">
              <div className={`${s.color} mb-1`}><s.icon className="w-5 h-5" /></div>
              <div className="font-heading text-2xl font-black">{s.value}</div>
              <div className="overline text-xs text-ink/50 mt-1">{s.label}</div>
            </div>
          ))}
        </div>

        {/* Flags table */}
        <div className="card-flat">
          <div className="px-6 py-4 border-b border-ink/10 flex items-center justify-between">
            <h2 className="font-heading font-bold">Pending Flags ({total})</h2>
          </div>
          {loading ? (
            <div className="flex justify-center py-10">
              <Loader2 className="w-5 h-5 animate-spin text-copper" />
            </div>
          ) : flags.length === 0 ? (
            <div className="text-center py-10 text-ink/40 text-sm">No pending flags — community is clean.</div>
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
                  <div className="text-xs text-ink/40 shrink-0">
                    {new Date(f.created_at).toLocaleDateString()}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}
