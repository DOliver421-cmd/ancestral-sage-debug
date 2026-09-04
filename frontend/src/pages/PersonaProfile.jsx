import { useState, useEffect, useRef, useCallback } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import { useMic } from "../hooks/useMic";
import { useBrowserTTS } from "../hooks/useBrowserTTS";
import { toast } from "sonner";
import {
  Loader2, ArrowLeft, XCircle, Send, Mic, MicOff, Volume2, VolumeX, SlidersHorizontal,
} from "lucide-react";

const LEVEL_COLORS = {
  executive: "bg-amber-100 text-amber-800",
  director:  "bg-blue-100 text-blue-800",
  assistant: "bg-green-100 text-green-800",
  production: "bg-purple-100 text-purple-800",
  governance: "bg-ink/10 text-ink/70",
};

const LEVEL_LABELS = {
  executive: "Executive",
  director: "Director",
  assistant: "Assistant",
  production: "Production",
  governance: "Governance",
};

const humanize = (k) =>
  (k || "").split("_").map((w) => w.charAt(0).toUpperCase() + w.slice(1)).join(" ");

export default function PersonaProfile() {
  const { slug } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [persona, setPersona] = useState(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);

  // ── Chat ────────────────────────────────────────────────────────────────
  const [msgs, setMsgs] = useState([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const listRef = useRef(null);
  const { enabled: voiceOn, toggle: toggleVoice, speak, supported: ttsSupported } =
    useBrowserTTS({ storageKey: "persona_voice", defaultOn: true });
  const { listening, toggle: toggleMic } = useMic({
    onResult: (text) => { setInput(text); sendRef.current(text); },
    onError: (msg) => toast.error(msg),
    continuous: false,
  });

  // ── Tuning sliders (per-user, per-persona) ─────────────────────────────
  const [tune, setTune] = useState(null);
  const [tuneVal, setTuneVal] = useState(null);
  const [savingTune, setSavingTune] = useState(false);

  const send = useCallback(async (text) => {
    const t = (text || "").trim();
    if (!t || sending) return;
    setMsgs((m) => [...m, { role: "user", text: t }]);
    setInput("");
    setSending(true);
    try {
      const { data } = await api.post(`/ai/personas/${slug}/chat`, {
        message: t,
        session_id: "profile",
      });
      setMsgs((m) => [...m, { role: "assistant", text: data.reply, status: data.status }]);
      if (voiceOn && ttsSupported) speak(data.reply);
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Couldn't reach them right now.");
    } finally {
      setSending(false);
    }
  }, [slug, sending, voiceOn, ttsSupported, speak]);

  const sendRef = useRef(send);
  useEffect(() => { sendRef.current = send; }, [send]);

  // Auto-scroll to the newest message
  useEffect(() => {
    if (listRef.current) listRef.current.scrollTop = listRef.current.scrollHeight;
  }, [msgs]);

  useEffect(() => {
    api.get(`/ai/personas/${slug}`)
      .then((r) => setPersona(r.data))
      .catch((err) => {
        if (err?.response?.status === 404) setNotFound(true);
      })
      .finally(() => setLoading(false));
    if (user) {
      api.get(`/ai/personas/${slug}/controls`)
        .then((r) => { setTune(r.data); setTuneVal({ ...r.data.controls }); })
        .catch(() => {});
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [slug, user]);

  if (loading) {
    return (
      <div className="min-h-screen bg-bone flex items-center justify-center">
        <Loader2 className="w-6 h-6 animate-spin text-copper" />
      </div>
    );
  }

  if (notFound || !persona) {
    return (
      <div className="min-h-screen bg-bone flex flex-col items-center justify-center gap-4">
        <p className="text-ink/60">Persona not found.</p>
        <Link to="/personas" className="text-copper hover:underline text-sm">← Back to the team</Link>
      </div>
    );
  }

  const declines = persona.record?.declines || [];
  const decisionTree = persona.decision_tree || null;

  const saveTune = async () => {
    setSavingTune(true);
    try {
      const { data } = await api.post(`/ai/personas/${slug}/controls`, { controls: tuneVal });
      setTune((t) => ({ ...t, controls: { ...data.controls } }));
      setTuneVal({ ...data.controls });
      toast.success(`Tuning saved — your next message to ${persona.name} speaks it.`);
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Couldn't save tuning");
    } finally {
      setSavingTune(false);
    }
  };

  const tuneDirty = tune && tuneVal && tune.order.some((k) => tune.controls[k] !== tuneVal[k]);

  return (
    <div className="min-h-screen bg-bone">
      {/* Back */}
      <div className="px-6 pt-6 md:px-16 max-w-3xl mx-auto">
        <Link to="/personas" className="inline-flex items-center gap-2 text-sm text-ink/40 hover:text-ink/70 transition-colors">
          <ArrowLeft className="w-4 h-4" /> All personas
        </Link>
      </div>

      {/* Identity */}
      <div className="px-6 py-8 md:px-16 max-w-3xl mx-auto">
        <div className="flex items-start gap-4 flex-wrap">
          <div className="flex-1">
            <div className="flex items-center gap-3 flex-wrap">
              <span className={`text-xs font-bold px-2 py-0.5 rounded-full uppercase tracking-wide ${LEVEL_COLORS[persona.level] || "bg-ink/10 text-ink/60"}`}>
                {LEVEL_LABELS[persona.level] || persona.level}
              </span>
              <span className="text-xs text-ink/40">{persona.department}</span>
            </div>
            <h1 className="font-heading text-3xl font-bold mt-2">{persona.name}</h1>
            <p className="text-sm text-ink/50 mt-1">{persona.domain}</p>
          </div>
        </div>

        {/* Statement */}
        <div className="mt-8 bg-white border border-ink/10 rounded-2xl p-6">
          <div className="overline text-copper text-xs tracking-widest mb-3">In their own words</div>
          <p className="text-ink/80 leading-relaxed">{persona.statement}</p>
        </div>

        {/* ── Speak with this persona ─────────────────────────────────── */}
        <div className="mt-6 bg-white border border-ink/10 rounded-2xl overflow-hidden">
          <div className="px-6 pt-5 pb-4 border-b border-ink/5 flex items-center justify-between gap-3 flex-wrap">
            <div>
              <div className="overline text-copper text-xs tracking-widest">Live — speak or type</div>
              <div className="font-heading text-lg font-bold mt-0.5">Talk with {persona.name}</div>
            </div>
            {user && (
              <div className="flex items-center gap-2">
                {ttsSupported && (
                  <button
                    onClick={toggleVoice}
                    title={voiceOn ? "Voice readout on" : "Voice readout off"}
                    className={`flex items-center gap-1.5 text-xs font-bold px-3 py-1.5 rounded-lg border transition-colors cursor-pointer ${
                      voiceOn ? "bg-emerald-50 text-emerald-700 border-emerald-300" : "bg-ink/5 text-ink/50 border-ink/15"
                    }`}
                  >
                    {voiceOn ? <Volume2 className="w-3.5 h-3.5" /> : <VolumeX className="w-3.5 h-3.5" />}
                    {voiceOn ? "Voice on" : "Voice off"}
                  </button>
                )}
                <button
                  onClick={toggleMic}
                  title={listening ? "Stop listening" : "Speak — your words are sent"}
                  className={`flex items-center gap-1.5 text-xs font-bold px-3 py-1.5 rounded-lg border transition-colors cursor-pointer ${
                    listening ? "bg-red-50 text-red-600 border-red-300 animate-pulse" : "bg-ink text-white border-ink"
                  }`}
                >
                  {listening ? <MicOff className="w-3.5 h-3.5" /> : <Mic className="w-3.5 h-3.5" />}
                  {listening ? "Listening…" : "Mic"}
                </button>
              </div>
            )}
          </div>

          {!user ? (
            <div className="px-6 py-10 text-center">
              <div className="text-4xl mb-3">🗣️</div>
              <p className="text-sm text-ink/60 mb-4 max-w-sm mx-auto">
                Sign in to speak with {persona.name} — voice input and read-aloud included.
              </p>
              <button
                onClick={() => navigate(`/login?returnTo=${encodeURIComponent(`/personas/${slug}`)}`)}
                className="bg-ink text-white font-bold text-sm px-6 py-2.5 rounded-xl hover:bg-ink/80 transition-colors cursor-pointer"
              >
                Sign in to talk
              </button>
            </div>
          ) : (
            <>
              {/* Messages */}
              <div
                ref={listRef}
                className="px-6 py-5 space-y-4 max-h-96 overflow-y-auto"
              >
                {msgs.length === 0 && (
                  <div className="text-center py-8">
                    <p className="text-sm text-ink/40 max-w-md mx-auto leading-relaxed">
                      Start the conversation. Say something out loud or type it — they answer in
                      their own voice, tuned by your sliders below.
                    </p>
                  </div>
                )}
                {msgs.map((m, i) => (
                  <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
                    <div
                      className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                        m.role === "user"
                          ? "bg-ink text-white rounded-br-sm"
                          : "bg-bone border border-ink/10 text-ink rounded-bl-sm"
                      }`}
                    >
                      {m.status === "fallback" || m.status === "failure" || m.status === "kb" ? (
                        <div className="mt-1 mb-2 flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-widest text-amber-700">
                          <svg className="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
                            <line x1="12" y1="9" x2="12" y2="13" />
                            <line x1="12" y1="17" x2="12.01" y2="17" />
                          </svg>
                          {m.status === "kb"
                            ? "Limited answer — knowledge-base fallback"
                            : "Temporary outage — persona not connected to AI right now"}
                        </div>
                      ) : null}
                      {m.text}
                      {m.role === "assistant" && ttsSupported && voiceOn && (
                        <button
                          onClick={() => speak(m.text)}
                          title="Read aloud"
                          className="mt-2 flex items-center gap-1 text-[10px] font-bold uppercase tracking-widest text-copper hover:text-copper/70 cursor-pointer"
                        >
                          <Volume2 className="w-3 h-3" /> replay
                        </button>
                      )}
                    </div>
                  </div>
                ))}
                {sending && (
                  <div className="flex justify-start">
                    <div className="bg-bone border border-ink/10 rounded-2xl rounded-bl-sm px-4 py-3 text-sm text-ink/40 italic">
                      thinking…
                    </div>
                  </div>
                )}
              </div>

              {/* Input */}
              <div className="px-6 py-4 border-t border-ink/5 flex items-end gap-3">
                <textarea
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      send(input);
                    }
                  }}
                  rows={1}
                  placeholder="Ask them anything…"
                  className="flex-1 px-4 py-3 bg-bone border border-ink/15 rounded-xl text-sm focus:outline-none focus:border-copper resize-none"
                />
                <button
                  onClick={() => send(input)}
                  disabled={sending || !input.trim()}
                  className="bg-copper text-white font-bold px-4 py-3 rounded-xl transition-opacity disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
                  title="Send"
                >
                  <Send className="w-4 h-4" />
                </button>
              </div>
            </>
          )}
        </div>

        {/* ── Tuning sliders — this persona, your way ─────────────────── */}
        {user && tune && (
          <div className="mt-6 bg-white border border-ink/10 rounded-2xl p-6">
            <div className="flex items-center gap-2 overline text-copper text-xs tracking-widest">
              <SlidersHorizontal className="w-3.5 h-3.5" /> Tune this persona
            </div>
            <p className="text-sm text-ink/50 mt-1.5 leading-relaxed">
              Move the sliders and save — {persona.name} will speak with this configuration on
              your next message. Your tuning is yours alone; the Source's master controls stay global.
            </p>
            <div className="mt-5 space-y-4">
              {tune.order.map((key) => {
                const label = tune.labels?.[key] || humanize(key);
                const hint = tune.hints?.[key] || "";
                const val = tuneVal[key] ?? tune.defaults[key];
                return (
                  <div key={key}>
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-bold text-ink/80">{label}</span>
                      <span className="font-black text-sm text-copper">{val}</span>
                    </div>
                    <input
                      type="range"
                      min="0" max="100" step="1"
                      value={val}
                      onChange={(e) => setTuneVal((v) => ({ ...v, [key]: Number(e.target.value) }))}
                      className="w-full mt-1.5 accent-copper cursor-pointer"
                    />
                    <div className="text-[10px] text-ink/40 mt-0.5">{hint}</div>
                  </div>
                );
              })}
            </div>
            <button
              onClick={saveTune}
              disabled={savingTune || !tuneDirty}
              className="mt-5 text-xs font-black uppercase tracking-widest px-5 py-2.5 rounded-xl text-white bg-copper transition-opacity disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
            >
              {savingTune ? "Saving…" : tuneDirty ? "Apply to my conversations" : "Tuning live for you"}
            </button>
          </div>
        )}

        {/* Will not do */}
        <div className="mt-6 bg-white border border-ink/10 rounded-2xl p-6">
          <div className="overline text-copper text-xs tracking-widest mb-4">What they will not do</div>
          <ul className="space-y-3">
            {persona.will_not.map((item, i) => (
              <li key={i} className="flex items-start gap-3 text-sm text-ink/70">
                <XCircle className="w-4 h-4 text-ink/25 flex-shrink-0 mt-0.5" />
                {item}
              </li>
            ))}
          </ul>
        </div>

        {/* Decision tree — only for Supervisor */}
        {decisionTree && (
          <div className="mt-6 bg-white border border-ink/10 rounded-2xl p-6">
            <div className="overline text-copper text-xs tracking-widest mb-2">How decisions are made</div>
            <p className="text-sm text-ink/60 mb-5">{decisionTree.description}</p>
            {[
              { key: "legal_branch", label: "Legal & financial actions" },
              { key: "non_legal_branch", label: "Operational actions" },
            ].map(({ key, label }) => {
              const branch = decisionTree[key];
              if (!branch) return null;
              return (
                <div key={key} className="mb-5">
                  <div className="text-sm font-bold text-ink mb-1">{label}</div>
                  <div className="text-xs text-ink/40 mb-3 italic">Applies when: {branch.triggers_when}</div>
                  <div className="space-y-2">
                    {branch.checks.map((c, i) => (
                      <div key={i} className="flex items-start gap-3 text-xs">
                        <div className="w-1 h-1 rounded-full bg-copper/50 mt-1.5 flex-shrink-0" />
                        <div>
                          <span className="font-mono text-ink/60">{c.condition}</span>
                          {" → "}
                          <span className={
                            (c.if_false || c.if_true || c.if_false_or_unknown || c.if_true_or_unknown || "").includes("BLOCK")
                              ? "text-red-600 font-bold"
                              : (c.if_false || c.if_true || c.if_false_or_unknown || c.if_true_or_unknown || "").includes("ESCALATE")
                              ? "text-amber-600 font-bold"
                              : "text-green-600 font-bold"
                          }>
                            {c.if_false || c.if_true || c.if_false_or_unknown || c.if_true_or_unknown || c.result}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
            <p className="text-xs text-ink/30 mt-4 border-t border-ink/5 pt-4">{decisionTree.note}</p>
          </div>
        )}

        {/* Public record */}
        <div className="mt-6 bg-white border border-ink/10 rounded-2xl p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="overline text-copper text-xs tracking-widest">Public record of declines</div>
            {declines.length > 0 && (
              <span className="text-xs text-ink/40">{declines.length} recorded</span>
            )}
          </div>

          {declines.length === 0 ? (
            <p className="text-sm text-ink/40 italic">
              No recorded declines yet. When this persona declines a request, the reason
              and date are logged here permanently.
            </p>
          ) : (
            <div className="space-y-4">
              {declines.map((d, i) => (
                <div key={d.id || i} className="border-l-2 border-ink/10 pl-4 py-1">
                  <p className="text-xs text-ink/35 mb-1">
                    {new Date(d.at).toLocaleDateString("en-US", {
                      year: "numeric", month: "long", day: "numeric",
                    })}
                  </p>
                  <p className="text-sm text-ink/50 italic mb-1">
                    Request: "{d.request_summary}"
                  </p>
                  <p className="text-sm text-ink/80">
                    {d.decline_reason}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="mt-10 pb-12">
          <p className="text-xs text-ink/25 leading-relaxed">
            This profile is public and permanent. The statements above were written as standing
            declarations of this persona's character and limits. The record of declines is an
            uneditable log — added to automatically when a decline occurs in the operational
            system, and visible to anyone who visits this page.
          </p>
        </div>
      </div>
    </div>
  );
}
