import { useState, useEffect, useCallback } from "react";
import { Link, useNavigate } from "react-router-dom";
import AppShell from "../components/AppShell";
import { useAuth } from "../lib/auth";
import { api } from "../lib/api";
import {
  HandHelping, MessageSquare, Scale, HelpCircle, Shield, Flag,
  Trash2, PlusCircle, BookOpen, Heart, Users, Clock, Loader2,
  RefreshCw, Layers, Eye, X, Zap, ChevronRight, Star,
} from "lucide-react";
import { toast } from "sonner";
import FlagModal from "../components/FlagModal";

const ROLE_CONFIG = {
  student:        { label: "Community Member",    color: "#22d3ee", features: ["browse","post","need","chat","legal","helper"] },
  instructor:     { label: "Instructor",           color: "#f59e0b", features: ["browse","post","need","chat","legal","helper","flag_view"] },
  admin:          { label: "Administrator",        color: "#f97316", features: ["browse","post","need","chat","legal","helper","flag_view","flag_manage","purge"] },
  executive_admin:{ label: "Executive Director",  color: "#ef4444", features: ["browse","post","need","chat","legal","helper","flag_view","flag_manage","purge","sage_council"] },
};

const CAT = {
  skill_offer: { label:"Skill Offer", icon:BookOpen,    bg:"bg-emerald-500",  pill:"bg-emerald-50 text-emerald-700 border-emerald-200" },
  need:        { label:"Need",        icon:HandHelping, bg:"bg-amber-500",    pill:"bg-amber-50 text-amber-700 border-amber-200" },
  community:   { label:"Community",  icon:Users,       bg:"bg-blue-500",     pill:"bg-blue-50 text-blue-700 border-blue-200" },
  story:       { label:"Story",      icon:Heart,       bg:"bg-purple-500",   pill:"bg-purple-50 text-purple-700 border-purple-200" },
};

// ── Quick action tile ─────────────────────────────────────────────────────────
function ActionTile({ icon: Icon, label, sub, color, onClick, to }) {
  const cls = "flex flex-col gap-3 p-5 rounded-2xl border-2 border-transparent hover:border-amber-300 hover:shadow-lg cursor-pointer transition-all group text-left bg-white";
  const inner = (
    <>
      <div className="w-11 h-11 rounded-xl flex items-center justify-center" style={{ background: color + "20" }}>
        <Icon className="w-5 h-5" style={{ color }} />
      </div>
      <div>
        <div className="font-heading font-extrabold text-sm text-ink group-hover:text-amber-600 transition-colors">{label}</div>
        <div className="text-xs text-ink/50 mt-0.5">{sub}</div>
      </div>
    </>
  );
  return to
    ? <Link to={to} className={cls}>{inner}</Link>
    : <button onClick={onClick} className={cls}>{inner}</button>;
}

