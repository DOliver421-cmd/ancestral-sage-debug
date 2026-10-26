import { useState } from "react";
import { Plus, ClipboardList, Camera, Send, Phone, Accessibility } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { constructionApi } from "@/lib/construction-pm";
import { toast } from "sonner";

export default function FieldLogForm({ projectId, items = [], onLogSubmit }) {
  const [itemId, setItemId] = useState("");
  const [quantity, setQuantity] = useState("");
  const [hours, setHours] = useState("");
  const [photos, setPhotos] = useState([]);
  const [submitting, setSubmitting] = useState(false);

  const handlePhoto = (e) => {
    const files = Array.from(e.target.files || []);
    setPhotos((prev) => [...prev, ...files]);
  };

  const removePhoto = (idx) => setPhotos(photos.filter((_, i) => i !== idx));

  const submit = async (e) => {
    e.preventDefault();
    if (!itemId || !quantity || !hours) {
      toast.error("Item, quantity, and hours are required");
      return;
    }
    setSubmitting(true);
    try {
      await constructionApi.submitFieldLog(projectId, {
        item_id: itemId,
        actual_quantity_installed: Number(quantity),
        actual_hours_spent: Number(hours),
      });
      toast.success("Daily field log submitted");
      setItemId("");
      setQuantity("");
      setHours("");
      setPhotos([]);
      onLogSubmit?.();
    } catch {
      toast.error("Failed to submit field log");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="bg-white border border-ink/10 rounded-xl p-6">
      <div className="flex items-center gap-2 mb-4">
        <ClipboardList className="w-5 h-5 text-copper" />
        <h3 className="font-bold text-lg text-ink">Daily Crew Log</h3>
      </div>
      <p className="text-xs text-ink/60 mb-6">Log installed quantities, hours spent, and photo proofs from the job site.</p>

      <form onSubmit={submit} className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-xs font-bold text-ink/70 mb-1">CSI Division 26 Item</label>
            <select
              value={itemId}
              onChange={(e) => setItemId(e.target.value)}
              className="w-full border border-ink/20 rounded px-3 py-2 text-sm text-ink focus:outline-none focus:border-copper"
            >
              <option value="">Select item</option>
              {items.map((it) => (
                <option key={it.item_id} value={it.item_id}>
                  {it.csi_code} — {it.description}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs font-bold text-ink/70 mb-1">Qty Installed</label>
            <Input type="number" value={quantity} onChange={(e) => setQuantity(e.target.value)} placeholder="0" />
          </div>
          <div>
            <label className="block text-xs font-bold text-ink/70 mb-1">Hours Spent</label>
            <Input type="number" value={hours} onChange={(e) => setHours(e.target.value)} placeholder="0.0" />
          </div>
        </div>

        <div>
          <label className="block text-xs font-bold text-ink/70 mb-2">Photo Proofs</label>
          <div className="flex gap-2 mb-2">
            <input
              id="photo-upload"
              type="file"
              accept="image/*"
              multiple
              onChange={handlePhoto}
              className="sr-only"
            />
            <Button size="sm" variant="outline" onClick={() => document.getElementById("photo-upload")?.click()} className="flex items-center gap-2 text-sm">
              <Plus className="w-3 h-3" /> Add photos
            </Button>
          </div>
          <div className="flex gap-2">
            {photos.map((file, idx) => (
              <div key={idx} className="flex items-center gap-2 px-2 py-1.5 bg-ink/5 rounded border border-ink/10">
                <span className="text-xs text-ink/60 truncate max-w-[140px]">{file.name}</span>
                <Button variant="ghost" size="sm" onClick={() => removePhoto(idx)} className="h-6 w-6 p-0 text-ink/50 hover:text-red-600">
                  <span className="w-3 h-3">×</span>
                </Button>
              </div>
            ))}
          </div>
        </div>

        <div className="pt-2 flex items-center gap-3 text-xs text-ink/60">
          <span className="flex items-center gap-1">
            <Phone className="w-3 h-3 text-green-600" />
            Mobile-ready — works offline, syncs on reconnect
          </span>
        </div>

        <Button type="submit" disabled={submitting} className="w-full bg-copper text-white font-bold py-3 hover:bg-copper/90 disabled:opacity-60 flex items-center justify-center gap-2">
          {submitting ? "Submitting…" : "Submit Field Log"}
          <Send className="w-4 h-4" />
        </Button>
      </form>
    </div>
  );
}
