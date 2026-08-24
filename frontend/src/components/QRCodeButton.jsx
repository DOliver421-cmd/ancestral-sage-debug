import { useState } from "react";
import QRCode from "qrcode";
import { Download, QrCode } from "lucide-react";
import { toast } from "sonner";

export default function QRCodeButton({ url, label = "QR code" }) {
  const [busy, setBusy] = useState(false);

  async function download() {
    if (!url) return;
    setBusy(true);
    try {
      const absolute = url.startsWith("http") ? url : `${window.location.origin}${url}`;
      const dataUrl = await QRCode.toDataURL(absolute, {
        width: 800,
        margin: 2,
        errorCorrectionLevel: "M",
        color: { dark: "#14120f", light: "#ffffff" },
      });
      const anchor = document.createElement("a");
      anchor.href = dataUrl;
      anchor.download = `${label.toLowerCase().replace(/[^a-z0-9]+/g, "-")}-qr.png`;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      toast.success("QR code downloaded.");
    } catch {
      toast.error("QR code could not be generated. Try again.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <button type="button" onClick={download} disabled={busy} title={`Download ${label}`} className="inline-flex items-center gap-1.5 text-xs font-bold text-copper border border-copper/40 hover:border-copper px-3 py-1.5 rounded-full transition-colors disabled:opacity-50">
      <QrCode className="w-3.5 h-3.5" />
      {busy ? "Creating…" : "Download QR"}
      {!busy && <Download className="w-3 h-3" />}
    </button>
  );
}
