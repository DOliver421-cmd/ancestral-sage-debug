import { Link } from "react-router-dom";
import { XCircle } from "lucide-react";

export default function VerificationCancel() {
  return (
    <div className="min-h-screen bg-bone flex items-center justify-center p-8">
      <div className="max-w-md w-full bg-white rounded-2xl shadow-sm border border-ink/10 p-10 text-center">
        <div className="w-16 h-16 bg-amber-100 rounded-full flex items-center justify-center mx-auto mb-6">
          <XCircle className="w-9 h-9 text-amber-600" />
        </div>
        <h1 className="font-heading text-2xl font-bold mb-2">Verification Cancelled</h1>
        <p className="text-ink/60 mb-8">
          The $1 verification payment was not completed. Your account remains active but may be subject to review if flagged.
        </p>
        <div className="flex flex-col gap-3">
          <Link to="/profile" className="btn-primary w-full py-3 text-center block">Return to Profile</Link>
          <Link to="/help-center" className="text-sm text-copper hover:underline">Contact Support</Link>
        </div>
      </div>
    </div>
  );
}
