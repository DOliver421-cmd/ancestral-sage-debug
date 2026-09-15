import { useEffect, useState } from "react";
import { useSearchParams, Link } from "react-router-dom";
import { CheckCircle, XCircle, Loader2 } from "lucide-react";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";

export default function VerificationSuccess() {
  const [params] = useSearchParams();
  const sessionId = params.get("session_id");
  const [status, setStatus] = useState("checking"); // checking | success | failed
  const [msg, setMsg] = useState("");

  useEffect(() => {
    let cancelled = false;
    const check = async () => {
      if (!sessionId) { setStatus("failed"); setMsg("Missing session ID."); return; }
      try {
        const { data } = await api.get("/verification/status");
        if (cancelled) return;
        if (data?.age_verified || data?.verification_status === "approved") {
          setStatus("success");
          setMsg("Your age verification is complete. Your account is now fully active.");
        } else if (data?.verification_status === "pending") {
          setStatus("checking");
          setMsg("Verification is still being processed. Please wait…");
          setTimeout(check, 3000);
        } else {
          setStatus("failed");
          setMsg("Verification could not be confirmed. Please contact support.");
        }
      } catch {
        if (cancelled) return;
        setStatus("failed");
        setMsg("Unable to check verification status.");
      }
    };
    check();
    return () => { cancelled = true; };
  }, [sessionId]);

  return (
    <div className="min-h-screen bg-bone flex items-center justify-center p-8">
      <div className="max-w-md w-full bg-white rounded-2xl shadow-sm border border-ink/10 p-10 text-center">
        {status === "checking" && (
          <>
            <Loader2 className="w-12 h-12 text-copper animate-spin mx-auto mb-4" />
            <h1 className="font-heading text-2xl font-bold mb-2">Verifying…</h1>
            <p className="text-ink/60">{msg}</p>
          </>
        )}
        {status === "success" && (
          <>
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
              <CheckCircle className="w-9 h-9 text-green-600" />
            </div>
            <h1 className="font-heading text-2xl font-bold mb-2">Age Verified</h1>
            <p className="text-ink/60 mb-8">{msg}</p>
            <Link to="/profile" className="btn-primary w-full py-3 text-center block">Go to My Profile</Link>
          </>
        )}
        {status === "failed" && (
          <>
            <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-6">
              <XCircle className="w-9 h-9 text-red-600" />
            </div>
            <h1 className="font-heading text-2xl font-bold mb-2">Verification Incomplete</h1>
            <p className="text-ink/60 mb-8">{msg}</p>
            <div className="flex flex-col gap-3">
              <Link to="/profile" className="btn-primary w-full py-3 text-center block">Return to Profile</Link>
              <Link to="/help-center" className="text-sm text-copper hover:underline">Contact Support</Link>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
