import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  ArrowRight,
  Activity,
  BadgeCheck,
  DollarSign,
  Globe,
  ShieldCheck,
  Sparkles,
  Users,
  MapPin,
} from "lucide-react";
import PublicNav from "../components/PublicNav";
import BackButton from "../components/BackButton";
import { api } from "../lib/api";

const LANDSCAPE = [
  {
    icon: DollarSign,
    title: "Autonomous Finance",
    desc: "A self-managing finance department runs budgets, compliance, and expense flow for the M.O.R.E. Help Center.",
  },
  {
    icon: ShieldCheck,
    title: "Legal & Compliance",
    desc: "Governance guidance, risk controls, and community-safe procedures are built into every process.",
  },
  {
    icon: Users,
    title: "Community Market",
    desc: "A virtual African market plaza where visitors discover services, training, and trusted allies.",
  },
  {
    icon: Sparkles,
    title: "Creative Production",
    desc: "Media, course-building, branding and storytelling tools keep the hub vibrant and alive.",
  },
  {
    icon: Globe,
    title: "Platform Gateway",
    desc: "All calls are routed through the secure platform gateway so every API action is tracked and protected.",
  },
  {
    icon: Activity,
    title: "Supervisor Welcome",
    desc: "Every visitor is greeted by the Supervisor, who introduces the platform and points them to support and community resources.",
  },
];

const QUICK_ACTIONS = [
  { label: "Visit the Help Center", to: "/help-center", style: { background: "#f6d06d", color: "#1a1a2e" } },
  { label: "Explore M.O.R.E.", to: "/more", style: { background: "#0d7377", color: "white" } },
  { label: "Meet the Finance Team", to: "/more", style: { background: "#583c1d", color: "white" } },
  { label: "Executive Oversight", to: "/admin/system", style: { background: "#5a3d1a", color: "white" } },
];

const WAYPOINTS = [
  {
    icon: MapPin,
    title: "Entrance Atrium",
    desc: "Step in like a mall visitor and find the main path to finance, legal, and community services.",
  },
  {
    icon: Users,
    title: "Service Lanes",
    desc: "Move through themed lanes for support, training, production, and marketplace discovery.",
  },
  {
    icon: BadgeCheck,
    title: "Human Oversight Desk",
    desc: "Every AI-driven direction is backed by human review, audit, and executive supervision.",
  },
  {
    icon: Globe,
    title: "WAI Infrastructure",
    desc: "This hub is connected to the full WAI system, from course catalogs to executive controls.",
  },
];

const INFRASTRUCTURE_LINKS = [
  { label: "WAI Help Center", to: "/help-center", description: "Core support and community navigation." },
  { label: "M.O.R.E. Hub", to: "/more", description: "Community marketplace, free resources, and living systems." },
  { label: "Executive Corridor", to: "/admin/system", description: "Human oversight, audit, and executive review paths." },
  { label: "Plans & Programs", to: "/plans", description: "The broader WAI infrastructure of training and services." },
];

const ROLE_LANES = [
  {
    title: "Visitor lane",
    desc: "Public guests are guided to support, community learning, and marketplace discovery with clear wayfinding.",
    icon: Globe,
  },
  {
    title: "Operator lane",
    desc: "Platform operators manage service routing, compliance checks, and live response workflows.",
    icon: Activity,
  },
  {
    title: "Supervisor lane",
    desc: "Supervisors review AI suggestions, coordinate escalations, and maintain executive visibility.",
    icon: BadgeCheck,
  },
  {
    title: "Auditor lane",
    desc: "Auditors verify governance, privacy, and finance decisions with transparent records.",
    icon: ShieldCheck,
  },
];

