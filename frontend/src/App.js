import { useEffect } from "react";
import { BrowserRouter, Routes, Route, Navigate, useLocation, useParams } from "react-router-dom";
import { Toaster } from "sonner";
import "./App.css";
import { AuthProvider, useAuth } from "./lib/auth";
import { isWaiDoor } from "./lib/domain";
import { useSeoManager } from "./lib/seo";
import { TierGate } from "./lib/tiers";
import AccessGate from "./components/AccessGate";
import LandingMarketplace from "./pages/LandingMarketplace";
import SupervisorLogin from "./pages/SupervisorLogin";
import Login from "./pages/Login";
import Register from "./pages/Register";
import StudentDashboard from "./pages/StudentDashboard";
import InstructorDashboard from "./pages/InstructorDashboard";
import AdminDashboard from "./pages/AdminDashboard";
import IAMConsole from "./pages/IAMConsole";
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
import Analytics from "./pages/Analytics";
import AuditLog from "./pages/AuditLog";
import Attendance from "./pages/Attendance";
import Incidents from "./pages/Incidents";
import Settings from "./pages/Settings";
import ForgotPassword from "./pages/ForgotPassword";
import FactoryReset from "./pages/FactoryReset";
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
function CreatorSlugRedirect() { const { slug } = useParams(); return <Navigate to={`/u/${slug}`} replace />; }
function ClassicToolRoute() { const { slug } = useParams(); return <LegacyTool slug={slug} />; }
import SocialPublish from "./pages/SocialPublish";
import Internships from "./pages/Internships";
import PlaylistSubmit from "./pages/PlaylistSubmit";
import PlaylistDashboard from "./pages/PlaylistDashboard";
import ErrorBoundary from "./components/ErrorBoundary";
import AppShell from "./components/AppShell";
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
import KnowledgeBase from "./pages/KnowledgeBase";
import KnowledgeFinder from "./pages/KnowledgeFinder";
import SeshatsHub from "./pages/SeshatsHub";
import SeshatsHubPublic from "./pages/SeshatsHubPublic";
import TermsOfService from "./pages/TermsOfService";
import PrivacyPolicy from "./pages/PrivacyPolicy";
import RefundPolicy from "./pages/RefundPolicy";
import MoreHelpCenter from "./pages/MoreHelpCenter";
import WAIInstitute from "./pages/WAIInstitute";
import OurLegacy from "./pages/OurLegacy";
import VonnsSaga from "./pages/VonnsSaga";
import CookieConsent from "./components/CookieConsent";
import HelpGuide from "./components/HelpGuide";
import WelcomeWizard from "./components/WelcomeWizard";
import StaffMeetingHistory from "./pages/StaffMeetingHistory";
import SystemHealth from "./pages/SystemHealth";
import ModerationAnalytics from "./pages/ModerationAnalytics";
import RevenueDivision from "./pages/RevenueDivision";
import Courses from "./pages/Courses";
import AscensionProtocols from "./pages/AscensionProtocols";
import SponsorScholarship from "./pages/SponsorScholarship";
import ScholarshipApply from "./pages/ScholarshipApply";
import AdminScholarships from "./pages/AdminScholarships";
import AdminPromoCodes from "./pages/AdminPromoCodes";
import VideoPresenter from "./pages/VideoPresenter";
import ExecutiveCommandCenter from "./pages/ExecutiveCommandCenter";
import Community from "./pages/Community";
import Creators from "./pages/Creators";
import GhostProducer from "./pages/GhostProducer";
import PartnershipDashboard from "./pages/PartnershipDashboard";
import PartnershipDiscounts from "./pages/PartnershipDiscounts";
import UserProfile from "./pages/UserProfile";
import UnifiedProfile from "./pages/UnifiedProfile";
import LabSimulations from "./pages/LabSimulations";
import Landing from "./pages/Landing";
import PlatformPrices from "./pages/PlatformPrices";
import AuditorDashboard from "./pages/AuditorDashboard";
import ProviderGateway from "./pages/ProviderGateway";
import ExecutiveSiteReport from "./pages/ExecutiveSiteReport";
import TeamOps from "./pages/TeamOps";
import BillingAdmin from "./pages/BillingAdmin";
import CreatorCourses from "./pages/CreatorCourses";
import CreatorEarnings from "./pages/CreatorEarnings";
// CreatorProfileEdit is retired — editing lives in /profile Settings tab
import SiteControlPanel from "./pages/SiteControlPanel";
import FeatureControlCenter from "./pages/FeatureControlCenter";
import ExecBusinessOffice from "./pages/ExecBusinessOffice";
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
import ExecutiveSuite from "./pages/ExecutiveSuite";
import Jamil from "./pages/Jamil";
import ProjectDashboard from "./pages/ProjectDashboard";
import AITeamBridge from "./pages/AITeamBridge";
import BYOK from "./pages/BYOK";
import SiteGuide from "./pages/SiteGuide";
import SiteSearch, { SiteSearchModal } from "./components/SiteSearch";
import BusinessOffice from "./pages/BusinessOffice";
import ClassicTools from "./pages/ClassicTools";
import LegacyTool from "./pages/LegacyTool";
import AgentRegistryView from "./pages/aawab/AgentRegistryView";
import CertificationChamber from "./pages/aawab/CertificationChamber";
import AdminAawabDashboard from "./pages/aawab/AdminAawabDashboard";
import CrossSiteLogin from "./pages/CrossSiteLogin";
import { ROLE_RANK } from "./lib/roles";

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
  if (user.role === "instructor" || user.role === "trial_pass") return <Navigate to="/instructor" replace />;
  return <Navigate to="/dashboard" replace />;
}

