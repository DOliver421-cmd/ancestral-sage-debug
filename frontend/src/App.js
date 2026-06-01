import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "sonner";
import "./App.css";
import { AuthProvider, useAuth } from "./lib/auth";
import LandingMarketplace from "./pages/LandingMarketplace";
import SupervisorLogin from "./pages/SupervisorLogin";
import Login from "./pages/Login";
import Register from "./pages/Register";
import StudentDashboard from "./pages/StudentDashboard";
import InstructorDashboard from "./pages/InstructorDashboard";
import AdminDashboard from "./pages/AdminDashboard";
import ModulesList from "./pages/ModulesList";
import ModuleView from "./pages/ModuleView";
import Certificates from "./pages/Certificates";
import AITutor from "./pages/AITutor";
import LabsHub from "./pages/LabsHub";
import LabDetail from "./pages/LabDetail";
import Competencies from "./pages/Competencies";
import InstructorLabs from "./pages/InstructorLabs";
import Credentials from "./pages/Credentials";
import Portfolio from "./pages/Portfolio";
import PublicPortfolio from "./pages/PublicPortfolio";
import Adaptive from "./pages/Adaptive";
import ComplianceList from "./pages/ComplianceList";
import ComplianceDetail from "./pages/ComplianceDetail";
import AdminTools from "./pages/AdminTools";
import Analytics from "./pages/Analytics";
import AuditLog from "./pages/AuditLog";
import Attendance from "./pages/Attendance";
import Incidents from "./pages/Incidents";
import Settings from "./pages/Settings";
import ExecSystem from "./pages/ExecSystem";
import ForgotPassword from "./pages/ForgotPassword";
import ResetPassword from "./pages/ResetPassword";
import { Error404 } from "./pages/ErrorPages";
import SageAudit from "./pages/SageAudit";
import OrchestratorChat from "./pages/OrchestratorChat";
import More from "./pages/More";
import MoreHub from "./pages/MoreHub";
import MoreChat from "./pages/MoreChat";
import MoreAdmin from "./pages/MoreAdmin";
import MoreOps from "./pages/MoreOps";
import LitigationWeapon from "./pages/LitigationWeapon";
import CreatorProfile from "./pages/CreatorProfile";
import SocialPublish from "./pages/SocialPublish";
import Internships from "./pages/Internships";
import PlaylistSubmit from "./pages/PlaylistSubmit";
import PlaylistDashboard from "./pages/PlaylistDashboard";
import DirectorWidget from "./components/DirectorWidget";
import SupervisorWidget from "./components/SupervisorWidget";
import ErrorBoundary from "./components/ErrorBoundary";
import Helper from "./pages/Helper";
import Leaderboard from "./pages/Leaderboard";
import Store from "./pages/Store";
import SubscribePage from "./pages/SubscribePage";
import DonatePage from "./pages/DonatePage";
import PaymentSuccess from "./pages/PaymentSuccess";
import PaymentCancel from "./pages/PaymentCancel";
import PaymentHistory from "./pages/PaymentHistory";
import AdminPayments from "./pages/AdminPayments";
import AvatarSetup from "./pages/AvatarSetup";
import SovereignChat from "./components/SovereignChat";
import Palace from "./pages/Palace";
import ElderCouncil from "./pages/ElderCouncil";
import Plans from "./pages/Plans";
import HelpCenter from "./pages/HelpCenter";
import SeshatsHub from "./pages/SeshatsHub";
import SeshatsHubPublic from "./pages/SeshatsHubPublic";
import TermsOfService from "./pages/TermsOfService";
import PrivacyPolicy from "./pages/PrivacyPolicy";
import MoreHelpCenter from "./pages/MoreHelpCenter";
import CookieConsent from "./components/CookieConsent";
import HelpGuide from "./components/HelpGuide";
import WelcomeWizard from "./components/WelcomeWizard";
import StaffMeetingHistory from "./pages/StaffMeetingHistory";
import SystemHealth from "./pages/SystemHealth";
import ModerationAnalytics from "./pages/ModerationAnalytics";
import RevenueDivision from "./pages/RevenueDivision";
import Courses from "./pages/Courses";
import Community from "./pages/Community";
import Creators from "./pages/Creators";
import GhostProducer from "./pages/GhostProducer";
import ExecutiveDirectorDashboard from "./pages/ExecutiveDirectorDashboard";
import PartnershipDashboard from "./pages/PartnershipDashboard";
import PartnershipDiscounts from "./pages/PartnershipDiscounts";
import UserProfile from "./pages/UserProfile";
import LabSimulations from "./pages/LabSimulations";
import Landing from "./pages/Landing";
import PlatformPrices from "./pages/PlatformPrices";
import AuditorDashboard from "./pages/AuditorDashboard";
import ProviderGateway from "./pages/ProviderGateway";
import BillingAdmin from "./pages/BillingAdmin";
import CreatorCourses from "./pages/CreatorCourses";
import CreatorEarnings from "./pages/CreatorEarnings";
import CreatorProfileEdit from "./pages/CreatorProfileEdit";
import SiteControlPanel from "./pages/SiteControlPanel";

