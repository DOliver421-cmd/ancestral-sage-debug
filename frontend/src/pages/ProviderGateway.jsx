import { useState, useEffect, useCallback } from "react";
import { api } from "../lib/api";
import { toast } from "sonner";
import { CheckCircle, XCircle, ExternalLink, Key, RefreshCw, Activity, Loader2 } from "lucide-react";

// ── 6 preset free providers ────────────────────────────────────────────────────
const PRESETS = [
  {
    type:     "groq",
    name:     "Groq",
    model:    "Llama 3.3 70B",
    badge:    "Tier 1 · Fastest",
    cost:     "Free",
    note:     "Best starting point. Fastest inference, no rate limits in practice.",
    signup:   "https://console.groq.com",
    signupLabel: "Get free key at console.groq.com",
    color:    "#f97316",
  },
  {
    type:     "cerebras",
    name:     "Cerebras",
    model:    "Llama 3.3 70B",
    badge:    "Tier 1 · Very Fast",
    cost:     "Free",
    note:     "Hardware-accelerated inference. Free with account.",
    signup:   "https://cloud.cerebras.ai",
    signupLabel: "Get free key at cloud.cerebras.ai",
    color:    "#8b5cf6",
  },
  {
    type:     "gemini",
    name:     "Google Gemini",
    model:    "Gemini 2.0 Flash",
    badge:    "Tier 2 · 1M context",
    cost:     "Free — 15 RPM",
    note:     "Large context window. Rate-limited to 15 requests/minute.",
    signup:   "https://aistudio.google.com/apikey",
    signupLabel: "Get free key at aistudio.google.com",
    color:    "#3b82f6",
  },
  {
    type:     "mistral",
    name:     "Mistral",
    model:    "Mistral Small",
    badge:    "Tier 5 · 1M tokens/mo",
    cost:     "Free — 1M tokens/month",
    note:     "European model. 1 million free tokens per month.",
    signup:   "https://console.mistral.ai",
    signupLabel: "Get free key at console.mistral.ai",
    color:    "#06b6d4",
  },
  {
    type:     "cohere",
    name:     "Cohere",
    model:    "Command R+",
    badge:    "Tier 4 · Tool-capable",
    cost:     "Free tier",
    note:     "Strong reasoning and tool-calling on the free tier.",
    signup:   "https://dashboard.cohere.com/api-keys",
    signupLabel: "Get free key at dashboard.cohere.com",
    color:    "#10b981",
  },
  {
    type:     "together",
    name:     "Together AI",
    model:    "Llama 3.3 70B Free",
    badge:    "Tier 6 · $25 credit",
    cost:     "Free $25 credit",
    note:     "Free credit on signup. Llama 3.3 70B free model always available.",
    signup:   "https://api.together.xyz/settings/api-keys",
    signupLabel: "Get free key at api.together.xyz",
    color:    "#f59e0b",
  },
];

function ProviderCard({ preset, status, onSave, saving }) {
  const [key, setKey] = useState("");
  const [showInput, setShowInput] = useState(false);
  const configured = status?.configured;

  const handleSave = async () => {
    if (!key.trim()) { toast.error("Paste your API key first"); return; }
    await onSave(preset.type, key.trim());
    setKey("");
    setShowInput(false);
  };

  return (
    <div className="bg-white border border-ink/10 rounded-2xl p-5 flex flex-col gap-3"
      style={{ borderLeft: `3px solid ${preset.color}` }}>
      {/* Header */}
      <div className="flex items-start justify-between gap-2">
        <div>
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-heading font-bold text-ink">{preset.name}</span>
            <span className="text-xs text-ink/40">{preset.model}</span>
            <span className="text-xs font-semibold px-2 py-0.5 rounded-full"
              style={{ background: preset.color + "18", color: preset.color }}>
              {preset.badge}
            </span>
          </div>
          <div className="text-xs text-ink/50 mt-0.5">{preset.cost}</div>
        </div>
        {configured
          ? <CheckCircle className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
          : <XCircle className="w-5 h-5 text-ink/20 flex-shrink-0 mt-0.5" />}
      </div>

      <p className="text-xs text-ink/60 leading-relaxed">{preset.note}</p>

      {/* Status */}
      {configured && !showInput && (
        <div className="flex items-center justify-between">
          <span className="text-xs text-green-600 font-semibold flex items-center gap-1">
            <CheckCircle className="w-3.5 h-3.5" /> Active — {status.key_masked}
          </span>
          <button onClick={() => setShowInput(true)}
            className="text-xs text-ink/40 hover:text-copper transition-colors">
            Replace key
          </button>
        </div>
      )}

      {/* Key input */}
      {(!configured || showInput) && (
        <div className="space-y-2">
          {!showInput && (
            <a href={preset.signup} target="_blank" rel="noopener noreferrer"
              className="flex items-center gap-1.5 text-xs font-semibold text-copper hover:underline">
              <ExternalLink className="w-3 h-3" /> {preset.signupLabel}
            </a>
          )}
          <div className="flex gap-2">
            <input
              value={key}
              onChange={e => setKey(e.target.value)}
              placeholder="Paste API key here…"
              type="password"
              className="flex-1 text-xs border border-ink/20 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-copper/30 focus:border-copper font-mono"
            />
            <button onClick={handleSave} disabled={saving || !key.trim()}
              className="flex items-center gap-1.5 bg-copper text-bone text-xs font-bold px-3 py-2 rounded-lg hover:bg-copper/90 disabled:opacity-40 disabled:cursor-not-allowed whitespace-nowrap">
              {saving ? <Loader2 className="w-3 h-3 animate-spin" /> : <Key className="w-3 h-3" />}
              {saving ? "Saving…" : "Save & Activate"}
            </button>
          </div>
          {showInput && (
            <button onClick={() => { setShowInput(false); setKey(""); }}
              className="text-xs text-ink/40 hover:text-ink/70 transition-colors">
              Cancel
            </button>
          )}
        </div>
      )}
    </div>
  );
}

