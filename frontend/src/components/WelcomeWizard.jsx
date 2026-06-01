import { useState, useEffect } from "react";
import { useAuth } from "../lib/auth";
import { X, ArrowRight, Check } from "lucide-react";

const WIZARD_KEY = "welcome_wizard_seen_v1";

const STEPS = {
  student: [
    { title: "Welcome to W.A.I.!", body: "You're now part of the Workforce Apprentice Institute. Let's get you started.", icon: "🎓" },
    { title: "Explore Courses", body: "Head to Courses to find training modules. Complete them at your own pace.", icon: "📚", link: "/courses" },
    { title: "Hands-On Labs", body: "Put your knowledge into practice with real-world lab exercises.", icon: "🔧", link: "/labs" },
    { title: "Earn Credentials", body: "Complete modules and labs to earn certificates and digital credentials.", icon: "🏆", link: "/certificates" },
    { title: "Get Help", body: "Use the Sage Guide (bottom-right ? button) anytime for help with any page.", icon: "💡" },
  ],
  instructor: [
    { title: "Welcome, Instructor!", body: "You have access to teaching tools and student management.", icon: "👋" },
    { title: "Your Dashboard", body: "Manage classes, review lab submissions, and track student progress.", icon: "📊", link: "/dashboard/instructor" },
    { title: "Create Labs", body: "Design and assign lab exercises for your students.", icon: "🧪", link: "/instructor/labs" },
    { title: "Track Attendance", body: "Take attendance and monitor student participation.", icon: "📋", link: "/attendance" },
    { title: "Get Help", body: "Use the Sage Guide (bottom-right ? button) anytime for help with any page.", icon: "💡" },
  ],
  admin: [
    { title: "Welcome, Admin!", body: "You have platform administration access.", icon: "🔐" },
    { title: "Manage Users", body: "Create and manage user accounts, roles, and cohorts.", icon: "👥", link: "/admin/users" },
    { title: "Analytics", body: "View platform metrics and generate reports.", icon: "📈", link: "/admin/analytics" },
    { title: "Audit Trail", body: "Review all administrative actions in the audit log.", icon: "📝", link: "/admin/audit" },
    { title: "Get Help", body: "Use the Sage Guide (bottom-right ? button) anytime for help with any page.", icon: "💡" },
  ],
  executive_admin: [
    { title: "Welcome, Executive!", body: "Full system oversight and command capabilities.", icon: "⚡" },
    { title: "Executive System", body: "Staff meetings, pipeline processing, and system commands.", icon: "🖥️", link: "/admin/system" },
    { title: "Sage Sessions", body: "Monitor and audit AI interactions across the platform.", icon: "👁️", link: "/admin/sage-audit" },
    { title: "Staff Meetings", body: "Convene the WAI persona network to delegate complex tasks.", icon: "🤝" },
    { title: "Get Help", body: "Use the Sage Guide (bottom-right ? button) anytime for help with any page.", icon: "💡" },
  ],
};

export default function WelcomeWizard() {
  const { user } = useAuth();
  const [visible, setVisible] = useState(false);
  const [step, setStep] = useState(0);

  useEffect(() => {
    if (!user) return;
    const seen = localStorage.getItem(WIZARD_KEY);
    if (!seen) {
      setVisible(true);
    }
  }, [user]);

  const dismiss = () => {
    localStorage.setItem(WIZARD_KEY, "1");
    setVisible(false);
  };

  if (!visible || !user) return null;

  const steps = STEPS[user.role] || STEPS.student;
  const current = steps[step];
  const isLast = step >= steps.length - 1;

  return (
    <div className="fixed inset-0 z-[100] bg-ink/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full overflow-hidden animate-fade-in">
        {/* Progress bar */}
        <div className="h-1.5 bg-ink/10">
          <div
            className="h-full bg-copper transition-all duration-500"
            style={{ width: `${((step + 1) / steps.length) * 100}%` }}
          />
        </div>

        {/* Body */}
        <div className="p-6 sm:p-8">
          <div className="flex items-start justify-between">
            <span className="text-3xl">{current.icon}</span>
            <button
              onClick={dismiss}
              className="text-ink/30 hover:text-ink transition-colors"
              aria-label="Close"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          <h2 className="font-heading text-xl font-bold text-ink mt-4">{current.title}</h2>
          <p className="text-sm text-ink/70 mt-2">{current.body}</p>

          {/* Step indicators */}
          <div className="flex gap-1.5 mt-6">
            {steps.map((_, i) => (
              <div
                key={i}
                className={`h-1.5 flex-1 rounded-full transition-colors ${
                  i <= step ? "bg-copper" : "bg-ink/10"
                }`}
              />
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="border-t border-ink/10 px-6 py-4 flex items-center justify-between">
          <button
            onClick={dismiss}
            className="text-xs text-ink/50 hover:text-ink transition-colors"
          >
            Skip tour
          </button>
          <div className="flex gap-3">
            {step > 0 && (
              <button
                onClick={() => setStep(step - 1)}
                className="px-4 py-2 text-sm border border-ink/20 rounded-lg hover:bg-ink/5 transition-colors"
              >
                Back
              </button>
            )}
            <button
              onClick={() => {
                if (isLast) {
                  dismiss();
                } else {
                  setStep(step + 1);
                }
              }}
              className="px-4 py-2 text-sm bg-copper text-white font-bold rounded-lg hover:bg-copper/90 transition-colors inline-flex items-center gap-2"
            >
              {isLast ? (
                <>Get Started <Check className="w-4 h-4" /></>
              ) : (
                <>Next <ArrowRight className="w-4 h-4" /></>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
