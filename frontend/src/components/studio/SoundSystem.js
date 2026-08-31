// Sacred Sound System — Web Audio API synthesized sounds
// AudioContext is created lazily on first user gesture

let ctx = null;

function getCtx() {
  if (!ctx) {
    ctx = new (window.AudioContext || window.webkitAudioContext)();
  }
  if (ctx.state === 'suspended') {
    ctx.resume();
  }
  return ctx;
}

function playChime(frequency, duration, type = 'sine', gain = 0.3, delay = 0) {
  const c = getCtx();
  const osc = c.createOscillator();
  const gainNode = c.createGain();
  osc.connect(gainNode);
  gainNode.connect(c.destination);
  osc.type = type;
  osc.frequency.setValueAtTime(frequency, c.currentTime + delay);
  gainNode.gain.setValueAtTime(0, c.currentTime + delay);
  gainNode.gain.linearRampToValueAtTime(gain, c.currentTime + delay + 0.02);
  gainNode.gain.exponentialRampToValueAtTime(0.001, c.currentTime + delay + duration);
  osc.start(c.currentTime + delay);
  osc.stop(c.currentTime + delay + duration);
}

function playTone(frequency, startTime, duration, type = 'sine', startGain = 0.3, endGain = 0.001) {
  const c = getCtx();
  const osc = c.createOscillator();
  const gainNode = c.createGain();
  osc.connect(gainNode);
  gainNode.connect(c.destination);
  osc.type = type;
  osc.frequency.setValueAtTime(frequency, startTime);
  gainNode.gain.setValueAtTime(startGain, startTime);
  gainNode.gain.exponentialRampToValueAtTime(endGain, startTime + duration);
  osc.start(startTime);
  osc.stop(startTime + duration);
}

const SOUNDS = {
  chamber_enter: () => {
    // Ascending three-note chime
    playChime(523.25, 0.6, 'sine', 0.25, 0);    // C5
    playChime(659.25, 0.6, 'sine', 0.25, 0.12); // E5
    playChime(783.99, 0.8, 'sine', 0.3, 0.24);  // G5
    playChime(1046.5, 0.9, 'sine', 0.2, 0.4);   // C6 bell overtone
  },

  save_ritual: () => {
    // Temple bell with overtones
    const c = getCtx();
    const now = c.currentTime;
    playTone(220, now, 1.2, 'sine', 0.2, 0.001);
    playTone(440, now, 1.0, 'sine', 0.15, 0.001);
    playTone(880, now + 0.05, 0.8, 'sine', 0.1, 0.001);
    playTone(1760, now + 0.1, 0.6, 'sine', 0.05, 0.001);
    // Soft completion note
    playChime(659.25, 0.7, 'sine', 0.2, 0.5);
    playChime(783.99, 0.8, 'sine', 0.2, 0.7);
  },

  task_complete: () => {
    // Quick upward sparkle
    playChime(880, 0.3, 'sine', 0.2, 0);
    playChime(1108.73, 0.3, 'sine', 0.2, 0.08);
    playChime(1318.51, 0.4, 'sine', 0.25, 0.16);
  },

  ritual_open: () => {
    // Scroll unfurling — low rumble then rise
    const c = getCtx();
    const now = c.currentTime;
    // Deep resonance
    playTone(110, now, 0.4, 'sine', 0.15, 0.001);
    // Rising chimes
    playChime(392, 0.5, 'sine', 0.2, 0.1);
    playChime(523.25, 0.5, 'sine', 0.2, 0.25);
    playChime(659.25, 0.6, 'sine', 0.25, 0.4);
    playChime(783.99, 0.7, 'sine', 0.2, 0.55);
  },

  summon: () => {
    // Soft conjuring — digital sparkle cluster
    const freqs = [523.25, 659.25, 783.99, 1046.5, 1318.51];
    freqs.forEach((f, i) => {
      playChime(f, 0.4, 'sine', 0.12 + i * 0.02, i * 0.06);
    });
  },

  timeline_advance: () => {
    // Forward motion — two confident notes
    playChime(392, 0.35, 'triangle', 0.2, 0);
    playChime(523.25, 0.5, 'sine', 0.25, 0.15);
  },
};

export const studioSound = {
  play(type) {
    try {
      const fn = SOUNDS[type];
      if (fn) fn();
    } catch (e) {
      // Silently fail — audio should never break the UI
      console.warn('SoundSystem: could not play', type, e);
    }
  },
};

export default studioSound;
