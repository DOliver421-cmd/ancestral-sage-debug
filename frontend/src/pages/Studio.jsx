/**
 * Studio — Ghost Producer Studio (v2).
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
 *     Mandate 2) and never claims copyright.
 *   • AI-disclosure is a first-class metadata field (required by modern
 *     platforms), and the publish flow records sample-clearance attestation.
 *
 * Engine: Web Audio API only — no audio libraries, no external requests.
 * Export: OfflineAudioContext render → 16-bit PCM WAV (open format).
 *
 * v2: 12 instruments, song arrangement with named sections, full-track export.
 */

import { useRef, useState, useCallback, useEffect } from "react";
import AppShell from "../components/AppShell";
import { useAuth } from "../lib/auth";
import { api } from "../lib/api";
import { toast } from "sonner";
import PageBack from "../components/PageBack";
import {
  Play, Square, Download, Save, Upload, Music2, SlidersHorizontal,
  Sparkles, Lock, FileText, Headphones,
} from "lucide-react";

const COPPER = "#0e7490";
const GOLD = "#E8A51E";
const GREEN = "#1B4332";
const INK = "#1c1917";
const BONE = "#ffffff";

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

// ── 12 Instruments ──────────────────────────────────────────────────────────
const DRUM_TRACKS = [
  { id: "kick",    label: "Kick",    color: "#db2777" },
  { id: "snare",   label: "Snare",   color: "#0e7490" },
  { id: "hat",     label: "Hat",     color: "#0e7490" },
  { id: "perc",    label: "Perc",    color: "#6d28d9" },
  { id: "clap",    label: "Clap",    color: "#c2410c" },
  { id: "rim",     label: "Rim",     color: "#ca8a04" },
  { id: "openHat", label: "Open Hat", color: "#059669" },
  { id: "shaker",  label: "Shaker",  color: "#be185d" },
  { id: "crash",   label: "Crash",   color: "#d97706" },
  { id: "ride",    label: "Ride",    color: "#2563eb" },
  { id: "cowbell", label: "Cowbell", color: "#7c3aed" },
  { id: "tom",     label: "Tom",     color: "#dc2626" },
];

// ── Song sections ────────────────────────────────────────────────────────────
const SECTION_DEFS = [
  { id: "intro",    label: "Intro",    icon: "🌅", defaultBars: 4 },
  { id: "verse",    label: "Verse",    icon: "🎤", defaultBars: 8 },
  { id: "chorus",   label: "Chorus",   icon: "🔥", defaultBars: 8 },
  { id: "bridge",   label: "Bridge",   icon: "🌊", defaultBars: 4 },
  { id: "outro",    label: "Outro",    icon: "🌙", defaultBars: 4 },
];

const DEFAULT_ARRANGEMENT = ["intro", "verse", "chorus", "verse", "chorus", "bridge", "chorus", "outro"];

function makeEmptyPatterns(kits, drumTracks, steps) {
  const init = {};
  for (const k of Object.keys(kits)) {
    init[k] = {};
    for (const t of drumTracks) {
      init[k][t.id] = [Array(steps).fill(false), Array(steps).fill(false)];
    }
  }
  return init;
}

function makeEmptyKeys(kits, rows, steps) {
  const init = {};
  for (const k of Object.keys(kits)) {
    init[k] = Array.from({ length: rows }, () => Array(steps).fill(false));
  }
  return init;
}

function makeDefaultDrumPatterns(kits) {
  const init = {};
  for (const k of Object.keys(kits)) {
    init[k] = {};
    // Original 4 tracks get the kit's built-in defaults
    for (const tId of ["kick", "snare", "hat", "perc"]) {
      init[k][tId] = [kits[k].drums[tId].slice(), kits[k].drums[tId].slice()];
    }
    // New tracks start empty
    for (const t of DRUM_TRACKS) {
      if (!init[k][t.id]) {
        init[k][t.id] = [Array(STEPS).fill(false), Array(STEPS).fill(false)];
      }
    }
  }
  return init;
}

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

const KEY_ROWS = 5;

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
  const bp = ctx.createBiquadFilter(); bp.type = "bandpass"; bp.frequency.value = 1800; bp.Q.value = 0.8;
  const g = ctx.createGain(); g.gain.setValueAtTime(gain, t0); g.gain.exponentialRampToValueAtTime(0.001, t0 + 0.2);
  const tone = ctx.createOscillator(); tone.type = "triangle"; tone.frequency.setValueAtTime(190, t0);
  const tg = ctx.createGain(); tg.gain.setValueAtTime(gain * 0.5, t0); tg.gain.exponentialRampToValueAtTime(0.001, t0 + 0.12);
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
  const hp = ctx.createBiquadFilter(); hp.type = "highpass"; hp.frequency.value = 7000;
  const g = ctx.createGain(); g.gain.setValueAtTime(gain, t0); g.gain.exponentialRampToValueAtTime(0.001, t0 + dur);
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
  const bp = ctx.createBiquadFilter(); bp.type = "bandpass"; bp.frequency.value = 900; bp.Q.value = 2;
  const g = ctx.createGain(); g.gain.setValueAtTime(gain, t0); g.gain.exponentialRampToValueAtTime(0.001, t0 + 0.12);
  const tick = ctx.createOscillator(); tick.type = "sine"; tick.frequency.setValueAtTime(660, t0);
  const tg = ctx.createGain(); tg.gain.setValueAtTime(gain * 0.6, t0); tg.gain.exponentialRampToValueAtTime(0.001, t0 + 0.08);
  noise.connect(bp).connect(g).connect(ctx.destination);
  tick.connect(tg).connect(ctx.destination);
  noise.start(t0); noise.stop(t0 + 0.16);
  tick.start(t0); tick.stop(t0 + 0.1);
}

// ── New instrument synthesis ─────────────────────────────────────────────────
function playClap(ctx, t, gain, swingShift) {
  const t0 = t + swingShift;
  for (let i = 0; i < 3; i++) {
    const noise = ctx.createBufferSource();
    const buf = ctx.createBuffer(1, ctx.sampleRate * 0.04, ctx.sampleRate);
    const d = buf.getChannelData(0);
    for (let j = 0; j < d.length; j++) d[j] = (Math.random() * 2 - 1) * (1 - j / d.length);
    noise.buffer = buf;
    const bp = ctx.createBiquadFilter(); bp.type = "bandpass"; bp.frequency.value = 2500; bp.Q.value = 1.2;
    const g = ctx.createGain(); g.gain.setValueAtTime(gain * 0.8, t0 + i * 0.008); g.gain.exponentialRampToValueAtTime(0.001, t0 + i * 0.008 + 0.08);
    noise.connect(bp).connect(g).connect(ctx.destination);
    noise.start(t0 + i * 0.008); noise.stop(t0 + i * 0.008 + 0.09);
  }
  const env = ctx.createBufferSource();
  const ebuf = ctx.createBuffer(1, ctx.sampleRate * 0.15, ctx.sampleRate);
  const ed = ebuf.getChannelData(0);
  for (let i = 0; i < ed.length; i++) ed[i] = (Math.random() * 2 - 1) * Math.exp(-i / (ctx.sampleRate * 0.04));
  env.buffer = ebuf;
  const bp2 = ctx.createBiquadFilter(); bp2.type = "bandpass"; bp2.frequency.value = 3500; bp2.Q.value = 0.7;
  const g2 = ctx.createGain(); g2.gain.setValueAtTime(gain * 0.6, t0 + 0.02); g2.gain.exponentialRampToValueAtTime(0.001, t0 + 0.15);
  env.connect(bp2).connect(g2).connect(ctx.destination);
  env.start(t0 + 0.02); env.stop(t0 + 0.16);
}

