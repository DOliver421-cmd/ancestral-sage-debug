import { useState, useEffect, useCallback } from "react";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import { toast } from "sonner";

// Real platform roles (mirror src/lib/roles.js): public is rank 0 (unauthenticated),
// never a stored role.
const ALL_ROLES = ["student", "trial_pass", "instructor", "support_staff", "oversight", "admin", "executive_admin"];
// Real product tiers (mirror src/lib/tiers.js): free → member → plus → pro → patron → executive.
const ALL_TIERS = ["free", "member", "plus", "pro", "patron", "executive"];

const CATEGORY_COLORS = {
  ai: { bg: "#ede9fe", text: "#6d28d9" },
  creation: { bg: "#dbeafe", text: "#1d4ed8" },
  learning: { bg: "#d1fae5", text: "#047857" },
  community: { bg: "#fef3c7", text: "#b45309" },
  commerce: { bg: "#fce7f3", text: "#be185d" },
  wellness: { bg: "#e0e7ff", text: "#4338ca" },
  entertainment: { bg: "#fed7aa", text: "#c2410c" },
  admin: { bg: "#e5e7eb", text: "#374151" },
};

const ECOSYSTEM_ORDER = ["NAM", "CREATE", "LEARN", "COMMUNITY", "MARKETPLACE", "SANCTUARY", "MUSIC", "GAMES", "ADMIN"];

