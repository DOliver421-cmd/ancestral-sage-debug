import { Link } from "react-router-dom";
import BackButton from "../components/BackButton";

export default function TermsOfService() {
  return (
    <div className="min-h-screen bg-bone">
      {/* Nav */}
      <nav className="bg-ink text-white px-6 py-4 flex items-center gap-4">
        <BackButton fallback="/" />
        <span className="font-heading font-bold text-lg">Terms of Service</span>
      </nav>

      <div className="max-w-3xl mx-auto px-6 py-12 prose prose-ink max-w-none">
        <h1>Terms of Service</h1>
        <p className="text-sm text-ink/60">Last updated: May 2026</p>

        <h2>1. Acceptance</h2>
        <p>By creating an account, you agree to these terms. If you do not agree, do not use the platform.</p>

        <h2>2. Account</h2>
        <p>You are responsible for keeping your password secure. You must be at least 13 years old. One account per person.</p>

        <h2>3. Acceptable Use</h2>
        <p>You agree not to: (a) use the platform for any illegal purpose; (b) attempt to bypass security or rate limits; (c) harass other users; (d) submit false or misleading information.</p>

        <h2>4. Content</h2>
        <p>Course content is provided for educational purposes. Lab submissions and portfolio content remain your intellectual property. You grant us a license to display your public portfolio.</p>

        <h2>5. Termination</h2>
        <p>We may suspend accounts that violate these terms. You may delete your account at any time via Account Settings.</p>

        <h2>6. Disclaimer</h2>
        <p>The platform is provided "as is" without warranty. We are not liable for any damages arising from use of the platform.</p>

        <h2>7. Changes</h2>
        <p>We may update these terms. Continued use after changes constitutes acceptance. We will notify registered users of material changes.</p>

        <h2>8. Contact</h2>
        <p>Questions? Visit our <Link to="/help-center" className="text-copper hover:underline">Help Center</Link>.</p>
      </div>
    </div>
  );
}
