import { useState, useEffect } from "react";
import { X, AlertCircle } from "lucide-react";

export default function BugReportModal() {
  const [isOpen, setIsOpen] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    venmoOrPaypal: "",
    whatYouTried: "",
    whatBroke: "",
    screenshot: null,
  });

  // Check if modal should show (first time, not submitted, within 48 hours of deploy)
  useEffect(() => {
    const lastShown = localStorage.getItem("bugReportModalShown");
    const deployTime = localStorage.getItem("deployTime") || new Date().getTime();
    localStorage.setItem("deployTime", deployTime);

    const hoursSinceDeploy = (new Date().getTime() - parseInt(deployTime)) / (1000 * 60 * 60);

    // Show modal if: not shown before AND within 48 hours of deploy
    if (!lastShown && hoursSinceDeploy < 48) {
      setIsOpen(true);
      localStorage.setItem("bugReportModalShown", "true");
    }
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await fetch("/api/bug-report", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });

      if (response.ok) {
        setSubmitted(true);
        setTimeout(() => setIsOpen(false), 2000);
      } else {
        alert("Error submitting bug report. Please try again.");
      }
    } catch (error) {
      console.error("Bug report submission failed:", error);
      alert("Error submitting bug report. Check console for details.");
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-bone border-2 border-copper rounded-lg max-w-lg w-full shadow-xl">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-copper/20">
          <div className="flex items-center gap-3">
            <AlertCircle className="w-6 h-6 text-copper" />
            <h2 className="text-xl font-bold">Break This Page</h2>
          </div>
          <button
            onClick={() => setIsOpen(false)}
            className="p-1 hover:bg-copper/10 rounded"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="p-6">
          {submitted ? (
            <div className="text-center py-8">
              <div className="text-4xl mb-4">✅</div>
              <p className="font-bold text-lg mb-2">Thanks for testing!</p>
              <p className="text-sm text-ink/70">
                You'll get <strong>$1</strong> for trying. If you found a bug, you get <strong>$1 + free BASIC membership</strong>.
              </p>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-bold mb-1">Name</label>
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-ink/20 rounded bg-white text-ink text-sm"
                  placeholder="Your name"
                />
              </div>

              <div>
                <label className="block text-sm font-bold mb-1">Email</label>
                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-ink/20 rounded bg-white text-ink text-sm"
                  placeholder="your@email.com"
                />
              </div>

              <div>
                <label className="block text-sm font-bold mb-1">Venmo or PayPal</label>
                <input
                  type="text"
                  name="venmoOrPaypal"
                  value={formData.venmoOrPaypal}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-ink/20 rounded bg-white text-ink text-sm"
                  placeholder="@venmo or paypal@email.com"
                />
              </div>

              <div>
                <label className="block text-sm font-bold mb-1">What did you try to do?</label>
                <select
                  name="whatYouTried"
                  value={formData.whatYouTried}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-ink/20 rounded bg-white text-ink text-sm"
                >
                  <option value="">Select...</option>
                  <option value="signup">Sign up</option>
                  <option value="login">Log in</option>
                  <option value="payment">Add payment method</option>
                  <option value="subscribe">Subscribe</option>
                  <option value="course">Access course</option>
                  <option value="refund">Request refund</option>
                  <option value="other">Other</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-bold mb-1">What broke?</label>
                <textarea
                  name="whatBroke"
                  value={formData.whatBroke}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-ink/20 rounded bg-white text-ink text-sm h-20 resize-none"
                  placeholder="Describe the bug, error message, or unexpected behavior..."
                />
              </div>

              <div className="flex gap-2 pt-4">
                <button
                  type="submit"
                  disabled={loading}
                  className="flex-1 btn-copper font-bold py-2 disabled:opacity-50"
                >
                  {loading ? "Submitting..." : "Submit Bug Report"}
                </button>
                <button
                  type="button"
                  onClick={() => setIsOpen(false)}
                  className="px-4 py-2 border border-ink/20 rounded font-bold hover:bg-ink/5"
                >
                  Skip
                </button>
              </div>

              <p className="text-xs text-ink/50 text-center">
                First 20 reports get $1. Breaking it gets you $1 + free BASIC membership.
              </p>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