function playRim(ctx, t, gain, swingShift) {
  const t0 = t + swingShift;
  const o = ctx.createOscillator(); o.type = "triangle";
  o.frequency.setValueAtTime(800, t0);
  o.frequency.exponentialRampToValueAtTime(400, t0 + 0.03);
  const g = ctx.createGain(); g.gain.setValueAtTime(gain, t0); g.gain.exponentialRampToValueAtTime(0.001, t0 + 0.06);
  o.connect(g).connect(ctx.destination);
  o.start(t0); o.stop(t0 + 0.07);
  const o2 = ctx.createOscillator(); o2.type = "sine";
  o2.frequency.setValueAtTime(1200, t0);
  const g2 = ctx.createGain(); g2.gain.setValueAtTime(gain * 0.3, t0); g2.gain.exponentialRampToValueAtTime(0.001, t0 + 0.02);
  o2.connect(g2).connect(ctx.destination);
  o2.start(t0); o2.stop(t0 + 0.03);
}

function playOpenHatFn(ctx, t, gain, swingShift) {
  playHat(ctx, t, gain, swingShift, true);
}

function playShaker(ctx, t, gain, swingShift) {
  const t0 = t + swingShift;
  const noise = ctx.createBufferSource();
  const buf = ctx.createBuffer(1, ctx.sampleRate * 0.08, ctx.sampleRate);
  const d = buf.getChannelData(0);
  for (let i = 0; i < d.length; i++) d[i] = (Math.random() * 2 - 1) * (1 - i / d.length) * 0.6;
  noise.buffer = buf;
  const hp = ctx.createBiquadFilter(); hp.type = "highpass"; hp.frequency.value = 5000;
  const bp = ctx.createBiquadFilter(); bp.type = "bandpass"; bp.frequency.value = 8000; bp.Q.value = 1.5;
  const g = ctx.createGain(); g.gain.setValueAtTime(gain * 0.5, t0); g.gain.exponentialRampToValueAtTime(0.001, t0 + 0.07);
  noise.connect(hp).connect(bp).connect(g).connect(ctx.destination);
  noise.start(t0); noise.stop(t0 + 0.09);
}

function playCrash(ctx, t, gain, swingShift) {
  const t0 = t + swingShift;
  const noise = ctx.createBufferSource();
  const buf = ctx.createBuffer(1, ctx.sampleRate * 0.6, ctx.sampleRate);
  const d = buf.getChannelData(0);
  for (let i = 0; i < d.length; i++) d[i] = (Math.random() * 2 - 1) * Math.exp(-i / (ctx.sampleRate * 0.18));
  noise.buffer = buf;
  const bp = ctx.createBiquadFilter(); bp.type = "highpass"; bp.frequency.value = 5000;
  const g = ctx.createGain(); g.gain.setValueAtTime(gain * 0.7, t0); g.gain.exponentialRampToValueAtTime(0.001, t0 + 0.55);
  noise.connect(bp).connect(g).connect(ctx.destination);
  noise.start(t0); noise.stop(t0 + 0.6);
}

function playRide(ctx, t, gain, swingShift) {
  const t0 = t + swingShift;
  const noise = ctx.createBufferSource();
  const buf = ctx.createBuffer(1, ctx.sampleRate * 0.35, ctx.sampleRate);
  const d = buf.getChannelData(0);
  for (let i = 0; i < d.length; i++) d[i] = (Math.random() * 2 - 1) * Math.exp(-i / (ctx.sampleRate * 0.12)) * 0.5;
  noise.buffer = buf;
  const hp = ctx.createBiquadFilter(); hp.type = "highpass"; hp.frequency.value = 6000;
  const g = ctx.createGain(); g.gain.setValueAtTime(gain * 0.4, t0); g.gain.exponentialRampToValueAtTime(0.001, t0 + 0.3);
  noise.connect(hp).connect(g).connect(ctx.destination);
  noise.start(t0); noise.stop(t0 + 0.36);
  const bell = ctx.createOscillator(); bell.type = "sine"; bell.frequency.setValueAtTime(8000, t0);
  const bg = ctx.createGain(); bg.gain.setValueAtTime(gain * 0.15, t0); bg.gain.exponentialRampToValueAtTime(0.001, t0 + 0.2);
  bell.connect(bg).connect(ctx.destination);
  bell.start(t0); bell.stop(t0 + 0.22);
}

function playCowbell(ctx, t, gain, swingShift) {
  const t0 = t + swingShift;
  const o1 = ctx.createOscillator(); o1.type = "square"; o1.frequency.setValueAtTime(800, t0);
  const o2 = ctx.createOscillator(); o2.type = "square"; o2.frequency.setValueAtTime(540, t0);
  const g = ctx.createGain(); g.gain.setValueAtTime(gain * 0.3, t0); g.gain.exponentialRampToValueAtTime(0.001, t0 + 0.12);
  const bp = ctx.createBiquadFilter(); bp.type = "bandpass"; bp.frequency.value = 800; bp.Q.value = 3;
  o1.connect(bp); o2.connect(bp); bp.connect(g).connect(ctx.destination);
  o1.start(t0); o1.stop(t0 + 0.13);
  o2.start(t0); o2.stop(t0 + 0.13);
}

function playTom(ctx, t, gain, swingShift) {
  const t0 = t + swingShift;
  const o = ctx.createOscillator(); o.type = "sine";
  o.frequency.setValueAtTime(200, t0);
  o.frequency.exponentialRampToValueAtTime(80, t0 + 0.15);
  const g = ctx.createGain(); g.gain.setValueAtTime(gain * 0.8, t0); g.gain.exponentialRampToValueAtTime(0.001, t0 + 0.25);
  o.connect(g).connect(ctx.destination);
  o.start(t0); o.stop(t0 + 0.26);
  const o2 = ctx.createOscillator(); o2.type = "triangle";
  o2.frequency.setValueAtTime(240, t0);
  o2.frequency.exponentialRampToValueAtTime(90, t0 + 0.12);
  const g2 = ctx.createGain(); g2.gain.setValueAtTime(gain * 0.4, t0); g2.gain.exponentialRampToValueAtTime(0.001, t0 + 0.18);
  o2.connect(g2).connect(ctx.destination);
  o2.start(t0); o2.stop(t0 + 0.19);
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
  else if (id === "perc") playPerc(ctx, t, gain, swingShift);
  else if (id === "clap") playClap(ctx, t, gain, swingShift);
  else if (id === "rim") playRim(ctx, t, gain, swingShift);
  else if (id === "openHat") playOpenHatFn(ctx, t, gain, swingShift);
  else if (id === "shaker") playShaker(ctx, t, gain, swingShift);
  else if (id === "crash") playCrash(ctx, t, gain, swingShift);
  else if (id === "ride") playRide(ctx, t, gain, swingShift);
  else if (id === "cowbell") playCowbell(ctx, t, gain, swingShift);
  else if (id === "tom") playTom(ctx, t, gain, swingShift);
}

