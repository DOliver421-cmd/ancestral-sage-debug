import { useState, useEffect, useCallback } from "react";
import { Dialog, DialogContent, DialogTitle, DialogDescription } from "./ui/dialog";
import { Loader2, X } from "lucide-react";

export default function CheckoutModal({ url, onClose }) {
  const [status, setStatus] = useState("loading"); // loading | success | cancel | error
  const [msg, setMsg] = useState("");

  const checkSuccess = useCallback(async () => {
    try {
      const { data } = await fetch("/api/auth/me", {
        headers: { "Authorization": `Bearer ${localStorage.getItem("token")}` },
      }).then(r => r.json());
      const tier = data?.feature_tier || "";
      if (tier && tier !== "free") {
        setStatus("success");
        setMsg(`Payment successful — ${tier} tier activated.`);
        setTimeout(onClose, 2000);
      }
    } catch {}
  }, [onClose]);

  useEffect(() => {
    if (!url) return;
    setStatus("loading");
    const interval = setInterval(checkSuccess, 2000);
    return () => clearInterval(interval);
  }, [url, checkSuccess]);

  if (!url) return null;

  return (
    <Dialog open={!!url} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-4xl w-[95vw] h-[85vh] p-0 gap-0">
        <div className="flex items-center justify-between px-4 py-3 border-b border-ink/10">
          <div>
            <DialogTitle className="text-sm font-bold">Secure Checkout</DialogTitle>
            <DialogDescription className="text-xs text-ink/50">
              Complete your purchase below. You will not leave this site.
            </DialogDescription>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded hover:bg-ink/10 text-ink/50 hover:text-ink"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
        <div className="flex-1 relative bg-white">
          {status === "loading" && (
            <div className="absolute inset-0 flex items-center justify-center bg-ink/5 z-10">
              <Loader2 className="w-6 h-6 animate-spin text-copper" />
            </div>
          )}
          {status === "success" && (
            <div className="absolute inset-0 flex items-center justify-center bg-green-50 z-10">
              <div className="text-center">
                <div className="text-green-600 font-bold text-lg">{msg}</div>
                <div className="text-sm text-green-700 mt-1">Closing…</div>
              </div>
            </div>
          )}
          {status === "cancel" && (
            <div className="absolute inset-0 flex items-center justify-center bg-ink/5 z-10">
              <div className="text-center">
                <div className="text-ink font-bold">Checkout cancelled</div>
                <button onClick={onClose} className="text-sm text-copper mt-2">Close</button>
              </div>
            </div>
          )}
          <iframe
            src={url}
            title="Secure Checkout"
            className="w-full h-full border-0"
            allow="payment"
            onLoad={() => setStatus("loading")}
          />
        </div>
      </DialogContent>
    </Dialog>
  );
}
