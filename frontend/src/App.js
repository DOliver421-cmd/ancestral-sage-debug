import { BrowserRouter, Routes, Route, Navigate, useLocation } from "react-router-dom";
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
import MediaStore from "./pages/MediaStore";
import Palace from "./pages/Palace";
import ElderCouncil from "./pages/ElderCouncil";
import Plans from "./pages/Plans";
import HelpCenter from "./pages/HelpCenter";
import SeshatsHub from "./pages/SeshatsHub";
import SeshatsHubPublic from "./pages/SeshatsHubPublic";
import TermsOfService from "./pages/TermsOfService";
import PrivacyPolicy from "./pages/PrivacyPolicy";
import MoreHelpCenter from "./pages/MoreHelpCenter";
import WAIInstitute from "./pages/WAIInstitute";
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
import UnifiedProfile from "./pages/UnifiedProfile";
import LabSimulations from "./pages/LabSimulations";
import Landing from "./pages/Landing";
import PlatformPrices from "./pages/PlatformPrices";
import AuditorDashboard from "./pages/AuditorDashboard";
import ProviderGateway from "./pages/ProviderGateway";
import TeamOps from "./pages/TeamOps";
import BillingAdmin from "./pages/BillingAdmin";
import CreatorCourses from "./pages/CreatorCourses";
import CreatorEarnings from "./pages/CreatorEarnings";
import CreatorProfileEdit from "./pages/CreatorProfileEdit";
import SiteControlPanel from "./pages/SiteControlPanel";
import ExecControlPanel from "./pages/ExecControlPanel";
import CreatorLounge from "./pages/CreatorLounge";
import BandOnPage from "./pages/BandOnPage";
import TrashPantheon from "./pages/TrashPantheon";
import CreatorPayoutDashboard from "./pages/CreatorPayoutDashboard";
import AccountControls from "./pages/AccountControls";
import MyPosition from "./pages/MyPosition";
import Personas from "./pages/Personas";
import PersonaProfile from "./pages/PersonaProfile";
import AdminAssistant from "./pages/AdminAssistant";
import CreativePartnerHub from "./pages/CreativePartnerHub";
import SentinelResearch from "./pages/SentinelResearch";
import ArcadeLanding from "./pages/ArcadeLanding";
import ArcadeGame from "./pages/ArcadeGame";
import CreatorStudio from "./pages/CreatorStudio";
import UnifiedGateway from "./pages/UnifiedGateway";
import CompetitionArena from "./pages/CompetitionArena";

// Role hierarchy must mirror backend ROLE_RANK in /app/backend/server.py.
// Higher rank = more authority; a higher-rank role passes any check meant
// for a lower-rank role (executive_admin passes every check).
// creative_partner is a lateral access level, not a promotion of student.
const ROLE_RANK = { student: 1, creative_partner: 1, instructor: 2, admin: 3, executive_admin: 4 };

function Protected({ children, roles }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="p-12 text-ink font-heading">Loading…</div>;
  if (!user) return <Navigate to="/login" replace />;
  if (roles && roles.length > 0) {
    // Exact role match first (for lateral roles like creative_partner), then rank check
    const exactMatch = roles.includes(user.role);
    const needed = Math.min(...roles.map((r) => ROLE_RANK[r] ?? 99));
    const have = ROLE_RANK[user.role] ?? 0;
    if (!exactMatch && have < needed) return <Navigate to="/dashboard" replace />;
  }
  return children;
}

// Wraps admin/exec routes in their own ErrorBoundary so a crash in one page
// doesn't bring down the whole app. resetKey resets the boundary on navigation.
function BoundedAdmin({ children, roles, label, backTo = "/admin" }) {
  const { pathname } = useLocation();
  return (
    <ErrorBoundary compact resetKey={pathname} label={label} backTo={backTo}>
      <Protected roles={roles}>{children}</Protected>
    </ErrorBoundary>
  );
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
  if (user.role === "creative_partner") return <Navigate to="/creative-partner" replace />;
  return <Navigate to="/dashboard" replace />;
}

