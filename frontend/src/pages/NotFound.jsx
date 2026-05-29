import { Link, useLocation } from "react-router-dom";
import { useAuth } from "../lib/auth";
import { WAI_LOGO, BRAND } from "../lib/brand";
import { ArrowLeft, Compass, Home } from "lucide-react";

export default function NotFound() {
  const { user } = useAuth();
  const location = useLocation();

  // Where "Home" should send the user, based on auth state.
  let homePath = "/";
  let homeLabel = "Back to landing";
  if (user) {
    if (user.role === "admin" || user.role === "executive_admin") {
      homePath = "/admin";
      homeLabel = "Back to admin dashboard";
    } else if (user.role === "instructor") {
      homePath = "/instructor";
      homeLabel = "Back to instructor dashboard";
    } else {
      homePath = "/dashboard";
      homeLabel = "Back to your dashboard";
    }
  }

  return (
    <div className="min-h-screen bg-bone grid lg:grid-cols-2" data-testid="not-found-page">
      <div className="hidden lg:block bg-ink relative overflow-hidden">
        <div className="absolute inset-0 grid-paper opacity-10" />
        <div className="relative h-full flex flex-col justify-between p-12 text-white">
          <Link to="/" className="flex items-center gap-3" data-testid="not-found-brand">
            <img src={WAI_LOGO} alt="W.A.I." className="w-12 h-12 object-contain bg-white p-1" />
            <div>
              <div className="overline text-signal">{BRAND.short}</div>
              <div className="font-heading font-bold">{BRAND.name}</div>
            </div>
          </Link>
          <div>
            <div className="overline text-copper">Error 404</div>
            <h1 className="font-heading text-7xl font-extrabold mt-4 leading-none tracking-tight">
              Off the <br /> blueprint.
            </h1>
            <p className="mt-6 text-white/70 max-w-md">
              The page you're looking for isn't on the schematic. It may have been renamed,
              moved, or never existed in this build.
            </p>
          </div>
          <div className="text-xs text-white/50 italic">
            "Direct my footsteps according to your word." — Psalm 119:133
          </div>
        </div>
      </div>

      <div className="flex items-center justify-center p-8">
        <div className="w-full max-w-md">
          <div className="overline text-copper">Page not found</div>
          <h2 className="font-heading text-3xl font-bold mt-2 flex items-center gap-3">
            <Compass className="w-7 h-7 text-signal" /> Wrong turn.
          </h2>
          <p className="text-ink/60 mt-3" data-testid="not-found-path">
            We couldn't find <span className="font-mono font-semibold break-all">{location.pathname}</span>.
            If you arrived here from a bookmark or an old link, the URL has likely changed.
          </p>

          <div className="card-flat p-4 mt-6 bg-white border-l-4 border-l-copper">
            <p className="text-sm text-ink/70">
              Try heading back to your dashboard, or use the main navigation. If you believe this is
              a bug, please <strong>contact your program administrator</strong>.
            </p>
          </div>

          <div className="mt-8 flex flex-col sm:flex-row gap-3">
            <Link
              to={homePath}
              className="btn-primary inline-flex items-center justify-center gap-2"
              data-testid="not-found-home-btn"
            >
              <Home className="w-4 h-4" /> {homeLabel}
            </Link>
            {user && (
              <Link
                to="/login"
                className="btn-secondary inline-flex items-center justify-center gap-2"
                data-testid="not-found-login-btn"
              >
                <ArrowLeft className="w-4 h-4" /> Sign in as someone else
              </Link>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
