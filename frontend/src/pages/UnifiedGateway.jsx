/**
 * M.O.R.E. Help Center — Unified Gateway
 *
 * One page that introduces the platform, routes every type of user,
 * shows the entire ecosystem at a glance, and removes the maze.
 * Admin/Exec see everything unlocked; public sees clean entry points.
 */

import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../lib/auth";
import {
  BookOpen, Music, Users, HandHelping,
  Sparkles, FlaskConical, BadgeCheck, Award, Brain,
  Gamepad2, Crown, Trophy, Scale, Radio,
  ShoppingBag, Star, Heart, Globe, Mic, Palette,
  Video, DollarSign, Receipt, Network,
  Settings, Shield, TrendingUp, ScrollText,
  Lock, ArrowRight, LogIn,
} from "lucide-react";

// ── Design tokens ──────────────────────────────────────────────────────────────
const T = {
  bg:     "#FFF8EC",
  forest: "#2D6A4F",
  amber:  "#E8A51E",
  copper: "#C47A1E",
  bark:   "#3E2723",
  sand:   "#F5DEB3",
  cream:  "#FFF1DC",
  ink:    "#1a1a1a",
  signal: "#22c55e",
};

// ── Role helpers ───────────────────────────────────────────────────────────────
const ROLE_RANK = { student: 1, creative_partner: 1, instructor: 2, admin: 3, executive_admin: 4 };
function rank(user) { return ROLE_RANK[user?.role] ?? 0; }

// ── District definitions ───────────────────────────────────────────────────────
const DISTRICTS = [
  {
    id: "learn",
    title: "LEARN",
    subtitle: "For Students & Public",
    icon: BookOpen,
    color: T.forest,
    bg: "#e8f5ee",
    cta: "Enter Learning Hub",
    ctaHref: "/modules",
    links: [
      { label: "Curriculum", href: "/modules" },
      { label: "Workforce Labs", href: "/labs" },
      { label: "AI Tutor", href: "/ai" },
      { label: "Learning Path", href: "/adaptive" },
      { label: "Credentials", href: "/credentials" },
      { label: "Certificates", href: "/certificates" },
      { label: "Lab Simulations", href: "/lab-simulations" },
      { label: "Compliance", href: "/compliance" },
    ],
  },
  {
    id: "create",
    title: "CREATE",
    subtitle: "For Creators & Public",
    icon: Music,
    color: T.copper,
    bg: "#fdf3e3",
    cta: "Enter Creator Hub",
    ctaHref: "/studio",
    links: [
      { label: "Creator Studio", href: "/studio" },
      { label: "Course Manager", href: "/creator/courses" },
      { label: "Ghost Producer", href: "/ghost-producer" },
      { label: "Band on a Page", href: "/band" },
      { label: "Creator Lounge", href: "/creator-lounge" },
      { label: "Playlist Manager", href: "/playlist/dashboard" },
      { label: "Social Publisher", href: "/social/publish" },
      { label: "Virtual Arcade", href: "/arcade" },
    ],
  },
  {
    id: "community",
    title: "COMMUNITY",
    subtitle: "For Everyone",
    icon: Users,
    color: "#7c3aed",
    bg: "#f3f0ff",
    cta: "Enter Community",
    ctaHref: "/palace",
    links: [
      { label: "Members' Palace", href: "/palace" },
      { label: "Elder Council", href: "/elder-council" },
      { label: "XP Leaderboard", href: "/leaderboard" },
      { label: "Personas", href: "/personas" },
      { label: "Community", href: "/community" },
      { label: "Public Profiles", href: "/creators" },
      { label: "Internships", href: "/internships" },
    ],
  },
  {
    id: "more",
    title: "M.O.R.E. SYSTEM",
    subtitle: "For Logged-in Users",
    icon: HandHelping,
    color: "#0d7377",
    bg: "#e6f4f5",
    cta: "Enter M.O.R.E. Hub",
    ctaHref: "/app/more",
    links: [
      { label: "M.O.R.E. Hub", href: "/app/more" },
      { label: "Community Chat", href: "/more/chat" },
      { label: "Personal Helper", href: "/app/helper" },
      { label: "Legal Tools", href: "/more/litigation" },
      { label: "Partnership Dashboard", href: "/partnership" },
      { label: "Report Incident", href: "/incidents" },
    ],
  },
];

