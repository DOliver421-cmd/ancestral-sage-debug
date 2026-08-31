import { ArrowLeft } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";

export default function PageBack({ to = "/dashboard", label = "Back" }) {
  const navigate = useNavigate();

  return (
    <div className="flex items-center gap-3 mb-6">
      <button
        type="button"
        onClick={() => navigate(-1)}
        className="inline-flex items-center gap-2 px-3 py-2 rounded-lg border border-ink/15 bg-white text-ink text-sm font-bold hover:border-copper hover:text-copper transition-colors"
        aria-label="Go back"
      >
        <ArrowLeft className="w-4 h-4" /> Back
      </button>
      <Link
        to={to}
        className="text-sm font-bold text-copper hover:underline"
      >
        {label}
      </Link>
    </div>
  );
}
