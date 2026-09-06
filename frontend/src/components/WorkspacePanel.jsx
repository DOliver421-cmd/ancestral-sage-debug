import { useEffect, useState } from "react";
import { Bookmark, ListChecks, StickyNote, Map, Trash2, Loader2, ExternalLink } from "lucide-react";
import { toast } from "sonner";
import { api } from "../lib/api";
import { Link } from "react-router-dom";

/**
 * WorkspacePanel — the Personal Workspace, rendered as a tab INSIDE the
 * existing UnifiedProfile page (no new route, no dead-end nav).
 *
 * Two sections over real backend collections:
 *  - Saved items  (db.saved_items)     — bookmarks from anywhere on the site
 *  - My items     (db.workspace_items) — notes, checklists, plans
 */
const KIND_ICONS = { note: StickyNote, checklist: ListChecks, plan: Map };
const KIND_LABELS = { book: "Book", course: "Course", post: "Post", product: "Product", page: "Page", chat: "Chat", plan: "Plan" };

export default function WorkspacePanel() {
  const [saved, setSaved] = useState(null);
  const [items, setItems] = useState(null);
  const [creating, setCreating] = useState(false);
  const [draft, setDraft] = useState({ kind: "note", title: "", content: "" });

  async function load() {
    try {
      const [a, b] = await Promise.all([
        api.get("/workspace/saved"),
        api.get("/workspace/items"),
      ]);
      setSaved(a.data.items || []);
      setItems(b.data.items || []);
    } catch {
      toast.error("Could not load your workspace");
      setSaved([]);
      setItems([]);
    }
  }
  useEffect(() => { load(); }, []);

  async function removeSaved(id) {
    try { await api.delete(`/workspace/saved/${id}`); setSaved(s => s.filter(x => x.id !== id)); }
    catch { toast.error("Could not remove"); }
  }

  async function removeItem(id) {
    try { await api.delete(`/workspace/items/${id}`); setItems(s => s.filter(x => x.id !== id)); }
    catch { toast.error("Could not remove"); }
  }

  async function createItem(e) {
    e.preventDefault();
    if (!draft.title.trim()) { toast.error("Give it a title"); return; }
    try {
      const { data } = await api.post("/workspace/items", {
        kind: draft.kind,
        title: draft.title.trim(),
        content: draft.kind === "note" ? draft.content.trim() || null : null,
        items: draft.kind === "checklist"
          ? draft.content.split("\n").map(t => t.trim()).filter(Boolean).map(text => ({ text, done: false }))
          : null,
        steps: draft.kind === "plan"
          ? draft.content.split("\n").map(t => t.trim()).filter(Boolean)
          : null,
      });
      setItems(s => [data, ...(s || [])]);
      setDraft({ kind: "note", title: "", content: "" });
      setCreating(false);
      toast.success("Saved to your workspace");
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Could not create");
    }
  }

  if (saved === null || items === null) {
    return <div className="flex justify-center py-10"><Loader2 className="animate-spin text-copper" /></div>;
  }

  return (
    <div className="space-y-6">
      {/* ── Saved from around the site ── */}
      <section>
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-heading font-bold flex items-center gap-2"><Bookmark size={16} className="text-copper" /> Saved Items</h3>
          <span className="text-xs text-ink/40">{saved.length} saved</span>
        </div>
        {saved.length === 0 ? (
          <p className="text-sm text-ink/50 bg-white rounded-xl border border-ink/10 p-4">
            Nothing saved yet. Look for the <Bookmark size={13} className="inline text-copper" /> button on books, courses, posts, and store items — tap it to keep them here.
          </p>
        ) : (
          <ul className="bg-white rounded-xl border border-ink/10 divide-y divide-ink/5">
            {saved.map(s => (
              <li key={s.id} className="flex items-center gap-3 px-4 py-3">
                <span className="text-[10px] font-bold uppercase tracking-wide text-ink/40 w-16 shrink-0">{KIND_LABELS[s.kind] || s.kind}</span>
                <Link to={s.url} className="flex-1 text-sm font-medium text-ink hover:text-copper truncate">{s.title}</Link>
                <Link to={s.url} className="text-ink/30 hover:text-copper"><ExternalLink size={14} /></Link>
                <button onClick={() => removeSaved(s.id)} className="text-ink/30 hover:text-destructive"><Trash2 size={14} /></button>
              </li>
            ))}
          </ul>
        )}
      </section>

      {/* ── My notes / checklists / plans ── */}
      <section>
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-heading font-bold flex items-center gap-2"><StickyNote size={16} className="text-copper" /> Notes, Checklists & Plans</h3>
          <button onClick={() => setCreating(c => !c)} className="text-sm font-bold text-copper hover:underline">
            {creating ? "Cancel" : "+ New"}
          </button>
        </div>

        {creating && (
          <form onSubmit={createItem} className="bg-white rounded-xl border border-ink/10 p-4 mb-4 space-y-3">
            <div className="flex gap-2">
              {["note", "checklist", "plan"].map(k => (
                <button type="button" key={k} onClick={() => setDraft(d => ({ ...d, kind: k }))}
                  className={`px-3 py-1.5 rounded-full text-xs font-bold border ${draft.kind === k ? "bg-copper text-white border-copper" : "border-ink/15 text-ink/60 hover:border-copper"}`}>
                  {k.charAt(0).toUpperCase() + k.slice(1)}
                </button>
              ))}
            </div>
            <input value={draft.title} onChange={e => setDraft(d => ({ ...d, title: e.target.value }))}
              placeholder="Title" className="w-full border border-ink/15 rounded-lg px-3 py-2 text-sm" />
            <textarea value={draft.content} onChange={e => setDraft(d => ({ ...d, content: e.target.value }))}
              placeholder={draft.kind === "note" ? "Write your note…" : draft.kind === "checklist" ? "One checklist item per line…" : "One step per line, in order…"}
              rows={draft.kind === "note" ? 4 : 3}
              className="w-full border border-ink/15 rounded-lg px-3 py-2 text-sm" />
            <button className="btn-copper text-sm">Create</button>
          </form>
        )}

        {items.length === 0 && !creating ? (
          <p className="text-sm text-ink/50 bg-white rounded-xl border border-ink/10 p-4">
            Create your first note, checklist, or step-by-step plan — it lives here, tied to your account.
          </p>
        ) : (
          <div className="grid sm:grid-cols-2 gap-3">
            {items.map(it => {
              const Icon = KIND_ICONS[it.kind] || StickyNote;
              return (
                <div key={it.id} className="bg-white rounded-xl border border-ink/10 p-4 relative">
                  <div className="flex items-start gap-2">
                    <Icon size={15} className="text-copper mt-0.5 shrink-0" />
                    <div className="flex-1 min-w-0">
                      <div className="font-bold text-sm text-ink truncate">{it.title}</div>
                      <div className="text-[10px] uppercase tracking-wide text-ink/40">{it.kind}</div>
                    </div>
                    <button onClick={() => removeItem(it.id)} className="text-ink/30 hover:text-destructive"><Trash2 size={13} /></button>
                  </div>
                  {it.content && <p className="text-sm text-ink/60 mt-2 line-clamp-3 whitespace-pre-wrap">{it.content}</p>}
                  {it.steps && <ol className="mt-2 space-y-1 text-sm text-ink/60 list-decimal list-inside">
                    {it.steps.slice(0, 4).map((s, i) => <li key={i} className="truncate">{s}</li>)}
                    {it.steps.length > 4 && <li className="text-ink/40">+{it.steps.length - 4} more</li>}
                  </ol>}
                  {it.items && <ul className="mt-2 space-y-1 text-sm">
                    {it.items.slice(0, 4).map((c, i) => (
                      <li key={i} className={c.done ? "text-ink/40 line-through" : "text-ink/70"}>□ {c.text}</li>
                    ))}
                    {it.items.length > 4 && <li className="text-ink/40">+{it.items.length - 4} more</li>}
                  </ul>}
                </div>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
}
