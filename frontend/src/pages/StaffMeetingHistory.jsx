import { useEffect, useState } from "react";
import AppShell from "../components/AppShell";
import { api } from "../lib/api";
import { MessageSquare, ChevronDown, ChevronUp, Clock, Users, AlertTriangle } from "lucide-react";

export default function StaffMeetingHistory() {
  const [meetings, setMeetings] = useState([]);
  const [busy, setBusy] = useState(true);
  const [expanded, setExpanded] = useState(null);

  useEffect(() => {
    (async () => {
      try {
        const r = await api.get("/exec/staff-meetings");
        setMeetings(r.data.meetings || []);
      } catch {
        setMeetings([]);
      } finally {
        setBusy(false);
      }
    })();
  }, []);

  return (
    <AppShell>
      <div className="px-10 py-10 max-w-5xl">
        <div className="flex items-center gap-3 mb-2">
          <MessageSquare className="w-6 h-6 text-copper" />
          <span className="overline text-copper">Executive</span>
        </div>
        <h1 className="font-heading text-4xl font-bold">Staff Meeting History</h1>
        <p className="text-ink/60 mt-2">Past convened meetings and their synthesis.</p>

        {busy && (
          <div className="mt-8 space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-24 bg-ink/5 rounded-xl animate-pulse" />
            ))}
          </div>
        )}

        {!busy && meetings.length === 0 && (
          <div className="mt-12 text-center text-ink/50">
            <MessageSquare className="w-12 h-12 mx-auto mb-4 opacity-30" />
            <p>No staff meetings yet.</p>
            <p className="text-sm mt-1">Convene one from the Executive System.</p>
          </div>
        )}

        {!busy && meetings.length > 0 && (
          <div className="mt-8 space-y-4">
            {meetings.map((m) => {
              const open = expanded === m.meeting_id;
              return (
                <div key={m.meeting_id} className="bg-white rounded-xl border border-ink/10 overflow-hidden">
                  <button
                    onClick={() => setExpanded(open ? null : m.meeting_id)}
                    className="w-full flex items-center justify-between p-5 text-left hover:bg-ink/5 transition-colors"
                  >
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-3">
                        <span className={`px-2 py-0.5 text-xs font-bold rounded ${
                          m.priority === "high" ? "bg-destructive/10 text-destructive" : "bg-ink/10 text-ink/60"
                        }`}>
                          {m.priority || "normal"}
                        </span>
                        <span className="text-sm text-ink/50 flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          {m.convened_at ? new Date(m.convened_at).toLocaleString() : ""}
                        </span>
                        <span className="text-sm text-ink/50 flex items-center gap-1">
                          <Users className="w-3 h-3" />
                          {m.participants?.length || 0}
                        </span>
                      </div>
                      <p className="font-medium text-ink mt-1 truncate">{m.brief}</p>
                    </div>
                    {open ? <ChevronUp className="w-5 h-5 text-ink/30" /> : <ChevronDown className="w-5 h-5 text-ink/30" />}
                  </button>

                  {open && (
                    <div className="px-5 pb-5 border-t border-ink/10 pt-4 space-y-4">
                      {/* Agenda */}
                      {m.agenda?.length > 0 && (
                        <div>
                          <p className="text-xs font-bold text-ink/50 uppercase tracking-wider mb-1">Agenda</p>
                          <ul className="text-sm text-ink/70 space-y-0.5">
                            {m.agenda.map((a, i) => <li key={i}>• {a}</li>)}
                          </ul>
                        </div>
                      )}

                      {/* Participants */}
                      {m.participants?.length > 0 && (
                        <div>
                          <p className="text-xs font-bold text-ink/50 uppercase tracking-wider mb-1">Participants</p>
                          <div className="flex flex-wrap gap-2">
                            {m.participants.map((p) => (
                              <span key={p} className="px-2 py-1 text-xs bg-copper/10 text-copper rounded-lg">{p}</span>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Domain briefs */}
                      {m.domain_briefs && Object.keys(m.domain_briefs).length > 0 && (
                        <div>
                          <p className="text-xs font-bold text-ink/50 uppercase tracking-wider mb-2">Persona Responses</p>
                          <div className="space-y-2">
                            {Object.entries(m.domain_briefs).map(([pid, brief]) => (
                              <div key={pid} className="p-3 bg-ink/5 rounded-lg">
                                <p className="text-sm font-bold text-ink">{pid}</p>
                                {brief.response && (
                                  <p className="text-xs text-ink/70 mt-1">{brief.response.slice(0, 300)}</p>
                                )}
                                {!brief.response && (
                                  <p className="text-xs text-ink/40 italic mt-1">No response recorded</p>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Synthesis */}
                      {m.synthesis && (
                        <div className="bg-ink text-white p-4 rounded-lg">
                          <p className="text-xs font-bold text-copper uppercase tracking-wider mb-2">The 9 Synthesis</p>
                          {m.synthesis.synthesis_brief && (
                            <p className="text-sm text-white/80 whitespace-pre-wrap">{m.synthesis.synthesis_brief}</p>
                          )}
                          {m.synthesis.unified_skill_set?.length > 0 && (
                            <div className="mt-3 flex flex-wrap gap-2">
                              {m.synthesis.unified_skill_set.map((skill) => (
                                <span key={skill} className="px-2 py-0.5 text-xs bg-white/10 text-white/70 rounded">{skill}</span>
                              ))}
                            </div>
                          )}
                        </div>
                      )}

                      {/* PRT status */}
                      {m.prt_cleared === false && (
                        <div className="flex items-center gap-2 text-sm text-destructive">
                          <AlertTriangle className="w-4 h-4" /> PRT did not clear this meeting
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </AppShell>
  );
}
