import { useEffect, useRef, useState } from "react";
import AppShell from "../components/AppShell";
import { api } from "../lib/api";
import { Sparkles, Send, Compass, ShieldAlert, Lock } from "lucide-react";
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

// Sage parameter options. Wider lists could be added later.
const SAGE_DEPTH = ["beginner", "intermediate", "advanced"];
const SAGE_INTENSITY = ["gentle", "moderate", "deep"];
const SAGE_CULTURE = [
  "pan_african",
  "ra_centered",
  "regional:west_african",
  "regional:east_african",
  "regional:diasporic",
];
const SAGE_DIVINATION = ["teaching", "reading", "practice", "predictive"];
const SAGE_SAFETY = ["conservative", "standard", "exploratory", "extreme"];

const COMPREHENSION_PHRASE = "I understand and accept the risks of this practice.";

function needsConsent(intensity, safety) {
  return intensity === "deep" || safety === "exploratory" || safety === "extreme";
}

export default function AITutor() {
  const [mode, setMode] = useState("tutor");
  const [msgs, setMsgs] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId] = useState(() => `${Date.now()}`);
  const endRef = useRef(null);

  // Sage state
  const [depth, setDepth] = useState("beginner");
  const [intensity, setIntensity] = useState("gentle");
  const [culture, setCulture] = useState("pan_african");
  const [divMode, setDivMode] = useState("teaching");
  const [safety, setSafety] = useState("conservative");
  const [consentLogId, setConsentLogId] = useState(null);
  const [consentOpen, setConsentOpen] = useState(false);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth" }); }, [msgs]);

  // Whenever sage params change such that consent is no longer required,
  // clear the stale id so the user is re-prompted if they raise intensity again.
  useEffect(() => {
    if (!needsConsent(intensity, safety)) setConsentLogId(null);
  }, [intensity, safety]);

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
      setMsgs((m) => [...m, { role: "assistant", text: r.data.reply }]);
    } catch (e) {
      const detail = e?.response?.data?.detail;
      if (e?.response?.status === 403 && typeof detail === "string" && detail.includes("Consent")) {
        toast.error("Consent required for this practice.");
        setConsentLogId(null);
        setConsentOpen(true);
      } else {
        toast.error("AI unavailable. Check configuration or try again.");
        setMsgs((m) => [...m, { role: "assistant", text: "Sorry — I couldn't reach the tutor service. Try again in a moment." }]);
      }
    } finally { setLoading(false); }
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
                className={`px-4 py-2 text-xs font-bold uppercase tracking-widest border transition-colors inline-flex items-center gap-2 ${
                  active ? "bg-ink text-white border-ink" : "bg-white text-ink border-ink/20 hover:border-ink"
                }`}
                data-testid={`mode-${m.key}`}
              >
                {Icon && <Icon className={`w-4 h-4 ${active ? "text-copper" : "text-copper"}`} />}
                {m.label}
              </button>
            );
          })}
        </div>

        {sageActive && (
          <SageParamPanel
            depth={depth} setDepth={setDepth}
            intensity={intensity} setIntensity={setIntensity}
            culture={culture} setCulture={setCulture}
            divMode={divMode} setDivMode={setDivMode}
            safety={safety} setSafety={setSafety}
            consentLogId={consentLogId}
            consentRequired={consentRequired}
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
              <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
                <div className={`max-w-[80%] p-4 text-sm leading-relaxed whitespace-pre-wrap ${m.role === "user" ? "bg-ink text-white" : "bg-bone border border-ink/10"}`} data-testid={`msg-${i}`}>
                  {m.text}
                </div>
              </div>
            ))}
            {loading && <div className="text-sm text-ink/50 italic">Tutor is thinking…</div>}
            <div ref={endRef} />
          </div>
          <div className="border-t border-ink/10 p-4 flex gap-2">
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
// Sage parameter panel — visible only when Ancestral Sage is selected.
// ---------------------------------------------------------------------------
function SageParamPanel({
  depth, setDepth, intensity, setIntensity, culture, setCulture,
  divMode, setDivMode, safety, setSafety,
  consentLogId, consentRequired, onClearConsent, onOpenConsent,
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
    </div>
  );
}

// ---------------------------------------------------------------------------
// Two-step consent modal. Posts to /api/ai/consent and returns log id.
// ---------------------------------------------------------------------------
function ConsentModal({ intensity, safety, onClose, onGranted }) {
  const [confirmYes, setConfirmYes] = useState("");
  const [comprehension, setComprehension] = useState("");
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

  return (
    <div
      className="fixed inset-0 bg-ink/70 flex items-center justify-center z-50 p-4"
      data-testid="sage-consent-modal"
      role="dialog"
      aria-modal="true"
    >
      <div className="bg-bone max-w-lg w-full p-8 border-l-4 border-l-copper">
        <div className="overline text-copper">Consent Required</div>
        <h3 className="font-heading text-2xl font-bold mt-2 flex items-center gap-2">
          <ShieldAlert className="w-6 h-6 text-copper" /> Deep practice gate
        </h3>

        <p className="text-sm text-ink/70 mt-4">
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

        <p className="text-sm text-ink/70 mt-5">
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
            disabled={busy || !yesOk || !compOk}
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
