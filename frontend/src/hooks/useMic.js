/**
 * useMic — shared microphone / SpeechRecognition hook
 *
 * Handles:
 *  - Browser support check (Chrome/Edge only)
 *  - getUserMedia permission request before starting (required or browser silently blocks)
 *  - Continuous or single-shot mode
 *  - Auto-stop on silence (continuous mode, configurable ms)
 *  - Clean teardown on unmount
 *
 * Usage:
 *   const { listening, toggle, stop } = useMic({
 *     onResult: (text) => setInput(text),
 *     onError:  (msg)  => toast.error(msg),
 *     continuous: true,       // optional, default false
 *     silenceMs:  2000,       // optional, default 2000 — only used when continuous=true
 *     lang:       "en-US",    // optional
 *   });
 */

import { useState, useRef, useCallback, useEffect } from "react";

const getSR = () =>
  typeof window !== "undefined"
    ? window.SpeechRecognition || window.webkitSpeechRecognition || null
    : null;

export function useMic({
  onResult,
  onError,
  continuous = false,
  silenceMs  = 2000,
  lang       = "en-US",
} = {}) {
  const [listening, setListening] = useState(false);
  const recRef     = useRef(null);
  const silenceRef = useRef(null);

  // Clean up on unmount
  useEffect(() => {
    return () => {
      clearTimeout(silenceRef.current);
      recRef.current?.stop();
    };
  }, []);

  const stop = useCallback(() => {
    clearTimeout(silenceRef.current);
    recRef.current?.stop();
    recRef.current = null;
    setListening(false);
  }, []);

  const start = useCallback(async () => {
    const SR = getSR();
    if (!SR) {
      onError?.("Voice input is not supported in this browser. Please use Chrome or Edge.");
      return;
    }

    // Request mic permission explicitly — browser silently blocks SpeechRecognition
    // if getUserMedia hasn't been called first on some browsers/versions.
    try {
      await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch {
      onError?.("Microphone access was denied. Please allow mic access in your browser settings.");
      return;
    }

    if (recRef.current) { recRef.current.stop(); recRef.current = null; }

    const rec = new SR();
    rec.lang            = lang;
    rec.continuous      = continuous;
    rec.interimResults  = continuous; // interim only useful in continuous mode
    rec.maxAlternatives = 1;

    rec.onresult = (ev) => {
      let txt = "";
      for (let i = ev.resultIndex; i < ev.results.length; i++) {
        if (ev.results[i].isFinal) txt += ev.results[i][0].transcript;
      }
      const trimmed = txt.trim();
      if (trimmed) {
        onResult?.(trimmed);
        if (continuous) {
          // reset silence timer on each new word
          clearTimeout(silenceRef.current);
          silenceRef.current = setTimeout(stop, silenceMs);
        }
      }
    };

    rec.onerror = (ev) => {
      if (ev.error === "no-speech") return; // ignore — just silence
      onError?.(`Mic error: ${ev.error || "unknown"}`);
      recRef.current = null;
      setListening(false);
    };

    rec.onend = () => {
      recRef.current = null;
      setListening(false);
    };

    recRef.current = rec;
    try {
      rec.start();
      setListening(true);
      if (continuous) {
        silenceRef.current = setTimeout(stop, silenceMs);
      }
    } catch {
      recRef.current = null;
      onError?.("Could not start microphone.");
    }
  }, [lang, continuous, silenceMs, onResult, onError, stop]);

  const toggle = useCallback(() => {
    if (listening) stop();
    else start();
  }, [listening, start, stop]);

  return { listening, toggle, stop, start, supported: !!getSR() };
}
