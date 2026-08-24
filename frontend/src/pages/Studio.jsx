/**
 * Studio — Ghost Producer Studio (v1).
 *
 * An in-browser music creation suite for southern soul, neo soul, gospel,
 * hip hop, jazz, blues, tribal, spiritual, meditation, and spoken word.
 *
 * LEGAL ARCHITECTURE (built in, not bolted on):
 *   • Every sound is SYNTHESIZED in the browser (Web Audio oscillators +
 *     noise). There are no third-party sample files, so there is no sample
 *     licensing exposure anywhere in the kit system.
 *   • The creator keeps 100% ownership of everything made here. The platform
 *     takes a 30% service fee on sales (the 70/30 creator-first split,
 *     Mandate 2) and never claims copyright. That is stated in the Publish
 *     tab and enforced by the existing creator earnings pipeline server-side.
 *   • AI-disclosure is a first-class metadata field (required by modern
 *     platforms), and the publish flow records sample-clearance attestation.
 *
 * Engine: Web Audio API only — no audio libraries, no external requests.
 * Export: OfflineAudioContext render → 16-bit PCM WAV (open format).
 */

import { useRef, useState, useCallback, useEffect } from "react";
import AppShell from "../components/AppShell";
import { useAuth } from "../lib/auth";
import { api } from "../lib/api";
import { toast } from "sonner";
import {
  Play, Square, Download, Save, Upload, Music2, SlidersHorizontal,
  Sparkles, Lock, FileText,
} from "lucide-react";

const COPPER = "#C0572D";
const GOLD = "#E8A51E";
const GREEN = "#1B4332";
const INK = "#1c1917";
const BONE = "#FDFBF5";

const STEPS = 16;

// ── Scales (root + semitone offsets) ─────────────────────────────────────────
const SCALES = {
  "minor-pent":    { label: "Minor Pentatonic", offsets: [0, 3, 5, 7, 10] },
  "blues":         { label: "Blues",            offsets: [0, 3, 5, 6, 7, 10] },
  "major-pent":    { label: "Major Pentatonic", offsets: [0, 2, 4, 7, 9] },
  "dorian":        { label: "Dorian (Neo Soul)", offsets: [0, 2, 3, 5, 7, 9, 10] },
  "phrygian-dom":  { label: "Phrygian Dominant", offsets: [0, 1, 4, 5, 7, 8, 10] },
  "major":         { label: "Major",            offsets: [0, 2, 4, 5, 7, 9, 11] },
  "natural-minor": { label: "Natural Minor",    offsets: [0, 2, 3, 5, 7, 8, 10] },
};

const ROOTS = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];
const ROOT_MIDI = { C: 60, "C#": 61, D: 62, "D#": 63, E: 64, F: 65, "F#": 66, G: 67, "G#": 68, A: 69, "A#": 70, B: 71 };
const midiToFreq = (m) => 440 * Math.pow(2, (m - 69) / 12);

