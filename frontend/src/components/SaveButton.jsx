import { useState } from "react";
import { Bookmark, BookmarkCheck, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";

/**
 * SaveButton — universal "save to my workspace" bookmark.
 *
 *   <SaveButton kind="product" ref={product.id} title={product.title} url={`/store?product=${product.id}`} />
 *
 * kind ∈ book | course | post | product | page | chat | plan
 * Renders inline (small icon chip) so it can sit on any existing card
 * without changing layout. Signed-in users get instant save; guests get
 * a sign-in hint, never a dead button.
 */
export default function SaveButton({ kind, refId, title, url, note = null }) {
  const { user } = useAuth() || {};
  const [saved, setSaved] = useState(false);
  const [busy, setBusy] = useState(false);

  async function save(e) {
    e.preventDefault();
    e.stopPropagation();
    if (!user) {
      toast.info("Sign in to save this to your workspace");
      return;
    }
    setBusy(true);
    try {
      const { data } = await api.post("/workspace/saved", {
        kind,
        ref: String(refId),
        title: String(title).slice(0, 200),
        url,
        note,
      });
      if (data?.duplicate) {
        setSaved(true);
        toast.info("Already in your workspace");
      } else {
        setSaved(true);
        toast.success("Saved to your workspace");
      }
    } catch (err) {
      const msg = err?.response?.data?.detail || "Could not save";
      toast.error(msg);
    } finally {
      setBusy(false);
    }
  }

  return (
    <button
      onClick={save}
      disabled={busy || saved}
      title={saved ? "In your workspace" : "Save to workspace"}
      className={`flex items-center justify-center w-8 h-8 rounded-lg bg-white/90 backdrop-blur shadow-sm transition-colors ${
        saved ? "text-copper" : "text-ink/60 hover:text-copper"
      } disabled:opacity-80`}
    >
      {busy ? (
        <Loader2 size={15} className="animate-spin" />
      ) : saved ? (
        <BookmarkCheck size={15} />
      ) : (
        <Bookmark size={15} />
      )}
    </button>
  );
}
