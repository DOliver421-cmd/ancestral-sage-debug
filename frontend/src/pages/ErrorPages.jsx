import { Link } from "react-router-dom";
import { useAuth } from "../lib/auth";
import { WAI_LOGO, BRAND } from "../lib/brand";
import { AlertCircle, Home, Phone, Mail, Heart } from "lucide-react";

// ── 404: Page Missing ──────────────────────────────────────────────────────
export function Error404() {
  const { user } = useAuth();
  const homePath = user ? "/dashboard" : "/";

  return (
    <div className="min-h-screen bg-gradient-to-br from-bone to-bone/50 flex items-center justify-center p-6">
      <div className="max-w-2xl w-full">
        <div className="text-center">
          <div className="mb-8">
            <img src={WAI_LOGO} alt="W.A.I." className="w-16 h-16 mx-auto mb-4 opacity-60" />
            <h1 className="text-6xl font-bold text-ink mb-2">404</h1>
            <p className="text-xl text-copper font-bold">This path isn't mapped yet.</p>
          </div>

          <div className="bg-white border-l-4 border-copper rounded-lg p-8 mb-8 text-left">
            <h2 className="text-2xl font-bold text-ink mb-4">We couldn't find what you're looking for.</h2>
            <p className="text-ink/70 mb-4">
              Sometimes the journey takes us somewhere unexpected. This page doesn't exist — maybe the link is old, or maybe it's a detour we need to take.
            </p>
            <p className="text-ink/60 text-sm">
              "The master has failed more times than the beginner has even tried." — Stephen McCranie
            </p>
          </div>

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link to={homePath} className="btn-primary inline-flex items-center justify-center gap-2">
              <Home className="w-4 h-4" /> Return home
            </Link>
            <Link to="/more" className="btn-copper inline-flex items-center justify-center gap-2">
              <Heart className="w-4 h-4" /> Get support
            </Link>
          </div>

          <p className="text-xs text-ink/40 mt-8">
            Can't find what you need? <a href="mailto:souppoetry@gmail.com" className="underline hover:text-ink">Reach out to us.</a>
          </p>
        </div>
      </div>
    </div>
  );
}

// ── 500: Server Error ──────────────────────────────────────────────────────
export function Error500() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-bone to-bone/50 flex items-center justify-center p-6">
      <div className="max-w-2xl w-full">
        <div className="text-center">
          <div className="mb-8">
            <img src={WAI_LOGO} alt="W.A.I." className="w-16 h-16 mx-auto mb-4 opacity-60" />
            <h1 className="text-6xl font-bold text-ink mb-2">500</h1>
            <p className="text-xl text-copper font-bold">Something broke on our end.</p>
          </div>

          <div className="bg-white border-l-4 border-copper rounded-lg p-8 mb-8 text-left">
            <h2 className="text-2xl font-bold text-ink mb-4">Our system needs a moment.</h2>
            <p className="text-ink/70 mb-4">
              We're experiencing a temporary issue. Our team has been notified and is working to restore service.
              This happens — what matters is how we recover.
            </p>
            <p className="text-ink/60 text-sm">
              Check back in a few minutes. If the problem persists, reach out directly.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button onClick={() => window.location.reload()} className="btn-primary inline-flex items-center justify-center gap-2">
              Try again
            </button>
            <a href="mailto:souppoetry@gmail.com" className="btn-copper inline-flex items-center justify-center gap-2">
              <Mail className="w-4 h-4" /> Contact support
            </a>
          </div>

          <p className="text-xs text-ink/40 mt-8">
            Reference: {new Date().toISOString()} — Share this time with support if needed.
          </p>
        </div>
      </div>
    </div>
  );
}

// ── 503: Service Unavailable ──────────────────────────────────────────────────
export function Error503() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-bone to-bone/50 flex items-center justify-center p-6">
      <div className="max-w-2xl w-full">
        <div className="text-center">
          <div className="mb-8">
            <img src={WAI_LOGO} alt="W.A.I." className="w-16 h-16 mx-auto mb-4 opacity-60" />
            <h1 className="text-6xl font-bold text-ink mb-2">503</h1>
            <p className="text-xl text-copper font-bold">We're temporarily closed.</p>
          </div>

          <div className="bg-white border-l-4 border-copper rounded-lg p-8 mb-8 text-left">
            <h2 className="text-2xl font-bold text-ink mb-4">We're undergoing maintenance.</h2>
            <p className="text-ink/70 mb-4">
              We're taking time to improve our platform. We'll be back soon, stronger and ready to serve you better.
              Thank you for your patience.
            </p>
            <p className="text-ink/60 text-sm">
              Expected to return shortly. Check back soon.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button onClick={() => window.location.reload()} className="btn-primary inline-flex items-center justify-center gap-2">
              Check again
            </button>
            <Link to="https://status.wai-institute.com" className="btn-copper inline-flex items-center justify-center gap-2">
              <AlertCircle className="w-4 h-4" /> Status page
            </Link>
          </div>

          <p className="text-xs text-ink/40 mt-8">
            Follow us for updates on when we're back online.
          </p>
        </div>
      </div>
    </div>
  );
}

// ── Generic Error Fallback ──────────────────────────────────────────────────
export function ErrorFallback({ error, resetErrorBoundary }) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-bone to-bone/50 flex items-center justify-center p-6">
      <div className="max-w-2xl w-full">
        <div className="text-center">
          <div className="mb-8">
            <img src={WAI_LOGO} alt="W.A.I." className="w-16 h-16 mx-auto mb-4 opacity-60" />
            <h1 className="text-6xl font-bold text-ink mb-2">⚠️</h1>
            <p className="text-xl text-copper font-bold">Something unexpected happened.</p>
          </div>

          <div className="bg-white border-l-4 border-copper rounded-lg p-8 mb-8 text-left">
            <h2 className="text-2xl font-bold text-ink mb-4">We hit an unexpected bump.</h2>
            <p className="text-ink/70 mb-4">
              An error occurred that we didn't anticipate. We appreciate you helping us discover and fix this.
            </p>
            {error && (
              <div className="bg-ink/5 p-4 rounded border border-ink/10 mb-4 font-mono text-xs text-ink/60 overflow-auto max-h-32">
                {error.message}
              </div>
            )}
            <p className="text-ink/60 text-sm">
              Please try again, or let us know what happened so we can improve.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button onClick={resetErrorBoundary} className="btn-primary inline-flex items-center justify-center gap-2">
              Try again
            </button>
            <Link to="/" className="btn-copper inline-flex items-center justify-center gap-2">
              <Home className="w-4 h-4" /> Go home
            </Link>
          </div>

          <p className="text-xs text-ink/40 mt-8">
            Error details have been logged. <a href="mailto:souppoetry@gmail.com" className="underline hover:text-ink">Report this</a> if it keeps happening.
          </p>
        </div>
      </div>
    </div>
  );
}
