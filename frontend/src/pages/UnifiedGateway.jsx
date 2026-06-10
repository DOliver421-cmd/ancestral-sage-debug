/**
 * M.O.R.E. Help Center — Unified Gateway
 * Dark theme, four-district layout, role-adaptive CTAs.
 */

import { Link } from "react-router-dom";
import { useAuth } from "../lib/auth";

const ROLE_RANK = { student: 1, creative_partner: 1, instructor: 2, admin: 3, executive_admin: 4 };
function rank(user) { return ROLE_RANK[user?.role] ?? 0; }

// ── Districts ──────────────────────────────────────────────────────────────────
const DISTRICTS = [
  {
    id: "learn", title: "Learn", color: "#3b82f6", btnClass: "btn-learn",
    subtitle: "Courses, modules, labs, and adaptive learning for students and professionals.",
    cta: "Enter Learning Hub", ctaHref: "/modules",
    links: ["AI Tutor → /ai", "Modules & Labs → /labs", "Adaptive Path → /adaptive", "Credentials & Certificates → /credentials", "Lab Simulations → /lab-simulations", "Compliance → /compliance"],
  },
  {
    id: "create", title: "Create", color: "#a855f7", btnClass: "btn-create",
    subtitle: "Tools for creators — courses, music, content, and production workflows.",
    cta: "Enter Creator Hub", ctaHref: "/studio",
    links: ["Creator Studio → /studio", "Courses You Teach → /creator/courses", "Ghost Producer → /ghost-producer", "Band on a Page → /band", "Creator Lounge → /creator-lounge", "Playlist Manager → /playlist/dashboard"],
  },
  {
    id: "community", title: "Community", color: "#22c55e", btnClass: "btn-community",
    subtitle: "Connect with others, join councils, and explore public profiles.",
    cta: "Enter Community", ctaHref: "/palace",
    links: ["Members' Palace → /palace", "Elder Council → /elder-council", "Creators Directory → /creators", "Personas → /personas", "XP Leaderboard → /leaderboard", "Internships → /internships"],
  },
  {
    id: "more", title: "M.O.R.E. System", color: "#eab308", btnClass: "btn-more",
    subtitle: "Advanced tools, AI partners, legal support, and partnership dashboards.",
    cta: "Enter M.O.R.E. Hub", ctaHref: "/app/more",
    links: ["M.O.R.E. Hub → /app/more", "Community Chat → /more/chat", "Personal Helper → /app/helper", "Legal Tools → /more/litigation", "Partnership Dashboard → /partnership", "Report Incident → /incidents"],
  },
];

// ── Features ───────────────────────────────────────────────────────────────────
const FEATURES = [
  { title: "AI Tutor",               desc: "Personalized AI-powered tutoring that adapts to your pace.",                   status: "included",  href: "/ai" },
  { title: "Creator Sanctuary",      desc: "A dedicated space for creators to build and manage content.",                   status: "included",  href: "/studio" },
  { title: "Ghost Producer",         desc: "AI-assisted music and content production tool.",                                status: "alacarte",  href: "/ghost-producer" },
  { title: "Lab Simulations",        desc: "Hands-on virtual labs for technical and scientific learning.",                  status: "included",  href: "/lab-simulations" },
  { title: "Advanced M.O.R.E. Tools",desc: "Deep system access for power users and administrators.",                        status: "tier2",     href: "/app/more" },
  { title: "Revenue Dashboard",      desc: "Track earnings, payouts, and financial performance.",                           status: "admin",     href: "/creator/earnings" },
  { title: "Virtual Arcade",         desc: "Mission-aligned games — learn through play and earn XP.",                      status: "included",  href: "/arcade" },
  { title: "Adaptive Learning Path", desc: "Personalized curriculum that evolves with your progress.",                     status: "tier1",     href: "/adaptive" },
  { title: "Legal Tools",            desc: "Governance guidance and community-safe compliance procedures.",                 status: "tier2",     href: "/more/litigation" },
  { title: "Credentials & Badges",   desc: "Verified professional credentials and achievement badges.",                    status: "included",  href: "/credentials" },
  { title: "Sovereign Command",      desc: "Executive system control — full platform visibility.",                          status: "admin",     href: "/admin/system" },
  { title: "Partnership Network",    desc: "Business partnership dashboard and discount management.",                       status: "tier2",     href: "/partnership" },
];

