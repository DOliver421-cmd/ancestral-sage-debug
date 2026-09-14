import { useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../lib/auth";
import { BRAND } from "../lib/brand";
import { Menu, X } from "lucide-react";

const LINKS = [
  { to: "/more-help-center", label: "MORE Help Center" },
  { to: "/supervisor/login", label: "Supervisor Login" },
  { to: "/helper", label: "My Helper" },
  { to: "/wai-institute", label: "Homeschool Academy" },
  { to: "/courses", label: "Trade Courses" },
  { to: "/community", label: "Community" },
  { to: "/creators", label: "Creators" },
  { to: "/store", label: "Store" },
  { to: "/plans", label: "Plans" },
];

const LINK_STYLE = { color: "#f1e9c9", textDecoration: "none", fontSize: 12, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.05em" };

export default function PublicNav() {
  const { user } = useAuth();
  const [open, setOpen] = useState(false);

  return (
    <header style={{ background: "linear-gradient(135deg, var(--wai-purple), #4c1d95)", borderBottom: "3px solid var(--wai-gold)" }}>
      <div className="max-w-6xl mx-auto px-6 py-3 flex items-center justify-between">
        <Link to="/" className="font-heading text-base" style={{ textDecoration: "none", color: "var(--wai-gold-light)", fontWeight: 800 }}>
          {BRAND.name}
        </Link>
        <span style={{ fontSize: 10, color: "rgba(241,233,201,0.5)", fontWeight: 600, letterSpacing: "0.05em", textTransform: "uppercase" }} className="hidden sm:inline">
          {BRAND.presentedBy}
        </span>

        {/* Desktop nav */}
        <nav className="hidden lg:flex items-center gap-3">
          {LINKS.map((l) => (
            <Link key={l.to} to={l.to} style={LINK_STYLE}>{l.label}</Link>
          ))}
          <Link to="/premium" style={LINK_STYLE}>Premium Services</Link>
          <a href="https://www.facebook.com/groups/waiinstitute" target="_blank" rel="noopener noreferrer" style={LINK_STYLE}>Facebook Group</a>
          {user ? (
            <Link to="/profile" style={{ background: "var(--wai-gold)", color: "#1a1100", padding: "0.35rem 0.8rem", borderRadius: 8, textDecoration: "none", fontWeight: 800, fontSize: 12 }}>My Profile</Link>
          ) : (
            <Link to="/login" style={{ background: "var(--wai-gold)", color: "#1a1100", padding: "0.35rem 0.8rem", borderRadius: 8, textDecoration: "none", fontWeight: 800, fontSize: 12 }}>Sign In</Link>
          )}
        </nav>

        {/* Mobile hamburger */}
        <button
          className="lg:hidden p-2 rounded-lg text-white/90 hover:text-white"
          onClick={() => setOpen((o) => !o)}
          aria-label="Toggle navigation"
        >
          {open ? <X size={22} /> : <Menu size={22} />}
        </button>
      </div>

      {/* Mobile drawer */}
      {open && (
        <div className="lg:hidden border-t border-white/10" style={{ background: "linear-gradient(135deg, #4c1d95, #3b1578)" }}>
          <nav className="max-w-6xl mx-auto px-6 py-4 flex flex-col gap-3">
            {LINKS.map((l) => (
              <Link
                key={l.to}
                to={l.to}
                style={LINK_STYLE}
                className="py-2 border-b border-white/5"
                onClick={() => setOpen(false)}
              >
                {l.label}
              </Link>
            ))}
            <Link to="/premium" style={LINK_STYLE} className="py-2 border-b border-white/5" onClick={() => setOpen(false)}>Premium Services</Link>
            <a href="https://www.facebook.com/groups/waiinstitute" target="_blank" rel="noopener noreferrer" style={LINK_STYLE} className="py-2 border-b border-white/5" onClick={() => setOpen(false)}>Facebook Group</a>
            {user ? (
              <Link to="/profile" style={{ background: "var(--wai-gold)", color: "#1a1100", padding: "0.5rem 1rem", borderRadius: 8, textDecoration: "none", fontWeight: 800, fontSize: 12 }} className="mt-2 text-center" onClick={() => setOpen(false)}>My Profile</Link>
            ) : (
              <Link to="/login" style={{ background: "var(--wai-gold)", color: "#1a1100", padding: "0.5rem 1rem", borderRadius: 8, textDecoration: "none", fontWeight: 800, fontSize: 12 }} className="mt-2 text-center" onClick={() => setOpen(false)}>Sign In</Link>
            )}
          </nav>
        </div>
      )}
    </header>
  );
}