// Role hierarchy must mirror backend ROLE_RANK in /app/backend/server.py.
// Higher rank = more authority; a higher-rank role passes any check meant
// for a lower-rank role (executive_admin passes every check).
const ROLE_RANK = { student: 1, instructor: 2, admin: 3, executive_admin: 4 };

function Protected({ children, roles }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="p-12 text-ink font-heading">Loading…</div>;
  if (!user) return <Navigate to="/login" replace />;
  if (roles && roles.length > 0) {
    const needed = Math.min(...roles.map((r) => ROLE_RANK[r] ?? 99));
    const have = ROLE_RANK[user.role] ?? 0;
    if (have < needed) return <Navigate to="/dashboard" replace />;
  }
  return children;
}

// Supervisor-specific protection — redirects to the Supervisor login, not the main login.
function SupervisorProtected({ children }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="p-12 text-ink font-heading">Loading…</div>;
  if (!user) return <Navigate to="/supervisor-login" replace />;
  if ((ROLE_RANK[user.role] ?? 0) < ROLE_RANK["executive_admin"]) return <Navigate to="/supervisor-login" replace />;
  return children;
}

function Home() {
  const { user, loading } = useAuth();
  if (loading) return null;
  if (!user) return <Navigate to="/more-help-center" replace />;
  // executive_admin and admin both land on the admin overview
  if (user.role === "executive_admin") return <Navigate to="/admin/system" replace />;
  if (user.role === "admin") return <Navigate to="/admin" replace />;
  if (user.role === "instructor") return <Navigate to="/instructor" replace />;
  return <Navigate to="/dashboard" replace />;
}

