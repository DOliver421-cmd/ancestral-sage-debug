import { Component } from "react";

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
        <div className="min-h-screen bg-bone flex items-center justify-center p-8">
          <div className="max-w-md w-full text-center space-y-4">
            <div className="w-16 h-16 bg-ink text-signal flex items-center justify-center mx-auto text-2xl font-black">!</div>
            <h1 className="font-heading text-2xl font-bold">Something went wrong</h1>
            <p className="text-ink/60 text-sm leading-relaxed">
              An unexpected error occurred. Your work is safe — refresh the page to continue.
            </p>
            <button
              onClick={() => { this.setState({ hasError: false, error: null }); window.location.reload(); }}
              className="btn-copper text-sm"
            >
              Reload Page
            </button>
            {process.env.REACT_APP_SHOW_DEMO === "true" && (
              <details className="text-left mt-4">
                <summary className="text-xs text-ink/40 cursor-pointer">Error details</summary>
                <pre className="text-xs text-red-600 mt-2 overflow-auto bg-white p-3 border border-red-200">
                  {this.state.error?.toString()}
                </pre>
              </details>
            )}
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
