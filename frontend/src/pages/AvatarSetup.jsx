import { useState } from "react";
import AppShell from "../components/AppShell";
import BackButton from "../components/BackButton";
import SovereignAvatar, { SOVEREIGN_AVATAR_KEY } from "../components/SovereignAvatar";
import { Crown, Upload } from "lucide-react";

// /avatar-setup — choose the photo that becomes The Sovereign's face. Stored
// client-side (localStorage) so it needs no backend; broadcast via a custom event
// so every mounted SovereignAvatar updates immediately.
export default function AvatarSetup() {
  const [preview, setPreview] = useState(() => {
    try {
      return localStorage.getItem(SOVEREIGN_AVATAR_KEY) || "";
    } catch {
      return "";
    }
  });
  const [error, setError] = useState("");
  const [saved, setSaved] = useState(false);

  const onFile = (e) => {
    const f = e.target.files?.[0];
    if (!f) return;
    if (!f.type.startsWith("image/")) {
      setError("Please choose an image file.");
      return;
    }
    if (f.size > 2 * 1024 * 1024) {
      setError("Image must be under 2 MB.");
      return;
    }
    setError("");
    setSaved(false);
    const reader = new FileReader();
    reader.onload = () => setPreview(reader.result);
    reader.readAsDataURL(f);
  };

  const save = () => {
    try {
      localStorage.setItem(SOVEREIGN_AVATAR_KEY, preview);
      window.dispatchEvent(new Event("sovereign-avatar-changed"));
      setSaved(true);
    } catch {
      setError("Could not save — the image may be too large for this device.");
    }
  };

  const clear = () => {
    try {
      localStorage.removeItem(SOVEREIGN_AVATAR_KEY);
    } catch {
      /* ignore */
    }
    setPreview("");
    setSaved(false);
    window.dispatchEvent(new Event("sovereign-avatar-changed"));
  };

  return (
    <AppShell>
      <div className="px-10 py-10 max-w-2xl">
        <BackButton className="mb-6" />
        <div className="flex items-center gap-2 overline text-copper">
          <Crown className="w-4 h-4" /> The Sovereign
        </div>
        <h1 className="font-heading text-3xl font-bold mt-2">Set The Sovereign's Face</h1>
        <p className="text-ink/60 mt-2">
          Your photo becomes The Sovereign — your clearer, sovereign self. Stored privately on this device.
        </p>

        <div className="card-flat p-8 mt-8 flex items-center gap-8">
          <SovereignAvatar size={96} name="The Sovereign" />
          <div className="flex-1">
            <label className="btn-primary text-sm inline-flex items-center gap-2 cursor-pointer">
              <Upload className="w-4 h-4" /> Choose Photo
              <input type="file" accept="image/*" onChange={onFile} className="hidden" data-testid="avatar-file" />
            </label>
            {error && <div className="text-sm text-destructive mt-3">{error}</div>}
            {saved && <div className="text-sm text-copper font-bold mt-3">Saved.</div>}
            <div className="flex gap-3 mt-4">
              <button onClick={save} disabled={!preview} className="btn-copper text-sm disabled:opacity-50" data-testid="avatar-save">
                Save
              </button>
              <button onClick={clear} className="btn-ghost text-sm" data-testid="avatar-clear">
                Remove
              </button>
            </div>
          </div>
        </div>

        {preview && (
          <div className="mt-6">
            <div className="overline text-ink/60 mb-2">Preview</div>
            <img src={preview} alt="preview" className="w-40 h-40 rounded-full object-cover border-2 border-signal" />
          </div>
        )}
      </div>
    </AppShell>
  );
}
