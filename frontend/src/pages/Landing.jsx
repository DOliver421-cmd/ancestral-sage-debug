import { Link } from "react-router-dom";
import { useEffect, useState } from "react";
import { WAI_LOGO, BRAND } from "../lib/brand";
import { Heart, BookOpen, Users, Award, Zap, ArrowRight, MessageSquare, DollarSign, Shield, Menu, X, GraduationCap, Wrench, FileText } from "lucide-react";
import BugReportModal from "../components/BugReportModal";
import { api } from "../lib/api";

export default function Landing() {
  const [featuredCourses, setFeaturedCourses] = useState(null);
  const [siteAssets, setSiteAssets] = useState(null);
  const [mobileOpen, setMobileOpen] = useState(false);

  const LINKS = [
    { href: "#academy", label: "Homeschool Academy" },
    { href: "#services", label: "Services" },
    { href: "#for-creators", label: "For Creators" },
    { href: "#community", label: "Community" },
    { to: "/login", label: "Sign in" },
    { to: "/register", label: "Join Us" },
  ];

  useEffect(() => {
    api.get("/creator/courses/published?limit=4")
      .then(r => setFeaturedCourses(r.data.courses || []))
      .catch(() => setFeaturedCourses([]));
  }, []);

  // Executive-assigned imagery (hero + gallery). Silent on failure — the
  // landing page is fully designed without any uploaded assets.
  useEffect(() => {
    api.get("/site-assets")
      .then(r => setSiteAssets(r.data.assets || {}))
      .catch(() => setSiteAssets({}));
  }, []);

  useEffect(() => {
    // Handle smooth scroll to anchor links
    const handleAnchorClick = (e) => {
      const href = e.currentTarget.getAttribute("href");
      if (href?.startsWith("#")) {
        e.preventDefault();
        const targetId = href.slice(1);
        const element = document.getElementById(targetId);
        if (element) {
          const headerHeight = 80; // sticky header height
          const elementPosition = element.getBoundingClientRect().top + window.scrollY;
          window.scrollTo({
            top: elementPosition - headerHeight,
            behavior: "smooth",
          });
        }
      }
    };

    // Attach handler to all anchor links
    const anchorLinks = document.querySelectorAll('a[href^="#"]');
    anchorLinks.forEach((link) => {
      link.addEventListener("click", handleAnchorClick);
    });

    return () => {
      anchorLinks.forEach((link) => {
        link.removeEventListener("click", handleAnchorClick);
      });
    };
  }, []);

  return (
    <div className="min-h-screen bg-bone text-ink">
      {/* Header */}
      <header className="border-b border-ink/10 bg-bone sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-3">
            <img src={WAI_LOGO} alt="M.O.R.E." className="w-12 h-12 object-contain" />
            <div>
              <div className="overline text-copper leading-none">{BRAND.short}</div>
              <div className="font-heading font-bold text-sm leading-tight">{BRAND.name}</div>
            </div>
          </Link>

          {/* Desktop nav */}
          <nav className="hidden md:flex items-center gap-4">
            <a href="#academy" className="text-sm font-medium hover:text-copper">Homeschool Academy</a>
            <a href="#services" className="text-sm font-medium hover:text-copper">Services</a>
            <a href="#for-creators" className="text-sm font-medium hover:text-copper">For Creators</a>
            <a href="#community" className="text-sm font-medium hover:text-copper">Community</a>
            <Link to="/login" className="text-sm font-bold uppercase tracking-widest hover:text-copper">Sign in</Link>
            <Link to="/register" className="btn-copper text-sm">Join Us</Link>
          </nav>

          {/* Mobile hamburger */}
          <button
            className="md:hidden p-2 rounded-lg text-ink hover:text-copper"
            onClick={() => setMobileOpen((o) => !o)}
            aria-label="Toggle navigation"
          >
            {mobileOpen ? <X size={22} /> : <Menu size={22} />}
          </button>
        </div>

        {/* Mobile drawer */}
        {mobileOpen && (
          <div className="md:hidden border-t border-ink/10 bg-bone">
            <nav className="max-w-7xl mx-auto px-6 py-4 flex flex-col gap-3">
              {LINKS.map((l) => (
                l.href ? (
                  <a
                    key={l.href}
                    href={l.href}
                    className="text-sm font-medium hover:text-copper py-2 border-b border-ink/5"
                    onClick={() => setMobileOpen(false)}
                  >
                    {l.label}
                  </a>
                ) : (
                  <Link
                    key={l.to}
                    to={l.to}
                    className="text-sm font-medium hover:text-copper py-2 border-b border-ink/5"
                    onClick={() => setMobileOpen(false)}
                  >
                    {l.label}
                  </Link>
                )
              ))}
            </nav>
          </div>
        )}
      </header>

      {/* HERO: Vision Section */}
      <section className="relative overflow-hidden bg-gradient-to-b from-bone to-bone/50">
        <div className="absolute inset-0 grid-paper opacity-20 pointer-events-none" />
        <div className="max-w-7xl mx-auto px-6 py-32 relative">
          <div className="text-center max-w-3xl mx-auto">
            <div className="inline-block mb-6 px-4 py-2 bg-copper/10 border border-copper text-copper rounded-full text-sm font-bold uppercase tracking-widest">
              Community Platform
            </div>

            <h1 className="font-heading text-6xl sm:text-7xl font-extrabold leading-tight mb-8">
              Partner With Us.<br />
              <span className="text-copper">Together We Give</span><br />
              <span className="text-copper">The World Something Beautiful.</span>
            </h1>

            {siteAssets?.hero?.file_url && (
              <div className="mt-10 mb-4 rounded-lg overflow-hidden border border-ink/10 shadow-lg max-w-4xl mx-auto">
                <img
                  src={siteAssets.hero.file_url}
                  alt={siteAssets.hero.label || "Community"}
                  className="w-full object-cover"
                  onError={(e) => { e.target.closest("div").style.display = "none"; }}
                />
              </div>
 )}

            <p className="text-xl text-ink/70 leading-relaxed mb-8 max-w-2xl mx-auto">
              You're the healers. The teachers. The artists. The ones building culture. Let's stop pretending that's not the most valuable work. We're here to make sure you own it, keep the money it makes, and build community on your terms.
            </p>

            <div className="flex flex-wrap justify-center gap-4 mb-16">
              <Link to="/HomeschoolAcademy" className="btn-primary inline-flex items-center gap-2">
                <GraduationCap className="w-4 h-4" /> Start Homeschooling Free
              </Link>
              <Link to="/register" className="btn-copper inline-flex items-center gap-2">
                Become A Creator <ArrowRight className="w-4 h-4" />
              </Link>
              <Link to="/more" className="btn-copper inline-flex items-center gap-2">
                <Users className="w-4 h-4" /> Find Support
              </Link>
              <Link to="/login" className="btn-ghost">Already Joined</Link>
            </div>

            {/* Real Commitments */}
            <div className="grid md:grid-cols-3 gap-8 mt-20">
              <div className="p-6 border border-ink/10 rounded-lg hover:border-copper/30 transition-colors">
                <DollarSign className="w-8 h-8 text-copper mb-4" />
                <h3 className="font-bold text-lg mb-2">70% Is Yours</h3>
                <p className="text-sm text-ink/60">Not a percentage we negotiate. Not "fair share." Seventy. You keep what you earn.</p>
              </div>
              <div className="p-6 border border-ink/10 rounded-lg hover:border-copper/30 transition-colors">
                <Heart className="w-8 h-8 text-copper mb-4" />
                <h3 className="font-bold text-lg mb-2">Your Content Stays Yours</h3>
                <p className="text-sm text-ink/60">We don't own it. We don't resell it. You control everything. Forever.</p>
              </div>
              <div className="p-6 border border-ink/10 rounded-lg hover:border-copper/30 transition-colors">
                <Shield className="w-8 h-8 text-copper mb-4" />
                <h3 className="font-bold text-lg mb-2">Built BY Us, Not FOR Us</h3>
                <p className="text-sm text-ink/60">You decide what gets built. We move at community speed, not venture speed.</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ACADEMY: the $0 doorway — the hook (owner decision 2026-10-12) */}
      <section id="academy" className="bg-ink text-white relative overflow-hidden">
        <div className="absolute inset-0 opacity-[0.07]" style={{ backgroundImage: "radial-gradient(circle at 1px 1px, #fff 1px, transparent 0)", backgroundSize: "28px 28px" }} />
        <div className="relative max-w-7xl mx-auto px-6 py-20">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-signal/40 bg-signal/10 text-signal text-xs font-black uppercase tracking-widest mb-6">
                <GraduationCap className="w-3.5 h-3.5" /> The $0 doorway
              </div>
              <h2 className="font-heading text-5xl md:text-6xl font-black leading-[1.02] mb-5">
                Homeschool, <span className="text-signal">done right.</span>
              </h2>
              <p className="text-white/70 text-xl leading-relaxed max-w-xl mb-8">
                A sequenced K–12 academy for your family — real academics, trade
                tracks, and printable records. One free account runs every
                learner in your household: you pick the grade, the track, and
                the pace, and lessons unlock as your child earns mastery.
              </p>
              <div className="flex flex-wrap items-center gap-4">
                <Link to="/HomeschoolAcademy" className="inline-flex items-center gap-2 px-7 py-3.5 bg-signal text-ink font-black hover:bg-signal/85 transition-all shadow-[4px_4px_0_rgba(255,255,255,0.15)]">
                  Start Homeschooling Free <ArrowRight className="w-4 h-4" />
                </Link>
                <Link to="/academy/curriculum" className="inline-flex items-center gap-2 px-7 py-3.5 border-2 border-white/30 text-white font-bold hover:bg-white/10 transition-colors">
                  See the Curriculum
                </Link>
              </div>
            </div>
            <div className="grid sm:grid-cols-2 gap-3">
              {[
                { icon: BookOpen, title: "Sequenced K–12", desc: "ELA, Math, Science and Social Studies, grade by grade." },
                { icon: Wrench, title: "Trade tracks", desc: "Builder, Artist, Scholar, Adult Ed, Life Skills, Leadership, Career, Entrepreneurship." },
                { icon: Users, title: "Run by the parent", desc: "One account, multiple learners, no per-child logins." },
                { icon: FileText, title: "Printable records", desc: "Progress, mastery scores and dates, ready to file." },
              ].map((c) => (
                <div key={c.title} className="bg-white/5 border border-white/10 rounded-lg p-5">
                  <c.icon className="w-6 h-6 text-signal mb-3" />
                  <div className="font-bold text-white mb-1">{c.title}</div>
                  <p className="text-sm text-white/60 leading-relaxed">{c.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* SERVICES: What We Offer */}
      <section id="services" className="py-24 bg-white border-t border-ink/10">
        <div className="max-w-7xl mx-auto px-6">
          <h2 className="font-heading text-5xl font-bold mb-4 text-center">What We Offer</h2>
          <p className="text-lg text-ink/60 text-center max-w-2xl mx-auto mb-16">
            Everything you need to heal, learn, create, and build economic power.
          </p>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {/* Creator Marketplace */}
            <div className="group p-8 border border-ink/10 rounded-lg hover:border-copper hover:shadow-lg transition-all">
              <div className="w-12 h-12 bg-copper/10 rounded-lg flex items-center justify-center mb-4 group-hover:bg-copper group-hover:text-white transition-colors">
                <Heart className="w-6 h-6 text-copper group-hover:text-white" />
              </div>
              <h3 className="font-bold text-xl mb-3">Creator Marketplace</h3>
              <p className="text-sm text-ink/60 mb-4">
                Poets, artists, healers — monetize your work. You keep 70%. Subscribers pay what they can.
              </p>
              <Link to="/register" className="text-sm font-bold text-copper hover:text-copper/80">
                Start Creating →
              </Link>
            </div>

            {/* Educational Access */}
            <div className="group p-8 border border-ink/10 rounded-lg hover:border-copper hover:shadow-lg transition-all">
              <div className="w-12 h-12 bg-copper/10 rounded-lg flex items-center justify-center mb-4 group-hover:bg-copper group-hover:text-white transition-colors">
                <BookOpen className="w-6 h-6 text-copper group-hover:text-white" />
              </div>
              <h3 className="font-bold text-xl mb-3">Homeschool Academy</h3>
              <p className="text-sm text-ink/60 mb-4">
                A sequenced K–12 academy with trade tracks, parent-managed learners, and printable records — free to start.
              </p>
              <Link to="/HomeschoolAcademy" className="text-sm font-bold text-copper hover:text-copper/80">
                Start Homeschooling Free →
              </Link>
            </div>

            {/* Community Support */}
            <div className="group p-8 border border-ink/10 rounded-lg hover:border-copper hover:shadow-lg transition-all">
              <div className="w-12 h-12 bg-copper/10 rounded-lg flex items-center justify-center mb-4 group-hover:bg-copper group-hover:text-white transition-colors">
                <Users className="w-6 h-6 text-copper group-hover:text-white" />
              </div>
              <h3 className="font-bold text-xl mb-3">Community & Support</h3>
              <p className="text-sm text-ink/60 mb-4">
                Connect. Share. Heal together. Real people, real support, real community.
              </p>
              <Link to="/more" className="text-sm font-bold text-copper hover:text-copper/80">
                Find Support →
              </Link>
            </div>

            {/* Healing Resources */}
            <div className="group p-8 border border-ink/10 rounded-lg hover:border-copper hover:shadow-lg transition-all">
              <div className="w-12 h-12 bg-copper/10 rounded-lg flex items-center justify-center mb-4 group-hover:bg-copper group-hover:text-white transition-colors">
                <Zap className="w-6 h-6 text-copper group-hover:text-white" />
              </div>
              <h3 className="font-bold text-xl mb-3">Healing Content</h3>
              <p className="text-sm text-ink/60 mb-4">
                Poetry, spoken word, guidance on grief, resilience, identity, belonging.
              </p>
              <Link to="/register" className="text-sm font-bold text-copper hover:text-copper/80">
                Explore Healing →
              </Link>
            </div>

            {/* Skill Building */}
            <div className="group p-8 border border-ink/10 rounded-lg hover:border-copper hover:shadow-lg transition-all">
              <div className="w-12 h-12 bg-copper/10 rounded-lg flex items-center justify-center mb-4 group-hover:bg-copper group-hover:text-white transition-colors">
                <Award className="w-6 h-6 text-copper group-hover:text-white" />
              </div>
              <h3 className="font-bold text-xl mb-3">Build Skills</h3>
              <p className="text-sm text-ink/60 mb-4">
                Mentorship, workshops, and tools to develop the skills that matter in your community.
              </p>
              <Link to="/modules" className="text-sm font-bold text-copper hover:text-copper/80">
                Start Learning →
              </Link>
            </div>

            {/* Support & Resources */}
            <div className="group p-8 border border-ink/10 rounded-lg hover:border-copper hover:shadow-lg transition-all">
              <div className="w-12 h-12 bg-copper/10 rounded-lg flex items-center justify-center mb-4 group-hover:bg-copper group-hover:text-white transition-colors">
                <MessageSquare className="w-6 h-6 text-copper group-hover:text-white" />
              </div>
              <h3 className="font-bold text-xl mb-3">Always Someone To Talk To</h3>
              <p className="text-sm text-ink/60 mb-4">
                Questions? Struggles? There's always someone here who gets it.
              </p>
              <Link to="/more" className="text-sm font-bold text-copper hover:text-copper/80">
                Get Help Now →
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* FEATURED CREATORS */}
      <section className="py-24 bg-white border-t border-ink/10">
        <div className="max-w-7xl mx-auto px-6">
          <h2 className="font-heading text-5xl font-bold mb-4 text-center">Creators Like You</h2>
          <p className="text-lg text-ink/60 text-center max-w-2xl mx-auto mb-16">
            Poets. Artists. Healers. Teachers. Building income and community on their own terms.
          </p>

          {featuredCourses === null ? (
            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
              {[1,2,3,4].map(i => (
                <div key={i} className="rounded-lg overflow-hidden border border-ink/10 animate-pulse">
                  <div className="aspect-square bg-ink/5" />
                  <div className="p-4 space-y-2">
                    <div className="h-4 bg-ink/10 rounded w-3/4" />
                    <div className="h-3 bg-ink/5 rounded w-full" />
                  </div>
                </div>
              ))}
            </div>
          ) : featuredCourses.length === 0 ? (
            <div className="text-center py-12 border border-dashed border-copper/30 rounded-2xl">
              <p className="text-ink/50 mb-4">Creators are just getting started. Be the first.</p>
              <Link to="/register" className="btn-primary inline-flex items-center gap-2">
                Start Creating <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          ) : (
            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
              {featuredCourses.map(course => (
                <div key={course.course_id} className="group rounded-lg overflow-hidden border border-ink/10 hover:border-copper hover:shadow-lg transition-all">
                  <div className="aspect-square bg-gradient-to-br from-copper/20 to-copper/5 flex items-center justify-center overflow-hidden">
                    {course.thumbnail_url ? (
                      <img
                        src={course.thumbnail_url}
                        alt={course.title}
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform"
                        onError={(e) => { e.target.style.display = "none"; }}
                      />
                    ) : (
                      <span className="text-4xl text-copper/40 font-bold">{(course.category || course.title || "?")[0].toUpperCase()}</span>
                    )}
                  </div>
                  <div className="p-4">
                    <h4 className="font-bold text-lg mb-1 line-clamp-2 leading-snug">{course.title}</h4>
                    <p className="text-sm text-ink/60 mb-3 line-clamp-2">
                      {course.description || course.category || ""}
                      {course.enrollment_count > 0 && ` · ${course.enrollment_count} enrolled`}
                    </p>
                    <div className="text-sm font-bold text-copper">
                      {course.price_cents === 0 ? "No charge" : `$${(course.price_cents / 100).toFixed(0)}`}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          <div className="text-center mt-12">
            <Link to="/register" className="btn-primary inline-flex items-center gap-2">
              Become A Creator Too <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </section>

      {/* FOR CREATORS */}
      <section id="for-creators" className="py-24 bg-bone">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <h2 className="font-heading text-5xl font-bold mb-6">For Creators & Builders</h2>
              <p className="text-lg text-ink/60 mb-8">
                Your work is sacred. Teaching is sacred. Healing is sacred. Creating culture is sacred. Stop apologizing for charging for it.
              </p>

              <div className="space-y-6 mb-8">
                <div className="flex gap-4">
                  <div className="w-6 h-6 rounded-full bg-copper/20 flex items-center justify-center flex-shrink-0 mt-1">
                    <div className="w-2 h-2 bg-copper rounded-full" />
                  </div>
                  <div>
                    <h4 className="font-bold mb-1">You keep 70%. Monthly. On the 1st.</h4>
                    <p className="text-sm text-ink/60">Not someday. Not "when we feel like it." Automatic deposit every month.</p>
                  </div>
                </div>

                <div className="flex gap-4">
                  <div className="w-6 h-6 rounded-full bg-copper/20 flex items-center justify-center flex-shrink-0 mt-1">
                    <div className="w-2 h-2 bg-copper rounded-full" />
                  </div>
                  <div>
                    <h4 className="font-bold mb-1">Pricing that grows with demand</h4>
                    <p className="text-sm text-ink/60">Start super cheap ($1.99-$9.99). Price increases as more people find your work. Early students lock in low price forever.</p>
                  </div>
                </div>

                <div className="flex gap-4">
                  <div className="w-6 h-6 rounded-full bg-copper/20 flex items-center justify-center flex-shrink-0 mt-1">
                    <div className="w-2 h-2 bg-copper rounded-full" />
                  </div>
                  <div>
                    <h4 className="font-bold mb-1">Your content. Your terms. Forever.</h4>
                    <p className="text-sm text-ink/60">We don't own it. We can't sell it without you. You can leave anytime and take it with you.</p>
                  </div>
                </div>

                <div className="flex gap-4">
                  <div className="w-6 h-6 rounded-full bg-copper/20 flex items-center justify-center flex-shrink-0 mt-1">
                    <div className="w-2 h-2 bg-copper rounded-full" />
                  </div>
                  <div>
                    <h4 className="font-bold mb-1">No algorithm. No shadow bans. No games.</h4>
                    <p className="text-sm text-ink/60">Your students find you. You build your community. We don't manipulate what they see.</p>
                  </div>
                </div>
              </div>

              <Link to="/register" className="btn-primary inline-flex items-center gap-2">
                Become A Creator <ArrowRight className="w-4 h-4" />
              </Link>
            </div>

            <div className="bg-copper/5 border border-copper/20 rounded-lg p-8">
              <h4 className="font-bold text-lg mb-6">Real Numbers</h4>
              <div className="space-y-6">
                <div>
                  <div className="text-4xl font-bold text-copper mb-2">$9.99</div>
                  <div className="text-sm text-ink/60">Basic tier monthly subscription</div>
                </div>
                <div>
                  <div className="text-4xl font-bold text-copper mb-2">70%</div>
                  <div className="text-sm text-ink/60">What creators actually earn</div>
                </div>
                <div>
                  <div className="text-4xl font-bold text-copper mb-2">$500</div>
                  <div className="text-sm text-ink/60">Monthly minimum (with 10K followers)</div>
                </div>
                <div className="border-t border-copper/20 pt-6 mt-6">
                  <p className="text-sm text-ink/60">
                    100 subscribers at $9.99/month = <strong>$700/month income</strong> (after you hit the 10K threshold)
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* HOW IT WORKS */}
      <section className="py-24 bg-white border-t border-ink/10">
        <div className="max-w-7xl mx-auto px-6">
          <h2 className="font-heading text-5xl font-bold mb-4 text-center">How It Works</h2>
          <p className="text-lg text-ink/60 text-center max-w-2xl mx-auto mb-16">
            No complicated processes. No extraction. Just straightforward.
          </p>

          <div className="grid md:grid-cols-4 gap-8">
            <div className="text-center">
              <div className="w-16 h-16 bg-copper/10 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="font-bold text-2xl text-copper">1</span>
              </div>
              <h4 className="font-bold text-lg mb-2">Sign Up</h4>
              <p className="text-sm text-ink/60">Create your account as a creator or community member.</p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-copper/10 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="font-bold text-2xl text-copper">2</span>
              </div>
              <h4 className="font-bold text-lg mb-2">Create or Connect</h4>
              <p className="text-sm text-ink/60">Share your work, take classes, or find support.</p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-copper/10 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="font-bold text-2xl text-copper">3</span>
              </div>
              <h4 className="font-bold text-lg mb-2">Build Community</h4>
              <p className="text-sm text-ink/60">Your audience grows. Your impact spreads.</p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-copper/10 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="font-bold text-2xl text-copper">4</span>
              </div>
              <h4 className="font-bold text-lg mb-2">Earn Together</h4>
              <p className="text-sm text-ink/60">You earn. Community grows. Everyone wins.</p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-24 bg-ink text-white">
        <div className="max-w-3xl mx-auto px-6 text-center">
          <h2 className="font-heading text-5xl font-bold mb-6">Let's Build This</h2>
          <p className="text-xl text-white/80 mb-8">
            If you're tired of systems that extract your labor, your culture, your genius—and you want to build something with people who actually get it. That's why we're here.
          </p>

          <div className="flex flex-wrap justify-center gap-4">
            <Link to="/register" className="btn-primary inline-flex items-center gap-2">
              Join Us <ArrowRight className="w-4 h-4" />
            </Link>
            <Link to="/login" className="px-6 py-3 border-2 border-white text-white font-bold hover:bg-white hover:text-ink transition-colors rounded-sm">
              Sign In
            </Link>
          </div>
        </div>
      </section>

      {/* Community & Footer */}
      <footer id="community" className="bg-ink/95 text-white/60 border-t border-white/10 py-12">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid md:grid-cols-4 gap-8 mb-12">
            <div>
              <div className="flex items-center gap-2 mb-4">
                <img src={WAI_LOGO} alt="M.O.R.E." className="w-8 h-8 object-contain" />
                <span className="font-bold text-white">{BRAND.short}</span>
              </div>
              <p className="text-sm">Skills, support, and solidarity — free for the community.</p>
            </div>
            <div>
              <h4 className="font-bold text-white mb-4">Community</h4>
              <ul className="space-y-2 text-sm">
                <li><a href="#community" className="hover:text-white transition-colors">About Us</a></li>
                <li><a href="#services" className="hover:text-white transition-colors">Services</a></li>
                <li><Link to="/more" className="hover:text-white transition-colors">Get Support</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="font-bold text-white mb-4">For Creators</h4>
              <ul className="space-y-2 text-sm">
                <li><Link to="/register" className="hover:text-white transition-colors">Become Creator</Link></li>
                <li><a href="#for-creators" className="hover:text-white transition-colors">Creator Info</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-bold text-white mb-4">Account</h4>
              <ul className="space-y-2 text-sm">
                <li><Link to="/login" className="hover:text-white transition-colors">Sign In</Link></li>
                <li><Link to="/register" className="hover:text-white transition-colors">Join</Link></li>
              </ul>
            </div>
          </div>

          <div className="border-t border-white/10 pt-8 text-sm text-center">
            <p>&copy; 2026 Michael Oliver Resource Exchange. Built with love for community.</p>
          </div>
        </div>
      </footer>

      <BugReportModal />
    </div>
  );
}
