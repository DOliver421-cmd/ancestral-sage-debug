import { useEffect, useState } from "react";
import { useSearchParams, Link } from "react-router-dom";
import { CheckCircle } from "lucide-react";

export default function PaymentSuccess() {
  const [params] = useSearchParams();
  const sessionId = params.get("session_id");
  const [dots, setDots] = useState("");

  useEffect(() => {
    const iv = setInterval(() => setDots((d) => (d.length < 3 ? d + "." : "")), 500);
    return () => clearInterval(iv);
  }, []);

  return (
    <div className="min-h-screen bg-bone flex items-center justify-center p-8">
      <div className="max-w-md w-full bg-white rounded-2xl shadow-sm border border-ink/10 p-10 text-center">
        <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
          <CheckCircle className="w-9 h-9 text-green-600" />
        </div>
        <h1 className="font-heading text-2xl font-bold text-ink mb-2">Payment Confirmed!</h1>
        <p className="text-ink/60 mb-2">
          Thank you for supporting the WAI Institute. Your transaction was successful.
        </p>
        {sessionId && (
          <p className="text-xs text-ink/30 font-mono mb-6 break-all">Ref: {sessionId}</p>
        )}
        <p className="text-sm text-ink/50 mb-8">
          A confirmation notification has been sent to your account.
        </p>
        <div className="flex flex-col gap-3">
          <Link to="/dashboard"
            className="w-full py-3 bg-ink text-white font-bold rounded-lg hover:bg-ink/80 transition-colors text-center">
            Return to Dashboard
          </Link>
          <Link to="/payment/history"
            className="w-full py-3 border border-ink/20 text-ink font-bold rounded-lg hover:bg-ink/5 transition-colors text-center text-sm">
            View Payment History
          </Link>
        </div>
      </div>
    </div>
  );
}