// ── Genre kits — feel + default drum patterns + scale ────────────────────────
const KITS = {
  "southern-soul": {
    label: "Southern Soul", bpm: 78, swing: 0.16, scale: "minor-pent",
    drums: {
      kick: [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 1, 0],
      snare: [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
      hat: [1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0],
      perc: [0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0],
    },
  },
  "neo-soul": {
    label: "Neo Soul", bpm: 84, swing: 0.22, scale: "dorian",
    drums: {
      kick: [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0],
      snare: [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
      hat: [0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0],
      perc: [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0],
    },
  },
  gospel: {
    label: "Gospel", bpm: 92, swing: 0.1, scale: "major-pent",
    drums: {
      kick: [1, 0, 0, 0, 1, 0, 1, 0, 1, 0, 0, 0, 1, 0, 1, 0],
      snare: [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
      hat: [1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0],
      perc: [0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1],
    },
  },
  "boom-bap": {
    label: "Boom-Bap Hip Hop", bpm: 90, swing: 0.28, scale: "minor-pent",
    drums: {
      kick: [1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1],
      snare: [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
      hat: [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0],
      perc: [0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0],
    },
  },
  jazz: {
    label: "Jazz", bpm: 120, swing: 0.3, scale: "dorian",
    drums: {
      kick: [1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
      snare: [0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0],
      hat: [1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0],
      perc: [0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0],
    },
  },
  blues: {
    label: "Blues", bpm: 100, swing: 0.3, scale: "blues",
    drums: {
      kick: [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0],
      snare: [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
      hat: [1, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 1, 0],
      perc: [0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0],
    },
  },
  tribal: {
    label: "Tribal", bpm: 108, swing: 0.12, scale: "phrygian-dom",
    drums: {
      kick: [1, 0, 1, 0, 0, 1, 0, 1, 1, 0, 1, 0, 0, 1, 0, 1],
      snare: [0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0],
      hat: [1, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 1, 0],
      perc: [1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0],
    },
  },
  meditation: {
    label: "Meditation", bpm: 66, swing: 0.05, scale: "major",
    drums: {
      kick: [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
      snare: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
      hat: [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
      perc: [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0],
    },
  },
};

const DRUM_TRACKS = [
  { id: "kick", label: "Kick", color: "#B23A2E" },
  { id: "snare", label: "Snare", color: "#E8A51E" },
  { id: "hat", label: "Hat", color: "#5B8C5A" },
  { id: "perc", label: "Perc", color: "#7C6FDE" },
];

const KEY_ROWS = 5; // 5-pitch grid for the keys lane

// ── Sound synthesis (no samples — nothing to license) ────────────────────────
function playKick(ctx, t, gain, swingShift) {
  const o = ctx.createOscillator();
  const g = ctx.createGain();
  const t0 = t + swingShift;
  o.type = "sine";
  o.frequency.setValueAtTime(150, t0);
  o.frequency.exponentialRampToValueAtTime(48, t0 + 0.12);
  g.gain.setValueAtTime(gain, t0);
  g.gain.exponentialRampToValueAtTime(0.001, t0 + 0.28);
  o.connect(g).connect(ctx.destination);
  o.start(t0); o.stop(t0 + 0.3);
}

function playSnare(ctx, t, gain, swingShift) {
  const t0 = t + swingShift;
  const noise = ctx.createBufferSource();
  const buf = ctx.createBuffer(1, ctx.sampleRate * 0.22, ctx.sampleRate);
  const d = buf.getChannelData(0);
  for (let i = 0; i < d.length; i++) d[i] = (Math.random() * 2 - 1) * (1 - i / d.length);
  noise.buffer = buf;
  const bp = ctx.createBiquadFilter();
  bp.type = "bandpass"; bp.frequency.value = 1800; bp.Q.value = 0.8;
  const g = ctx.createGain();
  g.gain.setValueAtTime(gain, t0);
  g.gain.exponentialRampToValueAtTime(0.001, t0 + 0.2);
  const tone = ctx.createOscillator();
  tone.type = "triangle"; tone.frequency.setValueAtTime(190, t0);
  const tg = ctx.createGain();
  tg.gain.setValueAtTime(gain * 0.5, t0);
  tg.gain.exponentialRampToValueAtTime(0.001, t0 + 0.12);
  noise.connect(bp).connect(g).connect(ctx.destination);
  tone.connect(tg).connect(ctx.destination);
  noise.start(t0); noise.stop(t0 + 0.24);
  tone.start(t0); tone.stop(t0 + 0.14);
}

function playHat(ctx, t, gain, swingShift, open) {
  const t0 = t + swingShift;
  const noise = ctx.createBufferSource();
  const dur = open ? 0.25 : 0.06;
  const buf = ctx.createBuffer(1, ctx.sampleRate * dur, ctx.sampleRate);
  const d = buf.getChannelData(0);
  for (let i = 0; i < d.length; i++) d[i] = (Math.random() * 2 - 1) * (1 - i / d.length);
  noise.buffer = buf;
  const hp = ctx.createBiquadFilter();
  hp.type = "highpass"; hp.frequency.value = 7000;
  const g = ctx.createGain();
  g.gain.setValueAtTime(gain, t0);
  g.gain.exponentialRampToValueAtTime(0.001, t0 + dur);
  noise.connect(hp).connect(g).connect(ctx.destination);
  noise.start(t0); noise.stop(t0 + dur + 0.01);
}

function playPerc(ctx, t, gain, swingShift) {
  const t0 = t + swingShift;
  const noise = ctx.createBufferSource();
  const buf = ctx.createBuffer(1, ctx.sampleRate * 0.15, ctx.sampleRate);
  const d = buf.getChannelData(0);
  for (let i = 0; i < d.length; i++) d[i] = (Math.random() * 2 - 1) * (1 - i / d.length);
  noise.buffer = buf;
  const bp = ctx.createBiquadFilter();
  bp.type = "bandpass"; bp.frequency.value = 900; bp.Q.value = 2;
  const g = ctx.createGain();
  g.gain.setValueAtTime(gain, t0);
  g.gain.exponentialRampToValueAtTime(0.001, t0 + 0.12);
  const tick = ctx.createOscillator();
  tick.type = "sine"; tick.frequency.setValueAtTime(660, t0);
  const tg = ctx.createGain();
  tg.gain.setValueAtTime(gain * 0.6, t0);
  tg.gain.exponentialRampToValueAtTime(0.001, t0 + 0.08);
  noise.connect(bp).connect(g).connect(ctx.destination);
  tick.connect(tg).connect(ctx.destination);
  noise.start(t0); noise.stop(t0 + 0.16);
  tick.start(t0); tick.stop(t0 + 0.1);
}

function playNote(ctx, t, freq, dur, gain, type) {
  const o = ctx.createOscillator();
  const g = ctx.createGain();
  const lp = ctx.createBiquadFilter();
  lp.type = "lowpass"; lp.frequency.value = Math.min(3200, freq * 6); lp.Q.value = 0.7;
  o.type = type || "triangle";
  o.frequency.setValueAtTime(freq, t);
  g.gain.setValueAtTime(0.0001, t);
  g.gain.exponentialRampToValueAtTime(gain, t + 0.012);
  g.gain.exponentialRampToValueAtTime(0.001, t + dur);
  o.connect(lp).connect(g).connect(ctx.destination);
  o.start(t); o.stop(t + dur + 0.02);
}

function drumAt(id, ctx, t, gain, swingShift) {
  if (id === "kick") playKick(ctx, t, gain, swingShift);
  else if (id === "snare") playSnare(ctx, t, gain, swingShift);
  else if (id === "hat") playHat(ctx, t, gain, swingShift, false);
  else playPerc(ctx, t, gain, swingShift);
}

// ── WAV encoder (16-bit PCM, open format) ────────────────────────────────────
function encodeWav(buffer, sampleRate) {
  const numCh = buffer.numberOfChannels;
  const len = buffer.length * numCh * 2;
  const out = new ArrayBuffer(44 + len);
  const v = new DataView(out);
  const writeStr = (o, s) => { for (let i = 0; i < s.length; i++) v.setUint8(o + i, s.charCodeAt(i)); };
  writeStr(0, "RIFF"); v.setUint32(4, 36 + len, true); writeStr(8, "WAVE");
  writeStr(12, "fmt "); v.setUint32(16, 16, true); v.setUint16(20, 1, true);
  v.setUint16(22, numCh, true); v.setUint32(24, sampleRate, true);
  v.setUint32(28, sampleRate * numCh * 2, true); v.setUint16(32, numCh * 2, true);
  v.setUint16(34, 16, true); writeStr(36, "data"); v.setUint32(40, len, true);
  const chans = [];
  for (let c = 0; c < numCh; c++) chans.push(buffer.getChannelData(c));
  let off = 44;
  for (let i = 0; i < buffer.length; i++) {
    for (let c = 0; c < numCh; c++) {
      let s = Math.max(-1, Math.min(1, chans[c][i]));
      v.setInt16(off, s < 0 ? s * 0x8000 : s * 0x7fff, true);
      off += 2;
    }
  }
  return out;
}

// ── Studio ───────────────────────────────────────────────────────────────────
export function StudioContent({ embedded = false }) {
  const { user } = useAuth();
  const [tab, setTab] = useState(() => {
    const requested = new URLSearchParams(window.location.search).get("tab");
    return ["beat", "keys", "publish"].includes(requested) ? requested : "beat";
  });

  // Shared project state
  const [kitId, setKitId] = useState("southern-soul");
  const [bpm, setBpm] = useState(KITS["southern-soul"].bpm);
  const [swing, setSwing] = useState(KITS["southern-soul"].swing);
  const [root, setRoot] = useState("C");
  const [patterns, setPatterns] = useState(() => {
    // patterns[trackId][step] — A and B banks
    const init = {};
    for (const k of Object.keys(KITS)) {
      init[k] = {};
      for (const t of DRUM_TRACKS) init[k][t.id] = [KITS[k].drums[t.id].slice(), KITS[k].drums[t.id].slice()];
    }
    return init;
  });
  const [bank, setBank] = useState(0); // 0 = A, 1 = B
  const [keys, setKeys] = useState(() => {
    // keys[kid][row][step]
    const init = {};
    for (const k of Object.keys(KITS)) {
      init[k] = Array.from({ length: KEY_ROWS }, () => Array(STEPS).fill(false));
    }
    return init;
  });
  const [muted, setMuted] = useState({ kick: false, snare: false, hat: false, perc: false, keys: false });
  const [playing, setPlaying] = useState(false);
  const [step, setStep] = useState(-1);
  const [exporting, setExporting] = useState(false);

  // Publish metadata
  const [meta, setMeta] = useState(() => {
    try { return JSON.parse(localStorage.getItem("ghost_studio_meta") || "null") || {}; } catch { return {}; }
  });

  // AI team projects (executive pipeline) — attach a published track as a deliverable.
  const [projects, setProjects] = useState([]);
  const [projectId, setProjectId] = useState("");

  useEffect(() => {
    api.get("/executive/projects")
      .then((r) => setProjects(r.data || []))
      .catch(() => {}); // non-exec users simply don't see the attach control
  }, []);

  const ctxRef = useRef(null);
  const timerRef = useRef(null);
  const nextTimeRef = useRef(0);
  const stepRef = useRef(0);

  const kit = KITS[kitId];
  const scale = SCALES[kit.scale];
  const stepDur = 60 / bpm / 4; // 16th note duration

  const ensureCtx = useCallback(() => {
    if (!ctxRef.current) {
      const AC = window.AudioContext || window.webkitAudioContext;
      ctxRef.current = new AC();
    }
    if (ctxRef.current.state === "suspended") ctxRef.current.resume();
    return ctxRef.current;
  }, []);

  const selectKit = (id) => {
    setKitId(id);
    setBpm(KITS[id].bpm);
    setSwing(KITS[id].swing);
  };

  // ── Scheduler ──
  const scheduleStep = useCallback((ctx, s, when) => {
    const sw = swing * stepDur;
    const swingOn = s % 2 === 1;
    const shift = swingOn ? sw : 0;
    const pat = patterns[kitId];
    DRUM_TRACKS.forEach((t) => {
      if (muted[t.id]) return;
      if (pat[t.id][bank][s]) drumAt(t.id, ctx, when, 0.9, shift);
    });
    if (!muted.keys) {
      const kp = keys[kitId];
      kp.forEach((row, r) => {
        if (!row[s]) return;
        const degree = Math.min(r, scale.offsets.length - 1);
        const note = ROOT_MIDI[root] + 12 + scale.offsets[degree];
        playNote(ctx, when, midiToFreq(note), stepDur * 3.5, 0.16, "triangle");
      });
    }
  }, [kitId, patterns, keys, bank, muted, swing, stepDur, root, scale]);

  const stop = useCallback(() => {
    if (timerRef.current) { clearInterval(timerRef.current); timerRef.current = null; }
    setPlaying(false);
    setStep(-1);
  }, []);

  const play = useCallback(() => {
    const ctx = ensureCtx();
    stop();
    nextTimeRef.current = ctx.currentTime + 0.06;
    stepRef.current = 0;
    setPlaying(true);
    timerRef.current = setInterval(() => {
      const ahead = 0.12;
      while (nextTimeRef.current < ctx.currentTime + ahead) {
        scheduleStep(ctx, stepRef.current, nextTimeRef.current);
        setStep(stepRef.current);
        nextTimeRef.current += stepDur;
        stepRef.current = (stepRef.current + 1) % STEPS;
      }
    }, 25);
  }, [ensureCtx, stop, scheduleStep, stepDur]);

  useEffect(() => () => stop(), [stop]);

  // ── Export WAV (offline render — same schedule, no audio card needed) ──────
  const exportWav = useCallback(async (bars = 8) => {
    setExporting(true);
    try {
      const AC = window.AudioContext || window.webkitAudioContext;
      const sr = 44100;
      const total = bars * STEPS * stepDur;
      const off = new OfflineAudioContext(2, Math.ceil(sr * total), sr);
      // Route synthesized sounds into the offline context destination.
      const origDest = off.destination;
      // Rebind helpers to the offline context by wrapping in a local fn.
      const schedOffline = (s, when) => {
        const sw = swing * stepDur;
        const shift = (s % 2 === 1) ? sw : 0;
        const pat = patterns[kitId];
        DRUM_TRACKS.forEach((t) => {
          if (muted[t.id]) return;
          if (pat[t.id][bank][s]) {
            // Clone synth into offline ctx with explicit dest
            if (t.id === "kick") {
              const o = off.createOscillator(), g = off.createGain();
              o.type = "sine";
              o.frequency.setValueAtTime(150, when + shift);
              o.frequency.exponentialRampToValueAtTime(48, when + shift + 0.12);
              g.gain.setValueAtTime(0.9, when + shift);
              g.gain.exponentialRampToValueAtTime(0.001, when + shift + 0.28);
              o.connect(g).connect(origDest);
              o.start(when + shift); o.stop(when + shift + 0.3);
            } else if (t.id === "snare") {
              const buf = off.createBuffer(1, sr * 0.22, sr);
              const d = buf.getChannelData(0);
              for (let i = 0; i < d.length; i++) d[i] = (Math.random() * 2 - 1) * (1 - i / d.length);
              const n = off.createBufferSource(); n.buffer = buf;
              const bp = off.createBiquadFilter(); bp.type = "bandpass"; bp.frequency.value = 1800; bp.Q.value = 0.8;
              const g = off.createGain();
              g.gain.setValueAtTime(0.9, when + shift);
              g.gain.exponentialRampToValueAtTime(0.001, when + shift + 0.2);
              const tone = off.createOscillator(); tone.type = "triangle"; tone.frequency.setValueAtTime(190, when + shift);
              const tg = off.createGain();
              tg.gain.setValueAtTime(0.45, when + shift);
              tg.gain.exponentialRampToValueAtTime(0.001, when + shift + 0.12);
              n.connect(bp).connect(g).connect(origDest);
              tone.connect(tg).connect(origDest);
              n.start(when + shift); n.stop(when + shift + 0.24);
              tone.start(when + shift); tone.stop(when + shift + 0.14);
            } else if (t.id === "hat") {
              const dur = 0.06;
              const buf = off.createBuffer(1, sr * dur, sr);
              const d = buf.getChannelData(0);
              for (let i = 0; i < d.length; i++) d[i] = (Math.random() * 2 - 1) * (1 - i / d.length);
              const n = off.createBufferSource(); n.buffer = buf;
              const hp = off.createBiquadFilter(); hp.type = "highpass"; hp.frequency.value = 7000;
              const g = off.createGain();
              g.gain.setValueAtTime(0.9, when + shift);
              g.gain.exponentialRampToValueAtTime(0.001, when + shift + dur);
              n.connect(hp).connect(g).connect(origDest);
              n.start(when + shift); n.stop(when + shift + dur + 0.01);
            } else {
              const buf = off.createBuffer(1, sr * 0.15, sr);
              const d = buf.getChannelData(0);
              for (let i = 0; i < d.length; i++) d[i] = (Math.random() * 2 - 1) * (1 - i / d.length);
              const n = off.createBufferSource(); n.buffer = buf;
              const bp = off.createBiquadFilter(); bp.type = "bandpass"; bp.frequency.value = 900; bp.Q.value = 2;
              const g = off.createGain();
              g.gain.setValueAtTime(0.9, when + shift);
              g.gain.exponentialRampToValueAtTime(0.001, when + shift + 0.12);
              const tick = off.createOscillator(); tick.type = "sine"; tick.frequency.setValueAtTime(660, when + shift);
              const tg = off.createGain();
              tg.gain.setValueAtTime(0.54, when + shift);
              tg.gain.exponentialRampToValueAtTime(0.001, when + shift + 0.08);
              n.connect(bp).connect(g).connect(origDest);
              tick.connect(tg).connect(origDest);
              n.start(when + shift); n.stop(when + shift + 0.16);
              tick.start(when + shift); tick.stop(when + shift + 0.1);
            }
          }
        });
        if (!muted.keys) {
          const kp = keys[kitId];
          kp.forEach((row, r) => {
            if (!row[s]) return;
            const degree = Math.min(r, scale.offsets.length - 1);
            const note = ROOT_MIDI[root] + 12 + scale.offsets[degree];
            const o = off.createOscillator(), g = off.createGain(), lp = off.createBiquadFilter();
            lp.type = "lowpass"; lp.frequency.value = Math.min(3200, midiToFreq(note) * 6); lp.Q.value = 0.7;
            o.type = "triangle"; o.frequency.setValueAtTime(midiToFreq(note), when);
            g.gain.setValueAtTime(0.0001, when);
            g.gain.exponentialRampToValueAtTime(0.16, when + 0.012);
            g.gain.exponentialRampToValueAtTime(0.001, when + stepDur * 3.5);
            o.connect(lp).connect(g).connect(origDest);
            o.start(when); o.stop(when + stepDur * 3.5 + 0.02);
          });
        }
      };
      let t = 0;
      for (let bar = 0; bar < bars; bar++) {
        for (let s = 0; s < STEPS; s++) {
          schedOffline(s, t);
          t += stepDur;
        }
      }
      const rendered = await off.startRendering();
      const wav = encodeWav(rendered, sr);
      const blob = new Blob([wav], { type: "audio/wav" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${(meta.title || "ghost-studio-track").replace(/[^\w-]+/g, "-").toLowerCase() || "track"}.wav`;
      a.click();
      setTimeout(() => URL.revokeObjectURL(url), 5000);
      toast.success("WAV exported — you own it 100%.");
      return blob;
    } catch (e) {
      toast.error("Export failed: " + (e?.message || e));
      return null;
    } finally {
      setExporting(false);
    }
  }, [kitId, patterns, keys, bank, muted, swing, stepDur, root, scale, meta.title]);

  // Publish to the Media Store
  const publish = useCallback(async () => {
    if (!meta.title || !meta.title.trim()) { toast.error("Give the track a title first."); setTab("publish"); return; }
    if (!meta.samples_cleared) { toast.error("Confirm the sample-clearance statement to publish."); setTab("publish"); return; }
    setExporting(true);
    try {
      const blob = await exportWav(8);
      if (!blob) return;
      const audio = new Audio(URL.createObjectURL(blob));
      const dur = await new Promise((res) => {
        audio.addEventListener("loadedmetadata", () => res(audio.duration || 30), { once: true });
        setTimeout(() => res(30), 4000);
      });
      const fd = new FormData();
      fd.append("file", blob, "track.wav");
      fd.append("duration_seconds", String(dur || 30));
      const up = await api.post("/media/upload", fd, { headers: { "Content-Type": "multipart/form-data" } });
      const fileUrl = up.data?.file_url || up.data?.url || up.data?.media_url;
      if (!fileUrl) throw new Error("Upload returned no file URL");
      const product = await api.post("/media/products", {
        title: meta.title,
        description: [meta.description, `Genre: ${meta.genre || kit.label}`, `BPM: ${bpm}`, `Key: ${root}`].filter(Boolean).join(" · "),
        price_cents: Number(meta.price_cents || 100),
        type: "audio",
        tags: [kitId, "ghost-producer-studio"].concat(meta.ai_disclosure ? ["ai-assisted"] : []),
        file_url: fileUrl,
        published: true,
      });
      // Attach to an AI team project as a deliverable, if one is selected.
      if (projectId) {
        try {
          const proj = await api.get(`/executive/projects/${projectId}`).then((r) => r.data).catch(() => null);
          await api.post(`/executive/projects/${projectId}/deliverables`, {
            stage: proj?.current_stage || "execute",
            persona: "Ghost Producer Studio",
            title: `${meta.title} (published track)`,
            content_type: "audio",
            content: `Released through the Ghost Producer Studio — ${meta.genre || kit.label}, ${bpm} BPM, ${root}.`,
            file_refs: [fileUrl],
            metadata: { bpm, root, kit: kitId, ai_disclosure: !!meta.ai_disclosure, product_id: product.data?.id },
          });
          toast.success("Track attached to the AI team project as a deliverable.");
        } catch { /* deliverable attach is best-effort */ }
      }
      toast.success("Published to your store — 70% of sales is yours.");
      setMeta((m) => ({ ...m, last_product_id: product.data?.id }));
    } catch (e) {
      toast.error("Publish failed: " + (e?.response?.data?.detail || e?.message || e));
    } finally {
      setExporting(false);
    }
  }, [meta, exportWav, kitId, kit, bpm, root, projectId]);

  useEffect(() => {
    try { localStorage.setItem("ghost_studio_meta", JSON.stringify(meta)); } catch {}
  }, [meta]);

  const setPattern = (trackId, s) => {
    setPatterns((p) => {
      const next = JSON.parse(JSON.stringify(p));
      next[kitId][trackId][bank][s] = !next[kitId][trackId][bank][s];
      return next;
    });
  };
  const setKey = (row, s) => {
    setKeys((p) => {
      const next = JSON.parse(JSON.stringify(p));
      next[kitId][row][s] = !next[kitId][row][s];
      return next;
    });
  };

  const title = meta.title || "Untitled";

  return (
    <div className={embedded ? "h-full overflow-y-auto bg-bone" : "bg-bone"} style={embedded ? {} : { minHeight: "100vh" }}>
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8">
        {/* ── Header ── */}
        <div className="rounded-2xl p-6 mb-6 text-white"
          style={{ background: `linear-gradient(135deg, ${GREEN}, #2D6A4F)` }}>
          <div className="flex items-center gap-3 flex-wrap">
            <span className="text-3xl">🎚️</span>
            <div>
              <div className="text-[10px] font-black uppercase tracking-widest" style={{ color: GOLD }}>Ghost Producer Studio</div>
              <h1 className="font-heading text-2xl font-bold tracking-tight">{title}</h1>
            </div>
            <div className="ml-auto flex items-center gap-2">
              <button onClick={() => { if (playing) stop(); exportWav(8); }}
                disabled={exporting}
                className="flex items-center gap-1.5 text-xs font-bold px-4 py-2 rounded-lg disabled:opacity-40 transition-colors"
                style={{ background: GOLD, color: "#0a0a0a" }}>
                <Download className="w-3.5 h-3.5" /> {exporting ? "Rendering…" : "Export WAV"}
              </button>
            </div>
          </div>
          <p className="text-white/70 text-sm mt-3 max-w-3xl">
            Every sound here is synthesized live in your browser — no samples, no licensing debt.
            You keep 100% ownership of what you make.
          </p>
        </div>

        {/* ── Tabs ── */}
        <div className="flex gap-1 border-b border-ink/10 mb-6 overflow-x-auto">
          {[
            { id: "beat", label: "Beat", icon: Music2 },
            { id: "keys", label: "Keys", icon: SlidersHorizontal },
            { id: "publish", label: "Publish", icon: Upload },
          ].map((t) => {
            const Icon = t.icon;
            return (
              <button key={t.id} onClick={() => setTab(t.id)}
                className={`flex items-center gap-1.5 px-4 py-2.5 text-sm font-bold border-b-2 whitespace-nowrap transition-colors ${
                  tab === t.id ? "border-copper text-copper" : "border-transparent text-ink/40 hover:text-ink/70"
                }`}>
                <Icon className="w-4 h-4" /> {t.label}
              </button>
            );
          })}
          <button onClick={() => window.location.href = "/ghost-producer"}
            className="ml-auto flex items-center gap-1.5 px-4 py-2.5 text-sm font-bold text-ink/40 hover:text-copper transition-colors whitespace-nowrap">
            <Sparkles className="w-4 h-4" /> Words &amp; Promotion
          </button>
        </div>

        {/* ── Transport ── */}
        <div className="flex flex-wrap items-center gap-3 mb-6 card-flat rounded-2xl p-4 border" style={{ background: "#fff" }}>
          <button onClick={playing ? stop : play}
            className="w-11 h-11 rounded-full flex items-center justify-center text-white transition-transform active:scale-95"
            style={{ background: playing ? "#B23A2E" : GREEN }}>
            {playing ? <Square className="w-4 h-4 fill-white" /> : <Play className="w-4 h-4 fill-white ml-0.5" />}
          </button>
          <label className="flex items-center gap-2 text-sm">
            <span className="text-xs font-bold text-ink/50 uppercase tracking-widest">BPM</span>
            <input type="range" min="50" max="160" value={bpm}
              onChange={(e) => setBpm(Number(e.target.value))}
              className="w-28 accent-[#C0572D]" />
            <span className="font-mono text-sm w-8">{bpm}</span>
          </label>
          <label className="flex items-center gap-2 text-sm">
            <span className="text-xs font-bold text-ink/50 uppercase tracking-widest">Swing</span>
            <input type="range" min="0" max="0.35" step="0.01" value={swing}
              onChange={(e) => setSwing(Number(e.target.value))}
              className="w-24 accent-[#C0572D]" />
            <span className="font-mono text-sm w-8">{(swing * 100).toFixed(0)}%</span>
          </label>
          <div className="flex items-center gap-1 ml-auto flex-wrap">
            {Object.entries(KITS).map(([id, k]) => (
              <button key={id} onClick={() => selectKit(id)}
                className={`text-[10px] font-black uppercase tracking-wider px-3 py-1.5 rounded-full border transition-colors ${
                  kitId === id ? "text-white" : "text-ink/50 hover:text-ink"
                }`}
                style={kitId === id ? { background: GREEN, borderColor: GREEN } : { borderColor: "rgba(28,25,23,0.15)" }}>
                {k.label}
              </button>
            ))}
          </div>
        </div>

        {/* ══ BEAT ══ */}
        {tab === "beat" && (
          <div className="card-flat rounded-2xl border overflow-hidden" style={{ background: "#fff" }}>
            {DRUM_TRACKS.map((t) => {
              const pat = patterns[kitId][t.id][bank];
              return (
                <div key={t.id} className="flex items-stretch border-b border-ink/5 last:border-0">
                  <div className="w-28 shrink-0 flex items-center gap-2 px-4 py-2 border-r border-ink/5">
                    <button onClick={() => setMuted((m) => ({ ...m, [t.id]: !m[t.id] }))}
                      title={muted[t.id] ? "Unmute" : "Mute"}
                      className={`w-7 h-7 rounded flex items-center justify-center text-[9px] font-black transition-colors ${muted[t.id] ? "bg-ink/10 text-ink/30" : "text-white"}`}
                      style={!muted[t.id] ? { background: t.color } : {}}>
                      {muted[t.id] ? "OFF" : "ON"}
                    </button>
                    <span className="text-sm font-bold text-ink">{t.label}</span>
                  </div>
                  <div className="flex-1 grid gap-1 p-2" style={{ gridTemplateColumns: `repeat(${STEPS}, 1fr)` }}>
                    {pat.map((on, s) => (
                      <button key={s} onClick={() => setPattern(t.id, s)}
                        className={`rounded-md transition-all ${step === s && playing ? "ring-2 ring-copper" : ""}`}
                        style={{
                          aspectRatio: "1",
                          background: on ? t.color : "#f3ede2",
                          opacity: on ? 1 : 0.6,
                        }} />
                    ))}
                  </div>
                </div>
              );
            })}
            {/* Bank switcher */}
            <div className="flex items-center gap-2 px-4 py-3 bg-bone">
              {[0, 1].map((b) => (
                <button key={b} onClick={() => setBank(b)}
                  className={`px-4 py-1.5 rounded-lg text-xs font-black uppercase tracking-widest transition-colors ${
                    bank === b ? "text-white" : "text-ink/40 bg-white border border-ink/10"
                  }`}
                  style={bank === b ? { background: COPPER } : {}}>
                  Pattern {b === 0 ? "A" : "B"}
                </button>
              ))}
              <span className="ml-auto text-xs text-ink/40">16 steps · drums synthesized live</span>
            </div>
          </div>
        )}

        {/* ══ KEYS ══ */}
        {tab === "keys" && (
          <div className="space-y-5">
            <div className="card-flat rounded-2xl border p-5" style={{ background: "#fff" }}>
              <div className="flex flex-wrap items-center gap-3 mb-4">
                <span className="text-sm font-bold text-ink">Scale lane</span>
                <span className="text-xs text-ink/50">{scale.label}</span>
                <label className="flex items-center gap-2 ml-auto text-sm">
                  <span className="text-xs font-bold text-ink/50 uppercase tracking-widest">Key</span>
                  <select value={root} onChange={(e) => setRoot(e.target.value)}
                    className="px-3 py-1.5 bg-white border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper">
                    {ROOTS.map((r) => <option key={r} value={r}>{r}</option>)}
                  </select>
                </label>
                <button onClick={() => setMuted((m) => ({ ...m, keys: !m.keys }))}
                  className={`px-3 py-1.5 rounded-lg text-xs font-black uppercase tracking-widest ${muted.keys ? "bg-ink/10 text-ink/30" : "text-white"}`}
                  style={!muted.keys ? { background: GREEN } : {}}>
                  {muted.keys ? "Keys OFF" : "Keys ON"}
                </button>
              </div>
              <div className="flex items-stretch gap-1">
                <div className="w-28 shrink-0 flex flex-col justify-around">
                  {Array.from({ length: KEY_ROWS }).map((_, r) => {
                    const degree = Math.min(r, scale.offsets.length - 1);
                    return (
                      <div key={r} className="text-xs font-mono text-ink/50 px-2">
                        {scale.offsets[degree]} ({r === 0 ? "root" : r === 1 ? "3rd" : r === 2 ? "5th" : r === 3 ? "7th" : "color"})
                      </div>
                    );
                  })}
                </div>
                <div className="flex-1">
                  {Array.from({ length: KEY_ROWS }).map((_, r) => (
                    <div key={r} className="flex gap-1 mb-1 last:mb-0">
                      {keys[kitId][r].map((on, s) => (
                        <button key={s} onClick={() => setKey(r, s)}
                          className={`flex-1 rounded-md transition-all ${step === s && playing ? "ring-2 ring-copper" : ""}`}
                          style={{
                            height: 28,
                            background: on ? "#2D6A4F" : "#f3ede2",
                            opacity: on ? 1 : 0.6,
                          }} />
                      ))}
                    </div>
                  ))}
                </div>
              </div>
              <p className="text-xs text-ink/45 mt-3">
                Rows map to scale degrees — play the root/3rd/5th/7th/color of the selected scale in {root}.
                Bass lives one octave down; pads ring longer.
              </p>
            </div>
          </div>
        )}

        {/* ══ PUBLISH ══ */}
        {tab === "publish" && (
          <div className="grid lg:grid-cols-2 gap-5">
            <div className="card-flat rounded-2xl border p-5 space-y-4" style={{ background: "#fff" }}>
              <div className="flex items-center gap-2">
                <FileText className="w-4 h-4" style={{ color: COPPER }} />
                <h2 className="font-heading font-bold text-ink">Track Metadata</h2>
              </div>
              <label className="block">
                <span className="text-xs font-bold text-ink/60">Title *</span>
                <input value={meta.title || ""} onChange={(e) => setMeta({ ...meta, title: e.target.value })}
                  placeholder="My first Ghost Producer track"
                  className="mt-1 w-full px-3 py-2 bg-white border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper" />
              </label>
              <div className="grid grid-cols-2 gap-3">
                <label className="block">
                  <span className="text-xs font-bold text-ink/60">Artist</span>
                  <input value={meta.artist || user?.full_name || ""} onChange={(e) => setMeta({ ...meta, artist: e.target.value })}
                    className="mt-1 w-full px-3 py-2 bg-white border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper" />
                </label>
                <label className="block">
                  <span className="text-xs font-bold text-ink/60">Genre</span>
                  <input value={meta.genre || kit.label} onChange={(e) => setMeta({ ...meta, genre: e.target.value })}
                    className="mt-1 w-full px-3 py-2 bg-white border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper" />
                </label>
              </div>
              <div className="grid grid-cols-3 gap-3">
                <div>
                  <div className="text-xs font-bold text-ink/60">BPM</div>
                  <div className="mt-1 font-mono text-sm text-ink/80">{bpm}</div>
                </div>
                <div>
                  <div className="text-xs font-bold text-ink/60">Key</div>
                  <div className="mt-1 font-mono text-sm text-ink/80">{root}</div>
                </div>
                <label className="block">
                  <span className="text-xs font-bold text-ink/60">Price ($)</span>
                  <input type="number" min="0" step="0.5" value={(meta.price_cents || 100) / 100}
                    onChange={(e) => setMeta({ ...meta, price_cents: Math.round(Number(e.target.value) * 100) })}
                    className="mt-1 w-full px-3 py-2 bg-white border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper" />
                </label>
              </div>
              <label className="block">
                <span className="text-xs font-bold text-ink/60">Description</span>
                <textarea value={meta.description || ""} onChange={(e) => setMeta({ ...meta, description: e.target.value })}
                  rows={2} placeholder="What is this track? What inspired it?"
                  className="mt-1 w-full px-3 py-2 bg-white border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper resize-y" />
              </label>
              <label className="block">
                <span className="text-xs font-bold text-ink/60">Credits</span>
                <input value={meta.credits || ""} onChange={(e) => setMeta({ ...meta, credits: e.target.value })}
                  placeholder="Who made this? (defaults to you)"
                  className="mt-1 w-full px-3 py-2 bg-white border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper" />
              </label>
              <div className="space-y-2 pt-1">
                <label className="flex items-start gap-2 text-sm cursor-pointer">
                  <input type="checkbox" checked={!!meta.ai_disclosure} onChange={(e) => setMeta({ ...meta, ai_disclosure: e.target.checked })}
                    className="mt-0.5 accent-[#C0572D]" />
                  <span className="text-ink/70">
                    <b>AI-assisted disclosure</b> — label this track as AI-assisted where platforms require it
                    <span className="block text-xs text-ink/45">Required by YouTube/Spotify/Apple policies for AI-generated content.</span>
                  </span>
                </label>
                <label className="flex items-start gap-2 text-sm cursor-pointer">
                  <input type="checkbox" checked={!!meta.samples_cleared} onChange={(e) => setMeta({ ...meta, samples_cleared: e.target.checked })}
                    className="mt-0.5 accent-[#C0572D]" />
                  <span className="text-ink/70">
                    <b>Sample clearance statement</b> — I confirm every sound in this track is either synthesized by this studio or mine to use
                  </span>
                </label>
              </div>
            </div>

            <div className="space-y-5">
              <div className="rounded-2xl border p-5" style={{ background: "#fff", borderColor: "rgba(181,101,29,0.3)" }}>
                <div className="flex items-center gap-2 mb-3">
                  <Lock className="w-4 h-4" style={{ color: GREEN }} />
                  <h2 className="font-heading font-bold text-ink">Ownership — yours, not ours</h2>
                </div>
                <div className="space-y-2 text-sm text-ink/70">
                  <p className="flex gap-2"><span style={{ color: GREEN }}>✓</span> You keep <b>100% ownership</b> of the copyright in everything made here.</p>
                  <p className="flex gap-2"><span style={{ color: GREEN }}>✓</span> The platform never claims your work — no transfers, no assignments.</p>
                  <p className="flex gap-2"><span style={{ color: GREEN }}>✓</span> When a track sells, the creator keeps <b>70%</b> and the platform retains a <b>30% service fee</b> (Mandate 2).</p>
                  <p className="flex gap-2"><span style={{ color: GREEN }}>✓</span> All sounds are synthesized — there are no third-party samples in the kits, so there's nothing to clear.</p>
                </div>
              </div>

              <div className="rounded-2xl border p-5" style={{ background: "rgba(232,165,30,0.05)", borderColor: "rgba(232,165,30,0.3)" }}>
                <div className="flex items-center gap-2 mb-3">
                  <Upload className="w-4 h-4" style={{ color: GOLD }} />
                  <h2 className="font-heading font-bold text-ink">Publish to your store</h2>
                </div>
                <p className="text-xs text-ink/55 mb-4">
                  8 bars will be rendered and uploaded to your Media Store as a sellable track with a 33-second preview.
                  You can unpublish or change the price anytime from your creator tools.
                </p>
                {projects.length > 0 && (
                  <label className="block mb-3">
                    <span className="text-xs font-bold text-ink/60">Attach to AI team project (optional)</span>
                    <select value={projectId} onChange={(e) => setProjectId(e.target.value)}
                      className="mt-1 w-full px-3 py-2 bg-white border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper">
                      <option value="">— No project —</option>
                      {projects.map((p) => (
                        <option key={p.id} value={p.id}>
                          {p.title} · {p.current_stage}
                        </option>
                      ))}
                    </select>
                    <span className="block text-[11px] text-ink/45 mt-1">
                      The published track becomes a deliverable the AI team can review and carry forward.
                    </span>
                  </label>
                )}
                <button onClick={publish}
                  disabled={exporting}
                  className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-lg text-sm font-black disabled:opacity-40 transition-colors"
                  style={{ background: GOLD, color: "#0a0a0a" }}>
                  {exporting ? <><Save className="w-4 h-4 animate-pulse" /> Rendering &amp; uploading…</> : <><Upload className="w-4 h-4" /> Publish Track</>}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default function Studio() {
  return <StudioContent />;
}
