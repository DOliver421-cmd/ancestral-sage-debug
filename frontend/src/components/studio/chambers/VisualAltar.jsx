import { useState, useCallback, useEffect } from "react";
import { toast } from "sonner";
import { Wand2, RefreshCw } from "lucide-react";

const PRESET_COLORS = ['#ffd700', '#c084fc', '#34d399', '#f87171', '#67e8f9', '#fb923c', '#a78bfa', '#f59e0b', '#ec4899', '#22d3ee'];

export default function VisualAltar({ tier = 'base', sovereignDispatch, artifact }) {
  const [descriptions, setDescriptions] = useState(['']);
  const [colors, setColors] = useState(['#ffd700', '#0a0a14', '#c084fc', '#34d399', '#f87171']);
  const [notes, setNotes] = useState('');
  const [direction, setDirection] = useState('');
  const [loading, setLoading] = useState(false);
  const [dragOver, setDragOver] = useState(false);

  // Receive AI result from Sovereign
  useEffect(() => { if (artifact) { setDirection(artifact); setLoading(false); } }, [artifact]);

  const addDescription = () => setDescriptions(d => [...d, '']);
  const updateDesc = (i, val) => setDescriptions(d => d.map((x, idx) => idx === i ? val : x));
  const removeDesc = (i) => setDescriptions(d => d.filter((_, idx) => idx !== i));

  const updateColor = (i, val) => setColors(c => c.map((x, idx) => idx === i ? val : x));

  const blessVision = useCallback(async () => {
    const filled = descriptions.filter(d => d.trim());
    if (!filled.length) { toast.error('Add at least one image description.'); return; }
    if (!sovereignDispatch?.current) { toast.error('Sovereign is not connected.'); return; }
    setLoading(true);
    setDirection('');
    await sovereignDispatch.current({
      action: 'visual_direction',
      context: { descriptions: filled, colors, notes },
      message: 'Bless this vision — give me visual direction.',
    });
  }, [descriptions, colors, notes, sovereignDispatch]);

  return (
    <div style={{ fontFamily: 'inherit', color: 'rgba(255,255,255,0.9)', display: 'flex', flexDirection: 'column', gap: 24 }}>

      {/* Upload zone */}
      <div
        onDragOver={e => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={e => { e.preventDefault(); setDragOver(false); toast.info('Connect your cloud storage to upload assets.'); }}
        style={{
          border: `2px dashed ${dragOver ? 'rgba(192,132,252,0.6)' : 'rgba(255,255,255,0.1)'}`,
          background: dragOver ? 'rgba(192,132,252,0.05)' : 'rgba(255,255,255,0.02)',
          padding: '32px 24px',
          textAlign: 'center',
          transition: 'all 0.2s ease',
          cursor: 'default',
        }}
      >
        <div style={{ fontSize: 32, marginBottom: 10, opacity: 0.4 }}>◉</div>
        <div style={{ fontSize: 13, color: 'rgba(255,255,255,0.5)', marginBottom: 6 }}>
          Drag & drop visual assets here
        </div>
        <div style={{ fontSize: 11, fontFamily: 'monospace', color: 'rgba(192,132,252,0.6)' }}>
          Connect your Dropbox / Google Drive to upload assets
        </div>
      </div>

      {/* Moodboard descriptions */}
      <div>
        <div style={sectionLabel}>Moodboard — Image Descriptions</div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {descriptions.map((desc, i) => (
            <div key={i} style={{ display: 'flex', gap: 8, alignItems: 'flex-start' }}>
              <div style={{
                flex: 1,
                background: 'rgba(192,132,252,0.04)',
                border: '1px solid rgba(192,132,252,0.2)',
                padding: '10px 12px',
                color: 'rgba(255,255,255,0.85)',
                fontSize: 13,
                minHeight: 56,
                display: 'flex', alignItems: 'center',
              }}>
                <input
                  value={desc}
                  onChange={e => updateDesc(i, e.target.value)}
                  placeholder={`Visual description ${i + 1} — e.g. "neon city at dusk, purple haze, cinematic"`}
                  style={{
                    background: 'none', border: 'none', outline: 'none',
                    color: 'inherit', fontSize: 'inherit', width: '100%', fontFamily: 'inherit',
                  }}
                />
              </div>
              {descriptions.length > 1 && (
                <button
                  onClick={() => removeDesc(i)}
                  style={{ background: 'none', border: 'none', color: 'rgba(255,255,255,0.25)', cursor: 'pointer', fontSize: 18, padding: '8px 4px' }}
                >×</button>
              )}
            </div>
          ))}
        </div>
        <button
          onClick={addDescription}
          style={{
            marginTop: 8, background: 'rgba(192,132,252,0.08)',
            border: '1px dashed rgba(192,132,252,0.3)',
            color: 'rgba(192,132,252,0.7)',
            padding: '7px 16px', cursor: 'pointer',
            fontFamily: 'monospace', fontSize: 11, letterSpacing: '0.1em',
          }}
        >
          + ADD IMAGE
        </button>
      </div>

      {/* Color palette */}
      <div>
        <div style={sectionLabel}>Project Color Palette (5 colors)</div>
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
          {colors.map((c, i) => (
            <div key={i} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6 }}>
              <div style={{
                width: 48, height: 48,
                background: c,
                border: '1px solid rgba(255,255,255,0.2)',
                cursor: 'pointer',
                boxShadow: `0 0 10px ${c}60`,
                position: 'relative',
              }}>
                <input
                  type="color"
                  value={c}
                  onChange={e => updateColor(i, e.target.value)}
                  style={{
                    position: 'absolute', inset: 0, width: '100%', height: '100%',
                    opacity: 0, cursor: 'pointer',
                  }}
                />
              </div>
              <div style={{ fontSize: 9, fontFamily: 'monospace', color: 'rgba(255,255,255,0.35)' }}>
                {c.toUpperCase()}
              </div>
            </div>
          ))}
        </div>
        <div style={{ marginTop: 10, display: 'flex', gap: 6, flexWrap: 'wrap' }}>
          {PRESET_COLORS.map(pc => (
            <button
              key={pc}
              onClick={() => {
                const empty = colors.findIndex((c, i) => i > 0 && c === colors[0]);
                setColors(prev => { const next = [...prev]; next[Math.min(empty >= 0 ? empty : 4, 4)] = pc; return next; });
              }}
              style={{
                width: 20, height: 20, background: pc, border: '1px solid rgba(255,255,255,0.15)',
                cursor: 'pointer', flexShrink: 0,
              }}
              title={`Use ${pc}`}
            />
          ))}
        </div>
      </div>

      {/* Visual notes */}
      <div>
        <div style={sectionLabel}>Visual Notes</div>
        <textarea
          value={notes}
          onChange={e => setNotes(e.target.value)}
          placeholder="Reference artists, visual style, era, influences..."
          rows={3}
          style={{
            width: '100%', boxSizing: 'border-box',
            background: 'rgba(255,255,255,0.03)',
            border: '1px solid rgba(192,132,252,0.2)',
            padding: '10px 12px', color: 'rgba(255,255,255,0.85)',
            fontSize: 13, fontFamily: 'inherit', outline: 'none', resize: 'vertical',
          }}
        />
      </div>

      <button
        onClick={blessVision}
        disabled={loading}
        style={{
          background: loading ? 'rgba(192,132,252,0.2)' : 'linear-gradient(135deg, #7c3aed, #c084fc)',
          border: 'none', color: '#fff',
          fontFamily: 'monospace', fontWeight: 900,
          fontSize: 13, letterSpacing: '0.1em', textTransform: 'uppercase',
          padding: '12px 28px', cursor: loading ? 'default' : 'pointer',
          display: 'flex', alignItems: 'center', gap: 8, alignSelf: 'flex-start',
          boxShadow: loading ? 'none' : '0 4px 0 rgba(124,58,237,0.5)',
        }}
      >
        {loading ? <RefreshCw style={{ width: 14, height: 14, animation: 'spin 1s linear infinite' }} /> : <Wand2 style={{ width: 14, height: 14 }} />}
        {loading ? 'Blessing...' : 'Bless This Vision'}
      </button>

      {direction && (
        <div style={{
          background: 'rgba(192,132,252,0.06)',
          border: '1px solid rgba(192,132,252,0.3)',
          padding: '20px 20px',
          boxShadow: '0 0 30px rgba(192,132,252,0.1)',
        }}>
          <div style={{ fontSize: 9, fontFamily: 'monospace', letterSpacing: '0.2em', textTransform: 'uppercase', color: 'rgba(192,132,252,0.7)', marginBottom: 10 }}>
            Visual Direction
          </div>
          <p style={{ margin: 0, fontSize: 14, color: 'rgba(255,255,255,0.88)', lineHeight: 1.7, fontStyle: 'italic' }}>
            {direction}
          </p>
        </div>
      )}

      <style>{`@keyframes spin { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }`}</style>
    </div>
  );
}

const sectionLabel = {
  fontSize: 9, fontFamily: 'monospace', letterSpacing: '0.2em',
  textTransform: 'uppercase', color: 'rgba(184,134,11,0.7)', marginBottom: 10, display: 'block',
};
