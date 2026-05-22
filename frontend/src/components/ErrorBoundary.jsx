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

  render() {
    if (this.state.hasError) {
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
                <a href="mailto:support@wai-institute.com" className="btn-copper inline-flex items-center justify-center gap-2">
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