// ── Feature grid ───────────────────────────────────────────────────────────────
const FEATURES = [
  { icon: Sparkles,    label: "AI Tutor",              href: "/ai",           tier: "free",      desc: "Conversational learning powered by AI" },
  { icon: Music,       label: "Creator Sanctuary",      href: "/studio",       tier: "free",      desc: "Full creative hub for music, video, art" },
  { icon: Mic,         label: "Ghost Producer",         href: "/ghost-producer", tier: "alacarte", desc: "Anonymous production work" },
  { icon: FlaskConical,label: "Lab Simulations",        href: "/lab-simulations", tier: "free",   desc: "Hands-on workforce simulations" },
  { icon: Brain,       label: "Adaptive Learning Path", href: "/adaptive",     tier: "tier1",     desc: "Personalized curriculum" },
  { icon: HandHelping, label: "Advanced M.O.R.E. Tools",href: "/app/more",    tier: "tier2",     desc: "Full M.O.R.E. system access" },
  { icon: DollarSign,  label: "Revenue Dashboard",      href: "/creator/earnings", tier: "creator", desc: "Creator earnings and analytics" },
  { icon: Crown,       label: "Sovereign Command",      href: "/admin/system", tier: "exec",      desc: "Executive system control" },
  { icon: Gamepad2,    label: "Virtual Arcade",         href: "/arcade",       tier: "free",      desc: "Mission-aligned games, earn XP" },
  { icon: BadgeCheck,  label: "Credentials & Badges",   href: "/credentials",  tier: "free",      desc: "Verified professional credentials" },
  { icon: Scale,       label: "Legal Tools",            href: "/more/litigation", tier: "tier2",  desc: "Governance and compliance tools" },
  { icon: Network,     label: "Partnership Network",    href: "/partnership",  tier: "tier3",     desc: "Business partnership dashboard" },
];

const TIER_LABEL = {
  free:     { label: "Free",          color: T.signal,  bg: "#dcfce7" },
  tier1:    { label: "Tier 1",        color: "#2563eb", bg: "#dbeafe" },
  tier2:    { label: "Tier 2",        color: T.copper,  bg: "#fef3c7" },
  tier3:    { label: "Tier 3",        color: "#7c3aed", bg: "#f3e8ff" },
  alacarte: { label: "À La Carte",    color: T.forest,  bg: "#d1fae5" },
  creator:  { label: "Creator",       color: T.copper,  bg: "#fdf3e3" },
  exec:     { label: "Exec Only",     color: T.amber,   bg: "#fef9c3" },
};

// ── Public discovery links ─────────────────────────────────────────────────────
const PUBLIC_LINKS = [
  { label: "Courses",       href: "/courses" },
  { label: "Creators",      href: "/creators" },
  { label: "Personas",      href: "/personas" },
  { label: "Community",     href: "/community" },
  { label: "Store",         href: "/store" },
  { label: "Plans",         href: "/plans" },
  { label: "Donate",        href: "/donate" },
  { label: "Internships",   href: "/internships" },
];

