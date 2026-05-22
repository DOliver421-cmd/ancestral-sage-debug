import { useState, useEffect } from "react";
import {
  AlertTriangle,
  Activity,
  Users,
  TrendingUp,
  Lock,
  Ban,
  ShieldAlert,
  Settings,
  BarChart3,
} from "lucide-react";

/**
 * Executive Director Dashboard
 * CEO-level controls for platform governance and emergency response
 * Can immediately shut down threats, ban users, delete content
 */

export default function ExecutiveDirectorDashboard() {
  const [alerts, setAlerts] = useState([
    {
      id: 1,
      type: "hate_speech",
      severity: "critical",
      user: "user_567",
      content: "Post with hate speech reported 50 times",
      reportedAt: "2 minutes ago",
      actions: 50,
    },
    {
      id: 2,
      type: "fraud",
      severity: "critical",
      user: "creator_89",
      content: "Suspicious payout pattern detected (3 payouts in 1 hour)",
      reportedAt: "5 minutes ago",
      actions: 3,
    },
    {
      id: 3,
      type: "harassment",
      severity: "high",
      user: "user_234",
      content: "Harassment campaign detected in community",
      reportedAt: "15 minutes ago",
      actions: 12,
    },
  ]);

  const [activeTab, setActiveTab] = useState("threats");
  const [selectedAlert, setSelectedAlert] = useState(null);

  return (
    <div className="min-h-screen bg-bone text-ink">
      {/* Critical Alert Banner */}
      {alerts.some((a) => a.severity === "critical") && (
        <div className="bg-red-900 text-white p-4 border-b-4 border-red-700">
          <div className="max-w-7xl mx-auto flex items-center justify-between">
            <div className="flex items-center gap-3">
              <ShieldAlert className="w-6 h-6 animate-pulse" />
              <div>
                <p className="font-bold">CRITICAL THREATS DETECTED</p>
                <p className="text-sm">{alerts.filter((a) => a.severity === "critical").length} require immediate action</p>
              </div>
            </div>
            <button className="px-4 py-2 bg-red-700 hover:bg-red-800 rounded font-bold">
              EMERGENCY MODE
            </button>
          </div>
        </div>
      )}

      {/* Header */}
      <div className="border-b border-ink/10 bg-white">
        <div className="max-w-7xl mx-auto px-6 py-8">
          <h1 className="font-heading text-4xl font-bold mb-2">Executive Director</h1>
          <p className="text-ink/60">Platform governance, crisis management, strategic oversight</p>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="grid md:grid-cols-5 gap-4 mb-8">
          <div className="bg-white border border-ink/10 rounded-lg p-6">
            <div className="flex items-center gap-3 mb-4">
              <AlertTriangle className="w-5 h-5 text-red-600" />
              <span className="text-sm text-ink/60 font-bold">CRITICAL</span>
            </div>
            <p className="text-4xl font-bold text-red-600">{alerts.filter((a) => a.severity === "critical").length}</p>
            <p className="text-xs text-ink/60 mt-2">Immediate action needed</p>
          </div>

          <div className="bg-white border border-ink/10 rounded-lg p-6">
            <div className="flex items-center gap-3 mb-4">
              <ShieldAlert className="w-5 h-5 text-orange-600" />
              <span className="text-sm text-ink/60 font-bold">HIGH</span>
            </div>
            <p className="text-4xl font-bold text-orange-600">{alerts.filter((a) => a.severity === "high").length}</p>
            <p className="text-xs text-ink/60 mt-2">Review in 1 hour</p>
          </div>

          <div className="bg-white border border-ink/10 rounded-lg p-6">
            <div className="flex items-center gap-3 mb-4">
              <Users className="w-5 h-5 text-ink" />
              <span className="text-sm text-ink/60 font-bold">USERS</span>
            </div>
            <p className="text-4xl font-bold text-ink">2,847</p>
            <p className="text-xs text-green-600">+12 active now</p>
          </div>

          <div className="bg-white border border-ink/10 rounded-lg p-6">
            <div className="flex items-center gap-3 mb-4">
              <TrendingUp className="w-5 h-5 text-green-600" />
              <span className="text-sm text-ink/60 font-bold">REVENUE</span>
            </div>
            <p className="text-4xl font-bold text-green-600">$12.4K</p>
            <p className="text-xs text-ink/60 mt-2">This month</p>
          </div>

          <div className="bg-white border border-ink/10 rounded-lg p-6">
            <div className="flex items-center gap-3 mb-4">
              <Activity className="w-5 h-5 text-ink" />
              <span className="text-sm text-ink/60 font-bold">STATUS</span>
            </div>
            <p className="text-4xl font-bold text-green-600">●</p>
            <p className="text-xs text-green-600">All systems normal</p>
          </div>
        </div>

        {/* Tabs */}
        <div className="border-b border-ink/10 flex gap-8 mb-8">
          <button
            onClick={() => setActiveTab("threats")}
            className={`py-3 font-bold border-b-2 transition-all ${
              activeTab === "threats"
                ? "border-red-600 text-red-600"
                : "border-transparent text-ink/60 hover:text-ink"
            }`}
          >
            🚨 Threats ({alerts.length})
          </button>
          <button
            onClick={() => setActiveTab("users")}
            className={`py-3 font-bold border-b-2 transition-all ${
              activeTab === "users"
                ? "border-copper text-copper"
                : "border-transparent text-ink/60 hover:text-ink"
            }`}
          >
            👥 User Management
          </button>
          <button
            onClick={() => setActiveTab("controls")}
            className={`py-3 font-bold border-b-2 transition-all ${
              activeTab === "controls"
                ? "border-copper text-copper"
                : "border-transparent text-ink/60 hover:text-ink"
            }`}
          >
            ⚙️ Emergency Controls
          </button>
          <button
            onClick={() => setActiveTab("logs")}
            className={`py-3 font-bold border-b-2 transition-all ${
              activeTab === "logs"
                ? "border-copper text-copper"
                : "border-transparent text-ink/60 hover:text-ink"
            }`}
          >
            📋 Audit Logs
          </button>
        </div>

        {/* THREATS TAB */}
        {activeTab === "threats" && (
          <div className="space-y-4">
            {alerts.map((alert) => (
              <div
                key={alert.id}
                className={`p-6 border-l-4 rounded-lg ${
                  alert.severity === "critical"
                    ? "bg-red-50 border-red-600"
                    : "bg-orange-50 border-orange-600"
                }`}
              >
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <p className="font-bold text-lg text-ink">{alert.type.replace("_", " ").toUpperCase()}</p>
                    <p className="text-sm text-ink/70 mt-1">{alert.content}</p>
                    <p className="text-xs text-ink/60 mt-2">User: {alert.user} • {alert.actions} reports</p>
                  </div>
                  <span className={`text-xs font-bold px-3 py-1 rounded ${
                    alert.severity === "critical"
                      ? "bg-red-600 text-white"
                      : "bg-orange-600 text-white"
                  }`}>
                    {alert.severity.toUpperCase()}
                  </span>
                </div>

                {/* Quick Actions */}
                <div className="flex gap-2 mt-4 pt-4 border-t border-ink/10">
                  <button className="flex-1 py-2 px-3 bg-red-600 text-white rounded font-bold hover:bg-red-700 transition-colors flex items-center justify-center gap-2 text-sm">
                    <Ban className="w-4 h-4" />
                    BAN USER
                  </button>
                  <button className="flex-1 py-2 px-3 bg-red-500 text-white rounded font-bold hover:bg-red-600 transition-colors flex items-center justify-center gap-2 text-sm">
                    <AlertTriangle className="w-4 h-4" />
                    DELETE CONTENT
                  </button>
                  <button className="flex-1 py-2 px-3 bg-orange-600 text-white rounded font-bold hover:bg-orange-700 transition-colors flex items-center justify-center gap-2 text-sm">
                    <Lock className="w-4 h-4" />
                    LOCK ACCOUNT
                  </button>
                  <button className="flex-1 py-2 px-3 border-2 border-ink/20 rounded font-bold hover:bg-ink/5 transition-colors text-sm">
                    Review
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* EMERGENCY CONTROLS TAB */}
        {activeTab === "controls" && (
          <div className="max-w-2xl space-y-6">
            <div className="bg-red-50 border-2 border-red-600 rounded-lg p-8">
              <h2 className="font-heading text-2xl font-bold text-red-900 mb-6">Emergency Controls</h2>

              <div className="space-y-4">
                {/* Lock Platform */}
                <div className="bg-white p-6 rounded border-l-4 border-red-600">
                  <h3 className="font-bold text-lg text-ink mb-2">🔒 Lock Platform (Everyone read-only)</h3>
                  <p className="text-sm text-ink/70 mb-4">
                    Prevents all writes. Users can view but not post, enroll, publish. Emergency mode only.
                  </p>
                  <button className="px-6 py-3 bg-red-600 text-white rounded font-bold hover:bg-red-700">
                    LOCK PLATFORM
                  </button>
                </div>

                {/* Shut Down Feature */}
                <div className="bg-white p-6 rounded border-l-4 border-red-600">
                  <h3 className="font-bold text-lg text-ink mb-2">⛔ Shut Down Marketplace</h3>
                  <p className="text-sm text-ink/70 mb-4">
                    Prevent new enrollments and course publishing. Existing access continues.
                  </p>
                  <button className="px-6 py-3 bg-red-600 text-white rounded font-bold hover:bg-red-700">
                    SHUT DOWN MARKETPLACE
                  </button>
                </div>

                {/* Ban by IP */}
                <div className="bg-white p-6 rounded border-l-4 border-orange-600">
                  <h3 className="font-bold text-lg text-ink mb-2">🚫 Ban by IP Address</h3>
                  <p className="text-sm text-ink/70 mb-4">
                    Block entire IP ranges for coordinated attacks.
                  </p>
                  <input
                    type="text"
                    placeholder="e.g., 192.168.1.0/24"
                    className="w-full px-4 py-2 border border-ink/20 rounded mb-4"
                  />
                  <button className="px-6 py-3 bg-orange-600 text-white rounded font-bold hover:bg-orange-700">
                    BAN IP RANGE
                  </button>
                </div>

                {/* Disable Feature */}
                <div className="bg-white p-6 rounded border-l-4 border-orange-600">
                  <h3 className="font-bold text-lg text-ink mb-2">⚠️ Disable Feature</h3>
                  <p className="text-sm text-ink/70 mb-4">
                    Quickly disable problematic features (comments, messaging, etc).
                  </p>
                  <select className="w-full px-4 py-2 border border-ink/20 rounded mb-4">
                    <option>Select feature...</option>
                    <option>Community comments</option>
                    <option>Direct messaging</option>
                    <option>Course reviews</option>
                    <option>Marketplace</option>
                    <option>Payouts</option>
                  </select>
                  <button className="px-6 py-3 bg-orange-600 text-white rounded font-bold hover:bg-orange-700">
                    DISABLE FEATURE
                  </button>
                </div>

                {/* Broadcast Emergency Message */}
                <div className="bg-white p-6 rounded border-l-4 border-yellow-600">
                  <h3 className="font-bold text-lg text-ink mb-2">📢 Broadcast Emergency Message</h3>
                  <p className="text-sm text-ink/70 mb-4">
                    Show banner to all users explaining situation.
                  </p>
                  <textarea
                    className="w-full px-4 py-2 border border-ink/20 rounded mb-4 h-24"
                    placeholder="e.g., We're experiencing an issue with payments. Please check back in 1 hour."
                  />
                  <button className="px-6 py-3 bg-yellow-600 text-white rounded font-bold hover:bg-yellow-700">
                    SEND MESSAGE
                  </button>
                </div>
              </div>
            </div>

            {/* Control Log */}
            <div className="bg-white border border-ink/10 rounded-lg p-6">
              <h3 className="font-bold text-lg mb-4">Recent Control Actions</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between py-2 border-b border-ink/10">
                  <span>Platform locked by Director</span>
                  <span className="text-ink/60">5 min ago</span>
                </div>
                <div className="flex justify-between py-2 border-b border-ink/10">
                  <span>IP range 203.0.113.0/24 banned</span>
                  <span className="text-ink/60">12 min ago</span>
                </div>
                <div className="flex justify-between py-2">
                  <span>Marketplace shut down (read-only)</span>
                  <span className="text-ink/60">18 min ago</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* AUDIT LOGS TAB */}
        {activeTab === "logs" && (
          <div className="bg-white border border-ink/10 rounded-lg p-6">
            <h2 className="font-bold text-lg mb-6">Audit Log (All Admin Actions)</h2>
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {[
                { time: "2:47 PM", action: "User banned: creator_89", by: "Director", reason: "Fraud investigation" },
                { time: "2:45 PM", action: "Content deleted: post_567", by: "Director", reason: "Hate speech" },
                { time: "2:43 PM", action: "Platform locked (read-only)", by: "Director", reason: "Security threat" },
                { time: "2:40 PM", action: "IP ban: 203.0.113.0/24", by: "Director", reason: "Spam attacks" },
                { time: "2:30 PM", action: "User reported: user_234", by: "Moderator James", reason: "Harassment" },
              ].map((log, idx) => (
                <div key={idx} className="flex justify-between py-3 border-b border-ink/10 text-sm">
                  <div>
                    <p className="font-bold text-ink">{log.action}</p>
                    <p className="text-xs text-ink/60">{log.reason}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-ink/60">{log.time}</p>
                    <p className="text-xs text-copper">{log.by}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