function App() {
  const hostname = window.location.hostname;
  // wai-institute.org is the institution portal (admin + classrooms) — redirect to the WAI Institute hub on morehelp.center
  if (hostname.includes("wai-institute.org")) {
    window.location.replace("https://www.morehelp.center/wai-institute");
    return null;
  }
  if (hostname.includes("morehelp.center")) {
    return (
      <AuthProvider>
        <BrowserRouter>
          <ErrorBoundary>
            <Toaster position="top-right" richColors />
            <CookieConsent />
            <HelpGuide />
            <Routes>
              {/* ── Auth ── */}
              <Route path="/login"            element={<Login />} />
              <Route path="/register"         element={<Register />} />
              <Route path="/forgot-password"  element={<ForgotPassword />} />
              <Route path="/reset-password"   element={<ResetPassword />} />

              {/* ── WAI Institute portal ── */}
              <Route path="/wai-institute"    element={<WAIInstitute />} />
              <Route path="/wai-institute/*"  element={<WAIInstitute />} />

              {/* ── Public pages that nav links reference ── */}
              <Route path="/more"             element={<More />} />
              <Route path="/more-help-center" element={<MoreHelpCenter />} />
              <Route path="/more/chat"        element={<Protected><MoreChat /></Protected>} />
              <Route path="/more/chat/:roomId" element={<Protected><MoreChat /></Protected>} />
              <Route path="/modules"          element={<ModulesList />} />
              <Route path="/modules/:slug"    element={<ModuleView />} />
              <Route path="/courses"          element={<Courses />} />
              <Route path="/community"        element={<Community />} />
              <Route path="/help-center"      element={<HelpCenter />} />
              <Route path="/store"            element={<MediaStore />} />
              <Route path="/merch"            element={<Store />} />
              <Route path="/plans"            element={<Plans />} />
              <Route path="/subscribe"        element={<SubscribePage />} />
              <Route path="/donate"           element={<DonatePage />} />
              <Route path="/leaderboard"      element={<Leaderboard />} />
              <Route path="/terms"            element={<TermsOfService />} />
              <Route path="/privacy"          element={<PrivacyPolicy />} />
              <Route path="/internships"      element={<Internships />} />
              <Route path="/helper"           element={<Helper requireAuth={false} />} />
              <Route path="/seshats-hub"      element={<SeshatsHubPublic />} />
              <Route path="/ghost-producer"   element={<GhostProducer />} />
              <Route path="/personas"         element={<Personas />} />
              <Route path="/personas/:slug"   element={<PersonaProfile />} />
              <Route path="/creators"         element={<Creators />} />
              <Route path="/creator/:slug"    element={<CreatorProfile />} />
              <Route path="/creator-lounge"   element={<Protected><CreatorLounge /></Protected>} />
              <Route path="/p/:slug"          element={<PublicPortfolio />} />
              <Route path="/playlist/:slug/submit" element={<PlaylistSubmit />} />
              <Route path="/trash-pantheon" element={<TrashPantheon />} />

              {/* ── Supervisor ── */}
              <Route path="/supervisor-login" element={<SupervisorLogin />} />
              <Route path="/supervisor"       element={<SupervisorProtected><SeshatsHub /></SupervisorProtected>} />

              {/* ── Protected dashboard routes ── */}
              <Route path="/dashboard"        element={<Protected><StudentDashboard /></Protected>} />
              <Route path="/dashboard/student" element={<Protected><StudentDashboard /></Protected>} />
              <Route path="/instructor"       element={<Protected roles={["instructor","admin"]}><InstructorDashboard /></Protected>} />
              <Route path="/council"          element={<Protected><OrchestratorChat /></Protected>} />
              <Route path="/social/publish"   element={<Protected><SocialPublish /></Protected>} />
              <Route path="/more/ops"         element={<BoundedAdmin roles={["admin"]} label="M.O.R.E. Ops"><MoreOps /></BoundedAdmin>} />
              <Route path="/more/admin"       element={<Protected roles={["admin"]}><MoreAdmin /></Protected>} />
              <Route path="/more/litigation"  element={<LitigationWeapon />} />
              <Route path="/payment/success"  element={<PaymentSuccess />} />
              <Route path="/payment/cancel"   element={<PaymentCancel />} />
              <Route path="/payment/history"  element={<Protected><PaymentHistory /></Protected>} />
              <Route path="/u/:username"      element={<UnifiedProfile />} />
              <Route path="/profile"          element={<Protected><UnifiedProfile /></Protected>} />
              <Route path="/settings"         element={<Protected><Settings /></Protected>} />
              <Route path="/creator/courses"  element={<Protected><CreatorCourses /></Protected>} />
              <Route path="/creator/earnings" element={<Protected><CreatorEarnings /></Protected>} />
              <Route path="/creator/profile/edit" element={<Protected><CreatorProfileEdit /></Protected>} />
              <Route path="/playlist/dashboard" element={<Protected><PlaylistDashboard /></Protected>} />

              {/* ── Admin / exec routes — redirect to login if not authenticated ── */}
              <Route path="/admin"            element={<BoundedAdmin roles={["admin"]} label="Admin Dashboard"><AdminDashboard /></BoundedAdmin>} />
              <Route path="/admin/system"     element={<BoundedAdmin roles={["executive_admin"]} label="Exec System"><ExecSystem /></BoundedAdmin>} />
              <Route path="/admin/audit"      element={<BoundedAdmin roles={["admin"]} label="Audit Log"><AuditLog /></BoundedAdmin>} />
              <Route path="/admin/health"     element={<BoundedAdmin roles={["admin"]} label="System Health"><SystemHealth /></BoundedAdmin>} />
              <Route path="/admin/moderation" element={<BoundedAdmin roles={["admin"]} label="Moderation"><ModerationAnalytics /></BoundedAdmin>} />
              <Route path="/admin/control"    element={<BoundedAdmin roles={["executive_admin"]} label="Site Control"><SiteControlPanel /></BoundedAdmin>} />
              <Route path="/admin/providers"  element={<BoundedAdmin roles={["executive_admin"]} label="Provider Gateway"><ProviderGateway /></BoundedAdmin>} />
              <Route path="/team/ops"         element={<BoundedAdmin roles={["executive_admin"]} label="Team Operations"><TeamOps /></BoundedAdmin>} />
              <Route path="/admin/payments"   element={<BoundedAdmin roles={["admin"]} label="Admin Payments"><AdminPayments /></BoundedAdmin>} />

              {/* ── Admin Assistant service ── */}
              <Route path="/assistant"        element={<Protected><AdminAssistant /></Protected>} />
              <Route path="/creative-partner" element={<Protected roles={["creative_partner","executive_admin"]}><CreativePartnerHub /></Protected>} />
              <Route path="/s-research" element={<SentinelResearch />} />
              <Route path="/arcade" element={<Protected><ArcadeLanding /></Protected>} />
              <Route path="/arcade/:slug" element={<Protected><ArcadeGame /></Protected>} />
              <Route path="/studio" element={<Protected><CreatorStudio /></Protected>} />
              <Route path="/arena" element={<BoundedAdmin roles={["admin"]} label="The Arena"><CompetitionArena /></BoundedAdmin>} />
              <Route path="/trash" element={<TrashPantheon />} />
              <Route path="/creator/payouts" element={<Protected><CreatorPayoutDashboard /></Protected>} />

              {/* ── Landing / home ── */}
              <Route path="/welcome"          element={<Landing />} />
              <Route path="/more-help-center" element={<MoreHelpCenter />} />
              <Route path="/"                 element={<UnifiedGateway />} />
              <Route path="*"                 element={<UnifiedGateway />} />
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
        <CookieConsent />
        <HelpGuide />
        <WelcomeWizard />

        {/* Routes wrapped with main-content anchor */}
        <div id="main-content">
        <Routes>
          <Route path="/" element={<UnifiedGateway />} />
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
          <Route path="/dashboard/exec" element={<BoundedAdmin roles={["executive_admin"]} label="Exec Dashboard" backTo="/admin"><ExecSystem /></BoundedAdmin>} />
          <Route path="/dashboard/admin" element={<BoundedAdmin roles={["admin"]} label="Admin Dashboard"><AdminDashboard /></BoundedAdmin>} />
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
          <Route path="/admin" element={<BoundedAdmin roles={["admin"]} label="Admin Dashboard"><AdminDashboard /></BoundedAdmin>} />
          <Route path="/admin/users" element={<BoundedAdmin roles={["admin"]} label="Admin Dashboard"><AdminDashboard /></BoundedAdmin>} />
          <Route path="/admin/accounts" element={<BoundedAdmin roles={["admin"]} label="Account Controls" backTo="/admin"><AccountControls /></BoundedAdmin>} />
          <Route path="/admin/associate" element={<BoundedAdmin roles={["admin"]} label="Admin Dashboard"><AdminDashboard /></BoundedAdmin>} />
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
          <Route path="/admin/tools" element={<BoundedAdmin roles={["admin"]} label="Admin Tools"><AdminTools /></BoundedAdmin>} />
          <Route path="/admin/analytics" element={<BoundedAdmin roles={["admin"]} label="Analytics"><Analytics /></BoundedAdmin>} />
          <Route path="/admin/audit" element={<BoundedAdmin roles={["admin"]} label="Audit Log"><AuditLog /></BoundedAdmin>} />
          <Route path="/attendance" element={<Protected roles={["instructor", "admin"]}><Attendance /></Protected>} />
          <Route path="/incidents" element={<Protected><Incidents /></Protected>} />
          <Route path="/settings" element={<Protected><Settings /></Protected>} />
          <Route path="/my-position" element={<Protected><MyPosition /></Protected>} />
          <Route path="/personas" element={<Personas />} />
          <Route path="/personas/:slug" element={<PersonaProfile />} />
          <Route path="/admin/system" element={<BoundedAdmin roles={["executive_admin"]} label="Exec System" backTo="/admin/control"><ExecSystem /></BoundedAdmin>} />
          {/* Site Control Panel — executive_admin only, not linked from any nav */}
          <Route path="/admin/control" element={<BoundedAdmin roles={["executive_admin"]} label="Site Control Panel" backTo="/admin"><SiteControlPanel /></BoundedAdmin>} />
          <Route path="/admin/exec-control" element={<BoundedAdmin roles={["executive_admin"]} label="Sovereign Command" backTo="/admin"><ExecControlPanel /></BoundedAdmin>} />
          <Route path="/admin/director" element={<BoundedAdmin roles={["executive_admin"]} label="Director Dashboard" backTo="/admin"><ExecutiveDirectorDashboard /></BoundedAdmin>} />
          <Route path="/admin/sage-audit" element={<BoundedAdmin roles={["executive_admin"]} label="Sage Audit" backTo="/admin"><SageAudit /></BoundedAdmin>} />
          <Route path="/admin/staff-meetings" element={<BoundedAdmin roles={["executive_admin"]} label="Staff Meetings" backTo="/admin"><StaffMeetingHistory /></BoundedAdmin>} />
          <Route path="/admin/health" element={<BoundedAdmin roles={["admin"]} label="System Health"><SystemHealth /></BoundedAdmin>} />
          <Route path="/admin/moderation" element={<BoundedAdmin roles={["admin"]} label="Moderation Analytics"><ModerationAnalytics /></BoundedAdmin>} />
          <Route path="/revenue" element={<BoundedAdmin roles={["admin", "executive_admin"]} label="Revenue Division"><RevenueDivision /></BoundedAdmin>} />
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
          <Route path="/creator-lounge" element={<Protected><CreatorLounge /></Protected>} />
          <Route path="/band" element={<Protected><BandOnPage /></Protected>} />
          <Route path="/trash-pantheon" element={<TrashPantheon />} />
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
          <Route path="/store" element={<MediaStore />} />
          <Route path="/merch" element={<Store />} />
          <Route path="/subscribe" element={<SubscribePage />} />
          <Route path="/donate" element={<DonatePage />} />
          <Route path="/payment/success" element={<PaymentSuccess />} />
          <Route path="/payment/cancel" element={<PaymentCancel />} />
          <Route path="/payment/history" element={<Protected><PaymentHistory /></Protected>} />
          <Route path="/payment/manage" element={<Protected><PaymentHistory /></Protected>} />
          <Route path="/admin/payments" element={<BoundedAdmin roles={["admin"]} label="Admin Payments"><AdminPayments /></BoundedAdmin>} />
          {/* Partnership & profile features */}
          <Route path="/partnership" element={<Protected><PartnershipDashboard /></Protected>} />
          <Route path="/partnership/discounts" element={<Protected><PartnershipDiscounts /></Protected>} />
          <Route path="/u/:username" element={<UnifiedProfile />} />
          <Route path="/profile" element={<Protected><UnifiedProfile /></Protected>} />
          <Route path="/profile/:id" element={<Protected><UserProfile /></Protected>} />
          {/* Lab simulations */}
          <Route path="/lab-simulations" element={<Protected><LabSimulations /></Protected>} />
          {/* Platform Prices — admin manage, exec delete */}
          <Route path="/admin/prices" element={<BoundedAdmin roles={["admin"]} label="Platform Prices"><PlatformPrices /></BoundedAdmin>} />
          {/* The Auditor — read-only ledger and reporting, admin+ */}
          <Route path="/auditor" element={<BoundedAdmin roles={["admin"]} label="Auditor Dashboard"><AuditorDashboard /></BoundedAdmin>} />
          {/* Provider Gateway — executive only */}
          <Route path="/admin/providers" element={<BoundedAdmin roles={["executive_admin"]} label="Provider Gateway" backTo="/admin/control"><ProviderGateway /></BoundedAdmin>} />
          <Route path="/team/ops" element={<BoundedAdmin roles={["executive_admin"]} label="Team Operations" backTo="/admin/control"><TeamOps /></BoundedAdmin>} />
          {/* Billing Admin — exec/admin */}
          <Route path="/admin/billing" element={<BoundedAdmin roles={["admin"]} label="Billing Admin"><BillingAdmin /></BoundedAdmin>} />
          {/* Original landing page (alternate entry point) */}
          <Route path="/assistant" element={<Protected><AdminAssistant /></Protected>} />
          <Route path="/creative-partner" element={<Protected roles={["creative_partner","executive_admin"]}><CreativePartnerHub /></Protected>} />
          <Route path="/s-research" element={<SentinelResearch />} />
          <Route path="/arcade" element={<Protected><ArcadeLanding /></Protected>} />
          <Route path="/arcade/:slug" element={<Protected><ArcadeGame /></Protected>} />
          <Route path="/studio" element={<Protected><CreatorStudio /></Protected>} />
          <Route path="/arena" element={<BoundedAdmin roles={["admin"]} label="The Arena"><CompetitionArena /></BoundedAdmin>} />
          <Route path="/trash" element={<TrashPantheon />} />
          <Route path="/creator/payouts" element={<Protected><CreatorPayoutDashboard /></Protected>} />
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
