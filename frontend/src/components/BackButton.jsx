import { useNavigate } from "react-router-dom";
import { ArrowLeft } from "lucide-react";

// Shared back control. `to` navigates to a specific route; otherwise goes back
// one step in history. Used to guarantee no dead-end views.
export default function BackButton({ to, label = "Back", className = "", style }) {
  const navigate = useNavigate();
  const go = () => (to ? navigate(to) : navigate(-1));
  return (
    <button
      type="button"
      onClick={go}
      data-testid="back-button"
      className={`inline-flex items-center gap-2 text-sm font-bold uppercase tracking-widest text-ink/70 hover:text-copper transition-colors ${className}`}
      style={style}
    >
      <ArrowLeft className="w-4 h-4" /> {label}
    </button>
  );
}