export default function ProviderGateway() {
  const [status, setStatus]     = useState({});
  const [usageLog, setUsageLog] = useState([]);
  const [tab, setTab]           = useState("setup");
  const [saving, setSaving]     = useState(null);
  const [loadingUsage, setLoadingUsage] = useState(false);

  const loadStatus = useCallback(async () => {
    try {
      const r = await api.get("/providers/quick-setup/status");
      setStatus(r.data);
    } catch { setStatus({}); }
  }, []);

  const loadUsage = useCallback(async () => {
    setLoadingUsage(true);
    try {
      const r = await api.get("/providers/usage-log?limit=50");
      setUsageLog(Array.isArray(r.data) ? r.data : r.data.logs || []);
    } catch { setUsageLog([]); }
    finally { setLoadingUsage(false); }
  }, []);

  useEffect(() => { loadStatus(); }, [loadStatus]);
  useEffect(() => { if (tab === "usage") loadUsage(); }, [tab, loadUsage]);

  const handleSave = async (providerType, apiKey) => {
    setSaving(providerType);
    try {
      await api.post("/providers/quick-setup", { provider_type: providerType, api_key: apiKey });
      toast.success(`${providerType} key saved and active`);
      await loadStatus();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Failed to save key");
    } finally {
      setSaving(null);
    }
  };

  const configuredCount = Object.values(status).filter(s => s?.configured).length;

  return (
    <div className="min-h-screen bg-bone">
      <div className="max-w-4xl mx-auto px-6 py-10">

        {/* Header */}
        <div className="mb-6">
          <h1 className="font-heading text-3xl font-bold text-ink">Provider Gateway</h1>
          <p className="text-ink/60 mt-1 text-sm">
            Add free API keys to power the team. Each provider is a fallback — the gateway tries them in order.
          </p>
          {configuredCount > 0 && (
            <div className="mt-3 inline-flex items-center gap-2 text-sm font-semibold text-green-700 bg-green-50 border border-green-200 rounded-full px-3 py-1">
              <CheckCircle className="w-4 h-4" />
              {configuredCount} of {PRESETS.length} providers active
            </div>
          )}
        </div>

        {/* Tabs */}
        <div className="flex gap-1 mb-6 border-b border-ink/10">
          {[["setup", "API Keys"], ["usage", "Usage Log"]].map(([id, label]) => (
            <button key={id} onClick={() => setTab(id)}
              className={`px-4 py-2 text-sm font-semibold border-b-2 transition ${tab === id ? "border-copper text-ink" : "border-transparent text-ink/50 hover:text-ink"}`}>
              {label}
            </button>
          ))}
          <button onClick={loadStatus} className="ml-auto flex items-center gap-1.5 text-xs text-ink/40 hover:text-ink/70 pb-2">
            <RefreshCw className="w-3 h-3" /> Refresh
          </button>
        </div>

        {/* Setup tab — 6 preset cards */}
        {tab === "setup" && (
          <div>
            <p className="text-xs text-ink/50 mb-5 leading-relaxed">
              Register for a free account at each service, copy the API key they give you, and paste it below.
              You don't need all 6 — one is enough to get started. Groq is recommended first.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {PRESETS.map(preset => (
                <ProviderCard
                  key={preset.type}
                  preset={preset}
                  status={status[preset.type]}
                  onSave={handleSave}
                  saving={saving === preset.type}
                />
              ))}
            </div>
            <p className="text-xs text-ink/30 mt-8 leading-relaxed">
              Keys are encrypted at rest. They are never returned in any API response.
              The gateway tries Groq first, then Cerebras, Gemini, Mistral, Cohere, Together in order.
            </p>
          </div>
        )}

        {/* Usage tab */}
        {tab === "usage" && (
          <div>
            {loadingUsage
              ? <div className="flex justify-center py-12"><Loader2 className="w-5 h-5 animate-spin text-copper" /></div>
              : usageLog.length === 0
              ? <p className="text-center text-ink/40 text-sm py-12">No usage logged yet.</p>
              : (
                <div className="space-y-2">
                  {usageLog.map((log, i) => (
                    <div key={i} className="bg-white border border-ink/10 rounded-xl px-4 py-3 flex items-center justify-between gap-4 text-sm">
                      <div className="flex items-center gap-3">
                        <Activity className="w-4 h-4 text-copper flex-shrink-0" />
                        <div>
                          <span className="font-mono text-xs text-ink/60">{log.provider_id}</span>
                          <span className={`ml-2 text-xs font-bold ${log.result === "success" ? "text-green-600" : "text-red-500"}`}>
                            {log.result}
                          </span>
                        </div>
                      </div>
                      <span className="text-xs text-ink/30 flex-shrink-0">
                        {log.created_at ? new Date(log.created_at).toLocaleString() : ""}
                      </span>
                    </div>
                  ))}
                </div>
              )
            }
          </div>
        )}
      </div>
    </div>
  );
}
