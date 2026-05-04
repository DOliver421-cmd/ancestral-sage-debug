import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "sonner";
import "./App.css";
import { AuthProvider, useAuth } from "./lib/auth";
import Landing from "./pages/Landing";
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

function Protected({ children, roles }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="p-12 text-ink font-heading">Loading…</div>;
  if (!user) return <Navigate to="/login" replace />;
  if (roles && !roles.includes(user.role)) return <Navigate to="/dashboard" replace />;
  return children;
}

function Home() {
  const { user, loading } = useAuth();
  if (loading) return null;
  if (!user) return <Landing />;
  if (user.role === "admin") return <Navigate to="/admin" replace />;
  if (user.role === "instructor") return <Navigate to="/instructor" replace />;
  return <Navigate to="/dashboard" replace />;
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Toaster position="top-right" richColors />
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/dashboard" element={<Protected><StudentDashboard /></Protected>} />
          <Route path="/instructor" element={<Protected roles={["instructor", "admin"]}><InstructorDashboard /></Protected>} />
          <Route path="/admin" element={<Protected roles={["admin"]}><AdminDashboard /></Protected>} />
          <Route path="/admin/users" element={<Protected roles={["admin"]}><AdminDashboard /></Protected>} />
          <Route path="/admin/associate" element={<Protected roles={["admin"]}><AdminDashboard /></Protected>} />
          <Route path="/modules" element={<Protected><ModulesList /></Protected>} />
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
          <Route path="/adaptive" element={<Protected><Adaptive /></Protected>} />
          <Route path="/compliance" element={<Protected><ComplianceList /></Protected>} />
          <Route path="/compliance/:slug" element={<Protected><ComplianceDetail /></Protected>} />
          <Route path="/admin/tools" element={<Protected roles={["admin"]}><AdminTools /></Protected>} />
          <Route path="/admin/analytics" element={<Protected roles={["admin"]}><Analytics /></Protected>} />
          <Route path="/admin/audit" element={<Protected roles={["admin"]}><AuditLog /></Protected>} />
          <Route path="/attendance" element={<Protected roles={["instructor", "admin"]}><Attendance /></Protected>} />
          <Route path="/incidents" element={<Protected><Incidents /></Protected>} />
          <Route path="/settings" element={<Protected><Settings /></Protected>} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
