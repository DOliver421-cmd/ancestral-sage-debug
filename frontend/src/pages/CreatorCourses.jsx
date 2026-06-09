import { useState, useEffect } from "react";
import AppShell from "../components/AppShell";
import BackButton from "../components/BackButton";
import { api } from "../lib/api";
import { toast } from "sonner";
import { PlusCircle, BookOpen, Eye, EyeOff, Pencil, Trash2, X, CheckCircle, ChevronDown, ChevronUp, Share2 } from "lucide-react";

function shareCourse(course) {
  const url = `${window.location.origin}/courses?highlight=${course.course_id}`;
  navigator.clipboard?.writeText(url)
    .then(() => toast.success("Share link copied to clipboard"))
    .catch(() => {
      prompt("Copy this link:", url);
    });
}

const CATEGORIES = ["general", "electrical", "ai-tech", "arts-music", "workforce", "wellness", "publishing", "business"];

const EMPTY_FORM = {
  title: "",
  description: "",
  category: "general",
  price_cents: 0,
  thumbnail_url: "",
  sections: [{ title: "", content: "" }],
};

export default function CreatorCourses() {
  const [courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [saving, setSaving] = useState(false);
  const [expandedId, setExpandedId] = useState(null);
  const [deleteTarget, setDeleteTarget] = useState(null);

  useEffect(() => { loadCourses(); }, []);

  async function loadCourses() {
    setLoading(true);
    try {
      const { data } = await api.get("/creator/courses");
      setCourses(data.courses || []);
    } catch {
      toast.error("Could not load your courses.");
    } finally {
      setLoading(false);
    }
  }

  function openCreate() {
    setEditingId(null);
    setForm(EMPTY_FORM);
    setShowForm(true);
  }

  function openEdit(course) {
    setEditingId(course.course_id);
    setForm({
      title: course.title,
      description: course.description || "",
      category: course.category || "general",
      price_cents: course.price_cents || 0,
      thumbnail_url: course.thumbnail_url || "",
      sections: course.sections?.length ? course.sections : [{ title: "", content: "" }],
    });
    setShowForm(true);
  }

  function closeForm() {
    setShowForm(false);
    setEditingId(null);
    setForm(EMPTY_FORM);
  }

  function setSection(idx, field, value) {
    setForm(f => {
      const sections = [...f.sections];
      sections[idx] = { ...sections[idx], [field]: value };
      return { ...f, sections };
    });
  }

  function addSection() {
    setForm(f => ({ ...f, sections: [...f.sections, { title: "", content: "" }] }));
  }

  function removeSection(idx) {
    setForm(f => ({ ...f, sections: f.sections.filter((_, i) => i !== idx) }));
  }

  async function save() {
    if (!form.title.trim()) { toast.error("Title is required."); return; }
    const validSections = form.sections.filter(s => s.title.trim() && s.content.trim());
    const payload = {
      ...form,
      price_cents: parseInt(form.price_cents) || 0,
      sections: validSections,
    };
    setSaving(true);
    try {
      if (editingId) {
        const { data } = await api.patch(`/creator/courses/${editingId}`, payload);
        setCourses(cs => cs.map(c => c.course_id === editingId ? data.course : c));
        toast.success("Course updated.");
      } else {
        const { data } = await api.post("/creator/courses", payload);
        setCourses(cs => [data.course, ...cs]);
        toast.success("Course created as draft.");
      }
      closeForm();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Save failed.");
    } finally {
      setSaving(false);
    }
  }

  async function togglePublish(course) {
    const newStatus = course.status === "published" ? "draft" : "published";
    try {
      const { data } = await api.patch(`/creator/courses/${course.course_id}`, { status: newStatus });
      setCourses(cs => cs.map(c => c.course_id === course.course_id ? data.course : c));
      toast.success(newStatus === "published" ? "Course published." : "Course set to draft.");
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Could not update status.");
    }
  }

  async function deleteCourse(course) {
    try {
      await api.delete(`/creator/courses/${course.course_id}`);
      setCourses(cs => cs.filter(c => c.course_id !== course.course_id));
      toast.success("Course deleted.");
      setDeleteTarget(null);
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Delete failed.");
    }
  }

  const published = courses.filter(c => c.status === "published");
  const drafts = courses.filter(c => c.status === "draft");

  return (
    <AppShell>
      <div className="px-6 py-10 max-w-5xl">
        <BackButton className="mb-4" />
        <div className="flex items-center justify-between mb-2">
          <div>
            <div className="overline text-copper">Creator Studio</div>
            <h1 className="font-heading text-4xl font-bold text-ink mt-1">My Courses</h1>
          </div>
          <button onClick={openCreate} className="btn-copper flex items-center gap-2 text-sm">
            <PlusCircle className="w-4 h-4" /> New Course
          </button>
        </div>
        <p className="text-ink/60 mb-8">
          Publish courses to the WAI catalog. You keep 70% of every sale. Payouts on the 1st.
        </p>

        {/* Stats bar */}
        <div className="grid grid-cols-3 gap-4 mb-8">
          <StatCard label="Total Courses" value={courses.length} />
          <StatCard label="Published" value={published.length} accent="text-green-600" />
          <StatCard label="Drafts" value={drafts.length} />
        </div>

        {/* Form modal */}
        {showForm && (
          <div className="fixed inset-0 bg-black/50 z-50 flex items-start justify-center pt-16 px-4 overflow-y-auto">
            <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl mb-16">
              <div className="flex items-center justify-between p-6 border-b border-ink/10">
                <h2 className="font-heading font-bold text-xl">{editingId ? "Edit Course" : "Create Course"}</h2>
                <button onClick={closeForm}><X className="w-5 h-5 text-ink/50 hover:text-ink" /></button>
              </div>
              <div className="p-6 space-y-5">
                <div>
                  <label className="overline text-xs text-ink/50 block mb-1">Title *</label>
                  <input
                    className="input w-full"
                    value={form.title}
                    onChange={e => setForm(f => ({ ...f, title: e.target.value }))}
                    placeholder="e.g. Electrical Safety Fundamentals"
                    maxLength={200}
                  />
                </div>
                <div>
                  <label className="overline text-xs text-ink/50 block mb-1">Description</label>
                  <textarea
                    className="input w-full h-24 resize-none"
                    value={form.description}
                    onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
                    placeholder="What will students learn?"
                    maxLength={2000}
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="overline text-xs text-ink/50 block mb-1">Category</label>
                    <select
                      className="input w-full"
                      value={form.category}
                      onChange={e => setForm(f => ({ ...f, category: e.target.value }))}
                    >
                      {CATEGORIES.map(c => (
                        <option key={c} value={c}>{c.replace("-", " & ").replace(/\b\w/g, l => l.toUpperCase())}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="overline text-xs text-ink/50 block mb-1">Price (USD)</label>
                    <div className="relative">
                      <span className="absolute left-3 top-1/2 -translate-y-1/2 text-ink/50 text-sm">$</span>
                      <input
                        type="number"
                        min="0"
                        max="999"
                        step="1"
                        className="input w-full pl-7"
                        value={(parseInt(form.price_cents) || 0) / 100}
                        onChange={e => setForm(f => ({ ...f, price_cents: Math.round(parseFloat(e.target.value) * 100) || 0 }))}
                        placeholder="0 = free"
                      />
                    </div>
                  </div>
                </div>
                <div>
                  <label className="overline text-xs text-ink/50 block mb-1">Thumbnail URL (optional)</label>
                  <input
                    className="input w-full"
                    value={form.thumbnail_url}
                    onChange={e => setForm(f => ({ ...f, thumbnail_url: e.target.value }))}
                    placeholder="https://..."
                    maxLength={500}
                  />
                </div>

                {/* Sections */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <label className="overline text-xs text-ink/50">Sections</label>
                    <button onClick={addSection} className="text-xs text-copper font-bold hover:underline">+ Add Section</button>
                  </div>
                  <div className="space-y-3">
                    {form.sections.map((sec, idx) => (
                      <div key={idx} className="border border-ink/10 rounded-xl p-4 space-y-2">
                        <div className="flex items-center gap-2">
                          <input
                            className="input flex-1 text-sm"
                            value={sec.title}
                            onChange={e => setSection(idx, "title", e.target.value)}
                            placeholder={`Section ${idx + 1} title`}
                            maxLength={200}
                          />
                          {form.sections.length > 1 && (
                            <button onClick={() => removeSection(idx)} className="text-ink/30 hover:text-destructive">
                              <X className="w-4 h-4" />
                            </button>
                          )}
                        </div>
                        <textarea
                          className="input w-full h-28 resize-none text-sm"
                          value={sec.content}
                          onChange={e => setSection(idx, "content", e.target.value)}
                          placeholder="Section content — lessons, instructions, resources..."
                          maxLength={20000}
                        />
                      </div>
                    ))}
                  </div>
                </div>
              </div>
              <div className="flex items-center justify-end gap-3 p-6 border-t border-ink/10">
                <button onClick={closeForm} className="btn-ghost text-sm">Cancel</button>
                <button onClick={save} disabled={saving} className="btn-copper text-sm disabled:opacity-50">
                  {saving ? "Saving…" : editingId ? "Save Changes" : "Create Draft"}
                </button>
              </div>
            </div>
          </div>
        )}

        {loading ? (
          <div className="text-ink/50 text-sm py-12 text-center">Loading courses…</div>
        ) : courses.length === 0 ? (
          <div className="card-flat p-12 text-center">
            <BookOpen className="w-12 h-12 text-ink/20 mx-auto mb-4" />
            <div className="font-heading font-bold text-lg text-ink/60">No courses yet</div>
            <p className="text-sm text-ink/40 mt-1 mb-6">Create your first course and start earning.</p>
            <button onClick={openCreate} className="btn-copper text-sm">Create Your First Course</button>
          </div>
        ) : (
          <div className="space-y-3">
            {courses.map(course => (
              <div key={course.course_id} className="card-flat overflow-hidden">
                <div
                  className="flex items-center gap-4 p-5 cursor-pointer hover:bg-bone/50 transition-colors"
                  onClick={() => setExpandedId(expandedId === course.course_id ? null : course.course_id)}
                >
                  {course.thumbnail_url ? (
                    <img src={course.thumbnail_url} alt="" className="w-12 h-12 rounded-lg object-cover shrink-0" />
                  ) : (
                    <div className="w-12 h-12 rounded-lg bg-copper/10 flex items-center justify-center shrink-0">
                      <BookOpen className="w-5 h-5 text-copper" />
                    </div>
                  )}
                  <div className="flex-1 min-w-0">
                    <div className="font-heading font-bold text-ink truncate">{course.title}</div>
                    <div className="text-xs text-ink/50 mt-0.5">
                      {course.category} · {course.sections?.length || 0} section{course.sections?.length !== 1 ? "s" : ""} ·{" "}
                      {course.price_cents === 0 ? "Free" : `$${(course.price_cents / 100).toFixed(2)}`}
                    </div>
                  </div>
                  <StatusBadge status={course.status} />
                  <div className="flex items-center gap-1 ml-2">
                    <button
                      onClick={e => { e.stopPropagation(); togglePublish(course); }}
                      title={course.status === "published" ? "Unpublish" : "Publish"}
                      className="p-2 text-ink/40 hover:text-green-600 transition-colors"
                    >
                      {course.status === "published" ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                    {course.status === "published" && (
                      <button
                        onClick={e => { e.stopPropagation(); shareCourse(course); }}
                        title="Copy share link"
                        className="p-2 text-ink/40 hover:text-copper transition-colors"
                      >
                        <Share2 className="w-4 h-4" />
                      </button>
                    )}
                    <button
                      onClick={e => { e.stopPropagation(); openEdit(course); }}
                      className="p-2 text-ink/40 hover:text-copper transition-colors"
                    >
                      <Pencil className="w-4 h-4" />
                    </button>
                    <button
                      onClick={e => { e.stopPropagation(); setDeleteTarget(course); }}
                      className="p-2 text-ink/40 hover:text-destructive transition-colors"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                    {expandedId === course.course_id
                      ? <ChevronUp className="w-4 h-4 text-ink/30 ml-1" />
                      : <ChevronDown className="w-4 h-4 text-ink/30 ml-1" />}
                  </div>
                </div>
                {expandedId === course.course_id && (
                  <div className="border-t border-ink/10 px-5 py-4 space-y-3 bg-bone/30">
                    {course.description && (
                      <p className="text-sm text-ink/70">{course.description}</p>
                    )}
                    {course.sections?.length > 0 && (
                      <div>
                        <div className="overline text-xs text-ink/40 mb-2">Sections</div>
                        <ol className="space-y-1">
                          {course.sections.map((s, i) => (
                            <li key={i} className="flex items-start gap-2 text-sm">
                              <CheckCircle className="w-4 h-4 text-copper mt-0.5 shrink-0" />
                              <span className="font-semibold">{s.title}</span>
                            </li>
                          ))}
                        </ol>
                      </div>
                    )}
                    <div className="text-xs text-ink/40">
                      Created {new Date(course.created_at).toLocaleDateString()} ·
                      Updated {new Date(course.updated_at).toLocaleDateString()} ·
                      {course.enrollment_count} enrolled
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
      {deleteTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-sm">
            <div className="px-6 py-5">
              <div className="flex items-center gap-2 mb-3">
                <Trash2 className="w-4 h-4 text-red-600" />
                <h2 className="font-heading font-bold text-lg text-slate-900">Delete Course</h2>
              </div>
              <p className="text-sm text-slate-600">
                Delete <strong>"{deleteTarget.title}"</strong>? This cannot be undone.
              </p>
            </div>
            <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-slate-100">
              <button onClick={() => setDeleteTarget(null)} className="text-sm px-4 py-2 rounded-lg text-slate-600 hover:bg-slate-50">Cancel</button>
              <button
                onClick={() => deleteCourse(deleteTarget)}
                className="flex items-center gap-2 text-sm px-5 py-2 rounded-lg bg-red-600 text-white font-bold hover:bg-red-700"
              >
                <Trash2 className="w-4 h-4" /> Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </AppShell>
  );
}

function StatusBadge({ status }) {
  if (status === "published") return (
    <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-green-100 text-green-700">Published</span>
  );
  if (status === "draft") return (
    <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-ink/10 text-ink/60">Draft</span>
  );
  return null;
}

function StatCard({ label, value, accent = "text-ink" }) {
  return (
    <div className="card-flat p-5">
      <div className={`font-heading text-3xl font-black ${accent}`}>{value}</div>
      <div className="overline text-ink/50 mt-1">{label}</div>
    </div>
  );
}