export default function FeatureControlCenter() {
  const { user } = useAuth();
  const [features, setFeatures] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState("all");
  const [search, setSearch] = useState("");
  const [saving, setSaving] = useState(null);
  const [view, setView] = useState("cards"); // "cards" | "tier-matrix" | "role-matrix"
  const [tierMatrix, setTierMatrix] = useState(null);
  const [roleMatrix, setRoleMatrix] = useState(null);
  const [lastSaved, setLastSaved] = useState(null);

  const isAdmin = user?.role === "executive_admin" || user?.role === "admin";

  const fetchFeatures = useCallback(async () => {
    try {
      const r = await api.get("/features");
      setFeatures(r.data.features || []);
      setError(null);
    } catch (err) {
      setError(err?.message || "Failed to load features");
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchTierMatrix = useCallback(async () => {
    try {
      const r = await api.get("/features/matrix/tier");
      setTierMatrix(r.data);
    } catch (err) {
      console.error("Failed to load tier matrix:", err);
    }
  }, []);

  const fetchRoleMatrix = useCallback(async () => {
    try {
      const r = await api.get("/features/matrix/role");
      setRoleMatrix(r.data);
    } catch (err) {
      console.error("Failed to load role matrix:", err);
    }
  }, []);

  useEffect(() => {
    if (isAdmin) {
      fetchFeatures();
      if (view === "tier-matrix") fetchTierMatrix();
      if (view === "role-matrix") fetchRoleMatrix();
    }
  }, [isAdmin, view, fetchFeatures, fetchTierMatrix, fetchRoleMatrix]);

  // The server is the source of truth.  After any successful write, re-read
  // everything from the API and only then update the UI — the page must never
  // trust a local guess over a server confirmation (and the matrix views must
  // not keep stale cells after a toggle).
  const refreshFromServer = useCallback(async () => {
    await fetchFeatures();
    if (view === "tier-matrix") await fetchTierMatrix();
    if (view === "role-matrix") await fetchRoleMatrix();
  }, [view, fetchFeatures, fetchTierMatrix, fetchRoleMatrix]);

  const handleToggle = async (featureId, field, value) => {
    setSaving(featureId);
    try {
      const r = await api.put(`/features/${featureId}`, { [field]: value });
      if (!r?.data?.saved) {
        throw new Error("Server did not confirm the write.");
      }
      await refreshFromServer();
      setLastSaved(featureId);
      toast.success("Saved to the database — the change is now enforced.");
    } catch (err) {
      console.error("Failed to update:", err);
      toast.error(err?.response?.data?.detail || "Could not save feature configuration — the change was NOT applied.");
    } finally {
      setSaving(null);
    }
  };

  const handleRoleToggle = async (featureId, role) => {
    const feature = features.find(f => f.feature_id === featureId);
    if (!feature) return;
    const current = feature.allowed_roles || [];
    const updated = current.includes(role)
      ? current.filter(r => r !== role)
      : [...current, role];
    setSaving(featureId);
    try {
      const r = await api.put(`/features/${featureId}`, { allowed_roles: updated });
      if (!r?.data?.saved) {
        throw new Error("Server did not confirm the write.");
      }
      await refreshFromServer();
      setLastSaved(featureId);
      toast.success("Role access saved to the database — now enforced.");
    } catch (err) {
      console.error("Failed to update:", err);
      toast.error(err?.response?.data?.detail || "Could not save role access — the change was NOT applied.");
    } finally {
      setSaving(null);
    }
  };

  const handleTierToggle = async (featureId, tier) => {
    const feature = features.find(f => f.feature_id === featureId);
    if (!feature) return;
    const current = feature.allowed_tiers || [];
    const updated = current.includes(tier)
      ? current.filter(t => t !== tier)
      : [...current, tier];
    setSaving(featureId);
    try {
      const r = await api.put(`/features/${featureId}`, { allowed_tiers: updated });
      if (!r?.data?.saved) {
        throw new Error("Server did not confirm the write.");
      }
      await refreshFromServer();
      setLastSaved(featureId);
      toast.success("Tier access saved to the database — now enforced.");
    } catch (err) {
      console.error("Failed to update:", err);
      toast.error(err?.response?.data?.detail || "Could not save tier access — the change was NOT applied.");
    } finally {
      setSaving(null);
    }
  };

  if (!isAdmin) {
    return (
      <div style={{ padding: 48, textAlign: "center" }}>
        <div style={{ fontSize: 48, marginBottom: 16 }}>🔒</div>
        <h2 style={{ fontWeight: 900, fontSize: 20, marginBottom: 8 }}>Admin Access Required</h2>
        <p style={{ color: "#000", fontSize: 14 }}>The Feature Control Center is only accessible to administrators.</p>
      </div>
    );
  }

  const filtered = features.filter(f => {
    if (filter !== "all" && f.category !== filter) return false;
    if (search && !f.name.toLowerCase().includes(search.toLowerCase()) && !f.feature_id.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  const categories = [...new Set(features.map(f => f.category))];

  return (
      <div style={{ maxWidth: 1200, margin: "0 auto", padding: "24px 32px", backgroundColor: "#fff", color: "#000" }}>
        {/* Header */}
        <div style={{ marginBottom: 32 }}>
          <h1 style={{ fontSize: 28, fontWeight: 900, marginBottom: 4 }}>
            Feature Control Center
          </h1>
          <p style={{ color: "#000", fontSize: 14 }}>
            Configure access for every platform feature. One feature = one control record.
            {lastSaved && <span style={{ marginLeft: 12, color: "#047857", fontWeight: 700 }}>● Changes saved</span>}
          </p>
          <div style={{ marginTop: 12, padding: "12px 16px", background: "#fef3c7", border: "1px solid #f59e0b", borderRadius: 8, fontSize: 13, lineHeight: 1.5 }}>
            <strong>AI funding policy (owner decision):</strong> platform-funded AI is for{" "}
            <strong>admin / executive_admin staff only</strong>. Customers at any tier get no platform-funded
            AI — their AI runs on their own BYOK key, or they receive the keyword knowledge base.
            The gateway enforces this before any provider call; this toggle configures feature access,
            not AI funding. See BUSINESS_ACCESS_POLICY.md §7A.
          </div>
        </div>

        {/* Stats */}
        <div style={{ display: "flex", gap: 16, marginBottom: 24, flexWrap: "wrap" }}>
          <StatCard label="Total Features" value={features.length} color="#6d28d9" />
          <StatCard label="AI Features" value={features.filter(f => f.category === "ai").length} color="#1d4ed8" />
          <StatCard label="Cost Bearing" value={features.filter(f => f.cost_bearing).length} color="#b45309" />
          <StatCard label="Internal Only" value={features.filter(f => f.internal_only).length} color="#dc2626" />
          <StatCard label="Customer Accessible" value={features.filter(f => f.customer_access_allowed !== false).length} color="#047857" />
        </div>

        {/* View Toggle + Filters */}
        <div style={{ display: "flex", gap: 12, marginBottom: 24, alignItems: "center", flexWrap: "wrap" }}>
          <div style={{ display: "flex", gap: 4, background: "#f3f4f6", borderRadius: 8, padding: 3 }}>
            {["cards", "tier-matrix", "role-matrix"].map(v => (
              <button key={v} onClick={() => setView(v)}
                style={{
                  padding: "6px 14px", borderRadius: 6, border: "none", cursor: "pointer", fontSize: 12, fontWeight: 700,
                  background: view === v ? "#fff" : "transparent",
                  color: view === v ? "#1a1a1a" : "#666",
                  boxShadow: view === v ? "0 1px 3px rgba(0,0,0,0.1)" : "none",
                }}>
                {v === "cards" ? "Feature Cards" : v === "tier-matrix" ? "Tier Matrix" : "Role Matrix"}
              </button>
            ))}
          </div>

          {view === "cards" && (
            <>
              <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
                <FilterChip label="All" active={filter === "all"} onClick={() => setFilter("all")} />
                {categories.map(c => (
                  <FilterChip key={c} label={c} active={filter === c} onClick={() => setFilter(c)}
                    color={CATEGORY_COLORS[c]} />
                ))}
              </div>
              <input
                type="text"
                placeholder="Search features..."
                value={search}
                onChange={e => setSearch(e.target.value)}
                style={{
                  padding: "6px 12px", border: "1px solid #e5e7eb", borderRadius: 6,
                  fontSize: 13, width: 200, marginLeft: "auto",
                }}
              />
            </>
          )}
        </div>

        {/* Content */}
        {loading ? (
          <div style={{ padding: 48, textAlign: "center", color: "#000" }}>Loading features...</div>
        ) : error ? (
          <div style={{ padding: 48, textAlign: "center", color: "#dc2626" }}>{error}</div>
        ) : view === "cards" ? (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(500px, 1fr))", gap: 16 }}>
            {filtered.map(f => (
              <FeatureCard
                key={f.feature_id}
                feature={f}
                saving={saving === f.feature_id}
                onToggle={handleToggle}
                onRoleToggle={handleRoleToggle}
                onTierToggle={handleTierToggle}
              />
            ))}
          </div>
        ) : view === "tier-matrix" && tierMatrix ? (
          <MatrixView
            matrix={tierMatrix.matrix}
            columns={tierMatrix.tiers}
            columnType="tier"
            onToggle={(featureId, col) => {
              const feature = features.find(f => f.feature_id === featureId);
              if (!feature) return;
              handleTierToggle(featureId, col);
            }}
          />
        ) : view === "role-matrix" && roleMatrix ? (
          <MatrixView
            matrix={roleMatrix.matrix}
            columns={roleMatrix.roles}
            columnType="role"
            onToggle={(featureId, col) => {
              handleRoleToggle(featureId, col);
            }}
          />
        ) : null}
      </div>
  );
}

function StatCard({ label, value, color }) {
  return (
    <div style={{
      background: "#fff", border: "1px solid #e5e7eb", borderRadius: 10, padding: "12px 20px",
      display: "flex", flexDirection: "column", minWidth: 140,
    }}>
      <span style={{ fontSize: 24, fontWeight: 900, color }}>{value}</span>
      <span style={{ fontSize: 11, color: "#000", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.05em" }}>{label}</span>
    </div>
  );
}

function FilterChip({ label, active, onClick, color }) {
  return (
    <button onClick={onClick} style={{
      padding: "4px 12px", borderRadius: 20, border: "none", cursor: "pointer", fontSize: 11, fontWeight: 700,
      textTransform: "uppercase", letterSpacing: "0.03em",
      background: active ? (color?.bg || "#1a1a1a") : "#f3f4f6",
      color: active ? (color?.text || "#fff") : "#666",
    }}>
      {label}
    </button>
  );
}

function FeatureCard({ feature, saving, onToggle, onRoleToggle, onTierToggle }) {
  const [expanded, setExpanded] = useState(false);
  const catColor = CATEGORY_COLORS[feature.category] || { bg: "#f3f4f6", text: "#666" };

  return (
    <div style={{
      background: "#fff", border: "1px solid #e5e7eb", borderRadius: 12, overflow: "hidden",
      opacity: saving ? 0.6 : 1, transition: "opacity 0.2s",
    }}>
      {/* Header */}
      <div style={{ padding: "16px 20px", display: "flex", alignItems: "center", gap: 12, borderBottom: expanded ? "1px solid #f3f4f6" : "none" }}>
        <div style={{
          width: 8, height: 8, borderRadius: "50%",
          background: feature.enabled ? "#22c55e" : "#ef4444",
        }} />
        <div style={{ flex: 1 }}>
          <div style={{ fontWeight: 800, fontSize: 15 }}>{feature.name}</div>
          <div style={{ fontSize: 12, color: "#000" }}>{feature.description}</div>
        </div>
        {feature.internal_only && (
          <span style={{
            background: "#fee2e2", color: "#dc2626", fontSize: 9, fontWeight: 700,
            padding: "2px 6px", borderRadius: 4, textTransform: "uppercase",
          }}>
            INTERNAL
          </span>
        )}
        {feature.cost_bearing && (
          <span style={{
            background: "#fef3c7", color: "#b45309", fontSize: 9, fontWeight: 700,
            padding: "2px 6px", borderRadius: 4, textTransform: "uppercase",
          }}>
            COST
          </span>
        )}
        {feature.public_access === true && (
          <span style={{
            background: "#e0f2fe", color: "#0369a1", fontSize: 9, fontWeight: 700,
            padding: "2px 6px", borderRadius: 4, textTransform: "uppercase",
          }}>
            PUBLIC
          </span>
        )}
        <span style={{
          background: catColor.bg, color: catColor.text, fontSize: 10, fontWeight: 700,
          padding: "2px 8px", borderRadius: 4, textTransform: "uppercase",
        }}>
          {feature.category}
        </span>
        <ToggleSwitch
          checked={feature.enabled}
          onChange={(v) => onToggle(feature.feature_id, "enabled", v)}
          disabled={saving}
        />
      </div>

      {/* Collapsed Summary */}
      {!expanded && (
        <div style={{ padding: "8px 20px", display: "flex", gap: 12, fontSize: 11, color: "#000" }}>
          <span>Route: {feature.route}</span>
          <span>·</span>
          <span>{feature.allowed_roles?.length || 0} roles</span>
          <span>·</span>
          <span>{feature.allowed_tiers?.length || 0} tiers</span>
          <span>·</span>
          <span style={{ color: feature.platform_ai ? "#047857" : "#999" }}>
            AI: {feature.platform_ai ? "ON" : "OFF"}
          </span>
          <button onClick={() => setExpanded(true)} style={{
            marginLeft: "auto", background: "none", border: "none", color: "#3b82f6",
            cursor: "pointer", fontSize: 11, fontWeight: 700,
          }}>
            Configure →
          </button>
        </div>
      )}

      {/* Expanded Config */}
      {expanded && (
        <div style={{ padding: "16px 20px" }}>
          {/* Route + API */}
          <div style={{ fontSize: 12, color: "#000", marginBottom: 16 }}>
            <div><strong>Route:</strong> {feature.route}</div>
            <div><strong>API:</strong> {(feature.api_endpoints || []).join(", ") || "—"}</div>
          </div>

          {/* Roles */}
          <div style={{ marginBottom: 16 }}>
            <div style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.05em", color: "#000", marginBottom: 8 }}>
              Allowed Roles
            </div>
            <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
              {ALL_ROLES.map(role => (
                <label key={role} style={{
                  display: "flex", alignItems: "center", gap: 4, padding: "4px 10px",
                  borderRadius: 6, border: "1px solid #e5e7eb", fontSize: 12, cursor: "pointer",
                  background: feature.allowed_roles?.includes(role) ? "#ede9fe" : "#fff",
                  color: feature.allowed_roles?.includes(role) ? "#6d28d9" : "#666",
                }}>
                  <input type="checkbox" checked={feature.allowed_roles?.includes(role) || false}
                    onChange={() => onRoleToggle(feature.feature_id, role)}
                    style={{ display: "none" }} />
                  {feature.allowed_roles?.includes(role) ? "☑" : "☐"} {role}
                </label>
              ))}
            </div>
          </div>

          {/* Tiers */}
          <div style={{ marginBottom: 16 }}>
            <div style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.05em", color: "#000", marginBottom: 8 }}>
              Allowed Tiers
            </div>
            <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
              {ALL_TIERS.map(tier => (
                <label key={tier} style={{
                  display: "flex", alignItems: "center", gap: 4, padding: "4px 10px",
                  borderRadius: 6, border: "1px solid #e5e7eb", fontSize: 12, cursor: "pointer",
                  background: feature.allowed_tiers?.includes(tier) ? "#d1fae5" : "#fff",
                  color: feature.allowed_tiers?.includes(tier) ? "#047857" : "#666",
                }}>
                  <input type="checkbox" checked={feature.allowed_tiers?.includes(tier) || false}
                    onChange={() => onTierToggle(feature.feature_id, tier)}
                    style={{ display: "none" }} />
                  {feature.allowed_tiers?.includes(tier) ? "☑" : "☐"} {tier}
                </label>
              ))}
            </div>
          </div>

          {/* Classification */}
          <div style={{ marginBottom: 16 }}>
            <div style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.05em", color: "#000", marginBottom: 8 }}>
              Classification
            </div>
            <div style={{ display: "flex", gap: 16, flexWrap: "wrap" }}>
              <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12 }}>
                <ToggleSwitch checked={feature.internal_only || false}
                  onChange={(v) => onToggle(feature.feature_id, "internal_only", v)} disabled={saving} />
                <span style={{ color: feature.internal_only ? "#dc2626" : "#666" }}>
                  {feature.internal_only ? "🔴 Internal Only" : "Internal Only"}
                </span>
              </label>
              <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12 }}>
                <ToggleSwitch checked={feature.customer_access_allowed !== false}
                  onChange={(v) => onToggle(feature.feature_id, "customer_access_allowed", v)} disabled={saving} />
                <span style={{ color: feature.customer_access_allowed ? "#047857" : "#666" }}>
                  {feature.customer_access_allowed ? "✅ Customer Access" : "Customer Access"}
                </span>
              </label>
              <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12 }}>
                <ToggleSwitch checked={feature.cost_bearing || false}
                  onChange={(v) => onToggle(feature.feature_id, "cost_bearing", v)} disabled={saving} />
                <span style={{ color: feature.cost_bearing ? "#b45309" : "#666" }}>
                  {feature.cost_bearing ? "💰 Cost Bearing" : "Cost Bearing"}
                </span>
              </label>
              <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12 }}>
                <ToggleSwitch checked={feature.public_access === true}
                  onChange={(v) => onToggle(feature.feature_id, "public_access", v)} disabled={saving} />
                <span style={{ color: feature.public_access ? "#0369a1" : "#666" }}>
                  {feature.public_access ? "🌐 Public Access" : "Public Access"}
                </span>
              </label>
            </div>
          </div>

          {/* AI Config */}
          <div style={{ display: "flex", gap: 16, marginBottom: 16 }}>
            <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12 }}>
              <ToggleSwitch checked={feature.platform_ai}
                onChange={(v) => onToggle(feature.feature_id, "platform_ai", v)} disabled={saving} />
              Platform AI
            </label>
            <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12 }}>
              <ToggleSwitch checked={feature.byok_allowed}
                onChange={(v) => onToggle(feature.feature_id, "byok_allowed", v)} disabled={saving} />
              BYOK Allowed
            </label>
            <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12 }}>
              <ToggleSwitch checked={feature.navigation_visible !== false}
                onChange={(v) => onToggle(feature.feature_id, "navigation_visible", v)} disabled={saving} />
              Visible in Nav
            </label>
          </div>

          <button onClick={() => setExpanded(false)} style={{
            background: "none", border: "none", color: "#3b82f6", cursor: "pointer",
            fontSize: 11, fontWeight: 700,
          }}>
            ← Collapse
          </button>
        </div>
      )}
    </div>
  );
}