// Sets per-route, per-door title/meta (see lib/seo.js). Must live inside the Router.
function SeoManager() {
  useSeoManager();
  return null;
}

// Wraps pages that forgot to include AppShell — gives them the sidebar nav
function AdminPage({ children }) {
  return <AppShell>{children}</AppShell>;
}

// Scrolls the window to the top on every route change.  Without this, React
// Router keeps the previous page's scroll offset, so navigating from a long
// page lands you mid-screen on the new page — the "stuck at an empty area"
// behavior across the whole site.
function ScrollToTop() {
  const { pathname } = useLocation();
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname]);
  return null;
}

function App() {
  // Domain-aware front door (see docs/morehelp-migration-blueprint.md):
  //   wai-institute.org  → focused WAI institution landing (same build)
  //   morehelp.center    → M.O.R.E. hub landing
  const waiDoor = isWaiDoor();
  return (
    <AuthProvider>
      <BrowserRouter>
        <ScrollToTop />
        <SeoManager />
        <ErrorBoundary>
        <Toaster position="top-right" richColors />
        {/* Skip-to-content link for accessibility */}
        <a href="#main-content" className="sr-only focus:not-sr-only focus:fixed focus:top-4 focus:left-4 focus:z-[200] focus:px-4 focus:py-2 focus:bg-copper focus:text-white focus:font-bold focus:rounded-lg">
          Skip to content
        </a>

        {/* Global widgets */}
        <CookieConsent />
        {/* On the WAI door, support links OUT to the M.O.R.E. Help Center instead of opening the in-app widget. */}
        {!waiDoor && <HelpGuide />}
        <SiteSearchModal />
        <WelcomeWizard />

        {/* Routes wrapped with main-content anchor + exec page-access gates */}
        <div id="main-content">
        <AccessGate>
        <Routes>
          <Route path="/" element={waiDoor ? <WAIInstitute /> : <UnifiedGateway />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/forgot-password" element={<ForgotPassword />} />
          <Route path="/factory-reset" element={<FactoryReset />} />
          <Route path="/reset-password" element={<ResetPassword />} />
          {/* Helper routes — /helper is public, /app/helper requires auth */}
          <Route path="/helper" element={<Helper requireAuth={false} />} />
          <Route path="/app/helper" element={<Helper requireAuth={true} />} />
          <Route path="/dashboard" element={<Protected><StudentDashboard /></Protected>} />
          {/* Dashboard aliases (handoff routing scheme) — same pages, role-gated */}
          <Route path="/dashboard/student" element={<Protected><StudentDashboard /></Protected>} />
          <Route path="/dashboard/exec" element={<Navigate to="/admin/command" replace />} />
          <Route path="/dashboard/admin" element={<BoundedAdmin roles={["admin"]} label="Admin Dashboard"><AdminDashboard /></BoundedAdmin>} />
          <Route path="/dashboard/instructor" element={<Protected roles={["instructor", "admin"]}><InstructorDashboard /></Protected>} />
          <Route path="/avatar-setup" element={<Protected><AvatarSetup /></Protected>} />
          {/* Themed member spaces */}
          <Route path="/palace" element={<Protected><Palace /></Protected>} />
          <Route path="/elder-council" element={<BoundedAdmin roles={["admin"]} label="Elder Council" backTo="/dashboard"><ElderCouncil /></BoundedAdmin>} />
          <Route path="/plans" element={<Plans />} />
          {/* Public funnel pages */}
          <Route path="/help-center" element={<HelpCenter />} />
          {/* Knowledge Base — handbooks + top support articles (Phase C) */}
          <Route path="/knowledge-base" element={<KnowledgeBase />} />
          <Route path="/knowledge" element={<KnowledgeFinder />} />
          <Route path="/seshats-hub" element={<SeshatsHubPublic />} />
          {/* M.O.R.E. Help Center — unified entry point (greeter / exec / decoy modes) */}
          <Route path="/more-help-center" element={<MoreHelpCenter />} />
          {/* Classic Tools — the preserved original HTML applications */}
          <Route path="/classic-tools" element={<ClassicTools />} />
          <Route path="/classic/:slug" element={<ClassicToolRoute />} />
          {/* Site search + Site Guide persona */}
          <Route path="/search" element={<SiteSearch />} />
          <Route path="/site-guide" element={<SiteGuide />} />
          {/* AI Business Office — the revenue engine command center */}
          <Route path="/business-office" element={<BoundedAdmin roles={["admin"]} label="AI Business Office" backTo="/admin"><BusinessOffice /></BoundedAdmin>} />
          <Route path="/admin/business-office" element={<BoundedAdmin roles={["admin"]} label="AI Business Office" backTo="/admin"><BusinessOffice /></BoundedAdmin>} />
          {/* Exec Control — change every office number and text without code */}
          <Route path="/admin/office-control" element={<Navigate to="/admin/office" replace />} />
          {/* AAWAB — Agent Wellness & Certification Bureau */}
          <Route path="/aawab" element={<BoundedAdmin roles={["admin"]} label="Agent Wellness" backTo="/admin"><AgentRegistryView /></BoundedAdmin>} />
          <Route path="/aawab/chamber" element={<BoundedAdmin roles={["admin"]} label="Certification Chamber" backTo="/aawab"><CertificationChamber /></BoundedAdmin>} />
          <Route path="/admin/aawab" element={<BoundedAdmin roles={["admin"]} label="AAWAB Admin" backTo="/admin"><AdminAawabDashboard /></BoundedAdmin>} />
          <Route path="/landing" element={<LandingMarketplace />} />
          {/* WAI Institute — accredited-track portal (also the redirect target for wai-institute.org) */}
          <Route path="/wai-institute" element={<WAIInstitute />} />
          {/* Our Legacy, Our Future — the flagship book + campaign (public) */}
          <Route path="/our-legacy" element={<OurLegacy />} />
          {/* Vonns Saga — the multiverse choose-your-own-adventure (public) */}
          <Route path="/vonns-saga" element={<VonnsSaga />} />
          {/* Supervisor — executive_admin only; separate login at /supervisor-login */}
          <Route path="/supervisor-login" element={<SupervisorLogin />} />
          <Route path="/supervisor" element={<SupervisorProtected><SeshatsHub /></SupervisorProtected>} />
          <Route path="/auth/cross-site" element={<CrossSiteLogin />} />
          <Route path="/terms" element={<TermsOfService />} />
          <Route path="/privacy" element={<PrivacyPolicy />} />
          <Route path="/refund-policy" element={<RefundPolicy />} />
          <Route path="/courses" element={<Courses />} />
          <Route path="/ascension-protocols" element={<Protected><AscensionProtocols /></Protected>} />
          <Route path="/sponsor" element={<AdminPage><SponsorScholarship /></AdminPage>} />
          <Route path="/scholarships/apply" element={<Protected><ScholarshipApply /></Protected>} />
          <Route path="/admin/scholarships" element={<BoundedAdmin roles={["admin"]} label="Scholarship Committee" backTo="/admin"><AdminScholarships /></BoundedAdmin>} />
          <Route path="/studio/video-presenter" element={<VideoPresenter />} />
          <Route path="/admin/command" element={<BoundedAdmin roles={["executive_admin"]} label="Executive Command Center" backTo="/admin"><ExecutiveCommandCenter /></BoundedAdmin>} />
          <Route path="/community" element={<Community />} />
          <Route path="/creators" element={<Creators />} />
          <Route path="/instructor" element={<Protected roles={["instructor", "admin"]}><InstructorDashboard /></Protected>} />
          <Route path="/admin" element={<BoundedAdmin roles={["admin"]} label="Admin Dashboard"><AdminDashboard /></BoundedAdmin>} />
          <Route path="/admin/users" element={<BoundedAdmin roles={["admin"]} label="Admin Dashboard"><AdminDashboard /></BoundedAdmin>} />
          <Route path="/admin/iam" element={<BoundedAdmin roles={["admin"]} label="IAM Console" backTo="/admin"><IAMConsole /></BoundedAdmin>} />
          <Route path="/admin/accounts" element={<BoundedAdmin roles={["admin"]} label="Account Controls" backTo="/admin"><AccountControls /></BoundedAdmin>} />
          <Route path="/admin/associate" element={<BoundedAdmin roles={["admin"]} label="Admin Dashboard"><AdminDashboard /></BoundedAdmin>} />
          {/* Modules — public preview shows free intro modules; full catalog gated */}
          <Route path="/modules" element={<ModulesList />} />
          <Route path="/modules/:slug" element={<Protected><ModuleView /></Protected>} />
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
          <Route path="/adaptive" element={<Protected><TierGate feature="tracks"><Adaptive /></TierGate></Protected>} />
          <Route path="/compliance" element={<Protected><ComplianceList /></Protected>} />
          <Route path="/compliance/:slug" element={<Protected><ComplianceDetail /></Protected>} />
          <Route path="/admin/tools" element={<Navigate to="/admin" replace />} />
          <Route path="/admin/analytics" element={<BoundedAdmin roles={["admin"]} label="Analytics"><Analytics /></BoundedAdmin>} />
          <Route path="/admin/audit" element={<BoundedAdmin roles={["support_staff", "admin"]} label="Audit Log"><AuditLog /></BoundedAdmin>} />
          <Route path="/attendance" element={<Protected roles={["instructor", "admin"]}><Attendance /></Protected>} />
          <Route path="/incidents" element={<Protected><Incidents /></Protected>} />
          <Route path="/settings" element={<Protected><Settings /></Protected>} />
          <Route path="/my-position" element={<Protected><MyPosition /></Protected>} />
          <Route path="/personas" element={<AdminPage><Personas /></AdminPage>} />
          <Route path="/personas/:slug" element={<AdminPage><PersonaProfile /></AdminPage>} />
          <Route path="/admin/system" element={<Navigate to="/admin/command" replace />} />
          {/* Site Control Panel — executive_admin only, not linked from any nav */}
          <Route path="/admin/control" element={<BoundedAdmin roles={["executive_admin"]} label="Site Control Panel" backTo="/admin"><SiteControlPanel /></BoundedAdmin>} />
          <Route path="/admin/features" element={<BoundedAdmin roles={["admin"]} label="Feature Control Center" backTo="/admin"><FeatureControlCenter /></BoundedAdmin>} />
          <Route path="/admin/office" element={<BoundedAdmin roles={["executive_admin"]} label="Business Office" backTo="/admin"><ExecBusinessOffice /></BoundedAdmin>} />
          <Route path="/admin/exec-control" element={<Navigate to="/admin/office" replace />} />
          <Route path="/admin/director" element={<Navigate to="/admin/command" replace />} />
          <Route path="/admin/sage-audit" element={<BoundedAdmin roles={["executive_admin"]} label="Sage Audit" backTo="/admin"><SageAudit /></BoundedAdmin>} />
          <Route path="/admin/staff-meetings" element={<BoundedAdmin roles={["executive_admin"]} label="Staff Meetings" backTo="/admin"><StaffMeetingHistory /></BoundedAdmin>} />
          <Route path="/admin/exec-report" element={<BoundedAdmin roles={["executive_admin"]} label="Executive Site Report" backTo="/admin"><ExecutiveSiteReport /></BoundedAdmin>} />
          <Route path="/admin/health-report" element={<BoundedAdmin roles={["admin", "executive_admin"]} label="System Health" backTo="/admin"><SystemHealth /></BoundedAdmin>} />
          <Route path="/admin/health" element={<BoundedAdmin roles={["admin"]} label="System Health"><SystemHealth /></BoundedAdmin>} />
          <Route path="/admin/moderation" element={<BoundedAdmin roles={["support_staff", "admin"]} label="Moderation Analytics"><ModerationAnalytics /></BoundedAdmin>} />
          <Route path="/revenue" element={<BoundedAdmin roles={["admin", "executive_admin"]} label="Revenue Division"><RevenueDivision /></BoundedAdmin>} />
          <Route path="/council" element={<Protected><OrchestratorChat /></Protected>} />
          {/* Leaderboard — public read-only */}
          <Route path="/leaderboard" element={<Leaderboard />} />
          {/* Creator Studio — publish & manage courses */}
          <Route path="/creator/courses" element={<Protected><TierGate feature="courses"><CreatorCourses /></TierGate></Protected>} />
          {/* Creator earnings & payouts */}
          <Route path="/creator/earnings" element={<Protected><TierGate feature="earnings"><CreatorEarnings /></TierGate></Protected>} />
          {/* Creator profile editor → now lives in /profile Settings tab */}
          <Route path="/creator/profile/edit" element={<Navigate to="/profile" replace />} />
          {/* Creator slug → unified profile */}
          <Route path="/creator/:slug" element={<CreatorSlugRedirect />} />
          <Route path="/ghost-producer" element={<TierGate feature="ghost"><GhostProducer /></TierGate>} />
          <Route path="/creator-lounge" element={<Protected><TierGate feature="lounge"><CreatorLounge /></TierGate></Protected>} />
          <Route path="/band" element={<Protected><TierGate feature="band"><BandOnPage /></TierGate></Protected>} />
          <Route path="/trash-pantheon" element={<TrashPantheon />} />
          {/* Public pages */}
          <Route path="/internships" element={<Internships />} />
          {/* Social publisher — authenticated */}
          <Route path="/social/publish" element={<Protected><TierGate feature="publisher_ai"><SocialPublish /></TierGate></Protected>} />
          {/* Playlist curation — public submission form, private dashboard */}
          <Route path="/playlist/:slug/submit" element={<PlaylistSubmit />} />
          <Route path="/playlist/dashboard" element={<Protected><AdminPage><PlaylistDashboard /></AdminPage></Protected>} />
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
          <Route path="/admin/promo-codes" element={<BoundedAdmin roles={["admin"]} label="Promo Codes" backTo="/admin"><AdminPromoCodes /></BoundedAdmin>} />
          {/* Partnership & profile features */}
          <Route path="/partnership" element={<Protected><AdminPage><PartnershipDashboard /></AdminPage></Protected>} />
          <Route path="/partnership/discounts" element={<Protected><AdminPage><PartnershipDiscounts /></AdminPage></Protected>} />
          <Route path="/u/:username" element={<UnifiedProfile />} />
          <Route path="/profile" element={<Protected><UnifiedProfile /></Protected>} />
          <Route path="/profile/:id" element={<Protected><AdminPage><UserProfile /></AdminPage></Protected>} />
          {/* Lab simulations */}
          <Route path="/lab-simulations" element={<Protected><LabSimulations /></Protected>} />
          {/* Platform Prices — admin manage, exec delete */}
          <Route path="/admin/prices" element={<BoundedAdmin roles={["admin"]} label="Platform Prices"><AdminPage><PlatformPrices /></AdminPage></BoundedAdmin>} />
          {/* The Auditor — read-only ledger and reporting, admin+ */}
          <Route path="/auditor" element={<BoundedAdmin roles={["admin"]} label="Auditor Dashboard"><AuditorDashboard /></BoundedAdmin>} />
          {/* Provider Gateway — executive only */}
          <Route path="/admin/providers" element={<BoundedAdmin roles={["executive_admin"]} label="Provider Gateway" backTo="/admin/control"><AdminPage><ProviderGateway /></AdminPage></BoundedAdmin>} />
          <Route path="/team/ops" element={<BoundedAdmin roles={["executive_admin"]} label="Team Operations" backTo="/admin/control"><AdminPage><TeamOps /></AdminPage></BoundedAdmin>} />
          {/* Billing Admin — exec/admin */}
          <Route path="/admin/billing" element={<BoundedAdmin roles={["admin"]} label="Billing Admin"><AdminPage><BillingAdmin /></AdminPage></BoundedAdmin>} />
          {/* Original landing page (alternate entry point) */}
          <Route path="/assistant" element={<Protected><AdminPage><AdminAssistant /></AdminPage></Protected>} />
          <Route path="/byok" element={<Protected><BYOK /></Protected>} />
          <Route path="/creative-partner" element={<Protected roles={["instructor","executive_admin"]}><CreativePartnerHub /></Protected>} />
          <Route path="/s-research" element={<BoundedAdmin roles={["executive_admin"]} label="Sentinel Research" backTo="/admin"><SentinelResearch /></BoundedAdmin>} />
          <Route path="/arcade" element={<Protected><ArcadeLanding /></Protected>} />
          <Route path="/arcade/:slug" element={<Protected><ArcadeGame /></Protected>} />
          <Route path="/studio" element={<Protected><TierGate feature="studio"><CreatorStudio /></TierGate></Protected>} />
          <Route path="/arena" element={<BoundedAdmin roles={["executive_admin"]} label="The Arena"><CompetitionArena /></BoundedAdmin>} />
          <Route path="/executive-suite" element={<BoundedAdmin roles={["admin"]} label="Executive Suite"><ExecutiveSuite /></BoundedAdmin>} />
          <Route path="/admin/bridge" element={<BoundedAdmin roles={["admin"]} label="AI Team Bridge" backTo="/admin"><AITeamBridge /></BoundedAdmin>} />
          <Route path="/jamil" element={<BoundedAdmin roles={["admin"]} label="Jamil"><Jamil /></BoundedAdmin>} />
          <Route path="/projects" element={<BoundedAdmin roles={["admin"]} label="Projects"><ProjectDashboard /></BoundedAdmin>} />
          <Route path="/trash" element={<TrashPantheon />} />
          <Route path="/creator/payouts" element={<Protected><TierGate feature="payouts"><CreatorPayoutDashboard /></TierGate></Protected>} />
          <Route path="/welcome" element={<Landing />} />

          {/* ── CANONICAL ECOSYSTEM ROUTES (Step 8 — Route Migration) ── */}
          <Route path="/nam" element={<Navigate to="/ai" replace />} />
          <Route path="/creator" element={<Navigate to="/studio" replace />} />
          <Route path="/publish" element={<Navigate to="/social/publish" replace />} />
          <Route path="/community/hub" element={<Navigate to="/community" replace />} />
          <Route path="/marketplace" element={<Navigate to="/store" replace />} />
          <Route path="/sanctuary" element={<Navigate to="/helper" replace />} />
          <Route path="/music" element={<Navigate to="/band" replace />} />
          <Route path="/games" element={<Navigate to="/arcade" replace />} />

          {/* ── LEGACY REDIRECTS (Step 8 — remaining from prior merges) ── */}
          <Route path="/admin/exec-control" element={<Navigate to="/admin/office" replace />} />
          <Route path="/admin/system" element={<Navigate to="/admin/command" replace />} />
          <Route path="/admin/director" element={<Navigate to="/admin/command" replace />} />
          <Route path="/dashboard/exec" element={<Navigate to="/admin/command" replace />} />
          <Route path="/admin/health-report" element={<Navigate to="/admin/health" replace />} />
          <Route path="/admin/tools" element={<Navigate to="/admin" replace />} />

          <Route path="*" element={<Error404 />} />
        </Routes>
        </AccessGate>
        </div>
        </ErrorBoundary>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
