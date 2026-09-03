import { useState, useCallback, useEffect } from "react";
import { toast } from "sonner";
import { Wand2, RefreshCw } from "lucide-react";

const KEYS = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];
const MOODS = ['Melancholy', 'Hype', 'Spiritual', 'Trap', 'Lo-fi', 'Jazz', 'Gospel', 'R&B', 'Pop', 'Boom Bap'];

// Local sound synthesis — zero AI, zero keys. Renders a short loop in the
// browser (OfflineAudioContext) from BPM/key/mood and gives the creator a WAV
// they can hear and keep. The AI blueprint is an optional enhancement on top.
const MOOD_WAVE = {
  Hype: 'square', Trap: 'sawtooth', Jazz: 'sine', Gospel: 'triangle',
  'R&B': 'sine', Pop: 'triangle', 'Boom Bap': 'sine', 'Lo-fi': 'triangle',
};
const KEY_TO_MIDI = { C: 60, 'C#': 61, D: 62, 'D#': 63, E: 64, F: 65, 'F#': 66, G: 67, 'G#': 68, A: 69, 'A#': 70, B: 71 };

function synthLocalLoop(bpm, key, moods) {
  const AC = window.AudioContext || window.webkitAudioContext;
  const bars = 4;
  const beat = 60 / bpm;
  const dur = bars * 4 * beat;
  const ctx = new (window.OfflineAudioContext || AC)(2, Math.ceil(dur * 44100), 44100);
  const master = ctx.createGain();
  master.gain.value = 0.8;
  master.connect(ctx.destination);
  const wave = MOOD_WAVE[moods[0]] || 'triangle';
  const rootMidi = (KEY_TO_MIDI[key] || 60) - 12;

  const kick = (t) => {
    const o = ctx.createOscillator(); const g = ctx.createGain();
    o.type = 'sine'; o.frequency.setValueAtTime(150, t);
    o.frequency.exponentialRampToValueAtTime(45, t + 0.12);
    g.gain.setValueAtTime(0.9, t); g.gain.exponentialRampToValueAtTime(0.001, t + 0.22);
    o.connect(g); g.connect(master); o.start(t); o.stop(t + 0.25);
  };
  const snare = (t) => {
    const g = ctx.createGain(); const src = ctx.createBufferSource();
    const buf = ctx.createBuffer(1, 44100 * 0.12, 44100);
    const d = buf.getChannelData(0);
    for (let i = 0; i < d.length; i++) d[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / d.length, 2);
    src.buffer = buf; g.gain.setValueAtTime(0.55, t); g.gain.exponentialRampToValueAtTime(0.001, t + 0.12);
    src.connect(g); g.connect(master); src.start(t);
  };
  const hat = (t, open) => {
    const g = ctx.createGain(); const src = ctx.createBufferSource();
    const len = open ? 0.25 : 0.05;
    const buf = ctx.createBuffer(1, Math.ceil(44100 * len), 44100);
    const d = buf.getChannelData(0);
    for (let i = 0; i < d.length; i++) d[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / d.length, 3);
    src.buffer = buf; g.gain.setValueAtTime(open ? 0.25 : 0.18, t); g.gain.exponentialRampToValueAtTime(0.001, t + len);
    src.connect(g); g.connect(master); src.start(t);
  };
  const bass = (t, midi, len) => {
    const o = ctx.createOscillator(); const g = ctx.createGain();
    o.type = wave; o.frequency.value = 440 * Math.pow(2, (midi - 69) / 12);
    g.gain.setValueAtTime(0.32, t); g.gain.exponentialRampToValueAtTime(0.001, t + len);
    o.connect(g); g.connect(master); o.start(t); o.stop(t + len + 0.02);
  };

  for (let bar = 0; bar < bars; bar++) {
    const barT = bar * 4 * beat;
    [0, 2].forEach((b) => kick(barT + b * beat));
    [1, 3].forEach((b) => snare(barT + b * beat));
    for (let e = 0; e < 8; e++) hat(barT + e * beat / 2, e === 7);
    bass(barT, rootMidi, beat * 3.8);
    bass(barT + 2 * beat, rootMidi + 3, beat * 1.8);
  }
  return ctx.startRendering().then((rendered) => {
    const wav = encodeWav(rendered);
    return { url: URL.createObjectURL(new Blob([wav], { type: 'audio/wav' })), dur };
  });
}

function encodeWav(buffer) {
  const numCh = buffer.numberOfChannels;
  const len = buffer.length * numCh * 2 + 44;
  const ab = new ArrayBuffer(len);
  const v = new DataView(ab);
  const ws = (o, s) => { for (let i = 0; i < s.length; i++) v.setUint8(o + i, s.charCodeAt(i)); };
  ws(0, 'RIFF'); v.setUint32(4, len - 8, true); ws(8, 'WAVE'); ws(12, 'fmt ');
  v.setUint32(16, 16, true); v.setUint16(20, 1, true); v.setUint16(22, numCh, true);
  v.setUint32(24, 44100, true); v.setUint32(28, 44100 * numCh * 2, true);
  v.setUint16(32, numCh * 2, true); v.setUint16(34, 16, true); ws(36, 'data');
  v.setUint32(40, buffer.length * numCh * 2, true);
  const chans = [];
  for (let c = 0; c < numCh; c++) chans.push(buffer.getChannelData(c));
  let off = 44;
  for (let i = 0; i < buffer.length; i++) {
    for (let c = 0; c < numCh; c++) {
      const s = Math.max(-1, Math.min(1, chans[c][i]));
      v.setInt16(off, s < 0 ? s * 0x8000 : s * 0x7fff, true); off += 2;
    }
  }
  return ab;
}

