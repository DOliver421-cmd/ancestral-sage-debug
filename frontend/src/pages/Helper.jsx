import { useEffect, useRef, useState } from "react";
import { useAuth } from "../lib/auth";
import { useNavigate } from "react-router-dom";

// Renders the actual helper UIs inline — no iframe, no external file dependency.
// /helper     → PublicHelper  (no auth required)
// /app/helper → AuthHelper    (requires WAI session)

export default function Helper({ requireAuth = false }) {
  const { user, loading } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    const fab = document.getElementById("wai-helper-fab");
    if (fab) fab.style.display = "none";
    return () => { if (fab) fab.style.display = ""; };
  }, []);

  if (loading) return (
    <div style={{ display:"flex", alignItems:"center", justifyContent:"center", height:"100vh", fontFamily:"system-ui" }}>
      Loading…
    </div>
  );

  if (requireAuth && !user) {
    navigate("/login");
    return null;
  }

  return requireAuth ? <AuthHelper user={user} /> : <PublicHelper />;
}

// ---------------------------------------------------------------------------
// Shared hook: call backend API
// ---------------------------------------------------------------------------
function useHelperAPI(requireAuth) {
  const callAPI = async (endpoint, body, showToast) => {
    try {
      const opts = {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      };
      if (requireAuth) opts.credentials = "include";
      const prefix = requireAuth ? "/api/helper/" : "/api/public/helper/";
      const r = await fetch(prefix + endpoint, opts);
      if (!r.ok) {
        if (requireAuth && r.status === 401) {
          showToast("Session expired. Please log in again.", "🔒", 3500);
          setTimeout(() => window.location.href = "/login", 2000);
          return null;
        }
        throw new Error(r.status);
      }
      return await r.json();
    } catch {
      showToast("Could not reach the helper service. Please try again.", "⚠️", 3000);
      return null;
    }
  };
  return callAPI;
}

