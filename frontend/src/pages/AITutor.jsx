import { useEffect, useRef, useState, useCallback } from "react";
import AppShell from "../components/AppShell";
import { api, API } from "../lib/api";
import { Sparkles, Send, Compass, ShieldAlert, Lock, Mic, MicOff, Volume2, VolumeX, Loader2, Square, Download } from "lucide-react";
import { toast } from "sonner";

const MODES = [
  { key: "tutor", label: "Master Electrician" },
  { key: "scripture", label: "Scripture Mentor" },
  { key: "explain", label: "Explain Like Apprentice" },
  { key: "quiz_gen", label: "Generate Quiz" },
  { key: "nec_lookup", label: "NEC Lookup" },
  { key: "blueprint", label: "Blueprint Reader" },
  { key: "ancestral_sage", label: "Ancestral Sage", icon: Compass },
];

const SAGE_DEPTH = ["beginner", "intermediate", "advanced"];
const SAGE_INTENSITY = ["gentle", "moderate", "deep"];
const SAGE_CULTURE = [
  "pan_african", "ra_centered", "regional:west_african",
  "regional:east_african", "regional:diasporic",
];
const SAGE_DIVINATION = ["teaching", "reading", "practice", "predictive"];
const SAGE_SAFETY = ["conservative", "standard", "exploratory", "extreme"];
const COMPREHENSION_PHRASE = "I understand and accept the risks of this practice.";

function needsConsent(intensity, safety) {
  return intensity === "deep" || safety === "exploratory" || safety === "extreme";
}

// Browser STT — Web Speech API (Chrome/Edge/Safari).
const SpeechRecognitionImpl = typeof window !== "undefined"
  ? (window.SpeechRecognition || window.webkitSpeechRecognition)
  : null;

