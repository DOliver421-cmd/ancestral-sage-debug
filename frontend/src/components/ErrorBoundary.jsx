import { Component } from "react";
import { WAI_LOGO } from "../lib/brand";

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, info) {
    console.error("ErrorBoundary caught:", error, info);
  }

  // Allow parent to reset via key prop change (e.g. on route change)
  componentDidUpdate(prevProps) {
    if (this.state.hasError && prevProps.resetKey !== this.props.resetKey) {
      this.setState({ hasError: false, error: null });
    }
  }

  reset() {
    this.setState({ hasError: false, error: null });
  }

  render() {
    if (this.state.hasError) {
      // compact=true → small inline card, used inside admin/exec pages
      if (this.props.compact) {
        return (
          <div className="m-6 p-6 bg-red-50 border border-red-200 rounded-2xl max-w-2xl">
            <div className="flex items-start gap-3">
              <span className="text-2xl">⚠️</span>
              <div className="flex-1">
                <p className="font-heading font-bold text-red-800">This panel encountered an error.</p>
                <p className="text-sm text-red-700 mt-1">
                  {this.props.label || "This section"} failed to render. Other parts of the site are unaffected.
                </p>
                {process.env.NODE_ENV !== "production" && this.state.error && (
                  <details className="mt-2">
                    <summary className="text-xs text-red-500 cursor-pointer">Error details</summary>
                    <pre className="text-xs text-red-600 mt-1 overflow-auto max-h-24 bg-red-100 p-2 rounded">
                      {this.state.error.toString()}
                    </pre>
                  </details>
                )}
                <div className="flex gap-3 mt-4">
                  <button
                    onClick={() => this.reset()}
                    className="text-sm font-bold px-4 py-2 bg-red-700 text-white rounded-lg hover:bg-red-800 transition-colors"
                  >
                    Try Again
                  </button>
                  <a href={this.props.backTo || "/admin"}
                    className="text-sm font-bold px-4 py-2 border border-red-300 text-red-700 rounded-lg hover:bg-red-100 transition-colors"
                  >
                    ← Back to Admin
                  </a>
                </div>
              </div>
            </div>
          </div>
        );
      }

      // Full-page fallback (global boundary)
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
                <p className="text-ink/60 text-sm">
                  Your work is safe. Reload the page to continue, or reach out if this keeps happening.
                </p>
              </div>

              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <button
                  onClick={() => { this.setState({ hasError: false, error: null }); window.location.reload(); }}
                  className="btn-primary inline-flex items-center justify-center gap-2"
                >
                  Reload Page
                </button>
                <a href="mailto:souppoetry@gmail.com" className="btn-copper inline-flex items-center justify-center gap-2">
                  Get Help
                </a>
              </div>

              {process.env.REACT_APP_SHOW_DEMO === "true" && (
                <details className="text-left mt-8">
                  <summary className="text-xs text-ink/40 cursor-pointer">Error details (dev mode)</summary>
                  <div className="bg-ink/5 p-4 rounded border border-ink/10 mt-3 font-mono text-xs text-ink/60 overflow-auto max-h-32">
                    {this.state.error?.toString()}
                  </div>
                </details>
              )}
            </div>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
