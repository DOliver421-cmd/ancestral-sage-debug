import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import AppShell from "../components/AppShell";
import BackButton from "../components/BackButton";
import { api } from "../lib/api";
import { toast } from "sonner";
import { PlusCircle, X, User } from "lucide-react";

const EMPTY_SOCIAL = { platform: "", handle: "", url: "", note: "" };
const EMPTY_OFFERING = { icon: "✨", title: "", desc: "" };
const EMPTY_COMMERCE = { label: "", desc: "", url: "" };

export default function CreatorProfileEdit() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
    slug: "",
    display_name: "",
    title: "",
    tagline: "",
    bio: "",
    pronouns: "",
    location: "",
    avatar: "✨",
    socials: [],
    more_offerings: [],
    commerce: [],
  });

  useEffect(() => {
    api.get("/creator/profile/me")
      .then(r => {
        const p = r.data.profile;
        if (p) {
          setForm({
            slug: p.slug || "",
            display_name: p.display_name || "",
            title: p.title || "",
            tagline: p.tagline || "",
            bio: p.bio || "",
            pronouns: p.pronouns || "",
            location: p.location || "",
            avatar: p.avatar || "✨",
            socials: p.socials || [],
            more_offerings: p.more_offerings || [],
            commerce: p.commerce || [],
          });
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const set = (field, value) => setForm(f => ({ ...f, [field]: value }));

  function updateList(field, idx, key, val) {
    setForm(f => {
      const arr = [...f[field]];
      arr[idx] = { ...arr[idx], [key]: val };
      return { ...f, [field]: arr };
    });
  }

  function addItem(field, empty) {
    setForm(f => ({ ...f, [field]: [...f[field], { ...empty }] }));
  }

  function removeItem(field, idx) {
    setForm(f => ({ ...f, [field]: f[field].filter((_, i) => i !== idx) }));
  }

  async function save(e) {
    e.preventDefault();
    if (!form.slug.trim() || !form.display_name.trim()) {
      toast.error("Profile URL and display name are required.");
      return;
    }
    if (!/^[a-z0-9-]+$/.test(form.slug)) {
      toast.error("Profile URL may only contain lowercase letters, numbers, and hyphens.");
      return;
    }
    setSaving(true);
    try {
      await api.put("/creator/profile", form);
      toast.success("Profile saved.");
      navigate(`/creator/${form.slug}`);
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Save failed.");
    } finally {
      setSaving(false);
    }
  }

  if (loading) return (
    <AppShell>
      <div className="p-10 text-ink/50 text-sm">Loading…</div>
    </AppShell>
  );

  return (
    <AppShell>
      <div className="px-6 py-10 max-w-3xl">
        <BackButton className="mb-4" />
        <div className="overline text-copper mb-1">Creator Studio</div>
        <h1 className="font-heading text-4xl font-bold text-ink mb-2">Edit Creator Profile</h1>
        <p className="text-ink/60 mb-8">Your public profile at <span className="font-mono text-copper">/creator/{form.slug || "your-slug"}</span></p>

        <form onSubmit={save} className="space-y-8">

          {/* Core info */}
          <Section title="Identity">
            <Field label="Profile URL slug *" hint="lowercase letters, numbers, hyphens only — e.g. nam-oshun">
              <input
                className="input w-full font-mono"
                value={form.slug}
                onChange={e => set("slug", e.target.value.toLowerCase().replace(/[^a-z0-9-]/g, "").slice(0, 80))}
                placeholder="your-name"
                required
              />
            </Field>
            <Field label="Display Name *">
              <input className="input w-full" value={form.display_name} onChange={e => set("display_name", e.target.value)} maxLength={100} required />
            </Field>
            <div className="grid grid-cols-2 gap-4">
              <Field label="Title / Role">
                <input className="input w-full" value={form.title} onChange={e => set("title", e.target.value)} maxLength={200} placeholder="Poet · Artist · Organizer" />
              </Field>
              <Field label="Pronouns">
                <input className="input w-full" value={form.pronouns} onChange={e => set("pronouns", e.target.value)} maxLength={50} placeholder="he/him" />
              </Field>
            </div>
            <Field label="Location">
              <input className="input w-full" value={form.location} onChange={e => set("location", e.target.value)} maxLength={100} placeholder="City, State" />
            </Field>
            <Field label="Avatar emoji">
              <input className="input w-24" value={form.avatar} onChange={e => set("avatar", e.target.value)} maxLength={10} placeholder="🌊" />
            </Field>
            <Field label="Tagline">
              <input className="input w-full" value={form.tagline} onChange={e => set("tagline", e.target.value)} maxLength={300} placeholder="Words that heal. Community that holds." />
            </Field>
            <Field label="Bio">
              <textarea className="input w-full h-48 resize-none" value={form.bio} onChange={e => set("bio", e.target.value)} maxLength={5000} placeholder="Tell your story…" />
            </Field>
          </Section>

          {/* Social links */}
          <Section title="Social Links">
            {form.socials.map((s, i) => (
              <div key={i} className="border border-ink/10 rounded-xl p-4 space-y-2">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-bold text-ink/50">Link {i + 1}</span>
                  <button type="button" onClick={() => removeItem("socials", i)} className="text-ink/30 hover:text-destructive"><X className="w-4 h-4" /></button>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <input className="input text-sm" value={s.platform} onChange={e => updateList("socials", i, "platform", e.target.value)} placeholder="Platform" maxLength={100} />
                  <input className="input text-sm" value={s.handle} onChange={e => updateList("socials", i, "handle", e.target.value)} placeholder="@handle" maxLength={100} />
                </div>
                <input className="input w-full text-sm" value={s.url} onChange={e => updateList("socials", i, "url", e.target.value)} placeholder="https://..." maxLength={500} />
                <input className="input w-full text-sm" value={s.note} onChange={e => updateList("socials", i, "note", e.target.value)} placeholder="Short note (optional)" maxLength={300} />
              </div>
            ))}
            <AddButton onClick={() => addItem("socials", EMPTY_SOCIAL)} label="Add Social Link" />
          </Section>

          {/* M.O.R.E. offerings */}
          <Section title="What You Offer (M.O.R.E.)">
            {form.more_offerings.map((o, i) => (
              <div key={i} className="border border-ink/10 rounded-xl p-4 space-y-2">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-bold text-ink/50">Offering {i + 1}</span>
                  <button type="button" onClick={() => removeItem("more_offerings", i)} className="text-ink/30 hover:text-destructive"><X className="w-4 h-4" /></button>
                </div>
                <div className="flex gap-3">
                  <input className="input w-16 text-center" value={o.icon} onChange={e => updateList("more_offerings", i, "icon", e.target.value)} placeholder="✨" maxLength={10} />
                  <input className="input flex-1" value={o.title} onChange={e => updateList("more_offerings", i, "title", e.target.value)} placeholder="Title" maxLength={200} />
                </div>
                <textarea className="input w-full h-20 resize-none text-sm" value={o.desc} onChange={e => updateList("more_offerings", i, "desc", e.target.value)} placeholder="Description…" maxLength={1000} />
              </div>
            ))}
            <AddButton onClick={() => addItem("more_offerings", EMPTY_OFFERING)} label="Add Offering" />
          </Section>

          {/* Commerce / products */}
          <Section title="Products & Links">
            {form.commerce.map((c, i) => (
              <div key={i} className="border border-ink/10 rounded-xl p-4 space-y-2">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-bold text-ink/50">Item {i + 1}</span>
                  <button type="button" onClick={() => removeItem("commerce", i)} className="text-ink/30 hover:text-destructive"><X className="w-4 h-4" /></button>
                </div>
                <input className="input w-full" value={c.label} onChange={e => updateList("commerce", i, "label", e.target.value)} placeholder="Product or link label" maxLength={200} />
                <input className="input w-full text-sm" value={c.desc} onChange={e => updateList("commerce", i, "desc", e.target.value)} placeholder="Short description" maxLength={500} />
                <input className="input w-full text-sm" value={c.url} onChange={e => updateList("commerce", i, "url", e.target.value)} placeholder="https://..." maxLength={500} />
              </div>
            ))}
            <AddButton onClick={() => addItem("commerce", EMPTY_COMMERCE)} label="Add Product / Link" />
          </Section>

          <div className="flex items-center gap-4 pt-2">
            <button type="submit" disabled={saving} className="btn-copper disabled:opacity-50">
              {saving ? "Saving…" : "Save Profile"}
            </button>
            {form.slug && (
              <a href={`/creator/${form.slug}`} className="text-sm text-copper underline">
                View public profile →
              </a>
            )}
          </div>
        </form>
      </div>
    </AppShell>
  );
}

function Section({ title, children }) {
  return (
    <div>
      <div className="overline text-xs text-ink/40 mb-3">{title}</div>
      <div className="space-y-4">{children}</div>
    </div>
  );
}

function Field({ label, hint, children }) {
  return (
    <div>
      <label className="overline text-xs text-ink/50 block mb-1">{label}</label>
      {hint && <div className="text-xs text-ink/40 mb-1">{hint}</div>}
      {children}
    </div>
  );
}

function AddButton({ onClick, label }) {
  return (
    <button type="button" onClick={onClick} className="flex items-center gap-2 text-sm text-copper font-bold hover:underline mt-1">
      <PlusCircle className="w-4 h-4" /> {label}
    </button>
  );
}
