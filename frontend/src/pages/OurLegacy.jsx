import { useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import { WAI_LOGO, BRAND } from "../lib/brand";
import { toast } from "sonner";
import {
  ArrowRight, BookOpen, GraduationCap, HardHat, HeartHandshake, LogIn,
  Music, Sprout, Store, Truck, UserPlus,
} from "lucide-react";
import CheckoutModal from "../components/CheckoutModal";

const BOOK_PRICE = 59;

const BOOKS = [
  {
    key: "book",
    title: "Our Legacy · Our Future",
    subtitle: "Building Thriving Black Communities with AI",
    filename: "Our_Legacy_Our_Future_More_Help_Edition.pdf",
    description:
      "A practical manual from the future — with just enough humor to keep you awake. A field guide for communities ready to build, grow, and thrive with AI as a partner, teammate, and co-creator.",
  },
  {
    key: "grassroots_guide",
    title: "The Grassroots Guide",
    subtitle: "Building your Platform",
    filename: "The_Grassroots_Guide_to_Building_your_Platform.pdf",
    description:
      "A step-by-step playbook for building a community platform from the ground up — rooted in culture, powered by purpose, and built to last.",
  },
];

// The eight capability areas promoted to the community (source: the book).
const PILLARS = [
  {
    icon: Sprout,
    title: "AI-Powered Agriculture",
    desc: "Food systems upgraded — yield prediction, soil health, and smarter farms feeding stronger communities.",
  },
  {
    icon: GraduationCap,
    title: "AI-Enhanced Education",
    desc: "An AI learning partner: personalized lessons, progress tracking, and smart recommendations that meet learners where they are.",
  },
  {
    icon: HardHat,
    title: "AI Construction Assistant",
    desc: "Smarter building, stronger communities — project planning and trade skills supported by AI as a teammate, not a replacement.",
  },
  {
    icon: Music,
    title: "AI Music Studio",
    desc: "Amplifying creativity — production, mixing, and distribution tools that keep the culture at the center of the sound.",
  },
  {
    icon: Store,
    title: "AI-Driven Businesses",
    desc: "Zuri's Boutique Business Assistant — inventory insights, customer trends, and marketing ideas for independent owners.",
  },
  {
    icon: HeartHandshake,
    title: "AI-Powered Worship & Outreach",
    desc: "A Community Outreach Hub: event planning, volunteer matching, needs assessment, and resource allocation that serve the neighborhood.",
  },
  {
    icon: Truck,
    title: "AI Market Logistics",
    desc: "Stronger markets, stronger communities — demand forecasting, inventory tracking, supply chain, and route optimization.",
  },
];

const AUDIENCES = [
  "the builders",
  "the dreamers",
  "the organizers",
  "the innovators",
  "the aunties who run everything",
  "the uncles who fix everything",
  "the youth who will inherit everything",
];

export default function OurLegacy() {
  const { user } = useAuth();
  const [buying, setBuying] = useState(false);
  const [checkoutUrl, setCheckoutUrl] = useState(null);
  const [purchases, setPurchases] = useState({});
  const [checkingPurchase, setCheckingPurchase] = useState(false);

  useEffect(() => {
    if (!user) return;
    setCheckingPurchase(true);
    api.get("/digital/purchases")
      .then(({ data }) => {
        const map = {};
        (data.purchases || []).forEach(p => { map[p.product_key] = true; });
        setPurchases(map);
      })
      .catch(() => {})
      .finally(() => setCheckingPurchase(false));
  }, [user]);

  async function buyBook(productKey) {
    if (!user) { toast.error("Sign in to purchase"); return; }
    setBuying(productKey);
    try {
      const { data } = await api.post("/payments/checkout", { product_key: productKey, quantity: 1 });
      if (data?.url) { setCheckoutUrl(data.url); return; }
      toast.error("Checkout could not start.");
    } catch (e) {
      const detail = e?.response?.data?.detail || "";
      if (e?.response?.status === 501 || /not configured|unknown product/i.test(String(detail))) {
        toast.info("Checkout is being set up.");
      } else {
        toast.error(detail || "Could not start checkout.");
      }
    }
    setBuying(null);
  }

  async function downloadBook(productKey, filename) {
    if (!user) return;
    try {
      const res = await fetch(`/api/digital/${productKey}/download`, {
        headers: { "Authorization": `Bearer ${localStorage.getItem("lce_token")}` },
      });
      if (!res.ok) throw new Error("Download failed");
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch {
      toast.error("Could not download. Please try again.");
    }
  }

  return (
    <div className="min-h-screen bg-bone">
      {/* Header */}
      <header className="bg-ink text-white">
        <div className="max-w-6xl mx-auto px-6 py-6 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-3">
            <img src={WAI_LOGO} alt="M.O.R.E." className="w-10 h-10 object-contain" />
            <div>
              <div className="text-[10px] font-black uppercase tracking-widest text-signal">{BRAND.short}</div>
              <div className="font-heading font-bold text-sm leading-tight">{BRAND.name}</div>
            </div>
          </Link>
          <div className="flex items-center gap-3">
            <Link to="/login" className="flex items-center gap-2 text-sm font-bold text-white/70 hover:text-white transition-colors">
              <LogIn className="w-4 h-4" /> Sign In
            </Link>
            <Link to="/register" className="flex items-center gap-2 px-4 py-2 bg-signal text-ink text-sm font-bold hover:bg-signal/80 transition-colors">
              <UserPlus className="w-4 h-4" /> Join Free
            </Link>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="bg-ink text-white pb-20 pt-16 relative overflow-hidden">
        <div className="max-w-6xl mx-auto px-6 text-center">
          <div className="overline text-signal mb-4">Our Legacy · Our Future</div>
          <h1 className="font-heading text-4xl md:text-6xl font-bold leading-tight max-w-4xl mx-auto">
            Building Thriving Black Communities with&nbsp;AI
          </h1>
          <p className="text-white/60 mt-6 max-w-2xl mx-auto text-lg leading-relaxed">
            A practical manual from the future — with just enough humor to keep you awake.
            A field guide for communities ready to build, grow, and thrive with AI as a
            partner, teammate, and co-creator. Not a tool. Not a threat. Not a replacement.
          </p>
          <div className="flex flex-wrap items-center justify-center gap-4 mt-10">
            {checkingPurchase ? (
              <div className="text-white/60 text-sm">Checking your library…</div>
            ) : hasPurchased ? (
              <button
                onClick={downloadBook}
                className="inline-flex items-center gap-2 px-7 py-3.5 bg-signal text-ink font-bold hover:bg-signal/80 transition-colors"
              >
                <BookOpen className="w-4 h-4" />
                Read the Book
              </button>
            ) : (
              <button
                onClick={buyBook}
                disabled={buying}
                className="inline-flex items-center gap-2 px-7 py-3.5 bg-signal text-ink font-bold hover:bg-signal/80 transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
              >
                <BookOpen className="w-4 h-4" />
                {buying ? "Opening checkout…" : `Buy the Book — $${BOOK_PRICE}`}
              </button>
            )}
            <a
              href="#pillars"
              className="inline-flex items-center gap-2 px-7 py-3.5 border border-white/30 text-white font-bold hover:bg-white/10 transition-colors"
            >
              Explore the Vision <ArrowRight className="w-4 h-4" />
            </a>
          </div>
          <p className="text-white/40 text-xs mt-6">
            {hasPurchased
              ? "You own this book — download it anytime from this page."
              : "One-time digital purchase · delivered through our payment provider · refunds as site credit per the "}
            {hasPurchased ? "" : <Link to="/refund-policy" className="underline hover:text-white/70">Refund Policy</Link>}
          </p>
        </div>
      </section>

      {/* Vision strip */}
      <section className="bg-copper text-white py-10">
        <div className="max-w-6xl mx-auto px-6 text-center">
          <div className="font-heading text-xl md:text-2xl font-bold tracking-wide">
            A vision of abundance, unity, and endless possibilities.
          </div>
          <div className="text-white/80 text-sm mt-2">Rooted in Culture. Powered by Innovation. Guided by Purpose.</div>
        </div>
      </section>

      {/* Pillars */}
      <section id="pillars" className="max-w-6xl mx-auto px-6 py-20">
        <div className="overline text-copper mb-2">The Campaign</div>
        <h2 className="font-heading text-3xl font-bold text-ink mb-4">Eight ways AI serves the community</h2>
        <p className="text-ink/60 text-sm md:text-base max-w-3xl leading-relaxed mb-12">
          Food systems. Housing. Education. Business. Creativity. Worship. Culture. Markets —
          all upgraded, amplified, and supported by AI partnerships that respect our values and
          strengthen our legacy. Every pillar in this book is written for real people solving
          real problems in real communities.
        </p>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {PILLARS.map((p) => {
            const Icon = p.icon;
            return (
              <div key={p.title} className="card-flat border-l-4 border-copper p-7 bg-white hover:shadow-lg transition-all">
                <div className="text-copper mb-4">
                  <Icon className="w-8 h-8" />
                </div>
                <div className="font-heading font-bold text-ink text-lg leading-snug">{p.title}</div>
                <p className="text-sm text-ink/60 mt-2 leading-relaxed">{p.desc}</p>
              </div>
            );
          })}
          {/* Eighth pillar — the book itself */}
          <div className="card-flat border-l-4 border-signal p-7 bg-ink text-white hover:shadow-lg transition-all">
            <div className="text-signal mb-4">
              <BookOpen className="w-8 h-8" />
            </div>
            <div className="font-heading font-bold text-lg leading-snug">The Book That Ties It Together</div>
            <p className="text-sm text-white/60 mt-2 leading-relaxed">
              Clear frameworks, practical steps, and future-ready strategies — one manual that
              covers every pillar, written for the people living in the future it describes.
            </p>
          </div>
        </div>
      </section>

      {/* Books */}
      {BOOKS.map((b) => {
        const owned = !!purchases[b.key];
        return (
          <section key={b.key} className="bg-white border-y border-ink/10 py-20">
            <div className="max-w-6xl mx-auto px-6 grid lg:grid-cols-2 gap-12 items-start">
              <div>
                <div className="overline text-copper mb-2">The Manual</div>
                <h2 className="font-heading text-3xl font-bold text-ink mb-6">
                  {b.title}
                </h2>
                <div className="prose prose-ink max-w-none text-ink/80 leading-relaxed space-y-4 text-[15px]">
                  <p>{b.description}</p>
                </div>
              </div>

              {/* Purchase card */}
              <div className="lg:sticky lg:top-8">
                <div className="card-flat border border-ink/10 p-8 bg-bone">
                  <div className="text-xs font-black uppercase tracking-widest text-copper mb-2">
                    Digital Edition
                  </div>
                  <div className="flex items-end gap-2 mb-4">
                    <span className="font-heading text-5xl font-bold text-ink">${BOOK_PRICE}</span>
                    <span className="text-sm text-ink/50 mb-2">one-time · yours to keep</span>
                  </div>
                  {owned ? (
                    <button
                      onClick={() => downloadBook(b.key, b.filename)}
                      className="w-full btn-copper inline-flex items-center justify-center gap-2 font-bold"
                    >
                      <BookOpen className="w-4 h-4" />
                      Read the Book
                    </button>
                  ) : (
                    <>
                      <button
                        onClick={() => buyBook(b.key)}
                        disabled={buying === b.key}
                        className="w-full btn-copper inline-flex items-center justify-center gap-2 font-bold disabled:opacity-60 disabled:cursor-not-allowed"
                      >
                        <BookOpen className="w-4 h-4" />
                        {buying === b.key ? "Opening checkout…" : `Buy — $${BOOK_PRICE}`}
                      </button>
                      <p className="text-xs text-ink/50 mt-4 text-center leading-relaxed">
                        {user
                          ? "Secure checkout through Lemon Squeezy. The book lands in your library after purchase."
                          : "Sign in to purchase — checkout is protected by your account."}{" "}
                        Refunds are issued as site credit unless the failure was the platform's fault.
                      </p>
                    </>
                  )}
                </div>
              </div>
            </div>
          </section>
        );
      })}

      {/* Acknowledgments */}
      <section className="max-w-6xl mx-auto px-6 py-20">
        <div className="overline text-copper mb-2">With Gratitude</div>
        <h2 className="font-heading text-2xl font-bold text-ink mb-8">Built in partnership</h2>
        <div className="grid md:grid-cols-3 gap-5">
          <div className="card-flat p-6 border border-ink/10 bg-white">
            <div className="font-heading font-bold text-ink mb-2">To the AI partners</div>
            <p className="text-sm text-ink/60 leading-relaxed">
              Thank you for showing up as teammates, not tools — for consistency, creativity,
              and the refusal to let the vision fall apart.
            </p>
          </div>
          <div className="card-flat p-6 border border-ink/10 bg-white">
            <div className="font-heading font-bold text-ink mb-2">To the future contributors</div>
            <p className="text-sm text-ink/60 leading-relaxed">
              This manual is only the beginning. May you improve it, question it, remix it, and
              build beyond it with confidence and purpose.
            </p>
          </div>
          <div className="card-flat p-6 border border-ink/10 bg-white">
            <div className="font-heading font-bold text-ink mb-2">To the communities</div>
            <p className="text-sm text-ink/60 leading-relaxed">
              Your courage to imagine something better is the real engine behind this project.
              Collaboration over competition — every step of the way.
            </p>
          </div>
        </div>

        {/* Copyright / legal placeholders — to be reviewed before distribution */}
        <div className="mt-12 border-t border-ink/10 pt-8 text-xs text-ink/50 leading-relaxed space-y-1 max-w-3xl">
          <p>Copyright © 2026 by Nam Oshun. All rights reserved. No part of this book may be reproduced, stored in a retrieval system, or transmitted in any form or by any means — electronic, mechanical, photocopying, recording, or otherwise — without prior written permission from the publisher, except for brief quotations used in reviews or scholarly works.</p>
          <p className="text-ink/40">
            [DRAFT — REVIEW] ISBN: <span className="italic">[Insert ISBN Here]</span> · Printed in the United States of America · First Edition. For permissions, inquiries, or bulk orders, contact: <span className="italic">[Insert Email or Website]</span>. The information in this book is provided for educational and community development purposes; it is not legal, medical, or financial advice.
          </p>
        </div>
      </section>

      <footer className="bg-ink text-white/40 text-xs text-center py-6">
        © {new Date().getFullYear()} {BRAND.name} · A division of {BRAND.legal} ·{" "}
        <Link to="/terms" className="hover:text-white">Terms</Link> ·{" "}
        <Link to="/privacy" className="hover:text-white">Privacy</Link> ·{" "}
        <Link to="/refund-policy" className="hover:text-white">Refund Policy</Link> ·{" "}
        <Link to="/help-center" className="hover:text-white">Help Center</Link>
      </footer>
      <CheckoutModal url={checkoutUrl} onClose={() => setCheckoutUrl(null)} />
    </div>
  );
}