// ---------------------------------------------------------------------------
// PUBLIC HELPER
// ---------------------------------------------------------------------------
function PublicHelper() {
  const [msgs, setMsgs] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState(null);
  const [name, setName] = useState("Friend");
  const [nameInput, setNameInput] = useState("");
  const [lang, setLang] = useState("English");
  const [lastFull, setLastFull] = useState("");
  const [isListening, setIsListening] = useState(false);
  const endRef = useRef(null);
  const recogRef = useRef(null);
  const callAPI = useHelperAPI(false);
  const navigate = useNavigate();

  const LANGS = ["English","Español","Kreyòl Ayisyen","Yorùbá","Af-Soomaali","Tagalog","Tiếng Việt"];

  const showToast = (msg, icon="ℹ️", dur=2500) => {
    setToast({ msg, icon });
    setTimeout(() => setToast(null), dur);
  };

  useEffect(() => {
    addMsg("helper", "Good to see you. I'll keep my answers short and simple. Tap \"Tell me more\" if you want more detail.");
  }, []);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior:"smooth" }); }, [msgs]);

  const addMsg = (role, text) => {
    const time = new Date().toLocaleTimeString([], { hour:"numeric", minute:"2-digit" });
    setMsgs(m => [...m, { role, text, time }]);
  };

  const send = async () => {
    if (!input.trim() || loading) return;
    const q = input.trim();
    setInput("");
    addMsg("user", q);
    setLoading(true);
    const data = await callAPI("ask", { question: q }, showToast);
    if (data?.answer || data?.reply || data?.short) {
      const short = data.short || data.answer || data.reply;
      const full = data.full || short;
      setLastFull(full);
      addMsg("helper", short);
    } else {
      addMsg("helper", "I'm having trouble reaching the service. Please try again in a moment.");
    }
    setLoading(false);
  };

  const toggleMic = () => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) { showToast("Voice not supported. Please type instead.", "🔇"); return; }
    if (isListening) { recogRef.current?.stop(); setIsListening(false); return; }
    const rec = new SR();
    rec.lang = "en-US"; rec.continuous = false; rec.interimResults = false;
    rec.onstart = () => { setIsListening(true); showToast("Listening… speak clearly.", "🎙️", 3000); };
    rec.onend = () => setIsListening(false);
    rec.onresult = e => { setInput(e.results[0][0].transcript); };
    rec.onerror = () => { setIsListening(false); showToast("Could not hear you. Try again.", "🔇"); };
    recogRef.current = rec;
    rec.start();
  };

  const cycleLang = () => {
    const i = LANGS.indexOf(lang);
    const next = LANGS[(i+1) % LANGS.length];
    setLang(next);
    showToast("I'll try to speak in " + next, "🌎", 3000);
  };

  const TOPICS = [
    ["📬","mail","Read My Mail","Taxes & posts — I'll read and explain."],
    ["💡","bills","My Bills","I'll explain what you owe and why."],
    ["💳","credit","Credit Score","I'll explain your credit in simple words."],
    ["👶","custody","Custody Help","I'll help you understand custody papers."],
    ["💊","medicines","My Medicines","Labels and instructions. Not a doctor."],
    ["🍽️","food","What Should I Eat?","Simple food guidance, not medical advice."],
    ["📅","appointments","My Appointments","I'll help you remember and prepare."],
    ["⚖️","legal","Legal Help","I'll explain legal letters and forms."],
    ["💼","employment","Employment","I'll help you understand job papers."],
    ["🎓","education","Education","I'll help with school forms."],
    ["🏠","housing","Housing","Rent, eviction, and housing letters."],
    ["🚨","emergency","Emergency","911, Poison Control, 988 — who to call."],
  ];

  const s = { // styles
    wrap: { minHeight:"100vh", background:"#f5f7fb", fontFamily:"system-ui,-apple-system,sans-serif", color:"#1f2933" },
    header: { background:"linear-gradient(135deg,#4b7cff,#7b5cff)", borderRadius:18, padding:"18px 16px", color:"#fff", margin:"12px 10px 0" },
    avatar: { width:64, height:64, borderRadius:"50%", background:"radial-gradient(circle at 30% 20%,#fde68a,#facc15 40%,#f97316 80%)", display:"flex", alignItems:"center", justifyContent:"center", fontWeight:800, fontSize:28, boxShadow:"0 0 0 4px rgba(15,23,42,.35)", flexShrink:0 },
    card: { background:"#fff", borderRadius:18, padding:"14px 12px", margin:"12px 10px 0", boxShadow:"0 10px 30px rgba(15,23,42,.12)" },
    bigBtn: (bg,color) => ({ flex:1, minWidth:110, borderRadius:999, border:"none", padding:"10px 12px", fontSize:14, fontWeight:600, background:bg, color, cursor:"pointer", display:"flex", alignItems:"center", justifyContent:"center", gap:6 }),
    pill: (primary) => ({ borderRadius:999, border:`1px solid ${primary?"#2563eb":"#d1d5db"}`, padding:"6px 10px", fontSize:12, background:"#fff", color:primary?"#1d4ed8":"#111827", cursor:"pointer", display:"inline-flex", alignItems:"center", gap:5 }),
    menuBtn: { borderRadius:14, border:"1px solid #e5e7eb", background:"#f9fafb", padding:"10px", cursor:"pointer", display:"flex", flexDirection:"column", gap:4, minHeight:70, textAlign:"left" },
    input: { flex:1, minHeight:60, maxHeight:120, resize:"vertical", borderRadius:14, border:"1px solid #d1d5db", padding:"8px 10px", fontSize:14, fontFamily:"system-ui" },
    sendBtn: { borderRadius:14, border:"none", padding:"0 14px", fontSize:14, fontWeight:600, background:"#2563eb", color:"#eff6ff", cursor:"pointer" },
    bubble: (role) => ({ background: role==="helper"?"#e0f2fe":"#e5e7eb", borderRadius:14, padding:"8px 10px", marginBottom:2 }),
    toast: { position:"fixed", bottom:16, left:"50%", transform:"translateX(-50%)", background:"#111827", color:"#f9fafb", padding:"8px 12px", borderRadius:999, fontSize:12, border:"1px solid #4b5563", zIndex:9999, display:"inline-flex", alignItems:"center", gap:6 },
  };

  return (
    <div style={s.wrap}>
      {/* HEADER */}
      <div style={s.header}>
        <div style={{ display:"flex", alignItems:"center", gap:12, marginBottom:10 }}>
          <div style={s.avatar}>H</div>
          <div>
            <div style={{ fontSize:22, fontWeight:700 }}>I am here to be your HELPER.</div>
            <div style={{ fontSize:14, lineHeight:1.4 }}>I can help you read mail, understand bills, explain legal papers — in plain, simple words.</div>
          </div>
        </div>
        <div style={{ display:"flex", flexWrap:"wrap", gap:8 }}>
          <button style={{ borderRadius:999, border:"none", padding:"10px 18px", fontSize:15, fontWeight:600, background:"#22c55e", color:"#064e3b", cursor:"pointer" }} onClick={() => showToast("Tap any big button below to get help.", "👉")}>Let's Get Started</button>
          <button style={{ borderRadius:999, border:"1px solid rgba(255,255,255,.7)", padding:"9px 14px", fontSize:13, background:"transparent", color:"#e5e7eb", cursor:"pointer" }} onClick={() => navigate("/login")}>Sign in for full access →</button>
        </div>
      </div>

      {/* MAIN CARD */}
      <div style={s.card}>
        <div style={{ marginBottom:10 }}>
          <div style={{ fontSize:18, fontWeight:700 }}>Hello, {name}!</div>
          <div style={{ fontSize:14, color:"#4b5563" }}>Tap any button below to get help.</div>
          <div style={{ display:"flex", gap:6, marginTop:6, flexWrap:"wrap" }}>
            <input value={nameInput} onChange={e=>setNameInput(e.target.value)} placeholder="Type your name…" style={{ padding:"7px 10px", borderRadius:999, border:"1px solid #d1d5db", fontSize:14, minWidth:160 }} />
            <button onClick={() => { if(nameInput.trim()){ setName(nameInput.trim()); showToast(`Nice to meet you, ${nameInput.trim()}.`,"😊"); }}} style={{ borderRadius:999, border:"none", padding:"7px 12px", fontSize:13, background:"#2563eb", color:"#eff6ff", cursor:"pointer" }}>Save my name</button>
          </div>
        </div>

        {/* ACTION BUTTONS */}
        <div style={{ display:"flex", flexWrap:"wrap", gap:8, marginBottom:8 }}>
          <button style={s.bigBtn("#2563eb","#eff6ff")} onClick={toggleMic}><span>🎙️</span>{isListening ? "Listening…" : "Speak to me"}</button>
          <button style={s.bigBtn("#facc15","#78350f")} onClick={() => showToast("Type what the document says and I'll explain it.","📷",3500)}><span>📷</span>Read this for me</button>
          <button style={s.bigBtn("#ef4444","#fee2e2")} onClick={() => { addMsg("helper","If someone asks for money right now, threatens you, or wants gift cards — that may be a scam. Real agencies never demand gift cards or wire transfers."); }}><span>🛡️</span>Is this a scam?</button>
        </div>
        <div style={{ display:"flex", flexWrap:"wrap", gap:8, marginBottom:10 }}>
          <button style={s.bigBtn("#7c3aed","#ede9fe")} onClick={cycleLang}><span>🌎</span>Language: {lang}</button>
          <button style={s.bigBtn("#e5e7eb","#111827")} onClick={() => window.print()}><span>🖨️</span>Print this</button>
        </div>

        {/* CONVERSATION */}
        <div style={{ border:"1px solid #e5e7eb", borderRadius:14, background:"#f9fafb", padding:10, maxHeight:260, overflowY:"auto", fontSize:14, marginBottom:8 }}>
          {msgs.map((m,i) => (
            <div key={i} style={{ marginBottom:8 }}>
              <div style={s.bubble(m.role)}>{m.text}</div>
              <div style={{ fontSize:11, color:"#6b7280", marginTop:2 }}>{m.role==="helper"?"Helper":name} • {m.time}</div>
            </div>
          ))}
          {loading && <div style={{ color:"#6b7280", fontStyle:"italic" }}>Thinking…</div>}
          <div ref={endRef} />
        </div>

        {/* INPUT */}
        <div style={{ display:"flex", gap:6, marginBottom:6 }}>
          <textarea value={input} onChange={e=>setInput(e.target.value)} onKeyDown={e=>{ if(e.key==="Enter"&&!e.shiftKey){e.preventDefault();send();}}} placeholder='Type here, or tap "Speak to me"…' style={s.input} />
          <button onClick={send} disabled={loading} style={s.sendBtn}>Send</button>
        </div>
        <div style={{ display:"flex", flexWrap:"wrap", gap:6, marginBottom:12 }}>
          <button style={s.pill(true)} onClick={() => { if(lastFull) addMsg("helper", lastFull); else showToast("Ask me something first.","ℹ️"); }}>➕ Tell me more</button>
          <button style={s.pill(false)} onClick={() => { setMsgs([]); addMsg("helper","You're back at the main menu. Tap any button to get help."); }}>🏠 Back to main menu</button>
        </div>

        {/* MENU GRID */}
        <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fill,minmax(180px,1fr))", gap:8 }}>
          {TOPICS.map(([icon,topic,title,desc]) => (
            <button key={topic} style={s.menuBtn} onClick={() => addMsg("helper", `You chose "${title}". ${desc} Type your question below and I'll help.`)}>
              <div style={{ display:"flex", alignItems:"center", gap:8, fontSize:15, fontWeight:600 }}><span>{icon}</span>{title}</div>
              <div style={{ fontSize:13, color:"#4b5563" }}>{desc}</div>
            </button>
          ))}
        </div>

        <div style={{ marginTop:10, fontSize:11, color:"#4b5563", textAlign:"center" }}>
          This public helper does not save your data. For saved notes and advanced tools, <button style={{ background:"none", border:"none", color:"#2563eb", cursor:"pointer", fontSize:11, padding:0 }} onClick={() => navigate("/login")}>sign in</button>.
        </div>
      </div>

      {toast && <div style={s.toast}><span>{toast.icon}</span><span>{toast.msg}</span></div>}
    </div>
  );
}

