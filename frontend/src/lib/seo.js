// Domain-aware SEO — one build, two doors (see docs/morehelp-migration-blueprint.md §4.6).
// Each route gets a title/description for the WAI door (high-intent technical terms:
// NFPA 70, NEC 2023, electrical safety) and one for the M.O.R.E. door (support,
// community, creative terms). A fallback covers any path not listed.
import { useEffect } from "react";
import { useLocation } from "react-router-dom";
import { isWaiDoor } from "./domain";

const ROUTES = [
  {
    match: "/",
    wai: {
      title: "WAI Institute — Electrical Education, NFPA 70 / NEC 2023 Training & Credentials",
      desc: "Trade training that pays, credentials that verify, and media skills that move the message. Electrical curriculum, workforce labs, compliance (NFPA 70 / NEC 2023), and AI Tutor — focused and professional.",
    },
    more: {
      title: "M.O.R.E. Help Center — Skills, Support & Community",
      desc: "The social-service virtual help center of the Michael Oliver Resource Exchange. Free courses, support resources, billing self-service, community chat, and the M.O.R.E. creative suite.",
    },
  },
  {
    match: "/modules",
    wai: {
      title: "Electrical Curriculum — WAI Institute",
      desc: "Structured electrical training modules: residential and commercial theory, code practice, and hands-on skill demonstrations for the trade.",
    },
    more: {
      title: "Course Catalog — M.O.R.E. Help Center",
      desc: "Free courses and training for every level — electrical trade, job readiness, and community learning.",
    },
  },
  {
    match: "/courses",
    wai: {
      title: "Courses & Training — WAI Institute",
      desc: "Electrical education and professional media courses from WAI Institute. Enroll to build verified, career-ready skills.",
    },
    more: {
      title: "Courses & Job Training — M.O.R.E. Help Center",
      desc: "Free and low-cost training paths — electrical, media, and job-readiness courses open to everyone.",
    },
  },
  {
    match: "/labs",
    wai: {
      title: "Workforce Labs — WAI Institute",
      desc: "Interactive electrical workforce labs and simulations. Practice real trade skills in a safe, guided environment.",
    },
    more: {
      title: "Workforce Labs — M.O.R.E. Help Center",
      desc: "Hands-on labs and simulations that build real job skills.",
    },
  },
  {
    match: "/credentials",
    wai: {
      title: "Credentials & Certificates — WAI Institute",
      desc: "Earn verified credentials and certificates for electrical training. Competency checks and portfolio evidence of your trade skills.",
    },
    more: {
      title: "Credentials & Certificates — M.O.R.E. Help Center",
      desc: "Track your certificates, competencies, and learning portfolio.",
    },
  },
  {
    match: "/compliance",
    wai: {
      title: "NFPA 70 / NEC 2023 Compliance Training — WAI Institute",
      desc: "Electrical code compliance training built around NFPA 70 / NEC 2023. Stay current on the code that governs the trade.",
    },
    more: {
      title: "Compliance Training — M.O.R.E. Help Center",
      desc: "Electrical code and workplace compliance learning resources.",
    },
  },
  {
    match: "/ai",
    wai: {
      title: "AI Tutor — WAI Institute",
      desc: "The on-demand learning guide for electrical education. Free, always available, powered by the M.O.R.E. gateway.",
    },
    more: {
      title: "AI Tutor — M.O.R.E. Help Center",
      desc: "Your free on-demand learning companion for any topic on the platform.",
    },
  },
  {
    match: "/help-center",
    wai: {
      title: "Help Center — M.O.R.E.",
      desc: "Housing, legal, food, jobs, education, and health help — free and in plain language from the M.O.R.E. Help Center.",
    },
    more: {
      title: "Help Center — M.O.R.E.",
      desc: "Housing, legal, food, jobs, education, and health help — free and in plain language from the M.O.R.E. Help Center.",
    },
  },
  {
    match: "/knowledge-base",
    wai: {
      title: "Knowledge Base — M.O.R.E. Help Center",
      desc: "Handbooks, troubleshooting guides, browser requirements, certificate delivery, and billing answers — the M.O.R.E. Knowledge Base.",
    },
    more: {
      title: "Knowledge Base — M.O.R.E. Help Center",
      desc: "Handbooks, troubleshooting guides, browser requirements, certificate delivery, and billing answers — the M.O.R.E. Knowledge Base.",
    },
  },
  {
    match: "/site-guide",
    wai: {
      title: "Site Guide — M.O.R.E.",
      desc: "How to use the platform: accounts, navigation, settings, and getting around both doors.",
    },
    more: {
      title: "Site Guide — M.O.R.E.",
      desc: "How to use the platform: accounts, navigation, settings, and getting around both doors.",
    },
  },
  {
    match: "/store",
    more: {
      title: "Store — M.O.R.E. Help Center",
      desc: "Digital products, media, and merch from M.O.R.E. and WAI Institute creators. Secure checkout with instant delivery.",
    },
  },
  {
    match: "/plans",
    more: {
      title: "Membership Plans — M.O.R.E. Help Center",
      desc: "Simple membership plans that unlock the full M.O.R.E. experience. Free tier available — no credit card required to start.",
    },
  },
  {
    match: "/subscribe",
    more: {
      title: "Subscribe — M.O.R.E. Help Center",
      desc: "Manage your M.O.R.E. membership subscription and billing.",
    },
  },
  {
    match: "/donate",
    more: {
      title: "Donate — M.O.R.E. Help Center",
      desc: "Support the Michael Oliver Resource Exchange and keep help free for the community.",
    },
  },
  {
    match: "/more-help-center",
    more: {
      title: "M.O.R.E. Help Center — Hub",
      desc: "Your hub for support, billing, community, and the creative suite.",
    },
  },
  {
    match: "/login",
    wai: {
      title: "Sign In — WAI Institute",
      desc: "Sign in to your WAI Institute account for classrooms, labs, credentials, and the AI Tutor.",
    },
    more: {
      title: "Sign In — M.O.R.E. Help Center",
      desc: "Sign in to your M.O.R.E. account.",
    },
  },
  {
    match: "/register",
    wai: {
      title: "Create Account — WAI Institute",
      desc: "Create a free WAI Institute account to enroll in electrical training, labs, and credentials.",
    },
    more: {
      title: "Create Account — M.O.R.E. Help Center",
      desc: "Create a free M.O.R.E. account — 60 seconds, no credit card required.",
    },
  },
];

