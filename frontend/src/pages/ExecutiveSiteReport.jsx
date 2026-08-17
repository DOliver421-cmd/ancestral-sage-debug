import { useState, useEffect, useCallback } from "react";
import { api } from "../lib/api";
import AppShell from "../components/AppShell";
import {
  ClipboardCheck, RefreshCw, ShieldCheck, Database, Code2, CreditCard,
  Radio, Globe, Plug, AlertTriangle, CheckCircle2, XCircle, Loader2,
} from "lucide-react";

const COPPER = "#b5651d";
const INK = "#1a1a1a";
const BONE = "#f5f0e8";

const CATEGORY_ICONS = {
  code: Code2,
  database: Database,
  security: ShieldCheck,
  integrations: Plug,
  ecommerce: CreditCard,
  edge: Radio,
  readiness: Globe,
};

const STATUS_META = {
  pass: { label: "Pass", color: "#1b7a3d", bg: "#e7f4ec", Icon: CheckCircle2 },
  warn: { label: "Warn", color: "#9a6b00", bg: "#fdf3d7", Icon: AlertTriangle },
  fail: { label: "Fail", color: "#b3261e", bg: "#fdeaea", Icon: XCircle },
};

function StatusPill({ status }) {
  const meta = STATUS_META[status] || STATUS_META.warn;
  const Icon = meta.Icon;
  return (
    <span style={{
      display: "inline-flex", alignItems: "center", gap: 5,
      background: meta.bg, color: meta.color,
      fontSize: 10, fontWeight: 800, textTransform: "uppercase",
      letterSpacing: "0.06em", padding: "2px 9px", borderRadius: 999,
    }}>
      <Icon size={11} /> {meta.label}
    </span>
  );
}