// ---------------------------------------------------------------------------
// AUTHENTICATED HELPER
// ---------------------------------------------------------------------------
function AuthHelper({ user }) {
  const [msgs, setMsgs] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState(null);
  const [lastFull, setLastFull] = useState("");
  const [context, setContext] = useState("General");
  const [activeNav, setActiveNav] = useState("home");
  const endRef = useRef(null);
  const callAPI = useHelperAPI(true);

  const showToast = (msg, icon="ℹ️", dur=2500) => {
    setToast({ msg, icon });
    setTimeout(() => setToast(null), dur);
  };

  useEffect(() => {
    addMsg("helper", "This is your private helper inside WAI‑Institute. I'll keep answers short and clear. Tap \"Tell me more\" for more detail.");
  }, []);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior:"smooth" }); }, [msgs]);

  const addMsg = (role, text) => {
    const time = new Date().toLocaleTimeString([], { hour:"numeric", minute:"2-digit" });
    setMsgs(m => [...m, { role, text, time }]);
  };

  const send = async () => {
    if (!input.trim() || loading) return;
    const q = input.trim();
    setInput("");
    addMsg("user", q);
    setLoading(true);
    const data = await callAPI("ask", { question: q, context }, showToast);
    if (data?.answer || data?.reply || data?.short) {
      const short = data.short || data.answer || data.reply;
      setLastFull(data.full || short);
      addMsg("helper", short);
    } else {
      addMsg("helper", "I'm having trouble reaching the service. Please try again.");
    }
    setLoading(false);
  };

  const saveChat = async () => {
    const transcript = msgs.map(m => `[${m.role}] ${m.text}`).join("\n\n");
    await callAPI("conversations/save", { transcript, context }, showToast);
    showToast("Chat saved.", "💾");
  };

  const TOOLS = [
    { section:"Daily tools", icon:"📅", items:[
      ["📬","read-mail","Read my mail","Upload or paste letters. I'll read and explain."],
      ["📷","scan-read","Scan & read (OCR)","Camera or files. I'll turn pictures into text."],
      ["💡","bills","My bills","I'll help you understand what you owe."],
      ["📅","appointments","Appointments","Review and prepare for upcoming visits."],
      ["📝","notes","Notes","Keep simple notes I can help you read later."],
      ["🗂️","documents","Saved documents","Documents you or staff have saved for you."],
    ]},
    { section:"Legal tools", icon:"⚖️", items:[
      ["📄","legal-draft","Draft legal form","Simple pleadings or forms. Staff must review."],
      ["✉️","letter-draft","Draft a letter","Clear, respectful letters in plain language."],
      ["📎","upload-review","Upload for review","Staff or instructors review it with you."],
      ["🛡️","scam-check","Scam check","Paste messages. I'll flag common scam signs."],
    ]},
    { section:"Health & life", icon:"💊", items:[
      ["💊","medicines","My medicines","Read labels and instructions. Not a doctor."],
      ["🍽️","food","Food & nutrition","Simple food ideas. Not medical advice."],
      ["🏠","housing","Housing","Rent, lease, and housing letters."],
      ["💼","employment","Employment & school","Job offers, school forms, training papers."],
    ]},
    { section:"Support & safety", icon:"🧑‍🤝‍🧑", items:[
      ["📇","trusted-contacts","Trusted contacts","People you trust to help you."],
      ["❤️","caregiver-mode","Caregiver mode","A caregiver works with you in this space."],
      ["💬","saved-conversations","Saved conversations","Review past helper chats."],
      ["🚨","emergency","Emergency info","911, 988, Poison Control reminders."],
    ]},
  ];

  const NAVS = ["home","tasks","messages","profile"];

  const s = {
    wrap: { minHeight:"100vh", background:"#f5f7fb", fontFamily:"system-ui,-apple-system,sans-serif", color:"#1f2933" },
    topBar: { display:"flex", alignItems:"center", justifyContent:"space-between", gap:10, padding:"10px 12px 0", flexWrap:"wrap" },
    avatar: { width:52, height:52, borderRadius:"50%", background:"radial-gradient(circle at 30% 20%,#fde68a,#facc15 40%,#f97316 80%)", display:"flex", alignItems:"center", justifyContent:"center", fontWeight:800, fontSize:24, boxShadow:"0 0 0 3px rgba(15,23,42,.35)", flexShrink:0 },
    navPill: (active) => ({ borderRadius:999, padding:"6px 12px", fontSize:13, border:`1px solid ${active?"#2563eb":"#d1d5db"}`, background:active?"#2563eb":"#fff", color:active?"#eff6ff":"#111827", cursor:"pointer", fontWeight:active?600:400 }),
    header: { background:"linear-gradient(135deg,#4b7cff,#7b5cff)", borderRadius:18, padding:"16px 14px", color:"#fff", margin:"10px 10px 12px", boxShadow:"0 10px 30px rgba(15,23,42,.18)" },
    bigBtn: (bg,color) => ({ flex:1, minWidth:110, borderRadius:999, border:"none", padding:"9px 12px", fontSize:14, fontWeight:600, background:bg, color, cursor:"pointer", display:"flex", alignItems:"center", justifyContent:"center", gap:6 }),
    card: { background:"#fff", borderRadius:18, padding:"14px 12px", boxShadow:"0 10px 30px rgba(15,23,42,.12)" },
    toolBtn: { borderRadius:14, border:"1px solid #e5e7eb", background:"#f9fafb", padding:"9px", cursor:"pointer", display:"flex", flexDirection:"column", gap:4, minHeight:70, textAlign:"left", width:"100%" },
    bubble: (role) => ({ background:role==="helper"?"#e0f2fe":"#e5e7eb", borderRadius:14, padding:"7px 9px", marginBottom:2 }),
    pill: (variant) => ({ borderRadius:999, border:`1px solid ${variant==="primary"?"#2563eb":variant==="danger"?"#ef4444":"#d1d5db"}`, padding:"6px 10px", fontSize:12, background:"#fff", color:variant==="primary"?"#1d4ed8":variant==="danger"?"#b91c1c":"#111827", cursor:"pointer", display:"inline-flex", alignItems:"center", gap:5 }),
    sendBtn: { borderRadius:14, border:"none", padding:"0 14px", fontSize:14, fontWeight:600, background:"#2563eb", color:"#eff6ff", cursor:"pointer" },
    toast: { position:"fixed", bottom:16, left:"50%", transform:"translateX(-50%)", background:"#111827", color:"#f9fafb", padding:"8px 12px", borderRadius:999, fontSize:12, border:"1px solid #4b5563", zIndex:9999, display:"inline-flex", alignItems:"center", gap:6 },
  };

  return (
    <div style={s.wrap}>
      {/* TOP BAR */}
      <div style={s.topBar}>
        <div style={{ display:"flex", alignItems:"center", gap:10 }}>
          <div style={s.avatar}>H</div>
          <div>
            <div style={{ fontSize:18, fontWeight:700 }}>Helper Workspace</div>
            <div style={{ fontSize:13, color:"#4b5563" }}>Welcome back. I'll keep things simple.</div>
          </div>
        </div>
        <div style={{ display:"flex", alignItems:"center", gap:8, flexWrap:"wrap" }}>
          <span style={{ borderRadius:999, padding:"5px 10px", fontSize:12, border:"1px solid #d1d5db", background:"#fff" }}>Role: {user?.role || "Student"}</span>
          <span style={{ borderRadius:999, padding:"6px 10px", fontSize:13, border:"1px solid #d1d5db", background:"#fff" }}>👤 {user?.name || user?.email || "Signed in"}</span>
        </div>
      </div>

      {/* NAV */}
      <div style={{ display:"flex", gap:6, padding:"8px 12px", flexWrap:"wrap" }}>
        {NAVS.map(n => <button key={n} style={s.navPill(activeNav===n)} onClick={() => setActiveNav(n)}>{n.charAt(0).toUpperCase()+n.slice(1)}</button>)}
      </div>

      {/* HEADER CARD */}
      <div style={s.header}>
        <div style={{ fontSize:20, fontWeight:700, marginBottom:4 }}>I am here to be your HELPER inside WAI‑Institute.</div>
        <div style={{ fontSize:14, lineHeight:1.4, marginBottom:12 }}>Your private workspace — read documents, draft letters, manage appointments, stay safe from scams.</div>
        <div style={{ display:"flex", flexWrap:"wrap", gap:8 }}>
          <button style={s.bigBtn("#22c55e","#064e3b")} onClick={() => addMsg("helper","Let's focus on today. What's the most important thing you need help with right now?")}>🎯 Focus on today's tasks</button>
          <button style={s.bigBtn("rgba(255,255,255,.15)","#e5e7eb")} onClick={() => { setContext("Scan & read"); addMsg("helper","You chose Scan & read. In the full system you can upload a photo. For now, paste or type what the document says and I'll explain it."); }}>📷 Quick scan & read</button>
          <button style={s.bigBtn("#ef4444","#fee2e2")} onClick={() => { setContext("Scam check"); addMsg("helper","Paste the message or letter below and I'll check it for common scam signs."); }}>🛡️ Scam check</button>
        </div>
      </div>

      {/* MAIN LAYOUT */}
      <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fit,minmax(320px,1fr))", gap:12, padding:"0 10px 24px" }}>
        {/* TOOLS */}
        <div style={s.card}>
          <div style={{ fontSize:15, fontWeight:700, marginBottom:10 }}>🧰 Your tools <span style={{ fontSize:12, color:"#4b5563", fontWeight:400 }}>— tap any tool to start</span></div>
          {TOOLS.map(({ section, icon, items }) => (
            <div key={section} style={{ marginBottom:12 }}>
              <div style={{ fontSize:14, fontWeight:700, marginBottom:6 }}>{icon} {section}</div>
              <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fill,minmax(150px,1fr))", gap:6 }}>
                {items.map(([ico,tool,title,desc]) => (
                  <button key={tool} style={s.toolBtn} onClick={() => { setContext(title); addMsg("helper", `You chose "${title}". ${desc} What would you like to do?`); }}>
                    <div style={{ display:"flex", alignItems:"center", gap:6, fontSize:14, fontWeight:600 }}><span>{ico}</span>{title}</div>
                    <div style={{ fontSize:12, color:"#4b5563" }}>{desc}</div>
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>

        {/* CONVERSATION */}
        <div style={s.card}>
          <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between", marginBottom:8 }}>
            <div style={{ fontSize:15, fontWeight:700 }}>💬 Conversation & guidance</div>
            <span style={{ fontSize:11, border:"1px solid #d1d5db", borderRadius:999, padding:"3px 8px", color:"#111827" }}>Context: {context}</span>
          </div>

          <div style={{ border:"1px solid #e5e7eb", borderRadius:14, background:"#f9fafb", padding:9, maxHeight:320, overflowY:"auto", fontSize:14, marginBottom:8 }}>
            {msgs.map((m,i) => (
              <div key={i} style={{ marginBottom:8 }}>
                <div style={s.bubble(m.role)}>{m.text}</div>
                <div style={{ fontSize:11, color:"#6b7280", marginTop:2 }}>{m.role==="helper"?"Helper":"You"} • {m.time}</div>
              </div>
            ))}
            {loading && <div style={{ color:"#6b7280", fontStyle:"italic" }}>Thinking…</div>}
            <div ref={endRef} />
          </div>

          <div style={{ display:"flex", gap:6, marginBottom:6 }}>
            <textarea value={input} onChange={e=>setInput(e.target.value)} onKeyDown={e=>{ if(e.key==="Enter"&&!e.shiftKey){e.preventDefault();send();}}} placeholder='Type here, or tap "Speak to me"…' style={{ flex:1, minHeight:60, maxHeight:120, resize:"vertical", borderRadius:14, border:"1px solid #d1d5db", padding:"8px 10px", fontSize:14, fontFamily:"system-ui" }} />
            <button onClick={send} disabled={loading} style={s.sendBtn}>Send</button>
          </div>

          <div style={{ display:"flex", flexWrap:"wrap", gap:6 }}>
            <button style={s.pill("primary")} onClick={() => { if(lastFull) addMsg("helper",lastFull); }}>➕ Tell me more</button>
            <button style={s.pill("none")} onClick={() => { setMsgs([]); addMsg("helper","Chat cleared. Tap any tool to start."); setContext("General"); }}>🧹 Clear this chat</button>
            <button style={s.pill("none")} onClick={saveChat}>💾 Save this chat</button>
            <button style={s.pill("danger")} onClick={() => { setContext("General"); addMsg("helper","Back to home tools. What do you need help with?"); }}>🏠 Back to home tools</button>
          </div>

          <div style={{ marginTop:10, fontSize:11, color:"#4b5563", textAlign:"center" }}>
            This authenticated helper is part of WAI‑Institute. Actions may be logged for safety and training. Not a lawyer, doctor, or emergency service.
          </div>
        </div>
      </div>

      {toast && <div style={s.toast}><span>{toast.icon}</span><span>{toast.msg}</span></div>}
    </div>
  );
}