// ── Offline synth (mirrors drumAt for OfflineAudioContext) ───────────────────
function offlineDrumAt(id, off, dest, t, gain, shift) {
  if (id === "kick") {
    const o = off.createOscillator(), g = off.createGain();
    o.type = "sine";
    o.frequency.setValueAtTime(150, t + shift); o.frequency.exponentialRampToValueAtTime(48, t + shift + 0.12);
    g.gain.setValueAtTime(gain, t + shift); g.gain.exponentialRampToValueAtTime(0.001, t + shift + 0.28);
    o.connect(g).connect(dest); o.start(t + shift); o.stop(t + shift + 0.3);
  } else if (id === "snare") {
    const buf = off.createBuffer(1, off.sampleRate * 0.22, off.sampleRate);
    const d = buf.getChannelData(0); for (let i = 0; i < d.length; i++) d[i] = (Math.random() * 2 - 1) * (1 - i / d.length);
    const n = off.createBufferSource(); n.buffer = buf;
    const bp = off.createBiquadFilter(); bp.type = "bandpass"; bp.frequency.value = 1800; bp.Q.value = 0.8;
    const g = off.createGain(); g.gain.setValueAtTime(gain, t + shift); g.gain.exponentialRampToValueAtTime(0.001, t + shift + 0.2);
    const tone = off.createOscillator(); tone.type = "triangle"; tone.frequency.setValueAtTime(190, t + shift);
    const tg = off.createGain(); tg.gain.setValueAtTime(gain * 0.5, t + shift); tg.gain.exponentialRampToValueAtTime(0.001, t + shift + 0.12);
    n.connect(bp).connect(g).connect(dest); tone.connect(tg).connect(dest);
    n.start(t + shift); n.stop(t + shift + 0.24); tone.start(t + shift); tone.stop(t + shift + 0.14);
  } else if (id === "hat" || id === "openHat") {
    const isOpen = id === "openHat"; const dur = isOpen ? 0.25 : 0.06;
    const buf = off.createBuffer(1, off.sampleRate * dur, off.sampleRate);
    const d = buf.getChannelData(0); for (let i = 0; i < d.length; i++) d[i] = (Math.random() * 2 - 1) * (1 - i / d.length);
    const n = off.createBufferSource(); n.buffer = buf;
    const hp = off.createBiquadFilter(); hp.type = "highpass"; hp.frequency.value = 7000;
    const g = off.createGain(); g.gain.setValueAtTime(gain, t + shift); g.gain.exponentialRampToValueAtTime(0.001, t + shift + dur);
    n.connect(hp).connect(g).connect(dest); n.start(t + shift); n.stop(t + shift + dur + 0.01);
  } else if (id === "clap") {
    for (let i = 0; i < 3; i++) {
      const buf = off.createBuffer(1, off.sampleRate * 0.04, off.sampleRate);
      const d = buf.getChannelData(0); for (let j = 0; j < d.length; j++) d[j] = (Math.random() * 2 - 1) * (1 - j / d.length);
      const n = off.createBufferSource(); n.buffer = buf;
      const bp = off.createBiquadFilter(); bp.type = "bandpass"; bp.frequency.value = 2500; bp.Q.value = 1.2;
      const g = off.createGain(); g.gain.setValueAtTime(gain * 0.8, t + shift + i * 0.008); g.gain.exponentialRampToValueAtTime(0.001, t + shift + i * 0.008 + 0.08);
      n.connect(bp).connect(g).connect(dest); n.start(t + shift + i * 0.008); n.stop(t + shift + i * 0.008 + 0.09);
    }
  } else if (id === "rim") {
    const o = off.createOscillator(); o.type = "triangle"; o.frequency.setValueAtTime(800, t + shift); o.frequency.exponentialRampToValueAtTime(400, t + shift + 0.03);
    const g = off.createGain(); g.gain.setValueAtTime(gain, t + shift); g.gain.exponentialRampToValueAtTime(0.001, t + shift + 0.06);
    o.connect(g).connect(dest); o.start(t + shift); o.stop(t + shift + 0.07);
  } else if (id === "shaker") {
    const buf = off.createBuffer(1, off.sampleRate * 0.08, off.sampleRate);
    const d = buf.getChannelData(0); for (let i = 0; i < d.length; i++) d[i] = (Math.random() * 2 - 1) * (1 - i / d.length) * 0.6;
    const n = off.createBufferSource(); n.buffer = buf;
    const hp = off.createBiquadFilter(); hp.type = "highpass"; hp.frequency.value = 5000;
    const g = off.createGain(); g.gain.setValueAtTime(gain * 0.5, t + shift); g.gain.exponentialRampToValueAtTime(0.001, t + shift + 0.07);
    n.connect(hp).connect(g).connect(dest); n.start(t + shift); n.stop(t + shift + 0.09);
  } else if (id === "crash") {
    const buf = off.createBuffer(1, off.sampleRate * 0.6, off.sampleRate);
    const d = buf.getChannelData(0); for (let i = 0; i < d.length; i++) d[i] = (Math.random() * 2 - 1) * Math.exp(-i / (off.sampleRate * 0.18));
    const n = off.createBufferSource(); n.buffer = buf;
    const bp = off.createBiquadFilter(); bp.type = "highpass"; bp.frequency.value = 5000;
    const g = off.createGain(); g.gain.setValueAtTime(gain * 0.7, t + shift); g.gain.exponentialRampToValueAtTime(0.001, t + shift + 0.55);
    n.connect(bp).connect(g).connect(dest); n.start(t + shift); n.stop(t + shift + 0.6);
  } else if (id === "ride") {
    const buf = off.createBuffer(1, off.sampleRate * 0.35, off.sampleRate);
    const d = buf.getChannelData(0); for (let i = 0; i < d.length; i++) d[i] = (Math.random() * 2 - 1) * Math.exp(-i / (off.sampleRate * 0.12)) * 0.5;
    const n = off.createBufferSource(); n.buffer = buf;
    const hp = off.createBiquadFilter(); hp.type = "highpass"; hp.frequency.value = 6000;
    const g = off.createGain(); g.gain.setValueAtTime(gain * 0.4, t + shift); g.gain.exponentialRampToValueAtTime(0.001, t + shift + 0.3);
    n.connect(hp).connect(g).connect(dest); n.start(t + shift); n.stop(t + shift + 0.36);
  } else if (id === "cowbell") {
    const o1 = off.createOscillator(); o1.type = "square"; o1.frequency.setValueAtTime(800, t + shift);
    const o2 = off.createOscillator(); o2.type = "square"; o2.frequency.setValueAtTime(540, t + shift);
    const g = off.createGain(); g.gain.setValueAtTime(gain * 0.3, t + shift); g.gain.exponentialRampToValueAtTime(0.001, t + shift + 0.12);
    const bp = off.createBiquadFilter(); bp.type = "bandpass"; bp.frequency.value = 800; bp.Q.value = 3;
    o1.connect(bp); o2.connect(bp); bp.connect(g).connect(dest);
    o1.start(t + shift); o1.stop(t + shift + 0.13); o2.start(t + shift); o2.stop(t + shift + 0.13);
  } else if (id === "tom") {
    const o = off.createOscillator(); o.type = "sine"; o.frequency.setValueAtTime(200, t + shift); o.frequency.exponentialRampToValueAtTime(80, t + shift + 0.15);
    const g = off.createGain(); g.gain.setValueAtTime(gain * 0.8, t + shift); g.gain.exponentialRampToValueAtTime(0.001, t + shift + 0.25);
    o.connect(g).connect(dest); o.start(t + shift); o.stop(t + shift + 0.26);
  } else {
    // fallback perc
    const buf = off.createBuffer(1, off.sampleRate * 0.15, off.sampleRate);
    const d = buf.getChannelData(0); for (let i = 0; i < d.length; i++) d[i] = (Math.random() * 2 - 1) * (1 - i / d.length);
    const n = off.createBufferSource(); n.buffer = buf;
    const bp = off.createBiquadFilter(); bp.type = "bandpass"; bp.frequency.value = 900; bp.Q.value = 2;
    const g = off.createGain(); g.gain.setValueAtTime(gain, t + shift); g.gain.exponentialRampToValueAtTime(0.001, t + shift + 0.12);
    n.connect(bp).connect(g).connect(dest); n.start(t + shift); n.stop(t + shift + 0.16);
  }
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
    return ["beat", "keys", "song", "publish"].includes(requested) ? requested : "beat";
  });

  // Shared project state
  const [kitId, setKitId] = useState("boom-bap");
  const [bpm, setBpm] = useState(KITS["boom-bap"].bpm);
  const [swing, setSwing] = useState(KITS["boom-bap"].swing);
  const [root, setRoot] = useState("C");

  // Section-based patterns: sectionPatterns[sectionId][kitId][trackId][bank][step]
  const [sectionPatterns, setSectionPatterns] = useState(() => {
    const sp = {};
    for (const sec of SECTION_DEFS) {
      sp[sec.id] = makeDefaultDrumPatterns(KITS);
    }
    return sp;
  });

  // Legacy patterns (kept for backwards compat, synced from active section)
  const [patterns, setPatterns] = useState(() => makeDefaultDrumPatterns(KITS));
  const [bank, setBank] = useState(0);
  const [keys, setKeys] = useState(() => makeEmptyKeys(KITS, KEY_ROWS, STEPS));

  // Section keys: sectionKeys[sectionId][kitId][row][step]
  const [sectionKeys, setSectionKeys] = useState(() => {
    const sk = {};
    for (const sec of SECTION_DEFS) sk[sec.id] = makeEmptyKeys(KITS, KEY_ROWS, STEPS);
    return sk;
  });

  // Arrangement state
  const [activeSection, setActiveSection] = useState("intro");
  const [arrangement, setArrangement] = useState([...DEFAULT_ARRANGEMENT]);
  const [sectionBars, setSectionBars] = useState(() => {
    const sb = {};
    for (const sec of SECTION_DEFS) sb[sec.id] = sec.defaultBars;
    return sb;
  });
  const [isPlayingSong, setIsPlayingSong] = useState(false);
  const [arrangeMode, setArrangeMode] = useState(false);

  const [muted, setMuted] = useState(() => {
    const m = {};
    for (const t of DRUM_TRACKS) m[t.id] = false;
    m.keys = false;
    return m;
  });
  const [playing, setPlaying] = useState(false);
  const [step, setStep] = useState(-1);
  const [exporting, setExporting] = useState(false);

  // Publish metadata
  const [meta, setMeta] = useState(() => {
    try { return JSON.parse(localStorage.getItem("ghost_studio_meta") || "null") || {}; } catch { return {}; }
  });

  const [projects, setProjects] = useState([]);
  const [projectId, setProjectId] = useState("");

  useEffect(() => {
    api.get("/my-projects")
      .then((r) => setProjects(r.data?.projects || []))
      .catch(() => {});
  }, []);

  const ctxRef = useRef(null);
  const timerRef = useRef(null);
  const nextTimeRef = useRef(0);
  const stepRef = useRef(0);
  const songTimerRef = useRef(null);

  const kit = KITS[kitId];
  const scale = SCALES[kit.scale];
  const stepDur = 60 / bpm / 4;

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

  // ── Sync active section → working patterns ──
  useEffect(() => {
    setPatterns(sectionPatterns[activeSection]?.[kitId] || makeDefaultDrumPatterns(KITS));
    setKeys(sectionKeys[activeSection]?.[kitId] || makeEmptyKeys(KITS, KEY_ROWS, STEPS));
  }, [activeSection, kitId]);

  const saveSection = useCallback((secId, pat, k) => {
    setSectionPatterns((prev) => ({ ...prev, [secId]: { ...prev[secId], [k]: pat } }));
  }, []);

  const saveSectionKeys = useCallback((secId, k, kKeys) => {
    setSectionKeys((prev) => ({ ...prev, [secId]: { ...prev[secId], [k]: kKeys } }));
  }, []);

  // Auto-save on change
  useEffect(() => {
    saveSection(activeSection, patterns, kitId);
  }, [patterns, activeSection, kitId, saveSection]);

  useEffect(() => {
    saveSectionKeys(activeSection, kitId, keys);
  }, [keys, activeSection, kitId, saveSectionKeys]);

  // ── Scheduler ──
  const scheduleStep = useCallback((ctx, s, when, overridePat, overrideKeys) => {
    const sw = swing * stepDur;
    const shift = (s % 2 === 1) ? sw : 0;
    const pat = overridePat || patterns[kitId];
    DRUM_TRACKS.forEach((t) => {
      if (muted[t.id]) return;
      const stepOn = pat[t.id] ? pat[t.id][bank]?.[s] : false;
      if (stepOn) drumAt(t.id, ctx, when, 0.9, shift);
    });
    if (!muted.keys) {
      const kp = overrideKeys || keys[kitId];
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
    if (songTimerRef.current) { clearTimeout(songTimerRef.current); songTimerRef.current = null; }
    setPlaying(false);
    setIsPlayingSong(false);
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

  // ── Full song playback (arrangement) ──
  const playSong = useCallback(() => {
    const ctx = ensureCtx();
    stop();
    setIsPlayingSong(true);
    setPlaying(true);
    let globalStep = 0;
    const totalSteps = arrangement.reduce((sum, secId) => sum + (sectionBars[secId] || 4) * STEPS, 0);
    nextTimeRef.current = ctx.currentTime + 0.06;
    timerRef.current = setInterval(() => {
      const ahead = 0.15;
      while (nextTimeRef.current < ctx.currentTime + ahead && globalStep < totalSteps) {
        // Determine which section and local step
        let stepsSoFar = 0;
        let secId = arrangement[0];
        let localStep = 0;
        for (const s of arrangement) {
          const secLen = (sectionBars[s] || 4) * STEPS;
          if (globalStep < stepsSoFar + secLen) {
            secId = s;
            localStep = globalStep - stepsSoFar;
            break;
          }
          stepsSoFar += secLen;
        }
        const pat = sectionPatterns[secId]?.[kitId];
        const kKeys = sectionKeys[secId]?.[kitId];
        const overridePat = pat || undefined;
        const overrideKeys = kKeys || undefined;
        const sInBar = localStep % STEPS;
        const sw = swing * stepDur;
        const shift = (sInBar % 2 === 1) ? sw : 0;
        DRUM_TRACKS.forEach((t) => {
          if (muted[t.id]) return;
          const stepOn = overridePat?.[t.id]?.[bank]?.[sInBar];
          if (stepOn) drumAt(t.id, ctx, nextTimeRef.current, 0.9, shift);
        });
        if (!muted.keys) {
          const kp = overrideKeys || keys[kitId];
          kp.forEach((row, r) => {
            if (!row[sInBar]) return;
            const degree = Math.min(r, scale.offsets.length - 1);
            const note = ROOT_MIDI[root] + 12 + scale.offsets[degree];
            playNote(ctx, nextTimeRef.current, midiToFreq(note), stepDur * 3.5, 0.16, "triangle");
          });
        }
        setStep(sInBar);
        nextTimeRef.current += stepDur;
        globalStep++;
      }
      if (globalStep >= totalSteps) {
        stop();
      }
    }, 25);
  }, [ensureCtx, stop, arrangement, sectionBars, sectionPatterns, sectionKeys, kitId, bank, muted, swing, stepDur, root, scale, keys]);

  useEffect(() => () => stop(), [stop]);

  // ── Export WAV (offline render) ────────────────────────────────────────────
  const exportWav = useCallback(async (bars = 8, download = true, useArrangement = false) => {
    setExporting(true);
    try {
      const AC = window.AudioContext || window.webkitAudioContext;
      const sr = 44100;
      let totalBars = bars;
      let totalSteps;
      if (useArrangement && arrangement.length > 0) {
        totalSteps = arrangement.reduce((sum, secId) => sum + (sectionBars[secId] || 4) * STEPS, 0);
      } else {
        totalSteps = bars * STEPS;
      }
      const total = totalSteps * stepDur;
      const off = new OfflineAudioContext(2, Math.ceil(sr * total), sr);
      const origDest = off.destination;
      let t = 0;
      for (let stepIdx = 0; stepIdx < totalSteps; stepIdx++) {
        // Determine section and local step
        let secId = arrangement[0];
        let localStep = stepIdx;
        if (useArrangement && arrangement.length > 0) {
          let stepsSoFar = 0;
          for (const s of arrangement) {
            const secLen = (sectionBars[s] || 4) * STEPS;
            if (stepIdx < stepsSoFar + secLen) {
              secId = s;
              localStep = stepIdx - stepsSoFar;
              break;
            }
            stepsSoFar += secLen;
          }
        }
        const sw = swing * stepDur;
        const shift = (localStep % 2 === 1) ? sw : 0;
        const pat = useArrangement ? (sectionPatterns[secId]?.[kitId] || patterns[kitId]) : patterns[kitId];
        DRUM_TRACKS.forEach((trk) => {
          if (muted[trk.id]) return;
          const stepOn = pat[trk.id]?.[bank]?.[localStep];
          if (stepOn) offlineDrumAt(trk.id, off, origDest, t, 0.9, shift);
        });
        if (!muted.keys) {
          const kp = useArrangement ? (sectionKeys[secId]?.[kitId] || keys[kitId]) : keys[kitId];
          kp.forEach((row, r) => {
            if (!row[localStep]) return;
            const degree = Math.min(r, scale.offsets.length - 1);
            const note = ROOT_MIDI[root] + 12 + scale.offsets[degree];
            const o = off.createOscillator(), g = off.createGain(), lp = off.createBiquadFilter();
            lp.type = "lowpass"; lp.frequency.value = Math.min(3200, midiToFreq(note) * 6); lp.Q.value = 0.7;
            o.type = "triangle"; o.frequency.setValueAtTime(midiToFreq(note), t);
            g.gain.setValueAtTime(0.0001, t);
            g.gain.exponentialRampToValueAtTime(0.16, t + 0.012);
            g.gain.exponentialRampToValueAtTime(0.001, t + stepDur * 3.5);
            o.connect(lp).connect(g).connect(origDest);
            o.start(t); o.stop(t + stepDur * 3.5 + 0.02);
          });
        }
        t += stepDur;
      }
      const rendered = await off.startRendering();
      const wav = encodeWav(rendered, sr);
      const blob = new Blob([wav], { type: "audio/wav" });
      if (download) {
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `${(meta.title || "ghost-studio-track").replace(/[^\w-]+/g, "-").toLowerCase() || "track"}.wav`;
        a.click();
        setTimeout(() => URL.revokeObjectURL(url), 5000);
        toast.success("WAV exported — you own it 100%.");
      }
      return blob;
    } catch (e) {
      toast.error("Export failed: " + (e?.message || e));
      return null;
    } finally {
      setExporting(false);
    }
  }, [kitId, patterns, keys, bank, muted, swing, stepDur, root, scale, meta.title, arrangement, sectionBars, sectionPatterns, sectionKeys]);

  // Preview
  const [previewUrl, setPreviewUrl] = useState(null);
  const [previewDur, setPreviewDur] = useState(null);
  const [previewing, setPreviewing] = useState(false);
  const [previewErr, setPreviewErr] = useState("");

  const generatePreview = useCallback(async () => {
    setPreviewing(true); setPreviewErr("");
    try {
      const useArr = arrangement.length > 1;
      const blob = await exportWav(useArr ? undefined : 8, false, useArr);
      if (!blob) { setPreviewErr("Preview render failed."); return; }
      if (previewUrl) URL.revokeObjectURL(previewUrl);
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      const dur = await new Promise((res) => {
        audio.addEventListener("loadedmetadata", () => res(audio.duration || 30), { once: true });
        setTimeout(() => res(30), 4000);
      });
      setPreviewUrl(url); setPreviewDur(Math.round(dur));
      toast.success("Preview ready — hear it before you publish.");
    } catch (e) { setPreviewErr("Preview failed: " + (e?.message || e)); }
    finally { setPreviewing(false); }
  }, [exportWav, previewUrl, arrangement]);

  // Publish
  const publish = useCallback(async () => {
    if (!meta.title?.trim()) { toast.error("Give the track a title first."); setTab("publish"); return; }
    if (!meta.samples_cleared) { toast.error("Confirm the sample-clearance statement."); setTab("publish"); return; }
    setExporting(true);
    try {
      const useArr = arrangement.length > 1;
      const blob = await exportWav(useArr ? undefined : 8, false, useArr);
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
      if (projectId) {
        try {
          const proj = await api.get(`/my-projects/${projectId}`).then((r) => r.data?.project || r.data).catch(() => null);
          await api.post(`/my-projects/${projectId}/deliverables`, {
            stage: proj?.current_stage || "execute",
            persona: "Ghost Producer Studio",
            title: `${meta.title} (published track)`,
            content_type: "audio",
            content: `Released through the Ghost Producer Studio — ${meta.genre || kit.label}, ${bpm} BPM, ${root}.`,
            file_refs: [fileUrl],
            metadata: { bpm, root, kit: kitId, ai_disclosure: !!meta.ai_disclosure, product_id: product.data?.id },
          });
          toast.success("Track attached to the AI team project.");
        } catch { /* best-effort */ }
      }
      toast.success("Published to your store — 70% of sales is yours.");
      setMeta((m) => ({ ...m, last_product_id: product.data?.id }));
    } catch (e) { toast.error("Publish failed: " + (e?.response?.data?.detail || e?.message || e)); }
    finally { setExporting(false); }
  }, [meta, exportWav, kitId, kit, bpm, root, projectId, arrangement]);

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

  // Arrangement helpers
  const addSection = (secId) => setArrangement((a) => [...a, secId]);
  const removeSection = (idx) => setArrangement((a) => a.filter((_, i) => i !== idx));
  const moveSection = (from, to) => {
    setArrangement((a) => {
      const next = [...a];
      const [item] = next.splice(from, 1);
      next.splice(to, 0, item);
      return next;
    });
  };
  const duplicateSection = (idx) => {
    setArrangement((a) => {
      const next = [...a];
      next.splice(idx + 1, 0, a[idx]);
      return next;
    });
  };

  const title = meta.title || "Untitled";

  return (
    <div className={embedded ? "h-full overflow-y-auto bg-[#ffffff]" : "bg-[#ffffff]"} style={embedded ? {} : { minHeight: "100vh" }}>
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8">
        {!embedded && <div className="mb-4"><PageBack to="/studio" label="Studio" /></div>}
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
            12 instruments. Full song arrangement. Every sound synthesized live — no samples, no licensing debt.
            You keep 100% ownership of what you make.
          </p>
        </div>

        {/* ── Tabs ── */}
        <div className="flex gap-1 border-b border-stone-300 mb-6 overflow-x-auto">
          {[
            { id: "beat", label: "Beat (12 Instruments)", icon: Music2 },
            { id: "keys", label: "Keys", icon: SlidersHorizontal },
            { id: "song", label: "Song Arrangement", icon: Sparkles },
            { id: "publish", label: "Publish", icon: Upload },
          ].map((t) => {
            const Icon = t.icon;
            return (
              <button key={t.id} onClick={() => setTab(t.id)}
                className={`flex items-center gap-1.5 px-4 py-2.5 text-sm font-bold border-b-2 whitespace-nowrap transition-colors ${
                  tab === t.id ? "border-cyan-700 text-cyan-700" : "border-transparent text-stone-500 hover:text-stone-800"
                }`}>
                <Icon className="w-4 h-4" /> {t.label}
              </button>
            );
          })}
        </div>

        {/* ── Transport ── */}
        <div className="flex flex-wrap items-center gap-3 mb-6 card-flat rounded-2xl p-4 border" style={{ background: "#ffffff" }}>
          <button onClick={playing ? stop : play}
            className="w-11 h-11 rounded-full flex items-center justify-center text-white transition-transform active:scale-95"
            style={{ background: playing ? "#B23A2E" : GREEN }}>
            {playing ? <Square className="w-4 h-4 fill-white" /> : <Play className="w-4 h-4 fill-white ml-0.5" />}
          </button>
          <label className="flex items-center gap-2 text-sm">
            <span className="text-xs font-bold text-stone-600 uppercase tracking-widest">BPM</span>
            <input type="range" min="50" max="160" value={bpm}
              onChange={(e) => setBpm(Number(e.target.value))}
              className="w-28 accent-[#0e7490]" />
            <span className="font-mono text-sm w-8">{bpm}</span>
          </label>
          <label className="flex items-center gap-2 text-sm">
            <span className="text-xs font-bold text-stone-600 uppercase tracking-widest">Swing</span>
            <input type="range" min="0" max="0.35" step="0.01" value={swing}
              onChange={(e) => setSwing(Number(e.target.value))}
              className="w-24 accent-[#0e7490]" />
            <span className="font-mono text-sm w-8">{(swing * 100).toFixed(0)}%</span>
          </label>
          <div className="flex items-center gap-1 ml-auto flex-wrap">
            {Object.entries(KITS).map(([id, k]) => (
              <button key={id} onClick={() => selectKit(id)}
                className={`text-[10px] font-black uppercase tracking-wider px-3 py-1.5 rounded-full border transition-colors ${
                  kitId === id ? "text-white" : "text-stone-600 hover:text-stone-900"
                }`}
                style={kitId === id ? { background: GREEN, borderColor: GREEN } : { borderColor: "rgba(28,25,23,0.15)" }}>
                {k.label}
              </button>
            ))}
          </div>
        </div>

        {/* ══ BEAT (12 Instruments) ══ */}
        {tab === "beat" && (
          <div className="card-flat rounded-2xl border overflow-hidden" style={{ background: "#ffffff" }}>
            {DRUM_TRACKS.map((t) => {
              const pat = patterns[kitId][t.id][bank];
              return (
                <div key={t.id} className="flex items-stretch border-b border-stone-200 last:border-0">
                  <div className="w-28 shrink-0 flex items-center gap-2 px-4 py-2 border-r border-stone-200">
                    <button onClick={() => setMuted((m) => ({ ...m, [t.id]: !m[t.id] }))}
                      title={muted[t.id] ? "Unmute" : "Mute"}
                      className={`w-7 h-7 rounded flex items-center justify-center text-[9px] font-black transition-colors ${muted[t.id] ? "bg-ink/10 text-stone-500" : "text-white"}`}
                      style={!muted[t.id] ? { background: t.color } : {}}>
                      {muted[t.id] ? "OFF" : "ON"}
                    </button>
                    <span className="text-sm font-bold text-stone-900">{t.label}</span>
                  </div>
                  <div className="flex-1 grid gap-1 p-2" style={{ gridTemplateColumns: `repeat(${STEPS}, 1fr)` }}>
                    {pat.map((on, s) => (
                      <button key={s} onClick={() => setPattern(t.id, s)}
                        className={`rounded-md transition-all ${step === s && playing ? "ring-2 ring-copper" : ""}`}
                        style={{
                          aspectRatio: "1",
                          background: on ? t.color : "#e7e0d2",
                          opacity: on ? 1 : 0.6,
                        }} />
                    ))}
                  </div>
                </div>
              );
            })}
            {/* Bank switcher */}
            <div className="flex items-center gap-2 px-4 py-3 bg-[#f1eee8]">
              {[0, 1].map((b) => (
                <button key={b} onClick={() => setBank(b)}
                  className={`px-4 py-1.5 rounded-lg text-xs font-black uppercase tracking-widest transition-colors ${
                    bank === b ? "text-white" : "text-stone-500 bg-[#ffffff] border border-stone-300"
                  }`}
                  style={bank === b ? { background: COPPER } : {}}>
                  Pattern {b === 0 ? "A" : "B"}
                </button>
              ))}
              <span className="ml-auto text-xs text-stone-500">12 instruments · 16 steps · {activeSection}</span>
            </div>
          </div>
        )}

        {/* ══ KEYS ══ */}
        {tab === "keys" && (
          <div className="space-y-5">
            <div className="card-flat rounded-2xl border p-5" style={{ background: "#ffffff" }}>
              <div className="flex flex-wrap items-center gap-3 mb-4">
                <span className="text-sm font-bold text-stone-900">Scale lane</span>
                <span className="text-xs text-stone-600">{scale.label}</span>
                <label className="flex items-center gap-2 ml-auto text-sm">
                  <span className="text-xs font-bold text-stone-600 uppercase tracking-widest">Key</span>
                  <select value={root} onChange={(e) => setRoot(e.target.value)}
                    className="px-3 py-1.5 bg-[#ffffff] border border-stone-400 rounded-lg text-sm focus:outline-none focus:border-cyan-700">
                    {ROOTS.map((r) => <option key={r} value={r}>{r}</option>)}
                  </select>
                </label>
                <button onClick={() => setMuted((m) => ({ ...m, keys: !m.keys }))}
                  className={`px-3 py-1.5 rounded-lg text-xs font-black uppercase tracking-widest ${muted.keys ? "bg-ink/10 text-stone-500" : "text-white"}`}
                  style={!muted.keys ? { background: GREEN } : {}}>
                  {muted.keys ? "Keys OFF" : "Keys ON"}
                </button>
              </div>
              <div className="flex items-stretch gap-1">
                <div className="w-28 shrink-0 flex flex-col justify-around">
                  {Array.from({ length: KEY_ROWS }).map((_, r) => {
                    const degree = Math.min(r, scale.offsets.length - 1);
                    return (
                      <div key={r} className="text-xs font-mono text-stone-600 px-2">
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
                            background: on ? "#2D6A4F" : "#e7e0d2",
                            opacity: on ? 1 : 0.6,
                          }} />
                      ))}
                    </div>
                  ))}
                </div>
              </div>
              <p className="text-xs text-stone-500 mt-3">
                Rows map to scale degrees — play the root/3rd/5th/7th/color of the selected scale in {root}.
                Each song section has its own keys pattern.
              </p>
            </div>
          </div>
        )}

        {/* ══ SONG ARRANGEMENT ══ */}
        {tab === "song" && (
          <div className="space-y-5">
            {/* Section selector */}
            <div className="card-flat rounded-2xl border p-5" style={{ background: "#ffffff" }}>
              <div className="flex flex-wrap items-center gap-3 mb-4">
                <span className="text-sm font-bold text-stone-900">Editing Section:</span>
                {SECTION_DEFS.map((sec) => (
                  <button key={sec.id} onClick={() => setActiveSection(sec.id)}
                    className={`px-4 py-2 rounded-lg text-sm font-bold transition-colors ${
                      activeSection === sec.id
                        ? "text-white"
                        : "text-stone-600 bg-[#f1eee8] border border-stone-300 hover:text-stone-900"
                    }`}
                    style={activeSection === sec.id ? { background: GREEN, border: `1px solid ${GREEN}` } : {}}>
                    {sec.icon} {sec.label}
                  </button>
                ))}
              </div>
              <div className="flex flex-wrap items-center gap-4">
                <label className="flex items-center gap-2 text-sm">
                  <span className="text-xs font-bold text-stone-600 uppercase tracking-widest">Bars in section</span>
                  <input type="number" min="1" max="32" value={sectionBars[activeSection] || 4}
                    onChange={(e) => setSectionBars((prev) => ({ ...prev, [activeSection]: Math.max(1, Math.min(32, Number(e.target.value))) }))}
                    className="w-16 px-2 py-1 bg-[#ffffff] border border-stone-400 rounded text-sm font-mono text-center focus:outline-none focus:border-cyan-700" />
                </label>
                <span className="text-xs text-stone-500">
                  {activeSection}: {sectionBars[activeSection] || 4} bars × 16 steps = {(sectionBars[activeSection] || 4) * 16} steps
                </span>
              </div>
              <p className="text-xs text-stone-500 mt-3">
                Edit the beat and keys for this section. Each section is an independent pattern.
                Then chain them in the arrangement below to build your full track.
              </p>
            </div>

            {/* Arrangement timeline */}
            <div className="card-flat rounded-2xl border p-5" style={{ background: "#ffffff", borderColor: "rgba(14,116,144,0.25)" }}>
              <div className="flex flex-wrap items-center gap-3 mb-4">
                <span className="text-sm font-bold text-stone-900">🎹 Song Arrangement</span>
                <span className="text-xs text-stone-600">
                  {arrangement.length} sections · {arrangement.reduce((sum, s) => sum + (sectionBars[s] || 4), 0)} bars total
                </span>
              </div>

              {/* Add section buttons */}
              <div className="flex flex-wrap gap-2 mb-4">
                {SECTION_DEFS.map((sec) => (
                  <button key={sec.id} onClick={() => addSection(sec.id)}
                    className="px-3 py-1.5 rounded-lg text-xs font-bold transition-colors hover:opacity-80"
                    style={{ background: "rgba(14,116,144,0.1)", border: "1px solid rgba(14,116,144,0.3)", color: GREEN }}>
                    + {sec.icon} {sec.label}
                  </button>
                ))}
              </div>

              {/* Arrangement strip */}
              <div className="flex gap-2 overflow-x-auto pb-2" style={{ minHeight: 60 }}>
                {arrangement.length === 0 && (
                  <div className="flex items-center justify-center w-full text-stone-500 text-sm">
                    Click + buttons above to add sections to your song arrangement
                  </div>
                )}
                {arrangement.map((secId, idx) => {
                  const sec = SECTION_DEFS.find((s) => s.id === secId);
                  const bars = sectionBars[secId] || 4;
                  const colors = {
                    intro: "#0e7490", verse: "#6d28d9", chorus: "#db2777",
                    bridge: "#d97706", outro: "#059669",
                  };
                  const color = colors[secId] || "#0e7490";
                  return (
                    <div key={`${secId}-${idx}`}
                      className="shrink-0 rounded-xl p-3 flex flex-col items-center gap-1 cursor-pointer transition-all hover:scale-105"
                      style={{
                        minWidth: Math.max(80, bars * 12),
                        background: `${color}15`,
                        border: `1px solid ${color}50`,
                      }}
                      onClick={() => setActiveSection(secId)}
                      title={`Click to edit ${sec?.label} section`}>
                      <div className="flex items-center gap-1">
                        <button onClick={(e) => { e.stopPropagation(); if (idx > 0) moveSection(idx, idx - 1); }}
                          className="text-[10px] text-stone-600 hover:text-stone-900 px-1">◀</button>
                        <span className="text-sm font-bold" style={{ color }}>{sec?.icon} {sec?.label}</span>
                        <button onClick={(e) => { e.stopPropagation(); if (idx < arrangement.length - 1) moveSection(idx, idx + 1); }}
                          className="text-[10px] text-stone-600 hover:text-stone-900 px-1">▶</button>
                      </div>
                      <span className="text-[10px] text-stone-500">{bars} bars</span>
                      <div className="flex gap-0.5 mt-1">
                        {Array.from({ length: Math.min(bars, 16) }).map((_, i) => (
                          <div key={i} className="w-1.5 h-1.5 rounded-full" style={{ background: color, opacity: 0.5 }} />
                        ))}
                      </div>
                      <div className="flex gap-1 mt-1">
                        <button onClick={(e) => { e.stopPropagation(); duplicateSection(idx); }}
                          className="text-[10px] text-stone-500 hover:text-stone-900" title="Duplicate">⧉</button>
                        <button onClick={(e) => { e.stopPropagation(); removeSection(idx); }}
                          className="text-[10px] text-red-600 hover:text-red-700" title="Remove">✕</button>
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Play song button */}
              <div className="flex items-center gap-3 mt-4 pt-4 border-t border-stone-300">
                <button onClick={isPlayingSong ? stop : playSong}
                  className="flex items-center gap-2 px-6 py-3 rounded-xl text-sm font-bold transition-colors"
                  style={{ background: isPlayingSong ? "#B23A2E" : GREEN, color: "#fff" }}>
                  {isPlayingSong ? <><Square className="w-4 h-4" /> Stop Song</> : <><Play className="w-4 h-4" /> Play Full Song</>}
                </button>
                <button onClick={() => exportWav(undefined, true, true)}
                  disabled={exporting}
                  className="flex items-center gap-2 px-6 py-3 rounded-xl text-sm font-bold transition-colors disabled:opacity-40"
                  style={{ background: GOLD, color: "#0a0a0a" }}>
                  <Download className="w-4 h-4" /> {exporting ? "Rendering…" : "Export Full Song WAV"}
                </button>
              </div>
            </div>

            {/* Quick arrangement templates */}
            <div className="card-flat rounded-2xl border p-5" style={{ background: "#ffffff" }}>
              <span className="text-sm font-bold text-stone-900 mb-3 block">Quick Templates</span>
              <div className="flex flex-wrap gap-2">
                <button onClick={() => setArrangement(["intro", "verse", "chorus", "outro"])}
                  className="px-3 py-1.5 rounded-lg text-xs font-bold text-stone-600 bg-[#f1eee8] border border-stone-300 hover:text-stone-900 transition-colors">
                  Simple (4 sections)
                </button>
                <button onClick={() => setArrangement(["intro", "verse", "chorus", "verse", "chorus", "outro"])}
                  className="px-3 py-1.5 rounded-lg text-xs font-bold text-stone-600 bg-[#f1eee8] border border-stone-300 hover:text-stone-900 transition-colors">
                  Pop (6 sections)
                </button>
                <button onClick={() => setArrangement([...DEFAULT_ARRANGEMENT])}
                  className="px-3 py-1.5 rounded-lg text-xs font-bold text-stone-600 bg-[#f1eee8] border border-stone-300 hover:text-stone-900 transition-colors">
                  Full (8 sections)
                </button>
                <button onClick={() => setArrangement(["intro", "verse", "chorus", "verse", "chorus", "bridge", "chorus", "verse", "chorus", "outro"])}
                  className="px-3 py-1.5 rounded-lg text-xs font-bold text-stone-600 bg-[#f1eee8] border border-stone-300 hover:text-stone-900 transition-colors">
                  Extended (10 sections)
                </button>
              </div>
            </div>
          </div>
        )}

        {/* ══ PUBLISH ══ */}
        {tab === "publish" && (
          <div className="grid lg:grid-cols-2 gap-5">
            <div className="card-flat rounded-2xl border p-5 space-y-4" style={{ background: "#ffffff" }}>
              <div className="flex items-center gap-2">
                <FileText className="w-4 h-4" style={{ color: COPPER }} />
                <h2 className="font-heading font-bold text-stone-900">Track Metadata</h2>
              </div>
              <label className="block">
                <span className="text-xs font-bold text-stone-700">Title *</span>
                <input value={meta.title || ""} onChange={(e) => setMeta({ ...meta, title: e.target.value })}
                  placeholder="My first Ghost Producer track"
                  className="mt-1 w-full px-3 py-2 bg-[#ffffff] border border-stone-400 rounded-lg text-sm focus:outline-none focus:border-cyan-700" />
              </label>
              <div className="grid grid-cols-2 gap-3">
                <label className="block">
                  <span className="text-xs font-bold text-stone-700">Artist</span>
                  <input value={meta.artist || user?.full_name || ""} onChange={(e) => setMeta({ ...meta, artist: e.target.value })}
                    className="mt-1 w-full px-3 py-2 bg-[#ffffff] border border-stone-400 rounded-lg text-sm focus:outline-none focus:border-cyan-700" />
                </label>
                <label className="block">
                  <span className="text-xs font-bold text-stone-700">Genre</span>
                  <input value={meta.genre || kit.label} onChange={(e) => setMeta({ ...meta, genre: e.target.value })}
                    className="mt-1 w-full px-3 py-2 bg-[#ffffff] border border-stone-400 rounded-lg text-sm focus:outline-none focus:border-cyan-700" />
                </label>
              </div>
              <div className="grid grid-cols-3 gap-3">
                <div>
                  <div className="text-xs font-bold text-stone-700">BPM</div>
                  <div className="mt-1 font-mono text-sm text-stone-900">{bpm}</div>
                </div>
                <div>
                  <div className="text-xs font-bold text-stone-700">Key</div>
                  <div className="mt-1 font-mono text-sm text-stone-900">{root}</div>
                </div>
                <label className="block">
                  <span className="text-xs font-bold text-stone-700">Price ($)</span>
                  <input type="number" min="0" step="0.5" value={(meta.price_cents || 100) / 100}
                    onChange={(e) => setMeta({ ...meta, price_cents: Math.round(Number(e.target.value) * 100) })}
                    className="mt-1 w-full px-3 py-2 bg-[#ffffff] border border-stone-400 rounded-lg text-sm focus:outline-none focus:border-cyan-700" />
                </label>
              </div>
              <label className="block">
                <span className="text-xs font-bold text-stone-700">Description</span>
                <textarea value={meta.description || ""} onChange={(e) => setMeta({ ...meta, description: e.target.value })}
                  rows={2} placeholder="What is this track? What inspired it?"
                  className="mt-1 w-full px-3 py-2 bg-[#ffffff] border border-stone-400 rounded-lg text-sm focus:outline-none focus:border-cyan-700 resize-y" />
              </label>
              <label className="block">
                <span className="text-xs font-bold text-stone-700">Credits</span>
                <input value={meta.credits || ""} onChange={(e) => setMeta({ ...meta, credits: e.target.value })}
                  placeholder="Who made this? (defaults to you)"
                  className="mt-1 w-full px-3 py-2 bg-[#ffffff] border border-stone-400 rounded-lg text-sm focus:outline-none focus:border-cyan-700" />
              </label>
              <div className="space-y-2 pt-1">
                <label className="flex items-start gap-2 text-sm cursor-pointer">
                  <input type="checkbox" checked={!!meta.ai_disclosure} onChange={(e) => setMeta({ ...meta, ai_disclosure: e.target.checked })}
                    className="mt-0.5 accent-[#0e7490]" />
                  <span className="text-stone-800">
                    <b>AI-assisted disclosure</b> — label this track as AI-assisted where platforms require it
                    <span className="block text-xs text-stone-500">Required by YouTube/Spotify/Apple policies for AI-generated content.</span>
                  </span>
                </label>
                <label className="flex items-start gap-2 text-sm cursor-pointer">
                  <input type="checkbox" checked={!!meta.samples_cleared} onChange={(e) => setMeta({ ...meta, samples_cleared: e.target.checked })}
                    className="mt-0.5 accent-[#0e7490]" />
                  <span className="text-stone-800">
                    <b>Sample clearance statement</b> — I confirm every sound in this track is either synthesized by this studio or mine to use
                  </span>
                </label>
              </div>
            </div>

            <div className="space-y-5">
              <div className="rounded-2xl border p-5" style={{ background: "#ffffff", borderColor: "rgba(14,116,144,0.3)" }}>
                <div className="flex items-center gap-2 mb-3">
                  <Lock className="w-4 h-4" style={{ color: GREEN }} />
                  <h2 className="font-heading font-bold text-stone-900">Ownership — yours, not ours</h2>
                </div>
                <div className="space-y-2 text-sm text-stone-800">
                  <p className="flex gap-2"><span style={{ color: GREEN }}>✓</span> You keep <b>100% ownership</b> of the copyright in everything made here.</p>
                  <p className="flex gap-2"><span style={{ color: GREEN }}>✓</span> The platform never claims your work — no transfers, no assignments.</p>
                  <p className="flex gap-2"><span style={{ color: GREEN }}>✓</span> When a track sells, the creator keeps <b>70%</b> and the platform retains a <b>30% service fee</b> (Mandate 2).</p>
                  <p className="flex gap-2"><span style={{ color: GREEN }}>✓</span> All sounds are synthesized — there are no third-party samples in the kits, so there's nothing to clear.</p>
                  <p className="flex gap-2"><span style={{ color: GREEN }}>✓</span> Full song arrangement exported as one WAV — sections play in sequence.</p>
                </div>
              </div>

              <div className="rounded-2xl border p-5" style={{ background: "rgba(14,116,144,0.05)", borderColor: "rgba(14,116,144,0.3)" }}>
                <div className="flex items-center gap-2 mb-3">
                  <Upload className="w-4 h-4" style={{ color: GOLD }} />
                  <h2 className="font-heading font-bold text-stone-900">Publish to your store</h2>
                </div>
                <p className="text-xs text-stone-600 mb-4">
                  {arrangement.length > 1
                    ? "Your full arrangement will be rendered and published. Preview it first to hear exactly what buyers get."
                    : "Generate a preview to hear what buyers get, then render & publish to your Media Store."}
                </p>
                {projects.length > 0 && (
                  <label className="block mb-3">
                    <span className="text-xs font-bold text-stone-700">Attach to AI team project (optional)</span>
                    <select value={projectId} onChange={(e) => setProjectId(e.target.value)}
                      className="mt-1 w-full px-3 py-2 bg-[#ffffff] border border-stone-400 rounded-lg text-sm focus:outline-none focus:border-cyan-700">
                      <option value="">— No project —</option>
                      {projects.map((p) => (
                        <option key={p.id} value={p.id}>
                          {p.title} · {p.current_stage}
                        </option>
                      ))}
                    </select>
                    <span className="block text-[11px] text-stone-500 mt-1">
                      The published track becomes a deliverable the AI team can review and carry forward.
                    </span>
                  </label>
                )}
                {previewErr && <p className="text-xs mb-3" style={{ color: "#B23A2E" }}>{previewErr}</p>}
                {previewUrl && (
                  <div className="mb-3 p-3 rounded-lg" style={{ border: "1px solid rgba(14,116,144,0.3)", background: "rgba(14,116,144,0.06)" }}>
                    <div className="text-[11px] font-black mb-1.5" style={{ color: GOLD }}>
                      PREVIEW{previewDur ? ` · ~${previewDur}s` : ""}
                    </div>
                    <audio controls src={previewUrl} style={{ width: "100%", height: 32 }} />
                  </div>
                )}
                <button onClick={generatePreview}
                  disabled={previewing || exporting}
                  className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-lg text-sm font-black disabled:opacity-40 transition-colors mb-2"
                  style={{ background: "transparent", border: `1px solid ${GREEN}55`, color: GREEN }}>
                  {previewing ? <><Save className="w-4 h-4 animate-pulse" /> Rendering preview…</> : <><Headphones className="w-4 h-4" /> Generate Preview</>}
                </button>
                <button onClick={publish}
                  disabled={exporting || previewing}
                  className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-lg text-sm font-black disabled:opacity-40 transition-colors"
                  style={{ background: GOLD, color: "#0a0a0a" }}>
                  {exporting ? <><Save className="w-4 h-4 animate-pulse" /> Rendering &amp; publishing…</> : <><Upload className="w-4 h-4" /> Render &amp; Publish WAV</>}
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
