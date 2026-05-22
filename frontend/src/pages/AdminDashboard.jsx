import { useState, useEffect } from "react";
import {
  AlertTriangle,
  Users,
  Trash2,
  Ban,
  ShieldAlert,
  CheckCircle,
  Clock,
  Activity,
  TrendingDown,
  MessageSquare,
  Flag,
  Lock,
} from "lucide-react";

/**
 * Moderation & Governance Dashboard
 * For Moderators, Stewards, and Elders to manage community content and users
 * Escalation path to Executive Director for platform-level threats
 */

export default function AdminDashboard() {
  const [activeTab, setActiveTab] = useState("reports");
  const [reports, setReports] = useState([
    {
      id: 1,
      type: "hate_speech",
      severity: "critical",
      reportedUser: "user_567",
      content: "Post with hate speech reported 47 times",
      reportCount: 47,
      reportedAt: "2 minutes ago",
      status: "open",
      reason: "Violates community standards"
    },
    {
      id: 2,
      type: "harassment",
      severity: "high",
      reportedUser: "user_234",
      content: "Harassment campaign in community discussion",
      reportCount: 12,
      reportedAt: "15 minutes ago",
      status: "open",
      reason: "Targeted abuse"
    },
    {
      id: 3,
      type: "spam",
      severity: "medium",
      reportedUser: "user_891",
      content: "Repeated promotional messages",
      reportCount: 5,
      reportedAt: "45 minutes ago",
      status: "investigating",
      reason: "Commercial spam"
    },
  ]);

  const [suspiciousUsers, setSuspiciousUsers] = useState([
    {
      id: 1,
      username: "user_567",
      email: "user567@example.com",
      riskScore: 92,
      flags: ["hate_speech", "multiple_reports", "account_3_days_old"],
      activeReports: 5,
      joinedAt: "May 19, 2026"
    },
    {
      id: 2,
      username: "creator_89",
      email: "creator89@example.com",
      riskScore: 68,
      flags: ["fraud_pattern", "suspicious_payouts"],
      activeReports: 1,
      joinedAt: "Jan 15, 2025"
    },
    {
      id: 3,
      username: "user_234",
      email: "user234@example.com",
      riskScore: 85,
      flags: ["coordinated_harassment", "ban_evasion_suspected"],
      activeReports: 3,
      joinedAt: "Mar 22, 2026"
    },
  ]);

  const [actionLog, setActionLog] = useState([
    { time: "2:47 PM", action: "Content deleted: post_567", by: "Moderator James", reason: "Hate speech", status: "completed" },
    { time: "2:30 PM", action: "User warned: user_234", by: "Moderator James", reason: "Harassment", status: "completed" },
    { time: "2:15 PM", action: "Escalated to Director: creator_89", by: "Steward Maria", reason: "Possible fraud pattern", status: "pending_director" },
    { time: "1:45 PM", action: "Account locked: user_567", by: "Moderator James", reason: "Critical severity report", status: "completed" },
  ]);

  const [userRole] = useState("steward"); // Mock: would come from auth context

  // Permission checks based on role
  const canDelete = ["moderator", "steward", "elder", "admin"].includes(userRole);
  const canBan = ["moderator", "steward", "elder", "admin"].includes(userRole);
  const canEscalate = ["steward", "elder", "admin"].includes(userRole);
  const canLockPlatform = ["elder", "admin"].includes(userRole); // Director-only feature

  const handleDeleteContent = (reportId) => {
    if (!canDelete) {
      alert("You don't have permission to delete content");
      return;
    }
    if (window.confirm("Delete this content? This action cannot be undone.")) {
      setReports(reports.map(r => r.id === reportId ? { ...r, status: "resolved" } : r));
      setActionLog([
        { time: new Date().toLocaleTimeString(), action: `Content deleted: report_${reportId}`, by: "You", reason: "Moderator action", status: "completed" },
        ...actionLog
      ]);
    }
  };

  const handleBanUser = (userId) => {
    if (!canBan) {
      alert("You don't have permission to ban users");
      return;
    }
    if (window.confirm("Ban this user from the platform?")) {
      setSuspiciousUsers(suspiciousUsers.filter(u => u.id !== userId));
      setActionLog([
        { time: new Date().toLocaleTimeString(), action: `User banned: ${userId}`, by: "You", reason: "Moderation decision", status: "completed" },
        ...actionLog
      ]);
    }
  };

  const handleWarnUser = (userId) => {
    if (!canDelete) {
      alert("You don't have permission to warn users");
      return;
    }
    if (window.confirm("Send warning to this user?")) {
      setActionLog([
        { time: new Date().toLocaleTimeString(), action: `User warned: user_${userId}`, by: "You", reason: "Community violation", status: "completed" },
        ...actionLog
      ]);
    }
  };

  const handleEscalate = (reportId) => {
    if (!canEscalate) {
      alert("Only Steward+ can escalate to Director");
      return;
    }
    if (window.confirm("Escalate this report to the Executive Director? They have platform-level controls.")) {
      setReports(reports.map(r => r.id === reportId ? { ...r, status: "escalated_to_director" } : r));
      setActionLog([
        { time: new Date().toLocaleTimeString(), action: `Escalated to Director: report_${reportId}`, by: "You", reason: "High-severity threat", status: "pending_director" },
        ...actionLog
      ]);
    }
  };

  return (
    <div className="min-h-screen bg-bone text-ink">
      {/* Header */}
      <div className="border-b border-ink/10 bg-white">
        <div className="max-w-7xl mx-auto px-6 py-8">
          <h1 className="font-heading text-4xl font-bold mb-2">Moderation & Governance</h1>
          <p className="text-ink/60">Manage community content, handle reports, and escalate to leadership</p>
          <div className="mt-4 text-sm text-ink/70">
            Role: <span className="font-bold capitalize">{userRole}</span>
            {canEscalate && <span className="ml-4 text-copper">✓ Can escalate to Director</span>}
            {canDelete && <span className="ml-4">✓ Can delete/ban</span>}
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="max-w-7xl mx-auto px-6">
        <div className="border-b border-ink/10 flex gap-8 mt-0">
          <button
            onClick={() => setActiveTab("reports")}
            className={`py-4 font-bold border-b-2 transition-all ${
              activeTab === "reports"
                ? "border-red-600 text-red-600"
                : "border-transparent text-ink/60 hover:text-ink"
            }`}
          >
            🚨 Reported Content ({reports.filter(r => r.status === "open").length})
          </button>
          <button
            onClick={() => setActiveTab("suspicious")}
            className={`py-4 font-bold border-b-2 transition-all ${
              activeTab === "suspicious"
                ? "border-orange-600 text-orange-600"
                : "border-transparent text-ink/60 hover:text-ink"
            }`}
          >
            ⚠️ Suspicious Users ({suspiciousUsers.length})
          </button>
          <button
            onClick={() => setActiveTab("actions")}
            className={`py-4 font-bold border-b-2 transition-all ${
              activeTab === "actions"
                ? "border-copper text-copper"
                : "border-transparent text-ink/60 hover:text-ink"
            }`}
          >
            📋 Action Log ({actionLog.length})
          </button>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* REPORTED CONTENT TAB */}
        {activeTab === "reports" && (
          <div className="space-y-4">
            {reports.length === 0 ? (
              <div className="bg-white border border-ink/10 rounded-lg p-8 text-center text-ink/60">
                No reports at this time. Community is healthy.
              </div>
            ) : (
              reports.map((report) => (
                <div
                  key={report.id}
                  className={`p-6 border-l-4 rounded-lg ${
                    report.status === "open"
                      ? "bg-red-50 border-red-600"
                      : report.status === "escalated_to_director"
                      ? "bg-purple-50 border-purple-600"
                      : "bg-green-50 border-green-600"
                  }`}
                >
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <p className="font-bold text-lg text-ink">{report.type.replace("_", " ").toUpperCase()}</p>
                      <p className="text-sm text-ink/70 mt-1">{report.content}</p>
                      <p className="text-xs text-ink/60 mt-2">
                        User: {report.reportedUser} • {report.reportCount} reports • Status: {report.status.replace("_", " ")}
                      </p>
                    </div>
                    <span className={`text-xs font-bold px-3 py-1 rounded ${
                      report.severity === "critical"
                        ? "bg-red-600 text-white"
                        : report.severity === "high"
                        ? "bg-orange-600 text-white"
                        : "bg-yellow-600 text-white"
                    }`}>
                      {report.severity.toUpperCase()}
                    </span>
                  </div>

                  {/* Actions */}
                  <div className="flex gap-2 mt-4 pt-4 border-t border-ink/10">
                    {report.status === "open" && (
                      <>
                        {canDelete && (
                          <button
                            onClick={() => handleDeleteContent(report.id)}
                            className="flex-1 py-2 px-3 bg-red-600 text-white rounded font-bold hover:bg-red-700 transition-colors flex items-center justify-center gap-2 text-sm"
                          >
                            <Trash2 className="w-4 h-4" />
                            DELETE CONTENT
                          </button>
                        )}
                        {canBan && (
                          <button
                            onClick={() => handleBanUser(report.reportedUser)}
                            className="flex-1 py-2 px-3 bg-red-600 text-white rounded font-bold hover:bg-red-700 transition-colors flex items-center justify-center gap-2 text-sm"
                          >
                            <Ban className="w-4 h-4" />
                            BAN USER
                          </button>
                        )}
                        <button
                          onClick={() => handleWarnUser(report.reportedUser)}
                          className="flex-1 py-2 px-3 bg-orange-600 text-white rounded font-bold hover:bg-orange-700 transition-colors flex items-center justify-center gap-2 text-sm"
                        >
                          <AlertTriangle className="w-4 h-4" />
                          WARN USER
                        </button>
                        {canEscalate && (
                          <button
                            onClick={() => handleEscalate(report.id)}
                            className="flex-1 py-2 px-3 bg-purple-600 text-white rounded font-bold hover:bg-purple-700 transition-colors flex items-center justify-center gap-2 text-sm"
                          >
                            <ShieldAlert className="w-4 h-4" />
                            ESCALATE
                          </button>
                        )}
                      </>
                    )}
                    {report.status === "escalated_to_director" && (
                      <div className="w-full py-2 px-3 bg-purple-100 text-purple-700 rounded text-sm font-bold text-center">
                        ⬆️ Awaiting Director action
                      </div>
                    )}
                    {report.status === "resolved" && (
                      <div className="w-full py-2 px-3 bg-green-100 text-green-700 rounded text-sm font-bold text-center">
                        ✓ Resolved
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {/* SUSPICIOUS USERS TAB */}
        {activeTab === "suspicious" && (
          <div className="space-y-4">
            {suspiciousUsers.map((user) => (
              <div key={user.id} className="bg-white border border-ink/10 rounded-lg p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-3">
                      <div>
                        <p className="font-bold text-lg text-ink">{user.username}</p>
                        <p className="text-sm text-ink/60 font-mono">{user.email}</p>
                        <p className="text-xs text-ink/60 mt-1">Joined {user.joinedAt}</p>
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className={`text-3xl font-bold ${
                      user.riskScore >= 80 ? "text-red-600" : user.riskScore >= 60 ? "text-orange-600" : "text-yellow-600"
                    }`}>
                      {user.riskScore}
                    </div>
                    <p className="text-xs text-ink/60">Risk Score</p>
                  </div>
                </div>

                <div className="mb-4">
                  <p className="text-xs text-ink/60 mb-2">Flags:</p>
                  <div className="flex flex-wrap gap-2">
                    {user.flags.map((flag, idx) => (
                      <span key={idx} className="px-2 py-1 bg-orange-100 text-orange-700 text-xs rounded">
                        {flag.replace(/_/g, " ")}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="flex gap-2 pt-4 border-t border-ink/10">
                  <button
                    onClick={() => handleWarnUser(user.id)}
                    className="flex-1 py-2 px-3 bg-orange-600 text-white rounded font-bold hover:bg-orange-700 transition-colors text-sm"
                  >
                    Warn
                  </button>
                  {canBan && (
                    <button
                      onClick={() => handleBanUser(user.id)}
                      className="flex-1 py-2 px-3 bg-red-600 text-white rounded font-bold hover:bg-red-700 transition-colors text-sm"
                    >
                      Ban User
                    </button>
                  )}
                  {canEscalate && (
                    <button
                      onClick={() => window.confirm("Escalate to Director?")}
                      className="flex-1 py-2 px-3 bg-purple-600 text-white rounded font-bold hover:bg-purple-700 transition-colors text-sm"
                    >
                      Escalate
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* ACTION LOG TAB */}
        {activeTab === "actions" && (
          <div className="bg-white border border-ink/10 rounded-lg p-6">
            <h3 className="font-bold text-lg mb-6">Moderation Action Log</h3>
            <div className="space-y-2">
              {actionLog.map((log, idx) => (
                <div key={idx} className="flex justify-between py-3 border-b border-ink/10 text-sm">
                  <div className="flex-1">
                    <p className="font-bold text-ink">{log.action}</p>
                    <p className="text-xs text-ink/60">{log.reason}</p>
                  </div>
                  <div className="text-right ml-4">
                    <p className="text-ink/60 text-xs">{log.time}</p>
                    <p className="text-xs font-bold text-copper">{log.by}</p>
                    <span className={`inline-block mt-1 text-xs px-2 py-1 rounded ${
                      log.status === "completed" ? "bg-green-100 text-green-700" : "bg-yellow-100 text-yellow-700"
                    }`}>
                      {log.status.replace(/_/g, " ")}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Permission Info */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-sm text-blue-700">
          <p className="font-bold mb-2">Permission Summary for {userRole.toUpperCase()}:</p>
          <ul className="text-xs space-y-1">
            {canDelete && <li>✓ Can delete content and issue warnings</li>}
            {canBan && <li>✓ Can ban users from platform</li>}
            {canEscalate && <li>✓ Can escalate reports to Executive Director (platform-level action)</li>}
            {!canLockPlatform && <li className="text-blue-600">ℹ️ Only Directors can lock the platform or shut down features</li>}
          </ul>
        </div>
      </div>
    </div>
  );
}