const STATUS_META = {
  included: { label: "Included",       cls: "status-included" },
  tier1:    { label: "Requires Tier 1", cls: "status-tier2" },
  tier2:    { label: "Requires Tier 2", cls: "status-tier2" },
  alacarte: { label: "À La Carte",     cls: "status-alacarte" },
  admin:    { label: "Admin / Exec",   cls: "status-admin" },
};

const PUBLIC_LINKS = [
  ["Browse Courses",      "/courses"],
  ["Meet Creators",       "/creators"],
  ["Explore Personas",    "/personas"],
  ["Plans & Pricing",     "/plans"],
  ["Donate",              "/donate"],
  ["Trash Pantheon",      "/trash"],
  ["Internships",         "/internships"],
  ["WAI Institute",       "/wai-institute"],
];

// ── Parse "Label → /path" helper ──────────────────────────────────────────────
function parseLink(s) {
  const [label, path] = s.split(" → ");
  return { label, path };
}

export default function UnifiedGateway() {
  const { user } = useAuth();
  const r = rank(user);
  const isAdmin  = r >= 3;
  const isExec   = r >= 4;
  const loggedIn = !!user;

  return (
    <div style={S.page}>
      <style>{CSS}</style>

      {/* ── HERO ────────────────────────────────────────────────────────── */}
      <header style={S.hero}>
        <div style={S.container}>
          <p style={S.heroEyebrow}>WAI INSTITUTE · M.O.R.E. HELP CENTER</p>
          <h1 style={S.heroH1}>Welcome to the M.O.R.E. Help Center</h1>
          <p style={S.heroSub}>Your gateway to learning, creating, community, and system tools.</p>
          <div className="hero-buttons">
            <Link className="btn btn-learn" to="/modules">Start Learning</Link>
            <Link className="btn btn-create" to="/creators">Explore Creators</Link>
            <Link className="btn btn-community" to="/palace">Visit Community</Link>
            {!loggedIn && <Link className="btn btn-ghost" to="/login">Log In / Continue</Link>}
            {loggedIn && !isAdmin && <Link className="btn btn-ghost" to="/dashboard">Go to Dashboard</Link>}
            {isAdmin  && <Link className="btn btn-more" to="/admin">Enter Admin System</Link>}
            {isExec   && <Link className="btn btn-more" to="/admin/system">Sovereign Command</Link>}
          </div>
        </div>
      </header>

      <main>
        {/* ── FOUR DISTRICTS ──────────────────────────────────────────── */}
        <section style={S.section}>
          <div style={S.container}>
            <h2 className="section-title">Explore the Four Districts</h2>
            <p className="section-subtitle">
              M.O.R.E. is built around four core districts. Each one serves a distinct purpose
              in the ecosystem — learning, creating, community, and system operations.
            </p>
            <div className="districts-grid">
              {DISTRICTS.map((d) => (
                <div key={d.id} className={`district-card card-${d.id}`} style={{ "--accent": d.color }}>
                  <h3 style={{ color: d.color }}>{d.title}</h3>
                  <p>{d.subtitle}</p>
                  <ul>
                    {d.links.map((l) => {
                      const { label, path } = parseLink(l);
                      return <li key={path}><Link to={path}>{label}</Link></li>;
                    })}
                  </ul>
                  <Link className={`btn ${d.btnClass}`} to={d.ctaHref}>{d.cta}</Link>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ── FEATURE GRID ────────────────────────────────────────────── */}
        <section style={{ ...S.section, background: "var(--bg-secondary)" }}>
          <div style={S.container}>
            <h2 className="section-title">Key Features at a Glance</h2>
            <p className="section-subtitle">
              {isAdmin
                ? "All features unlocked — admin and exec bypass all tier restrictions."
                : "A quick look at what's available across the platform. Check the status badge."}
            </p>
            <div className="features-grid">
              {FEATURES.map((f) => {
                const meta = STATUS_META[isAdmin ? "included" : f.status];
                return (
                  <Link key={f.href} to={f.href} className="feature-tile">
                    <h4>{f.title}</h4>
                    <p>{f.desc}</p>
                    <span className={`feature-status ${meta.cls}`}>{isAdmin && f.status === "admin" ? "Unlocked" : meta.label}</span>
                  </Link>
                );
              })}
            </div>
          </div>
        </section>

        {/* ── ROLE GATEWAYS ───────────────────────────────────────────── */}
        <section style={S.section}>
          <div style={S.container}>
            <h2 className="section-title">Who Is This For?</h2>
            <p className="section-subtitle">M.O.R.E. serves many roles. Find yours and get started.</p>
            <div className="roles-grid">
              {!loggedIn ? (
                <>
                  <RoleCard title="Students & Learners"  desc="Log in or register to access your dashboard."    href="/login"            btn="Go to Login"    btnCls="btn-ghost" />
                  <RoleCard title="Creators"              desc="Manage courses, earnings, and creative tools."    href="/login"            btn="Go to Login"    btnCls="btn-ghost" />
                  <RoleCard title="Instructors"           desc="Approve labs, manage rosters, track attendance."  href="/login"            btn="Go to Login"    btnCls="btn-ghost" />
                  <RoleCard title="Admins & Executives"   desc="Enter the admin system to manage users and tools." href="/admin"           btn="Enter Admin"    btnCls="btn-more" />
                  <RoleCard title="Supervisor"            desc="Supervisor portal — separate login required."     href="/supervisor-login" btn="Supervisor Login" btnCls="btn-ghost" />
                </>
              ) : (
                <>
                  <RoleCard title="Dashboard"         desc="Your personal overview."                href="/dashboard"    btn="Go to Dashboard"  btnCls="btn-learn" />
                  <RoleCard title="Creator Studio"    desc="Build, publish, and earn."              href="/studio"       btn="Open Studio"      btnCls="btn-create" />
                  {r >= 2 && <RoleCard title="Instructor Panel" desc="Rosters, labs, attendance." href="/instructor"   btn="Open Panel"       btnCls="btn-ghost" />}
                  {isAdmin  && <RoleCard title="Admin System"   desc="Manage users and platform." href="/admin"        btn="Enter Admin"      btnCls="btn-more" />}
                  {isExec   && <RoleCard title="Exec Command"   desc="Full platform control."     href="/admin/system" btn="Sovereign Command" btnCls="btn-more" />}
                </>
              )}
            </div>
          </div>
        </section>

        {/* ── PUBLIC DISCOVERY ────────────────────────────────────────── */}
        <section style={{ ...S.section, background: "var(--bg-secondary)" }}>
          <div style={S.container}>
            <h2 className="section-title">Public Discovery</h2>
            <p className="section-subtitle">Not logged in? No problem. Explore what M.O.R.E. has to offer.</p>
            <div className="discovery-links">
              {PUBLIC_LINKS.map(([label, href]) => (
                <Link key={href} className="btn btn-ghost" to={href}>{label}</Link>
              ))}
            </div>
          </div>
        </section>
      </main>

      {/* ── FOOTER ──────────────────────────────────────────────────────── */}
      <footer style={S.footer}>
        <div style={S.container}>
          <div className="footer-links">
            {[["Terms of Service","/terms"],["Privacy Policy","/privacy"],["Help Center","/more-help-center"],["Contact","mailto:support@wai-institute.org"],["Public Profiles","/creators"],["Internships","/internships"]].map(([label, href]) => (
              <a key={label} href={href}>{label}</a>
            ))}
          </div>
          <div className="footer-bottom">
            <p>&copy; {new Date().getFullYear()} WAI Institute — M.O.R.E. Help Center. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}

function RoleCard({ title, desc, href, btn, btnCls }) {
  return (
    <div className="role-card">
      <h4>{title}</h4>
      <p>{desc}</p>
      <Link className={`btn ${btnCls} btn-sm`} to={href}>{btn}</Link>
    </div>
  );
}

// ── Inline styles (layout / non-class) ────────────────────────────────────────
const S = {
  page: { fontFamily: "system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif", background: "var(--bg-primary)", color: "var(--text-primary)", lineHeight: 1.6, minHeight: "100vh" },
  hero: { minHeight: "65vh", display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center", textAlign: "center", padding: "4rem 1.5rem", background: "radial-gradient(ellipse at 20% 50%,rgba(59,130,246,.08) 0%,transparent 50%),radial-gradient(ellipse at 80% 50%,rgba(168,85,247,.08) 0%,transparent 50%),#0d1117" },
  container: { width: "100%", maxWidth: 1200, margin: "0 auto", padding: "0 1.5rem" },
  heroEyebrow: { fontSize: 11, letterSpacing: "0.25em", textTransform: "uppercase", color: "#eab308", marginBottom: 16, fontWeight: 700 },
  heroH1: { fontFamily: "Georgia,'Times New Roman',serif", fontSize: "clamp(2rem,5vw,3.25rem)", fontWeight: 700, lineHeight: 1.2, marginBottom: "1rem", color: "#e6edf3" },
  heroSub: { fontSize: "clamp(1rem,2.5vw,1.2rem)", color: "#8b949e", maxWidth: 560, margin: "0 auto 2rem" },
  section: { padding: "4rem 0" },
  footer: { background: "#161b22", borderTop: "1px solid rgba(255,255,255,.06)", padding: "2.5rem 0 1.5rem" },
};

// ── CSS injected once (mirrors the HTML spec faithfully) ──────────────────────
const CSS = `
  :root {
    --bg-primary: #0d1117; --bg-secondary: #161b22; --bg-card: #1c2333; --bg-card-hover: #242d3f;
    --text-primary: #e6edf3; --text-secondary: #8b949e; --text-muted: #6e7681;
    --accent-learn: #3b82f6; --accent-create: #a855f7; --accent-community: #22c55e; --accent-more: #eab308;
    --status-included: #22c55e; --status-tier2: #f59e0b; --status-alacarte: #3b82f6; --status-admin: #ef4444;
  }
  .btn {
    display: inline-block; padding: .75rem 1.75rem; font-size: 1rem; font-weight: 600;
    font-family: inherit; border: none; border-radius: 8px; cursor: pointer;
    transition: background-color .2s,transform .15s; text-align: center; line-height: 1.4; text-decoration: none;
  }
  .btn:hover { transform: translateY(-1px); }
  .btn-sm { padding: .5rem 1.25rem; font-size: .9rem; }
  .btn-learn     { background: #3b82f6; color:#fff; }
  .btn-learn:hover { background: #2563eb; }
  .btn-create    { background: #a855f7; color:#fff; }
  .btn-create:hover { background: #9333ea; }
  .btn-community { background: #22c55e; color:#fff; }
  .btn-community:hover { background: #16a34a; }
  .btn-more      { background: #eab308; color:#111; }
  .btn-more:hover { background: #ca8a04; }
  .btn-ghost     { background: transparent; color:#e6edf3; border:1.5px solid rgba(255,255,255,.15); }
  .btn-ghost:hover { background:rgba(255,255,255,.08); border-color:rgba(255,255,255,.3); }

  .section-title { font-family:Georgia,'Times New Roman',serif; font-size:1.75rem; font-weight:600; margin-bottom:1rem; text-align:center; color:#e6edf3; }
  .section-subtitle { text-align:center; color:#8b949e; max-width:600px; margin:0 auto 2.5rem; font-size:1.05rem; }

  .hero-buttons { display:flex; flex-wrap:wrap; gap:1rem; justify-content:center; max-width:900px; margin:0 auto; }
  .hero-buttons .btn { flex:1 1 200px; min-width:180px; }

  .districts-grid { display:grid; grid-template-columns:repeat(2,1fr); gap:1.5rem; }
  .district-card { background:#1c2333; border:1px solid rgba(255,255,255,.06); border-radius:12px; padding:1.5rem; transition:background .2s,border-color .2s,transform .15s; display:flex; flex-direction:column; }
  .district-card:hover { background:#242d3f; border-color:rgba(255,255,255,.12); transform:translateY(-2px); }
  .district-card h3 { font-family:Georgia,'Times New Roman',serif; font-size:1.5rem; font-weight:700; margin-bottom:.5rem; }
  .district-card p { color:#8b949e; font-size:.95rem; margin-bottom:1rem; }
  .district-card ul { list-style:none; margin-bottom:1.5rem; flex:1; }
  .district-card ul li { color:#e6edf3; font-size:.92rem; padding:.25rem 0 .25rem 1.25rem; position:relative; }
  .district-card ul li::before { content:"— "; position:absolute; left:0; color:#6e7681; font-weight:700; }
  .district-card ul li a { color:inherit; text-decoration:none; }
  .district-card ul li a:hover { text-decoration:underline; }

  .features-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(260px,1fr)); gap:1rem; }
  .feature-tile { background:#1c2333; border:1px solid rgba(255,255,255,.06); border-radius:8px; padding:1.5rem; transition:background .2s; text-decoration:none; display:block; }
  .feature-tile:hover { background:#242d3f; }
  .feature-tile h4 { font-size:1.05rem; font-weight:600; margin-bottom:.25rem; color:#e6edf3; }
  .feature-tile p { font-size:.88rem; color:#8b949e; margin-bottom:.75rem; }
  .feature-status { display:inline-block; font-size:.8rem; font-weight:700; padding:.2rem .6rem; border-radius:999px; text-transform:uppercase; letter-spacing:.03em; }
  .status-included { background:rgba(34,197,94,.15); color:#22c55e; }
  .status-tier2    { background:rgba(245,158,11,.15); color:#f59e0b; }
  .status-alacarte { background:rgba(59,130,246,.15); color:#3b82f6; }
  .status-admin    { background:rgba(239,68,68,.15);  color:#ef4444; }

  .roles-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(220px,1fr)); gap:1rem; }
  .role-card { background:#1c2333; border:1px solid rgba(255,255,255,.06); border-radius:8px; padding:1.5rem; text-align:center; transition:background .2s; }
  .role-card:hover { background:#242d3f; }
  .role-card h4 { font-size:1.1rem; font-weight:600; margin-bottom:.5rem; color:#e6edf3; }
  .role-card p { font-size:.88rem; color:#8b949e; margin-bottom:1rem; }

  .discovery-links { display:flex; flex-wrap:wrap; gap:1rem; justify-content:center; }
  .discovery-links .btn { min-width:160px; }

  .footer-links { display:flex; flex-wrap:wrap; gap:1.5rem; justify-content:center; margin-bottom:1.5rem; }
  .footer-links a { color:#8b949e; font-size:.9rem; text-decoration:none; transition:color .2s; }
  .footer-links a:hover { color:#e6edf3; }
  .footer-bottom { text-align:center; color:#6e7681; font-size:.82rem; padding-top:1.5rem; border-top:1px solid rgba(255,255,255,.04); }

  @media (max-width:768px) {
    .districts-grid { grid-template-columns:1fr; }
    .hero-buttons .btn { flex:1 1 100%; }
    .features-grid { grid-template-columns:1fr; }
    .roles-grid { grid-template-columns:1fr; }
    .discovery-links { flex-direction:column; align-items:center; }
    .discovery-links .btn { width:100%; max-width:300px; }
  }
`;
