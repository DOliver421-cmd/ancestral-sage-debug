import { Link } from "react-router-dom";
import { XCircle } from "lucide-react";

export default function PaymentCancel() {
  return (
    <div className="min-h-screen bg-bone flex items-center justify-center p-8">
      <div className="max-w-md w-full bg-white rounded-2xl shadow-sm border border-ink/10 p-10 text-center">
        <div className="w-16 h-16 bg-red-50 rounded-full flex items-center justify-center mx-auto mb-6">
          <XCircle className="w-9 h-9 text-red-400" />
        </div>
        <h1 className="font-heading text-2xl font-bold text-ink mb-2">Payment Canceled</h1>
        <p className="text-ink/60 mb-8">
          No charge was made. You can try again whenever you're ready.
        </p>
        <div className="flex flex-col gap-3">
          <Link to="/store"
            className="w-full py-3 bg-ink text-white font-bold rounded-lg hover:bg-ink/80 transition-colors text-center">
            Back to Store
          </Link>
          <Link to="/dashboard"
            className="w-full py-3 border border-ink/20 text-ink font-bold rounded-lg hover:bg-ink/5 transition-colors text-center text-sm">
            Go to Dashboard
          </Link>
        </div>
      </div>
    </div>
  );
}
