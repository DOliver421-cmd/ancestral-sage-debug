import { useState } from "react";
import { X, Flag } from "lucide-react";
import { api } from "../lib/api";
import { toast } from "sonner";

export default function FlagModal({ targetId, targetType, onClose }) {
  const [reason, setReason] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit() {
    setSubmitting(true);
    try {
      await api.post("/more/flag", { target_id: targetId, target_type: targetType, reason: reason.trim() || "No reason given" });
      toast.success("Flagged — thank you.");
      onClose();
    } catch {
      toast.error("Could not submit flag.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md">
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100">
          <div className="flex items-center gap-2">
            <Flag className="w-4 h-4 text-red-500" />
            <h2 className="font-heading font-bold text-lg text-slate-900">Flag Content</h2>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600"><X className="w-5 h-5" /></button>
        </div>
        <div className="px-6 py-5 space-y-3">
          <p className="text-sm text-slate-600">Let us know why you're flagging this. Our moderation team reviews every report.</p>
          <textarea
            value={reason}
            onChange={e => setReason(e.target.value)}
            rows={3}
            placeholder="Describe the issue (optional)…"
            className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-copper resize-none"
            autoFocus
          />
        </div>
        <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-slate-100">
          <button onClick={onClose} className="text-sm px-4 py-2 rounded-lg text-slate-600 hover:bg-slate-50">Cancel</button>
          <button onClick={handleSubmit} disabled={submitting}
            className="flex items-center gap-2 text-sm px-5 py-2 rounded-lg bg-red-600 text-white font-bold hover:bg-red-700 disabled:opacity-50">
            <Flag className="w-3.5 h-3.5" />
            {submitting ? "Submitting…" : "Submit Report"}
          </button>
        </div>
      </div>
    </div>
  );
}