const DEFAULT = {
  wai: {
    title: "WAI Institute — Electrical Education & Credentials",
    desc: "Trade training that pays, credentials that verify, and media skills that move the message. Electrical education, NFPA 70 / NEC 2023 compliance, and AI Tutor.",
  },
  more: {
    title: "M.O.R.E. Help Center — Michael Oliver Resource Exchange",
    desc: "The social-service virtual help center of the Michael Oliver Resource Exchange. Skills, support, and community resources — free for everyone.",
  },
};

function setMeta(attr, name, content) {
  let el = document.head.querySelector(`meta[${attr}="${name}"]`);
  if (!el) {
    el = document.createElement("meta");
    el.setAttribute(attr, name);
    document.head.appendChild(el);
  }
  el.setAttribute("content", content);
}

export function useSeoManager() {
  const location = useLocation();
  const waiDoor = isWaiDoor();
  useEffect(() => {
    const path = location.pathname;
    const segs = path.split("/").filter(Boolean);
    // Longest-prefix match so /modules/:slug inherits /modules SEO.
    let hit = null;
    for (const r of ROUTES) {
      const rSegs = r.match.split("/").filter(Boolean);
      if (rSegs.length > segs.length) continue;
      const ok = rSegs.every((s, i) => segs[i] === s);
      if (ok && (!hit || rSegs.length > hit.match.split("/").filter(Boolean).length)) hit = r;
    }
    const entry = (hit && hit[waiDoor ? "wai" : "more"]) || DEFAULT[waiDoor ? "wai" : "more"];
    const title = entry.title;
    const desc = entry.desc;
    const url = `${window.location.origin}${path}`;

    document.title = title;
    setMeta("name", "description", desc);
    setMeta("property", "og:title", title);
    setMeta("property", "og:description", desc);
    setMeta("property", "og:url", url);
    setMeta("name", "twitter:title", title);
    setMeta("name", "twitter:description", desc);
  }, [location.pathname, waiDoor]);
}