export default function SeshatsHub() {
  const [gatewayStatus, setGatewayStatus] = useState({ label: "Checking…", state: "pending" });

  useEffect(() => {
    let mounted = true;
    api
      .get("/health")
      .then(() => {
        if (!mounted) return;
        setGatewayStatus({ label: "Gateway online", state: "online" });
      })
      .catch(() => {
        if (!mounted) return;
        setGatewayStatus({ label: "Gateway unavailable", state: "offline" });
      });
    return () => {
      mounted = false;
    };
  }, []);

  return (
    <div className="min-h-screen bg-[#f7efe6] text-[#1e1f25]">
      <PublicNav />
      <div className="max-w-7xl mx-auto px-6 py-10">
        <BackButton to="/help-center" />
        <section className="grid gap-10 lg:grid-cols-[1.2fr_0.8fr] items-start">
          <div>
            <div className="overline" style={{ color: "#8d5a33" }}>Supervisor Plaza</div>
            <h1 className="font-heading text-5xl font-black tracking-tight text-[#2b1f15] mt-3">Seshat’s Hub</h1>
            <p className="mt-6 max-w-3xl text-lg leading-8 text-[#4b4038]">
              Welcome to Seshat’s Hub — the virtual community center wrapped in an African marketplace and driven by the Supervisor. Walk through the plaza the way you would walk through a mall, with clear corridors, visible storefronts, and a human-guided path to every service.
            </p>
            <p className="mt-6 max-w-3xl text-lg leading-8 text-[#4b4038]">
              This hub is designed with security, privacy, and executive visibility built in. Every action is routed through governance checks, and fallback paths are available when automated systems need human support.
            </p>
            <div className="mt-10 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
              {WAYPOINTS.map((point) => {
                const Icon = point.icon;
                return (
                  <div key={point.title} className="rounded-[24px] border border-[#e2d3ba] bg-white p-6 shadow-[0_14px_35px_rgba(96,62,28,0.08)]">
                    <div className="inline-flex h-12 w-12 items-center justify-center rounded-3xl bg-[#f7ebdc] text-[#8c5c33]">
                      <Icon className="h-6 w-6" />
                    </div>
                    <h3 className="mt-5 text-lg font-bold text-[#2b1f15]">{point.title}</h3>
                    <p className="mt-3 text-sm leading-7 text-[#5c4c41]">{point.desc}</p>
                  </div>
                );
              })}
            </div>
            <div className="mt-8 rounded-[28px] border border-[#d1b38e] bg-[#fff6ec] p-8 shadow-[0_18px_60px_rgba(76,55,33,0.1)]">
              <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <div className="text-sm uppercase tracking-[0.35em] font-bold text-[#8d5a33]">Supervisor greeting</div>
                  <p className="mt-3 text-[#4d4338] leading-relaxed">
                    The Supervisor welcomes every visitor, explains the platform, and guides them to the right community resources, finance tools, and learning pathways.
                  </p>
                </div>
                <div className="rounded-3xl border border-[#e0c6a8] bg-[#fff1d9] px-5 py-4 text-sm font-semibold text-[#3f2e1d]">
                  {gatewayStatus.label}
                </div>
              </div>
            </div>
          </div>

          <div className="space-y-4 rounded-[28px] border border-[#ebd8c6] bg-[#fffdf7] p-7 shadow-[0_14px_50px_rgba(97,70,42,0.08)]">
            <div className="text-xs uppercase tracking-[0.35em] font-black text-[#7c593d]">Market Pulse</div>
            <div className="text-2xl font-bold text-[#2e1f17]">Live services in this plaza</div>
            <div className="mt-4 space-y-3">
              {QUICK_ACTIONS.map((action) => (
                <Link key={action.label} to={action.to} className="block rounded-3xl px-5 py-4 text-sm font-semibold transition hover:-translate-y-0.5" style={{ ...action.style }}>
                  {action.label}
                </Link>
              ))}
            </div>
          </div>
        </section>

        <section className="mt-16">
          <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
            <div>
              <p className="overline" style={{ color: "#8d5a33" }}>Designed around the hub</p>
              <h2 className="font-heading text-4xl font-black text-[#2b1f15]">What this hub is built to do</h2>
            </div>
            <div className="rounded-full border border-[#d7b290] bg-[#fff5e5] px-5 py-3 text-sm font-semibold text-[#5c422c]">
              Finance-led autonomy + community guidance
            </div>
          </div>
          <div className="grid gap-6 mt-8 lg:grid-cols-3">
            {LANDSCAPE.map((feature) => {
              const Icon = feature.icon;
              return (
                <div key={feature.title} className="rounded-[28px] border border-[#e4d1b4] bg-white p-8 shadow-[0_20px_45px_rgba(102,70,33,0.08)]">
                  <div className="inline-flex h-14 w-14 items-center justify-center rounded-3xl bg-[#f7ebdc] text-[#8c5c33]">
                    <Icon className="h-7 w-7" />
                  </div>
                  <h3 className="mt-5 text-xl font-bold text-[#2b1f15]">{feature.title}</h3>
                  <p className="mt-3 text-sm leading-7 text-[#5c4e44]">{feature.desc}</p>
                </div>
              );
            })}
          </div>
        </section>

        <section className="mt-20 rounded-[32px] border border-[#d8b88e] bg-[#fff1dd] p-10 shadow-[0_24px_80px_rgba(97,60,20,0.12)]">
          <div className="grid gap-10 lg:grid-cols-[1.2fr_0.8fr] items-center">
            <div>
              <div className="text-sm uppercase tracking-[0.35em] font-bold text-[#8d5a33]">Finance Backbone</div>
              <h2 className="mt-3 text-4xl font-black text-[#2b1f15]">The finance department acts like its own autonomous staff.</h2>
              <p className="mt-5 max-w-2xl text-lg leading-8 text-[#524236]">
                Every resource in the hub is supported by finance, compliance, and revenue operations. This makes the help center not just a landing spot, but a living marketplace that can route assistance, track budgets, and support community projects.
              </p>
              <ul className="mt-8 space-y-4 text-[#4c3f35]">
                <li className="flex gap-3"><BadgeCheck className="mt-1 h-5 w-5 text-[#8d5a33]" /> Real-time budget visibility for help center initiatives.</li>
                <li className="flex gap-3"><BadgeCheck className="mt-1 h-5 w-5 text-[#8d5a33]" /> Compliance and approvals built into autonomous workflows.</li>
                <li className="flex gap-3"><BadgeCheck className="mt-1 h-5 w-5 text-[#8d5a33]" /> Finance staff personas coordinate with production, legal, and community teams.</li>
              </ul>
            </div>

            <div className="rounded-[28px] border border-[#e3c6a6] bg-[#fff5e5] p-8">
              <div className="text-sm uppercase tracking-[0.35em] font-bold text-[#8d5a33]">Supervisor briefing</div>
              <div className="mt-5 space-y-4 text-[#4f4134]">
                <p>
                  The Supervisor is the landing greeter and navigator. It is the page’s host, offering a warm welcome and making the mission of the hub obvious from the first moment.
                </p>
                <p>
                  Visitors are guided into the African market experience, with finance, legal, community, and production services all clearly visible and accessible.
                </p>
                <p className="font-semibold text-[#6b4c2b]">
                  Human oversight is a must-have here: executive review, audit checkpoints, and real people ensure every action is safe, compliant, and accountable.
                </p>
              </div>
              <div className="mt-7 rounded-[24px] bg-[#fff1d2] p-5 text-[#3e2f1f]">
                <div className="font-semibold">Gateway status</div>
                <div className="mt-3 text-lg font-bold">{gatewayStatus.label}</div>
                <p className="mt-2 text-sm text-[#5b4735]">All API requests on this page are routed through the platform gateway to keep the system stable and secure.</p>
                <p className="mt-2 text-sm text-[#5b4735]">
                  If the gateway is unavailable, the hub will shift traffic to human-assisted channels and the Supervisor will offer a manual escalation path.
                </p>
              </div>
            </div>
          </div>
        </section>

        <section className="mt-16 rounded-[32px] border border-[#d8b88e] bg-[#fff9ed] p-10 shadow-[0_24px_60px_rgba(97,60,20,0.12)]">
          <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
            <div className="max-w-2xl">
              <div className="overline" style={{ color: "#8d5a33" }}>Governance pulse</div>
              <h2 className="mt-3 text-3xl font-black text-[#2b1f15]">Live oversight, analytics, and process flow</h2>
              <p className="mt-4 text-sm leading-7 text-[#5c4c41]">
                The hub surface is more than navigation: it is a monitored system with audit-ready checkpoints, process handoffs, and measurable service health.
              </p>
            </div>
            <div className="grid gap-4 sm:grid-cols-3 xl:grid-cols-3">
              <div className="rounded-[28px] border border-[#e2d2b7] bg-white p-5 text-sm text-[#5c4c41]">
                <div className="font-semibold text-[#2b1f15]">Audit readiness</div>
                <p className="mt-3">Every task can be traced back to a supervisor review and a compliance checklist.</p>
              </div>
              <div className="rounded-[28px] border border-[#e2d2b7] bg-white p-5 text-sm text-[#5c4c41]">
                <div className="font-semibold text-[#2b1f15]">Observability</div>
                <p className="mt-3">Usage trends, service demand, and escalation volume are visible in the platform dashboard.</p>
              </div>
              <div className="rounded-[28px] border border-[#e2d2b7] bg-white p-5 text-sm text-[#5c4c41]">
                <div className="font-semibold text-[#2b1f15]">Fallback mode</div>
                <p className="mt-3">When automation is unstable, the Supervisor switches to manual support and executive review routes.</p>
              </div>
            </div>
          </div>
          <div className="mt-8 grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
            <div className="rounded-[28px] border border-[#e4d1b4] bg-white p-7 shadow-[0_18px_50px_rgba(96,62,28,0.08)]">
              <div className="text-sm uppercase tracking-[0.35em] font-bold text-[#8d5a33]">Process map</div>
              <div className="mt-5 space-y-4 text-[#4c3f35]">
                <div className="rounded-3xl bg-[#f7ead9] p-5">
                  <div className="font-semibold">1. Request</div>
                  <div className="mt-2 text-sm">A visitor enters the plaza and selects help, service, finance, or community support.</div>
                </div>
                <div className="rounded-3xl bg-[#f7ead9] p-5">
                  <div className="font-semibold">2. Review</div>
                  <div className="mt-2 text-sm">The Supervisor and operator lane assess the need, apply compliance checks, and route the request.</div>
                </div>
                <div className="rounded-3xl bg-[#f7ead9] p-5">
                  <div className="font-semibold">3. Approve</div>
                  <div className="mt-2 text-sm">Human oversight verifies decisions, triggers executive visibility, or escalates to audit if needed.</div>
                </div>
                <div className="rounded-3xl bg-[#f7ead9] p-5">
                  <div className="font-semibold">4. Execute</div>
                  <div className="mt-2 text-sm">Workflows are completed and results are published to the help/manual system for future reference.</div>
                </div>
              </div>
            </div>
            <div className="rounded-[28px] border border-[#e4d1b4] bg-[#fff7e3] p-7 shadow-[0_18px_50px_rgba(96,62,28,0.08)]">
              <div className="text-sm uppercase tracking-[0.35em] font-bold text-[#8d5a33]">Service ownership</div>
              <div className="mt-5 space-y-4 text-[#4c3f35]">
                <p className="font-semibold">Finance</p>
                <p className="text-sm">Manages budgets, approvals, and audit trails for every community and help service.</p>
                <p className="font-semibold">Compliance</p>
                <p className="text-sm">Verifies that recommendations follow policy, privacy, and safety standards.</p>
                <p className="font-semibold">Community</p>
                <p className="text-sm">Operates the marketplace lanes and ensures each service has a visible help manual entry.</p>
              </div>
            </div>
          </div>
        </section>

        <section className="mt-16 rounded-[32px] border border-[#ded1be] bg-[#f9f3e8] p-10 shadow-[0_24px_60px_rgba(104,73,34,0.08)]">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <div className="overline" style={{ color: "#8d5a33" }}>WAI Institute Infrastructure</div>
              <h2 className="font-heading text-3xl font-black text-[#2b1f15]">Connected to the wider platform</h2>
              <p className="mt-4 max-w-2xl text-sm leading-7 text-[#5c4c41]">
                This hub is not isolated. It is part of the broader WAI Institute infrastructure, with links to community resources, learning, compliance, and executive oversight.
              </p>
            </div>
            <div className="rounded-full border border-[#d7b290] bg-[#fff5e5] px-5 py-3 text-sm font-semibold text-[#5c422c]">
              Built for human review and executive visibility
            </div>
          </div>
          <div className="mt-8 grid gap-6 lg:grid-cols-4">
            {INFRASTRUCTURE_LINKS.map((link) => (
              <Link key={link.label} to={link.to} className="block rounded-[28px] border border-[#e4d1b4] bg-white p-6 text-sm shadow-[0_18px_45px_rgba(102,70,33,0.08)] transition hover:-translate-y-0.5">
                <div className="font-bold text-[#2b1f15]">{link.label}</div>
                <p className="mt-3 text-[#5c4c41]">{link.description}</p>
              </Link>
            ))}
          </div>
        </section>

        <section className="mt-16 rounded-[32px] border border-[#e1d2be] bg-[#fff8f0] p-10 shadow-[0_24px_60px_rgba(104,73,34,0.08)]">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <div className="overline" style={{ color: "#8d5a33" }}>Role-based lanes</div>
              <h2 className="font-heading text-3xl font-black text-[#2b1f15]">Choose your entry path</h2>
              <p className="mt-4 max-w-2xl text-sm leading-7 text-[#5c4c41]">
                The hub supports different personas with specific corridors: public visitors, operators, supervisors, and auditors all have distinct journeys within the same marketplace.
              </p>
            </div>
          </div>
          <div className="mt-8 grid gap-6 md:grid-cols-2 xl:grid-cols-4">
            {ROLE_LANES.map((lane) => {
              const Icon = lane.icon;
              return (
                <div key={lane.title} className="rounded-[28px] border border-[#e4d1b4] bg-white p-7 shadow-[0_18px_45px_rgba(96,62,28,0.08)]">
                  <div className="inline-flex h-12 w-12 items-center justify-center rounded-3xl bg-[#f7ead9] text-[#855a32]">
                    <Icon className="h-6 w-6" />
                  </div>
                  <h3 className="mt-5 text-xl font-bold text-[#2b1f15]">{lane.title}</h3>
                  <p className="mt-3 text-sm leading-7 text-[#5c4c41]">{lane.desc}</p>
                </div>
              );
            })}
          </div>
        </section>

        <section className="mt-16">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p className="overline" style={{ color: "#8d5a33" }}>Meet the market</p>
              <h2 className="font-heading text-3xl font-black text-[#2b1f15]">What visitors do here</h2>
            </div>
            <div className="text-sm font-semibold text-[#5c4a3f]">Explore, learn, connect, and take action.</div>
          </div>
          <div className="mt-8 grid gap-6 md:grid-cols-2 xl:grid-cols-3">
            {[
              {
                title: "Receive a guided welcome",
                desc: "The Supervisor points new visitors to platform support, finance tools, and the help center.",
                icon: MapPin,
              },
              {
                title: "Access the help center",
                desc: "Find help across housing, legal, training, and community resources with a single click.",
                icon: Globe,
              },
              {
                title: "Join the market experience",
                desc: "Browse the community marketplace of services, courses, and production support.",
                icon: Users,
              },
            ].map((item) => {
              const Icon = item.icon;
              return (
                <div key={item.title} className="rounded-[28px] border border-[#e3ccb1] bg-white p-7 shadow-[0_18px_45px_rgba(90,60,30,0.08)]">
                  <div className="inline-flex h-12 w-12 items-center justify-center rounded-3xl bg-[#f7ead9] text-[#855a32]">
                    <Icon className="h-6 w-6" />
                  </div>
                  <h3 className="mt-5 text-xl font-bold text-[#2b1f15]">{item.title}</h3>
                  <p className="mt-3 text-sm leading-7 text-[#5c4c41]">{item.desc}</p>
                </div>
              );
            })}
          </div>
        </section>

        <div className="mt-16 flex flex-col gap-4 sm:flex-row sm:items-center">
          <Link className="inline-flex items-center justify-center gap-2 rounded-full bg-[#8d5a33] px-8 py-4 text-sm font-bold uppercase tracking-[0.18em] text-white transition hover:bg-[#734923]" to="/help-center">
            Enter the Help Center <ArrowRight className="h-4 w-4" />
          </Link>
          <Link className="inline-flex items-center justify-center gap-2 rounded-full border border-[#8d5a33] bg-white px-8 py-4 text-sm font-bold uppercase tracking-[0.18em] text-[#8d5a33] transition hover:bg-[#f2e2c4]" to="/more">
            Explore M.O.R.E. <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </div>
    </div>
  );
}