// ── Post card ─────────────────────────────────────────────────────────────────
function PostCard({ post, onFlag }) {
  const cfg = CAT[post.category] || CAT.community;
  const Icon = cfg.icon;
  const daysLeft = Math.max(0, Math.ceil((new Date(post.expires_at) - Date.now()) / 86400000));
  return (
    <div className="bg-white rounded-2xl shadow-sm border-2 border-transparent hover:border-amber-300 hover:shadow-md transition-all overflow-hidden group">
      <div className={`h-1.5 ${cfg.bg}`} />
      <div className="p-5">
        <div className="flex items-start justify-between gap-2 mb-3">
          <span className={`inline-flex items-center gap-1.5 text-xs font-bold px-3 py-1 rounded-full border ${cfg.pill}`}>
            <Icon className="w-3 h-3" />{cfg.label}
          </span>
          <span className="text-xs text-ink/30 flex items-center gap-1"><Clock className="w-3 h-3" />{daysLeft}d</span>
        </div>
        <p className="text-sm text-ink/85 leading-relaxed whitespace-pre-wrap font-medium">{post.content}</p>
        <div className="flex items-center justify-between mt-4 pt-3 border-t border-ink/5">
          <span className="text-xs font-semibold text-ink/50">{post.author_name}</span>
          <button onClick={() => onFlag(post.id, "post")}
            className="flex items-center gap-1 text-xs text-ink/20 hover:text-red-500 transition-colors opacity-0 group-hover:opacity-100">
            <Flag className="w-3 h-3" /> Flag
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Oliver banner ─────────────────────────────────────────────────────────────
function OliverBanner({ message, onDismiss }) {
  if (!message) return null;
  return (
    <div className="flex items-start gap-3 bg-amber-50 border border-amber-300 rounded-xl p-4 mb-4">
      <Shield className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
      <p className="flex-1 text-sm text-amber-800"><span className="font-bold">Oliver Guardian: </span>{message}</p>
      <button onClick={onDismiss} className="text-amber-500 text-xs font-bold">✕</button>
    </div>
  );
}

// ── New Post Modal ────────────────────────────────────────────────────────────
function NewPostModal({ onClose, onSuccess }) {
  const [content, setContent] = useState("");
  const [category, setCategory] = useState("community");
  const [loading, setLoading] = useState(false);
  const [oliver, setOliver] = useState(null);
  const cats = [
    { k:"skill_offer", emoji:"🛠️", label:"Skill Offer", sub:"I can teach or help with…" },
    { k:"need",        emoji:"🙏", label:"Need",        sub:"I need help with…" },
    { k:"community",   emoji:"🤝", label:"Community",   sub:"General post" },
    { k:"story",       emoji:"✨", label:"Story",       sub:"Share a win or story" },
  ];
  const submit = async () => {
    if (!content.trim()) return;
    setLoading(true); setOliver(null);
    try {
      const r = await api.post("/more/post", { content: content.trim(), category });
      if (r.data.oliver_response) setOliver(r.data.oliver_response);
      else { toast.success("Posted!"); onSuccess(); onClose(); }
    } catch (err) { const msg = err?.response?.data?.detail||"Could not post"; toast.error(msg); setOliver(msg); }
    finally { setLoading(false); }
  };
  return (
    <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4 backdrop-blur-sm">
      <div className="bg-white w-full max-w-lg rounded-2xl shadow-2xl overflow-hidden">
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 p-5 text-white flex items-center justify-between">
          <div className="font-heading font-extrabold text-lg">Share with the Community</div>
          <button onClick={onClose}><X className="w-5 h-5 text-white/60 hover:text-white" /></button>
        </div>
        <div className="p-6 space-y-4">
          {oliver && <OliverBanner message={oliver} onDismiss={() => setOliver(null)} />}
          <div className="grid grid-cols-2 gap-2">
            {cats.map(c => (
              <button key={c.k} onClick={() => setCategory(c.k)}
                className={`rounded-xl p-3 border-2 text-left transition-all ${category===c.k?"border-blue-500 bg-blue-50":"border-ink/10 hover:border-ink/30"}`}>
                <div className="text-xl mb-1">{c.emoji}</div>
                <div className="font-bold text-sm">{c.label}</div>
                <div className="text-xs text-ink/50">{c.sub}</div>
              </button>
            ))}
          </div>
          <textarea value={content} onChange={e=>setContent(e.target.value)} maxLength={2000} rows={4}
            placeholder="Share skills, support, stories — no money, no personal info."
            className="w-full border-2 border-ink/10 focus:border-blue-400 rounded-xl px-4 py-3 text-sm resize-none outline-none transition-colors" />
          <p className="text-xs text-ink/40 italic text-center">Reviewed by Oliver Guardian · Auto-deletes in 30 days</p>
        </div>
        <div className="px-6 pb-6 flex gap-3">
          <button onClick={onClose} className="flex-1 py-3 border-2 border-ink/10 rounded-xl font-bold text-sm hover:bg-ink/5">Cancel</button>
          <button onClick={submit} disabled={loading||!content.trim()}
            className="flex-1 py-3 bg-amber-500 hover:bg-amber-400 text-ink font-bold rounded-xl text-sm flex items-center justify-center gap-2 disabled:opacity-50 transition-colors">
            {loading?<Loader2 className="w-4 h-4 animate-spin"/>:<Zap className="w-4 h-4"/>} Post It
          </button>
        </div>
      </div>
    </div>
  );
}

// ── New Need Modal ────────────────────────────────────────────────────────────
function NewNeedModal({ onClose, onSuccess }) {
  const [title,setTitle]=useState(""); const [desc,setDesc]=useState(""); const [category,setCategory]=useState("general"); const [loading,setLoading]=useState(false);
  const CATS=["general","transportation","household","meals","companionship","tutoring","mentorship","other"];
  const submit=async()=>{
    if(!title.trim()||!desc.trim())return; setLoading(true);
    try{await api.post("/more/need",{title:title.trim(),description:desc.trim(),category});toast.success("Need posted!");onSuccess();onClose();}
    catch(err){toast.error(err?.response?.data?.detail||"Could not post");}
    finally{setLoading(false);}
  };
  return(
    <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4 backdrop-blur-sm">
      <div className="bg-white w-full max-w-lg rounded-2xl shadow-2xl overflow-hidden">
        <div className="bg-gradient-to-r from-amber-500 to-orange-500 p-5 text-white flex items-center justify-between">
          <div><div className="font-heading font-extrabold text-lg">Post a Need</div><div className="text-white/80 text-sm">Someone is ready to help</div></div>
          <button onClick={onClose}><X className="w-5 h-5 text-white/60 hover:text-white"/></button>
        </div>
        <div className="p-6 space-y-3">
          <input value={title} onChange={e=>setTitle(e.target.value)} maxLength={120} placeholder="What do you need? (brief title)"
            className="w-full border-2 border-ink/10 focus:border-amber-400 rounded-xl px-4 py-3 text-sm outline-none transition-colors font-medium"/>
          <textarea value={desc} onChange={e=>setDesc(e.target.value)} maxLength={1000} rows={4} placeholder="Describe your need — no money, no personal info"
            className="w-full border-2 border-ink/10 focus:border-amber-400 rounded-xl px-4 py-3 text-sm resize-none outline-none transition-colors"/>
          <select value={category} onChange={e=>setCategory(e.target.value)}
            className="w-full border-2 border-ink/10 focus:border-amber-400 rounded-xl px-4 py-3 text-sm outline-none transition-colors bg-white">
            {CATS.map(c=><option key={c} value={c}>{c.charAt(0).toUpperCase()+c.slice(1)}</option>)}
          </select>
        </div>
        <div className="px-6 pb-6 flex gap-3">
          <button onClick={onClose} className="flex-1 py-3 border-2 border-ink/10 rounded-xl font-bold text-sm hover:bg-ink/5">Cancel</button>
          <button onClick={submit} disabled={loading||!title.trim()||!desc.trim()}
            className="flex-1 py-3 bg-amber-500 hover:bg-amber-400 text-ink font-bold rounded-xl text-sm flex items-center justify-center gap-2 disabled:opacity-50 transition-colors">
            {loading?<Loader2 className="w-4 h-4 animate-spin"/>:<HandHelping className="w-4 h-4"/>} Post My Need
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Admin Panel ───────────────────────────────────────────────────────────────
function AdminPanel({ hasFeature }) {
  const [flags,setFlags]=useState([]); const [flagTotal,setFlagTotal]=useState(0); const [purging,setPurging]=useState(false); const [loading,setLoading]=useState(false);
  const loadFlags=useCallback(async()=>{
    if(!hasFeature("flag_view"))return; setLoading(true);
    try{const r=await api.get("/more/admin/flags");setFlags(r.data.flags||[]);setFlagTotal(r.data.total||0);}
    catch{toast.error("Could not load flags");}finally{setLoading(false);}
  },[hasFeature]);
  useEffect(()=>{loadFlags();},[loadFlags]);
  const purge=async()=>{
    if(!window.confirm("Run manual purge? Deletes all expired M.O.R.E. content now."))return;
    setPurging(true);
    try{const r=await api.post("/more/purge");const{posts,chats,flags:f}=r.data.purged;toast.success(`Purged: ${posts} posts · ${chats} chats · ${f} flags`);loadFlags();}
    catch{toast.error("Purge failed");}finally{setPurging(false);}
  };
  return(
    <div className="bg-ink rounded-2xl overflow-hidden mt-8">
      <div className="px-6 py-4 flex items-center justify-between border-b border-white/10">
        <div className="flex items-center gap-2 font-heading font-bold text-white"><Shield className="w-5 h-5 text-signal"/>Moderation Panel</div>
        <div className="flex gap-3">
          <button onClick={loadFlags} className="text-xs text-white/40 hover:text-white flex items-center gap-1"><RefreshCw className="w-3.5 h-3.5"/>Refresh</button>
          {hasFeature("purge")&&<button onClick={purge} disabled={purging} className="text-xs text-red-400 hover:text-red-300 flex items-center gap-1 disabled:opacity-50"><Trash2 className="w-3.5 h-3.5"/>Run Purge</button>}
        </div>
      </div>
      <div className="p-6">
        {loading?<div className="flex justify-center py-6"><Loader2 className="w-5 h-5 animate-spin text-amber-400"/></div>:
          flagTotal===0?<p className="text-sm text-white/30 text-center py-4">No pending flags — community is clean.</p>:(
            <div className="space-y-2">
              <div className="text-xs text-white/40 uppercase tracking-widest mb-3">Pending Flags ({flagTotal})</div>
              {flags.slice(0,10).map(f=>(
                <div key={f.id} className="flex items-start gap-3 p-3 rounded-xl bg-white/5">
                  <Flag className="w-4 h-4 text-red-400 shrink-0 mt-0.5"/>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium text-white capitalize">{f.target_type} flagged</div>
                    <div className="text-xs text-white/40">{f.reason}</div>
                  </div>
                  <div className="text-xs text-white/20">{new Date(f.created_at).toLocaleDateString()}</div>
                </div>
              ))}
            </div>
          )}
      </div>
    </div>
  );
}

// ── Main Hub ──────────────────────────────────────────────────────────────────
export default function MoreHub() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const role = user?.role || "student";
  const config = ROLE_CONFIG[role] || ROLE_CONFIG.student;
  const hasFeature = (f) => config.features.includes(f);

  const [tab, setTab] = useState("posts");
  const [posts, setPosts] = useState([]);
  const [needs, setNeeds] = useState([]);
  const [postsTotal, setPostsTotal] = useState(0);
  const [needsTotal, setNeedsTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [showPost, setShowPost] = useState(false);
  const [showNeed, setShowNeed] = useState(false);
  const [catFilter, setCatFilter] = useState("all");
  const [flagTarget, setFlagTarget] = useState(null);

  const loadPosts = useCallback(async () => {
    setLoading(true);
    try { const r = await api.get("/more/posts?limit=30"); setPosts(r.data.posts||[]); setPostsTotal(r.data.total||0); }
    catch { toast.error("Could not load posts"); }
    finally { setLoading(false); }
  }, []);

  const loadNeeds = useCallback(async () => {
    setLoading(true);
    try { const r = await api.get("/more/needs?limit=30"); setNeeds(r.data.needs||[]); setNeedsTotal(r.data.total||0); }
    catch { toast.error("Could not load needs"); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { if (tab === "posts") loadPosts(); else loadNeeds(); }, [tab, loadPosts, loadNeeds]);

  const handleFlag = (targetId, targetType) => {
    setFlagTarget({ targetId, targetType });
  };

  const filteredPosts = catFilter === "all" ? posts : posts.filter(p => p.category === catFilter);

  const QUICK_ACTIONS = [
    hasFeature("post")        && { icon:PlusCircle,   label:"Share",          sub:"Post a skill or story",     color:"#f59e0b", onClick:()=>setShowPost(true) },
    hasFeature("need")        && { icon:HandHelping,   label:"Post a Need",    sub:"Ask the community",         color:"#f97316", onClick:()=>setShowNeed(true) },
    hasFeature("chat")        && { icon:MessageSquare, label:"Community Chat", sub:"60-min rooms",              color:"#3b82f6", to:"/more/chat" },
    hasFeature("legal")       && { icon:Scale,         label:"Legal Aid",      sub:"Know your rights",          color:"#22d3ee", to:"/more/litigation" },
    hasFeature("helper")      && { icon:HelpCircle,    label:"Help Center AI", sub:"Bills, letters, rights",   color:"#a855f7", to:"/app/helper" },
    hasFeature("sage_council")&& { icon:Layers,        label:"Council (Sage)", sub:"AI advisor council",        color:"#22d3ee", to:"/council" },
    hasFeature("flag_view")   && { icon:Shield,        label:"Moderation",     sub:"Flags & admin tools",       color:"#ef4444", to:"/more/admin" },
                                  { icon:Eye,           label:"Public View",    sub:"See visitor experience",   color:"#6b7280", to:"/more" },
  ].filter(Boolean);

  return (
    <AppShell>
      <div className="min-h-screen" style={{ background: "linear-gradient(180deg,#0f172a 0%,#1e1b4b 220px,#f8f7f4 220px)" }}>
        <div className="max-w-6xl mx-auto px-6 py-8">

          {/* ── Hero header ─────────────────────────────────────────────────── */}
          <div className="text-white mb-8">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 rounded-full bg-amber-500/20 flex items-center justify-center">
                <HandHelping className="w-5 h-5 text-amber-400" />
              </div>
              <div>
                <div className="text-xs font-bold uppercase tracking-widest" style={{ color: config.color }}>{config.label}</div>
                <div className="font-heading font-extrabold text-2xl leading-none">M.O.R.E. Help Center</div>
              </div>
              <div className="ml-auto flex items-center gap-2 bg-white/10 rounded-full px-4 py-1.5 text-sm">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                <span className="text-white/70">{postsTotal} posts · {needsTotal} needs</span>
              </div>
            </div>
          </div>

          {/* ── Quick actions grid ───────────────────────────────────────────── */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3 mb-8">
            {QUICK_ACTIONS.map((a, i) => <ActionTile key={i} {...a} />)}
          </div>

          {/* ── Feed ─────────────────────────────────────────────────────────── */}
          <div className="bg-white rounded-2xl shadow-lg p-4 mb-5 flex flex-col sm:flex-row sm:items-center gap-4">
            <div className="flex gap-2">
              {[{ k:"posts", label:`Community (${postsTotal})` }, { k:"needs", label:`Needs (${needsTotal})` }].map(t => (
                <button key={t.k} onClick={() => setTab(t.k)}
                  className={`px-5 py-2.5 rounded-xl font-bold text-sm transition-all ${tab === t.k ? "bg-ink text-white" : "text-ink/50 hover:text-ink hover:bg-ink/5"}`}>
                  {t.label}
                </button>
              ))}
            </div>
            {tab === "posts" && (
              <div className="flex gap-2 flex-wrap sm:ml-auto">
                {[["all","All"],["skill_offer","🛠️ Skills"],["community","🤝 Community"],["story","✨ Stories"]].map(([k,label]) => (
                  <button key={k} onClick={() => setCatFilter(k)}
                    className={`px-3 py-1.5 rounded-full text-xs font-bold transition-all ${catFilter===k?"bg-amber-500 text-ink":"bg-ink/5 text-ink/60 hover:bg-ink/10"}`}>
                    {label}
                  </button>
                ))}
              </div>
            )}
            <button onClick={tab==="posts"?loadPosts:loadNeeds} className="sm:ml-auto text-ink/30 hover:text-amber-500 transition-colors p-1.5">
              <RefreshCw className="w-4 h-4"/>
            </button>
          </div>

          {loading ? (
            <div className="flex justify-center py-20">
              <div className="flex flex-col items-center gap-3">
                <Loader2 className="w-8 h-8 animate-spin text-amber-500" />
                <span className="text-ink/40 text-sm">Loading community…</span>
              </div>
            </div>
          ) : tab === "posts" ? (
            filteredPosts.length === 0 ? (
              <div className="bg-white rounded-2xl shadow p-16 text-center">
                <div className="text-5xl mb-4">🌱</div>
                <div className="font-heading text-2xl font-bold">Be the first to share</div>
                <p className="text-ink/50 mt-2">Drop a skill offer, share a win, or say hello.</p>
                <button onClick={() => setShowPost(true)}
                  className="mt-6 bg-amber-500 hover:bg-amber-400 text-ink font-bold px-8 py-3 rounded-xl transition-colors inline-flex items-center gap-2">
                  <PlusCircle className="w-4 h-4" /> Share Something
                </button>
              </div>
            ) : (
              <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {filteredPosts.map(p => <PostCard key={p.id} post={p} onFlag={handleFlag} />)}
              </div>
            )
          ) : (
            needs.length === 0 ? (
              <div className="bg-white rounded-2xl shadow p-16 text-center">
                <div className="text-5xl mb-4">🙌</div>
                <div className="font-heading text-2xl font-bold">No open needs right now</div>
                <p className="text-ink/50 mt-2">If you need something, ask. This community shows up.</p>
                <button onClick={() => setShowNeed(true)}
                  className="mt-6 bg-amber-500 hover:bg-amber-400 text-ink font-bold px-8 py-3 rounded-xl transition-colors inline-flex items-center gap-2">
                  <HandHelping className="w-4 h-4" /> Post a Need
                </button>
              </div>
            ) : (
              <div className="grid sm:grid-cols-2 gap-4">
                {needs.map(n => (
                  <div key={n.id} className="bg-white rounded-2xl shadow-sm border-2 border-transparent hover:border-amber-300 hover:shadow-md transition-all overflow-hidden group">
                    <div className="h-1.5 bg-amber-500" />
                    <div className="p-5">
                      <div className="flex items-start justify-between gap-2 mb-2">
                        <span className="inline-flex items-center gap-1.5 text-xs font-bold px-3 py-1 rounded-full bg-amber-50 text-amber-700 border border-amber-200">
                          <HandHelping className="w-3 h-3"/>Need
                        </span>
                        <span className="text-xs text-ink/30 flex items-center gap-1">
                          <Clock className="w-3 h-3"/>{Math.max(0,Math.ceil((new Date(n.expires_at)-Date.now())/86400000))}d
                        </span>
                      </div>
                      <h3 className="font-heading font-extrabold text-ink text-base mt-2">{n.title}</h3>
                      <p className="text-sm text-ink/70 leading-relaxed mt-1">{n.description}</p>
                      <div className="flex items-center justify-between mt-4 pt-3 border-t border-ink/5">
                        <span className="text-xs font-semibold text-ink/50">{n.author_name} · {n.category}</span>
                        <button onClick={() => handleFlag(n.id, "need")}
                          className="flex items-center gap-1 text-xs text-ink/20 hover:text-red-500 transition-colors opacity-0 group-hover:opacity-100">
                          <Flag className="w-3 h-3"/>
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )
          )}

          {hasFeature("flag_view") && <AdminPanel hasFeature={hasFeature} />}
        </div>
      </div>

      {showPost && <NewPostModal onClose={() => setShowPost(false)} onSuccess={() => { if (tab==="posts") loadPosts(); }} />}
      {showNeed && <NewNeedModal onClose={() => setShowNeed(false)} onSuccess={() => { if (tab==="needs") loadNeeds(); }} />}
      {flagTarget && <FlagModal targetId={flagTarget.targetId} targetType={flagTarget.targetType} onClose={() => setFlagTarget(null)} />}
    </AppShell>
  );
}
