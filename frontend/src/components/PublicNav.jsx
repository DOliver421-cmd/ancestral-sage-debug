import { Link } from "react-router-dom";

// Shared header for the public funnel pages (festival purple + gold). Keeps the
// public page set cross-linked without cluttering the authenticated app sidebar.
const LINKS = [
  { to: "/more-help-center", label: "MORE Help Center" },
  { to: "/supervisor/login", label: "Supervisor Login" },
  { to: "/courses", label: "Courses" },
  { to: "/community", label: "Community" },
  { to: "/creators", label: "Creators" },
  { to: "/plans", label: "Plans" },
];

export default function PublicNav() {
  return (
    <header style={{ background: "linear-gradient(135deg, var(--wai-purple), #4c1d95)", borderBottom: "3px solid var(--wai-gold)" }}>
      <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between flex-wrap gap-3">
        <Link to="/" className="font-heading text-lg" style={{ textDecoration: "none", color: "var(--wai-gold-light)", fontWeight: 800 }}>
          W.A.I. · M.O.R.E.
        </Link>
        <nav className="flex items-center gap-4 flex-wrap">
          {LINKS.map((l) => (
            <Link
              key={l.to}
              to={l.to}
              style={{ color: "#f1e9c9", textDecoration: "none", fontSize: 13, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.05em" }}
            >
              {l.label}
            </Link>
          ))}
          <Link
            to="/login"
            style={{ background: "var(--wai-gold)", color: "#1a1100", padding: "0.4rem 0.9rem", borderRadius: 8, textDecoration: "none", fontWeight: 800, fontSize: 13 }}
          >
            Sign In
          </Link>
        </nav>
      </div>
    </header>
  );
}