export default function ExecutiveSiteReport() {
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    setRefreshing(true);
    setError(null);
    try {
      const r = await api.get("/exec/site-report");
      setReport(r.data);
    } catch (e) {
      setError(e?.response?.data?.detail || e?.message || "Could not load the site report.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const overall = report?.overall || "loading";
  const overallColor = overall === "operational" ? "#1b7a3d" : overall === "degraded" ? "#9a6b00" : "#b3261e";
  const summary = report?.summary || { pass: 0, warn: 0, fail: 0, total: 0 };
  const score = report?.readiness_score ?? 0;

  return (
    <AppShell>
      <div style={{ maxWidth: 1020, margin: "0 auto", padding: "28px 20px" }}>
        {/* Header */}
        <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 16, flexWrap: "wrap", marginBottom: 22 }}>
          <div>
            <h1 style={{ margin: 0, fontSize: 28, fontWeight: 900, color: INK, letterSpacing: "-0.02em", display: "flex", alignItems: "center", gap: 12 }}>
              <ClipboardCheck color={COPPER} size={28} /> Executive Site Report
            </h1>
            <p style={{ margin: "6px 0 0", color: "#666", fontSize: 14, maxWidth: 640 }}>
              Full-system white-glove audit — code, database, security &amp; access control, integrations,
              ecommerce, background jobs, and public readiness. For live production review.
            </p>
          </div>
          <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 8 }}>
            <span style={{
              background: overallColor, color: "#fff", fontSize: 12, fontWeight: 800,
              textTransform: "uppercase", letterSpacing: "0.08em", padding: "6px 14px", borderRadius: 999,
            }}>
              {overall}
            </span>
            <button onClick={load} disabled={refreshing} style={{
              display: "inline-flex", alignItems: "center", gap: 8, cursor: "pointer",
              background: "transparent", color: COPPER, border: `1.5px solid ${COPPER}`,
              borderRadius: 8, padding: "8px 16px", fontWeight: 800, fontSize: 12,
              textTransform: "uppercase", letterSpacing: "0.06em",
            }}>
              {refreshing ? <Loader2 size={14} /> : <RefreshCw size={14} />} Re-run audit
            </button>
          </div>
        </div>

        {error && (
          <div style={{ background: "#fdeaea", color: "#b3261e", border: "1px solid #f5c6c0", borderRadius: 10, padding: "14px 16px", fontSize: 13, marginBottom: 20 }}>
            {error}
          </div>
        )}

        {loading && !report && (
          <div style={{ textAlign: "center", padding: "60px 0", color: "#999", fontSize: 14 }}>
            <Loader2 size={22} style={{ animation: "spin 1s linear infinite", margin: "0 auto 10px" }} />
            Running white-glove audit…
          </div>
        )}

        {report && (
          <>
            {/* Score + summary */}
            <div style={{ display: "grid", gridTemplateColumns: "220px 1fr", gap: 16, marginBottom: 22 }}>
              <div style={{ background: "#fff", border: `2px solid ${BONE}`, borderRadius: 14, padding: 22, textAlign: "center", boxShadow: "0 2px 8px rgba(26,26,26,0.05)" }}>
                <div style={{ fontSize: 11, fontWeight: 800, textTransform: "uppercase", letterSpacing: "0.08em", color: "#888", marginBottom: 6 }}>Readiness</div>
                <div style={{ fontSize: 52, fontWeight: 900, color: overallColor, lineHeight: 1 }}>{score}%</div>
                <div style={{ fontSize: 11, color: "#888", marginTop: 6 }}>{report.generated_at?.replace("T", " ").slice(0, 16)}</div>
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12 }}>
                {[["pass", "Passed"], ["warn", "Warnings"], ["fail", "Failed"]].map(([k, label]) => {
                  const meta = STATUS_META[k];
                  return (
                    <div key={k} style={{ background: "#fff", border: `2px solid ${BONE}`, borderRadius: 14, padding: 18, textAlign: "center" }}>
                      <div style={{ fontSize: 34, fontWeight: 900, color: meta.color }}>{summary[k] ?? 0}</div>
                      <div style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.06em", color: "#888" }}>{label}</div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Categories */}
            {Object.entries(report.categories || {}).map(([key, cat]) => {
              const Icon = CATEGORY_ICONS[key] || ClipboardCheck;
              const catFails = cat.items.filter((i) => i.status === "fail").length;
              const catWarns = cat.items.filter((i) => i.status === "warn").length;
              return (
                <div key={key} style={{ background: "#fff", border: `2px solid ${BONE}`, borderRadius: 14, padding: 20, marginBottom: 18, boxShadow: "0 2px 8px rgba(26,26,26,0.04)" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 4 }}>
                    <Icon size={18} color={COPPER} />
                    <h3 style={{ margin: 0, fontSize: 16, fontWeight: 800, color: INK, flex: 1 }}>{cat.label}</h3>
                    {catFails > 0 && <span style={{ fontSize: 11, fontWeight: 800, color: "#b3261e" }}>{catFails} fail</span>}
                    {catWarns > 0 && <span style={{ fontSize: 11, fontWeight: 800, color: "#9a6b00" }}>{catWarns} warn</span>}
                  </div>
                  <div style={{ marginTop: 10 }}>
                    {cat.items.map((item, i) => (
                      <div key={i} style={{
                        display: "flex", alignItems: "flex-start", gap: 12, padding: "9px 0",
                        borderBottom: i < cat.items.length - 1 ? `1px solid ${BONE}` : "none",
                      }}>
                        <StatusPill status={item.status} />
                        <div style={{ flex: 1, minWidth: 0 }}>
                          <div style={{ fontSize: 13, fontWeight: 700, color: INK }}>{item.item}</div>
                          <div style={{ fontSize: 12, color: "#777", marginTop: 1, lineHeight: 1.5 }}>{item.detail}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}

            <div style={{ background: BONE, borderRadius: 10, padding: "12px 16px", fontSize: 12, color: "#555", lineHeight: 1.6 }}>
              <ShieldCheck size={14} color={COPPER} style={{ verticalAlign: "-2px", marginRight: 6 }} />
              <strong>Executive-only.</strong> This report checks live system state and never exposes secret values —
              only whether each key or provider is configured. Generated by {report.generated_by}.
            </div>
          </>
        )}
      </div>
    </AppShell>
  );
}
