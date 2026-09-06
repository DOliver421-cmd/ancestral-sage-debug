/**
 * /video-studio — the standalone M.O.R.E. Pro Short-Form Video Studio.
 *
 * Per the production spec this is a SEPARATE feature, not a buried tab.
 * Access mirrors the backend rule in backend/routers/studio.py
 * (_video_access): feature_tier pro/patron/platinum/executive, or the
 * staff roles instructor/support_staff/oversight/admin/executive_admin.
 * The same rule is enforced server-side on every /api/video/* route, so
 * the gate here is a UX courtesy — the backend is the real gate.
 *
 * Renders the existing VideoStudio component (components/video/VideoStudio.jsx),
 * which is fully wired to the real /api/video/* endpoints (projects, scenes,
 * audio, voice, templates, render, publish, share). No second system, no mocks.
 */
import { Link, useSearchParams } from "react-router-dom";
import { useAuth } from "../lib/auth";
import { tierRank } from "../lib/tiers";
import AppShell from "../components/AppShell";
import BackButton from "../components/BackButton";
import VideoStudio from "../components/video/VideoStudio";
import { Clapperboard, Loader2 } from "lucide-react";

// Must match backend/routers/studio.py VIDEO_TIERS / VIDEO_STAFF_ROLES.
const VIDEO_TIERS = ["pro", "patron", "platinum", "executive"];
const VIDEO_STAFF_ROLES = ["instructor", "support_staff", "oversight", "admin", "executive_admin"];

export default function VideoStudioPage() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <AppShell>
        <div className="flex items-center justify-center py-24 text-ink/40">
          <Loader2 className="w-5 h-5 animate-spin mr-2" /> Loading studio…
        </div>
      </AppShell>
    );
  }

  if (!user) {
    return (
      <AppShell>
        <div className="p-8 max-w-xl mx-auto mt-12 text-center">
          <Clapperboard className="w-10 h-10 text-copper mx-auto mb-3" />
          <h1 className="font-heading text-2xl font-bold text-ink">M.O.R.E. Video Studio</h1>
          <p className="text-ink/60 text-sm mt-2">
            Make, edit, render, and share real short-form videos — right in your browser.
            Sign in to continue.
          </p>
          <div className="flex gap-3 justify-center mt-6">
            <Link
              to="/login?returnTo=%2Fvideo-studio"
              className="btn-copper text-sm"
              data-testid="video-studio-signin"
            >
              Sign In to Open the Studio
            </Link>
            <Link to="/plans" className="btn-primary text-sm">See Plans</Link>
          </div>
        </div>
      </AppShell>
    );
  }

  const tier = String(user.feature_tier || "free");
  const allowed =
    VIDEO_STAFF_ROLES.includes(user.role) || VIDEO_TIERS.includes(tier) || tierRank(tier) >= tierRank("pro");

  if (!allowed) {
    return (
      <AppShell>
        <div className="p-8 max-w-xl mx-auto mt-12 text-center">
          <Clapperboard className="w-10 h-10 text-copper mx-auto mb-3" />
          <h1 className="font-heading text-2xl font-bold text-ink">Pro-Tier Access Required</h1>
          <p className="text-ink/60 text-sm mt-2">
            The Short-Form Video Studio is available to Pro members, staff, and instructors.
            Upgrade to Pro to build, render, and publish real short-form videos with no watermarks.
          </p>
          <Link to="/plans" className="btn-copper text-sm mt-6 inline-block" data-testid="video-studio-upgrade">
            Upgrade to Pro →
          </Link>
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <div className="p-6 max-w-7xl mx-auto">
        <div className="flex items-center justify-between mb-4">
          <div>
            <div className="flex items-center gap-2">
              <Clapperboard className="w-5 h-5 text-copper" />
              <h1 className="font-heading text-2xl font-bold text-ink">M.O.R.E. Video Studio</h1>
              <span className="text-[10px] font-black uppercase tracking-widest bg-green-100 text-green-800 px-2 py-0.5 rounded-full">
                Pro · No watermarks
              </span>
            </div>
            <p className="text-ink/60 text-sm mt-1">
              Idea → plan → media → words → voice → music → scenes → preview → render MP4 → share.
            </p>
          </div>
          <BackButton to="/studio" />
        </div>
        <VideoStudio user={user} />
      </div>
    </AppShell>
  );
}
