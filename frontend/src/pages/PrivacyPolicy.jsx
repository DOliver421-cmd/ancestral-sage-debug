import { Link } from "react-router-dom";
import BackButton from "../components/BackButton";

export default function PrivacyPolicy() {
  return (
    <div className="min-h-screen bg-bone">
      {/* Nav */}
      <nav className="bg-ink text-white px-6 py-4 flex items-center gap-4">
        <BackButton fallback="/" />
        <span className="font-heading font-bold text-lg">Privacy Policy</span>
      </nav>

      <div className="max-w-3xl mx-auto px-6 py-12 prose prose-ink max-w-none">
        <h1>Privacy Policy</h1>
        <p className="text-sm text-ink/60">Last updated: May 2026</p>

        <h2>1. Information We Collect</h2>
        <p>When you register for an account, we collect your name and email address. We also collect course progress, lab submissions, and certificate data necessary to provide our educational services.</p>

        <h2>2. How We Use Your Data</h2>
        <p>We use your data solely to operate the platform: authenticate you, track your learning progress, issue certificates, and communicate account-related notices. We do not sell your personal data to third parties.</p>

        <h2>3. Cookies</h2>
        <p>We use essential cookies for authentication (JWT tokens) and security. No tracking or advertising cookies are used. You may decline cookies, but you will need to log in again each session.</p>

        <h2>4. Data Retention</h2>
        <p>We retain your data for as long as your account is active. Upon account deletion (see Your Rights), all personal data is anonymized within 30 days.</p>

        <h2>5. Your Rights (GDPR / CCPA)</h2>
        <ul>
          <li><strong>Right to access</strong> — export your data via Account Settings → Export Data.</li>
          <li><strong>Right to rectification</strong> — update your profile at any time.</li>
          <li><strong>Right to erasure</strong> — delete your account via Account Settings → Delete Account.</li>
          <li><strong>Right to data portability</strong> — your data export is in JSON format.</li>
        </ul>

        <h2>6. Children's Privacy (COPPA)</h2>
        <p>You must be at least 13 years old to create an account. If we learn that a user under 13 has registered, we will delete their account promptly.</p>

        <h2>7. Contact</h2>
        <p>Questions? Visit our <Link to="/help-center" className="text-copper hover:underline">Help Center</Link> or contact the data protection team.</p>
      </div>
    </div>
  );
}
