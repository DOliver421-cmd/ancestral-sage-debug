import { useState, useEffect, useCallback } from "react";

export const THEMES = {
  gold:    { primary: '#ffd700', glow: 'rgba(255,215,0,0.4)',    bg: '#0a0a14' },
  violet:  { primary: '#c084fc', glow: 'rgba(192,132,252,0.4)', bg: '#0d0818' },
  emerald: { primary: '#34d399', glow: 'rgba(52,211,153,0.4)',  bg: '#051a10' },
  crimson: { primary: '#f87171', glow: 'rgba(248,113,113,0.4)', bg: '#150505' },
  cyan:    { primary: '#67e8f9', glow: 'rgba(103,232,249,0.4)', bg: '#051a1a' },
};

const GLYPH_STYLES = ['geometric', 'runic', 'celestial', 'elemental'];
const BG_TEXTURES = ['blueprint', 'circuit', 'constellation', 'void'];

const DEFAULTS = { colorTheme: 'gold', glyphStyle: 'geometric', bgTexture: 'blueprint' };

export function useStudioTheme() {
  const [theme, setTheme] = useState(() => {
    try {
      const stored = JSON.parse(localStorage.getItem('studio_theme') || '{}');
      return { ...DEFAULTS, ...stored };
    } catch {
      return DEFAULTS;
    }
  });

  const updateTheme = useCallback((updates) => {
    setTheme(prev => {
      const next = { ...prev, ...updates };
      try { localStorage.setItem('studio_theme', JSON.stringify(next)); } catch {}
      return next;
    });
  }, []);

  return { theme, updateTheme, colors: THEMES[theme.colorTheme] || THEMES.gold };
}

export default function CustomizationPanel({ onClose }) {
  const { theme, updateTheme, colors } = useStudioTheme();

  return (
    <div
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
      style={{
        position: 'fixed', inset: 0, zIndex: 500,
        background: 'rgba(0,0,0,0.8)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        animation: 'cpFadeIn 0.3s ease',
      }}
    >
      <div style={{
        width: 480, maxWidth: '94vw',
        background: 'linear-gradient(160deg, #0d0d1a, #080812)',
        border: `1px solid ${colors.primary}40`,
        boxShadow: `0 0 60px ${colors.glow}`,
        padding: '32px 28px',
        position: 'relative',
        animation: 'cpSlideIn 0.35s cubic-bezier(0.23,1,0.32,1)',
      }}>
        {/* Top line */}
        <div style={{
          position: 'absolute', top: 0, left: 0, right: 0, height: 2,
          background: `linear-gradient(90deg, transparent, ${colors.primary}, transparent)`,
        }} />

        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 28 }}>
          <div>
            <div style={{ fontFamily: 'monospace', fontSize: 9, letterSpacing: '0.3em', textTransform: 'uppercase', color: `${colors.primary}99`, marginBottom: 4 }}>
              Sanctuary Customization
            </div>
            <h2 style={{ margin: 0, fontSize: 18, fontWeight: 900, color: colors.primary, fontFamily: 'Georgia, serif' }}>
              Shape Your Space
            </h2>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: 'rgba(255,255,255,0.35)', cursor: 'pointer', fontSize: 20 }}>×</button>
        </div>

        {/* Color Theme */}
        <Section label="Color Theme">
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            {Object.entries(THEMES).map(([key, t]) => (
              <button
                key={key}
                onClick={() => updateTheme({ colorTheme: key })}
                style={{
                  width: 40, height: 40, borderRadius: '50%',
                  background: `radial-gradient(circle at 35% 35%, ${t.primary}, ${t.bg})`,
                  border: theme.colorTheme === key ? `2px solid ${t.primary}` : '2px solid rgba(255,255,255,0.1)',
                  cursor: 'pointer',
                  boxShadow: theme.colorTheme === key ? `0 0 12px ${t.glow}` : 'none',
                  transition: 'all 0.2s ease',
                  position: 'relative',
                }}
                title={key}
              >
                {theme.colorTheme === key && (
                  <div style={{ position: 'absolute', inset: -4, borderRadius: '50%', border: `1px solid ${t.primary}80` }} />
                )}
              </button>
            ))}
          </div>
          <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.4)', marginTop: 6, fontFamily: 'monospace', textTransform: 'capitalize' }}>
            {theme.colorTheme}
          </div>
        </Section>

        {/* Glyph Style */}
        <Section label="Glyph Style">
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            {GLYPH_STYLES.map(style => (
              <OptionChip
                key={style}
                label={style}
                active={theme.glyphStyle === style}
                onClick={() => updateTheme({ glyphStyle: style })}
                activeColor={colors.primary}
              />
            ))}
          </div>
        </Section>

        {/* Background Texture */}
        <Section label="Background Texture">
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            {BG_TEXTURES.map(tex => (
              <OptionChip
                key={tex}
                label={tex}
                active={theme.bgTexture === tex}
                onClick={() => updateTheme({ bgTexture: tex })}
                activeColor={colors.primary}
              />
            ))}
          </div>
        </Section>

        <button
          onClick={onClose}
          style={{
            marginTop: 8, width: '100%',
            background: `linear-gradient(135deg, ${colors.primary}cc, ${colors.primary})`,
            border: 'none', color: '#050508',
            fontFamily: 'monospace', fontWeight: 900,
            fontSize: 12, letterSpacing: '0.15em', textTransform: 'uppercase',
            padding: '12px', cursor: 'pointer',
            boxShadow: `0 4px 0 ${colors.primary}40`,
          }}
        >
          Apply & Close
        </button>
      </div>

      <style>{`
        @keyframes cpFadeIn { from{opacity:0} to{opacity:1} }
        @keyframes cpSlideIn { from{transform:translateY(20px);opacity:0} to{transform:translateY(0);opacity:1} }
      `}</style>
    </div>
  );
}

function Section({ label, children }) {
  return (
    <div style={{ marginBottom: 22 }}>
      <div style={{
        fontFamily: 'monospace', fontSize: 9, letterSpacing: '0.2em',
        textTransform: 'uppercase', color: 'rgba(184,134,11,0.6)', marginBottom: 10,
      }}>
        {label}
      </div>
      {children}
    </div>
  );
}

function OptionChip({ label, active, onClick, activeColor }) {
  return (
    <button
      onClick={onClick}
      style={{
        background: active ? `${activeColor}22` : 'rgba(255,255,255,0.04)',
        border: `1px solid ${active ? activeColor : 'rgba(255,255,255,0.12)'}`,
        color: active ? activeColor : 'rgba(255,255,255,0.55)',
        padding: '5px 12px',
        fontFamily: 'monospace', fontSize: 11,
        fontWeight: active ? 900 : 400,
        cursor: 'pointer', textTransform: 'capitalize',
        letterSpacing: '0.05em',
        transition: 'all 0.2s ease',
        boxShadow: active ? `0 0 8px ${activeColor}40` : 'none',
      }}
    >
      {label}
    </button>
  );
}
