import { Link } from "react-router-dom";
import { useAuth } from "../lib/auth";
import { BRAND } from "../lib/brand";

// Shared header for the public funnel pages. Keeps the public page set
// cross-linked without cluttering the authenticated app sidebar.
const LINKS = [
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
    <header style={{ background: "#fff", borderBottom: "1px solid #e3ddd2" }}>
      <div className="max-w-6xl mx-auto px-6 py-3 flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-3">
          <Link to="/" className="font-heading text-base" style={{ textDecoration: "none", color: "#111111", fontWeight: 800 }}>
            {BRAND.name}
          </Link>
          <span style={{ fontSize: 10, color: "#5a5045", fontWeight: 600, letterSpacing: "0.05em", textTransform: "uppercase" }}>
            {BRAND.presentedBy}
          </span>
        </div>
        <nav className="flex items-center gap-3 flex-wrap">
          {LINKS.map((l) => (
            <Link
              key={l.to}
              to={l.to}
              style={{ color: "#2b2722", textDecoration: "none", fontSize: 12, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.05em" }}
            >
              {l.label}
            </Link>
          ))}
          <Link to="/premium"
            style={{ color: "#2b2722", textDecoration: "none", fontSize: 12, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.05em" }}>
            Premium Services
          </Link>
          <a href="https://www.facebook.com/groups/waiinstitute" target="_blank" rel="noopener noreferrer"
            style={{ color: "#2b2722", textDecoration: "none", fontSize: 12, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.05em" }}>
            Facebook Group
          </a>
          {user ? (
            <Link
              to="/profile"
              style={{ background: "#b8860b", color: "#111111", padding: "0.35rem 0.8rem", borderRadius: 8, textDecoration: "none", fontWeight: 800, fontSize: 12 }}
            >
              My Profile
            </Link>
          ) : (
            <Link
              to="/login"
              style={{ background: "#b8860b", color: "#111111", padding: "0.35rem 0.8rem", borderRadius: 8, textDecoration: "none", fontWeight: 800, fontSize: 12 }}
            >
              Sign In
            </Link>
          )}
        </nav>
      </div>
    </header>
  );
}