export default function UnifiedGateway() {
  const { user, loading } = useAuth();
  const navigate = useNavigate();
  const r = rank(user);
  const isAdmin = r >= 3;
  const isExec  = r >= 4;
  const loggedIn = !!user;

  return (
    <div style={{ background: T.bg, minHeight: "100vh", fontFamily: "system-ui, sans-serif" }}>

      {/* ── HERO ──────────────────────────────────────────────────────────── */}
      <section style={{
        background: `linear-gradient(135deg, ${T.forest} 0%, #1B4332 100%)`,
        color: "#fff",
        padding: "64px 24px 48px",
        textAlign: "center",
        position: "relative",
        overflow: "hidden",
      }}>
        <div style={{ maxWidth: 720, margin: "0 auto", position: "relative", zIndex: 1 }}>
          <div style={{ fontSize: 11, letterSpacing: "0.25em", textTransform: "uppercase", color: T.amber, marginBottom: 16, fontWeight: 700 }}>
            WAI INSTITUTE · M.O.R.E. HELP CENTER
          </div>
          <h1 style={{ fontSize: "clamp(2rem, 5vw, 3.5rem)", fontWeight: 900, lineHeight: 1.1, margin: "0 0 16px" }}>
            Welcome to the M.O.R.E. Help Center
          </h1>
          <p style={{ fontSize: 18, opacity: 0.85, maxWidth: 560, margin: "0 auto 32px", lineHeight: 1.6 }}>
            Your Gateway to Learning, Creating, Earning, and Leading.
          </p>

          {/* CTA buttons — adapt to role */}
          <div style={{ display: "flex", flexWrap: "wrap", gap: 12, justifyContent: "center" }}>
            <Link to="/modules" style={btnStyle(T.amber, T.bark)}>Start Learning</Link>
            <Link to="/creators" style={btnStyle("transparent", "#fff", "1px solid rgba(255,255,255,0.4)")}>Explore Creators</Link>
            <Link to="/palace" style={btnStyle("transparent", "#fff", "1px solid rgba(255,255,255,0.4)")}>Visit the Community</Link>
            {!loggedIn && <Link to="/login" style={btnStyle("rgba(255,255,255,0.15)", "#fff")}>Log In / Continue</Link>}
            {loggedIn && !isAdmin && <Link to="/dashboard" style={btnStyle("rgba(255,255,255,0.15)", "#fff")}>Go to Dashboard</Link>}
            {isAdmin && <Link to="/admin" style={btnStyle("#fff", T.forest)}>Enter Admin System</Link>}
            {isExec  && <Link to="/admin/system" style={btnStyle(T.amber, T.bark)}>Sovereign Command</Link>}
          </div>
        </div>

        {/* Decorative glyphs */}
        <div style={{ position: "absolute", inset: 0, pointerEvents: "none", opacity: 0.06 }}>
          {["✦","◈","⬡","✧","⟡"].map((g, i) => (
            <span key={i} style={{ position: "absolute", fontSize: 40 + i * 20,
              left: `${8 + i * 20}%`, top: `${10 + (i % 2) * 50}%` }}>{g}</span>
          ))}
        </div>
      </section>

      {/* ── FOUR DISTRICTS ────────────────────────────────────────────────── */}
      <section style={{ padding: "56px 24px", maxWidth: 1200, margin: "0 auto" }}>
        <h2 style={sectionTitle}>Choose Your District</h2>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: 24 }}>
          {DISTRICTS.map((d) => {
            const Icon = d.icon;
            return (
              <div key={d.id} style={{
                background: d.bg,
                border: `2px solid ${d.color}30`,
                borderRadius: 16,
                padding: 24,
                display: "flex",
                flexDirection: "column",
              }}>
                <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 16 }}>
                  <div style={{ width: 40, height: 40, borderRadius: 10, background: `${d.color}20`, display: "flex", alignItems: "center", justifyContent: "center" }}>
                    <Icon size={20} color={d.color} />
                  </div>
                  <div>
                    <div style={{ fontSize: 18, fontWeight: 900, color: d.color }}>{d.title}</div>
                    <div style={{ fontSize: 11, color: T.ink, opacity: 0.55 }}>{d.subtitle}</div>
                  </div>
                </div>
                <ul style={{ margin: "0 0 20px", padding: 0, listStyle: "none", flex: 1 }}>
                  {d.links.map((l) => (
                    <li key={l.href} style={{ marginBottom: 6 }}>
                      <Link to={l.href} style={{ fontSize: 13, color: T.ink, textDecoration: "none", opacity: 0.8, display: "flex", alignItems: "center", gap: 6 }}
                        onMouseEnter={e => e.currentTarget.style.opacity = 1}
                        onMouseLeave={e => e.currentTarget.style.opacity = 0.8}>
                        <ArrowRight size={12} color={d.color} />
                        {l.label}
                      </Link>
                    </li>
                  ))}
                </ul>
                <Link to={d.ctaHref} style={btnStyle(d.color, "#fff")}>
                  {d.cta} →
                </Link>
              </div>
            );
          })}
        </div>
      </section>

      {/* ── FEATURE GRID ──────────────────────────────────────────────────── */}
      <section style={{ padding: "0 24px 56px", maxWidth: 1200, margin: "0 auto" }}>
        <h2 style={sectionTitle}>Platform Features</h2>
        <p style={{ color: T.ink, opacity: 0.55, marginBottom: 32, fontSize: 14 }}>
          {isAdmin ? "All features unlocked — admin/exec bypass all tier restrictions." : "Free features available to everyone. Upgrade to unlock more."}
        </p>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))", gap: 16 }}>
          {FEATURES.map((f) => {
            const Icon = f.icon;
            const t = TIER_LABEL[f.tier];
            const locked = !isAdmin && !["free", "alacarte"].includes(f.tier) && f.tier !== "creator";
            return (
              <Link key={f.href} to={f.href} style={{
                background: "#fff",
                border: `1px solid ${locked ? "#e5e7eb" : t.color + "40"}`,
                borderRadius: 12,
                padding: 20,
                textDecoration: "none",
                opacity: locked ? 0.6 : 1,
                display: "block",
                transition: "box-shadow 0.15s",
              }}
              onMouseEnter={e => { if (!locked) e.currentTarget.style.boxShadow = `0 4px 16px ${t.color}30`; }}
              onMouseLeave={e => e.currentTarget.style.boxShadow = "none"}>
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 10 }}>
                  <div style={{ width: 36, height: 36, borderRadius: 8, background: t.bg, display: "flex", alignItems: "center", justifyContent: "center" }}>
                    <Icon size={18} color={t.color} />
                  </div>
                  {locked
                    ? <span style={{ fontSize: 10, fontWeight: 700, color: "#9ca3af", display: "flex", alignItems: "center", gap: 4 }}><Lock size={10} /> {t.label}</span>
                    : <span style={{ fontSize: 10, fontWeight: 700, color: t.color, background: t.bg, padding: "2px 8px", borderRadius: 99 }}>{t.label}</span>
                  }
                </div>
                <div style={{ fontWeight: 700, fontSize: 13, color: T.ink, marginBottom: 4 }}>{f.label}</div>
                <div style={{ fontSize: 11, color: T.ink, opacity: 0.55, lineHeight: 1.5 }}>{f.desc}</div>
                {locked && <Link to="/plans" style={{ fontSize: 11, color: T.copper, fontWeight: 600, marginTop: 8, display: "block" }} onClick={e => e.stopPropagation()}>Upgrade →</Link>}
              </Link>
            );
          })}
        </div>
      </section>

      {/* ── ROLE GATEWAYS ─────────────────────────────────────────────────── */}
      <section style={{ background: T.cream, padding: "56px 24px" }}>
        <div style={{ maxWidth: 900, margin: "0 auto" }}>
          <h2 style={sectionTitle}>Where Do You Want to Go?</h2>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))", gap: 12 }}>
            {!loggedIn ? (
              <>
                {[
                  { label: "Student Login",    href: "/login",            icon: BookOpen },
                  { label: "Creator Login",    href: "/login",            icon: Music },
                  { label: "Instructor Login", href: "/login",            icon: Users },
                  { label: "Admin Login",      href: "/login",            icon: Settings },
                  { label: "Supervisor Login", href: "/supervisor-login", icon: Shield },
                ].map(({ label, href, icon: Icon }) => (
                  <Link key={label} to={href} style={gatewayBtn(T.forest)}>
                    <Icon size={18} />
                    {label}
                  </Link>
                ))}
              </>
            ) : (
              <>
                <Link to="/dashboard"    style={gatewayBtn(T.forest)}><BookOpen size={18} /> Dashboard</Link>
                <Link to="/studio"       style={gatewayBtn(T.copper)}><Music size={18} /> Creator Studio</Link>
                {r >= 2 && <Link to="/instructor" style={gatewayBtn("#7c3aed")}><Users size={18} /> Instructor Panel</Link>}
                {isAdmin  && <Link to="/admin"       style={gatewayBtn("#1d4ed8")}><Settings size={18} /> Admin System</Link>}
                {isExec   && <Link to="/admin/system" style={gatewayBtn(T.amber, T.bark)}><Crown size={18} /> Exec Command</Link>}
              </>
            )}
          </div>
        </div>
      </section>

      {/* ── PUBLIC DISCOVERY ──────────────────────────────────────────────── */}
      <section style={{ padding: "56px 24px", maxWidth: 900, margin: "0 auto" }}>
        <h2 style={sectionTitle}>Explore the Platform</h2>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 10 }}>
          {PUBLIC_LINKS.map(({ label, href }) => (
            <Link key={href} to={href} style={{
              padding: "8px 18px",
              borderRadius: 99,
              border: `1px solid ${T.copper}40`,
              color: T.copper,
              textDecoration: "none",
              fontSize: 13,
              fontWeight: 600,
              background: "#fff",
              transition: "background 0.15s",
            }}
            onMouseEnter={e => e.currentTarget.style.background = "#fdf3e3"}
            onMouseLeave={e => e.currentTarget.style.background = "#fff"}>
              {label}
            </Link>
          ))}
        </div>
      </section>

      {/* ── FOOTER ────────────────────────────────────────────────────────── */}
      <footer style={{ background: T.bark, color: "#fff", padding: "32px 24px", textAlign: "center" }}>
        <div style={{ maxWidth: 700, margin: "0 auto" }}>
          <div style={{ display: "flex", flexWrap: "wrap", justifyContent: "center", gap: "8px 24px", marginBottom: 16 }}>
            {[
              { label: "Terms",           href: "/terms" },
              { label: "Privacy",         href: "/privacy" },
              { label: "Help Center",     href: "/more-help-center" },
              { label: "Contact",         href: "mailto:support@wai-institute.org" },
              { label: "Public Profiles", href: "/creators" },
              { label: "Internships",     href: "/internships" },
            ].map(({ label, href }) => (
              <a key={label} href={href} style={{ color: "rgba(255,255,255,0.65)", textDecoration: "none", fontSize: 13 }}>{label}</a>
            ))}
          </div>
          <div style={{ fontSize: 12, opacity: 0.4 }}>
            © {new Date().getFullYear()} WAI Institute — M.O.R.E. Help Center. All rights reserved.
          </div>
        </div>
      </footer>

    </div>
  );
}

// ── Style helpers ──────────────────────────────────────────────────────────────
function btnStyle(bg, color, border) {
  return {
    display: "inline-flex", alignItems: "center", justifyContent: "center",
    padding: "10px 22px", borderRadius: 8, fontWeight: 700, fontSize: 13,
    textDecoration: "none", background: bg, color,
    border: border || "none", cursor: "pointer", transition: "opacity 0.15s",
  };
}

function gatewayBtn(bg, color = "#fff") {
  return {
    display: "flex", alignItems: "center", gap: 8,
    padding: "12px 16px", borderRadius: 10, fontWeight: 700, fontSize: 13,
    textDecoration: "none", background: bg, color,
    justifyContent: "center", transition: "opacity 0.15s",
  };
}

const sectionTitle = {
  fontSize: "clamp(1.4rem, 3vw, 2rem)",
  fontWeight: 900,
  color: T.bark,
  marginBottom: 24,
  marginTop: 0,
};
