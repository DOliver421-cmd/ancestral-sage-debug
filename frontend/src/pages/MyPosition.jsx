import { useState, useEffect } from "react";
import AppShell from "../components/AppShell";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import { toast } from "sonner";
import {
  User, LogOut, ChevronDown, Pause, DollarSign,
  CheckCircle, AlertTriangle, Loader2, X, Clock,
} from "lucide-react";

function formatEventLabel(action, meta) {
  switch (action) {
    case "auth.register.success": return "Joined the platform";
    case "position.step_down": return `Stepped down from ${ROLE_LABELS[meta?.from_role] || meta?.from_role} to ${ROLE_LABELS[meta?.to_role] || meta?.to_role}`;
    case "position.exit_requested": return "Requested to go inactive";
    case "position.exit_cancelled": return "Cancelled exit request";
    case "position.emergency_exit": return "Left via emergency exit";
    case "position.leave_more": return "Left M.O.R.E. community membership";
    case "position.proceeds_preference_set": return `Set proceeds preference to: ${meta?.preference}`;
    case "position.self_deactivate": return "Account paused";
    default: return action;
  }
}

const ROLE_LABELS = {
  student: "Member",
  instructor: "Instructor",
  admin: "Administrator",
  executive_admin: "Executive",
};

const PROCEEDS_OPTIONS = [
  {
    id: "reinvest",
    label: "Reinvest into the platform",
    desc: "Your share goes back into operations, tools, and infrastructure that everyone uses.",
  },
  {
    id: "donate",
    label: "Donate to community fund",
    desc: "Directed to the M.O.R.E. community fund — direct aid, skills support, elder care.",
  },
  {
    id: "hold",
    label: "Hold in my account",
    desc: "Accumulated in your account until you decide. No expiry.",
  },
  {
    id: "payout",
    label: "Pay out to me",
    desc: "Sent to your registered payment method on the normal payout cycle.",
  },
];

