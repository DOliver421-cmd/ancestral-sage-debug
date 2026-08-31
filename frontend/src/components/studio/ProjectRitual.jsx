import { useState, useEffect, useRef } from "react";
import { studioSound } from "./SoundSystem";

const GLYPHS = ['⬡','⊕','⌬','⟁','⍟','⎔','⊞','⊗','⊙','⊛','⋈','⌘','✦','⟐','⬢'];

function pickGlyph(name) {
  const idx = name.length % GLYPHS.length;
  return GLYPHS[idx];
}

export default function ProjectRitual({ onCreated, onClose }) {
  const [name, setName] = useState('');
  const [sealed, setSealed] = useState(false);
  const [sigil, setSigil] = useState('');
  const inputRef = useRef(null);

  useEffect(() => {
    const t = setTimeout(() => inputRef.current?.focus(), 400);
    return () => clearTimeout(t);
  }, []);

  const submit = () => {
    if (!name.trim()) return;
    const glyph = pickGlyph(name.trim());
    setSigil(glyph);
    studioSound.play('ritual_open');
    setSealed(true);

    setTimeout(() => {
      onCreated({ name: name.trim(), glyph, id: Date.now() });
    }, 1800);
  };

  const handleKey = (e) => {
    if (e.key === 'Enter') submit();
    if (e.key === 'Escape') onClose();
  };

  return (
    <div
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
      style={{
        position: 'fixed', inset: 0, zIndex: 500,
        background: 'rgba(0,0,0,0.85)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        animation: 'ritualFadeIn 0.35s ease',
      }}
    >
      {/* Scroll */}
      <div style={{
        width: 480, maxWidth: '92vw',
        background: 'linear-gradient(160deg, #0d0d1a 0%, #080812 100%)',
        border: '1px solid rgba(255,215,0,0.35)',
        boxShadow: '0 0 60px rgba(255,215,0,0.15), 0 0 120px rgba(255,215,0,0.07)',
        padding: '40px 36px',
        transformOrigin: 'top center',
        animation: 'scrollUnfurl 0.5s cubic-bezier(0.23,1,0.32,1) both',
        position: 'relative',
        overflow: 'hidden',
      }}>
        {/* Top decorative line */}
        <div style={{
          position: 'absolute', top: 0, left: 0, right: 0, height: 2,
          background: 'linear-gradient(90deg, transparent, rgba(255,215,0,0.6), transparent)',
        }} />
        {/* Bottom decorative line */}
        <div style={{
          position: 'absolute', bottom: 0, left: 0, right: 0, height: 2,
          background: 'linear-gradient(90deg, transparent, rgba(255,215,0,0.6), transparent)',
        }} />

        {!sealed ? (
          <>
            <div style={{ textAlign: 'center', marginBottom: 32 }}>
              <div style={{
                fontSize: 40, marginBottom: 12,
                filter: 'drop-shadow(0 0 16px rgba(255,215,0,0.5))',
                animation: 'glyphFloat 3s ease-in-out infinite',
              }}>✦</div>
              <div style={{
                fontFamily: 'monospace', fontSize: 10, letterSpacing: '0.3em',
                textTransform: 'uppercase', color: 'rgba(184,134,11,0.7)', marginBottom: 10,
              }}>
                New Creation
              </div>
              <h2 style={{
                fontFamily: 'Georgia, serif', fontSize: 22, fontWeight: 900,
                color: '#ffd700', margin: 0,
                textShadow: '0 0 20px rgba(255,215,0,0.3)',
              }}>
                Name Your Creation
              </h2>
              <p style={{
                color: 'rgba(255,255,255,0.5)', fontSize: 13, marginTop: 8, lineHeight: 1.6,
              }}>
                Speak its name into existence. This is your act of creation.
              </p>
            </div>

            <input
              ref={inputRef}
              value={name}
              onChange={e => setName(e.target.value)}
              onKeyDown={handleKey}
              placeholder="Name your creation..."
              maxLength={80}
              style={{
                width: '100%', boxSizing: 'border-box',
                background: 'rgba(255,255,255,0.04)',
                border: '1px solid rgba(255,215,0,0.4)',
                padding: '14px 16px',
                color: 'rgba(255,255,255,0.9)',
                fontSize: 16, fontFamily: 'Georgia, serif',
                outline: 'none',
                textAlign: 'center',
                letterSpacing: '0.03em',
                boxShadow: name ? '0 0 16px rgba(255,215,0,0.2)' : 'none',
                transition: 'box-shadow 0.3s ease',
              }}
            />

            <div style={{ display: 'flex', gap: 12, marginTop: 24 }}>
              <button
                onClick={onClose}
                style={{
                  flex: 1, background: 'transparent',
                  border: '1px solid rgba(255,255,255,0.12)',
                  color: 'rgba(255,255,255,0.4)', padding: '11px',
                  cursor: 'pointer', fontFamily: 'monospace', fontSize: 12,
                  letterSpacing: '0.1em',
                }}
              >
                CANCEL
              </button>
              <button
                onClick={submit}
                disabled={!name.trim()}
                style={{
                  flex: 2,
                  background: name.trim()
                    ? 'linear-gradient(135deg, #b8860b, #d4a017)'
                    : 'rgba(184,134,11,0.2)',
                  border: 'none',
                  color: name.trim() ? '#0a0a0f' : 'rgba(184,134,11,0.4)',
                  padding: '11px',
                  cursor: name.trim() ? 'pointer' : 'default',
                  fontFamily: 'monospace', fontSize: 12,
                  fontWeight: 900, letterSpacing: '0.15em',
                  textTransform: 'uppercase',
                  boxShadow: name.trim() ? '0 0 20px rgba(255,215,0,0.2)' : 'none',
                  transition: 'all 0.25s ease',
                }}
              >
                SEAL IT
              </button>
            </div>
          </>
        ) : (
          /* Sealed confirmation */
          <div style={{ textAlign: 'center', padding: '20px 0' }}>
            <div style={{
              fontSize: 56, marginBottom: 16,
              filter: 'drop-shadow(0 0 24px rgba(255,215,0,0.8))',
              animation: 'sigilPulse 0.8s ease-in-out infinite',
            }}>
              {sigil}
            </div>
            <h3 style={{
              fontFamily: 'Georgia, serif', fontSize: 18, color: '#ffd700',
              margin: '0 0 8px', textShadow: '0 0 20px rgba(255,215,0,0.4)',
            }}>
              {name}
            </h3>
            <div style={{
              fontFamily: 'monospace', fontSize: 12, letterSpacing: '0.2em',
              color: 'rgba(184,134,11,0.8)', textTransform: 'uppercase',
              animation: 'fadeInUp 0.4s ease 0.3s both',
            }}>
              Your work is sealed.
            </div>
          </div>
        )}
      </div>

      <style>{`
        @keyframes ritualFadeIn { from { opacity: 0 } to { opacity: 1 } }
        @keyframes scrollUnfurl { from { transform: scaleY(0.1); opacity: 0 } to { transform: scaleY(1); opacity: 1 } }
        @keyframes glyphFloat { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-6px)} }
        @keyframes sigilPulse { 0%,100%{filter:drop-shadow(0 0 16px rgba(255,215,0,0.6))} 50%{filter:drop-shadow(0 0 32px rgba(255,215,0,1))} }
        @keyframes fadeInUp { from{opacity:0;transform:translateY(8px)} to{opacity:1;transform:translateY(0)} }
      `}</style>
    </div>
  );
}