function App() {
  const hostname = window.location.hostname;
  if (hostname.includes("morehelp.center")) {
    return (
      <AuthProvider>
        <BrowserRouter>
          <ErrorBoundary>
            <Toaster position="top-right" richColors />
            <Routes>
              {/* Auth pages must work on morehelp.center too */}
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />
              <Route path="*" element={<MoreHelpCenter />} />
            </Routes>
          </ErrorBoundary>
        </BrowserRouter>
      </AuthProvider>
    );
  }

  return (
    <AuthProvider>
      <BrowserRouter>
        <ErrorBoundary>
        <Toaster position="top-right" richColors />
        {/* Skip-to-content link for accessibility */}
        <a href="#main-content" className="sr-only focus:not-sr-only focus:fixed focus:top-4 focus:left-4 focus:z-[200] focus:px-4 focus:py-2 focus:bg-copper focus:text-white focus:font-bold focus:rounded-lg">
          Skip to content
        </a>

        {/* Global widgets */}
        <DirectorWidget />
        <SupervisorWidget />
        <SovereignChat />
        <CookieConsent />
        <HelpGuide />
        <WelcomeWizard />

        {/* Routes wrapped with main-content anchor */}
        <div id="main-content">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/forgot-password" element={<ForgotPassword />} />
          <Route path="/reset-password" element={<ResetPassword />} />
          {/* Helper routes — /helper is public, /app/helper requires auth */}
          <Route path="/helper" element={<Helper requireAuth={false} />} />
          <Route path="/app/helper" element={<Helper requireAuth={true} />} />
          <Route path="/dashboard" element={<Protected><StudentDashboard /></Protected>} />
          {/* Dashboard aliases (handoff routing scheme) — same pages, role-gated */}
          <Route path="/dashboard/student" element={<Protected><StudentDashboard /></Protected>} />
          <Route path="/dashboard/exec" element={<Protected roles={["executive_admin"]}><ExecSystem /></Protected>} />
          <Route path="/dashboard/admin" element={<Protected roles={["admin"]}><AdminDashboard /></Protected>} />
          <Route path="/dashboard/instructor" element={<Protected roles={["instructor", "admin"]}><InstructorDashboard /></Protected>} />
          <Route path="/avatar-setup" element={<Protected><AvatarSetup /></Protected>} />
          {/* Themed member spaces */}
          <Route path="/palace" element={<Protected><Palace /></Protected>} />
          <Route path="/elder-council" element={<Protected><ElderCouncil /></Protected>} />
          <Route path="/plans" element={<Plans />} />
          {/* Public funnel pages */}
          <Route path="/help-center" element={<HelpCenter />} />
          <Route path="/seshats-hub" element={<SeshatsHubPublic />} />
          {/* MORE Help Center — unified entry point (greeter / exec / decoy modes) */}
          <Route path="/more-help-center" element={<MoreHelpCenter />} />
          <Route path="/landing" element={<LandingMarketplace />} />
          {/* Supervisor — executive_admin only; separate login at /supervisor-login */}
          <Route path="/supervisor-login" element={<SupervisorLogin />} />
          <Route path="/supervisor" element={<SupervisorProtected><SeshatsHub /></SupervisorProtected>} />
          <Route path="/terms" element={<TermsOfService />} />
          <Route path="/privacy" element={<PrivacyPolicy />} />
          <Route path="/courses" element={<Courses />} />
          <Route path="/community" element={<Community />} />
          <Route path="/creators" element={<Creators />} />
          <Route path="/instructor" element={<Protected roles={["instructor", "admin"]}><InstructorDashboard /></Protected>} />
          <Route path="/admin" element={<Protected roles={["admin"]}><AdminDashboard /></Protected>} />
          <Route path="/admin/users" element={<Protected roles={["admin"]}><AdminDashboard /></Protected>} />
          <Route path="/admin/associate" element={<Protected roles={["admin"]}><AdminDashboard /></Protected>} />
          {/* Modules — public preview shows free intro modules; full catalog gated */}
          <Route path="/modules" element={<ModulesList />} />
          <Route path="/modules/:slug" element={<ModuleView />} />
          <Route path="/lab" element={<Navigate to="/labs" replace />} />
          <Route path="/labs" element={<Protected><LabsHub /></Protected>} />
          <Route path="/labs/:slug" element={<Protected><LabDetail /></Protected>} />
          <Route path="/competencies" element={<Protected><Competencies /></Protected>} />
          <Route path="/instructor/labs" element={<Protected roles={["instructor", "admin"]}><InstructorLabs /></Protected>} />
          <Route path="/ai" element={<Protected><AITutor /></Protected>} />
          <Route path="/certificates" element={<Protected><Certificates /></Protected>} />
          <Route path="/credentials" element={<Protected><Credentials /></Protected>} />
          <Route path="/portfolio" element={<Protected><Portfolio /></Protected>} />
          <Route path="/p/:slug" element={<PublicPortfolio />} />
          <Route path="/adaptive" element={<Protected><Adaptive /></Protected>} />
          <Route path="/compliance" element={<Protected><ComplianceList /></Protected>} />
          <Route path="/compliance/:slug" element={<Protected><ComplianceDetail /></Protected>} />
          <Route path="/admin/tools" element={<Protected roles={["admin"]}><AdminTools /></Protected>} />
          <Route path="/admin/analytics" element={<Protected roles={["admin"]}><Analytics /></Protected>} />
          <Route path="/admin/audit" element={<Protected roles={["admin"]}><AuditLog /></Protected>} />
          <Route path="/attendance" element={<Protected roles={["instructor", "admin"]}><Attendance /></Protected>} />
          <Route path="/incidents" element={<Protected><Incidents /></Protected>} />
          <Route path="/settings" element={<Protected><Settings /></Protected>} />
          <Route path="/admin/system" element={<Protected roles={["executive_admin"]}><ExecSystem /></Protected>} />
          {/* Site Control Panel — executive_admin only, not linked from any nav */}
          <Route path="/admin/control" element={<Protected roles={["executive_admin"]}><SiteControlPanel /></Protected>} />
          <Route path="/admin/director" element={<Protected roles={["executive_admin"]}><ExecutiveDirectorDashboard /></Protected>} />
          <Route path="/admin/sage-audit" element={<Protected roles={["executive_admin"]}><SageAudit /></Protected>} />
          <Route path="/admin/staff-meetings" element={<Protected roles={["executive_admin"]}><StaffMeetingHistory /></Protected>} />
          <Route path="/admin/health" element={<Protected roles={["admin"]}><SystemHealth /></Protected>} />
          <Route path="/admin/moderation" element={<Protected roles={["admin"]}><ModerationAnalytics /></Protected>} />
          <Route path="/revenue" element={<Protected roles={["admin", "executive_admin"]}><RevenueDivision /></Protected>} />
          <Route path="/council" element={<Protected><OrchestratorChat /></Protected>} />
          {/* Leaderboard — public read-only */}
          <Route path="/leaderboard" element={<Leaderboard />} />
          {/* Creator Studio — publish & manage courses */}
          <Route path="/creator/courses" element={<Protected><CreatorCourses /></Protected>} />
          {/* Creator earnings & payouts */}
          <Route path="/creator/earnings" element={<Protected><CreatorEarnings /></Protected>} />
          {/* Creator profile editor */}
          <Route path="/creator/profile/edit" element={<Protected><CreatorProfileEdit /></Protected>} />
          {/* Creator profiles — public, slug-based */}
          <Route path="/creator/:slug" element={<CreatorProfile />} />
          <Route path="/ghost-producer" element={<GhostProducer />} />
          {/* Public pages */}
          <Route path="/internships" element={<Internships />} />
          {/* Social publisher — authenticated */}
          <Route path="/social/publish" element={<Protected><SocialPublish /></Protected>} />
          {/* Playlist curation — public submission form, private dashboard */}
          <Route path="/playlist/:slug/submit" element={<PlaylistSubmit />} />
          <Route path="/playlist/dashboard" element={<Protected><PlaylistDashboard /></Protected>} />
          {/* M.O.R.E. — public tier */}
          <Route path="/more" element={<More />} />
          <Route path="/more/litigation" element={<LitigationWeapon />} />
          {/* M.O.R.E. — authenticated tier (full features, role-gated) */}
          <Route path="/app/more" element={<Protected><MoreHub /></Protected>} />
          <Route path="/more/chat" element={<Protected><MoreChat /></Protected>} />
          <Route path="/more/chat/:roomId" element={<Protected><MoreChat /></Protected>} />
          <Route path="/more/admin" element={<Protected roles={["admin"]}><MoreAdmin /></Protected>} />
          <Route path="/more/ops" element={<Protected roles={["admin"]}><MoreOps /></Protected>} />
          {/* Payments */}
          {/* Store & subscribe — public browsing, gated checkout */}
          <Route path="/store" element={<Store />} />
          <Route path="/subscribe" element={<SubscribePage />} />
          <Route path="/donate" element={<DonatePage />} />
          <Route path="/payment/success" element={<PaymentSuccess />} />
          <Route path="/payment/cancel" element={<PaymentCancel />} />
          <Route path="/payment/history" element={<Protected><PaymentHistory /></Protected>} />
          <Route path="/payment/manage" element={<Protected><PaymentHistory /></Protected>} />
          <Route path="/admin/payments" element={<Protected roles={["admin"]}><AdminPayments /></Protected>} />
          {/* Partnership & profile features */}
          <Route path="/partnership" element={<Protected><PartnershipDashboard /></Protected>} />
          <Route path="/partnership/discounts" element={<Protected><PartnershipDiscounts /></Protected>} />
          <Route path="/profile" element={<Protected><UserProfile /></Protected>} />
          <Route path="/profile/:id" element={<Protected><UserProfile /></Protected>} />
          {/* Lab simulations */}
          <Route path="/lab-simulations" element={<Protected><LabSimulations /></Protected>} />
          {/* Platform Prices — admin manage, exec delete */}
          <Route path="/admin/prices" element={<Protected roles={["admin"]}><PlatformPrices /></Protected>} />
          {/* The Auditor — read-only ledger and reporting, admin+ */}
          <Route path="/auditor" element={<Protected roles={["admin"]}><AuditorDashboard /></Protected>} />
          {/* Provider Gateway — executive only */}
          <Route path="/admin/providers" element={<Protected roles={["executive_admin"]}><ProviderGateway /></Protected>} />
          {/* Billing Admin — exec/admin */}
          <Route path="/admin/billing" element={<Protected roles={["admin"]}><BillingAdmin /></Protected>} />
          {/* Original landing page (alternate entry point) */}
          <Route path="/welcome" element={<Landing />} />
          <Route path="*" element={<Error404 />} />
        </Routes>
        </div>
        </ErrorBoundary>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