export default function MyPosition() {
  const { user, refresh } = useAuth();
  const [position, setPosition] = useState(null);
  const [loading, setLoading] = useState(true);
  const [modal, setModal] = useState(null); // "step-down" | "inactive" | "leave-more" | "proceeds"
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState(false);
  const [proceedsChoice, setProceedsChoice] = useState(null);
  const [savedProceeds, setSavedProceeds] = useState(null);
  const [history, setHistory] = useState([]);

  const load = async () => {
    try {
      const [posRes, procRes, histRes] = await Promise.allSettled([
        api.get("/me/position"),
        api.get("/me/proceeds-preference"),
        api.get("/me/position/history"),
      ]);
      if (posRes.status === "fulfilled") setPosition(posRes.value.data);
      if (histRes.status === "fulfilled") setHistory(histRes.value.data?.history || []);
      if (procRes.status === "fulfilled") {
        const pref = procRes.value.data?.preference;
        setSavedProceeds(pref || null);
        setProceedsChoice(pref || "reinvest");
      } else {
        setProceedsChoice("reinvest");
      }
    } catch {
      toast.error("Couldn't load your position. Try refreshing.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const closeModal = () => { setModal(null); setReason(""); };

  const handleStepDown = async () => {
    if (reason.trim().length < 10) return toast.error("Please add a few words — just for the record.");
    setBusy(true);
    try {
      const r = await api.post("/me/step-down", { reason: reason.trim() });
      toast.success(r.data.message);
      closeModal();
      await refresh?.();
      await load();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Something went wrong.");
    } finally {
      setBusy(false);
    }
  };

  const handleRequestExit = async () => {
    if (reason.trim().length < 10) return toast.error("Please share a bit more — just a sentence or two.");
    setBusy(true);
    try {
      const r = await api.post("/me/request-exit", { reason: reason.trim() });
      toast.success(r.data.message);
      closeModal();
      await load();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Something went wrong.");
    } finally {
      setBusy(false);
    }
  };

  const handleEmergencyExit = async () => {
    if (reason.trim().length < 10) return toast.error("Please share what's happening — even briefly.");
    setBusy(true);
    try {
      const r = await api.post("/me/emergency-exit", { reason: reason.trim() });
      toast.success(r.data.message);
      closeModal();
      localStorage.removeItem("lce_token");
      localStorage.removeItem("lce_user");
      setTimeout(() => { window.location.href = "/"; }, 1500);
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Something went wrong.");
    } finally {
      setBusy(false);
    }
  };

  const handleCancelExit = async () => {
    setBusy(true);
    try {
      const r = await api.post("/me/cancel-exit");
      toast.success(r.data.message);
      await load();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Something went wrong.");
    } finally {
      setBusy(false);
    }
  };

  const handleLeaveMore = async () => {
    setBusy(true);
    try {
      const r = await api.post("/me/leave-more");
      toast.success(r.data.message);
      closeModal();
      await load();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Something went wrong.");
    } finally {
      setBusy(false);
    }
  };

  const handleSaveProceeds = async () => {
    setBusy(true);
    try {
      await api.post("/me/proceeds-preference", { preference: proceedsChoice });
      setSavedProceeds(proceedsChoice);
      toast.success("Proceeds preference saved.");
      closeModal();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Couldn't save preference.");
    } finally {
      setBusy(false);
    }
  };

  if (loading) {
    return (
      <AppShell>
        <div className="flex items-center justify-center h-64">
          <Loader2 className="w-6 h-6 animate-spin text-copper" />
        </div>
      </AppShell>
    );
  }

  const roleLabel = ROLE_LABELS[position?.role] || position?.role;
  const savedProceedsOption = PROCEEDS_OPTIONS.find((o) => o.id === savedProceeds);

  return (
    <AppShell>
      <div className="px-6 py-10 max-w-2xl mx-auto space-y-8">

        {/* Header */}
        <div>
          <div className="overline text-copper text-xs">Your standing</div>
          <h1 className="font-heading text-3xl font-bold mt-1">My Position</h1>
          <p className="text-ink/50 text-sm mt-2">
            This is yours to manage. No approval needed.
          </p>
        </div>

        {/* Identity card */}
        <div className="bg-white border border-ink/10 rounded-2xl p-6">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-full bg-copper/10 flex items-center justify-center flex-shrink-0">
              <User className="w-6 h-6 text-copper" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="font-heading font-bold text-lg">{position?.full_name}</div>
              <div className="text-sm text-ink/50">{position?.email}</div>
              {position?.associate && (
                <div className="text-xs text-ink/40 mt-0.5 font-mono">{position.associate}</div>
              )}
            </div>
            <span className="flex-shrink-0 text-xs font-bold px-3 py-1 bg-copper/10 text-copper rounded-full uppercase tracking-wide">
              {roleLabel}
            </span>
          </div>
          <p className="mt-4 text-sm text-ink/70 leading-relaxed border-t border-ink/5 pt-4">
            {position?.role_description}
          </p>
          {position?.created_at && (
            <p className="text-xs text-ink/30 mt-3">
              Member since {new Date(position.created_at).toLocaleDateString("en-US", { year: "numeric", month: "long" })}
            </p>
          )}
        </div>

        {/* Proceeds preference */}
        <div className="bg-white border border-ink/10 rounded-2xl p-6">
          <div className="flex items-start justify-between gap-4">
            <div>
              <div className="flex items-center gap-2">
                <DollarSign className="w-4 h-4 text-copper" />
                <h2 className="font-heading font-bold">Proceeds Preference</h2>
              </div>
              <p className="text-sm text-ink/50 mt-1">
                How your share of platform proceeds is handled. Your call, always.
              </p>
            </div>
            <button
              onClick={() => setModal("proceeds")}
              className="flex-shrink-0 text-sm font-bold text-copper hover:text-copper/80 transition-colors"
            >
              Change
            </button>
          </div>
          <div className="mt-4 p-4 bg-bone rounded-xl">
            {savedProceedsOption ? (
              <div>
                <div className="font-bold text-sm">{savedProceedsOption.label}</div>
                <div className="text-xs text-ink/50 mt-0.5">{savedProceedsOption.desc}</div>
              </div>
            ) : (
              <div className="text-sm text-ink/40 italic">Not set — defaults to reinvesting into the platform.</div>
            )}
          </div>
        </div>

        {/* M.O.R.E. membership */}
        {position?.more_member && (
          <div className="bg-white border border-ink/10 rounded-2xl p-6">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h2 className="font-heading font-bold">M.O.R.E. Membership</h2>
                {position.more_member_since && (
                  <p className="text-xs text-ink/40 mt-0.5">
                    Since {new Date(position.more_member_since).toLocaleDateString("en-US", { year: "numeric", month: "long" })}
                  </p>
                )}
              </div>
              <span className="text-xs font-bold px-2 py-1 bg-green-100 text-green-700 rounded-full">Active</span>
            </div>
            <p className="text-sm text-ink/60 mt-3">
              You're part of the M.O.R.E. community network. Leaving doesn't affect your main account.
            </p>
            <button
              onClick={() => setModal("leave-more")}
              className="mt-4 text-sm text-ink/40 hover:text-ink/70 underline transition-colors"
            >
              Leave M.O.R.E.
            </button>
          </div>
        )}

        {/* Position choices */}
        <div className="bg-white border border-ink/10 rounded-2xl p-6 space-y-4">
          <h2 className="font-heading font-bold">Your choices</h2>
          <p className="text-sm text-ink/50">
            These are yours to make. No request, no review, no waiting.
          </p>

          {position?.can_step_down && (
            <button
              onClick={() => setModal("step-down")}
              className="w-full text-left flex items-start gap-4 p-4 rounded-xl border border-ink/10 hover:border-ink/20 hover:bg-ink/[0.02] transition-colors group"
            >
              <ChevronDown className="w-5 h-5 text-ink/40 mt-0.5 flex-shrink-0 group-hover:text-ink/60 transition-colors" />
              <div>
                <div className="font-bold text-sm">Step down from {roleLabel}</div>
                <div className="text-xs text-ink/50 mt-0.5">
                  Move to {ROLE_LABELS[position.step_down_to] || position.step_down_to}. Your history and contributions stay exactly as they are.
                </div>
              </div>
            </button>
          )}

          {position?.pending_exit ? (
            <div className="p-4 rounded-xl border border-amber-200 bg-amber-50">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="font-bold text-sm text-amber-800">Exit request pending</div>
                  <div className="text-xs text-amber-700 mt-1">
                    Your account goes inactive automatically on{" "}
                    <strong>{new Date(position.pending_exit.auto_processes_at).toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric", hour: "2-digit", minute: "2-digit" })}</strong>{" "}
                    unless you cancel. The platform owner has been notified.
                  </div>
                </div>
                <button
                  onClick={handleCancelExit}
                  disabled={busy}
                  className="flex-shrink-0 text-xs font-bold text-amber-700 hover:text-amber-900 underline transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          ) : (
            <button
              onClick={() => setModal("inactive")}
              className="w-full text-left flex items-start gap-4 p-4 rounded-xl border border-ink/10 hover:border-ink/20 hover:bg-ink/[0.02] transition-colors group"
            >
              <Pause className="w-5 h-5 text-ink/40 mt-0.5 flex-shrink-0 group-hover:text-ink/60 transition-colors" />
              <div>
                <div className="font-bold text-sm">Go inactive</div>
                <div className="text-xs text-ink/50 mt-0.5">
                  Pause your account. You'll have 72 hours — the owner can reach out to address concerns.
                  It processes automatically after that.
                </div>
              </div>
            </button>
          )}
        </div>

        {/* Timeline */}
        {history.length > 0 && (
          <div className="bg-white border border-ink/10 rounded-2xl p-6">
            <div className="flex items-center gap-2 mb-4">
              <Clock className="w-4 h-4 text-copper" />
              <h2 className="font-heading font-bold">Your history here</h2>
            </div>
            <div className="space-y-3">
              {history.map((evt, i) => (
                <div key={i} className="flex gap-3 text-sm">
                  <div className="w-1.5 h-1.5 rounded-full bg-copper/40 mt-2 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <div className="text-ink/70">{formatEventLabel(evt.action, evt.meta)}</div>
                    <div className="text-xs text-ink/30 mt-0.5">
                      {new Date(evt.at).toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" })}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Legal note */}
        <p className="text-xs text-ink/30 leading-relaxed pb-8">
          Platform administrators retain emergency access as required by applicable law.
          That access is logged, time-limited, and used only under documented protocol —
          not for ordinary management.
        </p>
      </div>

      {/* Step-down modal */}
      {modal === "step-down" && (
        <Modal onClose={closeModal} title={`Step down from ${roleLabel}`} icon={<ChevronDown className="w-5 h-5 text-ink/60" />}>
          <p className="text-sm text-ink/60">
            You'll move from <strong>{roleLabel}</strong> to <strong>{ROLE_LABELS[position?.step_down_to]}</strong>.
            Your work, courses, and history are untouched.
          </p>
          <label className="block mt-4">
            <span className="text-xs font-bold text-ink/50 uppercase tracking-wide">A few words why — just for the record</span>
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              rows={3}
              placeholder="Taking a step back, changing focus, etc."
              className="w-full mt-2 px-3 py-2 text-sm bg-bone border border-ink/20 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-copper/30"
            />
          </label>
          <div className="flex gap-3 mt-5 justify-end">
            <button onClick={closeModal} className="px-4 py-2 text-sm text-ink/50 hover:text-ink transition-colors">Cancel</button>
            <button
              onClick={handleStepDown}
              disabled={busy || reason.trim().length < 10}
              className="px-5 py-2 text-sm font-bold bg-ink text-bone rounded-lg hover:bg-ink/80 disabled:opacity-40 transition-colors flex items-center gap-2"
            >
              {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle className="w-4 h-4" />}
              Step down
            </button>
          </div>
        </Modal>
      )}

      {/* Go-inactive modal */}
      {modal === "inactive" && (
        <Modal onClose={closeModal} title="Go inactive" icon={<Pause className="w-5 h-5 text-ink/60" />}>
          <p className="text-sm text-ink/60">
            Your account will be paused. Nothing is deleted. Everything you've built here stays intact.
            To return, reach out and we'll reactivate right away.
          </p>
          <label className="block mt-4">
            <span className="text-xs font-bold text-ink/50 uppercase tracking-wide">
              What's on your mind — shared with the platform owner so they can respond
            </span>
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              rows={3}
              placeholder="Tell us what brought you here. They genuinely want to know."
              className="w-full mt-2 px-3 py-2 text-sm bg-bone border border-ink/20 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-copper/30"
            />
          </label>
          <p className="text-xs text-ink/40 mt-2">
            Standard path: 72 hours — owner is notified and may reach out, then auto-processes.
            If you need to leave right now, use "Leave now." You define what that means.
          </p>
          <div className="flex gap-3 mt-4 justify-end flex-wrap">
            <button onClick={closeModal} className="px-4 py-2 text-sm text-ink/50 hover:text-ink transition-colors">
              Cancel
            </button>
            <button
              onClick={handleEmergencyExit}
              disabled={busy || reason.trim().length < 10}
              className="px-4 py-2 text-sm font-bold border-2 border-red-400 text-red-600 rounded-lg hover:bg-red-50 disabled:opacity-40 transition-colors flex items-center gap-2"
              title="Leave immediately — you define what an emergency is"
            >
              {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <AlertTriangle className="w-4 h-4" />}
              Leave now
            </button>
            <button
              onClick={handleRequestExit}
              disabled={busy || reason.trim().length < 10}
              className="px-5 py-2 text-sm font-bold bg-ink text-bone rounded-lg hover:bg-ink/80 disabled:opacity-40 transition-colors flex items-center gap-2"
            >
              {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <LogOut className="w-4 h-4" />}
              Request exit
            </button>
          </div>
        </Modal>
      )}

      {/* Leave M.O.R.E. modal */}
      {modal === "leave-more" && (
        <Modal onClose={closeModal} title="Leave M.O.R.E." icon={<LogOut className="w-5 h-5 text-ink/60" />}>
          <p className="text-sm text-ink/60">
            You'll leave the M.O.R.E. community network. Your main account stays fully active.
            You're welcome back anytime.
          </p>
          <div className="flex gap-3 mt-5 justify-end">
            <button onClick={closeModal} className="px-4 py-2 text-sm text-ink/50 hover:text-ink transition-colors">Cancel</button>
            <button
              onClick={handleLeaveMore}
              disabled={busy}
              className="px-5 py-2 text-sm font-bold bg-ink text-bone rounded-lg hover:bg-ink/80 disabled:opacity-40 transition-colors flex items-center gap-2"
            >
              {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle className="w-4 h-4" />}
              Leave M.O.R.E.
            </button>
          </div>
        </Modal>
      )}

      {/* Proceeds modal */}
      {modal === "proceeds" && (
        <Modal onClose={closeModal} title="Proceeds preference" icon={<DollarSign className="w-5 h-5 text-copper" />}>
          <p className="text-sm text-ink/60 mb-4">
            Choose how your share of platform proceeds is handled. You can change this anytime.
          </p>
          <div className="space-y-2">
            {PROCEEDS_OPTIONS.map((opt) => (
              <button
                key={opt.id}
                onClick={() => setProceedsChoice(opt.id)}
                className={`w-full text-left p-4 rounded-xl border transition-colors ${
                  proceedsChoice === opt.id
                    ? "border-copper bg-copper/5"
                    : "border-ink/10 hover:border-ink/20"
                }`}
              >
                <div className="flex items-center gap-3">
                  <div className={`w-4 h-4 rounded-full border-2 flex-shrink-0 ${
                    proceedsChoice === opt.id ? "border-copper bg-copper" : "border-ink/30"
                  }`} />
                  <div>
                    <div className="font-bold text-sm">{opt.label}</div>
                    <div className="text-xs text-ink/50 mt-0.5">{opt.desc}</div>
                  </div>
                </div>
              </button>
            ))}
          </div>
          <div className="flex gap-3 mt-5 justify-end">
            <button onClick={closeModal} className="px-4 py-2 text-sm text-ink/50 hover:text-ink transition-colors">Cancel</button>
            <button
              onClick={handleSaveProceeds}
              disabled={busy}
              className="px-5 py-2 text-sm font-bold bg-copper text-bone rounded-lg hover:bg-copper/80 disabled:opacity-40 transition-colors flex items-center gap-2"
            >
              {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle className="w-4 h-4" />}
              Save preference
            </button>
          </div>
        </Modal>
      )}
    </AppShell>
  );
}

function Modal({ onClose, title, icon, children }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md">
        <div className="flex items-center justify-between px-6 py-4 border-b border-ink/10">
          <div className="flex items-center gap-2 font-heading font-bold">
            {icon}
            {title}
          </div>
          <button onClick={onClose} className="text-ink/30 hover:text-ink/60 transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>
        <div className="px-6 py-5">{children}</div>
      </div>
    </div>
  );
}
