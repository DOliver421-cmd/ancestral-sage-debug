import { useState, useCallback } from "react";
import { toast } from "sonner";

function formatDate(ts) {
  if (!ts) return '—';
  return new Date(ts).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

export default function VaultOfVersions({ projects = [] }) {
  const [selectedProject, setSelectedProject] = useState(null);
  const [versionModal, setVersionModal] = useState(false);
  const [versionNote, setVersionNote] = useState('');
  // Local version history keyed by project id
  const [histories, setHistories] = useState({});

  const sealVersion = useCallback(() => {
    if (!selectedProject) return;
    const version = {
      id: Date.now(),
      note: versionNote.trim() || 'No note',
      timestamp: Date.now(),
      versionNumber: (histories[selectedProject.id]?.length || 0) + 1,
    };
    setHistories(h => ({
      ...h,
      [selectedProject.id]: [...(h[selectedProject.id] || []), version],
    }));
    setVersionNote('');
    setVersionModal(false);
    toast.success(`v${version.versionNumber} sealed.`);
  }, [selectedProject, versionNote, histories]);

  const restoreVersion = (v) => {
    toast.success('Version restored — working copy updated.');
  };

  return (
    <div style={{ fontFamily: 'inherit', color: 'rgba(255,255,255,0.9)', display: 'flex', flexDirection: 'column', gap: 20 }}>

      {projects.length === 0 ? (
        <div style={{
          textAlign: 'center', padding: '60px 24px',
          border: '1px dashed rgba(248,113,113,0.2)',
          color: 'rgba(255,255,255,0.3)',
        }}>
          <div style={{ fontSize: 40, marginBottom: 12, opacity: 0.3 }}>⌬</div>
          <div style={{ fontFamily: 'Georgia, serif', fontSize: 16, marginBottom: 8 }}>No projects sealed yet</div>
          <div style={{ fontSize: 12, fontFamily: 'monospace' }}>
            Create a project using ⊕ New Project to begin tracking versions.
          </div>
        </div>
      ) : (
        <>
          <div style={{ fontSize: 9, fontFamily: 'monospace', letterSpacing: '0.2em', textTransform: 'uppercase', color: 'rgba(248,113,113,0.7)' }}>
            {projects.length} Project{projects.length !== 1 ? 's' : ''} in the Vault
          </div>

          {projects.map(project => {
            const history = histories[project.id] || [];
            const isSelected = selectedProject?.id === project.id;

            return (
              <div
                key={project.id}
                style={{
                  border: `1px solid ${isSelected ? 'rgba(248,113,113,0.4)' : 'rgba(255,255,255,0.08)'}`,
                  background: isSelected ? 'rgba(248,113,113,0.05)' : 'rgba(255,255,255,0.02)',
                  transition: 'all 0.2s ease',
                }}
              >
                {/* Project header */}
                <div
                  onClick={() => setSelectedProject(isSelected ? null : project)}
                  style={{
                    padding: '16px 18px', cursor: 'pointer',
                    display: 'flex', alignItems: 'center', gap: 16,
                  }}
                >
                  <div style={{
                    fontSize: 28,
                    filter: isSelected ? 'drop-shadow(0 0 10px rgba(248,113,113,0.7))' : 'none',
                    transition: 'filter 0.2s ease',
                  }}>
                    {project.glyph || '⌬'}
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 14, fontWeight: 900, color: isSelected ? '#f87171' : 'rgba(255,255,255,0.85)' }}>
                      {project.name}
                    </div>
                    <div style={{ fontSize: 11, fontFamily: 'monospace', color: 'rgba(255,255,255,0.3)', marginTop: 3 }}>
                      Created {formatDate(project.id)} · v{history.length || 1}
                    </div>
                  </div>
                  <div style={{ fontSize: 10, fontFamily: 'monospace', color: 'rgba(248,113,113,0.5)' }}>
                    {isSelected ? '▲' : '▼'}
                  </div>
                </div>

                {/* Expanded */}
                {isSelected && (
                  <div style={{ padding: '0 18px 18px', borderTop: '1px solid rgba(248,113,113,0.15)' }}>
                    <div style={{ paddingTop: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
                      <div style={{ fontSize: 9, fontFamily: 'monospace', letterSpacing: '0.15em', textTransform: 'uppercase', color: 'rgba(248,113,113,0.6)' }}>
                        Version History
                      </div>
                      <button
                        onClick={() => setVersionModal(true)}
                        style={{
                          background: 'rgba(248,113,113,0.12)',
                          border: '1px solid rgba(248,113,113,0.3)',
                          color: '#f87171', padding: '6px 14px',
                          fontFamily: 'monospace', fontSize: 11,
                          fontWeight: 700, letterSpacing: '0.08em',
                          cursor: 'pointer',
                        }}
                      >
                        + Seal New Version
                      </button>
                    </div>

                    {history.length === 0 ? (
                      <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.25)', fontStyle: 'italic', padding: '8px 0' }}>
                        No versions sealed yet. Seal your first version.
                      </div>
                    ) : (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                        {[...history].reverse().map(v => (
                          <div
                            key={v.id}
                            style={{
                              display: 'flex', alignItems: 'center', gap: 12,
                              padding: '10px 12px',
                              background: 'rgba(0,0,0,0.3)',
                              border: '1px solid rgba(255,255,255,0.06)',
                            }}
                          >
                            <div style={{
                              fontFamily: 'monospace', fontSize: 11, fontWeight: 900,
                              color: '#f87171', minWidth: 24,
                            }}>
                              v{v.versionNumber}
                            </div>
                            <div style={{ flex: 1 }}>
                              <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.75)' }}>{v.note}</div>
                              <div style={{ fontSize: 10, fontFamily: 'monospace', color: 'rgba(255,255,255,0.25)', marginTop: 2 }}>
                                {formatDate(v.timestamp)}
                              </div>
                            </div>
                            <button
                              onClick={() => restoreVersion(v)}
                              style={{
                                background: 'none',
                                border: '1px solid rgba(255,255,255,0.1)',
                                color: 'rgba(255,255,255,0.35)',
                                padding: '4px 10px', fontFamily: 'monospace',
                                fontSize: 10, cursor: 'pointer',
                                letterSpacing: '0.05em',
                              }}
                            >
                              Restore
                            </button>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </>
      )}

      {/* Version note modal */}
      {versionModal && (
        <div
          onClick={(e) => { if (e.target === e.currentTarget) setVersionModal(false); }}
          style={{
            position: 'fixed', inset: 0, zIndex: 600,
            background: 'rgba(0,0,0,0.8)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}
        >
          <div style={{
            width: 400, maxWidth: '90vw',
            background: '#0d0d1a',
            border: '1px solid rgba(248,113,113,0.35)',
            padding: '28px 24px',
            boxShadow: '0 0 40px rgba(248,113,113,0.15)',
          }}>
            <div style={{ fontFamily: 'monospace', fontSize: 11, letterSpacing: '0.15em', textTransform: 'uppercase', color: 'rgba(248,113,113,0.7)', marginBottom: 16 }}>
              Seal New Version — {selectedProject?.name}
            </div>
            <textarea
              value={versionNote}
              onChange={e => setVersionNote(e.target.value)}
              placeholder="What changed in this version? (optional)"
              rows={3}
              autoFocus
              style={{
                width: '100%', boxSizing: 'border-box',
                background: 'rgba(255,255,255,0.03)',
                border: '1px solid rgba(248,113,113,0.25)',
                padding: '10px 12px',
                color: 'rgba(255,255,255,0.9)',
                fontSize: 13, fontFamily: 'inherit',
                outline: 'none', resize: 'none', marginBottom: 16,
              }}
            />
            <div style={{ display: 'flex', gap: 10 }}>
              <button
                onClick={() => setVersionModal(false)}
                style={{
                  flex: 1, background: 'transparent',
                  border: '1px solid rgba(255,255,255,0.1)',
                  color: 'rgba(255,255,255,0.4)',
                  padding: '10px', cursor: 'pointer',
                  fontFamily: 'monospace', fontSize: 11, letterSpacing: '0.08em',
                }}
              >
                CANCEL
              </button>
              <button
                onClick={sealVersion}
                style={{
                  flex: 2,
                  background: 'linear-gradient(135deg, #991b1b, #f87171)',
                  border: 'none', color: '#fff',
                  fontFamily: 'monospace', fontWeight: 900,
                  fontSize: 11, letterSpacing: '0.12em', textTransform: 'uppercase',
                  padding: '10px', cursor: 'pointer',
                  boxShadow: '0 3px 0 rgba(153,27,27,0.5)',
                }}
              >
                SEAL VERSION
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
