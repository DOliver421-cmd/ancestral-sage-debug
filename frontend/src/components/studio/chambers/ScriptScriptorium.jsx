import { useState, useCallback } from "react";
import { api } from "../../../lib/api";
import { toast } from "sonner";
import { Wand2, RefreshCw, Copy, Check } from "lucide-react";

const DOC_TYPES = ['Script', 'Treatment', 'Outline', 'Synopsis', 'Press Release'];

export default function ScriptScriptorium({ tier = 'base' }) {
  const [docType, setDocType] = useState('Script');
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [polished, setPolished] = useState('');
  const [loading, setLoading] = useState(false);
  const [showDiff, setShowDiff] = useState(false);
  const [accepted, setAccepted] = useState(false);
  const [copied, setCopied] = useState(false);

  const wordCount = content.trim() ? content.trim().split(/\s+/).length : 0;

  const polish = useCallback(async () => {
    if (!content.trim()) { toast.error('Write something first.'); return; }
    setLoading(true);
    setPolished('');
    setShowDiff(false);
    setAccepted(false);
    try {
      const r = await api.post('/studio/script', { type: docType, title, content });
      setPolished(r.data.polished);
      setShowDiff(true);
    } catch {
      toast.error('The Scriptorium hit a block — try again.');
    } finally {
      setLoading(false);
    }
  }, [docType, title, content]);

  const accept = () => {
    setContent(polished);
    setPolished('');
    setShowDiff(false);
    setAccepted(true);
    toast.success('AI polish accepted.');
    setTimeout(() => setAccepted(false), 2000);
  };

  const copyPolished = () => {
    navigator.clipboard?.writeText(polished).then(() => {
      setCopied(true);
      toast.success('Copied to clipboard.');
      setTimeout(() => setCopied(false), 2000);
    });
  };

  return (
    <div style={{ fontFamily: 'inherit', color: 'rgba(255,255,255,0.9)', display: 'flex', flexDirection: 'column', gap: 18 }}>

      {/* Type selector */}
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        {DOC_TYPES.map(t => (
          <button
            key={t}
            onClick={() => setDocType(t)}
            style={{
              background: docType === t ? 'rgba(103,232,249,0.15)' : 'rgba(255,255,255,0.03)',
              border: `1px solid ${docType === t ? 'rgba(103,232,249,0.5)' : 'rgba(255,255,255,0.1)'}`,
              color: docType === t ? '#67e8f9' : 'rgba(255,255,255,0.5)',
              padding: '6px 14px', fontFamily: 'monospace', fontSize: 11,
              fontWeight: docType === t ? 900 : 400,
              letterSpacing: '0.08em', cursor: 'pointer',
              transition: 'all 0.2s ease',
              boxShadow: docType === t ? '0 0 10px rgba(103,232,249,0.2)' : 'none',
            }}
          >
            {t}
          </button>
        ))}
      </div>

      {/* Title */}
      <div>
        <label style={labelStyle}>Title</label>
        <input
          value={title}
          onChange={e => setTitle(e.target.value)}
          placeholder={`${docType} title...`}
          style={inputStyle}
        />
      </div>

      {/* Editor */}
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
          <label style={labelStyle}>Content</label>
          <div style={{ fontSize: 10, fontFamily: 'monospace', color: 'rgba(255,255,255,0.3)' }}>
            {wordCount} words
          </div>
        </div>
        <textarea
          value={content}
          onChange={e => setContent(e.target.value)}
          placeholder={`Write your ${docType.toLowerCase()} here...`}
          style={{
            ...inputStyle,
            height: showDiff ? 260 : 380,
            resize: 'vertical',
            fontFamily: 'monospace',
            fontSize: 13,
            lineHeight: 1.8,
          }}
        />
      </div>

      <button
        onClick={polish}
        disabled={loading}
        style={{
          background: loading ? 'rgba(103,232,249,0.15)' : 'linear-gradient(135deg, #0e7490, #67e8f9)',
          border: 'none', color: loading ? '#67e8f9' : '#050508',
          fontFamily: 'monospace', fontWeight: 900,
          fontSize: 13, letterSpacing: '0.1em', textTransform: 'uppercase',
          padding: '11px 24px', cursor: loading ? 'default' : 'pointer',
          display: 'flex', alignItems: 'center', gap: 8, alignSelf: 'flex-start',
          boxShadow: loading ? 'none' : '0 4px 0 rgba(14,116,144,0.5)',
        }}
      >
        {loading ? <RefreshCw style={{ width: 14, height: 14, animation: 'spin 1s linear infinite' }} /> : <Wand2 style={{ width: 14, height: 14 }} />}
        {loading ? 'Polishing...' : 'AI Polish'}
      </button>

      {/* Diff view */}
      {showDiff && polished && (
        <div>
          <div style={{
            fontSize: 9, fontFamily: 'monospace', letterSpacing: '0.2em',
            textTransform: 'uppercase', color: 'rgba(103,232,249,0.7)', marginBottom: 10,
          }}>
            AI Revision — Review Changes
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            <div>
              <div style={{ fontSize: 9, fontFamily: 'monospace', letterSpacing: '0.1em', textTransform: 'uppercase', color: 'rgba(255,255,255,0.3)', marginBottom: 6 }}>Original</div>
              <textarea
                readOnly value={content}
                style={{ ...inputStyle, height: 220, fontFamily: 'monospace', fontSize: 12, lineHeight: 1.7, background: 'rgba(0,0,0,0.3)', resize: 'none', color: 'rgba(255,255,255,0.6)' }}
              />
            </div>
            <div>
              <div style={{ fontSize: 9, fontFamily: 'monospace', letterSpacing: '0.1em', textTransform: 'uppercase', color: 'rgba(103,232,249,0.6)', marginBottom: 6 }}>AI Polished</div>
              <textarea
                readOnly value={polished}
                style={{ ...inputStyle, height: 220, fontFamily: 'monospace', fontSize: 12, lineHeight: 1.7, color: '#67e8f9', background: 'rgba(103,232,249,0.04)', resize: 'none', border: '1px solid rgba(103,232,249,0.3)' }}
              />
            </div>
          </div>
          <div style={{ display: 'flex', gap: 10, marginTop: 10 }}>
            <button
              onClick={copyPolished}
              style={{
                background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.15)',
                color: 'rgba(255,255,255,0.7)', padding: '8px 16px',
                fontFamily: 'monospace', fontSize: 11, letterSpacing: '0.08em',
                cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 6,
              }}
            >
              {copied ? <Check style={{ width: 12, height: 12 }} /> : <Copy style={{ width: 12, height: 12 }} />}
              {copied ? 'Copied' : 'Copy'}
            </button>
            <button
              onClick={accept}
              style={{
                background: 'linear-gradient(135deg, #0e7490, #67e8f9)',
                border: 'none', color: '#050508',
                fontFamily: 'monospace', fontWeight: 900,
                fontSize: 11, letterSpacing: '0.1em', textTransform: 'uppercase',
                padding: '8px 20px', cursor: 'pointer',
                boxShadow: '0 2px 0 rgba(14,116,144,0.4)',
              }}
            >
              {accepted ? '✓ Accepted' : 'Accept'}
            </button>
            <button
              onClick={() => setShowDiff(false)}
              style={{
                background: 'none', border: '1px solid rgba(255,255,255,0.1)',
                color: 'rgba(255,255,255,0.35)', padding: '8px 14px',
                fontFamily: 'monospace', fontSize: 11, cursor: 'pointer',
              }}
            >
              Dismiss
            </button>
          </div>
        </div>
      )}

      <style>{`@keyframes spin { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }`}</style>
    </div>
  );
}

const labelStyle = {
  display: 'block', fontSize: 9, fontFamily: 'monospace', letterSpacing: '0.15em',
  textTransform: 'uppercase', color: 'rgba(184,134,11,0.7)', marginBottom: 6,
};
const inputStyle = {
  width: '100%', boxSizing: 'border-box',
  background: 'rgba(255,255,255,0.03)',
  border: '1px solid rgba(103,232,249,0.2)',
  padding: '9px 12px', color: 'rgba(255,255,255,0.9)',
  fontSize: 13, fontFamily: 'inherit', outline: 'none',
};
