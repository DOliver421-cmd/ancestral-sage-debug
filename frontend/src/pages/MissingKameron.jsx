import { useState, useRef, useEffect } from "react";
import { api, BACKEND_URL } from "../lib/api";
import { toast } from "sonner";

const SHARE_URL = "https://www.morehelp.center/missing/kameron";
const TIP_LINE = "859-955-0421";
const STORAGE_KEY = "kameron_photo_ids";

function getStoredPhotos() {
  try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]"); } catch { return []; }
}

export default function MissingKameron() {
  const [tip, setTip] = useState("");
  const [contact, setContact] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [photos, setPhotos] = useState(getStoredPhotos);
  const [uploading, setUploading] = useState(false);
  const fileRef = useRef();

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(photos));
  }, [photos]);

  const shareText = `MISSING: Kameron McMullen, 28, special needs adult. Missing since 6/06/2026. Last seen on skateboard near 131st Ave & Fletcher & Bruce B Downs Blvd, Tampa FL. 6'2", 180 lbs. If you have seen him call ${TIP_LINE}`;

  const handleShare = (platform) => {
    const encoded = encodeURIComponent(shareText + " " + SHARE_URL);
    const urls = {
      facebook: `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(SHARE_URL)}&quote=${encoded}`,
      twitter: `https://twitter.com/intent/tweet?text=${encoded}`,
      whatsapp: `https://wa.me/?text=${encoded}`,
    };
    window.open(urls[platform], "_blank", "noopener");
  };

  const handlePhotoUpload = async (e) => {
    const files = Array.from(e.target.files || []);
    if (!files.length) return;
    setUploading(true);
    const newIds = [];
    for (const file of files) {
      try {
        const fd = new FormData();
        fd.append("file", file);
        fd.append("title", `Kameron McMullen - ${file.name}`);
        fd.append("file_type", "other");
        fd.append("is_public", "true");
        const res = await api.post("/media/upload", fd, { headers: { "Content-Type": "multipart/form-data" } });
        newIds.push(res.data.id);
        toast.success("Photo uploaded");
      } catch {
        toast.error(`Failed to upload ${file.name}`);
      }
    }
    if (newIds.length) setPhotos(prev => [...prev, ...newIds].slice(-6));
    setUploading(false);
    if (fileRef.current) fileRef.current.value = "";
  };

  const removePhoto = (id) => setPhotos(prev => prev.filter(p => p !== id));

  const handleTipSubmit = async (e) => {
    e.preventDefault();
    if (!tip.trim()) return;
    setSubmitting(true);
    try {
      await api.post("/missing/tip", { name: "Kameron McMullen", tip: tip.trim(), contact: contact.trim() });
      setSubmitted(true);
      setTip(""); setContact("");
      toast.success("Tip submitted. Thank you.");
    } catch {
      window.location.href = `mailto:youpickeddoliver@gmail.com?subject=Tip: Kameron McMullen&body=${encodeURIComponent(tip)}`;
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div style={{ background: "#fff", minHeight: "100vh", fontFamily: "system-ui, sans-serif" }}>

      {/* ALERT BANNER */}
      <div style={{ background: "#cc0000", color: "#fff", textAlign: "center", padding: "14px 20px" }}>
        <div style={{ fontSize: 22, fontWeight: 900, letterSpacing: "0.05em" }}>⚠ MISSING PERSON ALERT</div>
        <div style={{ fontSize: 13, marginTop: 4 }}>Share this page immediately — every share could save a life</div>
      </div>

      <div style={{ maxWidth: 680, margin: "0 auto", padding: "28px 20px" }}>

        {/* Header */}
        <div style={{ textAlign: "center", marginBottom: 28 }}>
          <div style={{ fontSize: 38, fontWeight: 900, color: "#cc0000", lineHeight: 1.1 }}>MISSING</div>
          <div style={{ fontSize: 22, fontWeight: 800, color: "#111", marginTop: 4 }}>Special Needs Adult</div>
        </div>

        {/* Photos */}
        <div style={{ marginBottom: 28 }}>
          {photos.length > 0 ? (
            <div style={{ display: "flex", gap: 12, flexWrap: "wrap", justifyContent: "center", marginBottom: 12 }}>
              {photos.map(id => (
                <div key={id} style={{ position: "relative" }}>
                  <img
                    src={`${BACKEND_URL}/api/media/file/${id}`}
                    alt="Kameron McMullen"
                    style={{ width: 280, height: 340, objectFit: "cover", borderRadius: 8, border: "3px solid #cc0000" }}
                    onError={e => { e.target.style.display = "none"; }}
                  />
                  <button onClick={() => removePhoto(id)} style={{ position: "absolute", top: 6, right: 6, background: "rgba(0,0,0,0.6)", color: "#fff", border: "none", borderRadius: "50%", width: 24, height: 24, cursor: "pointer", fontSize: 14, lineHeight: 1 }}>×</button>
                </div>
              ))}
            </div>
          ) : (
            <div style={{ display: "flex", gap: 16, justifyContent: "center", flexWrap: "wrap", marginBottom: 12 }}>
              {[1, 2].map(n => (
                <div key={n} style={{ background: "#f5f5f5", borderRadius: 8, width: 260, height: 320, display: "flex", alignItems: "center", justifyContent: "center", color: "#999", fontSize: 13, border: "2px dashed #cc0000" }}>
                  Photo {n} — upload below
                </div>
              ))}
            </div>
          )}

          {/* Upload button */}
          <div style={{ textAlign: "center" }}>
            <input ref={fileRef} type="file" accept="image/*" multiple className="hidden" style={{ display: "none" }} onChange={handlePhotoUpload} />
            <button
              onClick={() => fileRef.current?.click()}
              disabled={uploading}
              style={{ background: uploading ? "#999" : "#cc0000", color: "#fff", border: "none", borderRadius: 8, padding: "10px 20px", fontSize: 14, fontWeight: 700, cursor: uploading ? "not-allowed" : "pointer" }}
            >
              {uploading ? "Uploading…" : "📷 Upload Photos"}
            </button>
            {photos.length > 0 && <div style={{ fontSize: 12, color: "#888", marginTop: 6 }}>{photos.length} photo{photos.length !== 1 ? "s" : ""} uploaded — photos save to this device</div>}
          </div>
        </div>

        {/* Info card */}
        <div style={{ border: "3px solid #cc0000", borderRadius: 12, padding: 24, marginBottom: 24 }}>
          <div style={{ fontSize: 24, fontWeight: 900, color: "#cc0000", marginBottom: 4 }}>Kameron McMullen</div>
          <div style={{ fontSize: 16, fontWeight: 700, marginBottom: 16 }}>Missing Since: June 6, 2026</div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px 24px", fontSize: 15 }}>
            <div><span style={{ fontWeight: 700 }}>DOB:</span> December 5, 1998</div>
            <div><span style={{ fontWeight: 700 }}>Age:</span> 28</div>
            <div><span style={{ fontWeight: 700 }}>Race:</span> Black</div>
            <div><span style={{ fontWeight: 700 }}>Sex:</span> Male</div>
            <div><span style={{ fontWeight: 700 }}>Eyes:</span> Black</div>
            <div><span style={{ fontWeight: 700 }}>Hair:</span> Black</div>
            <div><span style={{ fontWeight: 700 }}>Weight:</span> 180 lbs</div>
            <div><span style={{ fontWeight: 700 }}>Height:</span> 6'2"</div>
          </div>
          <div style={{ marginTop: 16, padding: "12px 16px", background: "#fff3cd", borderRadius: 8, fontSize: 15, fontWeight: 600 }}>
            <span style={{ fontWeight: 800 }}>Last Seen:</span> Riding skateboard near 131st Ave &amp; Fletcher &amp; Bruce B Downs Blvd, Tampa, FL
          </div>
        </div>

        {/* Tip line */}
        <div style={{ background: "#cc0000", borderRadius: 12, padding: 20, textAlign: "center", marginBottom: 24, color: "#fff" }}>
          <div style={{ fontSize: 16, fontWeight: 700, marginBottom: 6 }}>If you have seen Kameron — contact our tip hotline</div>
          <a href={`tel:${TIP_LINE}`} style={{ fontSize: 32, fontWeight: 900, color: "#fff", textDecoration: "none", letterSpacing: "0.05em" }}>
            {TIP_LINE}
          </a>
          <div style={{ fontSize: 13, marginTop: 6, opacity: 0.9 }}>Leave a message. Anonymous tips accepted.</div>
        </div>

        {/* Share buttons */}
        <div style={{ marginBottom: 28 }}>
          <div style={{ fontSize: 16, fontWeight: 800, marginBottom: 12, textAlign: "center" }}>📢 Share Immediately</div>
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap", justifyContent: "center" }}>
            <button onClick={() => handleShare("facebook")} style={{ background: "#1877f2", color: "#fff", border: "none", borderRadius: 8, padding: "12px 20px", fontSize: 15, fontWeight: 700, cursor: "pointer" }}>Share on Facebook</button>
            <button onClick={() => handleShare("twitter")} style={{ background: "#000", color: "#fff", border: "none", borderRadius: 8, padding: "12px 20px", fontSize: 15, fontWeight: 700, cursor: "pointer" }}>Share on X/Twitter</button>
            <button onClick={() => handleShare("whatsapp")} style={{ background: "#25d366", color: "#fff", border: "none", borderRadius: 8, padding: "12px 20px", fontSize: 15, fontWeight: 700, cursor: "pointer" }}>Share on WhatsApp</button>
            <button onClick={() => { navigator.clipboard.writeText(SHARE_URL); toast.success("Link copied!"); }} style={{ background: "#555", color: "#fff", border: "none", borderRadius: 8, padding: "12px 20px", fontSize: 15, fontWeight: 700, cursor: "pointer" }}>Copy Link</button>
          </div>
        </div>

        {/* Tip form */}
        <div style={{ border: "2px solid #ddd", borderRadius: 12, padding: 24, marginBottom: 32 }}>
          <div style={{ fontSize: 18, fontWeight: 800, marginBottom: 4 }}>Submit a Tip</div>
          <div style={{ fontSize: 13, color: "#666", marginBottom: 16 }}>Anonymous tips are welcome. Any information helps.</div>
          {submitted ? (
            <div style={{ background: "#d4edda", border: "1px solid #c3e6cb", borderRadius: 8, padding: 16, color: "#155724", fontWeight: 600 }}>
              ✓ Your tip has been submitted. Thank you for helping find Kameron.
            </div>
          ) : (
            <form onSubmit={handleTipSubmit}>
              <textarea value={tip} onChange={e => setTip(e.target.value)} placeholder="Describe what you saw, where, and when..." required rows={4}
                style={{ width: "100%", padding: 12, borderRadius: 8, border: "1px solid #ccc", fontSize: 14, marginBottom: 10, boxSizing: "border-box", resize: "vertical" }} />
              <input type="text" value={contact} onChange={e => setContact(e.target.value)} placeholder="Your contact info (optional — leave blank to stay anonymous)"
                style={{ width: "100%", padding: 12, borderRadius: 8, border: "1px solid #ccc", fontSize: 14, marginBottom: 12, boxSizing: "border-box" }} />
              <button type="submit" disabled={submitting || !tip.trim()} style={{ background: "#cc0000", color: "#fff", border: "none", borderRadius: 8, padding: "12px 24px", fontSize: 16, fontWeight: 700, cursor: submitting ? "not-allowed" : "pointer", opacity: submitting ? 0.7 : 1 }}>
                {submitting ? "Submitting..." : "Submit Tip"}
              </button>
            </form>
          )}
        </div>

        <div style={{ textAlign: "center", fontSize: 13, color: "#888", borderTop: "1px solid #eee", paddingTop: 20 }}>
          This page is maintained by the family of Kameron McMullen.<br />Share freely. Every share matters.
        </div>
      </div>
    </div>
  );
}