export default function AITutor() {
  const [mode, setMode] = useState("tutor");
  const [msgs, setMsgs] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId] = useState(() => `${Date.now()}`);
  const endRef = useRef(null);

  const [depth, setDepth] = useState("beginner");
  const [intensity, setIntensity] = useState("gentle");
  const [culture, setCulture] = useState("pan_african");
  const [divMode, setDivMode] = useState("teaching");
  const [safety, setSafety] = useState("conservative");
  const [consentLogId, setConsentLogId] = useState(null);
  const [consentOpen, setConsentOpen] = useState(false);

  // Audio state
  const [audioOn, setAudioOn] = useState(false); // user opt-in for speaker
  const [audioSpeed, setAudioSpeed] = useState(1.0);
  const [audioVolume, setAudioVolume] = useState(1.0);
  const [audioPlaying, setAudioPlaying] = useState(false);
  const [recording, setRecording] = useState(false);
  const recogRef = useRef(null);
  const audioElRef = useRef(null);
  const audioAbortRef = useRef(null);

  // Restricted Mode (integrity drift)
  const [restricted, setRestricted] = useState(false);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth" }); }, [msgs]);
  useEffect(() => {
    if (mode !== "ancestral_sage") return;
    api.get("/ai/sage/integrity").then((r) => setRestricted(!!r.data.restricted)).catch(() => {});
  }, [mode]);

  useEffect(() => {
    if (!needsConsent(intensity, safety)) setConsentLogId(null);
  }, [intensity, safety]);

  const speak = useCallback(async (text) => {
    if (!audioOn || !text) return;
    // Cancel any in-flight request and stop any current audio
    audioAbortRef.current?.abort();
    if (audioElRef.current) {
      audioElRef.current.pause();
      audioElRef.current = null;
    }
    const controller = new AbortController();
    audioAbortRef.current = controller;
    try {
      const token = localStorage.getItem("lce_token");
      const r = await fetch(`${API}/ai/sage/tts`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
        body: JSON.stringify({ text, voice: "sage", speed: audioSpeed, session_id: sessionId }),
        signal: controller.signal,
      });
      if (r.status === 429) {
        toast.error("Voice budget for today is reached. Text remains visible.");
        return;
      }
      if (r.status === 503) {
        toast.error("Voice provider is temporarily unavailable. Falling back to text only.");
        return;
      }
      if (!r.ok) throw new Error(`TTS ${r.status}`);
      const blob = await r.blob();
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      audio.volume = audioVolume;
      audioElRef.current = audio;
      audio.onended = () => { URL.revokeObjectURL(url); setAudioPlaying(false); };
      audio.onpause = () => setAudioPlaying(false);
      audio.onplay = () => setAudioPlaying(true);
      await audio.play();
    } catch (e) {
      if (e?.name !== "AbortError") {
        toast.error("Couldn't play audio. Text remains visible.");
      }
    }
  }, [audioOn, audioSpeed, audioVolume, sessionId]);

  const cancelAudio = () => {
    audioAbortRef.current?.abort();
    audioElRef.current?.pause();
    audioElRef.current = null;
    setAudioPlaying(false);
  };

  const downloadTranscript = () => {
    const lines = msgs.map((m) => `[${m.role}] ${m.text}`).join("\n\n");
    const blob = new Blob([lines || "(no messages)"], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `sage-transcript-${sessionId}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const send = async () => {
    if (!input.trim() || loading) return;
    if (mode === "ancestral_sage" && needsConsent(intensity, safety) && !consentLogId) {
      setConsentOpen(true);
      return;
    }
    const userMsg = input.trim();
    setInput("");
    setMsgs((m) => [...m, { role: "user", text: userMsg }]);
    setLoading(true);
    try {
      const payload = { session_id: sessionId, message: userMsg, mode };
      if (mode === "ancestral_sage") {
        payload.depth = depth;
        payload.intensity = intensity;
        payload.cultural_focus = culture;
        payload.divination_mode = divMode;
        payload.safety_level = safety;
        if (consentLogId) payload.consent_log_id = consentLogId;
      }
      const r = await api.post("/ai/chat", payload);
      const reply = r.data.reply;
      setMsgs((m) => [...m, { role: "assistant", text: reply }]);
      if (mode === "ancestral_sage" && audioOn) speak(reply);
    } catch (e) {
      const detail = e?.response?.data?.detail;
      if (e?.response?.status === 403 && typeof detail === "string" && detail.toLowerCase().includes("consent")) {
        toast.error("Consent required for this practice.");
        setConsentLogId(null);
        setConsentOpen(true);
      } else if (e?.response?.status === 403 && typeof detail === "string" && detail.toLowerCase().includes("cap")) {
        toast.error(detail);
      } else {
        toast.error("AI unavailable. Check configuration or try again.");
        setMsgs((m) => [...m, { role: "assistant", text: "Sorry — I couldn't reach the tutor service. Try again in a moment." }]);
      }
    } finally { setLoading(false); }
  };

  // STT — toggle dictation. Permission is requested by the browser.
  const toggleMic = () => {
    if (!SpeechRecognitionImpl) {
      toast.error("Voice input is not supported in this browser. Use Chrome, Edge, or Safari.");
      return;
    }
    if (recording) {
      recogRef.current?.stop();
      setRecording(false);
      return;
    }
    const rec = new SpeechRecognitionImpl();
    rec.lang = "en-US";
    rec.interimResults = false;
    rec.continuous = false;
    rec.onresult = (ev) => {
      const txt = ev.results?.[0]?.[0]?.transcript?.trim();
      if (txt) setInput((cur) => (cur ? `${cur} ${txt}` : txt));
    };
    rec.onerror = (ev) => {
      toast.error(`Mic error: ${ev.error || "unknown"}`);
      setRecording(false);
    };
    rec.onend = () => setRecording(false);
    recogRef.current = rec;
    try {
      rec.start();
      setRecording(true);
      toast.info("Listening… speak now.");
    } catch {
      toast.error("Couldn't start microphone.");
    }
  };

  const sageActive = mode === "ancestral_sage";
  const consentRequired = sageActive && needsConsent(intensity, safety);
  const consentBlocking = consentRequired && !consentLogId;

  return (
    <AppShell>
      <div className="px-10 py-10 max-w-4xl">
        <div className="overline text-copper">Powered by Claude Sonnet 4.5</div>
        <h1 className="font-heading text-4xl font-bold mt-2 flex items-center gap-3"><Sparkles className="w-8 h-8 text-copper" /> AI Tutor</h1>
        <p className="text-ink/60 mt-2">Ask questions. Request explanations. Request scripture. Generate a practice quiz.</p>

        <div className="flex gap-2 mt-6 flex-wrap" data-testid="mode-switcher">
          {MODES.map((m) => {
            const Icon = m.icon;
            const active = mode === m.key;
            return (
              <button
                key={m.key}
                onClick={() => setMode(m.key)}
                aria-label={m.key === "ancestral_sage" ? "Open Ancestral Sage persona menu" : `Switch to ${m.label} mode`}
                title={m.key === "ancestral_sage" ? "Ancestral Sage — Guidance & Readings" : m.label}
                className={`px-4 py-2 text-xs font-bold uppercase tracking-widest border transition-colors inline-flex items-center gap-2 ${active ? "bg-ink text-white border-ink" : "bg-white text-ink border-ink/20 hover:border-ink"}`}
                data-testid={`mode-${m.key}`}
              >
                {Icon && <Icon className="w-4 h-4 text-copper" />}
                {m.label}
              </button>
            );
          })}
        </div>

        {sageActive && restricted && (
          <div className="card-flat mt-6 p-4 bg-red-50 border-l-4 border-l-red-700 flex items-start gap-3" data-testid="sage-restricted-banner">
            <ShieldAlert className="w-5 h-5 text-red-700 shrink-0 mt-0.5" />
            <div className="text-sm">
              <div className="font-bold text-red-900">Restricted Educational Mode</div>
              <p className="text-red-900/80 mt-1">
                The Ancestral Sage prompt failed an integrity check. Detailed scenarios,
                signal cards, and personalization are unavailable until administrators
                restore the canonical persona. High-level teaching still works.
              </p>
            </div>
          </div>
        )}

        {sageActive && (
          <SageParamPanel
            depth={depth} setDepth={setDepth}
            intensity={intensity} setIntensity={setIntensity}
            culture={culture} setCulture={setCulture}
            divMode={divMode} setDivMode={setDivMode}
            safety={safety} setSafety={setSafety}
            consentLogId={consentLogId}
            consentRequired={consentRequired}
            audioOn={audioOn} setAudioOn={setAudioOn}
            audioSpeed={audioSpeed} setAudioSpeed={setAudioSpeed}
            audioVolume={audioVolume} setAudioVolume={setAudioVolume}
            audioPlaying={audioPlaying} onCancelAudio={cancelAudio}
            onDownloadTranscript={downloadTranscript}
            onClearConsent={() => setConsentLogId(null)}
            onOpenConsent={() => setConsentOpen(true)}
          />
        )}

        <div className="card-flat mt-6 h-[500px] flex flex-col" data-testid="chat-window">
          <div className="flex-1 overflow-y-auto p-6 space-y-4">
            {msgs.length === 0 && (
              <div className="text-center text-ink/40 py-16">
                {sageActive ? (
                  <>
                    <Compass className="w-10 h-10 mx-auto text-copper/70" />
                    <div className="mt-3 text-sm">
                      Ancestral Sage is here in <strong className="text-ink/70">{intensity} / {safety}</strong> mode.
                      Type "stop" or "pause" any time to halt a practice.
                    </div>
                  </>
                ) : (
                  <>
                    <Sparkles className="w-10 h-10 mx-auto text-copper/50" />
                    <div className="mt-3 text-sm">Start by asking: <em>&quot;Explain why neutrals and grounds are only bonded at the service.&quot;</em></div>
                  </>
                )}
              </div>
            )}
            {msgs.map((m, i) => (
              <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"} group`}>
                <div className={`max-w-[80%] p-4 text-sm leading-relaxed whitespace-pre-wrap relative ${m.role === "user" ? "bg-ink text-white" : "bg-bone border border-ink/10"}`} data-testid={`msg-${i}`}>
                  {m.text}
                  {m.role === "assistant" && sageActive && (
                    <button
                      onClick={() => speak(m.text)}
                      className="absolute -bottom-3 right-3 bg-white border border-ink/20 p-1.5 hover:border-ink opacity-0 group-hover:opacity-100 transition-opacity"
                      aria-label="Replay this response as audio"
                      title="Replay as audio"
                      data-testid={`replay-${i}`}
                    >
                      <Volume2 className="w-3.5 h-3.5 text-copper" />
                    </button>
                  )}
                </div>
              </div>
            ))}
            {loading && (
              <div className="text-sm text-ink/50 italic flex items-center gap-2">
                <Loader2 className="w-3.5 h-3.5 animate-spin" /> Tutor is thinking…
              </div>
            )}
            <div ref={endRef} />
          </div>
          <div className="border-t border-ink/10 p-4 flex gap-2 items-center">
            {sageActive && (
              <button
                onClick={toggleMic}
                className={`p-3 border transition-colors ${recording ? "bg-red-700 text-white border-red-700" : "bg-white border-ink/20 hover:border-ink"}`}
                aria-label={recording ? "Stop dictation" : "Dictate message"}
                title={recording ? "Stop dictation" : "Dictate message (Web Speech API)"}
                data-testid="btn-mic"
              >
                {recording ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
              </button>
            )}
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && send()}
              placeholder={consentBlocking ? "Consent required before sending…" : "Ask the tutor…"}
              className="flex-1 px-4 py-3 bg-white border border-ink/20 focus:outline-none focus:border-ink focus:ring-2 focus:ring-signal"
              data-testid="chat-input"
            />
            <button
              onClick={send}
              disabled={loading}
              className="btn-primary inline-flex items-center gap-2"
              data-testid="btn-send"
            >
              {consentBlocking ? <Lock className="w-4 h-4" /> : <Send className="w-4 h-4" />}
              {consentBlocking ? "Consent" : "Send"}
            </button>
          </div>
        </div>
      </div>

      {consentOpen && (
        <ConsentModal
          intensity={intensity}
          safety={safety}
          onClose={() => setConsentOpen(false)}
          onGranted={(id) => {
            setConsentLogId(id);
            setConsentOpen(false);
            toast.success("Consent recorded. You may continue.");
          }}
        />
      )}
    </AppShell>
  );
}

