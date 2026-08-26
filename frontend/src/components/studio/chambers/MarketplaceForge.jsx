import { useState, useEffect } from "react";
import { toast } from "sonner";
import { Package, Upload, Check, ExternalLink, Loader2 } from "lucide-react";
import { api } from "../../../lib/api";

const DROP_TYPES = [
  { id: "ebook",    label: "Ebook / Guide" },
  { id: "digital",  label: "Digital Drop" },
  { id: "audio",    label: "Beat / Track" },
  { id: "video",    label: "Video / Course" },
  { id: "merch",    label: "Merch" },
  { id: "file",     label: "Other File" },
];

/**
 * Marketplace Forge — creates REAL sellable products in the Media Store.
 * - Attach a deliverable file → the product is published live with a download.
 * - No file yet → the product is saved as a draft with an honest warning, so
 *   customers never buy something that can't be delivered.
 */
export default function MarketplaceForge() {
  const [form, setForm] = useState({ title: "", type: "ebook", price: "", description: "", tags: "" });
  const [file, setFile] = useState(null);
  const [fileUrl, setFileUrl] = useState("");
  const [uploading, setUploading] = useState(false);
  const [forging, setForging] = useState(false);
  const [drops, setDrops] = useState([]);

  const loadDrops = () => {
    api.get("/media/products/mine")
      .then(r => setDrops(Array.isArray(r.data) ? r.data : []))
      .catch(() => { /* store may be unreachable — show empty */ });
  };

  useEffect(loadDrops, []);

  const uploadFile = async (f) => {
    if (!f) return;
    setUploading(true);
    try {
      const fd = new FormData();
      fd.append("file", f, f.name);
      const up = await api.post("/media/upload", fd, { headers: { "Content-Type": "multipart/form-data" } });
      const url = up.data?.file_url || up.data?.url || up.data?.media_url;
      if (!url) throw new Error("Upload returned no URL");
      setFileUrl(url);
      toast.success("Deliverable attached — ready to forge.");
    } catch (e) {
      toast.error("Upload failed: " + (e?.response?.data?.detail || e?.message || e));
    } finally {
      setUploading(false);
    }
  };

  const forge = async () => {
    if (!form.title.trim()) { toast.error("Give the drop a title."); return; }
    setForging(true);
    try {
      const priceCents = Math.max(0, Math.round((Number(form.price) || 0) * 100));
      const product = await api.post("/media/products", {
        title: form.title.trim(),
        description: form.description.trim(),
        price_cents: priceCents,
        type: form.type,
        tags: form.tags.split(",").map(t => t.trim()).filter(Boolean),
        file_url: fileUrl,
        published: !!fileUrl, // live only when a deliverable exists
      });
      const p = product.data || {};
      if (p.published) {
        toast.success(`"${form.title}" is live in your store.`);
      } else {
        toast.info("Saved as a draft — attach the deliverable file, then publish from the store.");
      }
      setForm({ title: "", type: form.type, price: "", description: "", tags: "" });
      setFile(null);
      setFileUrl("");
      loadDrops();
    } catch (e) {
      toast.error("Forge failed: " + (e?.response?.data?.detail || e?.message || e));
    } finally {
      setForging(false);
    }
  };

  const fmt = (cents) => `$${((cents || 0) / 100).toFixed(2)}`;

  return (
    <div style={{ fontFamily: "inherit", color: "rgba(255,255,255,0.9)", display: "flex", flexDirection: "column", gap: 22 }}>
      {/* ── Forge form ── */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
        <div>
          <label style={labelStyle}>Title *</label>
          <input style={inputStyle} value={form.title} onChange={e => setForm(f => ({ ...f, title: e.target.value }))} placeholder="e.g. The 7-Day Money Reset Guide" maxLength={120} />
        </div>
        <div>
          <label style={labelStyle}>Product Type</label>
          <select style={inputStyle} value={form.type} onChange={e => setForm(f => ({ ...f, type: e.target.value }))}>
            {DROP_TYPES.map(t => <option key={t.id} value={t.id}>{t.label}</option>)}
          </select>
        </div>
        <div>
          <label style={labelStyle}>Price ($)</label>
          <input style={inputStyle} type="number" min="0" step="0.5" value={form.price} onChange={e => setForm(f => ({ ...f, price: e.target.value }))} placeholder="0.00 = free" />
        </div>
        <div>
          <label style={labelStyle}>Tags (comma separated)</label>
          <input style={inputStyle} value={form.tags} onChange={e => setForm(f => ({ ...f, tags: e.target.value }))} placeholder="healing, finance, guide" />
        </div>
      </div>
      <div>
        <label style={labelStyle}>Description</label>
        <textarea style={{ ...inputStyle, height: 64, resize: "none" }} value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))} placeholder="What is this drop? Who is it for? What do they get?" maxLength={800} />
      </div>

      {/* Deliverable file */}
      <div style={{ border: "1px solid rgba(251,146,60,0.25)", background: "rgba(251,146,60,0.04)", padding: "12px 14px" }}>
        <div style={labelStyle}>Deliverable file (PDF, WAV, MP4, ZIP…)</div>
        <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
          <label style={{ display: "inline-flex", alignItems: "center", gap: 8, cursor: "pointer", background: "rgba(251,146,60,0.12)", border: "1px solid rgba(251,146,60,0.35)", color: "#fb923c", padding: "7px 14px", fontFamily: "monospace", fontSize: 11, fontWeight: 700 }}>
            <Upload style={{ width: 12, height: 12 }} />
            {uploading ? "Uploading…" : "Attach File"}
            <input type="file" hidden onChange={e => uploadFile(e.target.files?.[0])} />
          </label>
          {fileUrl && (
            <span style={{ fontSize: 12, color: "#22c55e", fontFamily: "monospace" }}>
              <Check style={{ width: 12, height: 12, verticalAlign: "-2px" }} /> Deliverable attached
            </span>
          )}
          {!fileUrl && (
            <span style={{ fontSize: 11, color: "rgba(255,255,255,0.4)" }}>
              No file = saved as a draft until you attach one.
            </span>
          )}
        </div>
      </div>

      <button
        onClick={forge} disabled={forging || uploading}
        style={{
          alignSelf: "flex-start",
          background: forging || uploading ? "rgba(251,146,60,0.3)" : "linear-gradient(135deg, #ea580c, #fb923c)",
          border: "none", color: "#0a0a0f", fontWeight: 900, fontSize: 13,
          padding: "12px 26px", cursor: forging || uploading ? "default" : "pointer",
          letterSpacing: "0.08em", textTransform: "uppercase", fontFamily: "monospace",
          display: "flex", alignItems: "center", gap: 8,
          boxShadow: forging || uploading ? "none" : "0 4px 0 #9a3412",
        }}
      >
        {forging ? <Loader2 style={{ width: 14, height: 14, animation: "forgeSpin 1s linear infinite" }} /> : <Package style={{ width: 14, height: 14 }} />}
        {forging ? "Forging…" : "Forge Product → Store"}
      </button>

      {/* ── Existing drops ── */}
      <div>
        <div style={{ fontSize: 9, fontFamily: "monospace", letterSpacing: "0.2em", textTransform: "uppercase", color: "rgba(251,146,60,0.7)", marginBottom: 10 }}>
          Your Drops ({drops.length})
        </div>
        {drops.length === 0 ? (
          <div style={{ fontSize: 12, color: "rgba(255,255,255,0.3)", fontStyle: "italic", padding: "12px 0" }}>
            Nothing forged yet. Your store products will appear here.
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {drops.map(d => (
              <div key={d.id} style={{ display: "flex", alignItems: "center", gap: 12, padding: "10px 12px", background: "rgba(0,0,0,0.3)", border: "1px solid rgba(255,255,255,0.07)" }}>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 13, fontWeight: 900, color: d.published ? "rgba(255,255,255,0.9)" : "rgba(255,255,255,0.5)" }}>{d.title}</div>
                  <div style={{ fontSize: 10, fontFamily: "monospace", color: "rgba(255,255,255,0.3)", marginTop: 2 }}>
                    {(d.product_type || d.type || "file").toUpperCase()} · {fmt(d.price_cents)}
                  </div>
                </div>
                <span style={{
                  fontSize: 9, fontFamily: "monospace", fontWeight: 900, letterSpacing: "0.08em",
                  textTransform: "uppercase", padding: "2px 8px",
                  color: d.published ? "#22c55e" : "rgba(255,255,255,0.4)",
                  border: `1px solid ${d.published ? "rgba(34,197,94,0.4)" : "rgba(255,255,255,0.15)"}`,
                }}>
                  {d.published ? "Live" : "Draft"}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      <a
        href="/store" target="_blank" rel="noopener noreferrer"
        style={{ fontSize: 11, fontFamily: "monospace", color: "#fb923c", textDecoration: "none", display: "inline-flex", alignItems: "center", gap: 6 }}
      >
        Open your store <ExternalLink style={{ width: 11, height: 11 }} />
      </a>

      <style>{`@keyframes forgeSpin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}

const labelStyle = { display: "block", fontSize: 10, fontFamily: "monospace", letterSpacing: "0.1em", textTransform: "uppercase", color: "rgba(251,146,60,0.8)", marginBottom: 6 };
const inputStyle = { width: "100%", background: "rgba(255,255,255,0.04)", border: "1px solid rgba(251,146,60,0.25)", padding: "9px 12px", color: "rgba(255,255,255,0.9)", fontSize: 13, fontFamily: "inherit", outline: "none", borderRadius: 4, boxSizing: "border-box" };
