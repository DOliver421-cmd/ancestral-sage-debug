import { Link } from "react-router-dom";
import { useAuth } from "../lib/auth";
import { BRAND } from "../lib/brand";

// Shared header for the public funnel pages (festival purple + gold). Keeps the
// public page set cross-linked without cluttering the authenticated app sidebar.
const LINKS = [
  { to: "/more-help-center", label: "MORE Help Center" },
  { to: "/supervisor/login", label: "Supervisor Login" },
  { to: "/helper", label: "My Helper" },
  { to: "/courses", label: "Courses" },
  { to: "/community", label: "Community" },
  { to: "/creators", label: "Creators" },
  { to: "/store", label: "Store" },
  { to: "/plans", label: "Plans" },
];

export default function PublicNav() {
  const { user } = useAuth();
  return (
    <header style={{ background: "linear-gradient(135deg, var(--wai-purple), #4c1d95)", borderBottom: "3px solid var(--wai-gold)" }}>
      <div className="max-w-6xl mx-auto px-6 py-3 flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-3">
          <Link to="/" className="font-heading text-base" style={{ textDecoration: "none", color: "var(--wai-gold-light)", fontWeight: 800 }}>
            {BRAND.name}
          </Link>
          <span style={{ fontSize: 10, color: "rgba(241,233,201,0.5)", fontWeight: 600, letterSpacing: "0.05em", textTransform: "uppercase" }}>
            {BRAND.presentedBy}
          </span>
        </div>
        <nav className="flex items-center gap-3 flex-wrap">
          {LINKS.map((l) => (
            <Link
              key={l.to}
              to={l.to}
              style={{ color: "#f1e9c9", textDecoration: "none", fontSize: 12, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.05em" }}
            >
              {l.label}
            </Link>
          ))}
          <Link to="/premium"
            style={{ color: "#f1e9c9", textDecoration: "none", fontSize: 12, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.05em" }}>
            Premium Services
          </Link>
          <a href="https://www.facebook.com/groups/waiinstitute" target="_blank" rel="noopener noreferrer"
            style={{ color: "#f1e9c9", textDecoration: "none", fontSize: 12, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.05em" }}>
            Facebook Group
          </a>
          {user ? (
            <Link
              to="/profile"
              style={{ background: "var(--wai-gold)", color: "#1a1100", padding: "0.35rem 0.8rem", borderRadius: 8, textDecoration: "none", fontWeight: 800, fontSize: 12 }}
            >
              My Profile
            </Link>
          ) : (
            <Link
              to="/login"
              style={{ background: "var(--wai-gold)", color: "#1a1100", padding: "0.35rem 0.8rem", borderRadius: 8, textDecoration: "none", fontWeight: 800, fontSize: 12 }}
            >
              Sign In
            </Link>
          )}
        </nav>
      </div>
    </header>
  );
}