// ---------------------------------------------------------------------------
// Sage parameter panel
// ---------------------------------------------------------------------------
function SageParamPanel({
  depth, setDepth, intensity, setIntensity, culture, setCulture,
  divMode, setDivMode, safety, setSafety,
  consentLogId, consentRequired, audioOn, setAudioOn,
  audioSpeed, setAudioSpeed, audioVolume, setAudioVolume,
  audioPlaying, onCancelAudio, onDownloadTranscript,
  onClearConsent, onOpenConsent,
}) {
  const fields = [
    { label: "Depth", value: depth, set: setDepth, opts: SAGE_DEPTH, testid: "sage-depth" },
    { label: "Intensity", value: intensity, set: setIntensity, opts: SAGE_INTENSITY, testid: "sage-intensity" },
    { label: "Cultural focus", value: culture, set: setCulture, opts: SAGE_CULTURE, testid: "sage-culture" },
    { label: "Divination mode", value: divMode, set: setDivMode, opts: SAGE_DIVINATION, testid: "sage-divination" },
    { label: "Safety level", value: safety, set: setSafety, opts: SAGE_SAFETY, testid: "sage-safety" },
  ];
  return (
    <div className="card-flat mt-6 p-5 bg-white border-l-4 border-l-copper" data-testid="sage-param-panel">
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div>
          <div className="overline text-copper">Ancestral Sage — Session Parameters</div>
          <p className="text-sm text-ink/60 mt-1">
            Tune the practice. Higher intensity or safety levels require explicit consent.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setAudioOn(!audioOn)}
            className={`text-xs font-bold uppercase tracking-widest px-3 py-2 inline-flex items-center gap-1.5 border ${audioOn ? "bg-copper text-white border-copper" : "bg-white text-ink border-ink/20 hover:border-ink"}`}
            aria-pressed={audioOn}
            aria-label="Toggle voice output"
            data-testid="sage-audio-toggle"
          >
            {audioOn ? <Volume2 className="w-3.5 h-3.5" /> : <VolumeX className="w-3.5 h-3.5" />}
            {audioOn ? "Voice on" : "Voice off"}
          </button>
          {consentRequired && (
            consentLogId ? (
              <button
                onClick={onClearConsent}
                className="text-xs font-semibold uppercase tracking-widest text-signal hover:underline inline-flex items-center gap-1"
                data-testid="sage-revoke-consent"
              >
                <ShieldAlert className="w-3.5 h-3.5" /> Consent active — revoke
              </button>
            ) : (
              <button
                onClick={onOpenConsent}
                className="text-xs font-bold uppercase tracking-widest text-white bg-ink px-3 py-2 inline-flex items-center gap-1"
                data-testid="sage-grant-consent"
              >
                <Lock className="w-3.5 h-3.5" /> Grant consent to continue
              </button>
            )
          )}
        </div>
      </div>

      <div className="grid sm:grid-cols-2 lg:grid-cols-5 gap-3 mt-4">
        {fields.map((f) => (
          <label key={f.label} className="block text-xs">
            <span className="overline text-ink/60">{f.label}</span>
            <select
              value={f.value}
              onChange={(e) => f.set(e.target.value)}
              className="mt-1 w-full px-3 py-2 bg-white border border-ink/20 text-sm focus:border-ink focus:outline-none"
              data-testid={f.testid}
            >
              {f.opts.map((o) => (
                <option key={o} value={o}>{o.replace("regional:", "regional · ")}</option>
              ))}
            </select>
          </label>
        ))}
      </div>

      {audioOn && (
        <div className="mt-4 pt-4 border-t border-ink/10 flex items-end gap-4 flex-wrap" data-testid="sage-audio-controls">
          <label className="block text-xs flex-1 min-w-[140px]">
            <span className="overline text-ink/60">
              Voice speed <span className="text-ink/40">({audioSpeed.toFixed(1)}x)</span>
            </span>
            <input
              type="range" min="0.5" max="2.0" step="0.1"
              value={audioSpeed}
              onChange={(e) => setAudioSpeed(parseFloat(e.target.value))}
              className="mt-2 w-full accent-copper"
              aria-label="Voice playback speed"
              data-testid="sage-speed-slider"
            />
          </label>
          <label className="block text-xs flex-1 min-w-[140px]">
            <span className="overline text-ink/60">
              Volume <span className="text-ink/40">({Math.round(audioVolume * 100)}%)</span>
            </span>
            <input
              type="range" min="0" max="1" step="0.05"
              value={audioVolume}
              onChange={(e) => setAudioVolume(parseFloat(e.target.value))}
              className="mt-2 w-full accent-copper"
              aria-label="Voice playback volume"
              data-testid="sage-volume-slider"
            />
          </label>
          {audioPlaying && (
            <button
              onClick={onCancelAudio}
              className="text-xs font-bold uppercase tracking-widest border border-red-700 text-red-700 px-3 py-2 hover:bg-red-50 inline-flex items-center gap-1.5"
              aria-label="Stop audio playback"
              data-testid="sage-cancel-audio"
            >
              <Square className="w-3.5 h-3.5 fill-red-700" /> Stop audio
            </button>
          )}
          <button
            onClick={onDownloadTranscript}
            className="text-xs font-bold uppercase tracking-widest border border-ink/20 px-3 py-2 hover:border-ink inline-flex items-center gap-1.5"
            aria-label="Download conversation transcript as a text file"
            data-testid="sage-download-transcript"
          >
            <Download className="w-3.5 h-3.5" /> Transcript
          </button>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Layered consent modal — 3 disclaimers + verbatim YES + comprehension.
// ---------------------------------------------------------------------------
function ConsentModal({ intensity, safety, onClose, onGranted }) {
  const [confirmYes, setConfirmYes] = useState("");
  const [comprehension, setComprehension] = useState("");
  const [d1, setD1] = useState(false);
  const [d2, setD2] = useState(false);
  const [d3, setD3] = useState(false);
  const [contentType, setContentType] = useState("personalization");
  const [requestReview, setRequestReview] = useState(false);
  const [busy, setBusy] = useState(false);

  const submit = async () => {
    if (busy) return;
    setBusy(true);
    try {
      const r = await api.post("/ai/consent", {
        persona: "ancestral_sage",
        confirm_yes: confirmYes,
        comprehension,
        intensity,
        safety_level: safety,
        content_type: contentType,
        disclaimer1_ack: d1,
        disclaimer2_ack: d2,
        disclaimer3_ack: d3,
        request_human_review: requestReview,
      });
      onGranted(r.data.consent_log_id);
    } catch (e) {
      const detail = e?.response?.data?.detail;
      toast.error(typeof detail === "string" ? detail : "Consent could not be recorded.");
    } finally {
      setBusy(false);
    }
  };

  const yesOk = confirmYes.trim().toUpperCase() === "YES";
  const compOk = comprehension.trim() === COMPREHENSION_PHRASE;
  const disclaimersOk = contentType === "general" || (d1 && d2 && d3);
  const canSubmit = yesOk && compOk && disclaimersOk;

  return (
    <div
      className="fixed inset-0 bg-ink/70 flex items-center justify-center z-50 p-4 overflow-y-auto"
      data-testid="sage-consent-modal"
      role="dialog"
      aria-modal="true"
    >
      <div className="bg-bone max-w-2xl w-full p-8 border-l-4 border-l-copper my-10">
        <div className="overline text-copper">Consent Required</div>
        <h3 className="font-heading text-2xl font-bold mt-2 flex items-center gap-2">
          <ShieldAlert className="w-6 h-6 text-copper" /> Layered consent
        </h3>

        <div className="mt-5 space-y-3">
          <DisclaimerCard
            n={1} checked={d1} onCheck={setD1} testid="disclaimer-1"
            title="Educational & Entertainment Only"
            body="The content below is educational and entertainment-only. It is not financial, legal, or medical advice. I will make my own decisions and seek licensed professionals when needed."
          />
          <DisclaimerCard
            n={2} checked={d2} onCheck={setD2} testid="disclaimer-2"
            title="Markets are uncertain"
            body="Markets and life patterns are uncertain. Past patterns do not guarantee future results. I am responsible for my own choices and outcomes."
          />
          <DisclaimerCard
            n={3} checked={d3} onCheck={setD3} testid="disclaimer-3"
            title="No personalized recommendations"
            body="Ancestral Sage will not give me personalized recommendations. Any 'If I had money to spend' scenarios are hypothetical educational examples — not advice."
          />
        </div>

        <div className="mt-5 grid sm:grid-cols-2 gap-3">
          <label className="text-xs">
            <span className="overline text-ink/60">Content type</span>
            <select
              value={contentType}
              onChange={(e) => setContentType(e.target.value)}
              className="mt-1 w-full px-3 py-2 bg-white border border-ink/20 text-sm focus:border-ink focus:outline-none"
              data-testid="consent-content-type"
            >
              <option value="general">General teaching</option>
              <option value="personalization">Personalization</option>
              <option value="high_confidence">High confidence</option>
              <option value="high_consensus">High consensus</option>
            </select>
          </label>
          <label className="text-xs flex items-end gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={requestReview}
              onChange={(e) => setRequestReview(e.target.checked)}
              className="w-4 h-4 mb-2"
              data-testid="consent-request-review"
            />
            <span className="text-ink/70 leading-snug pb-1">
              I'd like a human reviewer to follow up with me about this session.
            </span>
          </label>
        </div>

        <div className="mt-6 border-t border-ink/10 pt-5">
          <p className="text-sm text-ink/70">
            This practice involves deep visualization/regression and may be emotionally
            intense. Do you consent to proceed? Type <strong>YES</strong> to continue.
          </p>
          <input
            value={confirmYes}
            onChange={(e) => setConfirmYes(e.target.value)}
            placeholder="Type YES"
            className="mt-2 w-full px-3 py-2 bg-white border border-ink/20 text-sm focus:border-ink focus:outline-none font-mono uppercase"
            data-testid="sage-consent-yes"
            autoFocus
          />

          <p className="text-sm text-ink/70 mt-4">
            Please type the following exactly:
            <br />
            <span className="font-mono text-ink">{COMPREHENSION_PHRASE}</span>
          </p>
          <input
            value={comprehension}
            onChange={(e) => setComprehension(e.target.value)}
            placeholder={COMPREHENSION_PHRASE}
            className="mt-2 w-full px-3 py-2 bg-white border border-ink/20 text-sm focus:border-ink focus:outline-none"
            data-testid="sage-consent-comprehension"
          />
        </div>

        <div className="text-xs text-ink/50 mt-4">
          You can type <strong>pause</strong> or <strong>stop</strong> in chat at any time
          to halt a practice and receive grounding/aftercare. Consent expires after 2 hours.
        </div>

        <div className="flex gap-3 mt-6 justify-end">
          <button
            onClick={onClose}
            className="btn-secondary"
            data-testid="sage-consent-cancel"
            disabled={busy}
          >
            Cancel
          </button>
          <button
            onClick={submit}
            disabled={busy || !canSubmit}
            className="btn-primary inline-flex items-center gap-2"
            data-testid="sage-consent-submit"
          >
            {busy ? "Recording…" : "Grant consent"}
          </button>
        </div>
      </div>
    </div>
  );
}

function DisclaimerCard({ n, checked, onCheck, title, body, testid }) {
  return (
    <label className={`block card-flat p-3 bg-white cursor-pointer border-l-4 ${checked ? "border-l-copper" : "border-l-ink/20"}`}>
      <div className="flex items-start gap-3">
        <input
          type="checkbox"
          checked={checked}
          onChange={(e) => onCheck(e.target.checked)}
          className="w-4 h-4 mt-1"
          data-testid={testid}
        />
        <div className="flex-1">
          <div className="text-xs font-bold uppercase tracking-widest text-copper">Disclaimer {n}</div>
          <div className="font-heading text-sm font-bold mt-0.5">{title}</div>
          <p className="text-xs text-ink/70 mt-1 leading-snug">{body}</p>
        </div>
      </div>
    </label>
  );
}
