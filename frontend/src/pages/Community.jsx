import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import PublicNav from "../components/PublicNav";
import BackButton from "../components/BackButton";
import { api, BACKEND_URL } from "../lib/api";
import { HandHelping, Users, Sparkles, MessageSquare, Scale, HelpCircle, Clock, BookOpen, ArrowRight, Loader2 } from "lucide-react";

const CAT_ICONS = { skill_offer: BookOpen, need: HandHelping, community: Users, story: Sparkles };
const CAT_COLORS = { skill_offer: "bg-emerald-50 text-emerald-700", need: "bg-amber-50 text-amber-700", community: "bg-blue-50 text-blue-700", story: "bg-purple-50 text-purple-700" };

// Public community page — shows the real exchange (posts, needs, chat rooms)
// and funnels into registration for full access.
export default function Community() {
  const [posts, setPosts] = useState([]);
  const [needs, setNeeds] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.allSettled([
      fetch(`${BACKEND_URL}/api/more/posts?limit=6`).then(r => r.ok ? r.json() : []),
      fetch(`${BACKEND_URL}/api/more/needs?limit=6`).then(r => r.ok ? r.json() : []),
    ]).then(([pR, nR]) => {
      if (pR.status === "fulfilled") setPosts(Array.isArray(pR.value) ? pR.value : pR.value?.posts || []);
      if (nR.status === "fulfilled") setNeeds(Array.isArray(nR.value) ? nR.value : nR.value?.needs || []);
    }).finally(() => setLoading(false));
  }, []);

  return (
    <div className="min-h-screen bg-bone">
      <PublicNav />
      <div className="max-w-5xl mx-auto px-6 py-10">
        <BackButton to="/" />
        <div className="mt-6 text-center">
          <div className="overline" style={{ color: "var(--wai-purple)" }}>Community</div>
          <h1 className="font-heading text-4xl font-bold text-ink mt-2">Members are partners, not customers.</h1>
          <p className="text-ink/60 mt-3 max-w-2xl mx-auto">
            A festival of mutual aid, learning, and creation. Post a need, offer a skill, earn your way up — together.
          </p>
        </div>

        {/* Quick actions */}
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 mt-8">
          {[
            { to: "/more", icon: HandHelping, label: "Exchange", desc: "Skills & mutual aid", color: "var(--wai-purple)" },
            { to: "/more/chat/general", icon: MessageSquare, label: "Community Chat", desc: "5 rooms, real-time", color: "var(--wai-gold)" },
            { to: "/more/litigation", icon: Scale, label: "Legal Help", desc: "Know your rights", color: "var(--wai-gold)" },
            { to: "/helper", icon: HelpCircle, label: "Helper AI", desc: "Free guidance", color: "var(--wai-purple)" },
          ].map((a) => (
            <Link key={a.to} to={a.to} className="card-flat p-5 group hover:shadow-md transition-all">
              <a.icon className="w-6 h-6" style={{ color: a.color }} />
              <div className="font-heading font-bold mt-2 text-sm text-ink group-hover:text-copper transition-colors">{a.label}</div>
              <div className="text-xs text-ink/50 mt-0.5">{a.desc}</div>
            </Link>
          ))}
        </div>

        {/* Live community posts preview */}
        {!loading && (posts.length > 0 || needs.length > 0) && (
          <div className="mt-10">
            <div className="flex items-center justify-between mb-4">
              <div className="overline text-copper">Live from the Exchange</div>
              <Link to="/more" className="text-xs font-bold text-copper hover:underline flex items-center gap-1">See all <ArrowRight className="w-3 h-3" /></Link>
            </div>
            <div className="grid md:grid-cols-2 gap-4">
              {posts.slice(0, 3).map((p) => {
                const Icon = CAT_ICONS[p.category] || Users;
                const colorClass = CAT_COLORS[p.category] || "bg-gray-50 text-gray-700";
                return (
                  <div key={p.id || p.post_id} className="bg-white rounded-xl border border-ink/10 p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${colorClass}`}><Icon className="w-3 h-3 inline mr-1" />{p.category?.replace("_", " ")}</span>
                      <span className="text-[10px] text-ink/30 flex items-center gap-1"><Clock className="w-3 h-3" />{p.author_name || "Member"}</span>
                    </div>
                    <p className="text-sm text-ink line-clamp-2">{p.content}</p>
                  </div>
                );
              })}
              {needs.slice(0, 3).map((n) => (
                <div key={n.id || n.need_id} className="bg-white rounded-xl border border-ink/10 p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-50 text-amber-700"><HandHelping className="w-3 h-3 inline mr-1" />need</span>
                    <span className="text-[10px] text-ink/30 flex items-center gap-1"><Clock className="w-3 h-3" />{n.author_name || "Member"}</span>
                  </div>
                  <p className="text-sm text-ink line-clamp-2">{n.content}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {loading && (
          <div className="flex items-center justify-center py-12 text-ink/30">
            <Loader2 className="w-5 h-5 animate-spin mr-2" /> Loading community…
          </div>
        )}

        {/* Chat rooms preview */}
        <div className="mt-10">
          <div className="overline text-copper">Community Chat Rooms</div>
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 mt-4">
            {[
              { id: "general", label: "General", desc: "Open conversation" },
              { id: "skills", label: "Skills Exchange", desc: "Offer or request skills" },
              { id: "needs", label: "Help Needed", desc: "Immediate support" },
              { id: "elders", label: "Elder Support", desc: "Resources for elders" },
              { id: "youth", label: "Youth Space", desc: "Youth-safe space" },
            ].map((r) => (
              <Link key={r.id} to="/register" className="bg-white rounded-xl border border-ink/10 p-4 hover:shadow-md transition-all group">
                <MessageSquare className="w-5 h-5 text-copper mb-2" />
                <div className="font-heading font-bold text-sm text-ink group-hover:text-copper transition-colors">{r.label}</div>
                <div className="text-[11px] text-ink/50 mt-0.5">{r.desc}</div>
              </Link>
            ))}
          </div>
        </div>

        {/* CTA */}
        <div className="text-center mt-10 flex gap-3 justify-center flex-wrap">
          <Link to="/register" className="btn-copper text-sm">Join Free — Start Exchanging</Link>
          <Link to="/more" className="btn-primary text-sm">Browse the Exchange</Link>
        </div>
      </div>
    </div>
  );
}
