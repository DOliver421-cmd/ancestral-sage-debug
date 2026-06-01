import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import PublicNav from "../components/PublicNav";
import BackButton from "../components/BackButton";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import { toast } from "sonner";
import { BookOpen, ShoppingBag, CheckCircle, Loader2 } from "lucide-react";

const CATEGORY_LABELS = {
  general: "General",
  electrical: "Electrical & Trades",
  "ai-tech": "AI & Tech",
  "arts-music": "Arts & Music",
  workforce: "Workforce",
  wellness: "Wellness",
  publishing: "Publishing",
  business: "Business",
};

function PriceBadge({ cents }) {
  if (cents === 0) return <span className="text-xs font-bold text-green-600 bg-green-100 px-2 py-0.5 rounded-full">Free</span>;
  return <span className="text-xs font-bold text-copper bg-amber-100 px-2 py-0.5 rounded-full">${(cents / 100).toFixed(2)}</span>;
}

export default function Courses() {
  const { user } = useAuth();
  const [courses, setCourses] = useState([]);
  const [enrolledIds, setEnrolledIds] = useState(new Set());
  const [loading, setLoading] = useState(true);
  const [buying, setBuying] = useState(null);
  const [category, setCategory] = useState("");

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const [catalogRes, enrollRes] = await Promise.allSettled([
          api.get("/creator/courses/published", { params: { limit: 48, category } }),
          user ? api.get("/creator/enrollments/me") : Promise.resolve(null),
        ]);
        if (catalogRes.status === "fulfilled") {
          setCourses(catalogRes.value.data.courses || []);
        }
        if (enrollRes.status === "fulfilled" && enrollRes.value) {
          setEnrolledIds(new Set(enrollRes.value.data.enrolled_course_ids || []));
        }
      } catch {
        toast.error("Could not load courses.");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [user, category]);

  async function handleEnrollOrBuy(course) {
    if (!user) {
      window.location.href = "/login";
      return;
    }
    setBuying(course.course_id);
    try {
      const { data } = await api.post(`/creator/courses/${course.course_id}/checkout`);
      if (data.enrolled) {
        setEnrolledIds(prev => new Set([...prev, course.course_id]));
        toast.success("Enrolled! Check your dashboard.");
      } else if (data.url) {
        window.location.href = data.url;
      }
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Could not start enrollment.");
    } finally {
      setBuying(null);
    }
  }

  return (
    <div className="min-h-screen bg-bone">
      <PublicNav />
      <div className="max-w-6xl mx-auto px-6 py-10">
        <BackButton to="/" />
        <div className="mt-6">
          <div className="overline text-copper">Creator Catalog</div>
          <h1 className="font-heading text-4xl font-bold text-ink mt-2">Courses from the community.</h1>
          <p className="text-ink/60 mt-3 max-w-2xl">
            Real courses by real creators in the WAI network. Creators keep 70% of every sale.
          </p>
        </div>

        {/* Category filter */}
        <div className="flex gap-2 flex-wrap mt-6">
          <button
            onClick={() => setCategory("")}
            className={`text-xs font-bold px-3 py-1.5 rounded-full border transition-colors ${category === "" ? "bg-ink text-bone border-ink" : "border-ink/20 text-ink/60 hover:border-ink/40"}`}
          >
            All
          </button>
          {Object.entries(CATEGORY_LABELS).map(([key, label]) => (
            <button
              key={key}
              onClick={() => setCategory(key)}
              className={`text-xs font-bold px-3 py-1.5 rounded-full border transition-colors ${category === key ? "bg-ink text-bone border-ink" : "border-ink/20 text-ink/60 hover:border-ink/40"}`}
            >
              {label}
            </button>
          ))}
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-24 text-ink/40">
            <Loader2 className="w-6 h-6 animate-spin mr-2" /> Loading courses…
          </div>
        ) : courses.length === 0 ? (
          <div className="text-center py-24">
            <BookOpen className="w-10 h-10 text-ink/20 mx-auto mb-3" />
            <p className="text-ink/40 text-sm">No published courses yet in this category.</p>
            {user && (
              <Link to="/creator/courses" className="text-copper text-sm font-bold mt-2 inline-block">
                Publish your own →
              </Link>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mt-8">
            {courses.map(course => {
              const enrolled = enrolledIds.has(course.course_id);
              const isOwn = user && course.creator_id === user.id;
              const isBuying = buying === course.course_id;
              return (
                <div key={course.course_id} className="card-flat p-5 flex flex-col gap-3">
                  <div className="flex items-start justify-between gap-2">
                    <span className="text-xs text-ink/40 font-medium">
                      {CATEGORY_LABELS[course.category] || course.category}
                    </span>
                    <PriceBadge cents={course.price_cents} />
                  </div>
                  <div className="font-heading font-bold text-ink text-base leading-snug">{course.title}</div>
                  {course.description && (
                    <p className="text-xs text-ink/60 line-clamp-2">{course.description}</p>
                  )}
                  <div className="flex items-center justify-between mt-auto pt-2 border-t border-ink/10">
                    <span className="text-xs text-ink/40">
                      {course.enrollment_count || 0} enrolled
                    </span>
                    {isOwn ? (
                      <Link
                        to="/creator/courses"
                        className="text-xs font-bold text-copper border border-copper/40 hover:border-copper px-3 py-1.5 rounded-full transition-colors"
                      >
                        Manage
                      </Link>
                    ) : enrolled ? (
                      <span className="flex items-center gap-1 text-xs font-bold text-green-600">
                        <CheckCircle className="w-3.5 h-3.5" /> Enrolled
                      </span>
                    ) : (
                      <button
                        onClick={() => handleEnrollOrBuy(course)}
                        disabled={isBuying}
                        className="flex items-center gap-1.5 text-xs font-bold bg-copper hover:bg-amber-600 text-bone px-3 py-1.5 rounded-full transition-colors disabled:opacity-50"
                      >
                        {isBuying ? <Loader2 className="w-3 h-3 animate-spin" /> : <ShoppingBag className="w-3 h-3" />}
                        {course.price_cents === 0 ? "Enroll Free" : "Buy Now"}
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}

        <div className="text-center mt-10 text-sm text-ink/40">
          Want to teach?{" "}
          {user ? (
            <Link to="/creator/courses" className="text-copper font-bold">Publish your first course →</Link>
          ) : (
            <Link to="/register" className="text-copper font-bold">Create an account →</Link>
          )}
        </div>
      </div>
    </div>
  );
}