export default function SoundLab({ tier = 'base', sovereignDispatch, artifact }) {
  const [bpm, setBpm] = useState(90);
  const [key, setKey] = useState('C');
  const [activeMoods, setActiveMoods] = useState([]);
  const [reference, setReference] = useState('');
  const [blueprint, setBlueprint] = useState('');
  const [loading, setLoading] = useState(false);
  const [localPreview, setLocalPreview] = useState(null);
  const [previewBusy, setPreviewBusy] = useState(false);

  const previewLocal = useCallback(async () => {
    setPreviewBusy(true);
    try {
      const { url } = await synthLocalLoop(bpm, key, activeMoods);
      setLocalPreview(url);
      const el = document.getElementById('soundlab-local-preview');
      if (el) { el.load(); el.play().catch(() => {}); }
    } catch (e) {
      toast.error('Could not synthesize the preview in this browser.');
    } finally {
      setPreviewBusy(false);
    }
  }, [bpm, key, activeMoods]);

  // Receive blueprint from Sovereign
  useEffect(() => { if (artifact) { setBlueprint(artifact); setLoading(false); } }, [artifact]);

  const toggleMood = (mood) => {
    setActiveMoods(m => m.includes(mood) ? m.filter(x => x !== mood) : [...m, mood]);
  };

  const generate = useCallback(async () => {
    if (!sovereignDispatch?.current) { toast.error('Sovereign is not connected.'); return; }
    setLoading(true);
    setBlueprint('');
    await sovereignDispatch.current({
      action: 'sonic_blueprint',
      context: { bpm, key, mood: activeMoods, reference },
      message: `Build me a sonic blueprint — ${bpm} BPM, key of ${key}, ${activeMoods.join('/')} mood.`,
    });
  }, [bpm, key, activeMoods, reference, sovereignDispatch]);

  return (
    <div style={{ fontFamily: 'inherit', color: 'rgba(28,25,23,0.9)', display: 'flex', flexDirection: 'column', gap: 22 }}>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        {/* BPM */}
        <div>
          <label style={labelStyle}>BPM</label>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <input
              type="range"
              min={60} max={180}
              value={bpm}
              onChange={e => setBpm(Number(e.target.value))}
              style={{ flex: 1, accentColor: '#047857' }}
            />
            <div style={{
              minWidth: 44, textAlign: 'center',
              fontFamily: 'monospace', fontSize: 18, fontWeight: 900,
              color: '#047857',
            }}>
              {bpm}
            </div>
          </div>
          <div style={{ fontSize: 9, fontFamily: 'monospace', color: 'rgba(28,25,23,0.25)', marginTop: 4 }}>
            {bpm < 80 ? 'Slow / Ambient' : bpm < 100 ? 'Lo-fi / Chill' : bpm < 120 ? 'Mid-tempo' : bpm < 140 ? 'Energetic' : 'Fast / Hype'}
          </div>
        </div>

        {/* Key */}
        <div>
          <label style={labelStyle}>Key</label>
          <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
            {KEYS.map(k => (
              <button
                key={k}
                onClick={() => setKey(k)}
                style={{
                  width: 34, height: 34,
                  background: key === k ? 'rgba(4,120,87,0.2)' : 'rgba(28,25,23,0.03)',
                  border: `1px solid ${key === k ? '#047857' : 'rgba(28,25,23,0.1)'}`,
                  color: key === k ? '#047857' : 'rgba(28,25,23,0.55)',
                  fontFamily: 'monospace', fontSize: key.includes('#') ? 10 : 12,
                  fontWeight: key === k ? 900 : 400,
                  cursor: 'pointer',
                  boxShadow: key === k ? '0 0 8px rgba(4,120,87,0.3)' : 'none',
                  transition: 'all 0.15s ease',
                }}
              >
                {k}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Mood tags */}
      <div>
        <label style={labelStyle}>Mood Tags</label>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          {MOODS.map(mood => {
            const active = activeMoods.includes(mood);
            return (
              <button
                key={mood}
                onClick={() => toggleMood(mood)}
                style={{
                  background: active ? 'rgba(4,120,87,0.15)' : 'rgba(28,25,23,0.03)',
                  border: `1px solid ${active ? '#047857' : 'rgba(28,25,23,0.1)'}`,
                  color: active ? '#047857' : 'rgba(28,25,23,0.5)',
                  padding: '6px 14px',
                  fontFamily: 'monospace', fontSize: 11,
                  fontWeight: active ? 900 : 400,
                  cursor: 'pointer',
                  letterSpacing: '0.05em',
                  transition: 'all 0.15s ease',
                  boxShadow: active ? '0 0 8px rgba(4,120,87,0.25)' : 'none',
                }}
              >
                {mood}
              </button>
            );
          })}
        </div>
      </div>

      {/* Reference artist */}
      <div>
        <label style={labelStyle}>Reference Artist (optional)</label>
        <input
          value={reference}
          onChange={e => setReference(e.target.value)}
          placeholder="e.g. Kendrick Lamar, J Dilla, Frank Ocean..."
          style={inputStyle}
        />
      </div>

      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'center' }}>
        <button
          onClick={previewLocal}
          disabled={previewBusy}
          title="Renders drums + bass in your browser — no AI, no API key, works offline"
          style={{
            background: previewBusy ? 'rgba(28,25,23,0.08)' : 'rgba(28,25,23,0.9)',
            border: '1px solid rgba(28,25,23,0.35)',
            color: previewBusy ? 'rgba(28,25,23,0.5)' : '#ffffff',
            fontFamily: 'monospace', fontWeight: 900,
            fontSize: 12, letterSpacing: '0.1em', textTransform: 'uppercase',
            padding: '12px 24px', cursor: previewBusy ? 'default' : 'pointer',
            display: 'flex', alignItems: 'center', gap: 8,
          }}
        >
          {previewBusy ? <RefreshCw style={{ width: 14, height: 14, animation: 'spin 1s linear infinite' }} /> : <Wand2 style={{ width: 14, height: 14 }} />}
          {previewBusy ? 'Rendering...' : 'Preview Local Sound'}
        </button>
        <button
          onClick={generate}
          disabled={loading}
          style={{
            background: loading ? 'rgba(4,120,87,0.15)' : 'linear-gradient(135deg, #065f46, #047857)',
            border: 'none', color: loading ? '#047857' : '#ffffff',
            fontFamily: 'monospace', fontWeight: 900,
            fontSize: 13, letterSpacing: '0.1em', textTransform: 'uppercase',
            padding: '12px 28px', cursor: loading ? 'default' : 'pointer',
            display: 'flex', alignItems: 'center', gap: 8, alignSelf: 'flex-start',
            boxShadow: loading ? 'none' : '0 4px 0 rgba(6,95,70,0.5)',
          }}
        >
          {loading ? <RefreshCw style={{ width: 14, height: 14, animation: 'spin 1s linear infinite' }} /> : <Wand2 style={{ width: 14, height: 14 }} />}
          {loading ? 'Generating...' : 'Enhance with AI Blueprint'}
        </button>
      </div>

      {localPreview && (
        <div style={{
          background: 'rgba(28,25,23,0.04)',
          border: '1px solid rgba(28,25,23,0.2)',
          padding: '14px 16px',
          display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap',
        }}>
          <audio id="soundlab-local-preview" src={localPreview} controls style={{ height: 34 }} />
          <span style={{ fontSize: 10, fontFamily: 'monospace', color: 'rgba(28,25,23,0.55)' }}>
            Local preview — {bpm} BPM • {key} • {activeMoods.join(', ') || 'Mixed'} — synthesized in your browser, no AI or key required. Download from the player menu.
          </span>
        </div>
      )}

      {blueprint && (
        <div style={{
          background: 'rgba(28,25,23,0.04)',
          border: '1px solid rgba(4,120,87,0.35)',
          padding: '20px 20px',
          boxShadow: '0 0 30px rgba(4,120,87,0.1)',
        }}>
          <div style={{
            fontSize: 9, fontFamily: 'monospace', letterSpacing: '0.2em',
            textTransform: 'uppercase', color: 'rgba(4,120,87,0.7)', marginBottom: 12,
          }}>
            Sonic Blueprint — {bpm} BPM • {key} • {activeMoods.join(', ') || 'Mixed'}
          </div>
          <textarea
            value={blueprint}
            onChange={(e) => setBlueprint(e.target.value)}
            aria-label="Editable sonic blueprint draft"
            style={{
              width: '100%', minHeight: 220, boxSizing: 'border-box', resize: 'vertical',
              margin: 0, fontFamily: 'monospace', fontSize: 12,
              color: '#047857', lineHeight: 1.8,
              whiteSpace: 'pre-wrap', wordBreak: 'break-word',
              background: 'rgba(28,25,23,0.04)', border: '1px solid rgba(4,120,87,0.2)',
              padding: 12, outline: 'none',
            }}
          />
        </div>
      )}

      <style>{`@keyframes spin { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }`}</style>
    </div>
  );
}

const labelStyle = {
  display: 'block', fontSize: 9, fontFamily: 'monospace', letterSpacing: '0.15em',
  textTransform: 'uppercase', color: 'rgba(146,64,14,0.7)', marginBottom: 8,
};
const inputStyle = {
  width: '100%', boxSizing: 'border-box',
  background: 'rgba(28,25,23,0.03)',
  border: '1px solid rgba(4,120,87,0.2)',
  padding: '9px 12px', color: 'rgba(28,25,23,0.9)',
  fontSize: 13, fontFamily: 'inherit', outline: 'none',
};
