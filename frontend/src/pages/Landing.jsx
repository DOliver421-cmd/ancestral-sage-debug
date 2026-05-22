import { Link } from "react-router-dom";
import { useEffect } from "react";
import { WAI_LOGO, BRAND } from "../lib/brand";
import { Heart, BookOpen, Users, Award, Zap, ArrowRight, MessageSquare, DollarSign, Shield } from "lucide-react";

export default function Landing() {
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
            <img src={WAI_LOGO} alt="W.A.I." className="w-12 h-12 object-contain" style={{ mixBlendMode: "multiply" }} />
            <div>
              <div className="overline text-copper leading-none">{BRAND.short}</div>
              <div className="font-heading font-bold text-sm leading-tight">{BRAND.name}</div>
            </div>
          </Link>
          <nav className="flex items-center gap-4">
            <a href="#services" className="text-sm font-medium hover:text-copper">Services</a>
            <a href="#for-creators" className="text-sm font-medium hover:text-copper">For Creators</a>
            <a href="#community" className="text-sm font-medium hover:text-copper">Community</a>
            <Link to="/login" className="text-sm font-bold uppercase tracking-widest hover:text-copper">Sign in</Link>
            <Link to="/register" className="btn-copper text-sm">Join Us</Link>
          </nav>
        </div>
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
              We're Here For You.<br />
              <span className="text-copper">No Extraction.</span><br />
              <span className="text-copper">Just Community.</span>
            </h1>

            <p className="text-xl text-ink/70 leading-relaxed mb-8 max-w-2xl mx-auto">
              Social support and educational services for communities that every other system has abandoned. We provide healing, learning, and economic opportunity — all built with you, not for profit off you.
            </p>

            <div className="flex flex-wrap justify-center gap-4 mb-16">
              <Link to="/register" className="btn-primary inline-flex items-center gap-2">
                Become A Creator <ArrowRight className="w-4 h-4" />
              </Link>
              <Link to="/more" className="btn-copper inline-flex items-center gap-2">
                <Users className="w-4 h-4" /> Find Support
              </Link>
              <Link to="/login" className="btn-ghost">Already Joined</Link>
            </div>

            {/* Value Props */}
            <div className="grid md:grid-cols-3 gap-8 mt-20">
              <div className="p-6 border border-ink/10 rounded-lg hover:border-copper/30 transition-colors">
                <DollarSign className="w-8 h-8 text-copper mb-4" />
                <h3 className="font-bold text-lg mb-2">Earn With Dignity</h3>
                <p className="text-sm text-ink/60">Creators get 70%. Not 30%. Not 50%. Your work pays you.</p>
              </div>
              <div className="p-6 border border-ink/10 rounded-lg hover:border-copper/30 transition-colors">
                <Shield className="w-8 h-8 text-copper mb-4" />
                <h3 className="font-bold text-lg mb-2">Your Privacy Protected</h3>
                <p className="text-sm text-ink/60">No extraction. No surveillance. No algorithmic manipulation.</p>
              </div>
              <div className="p-6 border border-ink/10 rounded-lg hover:border-copper/30 transition-colors">
                <Heart className="w-8 h-8 text-copper mb-4" />
                <h3 className="font-bold text-lg mb-2">Built For Your Community</h3>
                <p className="text-sm text-ink/60">Cultural alignment. Safety. Trust. Structural, not contractual.</p>
              </div>
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
              <h3 className="font-bold text-xl mb-3">Education On Your Terms</h3>
              <p className="text-sm text-ink/60 mb-4">
                Learning that speaks to your reality. Modules designed by your community, for your community.
              </p>
              <Link to="/login" className="text-sm font-bold text-copper hover:text-copper/80">
                Access Courses →
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
              <Link to="/login" className="text-sm font-bold text-copper hover:text-copper/80">
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

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {/* Creator 1: Poet */}
            <div className="group rounded-lg overflow-hidden border border-ink/10 hover:border-copper hover:shadow-lg transition-all">
              <div className="aspect-square bg-gradient-to-br from-copper/20 to-copper/5 flex items-center justify-center">
                <img
                  src="/images/creators/creator-1-poet.jpg"
                  alt="Black poet and writer"
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform"
                  onError={(e) => {
                    e.target.src = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 400 400'%3E%3Crect fill='%23f5e6d3' width='400' height='400'/%3E%3Ctext x='50%25' y='50%25' font-size='18' fill='%23666' text-anchor='middle' dominant-baseline='middle'%3EPoet %26 Writer%3C/text%3E%3C/svg%3E";
                  }}
                />
              </div>
              <div className="p-4">
                <h4 className="font-bold text-lg mb-2">Poet & Healer</h4>
                <p className="text-sm text-ink/60 mb-3">Sharing poetry for trauma recovery. 342 students.</p>
                <div className="flex items-center gap-2 text-copper text-sm font-bold">
                  <span className="text-lg">★★★★★</span> 4.9
                </div>
              </div>
            </div>

            {/* Creator 2: Visual Artist */}
            <div className="group rounded-lg overflow-hidden border border-ink/10 hover:border-copper hover:shadow-lg transition-all">
              <div className="aspect-square bg-gradient-to-br from-copper/20 to-copper/5 flex items-center justify-center">
                <img
                  src="/images/creators/creator-2-artist.jpg"
                  alt="Black visual artist"
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform"
                  onError={(e) => {
                    e.target.src = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 400 400'%3E%3Crect fill='%23f5e6d3' width='400' height='400'/%3E%3Ctext x='50%25' y='50%25' font-size='18' fill='%23666' text-anchor='middle' dominant-baseline='middle'%3EVisual Artist%3C/text%3E%3C/svg%3E";
                  }}
                />
              </div>
              <div className="p-4">
                <h4 className="font-bold text-lg mb-2">Visual Artist</h4>
                <p className="text-sm text-ink/60 mb-3">Teaching painting & mixed media. 215 students.</p>
                <div className="flex items-center gap-2 text-copper text-sm font-bold">
                  <span className="text-lg">★★★★★</span> 4.8
                </div>
              </div>
            </div>

            {/* Creator 3: Wellness Teacher */}
            <div className="group rounded-lg overflow-hidden border border-ink/10 hover:border-copper hover:shadow-lg transition-all">
              <div className="aspect-square bg-gradient-to-br from-copper/20 to-copper/5 flex items-center justify-center">
                <img
                  src="/images/creators/creator-3-healer.jpg"
                  alt="Black wellness instructor"
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform"
                  onError={(e) => {
                    e.target.src = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 400 400'%3E%3Crect fill='%23f5e6d3' width='400' height='400'/%3E%3Ctext x='50%25' y='50%25' font-size='18' fill='%23666' text-anchor='middle' dominant-baseline='middle'%3EWellness Teacher%3C/text%3E%3C/svg%3E";
                  }}
                />
              </div>
              <div className="p-4">
                <h4 className="font-bold text-lg mb-2">Wellness Guide</h4>
                <p className="text-sm text-ink/60 mb-3">Yoga & meditation for Black joy. 628 students.</p>
                <div className="flex items-center gap-2 text-copper text-sm font-bold">
                  <span className="text-lg">★★★★★</span> 4.9
                </div>
              </div>
            </div>

            {/* Creator 4: Musician */}
            <div className="group rounded-lg overflow-hidden border border-ink/10 hover:border-copper hover:shadow-lg transition-all">
              <div className="aspect-square bg-gradient-to-br from-copper/20 to-copper/5 flex items-center justify-center">
                <img
                  src="/images/creators/creator-4-musician.jpg"
                  alt="Black music producer"
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform"
                  onError={(e) => {
                    e.target.src = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 400 400'%3E%3Crect fill='%23f5e6d3' width='400' height='400'/%3E%3Ctext x='50%25' y='50%25' font-size='18' fill='%23666' text-anchor='middle' dominant-baseline='middle'%3EMusic Producer%3C/text%3E%3C/svg%3E";
                  }}
                />
              </div>
              <div className="p-4">
                <h4 className="font-bold text-lg mb-2">Music Producer</h4>
                <p className="text-sm text-ink/60 mb-3">Hip-hop production masterclass. 891 students.</p>
                <div className="flex items-center gap-2 text-copper text-sm font-bold">
                  <span className="text-lg">★★★★★</span> 4.7
                </div>
              </div>
            </div>
          </div>

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
              <h2 className="font-heading text-5xl font-bold mb-6">For Creators & Artists</h2>
              <p className="text-lg text-ink/60 mb-8">
                You're doing the healing work. Teaching. Creating. Building community. The system should pay you for it.
              </p>

              <div className="space-y-6 mb-8">
                <div className="flex gap-4">
                  <div className="w-6 h-6 rounded-full bg-copper/20 flex items-center justify-center flex-shrink-0 mt-1">
                    <div className="w-2 h-2 bg-copper rounded-full" />
                  </div>
                  <div>
                    <h4 className="font-bold mb-1">You keep 70% of revenue</h4>
                    <p className="text-sm text-ink/60">Not 30%. Not 50%. Seventy percent. You're not the product.</p>
                  </div>
                </div>

                <div className="flex gap-4">
                  <div className="w-6 h-6 rounded-full bg-copper/20 flex items-center justify-center flex-shrink-0 mt-1">
                    <div className="w-2 h-2 bg-copper rounded-full" />
                  </div>
                  <div>
                    <h4 className="font-bold mb-1">$500/month guaranteed for 10K+ followers</h4>
                    <p className="text-sm text-ink/60">A revenue floor so you can actually build a life doing your work.</p>
                  </div>
                </div>

                <div className="flex gap-4">
                  <div className="w-6 h-6 rounded-full bg-copper/20 flex items-center justify-center flex-shrink-0 mt-1">
                    <div className="w-2 h-2 bg-copper rounded-full" />
                  </div>
                  <div>
                    <h4 className="font-bold mb-1">Multiple revenue streams</h4>
                    <p className="text-sm text-ink/60">Subscriptions, tips, educational licensing, research partnerships.</p>
                  </div>
                </div>

                <div className="flex gap-4">
                  <div className="w-6 h-6 rounded-full bg-copper/20 flex items-center justify-center flex-shrink-0 mt-1">
                    <div className="w-2 h-2 bg-copper rounded-full" />
                  </div>
                  <div>
                    <h4 className="font-bold mb-1">Your content stays yours</h4>
                    <p className="text-sm text-ink/60">We don't own it. We don't resell it. You control everything.</p>
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
          <h2 className="font-heading text-5xl font-bold mb-6">Ready?</h2>
          <p className="text-xl text-white/80 mb-8">
            Whether you're a creator looking to earn with dignity, someone seeking support, or both — we're building this for you.
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
                <img src={WAI_LOGO} alt="W.A.I." className="w-8 h-8 object-contain" style={{ mixBlendMode: "screen" }} />
                <span className="font-bold text-white">{BRAND.short}</span>
              </div>
              <p className="text-sm">Social support and education for invisible communities.</p>
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
            <p>&copy; 2026 WAI Institute. Built with love for community.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
