/**
 * useBrowserTTS — shared native browser text-to-speech hook.
 *
 * Replaces the old per-persona paid voice system (ElevenLabs / OpenAI TTS).
 * Every voice-output surface in the app now speaks through the browser's
 * built-in speechSynthesis: zero cost, zero keys, works on every device.
 *
 * Features:
 *  - A single global on/off toggle (persisted to localStorage per key)
 *  - speak(text) with cancel-before-speak (no overlapping voices)
 *  - Auto-cancel on unmount
 *  - Prefers a natural English voice; falls back to any English voice
 *  - Optional rate / volume controls
 *
 * Usage:
 *   const { enabled, toggle, speak, stop, supported, speaking } = useBrowserTTS({
 *     storageKey: "ai_tutor_audio",   // unique per surface
 *     defaultOn: false,
 *     onStart: () => setPlaying(true),
 *     onEnd:   () => setPlaying(false),
 *   });
 *
 *   <button onClick={toggle}>{enabled ? "Voice On" : "Voice Off"}</button>
 *   <button onClick={() => speak(reply)}>🔊 Speak</button>
 */

import { useState, useRef, useCallback, useEffect } from "react";

const MAX_CHARS = 500; // browsers stall on very long utterances; chunk long text

function pickVoice() {
  if (typeof window === "undefined" || !window.speechSynthesis) return null;
  const voices = window.speechSynthesis.getVoices();
  if (!voices || !voices.length) return null;
  // 1) A natural-sounding English voice by name
  const preferred =
    voices.find((v) =>
      v.lang.toLowerCase().startsWith("en") &&
      /natural|premium|google us english|samantha|karen|zira|salli|joanna|aria|jenny|guy|daniel|ava|emma/i.test(v.name)
    ) ||
    // 2) Any English voice
    voices.find((v) => v.lang.toLowerCase().startsWith("en")) ||
    // 3) First available
    voices[0];
  return preferred;
}

export function useBrowserTTS({
  storageKey = "wai_tts",
  defaultOn = false,
  onStart,
  onEnd,
  onError,
} = {}) {
  const [enabled, setEnabled] = useState(() => {
    if (typeof window === "undefined") return defaultOn;
    try {
      const saved = localStorage.getItem(storageKey);
      if (saved !== null) return saved === "1";
    } catch { /* ignore */ }
    return defaultOn;
  });

  const [speaking, setSpeaking] = useState(false);
  const [rate, setRate] = useState(1.0);
  const [volume, setVolume] = useState(1.0);
  const onStartRef = useRef(onStart);
  const onEndRef = useRef(onEnd);
  const onErrorRef = useRef(onError);
  const voicesLoadedRef = useRef(false);

  useEffect(() => { onStartRef.current = onStart; }, [onStart]);
  useEffect(() => { onEndRef.current = onEnd; }, [onEnd]);
  useEffect(() => { onErrorRef.current = onError; }, [onError]);

  // Persist toggle
  useEffect(() => {
    try { localStorage.setItem(storageKey, enabled ? "1" : "0"); } catch { /* ignore */ }
  }, [enabled, storageKey]);

  // Chrome loads voices asynchronously — warm the list once.
  useEffect(() => {
    if (typeof window === "undefined" || !window.speechSynthesis) return;
    if (!voicesLoadedRef.current) {
      voicesLoadedRef.current = true;
      window.speechSynthesis.getVoices();
      if (window.speechSynthesis.onvoiceschanged !== undefined) {
        window.speechSynthesis.onvoiceschanged = () => { window.speechSynthesis.getVoices(); };
      }
    }
  }, []);

  const supported = typeof window !== "undefined" && "speechSynthesis" in window;

  const stop = useCallback(() => {
    if (typeof window === "undefined" || !window.speechSynthesis) return;
    window.speechSynthesis.cancel();
    setSpeaking(false);
    onEndRef.current?.();
  }, []);

  const speak = useCallback((text) => {
    if (!enabled || !text) return;
    if (typeof window === "undefined" || !window.speechSynthesis) {
      onErrorRef.current?.("Speech synthesis is not supported in this browser.");
      return;
    }
    try {
      // Cancel anything already playing so voices never overlap.
      window.speechSynthesis.cancel();
      const chunk = String(text).slice(0, MAX_CHARS);
      const utt = new SpeechSynthesisUtterance(chunk);
      const voice = pickVoice();
      if (voice) utt.voice = voice;
      utt.rate = rate;
      utt.volume = volume;
      utt.onstart = () => { setSpeaking(true); onStartRef.current?.(); };
      utt.onend = () => { setSpeaking(false); onEndRef.current?.(); };
      utt.onerror = (e) => {
        setSpeaking(false);
        onEndRef.current?.();
        if (e?.error && e.error !== "interrupted" && e.error !== "canceled") {
          onErrorRef.current?.("Voice playback failed. Text remains visible.");
        }
      };
      window.speechSynthesis.speak(utt);
    } catch (err) {
      setSpeaking(false);
      onEndRef.current?.();
      onErrorRef.current?.("Couldn't play audio. Text remains visible.");
    }
  }, [enabled, rate, volume]);

  // Auto-cancel on unmount so audio never keeps playing after navigation.
  useEffect(() => {
    return () => {
      if (typeof window !== "undefined" && window.speechSynthesis) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  const toggle = useCallback(() => {
    setEnabled((v) => {
      const next = !v;
      if (!next) {
        // Turning off should stop anything currently speaking.
        if (typeof window !== "undefined" && window.speechSynthesis) {
          window.speechSynthesis.cancel();
        }
      }
      return next;
    });
  }, []);

  return { enabled, setEnabled, toggle, speak, stop, supported, speaking, rate, setRate, volume, setVolume };
}
