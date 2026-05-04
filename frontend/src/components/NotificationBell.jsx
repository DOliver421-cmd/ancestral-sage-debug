import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import { Bell, Check, CheckCheck } from "lucide-react";
import { toast } from "sonner";

const KIND_COLOR = {
  success: "bg-signal text-ink",
  warning: "bg-copper text-white",
  danger: "bg-destructive text-white",
  info: "bg-ink text-white",
};

export default function NotificationBell() {
  const [open, setOpen] = useState(false);
  const [data, setData] = useState({ items: [], unread: 0 });

  const load = () => api.get("/notifications/me").then((r) => setData(r.data)).catch(() => {});
  useEffect(() => {
    load();
    const t = setInterval(load, 30000);
    return () => clearInterval(t);
  }, []);

  const markRead = async (id) => {
    await api.post(`/notifications/${id}/read`, {});
    load();
  };
  const markAll = async () => {
    await api.post("/notifications/read-all", {});
    toast.success("All marked read");
    load();
  };

  return (
    <div className="relative">
      <button onClick={() => setOpen(!open)} className="relative p-2 hover:bg-white/5 transition-colors" data-testid="btn-notif-bell">
        <Bell className="w-5 h-5 text-white" />
        {data.unread > 0 && (
          <span className="absolute -top-0.5 -right-0.5 bg-signal text-ink text-[10px] font-black w-4 h-4 flex items-center justify-center rounded-full" data-testid="notif-badge">
            {data.unread > 9 ? "9+" : data.unread}
          </span>
        )}
      </button>
      {open && (
        <div className="fixed lg:absolute right-2 lg:right-0 top-14 lg:top-12 w-80 lg:w-96 bg-white border border-ink/20 shadow-2xl z-50 max-h-[70vh] overflow-y-auto" data-testid="notif-drawer">
          <div className="px-4 py-3 bg-ink text-white flex items-center justify-between">
            <span className="overline text-signal">Notifications</span>
            {data.unread > 0 && (
              <button onClick={markAll} className="text-xs uppercase tracking-widest font-bold flex items-center gap-1 hover:text-signal" data-testid="btn-mark-all">
                <CheckCheck className="w-3 h-3" /> Mark all read
              </button>
            )}
          </div>
          {data.items.length === 0 ? (
            <div className="p-8 text-center text-ink/50 text-sm">No notifications.</div>
          ) : (
            <div className="divide-y divide-ink/10">
              {data.items.map((n) => (
                <div key={n.id} className={`p-4 hover:bg-bone ${n.read ? "opacity-60" : ""}`} data-testid={`notif-${n.id}`}>
                  <div className="flex items-start justify-between gap-2">
                    <span className={`text-[10px] px-2 py-0.5 ${KIND_COLOR[n.kind] || KIND_COLOR.info}`}>{n.kind}</span>
                    {!n.read && (
                      <button onClick={() => markRead(n.id)} className="text-ink/40 hover:text-copper" title="Mark read"><Check className="w-3 h-3" /></button>
                    )}
                  </div>
                  <div className="font-heading font-bold mt-2 text-sm">{n.title}</div>
                  <div className="text-xs text-ink/70 mt-1 leading-relaxed">{n.body}</div>
                  {n.link && (
                    <Link to={n.link} onClick={() => { markRead(n.id); setOpen(false); }} className="text-xs font-bold uppercase text-copper mt-2 inline-block hover:underline">
                      View →
                    </Link>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
