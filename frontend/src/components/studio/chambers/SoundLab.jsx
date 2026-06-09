import { useState, useCallback } from "react";
import { api } from "../../../lib/api";
import { toast } from "sonner";
import { Wand2, RefreshCw } from "lucide-react";

const KEYS = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];
const MOODS = ['Melancholy', 'Hype', 'Spiritual', 'Trap', 'Lo-fi', 'Jazz', 'Gospel', 'R&B', 'Pop', 'Boom Bap'];

export default function SoundLab({ tier = 'base' }) {
  const [bpm, setBpm] = useState(90);
  const [key, setKey] = useState('C');
  const [activeMoods, setActiveMoods] = useState([]);
  const [reference, setReference] = useState('');
  const [blueprint, setBlueprint] = useState('');
  const [loading, setLoading] = useState(false);

  const toggleMood = (mood) => {
    setActiveMoods(m => m.includes(mood) ? m.filter(x => x !== mood) : [...m, mood]);
  };

  const generate = useCallback(async () => {
    setLoading(true);
    setBlueprint('');
    try {
      const r = await api.post('/studio/sound', { bpm, key, mood: activeMoods, reference });
      setBlueprint(r.data.blueprint);
    } catch {
      toast.error('The lab went silent — try again.');
    } finally {
      setLoading(false);
    }
  }, [bpm, key, activeMoods, reference]);

  return (
    <div style={{ fontFamily: 'inherit', color: 'rgba(255,255,255,0.9)', display: 'flex', flexDirection: 'column', gap: 22 }}>

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
              style={{ flex: 1, accentColor: '#34d399' }}
            />
            <div style={{
              minWidth: 44, textAlign: 'center',
              fontFamily: 'monospace', fontSize: 18, fontWeight: 900,
              color: '#34d399',
            }}>
              {bpm}
            </div>
          </div>
          <div style={{ fontSize: 9, fontFamily: 'monospace', color: 'rgba(255,255,255,0.25)', marginTop: 4 }}>
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
                  background: key === k ? 'rgba(52,211,153,0.2)' : 'rgba(255,255,255,0.03)',
                  border: `1px solid ${key === k ? '#34d399' : 'rgba(255,255,255,0.1)'}`,
                  color: key === k ? '#34d399' : 'rgba(255,255,255,0.55)',
                  fontFamily: 'monospace', fontSize: key.includes('#') ? 10 : 12,
                  fontWeight: key === k ? 900 : 400,
                  cursor: 'pointer',
                  boxShadow: key === k ? '0 0 8px rgba(52,211,153,0.3)' : 'none',
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
                  background: active ? 'rgba(52,211,153,0.15)' : 'rgba(255,255,255,0.03)',
                  border: `1px solid ${active ? '#34d399' : 'rgba(255,255,255,0.1)'}`,
                  color: active ? '#34d399' : 'rgba(255,255,255,0.5)',
                  padding: '6px 14px',
                  fontFamily: 'monospace', fontSize: 11,
                  fontWeight: active ? 900 : 400,
                  cursor: 'pointer',
                  letterSpacing: '0.05em',
                  transition: 'all 0.15s ease',
                  boxShadow: active ? '0 0 8px rgba(52,211,153,0.25)' : 'none',
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

      <button
        onClick={generate}
        disabled={loading}
        style={{
          background: loading ? 'rgba(52,211,153,0.15)' : 'linear-gradient(135deg, #065f46, #34d399)',
          border: 'none', color: loading ? '#34d399' : '#050508',
          fontFamily: 'monospace', fontWeight: 900,
          fontSize: 13, letterSpacing: '0.1em', textTransform: 'uppercase',
          padding: '12px 28px', cursor: loading ? 'default' : 'pointer',
          display: 'flex', alignItems: 'center', gap: 8, alignSelf: 'flex-start',
          boxShadow: loading ? 'none' : '0 4px 0 rgba(6,95,70,0.5)',
        }}
      >
        {loading ? <RefreshCw style={{ width: 14, height: 14, animation: 'spin 1s linear infinite' }} /> : <Wand2 style={{ width: 14, height: 14 }} />}
        {loading ? 'Generating...' : 'Generate Sonic Blueprint'}
      </button>

      {blueprint && (
        <div style={{
          background: 'rgba(0,0,0,0.5)',
          border: '1px solid rgba(52,211,153,0.35)',
          padding: '20px 20px',
          boxShadow: '0 0 30px rgba(52,211,153,0.1)',
        }}>
          <div style={{
            fontSize: 9, fontFamily: 'monospace', letterSpacing: '0.2em',
            textTransform: 'uppercase', color: 'rgba(52,211,153,0.7)', marginBottom: 12,
          }}>
            Sonic Blueprint — {bpm} BPM • {key} • {activeMoods.join(', ') || 'Mixed'}
          </div>
          <pre style={{
            margin: 0, fontFamily: 'monospace', fontSize: 12,
            color: '#34d399', lineHeight: 1.8,
            whiteSpace: 'pre-wrap', wordBreak: 'break-word',
          }}>
            {blueprint}
          </pre>
        </div>
      )}

      <style>{`@keyframes spin { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }`}</style>
    </div>
  );
}

const labelStyle = {
  display: 'block', fontSize: 9, fontFamily: 'monospace', letterSpacing: '0.15em',
  textTransform: 'uppercase', color: 'rgba(184,134,11,0.7)', marginBottom: 8,
};
const inputStyle = {
  width: '100%', boxSizing: 'border-box',
  background: 'rgba(255,255,255,0.03)',
  border: '1px solid rgba(52,211,153,0.2)',
  padding: '9px 12px', color: 'rgba(255,255,255,0.9)',
  fontSize: 13, fontFamily: 'inherit', outline: 'none',
};