function ToggleSwitch({ checked, onChange, disabled }) {
  return (
    <button
      onClick={() => !disabled && onChange(!checked)}
      disabled={disabled}
      style={{
        width: 36, height: 20, borderRadius: 10, border: "none", cursor: disabled ? "not-allowed" : "pointer",
        background: checked ? "#22c55e" : "#d1d5db", position: "relative", transition: "background 0.2s",
        flexShrink: 0,
      }}
    >
      <div style={{
        width: 16, height: 16, borderRadius: "50%", background: "#fff",
        position: "absolute", top: 2, left: checked ? 18 : 2,
        transition: "left 0.2s", boxShadow: "0 1px 3px rgba(0,0,0,0.2)",
      }} />
    </button>
  );
}

function MatrixView({ matrix, columns, columnType, onToggle }) {
  return (
    <div style={{ overflowX: "auto" }}>
      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
        <thead>
          <tr>
            <th style={{ textAlign: "left", padding: "8px 12px", borderBottom: "2px solid #e5e7eb", fontWeight: 800, fontSize: 12 }}>
              Feature
            </th>
            {columns.map(col => (
              <th key={col} style={{
                textAlign: "center", padding: "8px 12px", borderBottom: "2px solid #e5e7eb",
                fontWeight: 700, fontSize: 11, textTransform: "uppercase", letterSpacing: "0.03em",
                minWidth: 80,
              }}>
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {matrix.map(row => (
            <tr key={row.feature_id} style={{ borderBottom: "1px solid #f3f4f6" }}>
              <td style={{ padding: "8px 12px", fontWeight: 600 }}>{row.name}</td>
              {columns.map(col => (
                <td key={col} style={{ textAlign: "center", padding: "8px 12px" }}>
                  <button
                    onClick={() => onToggle(row.feature_id, col)}
                    style={{
                      width: 24, height: 24, borderRadius: 4, border: "1px solid #e5e7eb",
                      cursor: "pointer", fontSize: 14,
                      background: row[col] ? (columnType === "tier" ? "#d1fae5" : "#ede9fe") : "#fff",
                      color: row[col] ? (columnType === "tier" ? "#047857" : "#6d28d9") : "#ccc",
                    }}
                  >
                    {row[col] ? "✓" : ""}
                  </button>
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
