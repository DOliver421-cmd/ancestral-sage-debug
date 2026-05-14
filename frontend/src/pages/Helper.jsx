import { useEffect, useRef, useState, useCallback } from "react";
import { useAuth } from "../lib/auth";
import { useNavigate } from "react-router-dom";

// Keep-alive: ping backend every 14 min to prevent free-tier cold start
const BACKEND = "https://ancestral-sage-backend.onrender.com";
function useKeepAlive() {
  useEffect(() => {
    const ping = () => fetch(`${BACKEND}/api/health`, { method: "GET" }).catch(() => {});
    ping(); // immediate on mount
    const id = setInterval(ping, 14 * 60 * 1000);
    return () => clearInterval(id);
  }, []);
}

export default function Helper({ requireAuth = false }) {
  const { user, loading } = useAuth();
  const navigate = useNavigate();
  useKeepAlive();

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

  if (requireAuth && !user) { navigate("/login"); return null; }
  return requireAuth ? <AuthHelper user={user} /> : <PublicHelper />;
}

// ---------------------------------------------------------------------------
// Shared API hook
// ---------------------------------------------------------------------------
function useHelperAPI(requireAuth) {
  return useCallback(async (endpoint, body, showToast) => {
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
      showToast("Could not reach the helper service. Please try again in a moment.", "⚠️", 3000);
      return null;
    }
  }, [requireAuth]);
}

// ---------------------------------------------------------------------------
// Mic hook — requests permission explicitly, auto-sends after result
// ---------------------------------------------------------------------------
function useMic({ onResult, onError }) {
  const [listening, setListening] = useState(false);
  const recogRef = useRef(null);

  const start = useCallback(async () => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) { onError("Voice input is not supported in this browser. Please use Chrome or Edge."); return; }

    // Explicitly request mic permission first
    try {
      await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch {
      onError("Microphone access was denied. Please allow mic access in your browser settings.");
      return;
    }

    const rec = new SR();
    rec.lang = "en-US";
    rec.continuous = false;
    rec.interimResults = false;
    rec.maxAlternatives = 1;

    rec.onstart = () => setListening(true);
    rec.onend = () => setListening(false);
    rec.onresult = (e) => {
      const transcript = e.results[0]?.[0]?.transcript || "";
      if (transcript.trim()) onResult(transcript.trim());
    };
    rec.onerror = (e) => {
      setListening(false);
      if (e.error === "not-allowed") onError("Microphone access denied. Please allow mic access and try again.");
      else if (e.error === "no-speech") onError("No speech detected. Please try again.");
      else onError("Microphone error: " + e.error);
    };

    recogRef.current = rec;
    rec.start();
  }, [onResult, onError]);

  const stop = useCallback(() => {
    recogRef.current?.stop();
    setListening(false);
  }, []);

  const toggle = useCallback(() => {
    if (listening) stop(); else start();
  }, [listening, start, stop]);

  return { listening, toggle };
}

// ---------------------------------------------------------------------------
// Text-to-speech hook — uses browser Web Speech API (no backend needed)
// ---------------------------------------------------------------------------
function useTTS() {
  const [speaking, setSpeaking] = useState(false);

  const speak = useCallback((text) => {
    if (!window.speechSynthesis) return;
    window.speechSynthesis.cancel();
    const utt = new SpeechSynthesisUtterance(text);
    utt.lang = "en-US";
    utt.rate = 0.95;
    utt.onstart = () => setSpeaking(true);
    utt.onend = () => setSpeaking(false);
    utt.onerror = () => setSpeaking(false);
    window.speechSynthesis.speak(utt);
  }, []);

  const stop = useCallback(() => {
    window.speechSynthesis?.cancel();
    setSpeaking(false);
  }, []);

  return { speaking, speak, stop };
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
  const [audioEnabled, setAudioEnabled] = useState(false);
  const endRef = useRef(null);
  const callAPI = useHelperAPI(false);
  const navigate = useNavigate();

  const LANGS = ["English","Espanol","Kreyol Ayisyen","Yoruba","Af-Soomaali","Tagalog","Tieng Viet"];

  const showToast = useCallback((msg, icon="info", dur=2500) => {
    setToast({ msg, icon });
    setTimeout(() => setToast(null), dur);
  }, []);

  const addMsg = useCallback((role, text) => {
    const time = new Date().toLocaleTimeString([], { hour:"numeric", minute:"2-digit" });
    setMsgs(m => [...m, { role, text, time }]);
    return text;
  }, []);

  const { speaking, speak, stop: stopSpeech } = useTTS();

  const sendText = useCallback(async (text) => {
    if (!text.trim() || loading) return;
    addMsg("user", text);
    setInput("");
    setLoading(true);
    const data = await callAPI("ask", { question: text }, showToast);
    if (data?.answer || data?.reply || data?.short) {
      const short = data.short || data.answer || data.reply;
      const full = data.full || short;
      setLastFull(full);
      addMsg("helper", short);
      if (audioEnabled) speak(short);
    } else {
      addMsg("helper", "I am having trouble reaching the service. Please try again in a moment.");
    }
    setLoading(false);
  }, [loading, callAPI, showToast, addMsg, audioEnabled, speak]);

  const { listening, toggle: toggleMic } = useMic({
    onResult: (transcript) => sendText(transcript),
    onError: (msg) => showToast(msg, "🔇", 4000),
  });

  useEffect(() => {
    addMsg("helper", "Good to see you. I will keep my answers short and simple. Tap Tell me more if you want more detail.");
  }, []);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior:"smooth" }); }, [msgs]);

  const cycleLang = () => {
    const i = LANGS.indexOf(lang);
    const next = LANGS[(i+1) % LANGS.length];
    setLang(next);
    showToast("I will try to speak in " + next, "🌎", 3000);
  };

  const TOPICS = [
    ["📬","mail","Read My Mail","Taxes and posts. I will read and explain."],
    ["💡","bills","My Bills","I will explain what you owe and why."],
    ["💳","credit","Credit Score","I will explain your credit in simple words."],
    ["👶","custody","Custody Help","I will help you understand custody papers."],
    ["💊","medicines","My Medicines","Labels and instructions. Not a doctor."],
    ["🍽️","food","What Should I Eat?","Simple food guidance, not medical advice."],
    ["📅","appointments","My Appointments","I will help you remember and prepare."],
    ["⚖️","legal","Legal Help","I will explain legal letters and forms."],
    ["💼","employment","Employment","I will help you understand job papers."],
    ["🎓","education","Education","I will help with school forms."],
    ["🏠","housing","Housing","Rent, eviction, and housing letters."],
    ["🚨","emergency","Emergency","911, Poison Control, 988 — who to call."],
  ];

  const s = {
    wrap: { minHeight:"100vh", background:"#f5f7fb", fontFamily:"system-ui,-apple-system,sans-serif", color:"#1f2933" },
    header: { background:"linear-gradient(135deg,#4b7cff,#7b5cff)", borderRadius:18, padding:"18px 16px", color:"#fff", margin:"12px 10px 0" },
    avatar: { width:64, height:64, borderRadius:"50%", background:"radial-gradient(circle at 30% 20%,#fde68a,#facc15 40%,#f97316 80%)", display:"flex", alignItems:"center", justifyContent:"center", fontWeight:800, fontSize:28, boxShadow:"0 0 0 4px rgba(15,23,42,.35)", flexShrink:0 },
    card: { background:"#fff", borderRadius:18, padding:"14px 12px", margin:"12px 10px 0", boxShadow:"0 10px 30px rgba(15,23,42,.12)" },
    bigBtn: (bg, color, active) => ({ flex:1, minWidth:110, borderRadius:999, border: active ? "3px solid #fff" : "none", padding:"10px 12px", fontSize:14, fontWeight:600, background:bg, color, cursor:"pointer", display:"flex", alignItems:"center", justifyContent:"center", gap:6, boxShadow: active ? "0 0 0 3px rgba(0,0,0,0.3)" : "none" }),
    pill: (primary) => ({ borderRadius:999, border:`1px solid ${primary?"#2563eb":"#d1d5db"}`, padding:"6px 10px", fontSize:12, background:"#fff", color:primary?"#1d4ed8":"#111827", cursor:"pointer", display:"inline-flex", alignItems:"center", gap:5 }),
    menuBtn: { borderRadius:14, border:"1px solid #e5e7eb", background:"#f9fafb", padding:"10px", cursor:"pointer", display:"flex", flexDirection:"column", gap:4, minHeight:70, textAlign:"left" },
    input: { flex:1, minHeight:60, maxHeight:120, resize:"vertical", borderRadius:14, border:"1px solid #d1d5db", padding:"8px 10px", fontSize:14, fontFamily:"system-ui" },
    sendBtn: { borderRadius:14, border:"none", padding:"0 14px", fontSize:14, fontWeight:600, background:"#2563eb", color:"#eff6ff", cursor:"pointer" },
    bubble: (role) => ({ background: role==="helper"?"#e0f2fe":"#e5e7eb", borderRadius:14, padding:"8px 10px", marginBottom:2 }),
    toast: { position:"fixed", bottom:16, left:"50%", transform:"translateX(-50%)", background:"#111827", color:"#f9fafb", padding:"8px 16px", borderRadius:999, fontSize:13, border:"1px solid #4b5563", zIndex:9999, display:"inline-flex", alignItems:"center", gap:6, whiteSpace:"nowrap" },
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
          <button style={{ borderRadius:999, border:"none", padding:"10px 18px", fontSize:15, fontWeight:600, background:"#22c55e", color:"#064e3b", cursor:"pointer" }}
            onClick={() => showToast("Tap any big button below to get help.", "👉")}>
            Let us Get Started
          </button>
          <button style={{ borderRadius:999, border:"1px solid rgba(255,255,255,.7)", padding:"9px 14px", fontSize:13, background:"transparent", color:"#e5e7eb", cursor:"pointer" }}
            onClick={() => navigate("/login")}>
            Sign in for full access
          </button>
        </div>
      </div>

      {/* MAIN CARD */}
      <div style={s.card}>
        {/* Name row */}
        <div style={{ marginBottom:10 }}>
          <div style={{ fontSize:18, fontWeight:700 }}>Hello, {name}!</div>
          <div style={{ fontSize:14, color:"#4b5563" }}>Tap any button below to get help.</div>
          <div style={{ display:"flex", gap:6, marginTop:6, flexWrap:"wrap" }}>
            <input value={nameInput} onChange={e=>setNameInput(e.target.value)}
              onKeyDown={e=>{ if(e.key==="Enter" && nameInput.trim()){ setName(nameInput.trim()); showToast("Nice to meet you, " + nameInput.trim() + ".", "😊"); }}}
              placeholder="Type your name..." style={{ padding:"7px 10px", borderRadius:999, border:"1px solid #d1d5db", fontSize:14, minWidth:160 }} />
            <button onClick={() => { if(nameInput.trim()){ setName(nameInput.trim()); showToast("Nice to meet you, " + nameInput.trim() + ".", "😊"); }}}
              style={{ borderRadius:999, border:"none", padding:"7px 12px", fontSize:13, background:"#2563eb", color:"#eff6ff", cursor:"pointer" }}>
              Save my name
            </button>
          </div>
        </div>

        {/* ACTION BUTTONS */}
        <div style={{ display:"flex", flexWrap:"wrap", gap:8, marginBottom:8 }}>
          <button style={s.bigBtn(listening ? "#dc2626" : "#2563eb", "#eff6ff", listening)} onClick={toggleMic}>
            <span>{listening ? "🔴" : "🎙️"}</span>
            {listening ? "Listening... tap to stop" : "Speak to me"}
          </button>
          <button style={s.bigBtn("#facc15","#78350f", false)}
            onClick={() => showToast("Type what the document says and I will explain it.", "📷", 3500)}>
            <span>📷</span>Read this for me
          </button>
          <button style={s.bigBtn("#ef4444","#fee2e2", false)}
            onClick={() => sendText("Is this a scam? Someone is asking me for money urgently.")}>
            <span>🛡️</span>Is this a scam?
          </button>
        </div>
        <div style={{ display:"flex", flexWrap:"wrap", gap:8, marginBottom:10 }}>
          <button style={s.bigBtn("#7c3aed","#ede9fe", false)} onClick={cycleLang}>
            <span>🌎</span>Language: {lang}
          </button>
          <button style={s.bigBtn(audioEnabled ? "#059669" : "#e5e7eb", audioEnabled ? "#fff" : "#111827", audioEnabled)}
            onClick={() => { setAudioEnabled(a => !a); if(speaking) stopSpeech(); }}>
            <span>{audioEnabled ? "🔊" : "🔇"}</span>{audioEnabled ? "Audio: ON" : "Audio: OFF"}
          </button>
          <button style={s.bigBtn("#e5e7eb","#111827", false)} onClick={() => window.print()}>
            <span>🖨️</span>Print this
          </button>
        </div>

        {/* CONVERSATION */}
        <div style={{ border:"1px solid #e5e7eb", borderRadius:14, background:"#f9fafb", padding:10, maxHeight:280, overflowY:"auto", fontSize:14, marginBottom:8 }}>
          {msgs.map((m,i) => (
            <div key={i} style={{ marginBottom:8 }}>
              <div style={s.bubble(m.role)}>
                {m.text}
                {m.role === "helper" && (
                  <button onClick={() => speak(m.text)}
                    style={{ marginLeft:8, background:"none", border:"none", cursor:"pointer", fontSize:14, opacity:0.6 }}
                    title="Read this aloud">
                    🔊
                  </button>
                )}
              </div>
              <div style={{ fontSize:11, color:"#6b7280", marginTop:2 }}>{m.role==="helper"?"Helper":name} • {m.time}</div>
            </div>
          ))}
          {loading && <div style={{ color:"#6b7280", fontStyle:"italic" }}>Thinking...</div>}
          <div ref={endRef} />
        </div>

        {/* INPUT */}
        <div style={{ display:"flex", gap:6, marginBottom:6 }}>
          <textarea value={input} onChange={e=>setInput(e.target.value)}
            onKeyDown={e=>{ if(e.key==="Enter"&&!e.shiftKey){e.preventDefault(); sendText(input); }}}
            placeholder='Type here, or tap Speak to me...'
            style={s.input} />
          <button onClick={() => sendText(input)} disabled={loading} style={s.sendBtn}>Send</button>
        </div>
        <div style={{ display:"flex", flexWrap:"wrap", gap:6, marginBottom:12 }}>
          <button style={s.pill(true)} onClick={() => { if(lastFull) { addMsg("helper", lastFull); if(audioEnabled) speak(lastFull); } else showToast("Ask me something first.","ℹ️"); }}>
            ➕ Tell me more
          </button>
          <button style={s.pill(false)} onClick={() => { setMsgs([]); addMsg("helper","You are back at the main menu. Tap any button to get help."); }}>
            🏠 Back to main menu
          </button>
          {speaking && (
            <button style={s.pill(false)} onClick={stopSpeech}>⏹ Stop audio</button>
          )}
        </div>

        {/* MENU GRID */}
        <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fill,minmax(180px,1fr))", gap:8 }}>
          {TOPICS.map(([icon,topic,title,desc]) => (
            <button key={topic} style={s.menuBtn}
              onClick={() => sendText("I need help with: " + title)}>
              <div style={{ display:"flex", alignItems:"center", gap:8, fontSize:15, fontWeight:600 }}><span>{icon}</span>{title}</div>
              <div style={{ fontSize:13, color:"#4b5563" }}>{desc}</div>
            </button>
          ))}
        </div>

        <div style={{ marginTop:10, fontSize:11, color:"#4b5563", textAlign:"center" }}>
          This public helper does not save your data. For saved notes and advanced tools,{" "}
          <button style={{ background:"none", border:"none", color:"#2563eb", cursor:"pointer", fontSize:11, padding:0 }}
            onClick={() => navigate("/login")}>sign in</button>.
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
  const [audioEnabled, setAudioEnabled] = useState(false);
  const endRef = useRef(null);
  const callAPI = useHelperAPI(true);
  const { speaking, speak, stop: stopSpeech } = useTTS();

  const showToast = useCallback((msg, icon="ℹ️", dur=2500) => {
    setToast({ msg, icon });
    setTimeout(() => setToast(null), dur);
  }, []);

  const addMsg = useCallback((role, text) => {
    const time = new Date().toLocaleTimeString([], { hour:"numeric", minute:"2-digit" });
    setMsgs(m => [...m, { role, text, time }]);
    return text;
  }, []);

  const sendText = useCallback(async (text) => {
    if (!text.trim() || loading) return;
    addMsg("user", text);
    setInput("");
    setLoading(true);
    const data = await callAPI("ask", { question: text, context }, showToast);
    if (data?.answer || data?.reply || data?.short) {
      const short = data.short || data.answer || data.reply;
      setLastFull(data.full || short);
      addMsg("helper", short);
      if (audioEnabled) speak(short);
    } else {
      addMsg("helper", "I am having trouble reaching the service. Please try again.");
    }
    setLoading(false);
  }, [loading, callAPI, showToast, addMsg, context, audioEnabled, speak]);

  const { listening, toggle: toggleMic } = useMic({
    onResult: (transcript) => sendText(transcript),
    onError: (msg) => showToast(msg, "🔇", 4000),
  });

  useEffect(() => {
    addMsg("helper", "This is your private helper inside WAI-Institute. I will keep answers short and clear. Tap Tell me more for more detail.");
  }, []);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior:"smooth" }); }, [msgs]);

  const saveChat = async () => {
    const transcript = msgs.map(m => "[" + m.role + "] " + m.text).join("\n\n");
    await callAPI("conversations/save", { transcript, context }, showToast);
    showToast("Chat saved.", "💾");
  };

  const TOOLS = [
    { section:"Daily tools", icon:"📅", items:[
      ["📬","read-mail","Read my mail","Upload or paste letters. I will read and explain."],
      ["📷","scan-read","Scan and read","Camera or files. I will turn pictures into text."],
      ["💡","bills","My bills","I will help you understand what you owe."],
      ["📅","appointments","Appointments","Review and prepare for upcoming visits."],
      ["📝","notes","Notes","Keep simple notes I can help you read later."],
      ["🗂️","documents","Saved documents","Documents you or staff have saved for you."],
    ]},
    { section:"Legal tools", icon:"⚖️", items:[
      ["📄","legal-draft","Draft legal form","Simple pleadings or forms. Staff must review."],
      ["✉️","letter-draft","Draft a letter","Clear, respectful letters in plain language."],
      ["📎","upload-review","Upload for review","Staff or instructors review it with you."],
      ["🛡️","scam-check","Scam check","Paste messages. I will flag common scam signs."],
    ]},
    { section:"Health and life", icon:"💊", items:[
      ["💊","medicines","My medicines","Read labels and instructions. Not a doctor."],
      ["🍽️","food","Food and nutrition","Simple food ideas. Not medical advice."],
      ["🏠","housing","Housing","Rent, lease, and housing letters."],
      ["💼","employment","Employment and school","Job offers, school forms, training papers."],
    ]},
    { section:"Support and safety", icon:"🧑‍🤝‍🧑", items:[
      ["📇","trusted-contacts","Trusted contacts","People you trust to help you."],
      ["❤️","caregiver-mode","Caregiver mode","A caregiver works with you in this space."],
      ["💬","saved-conversations","Saved conversations","Review past helper chats."],
      ["🚨","emergency","Emergency info","911, 988, Poison Control reminders."],
    ]},
  ];

  const s = {
    wrap: { minHeight:"100vh", background:"#f5f7fb", fontFamily:"system-ui,-apple-system,sans-serif", color:"#1f2933" },
    navPill: (active) => ({ borderRadius:999, padding:"6px 12px", fontSize:13, border:`1px solid ${active?"#2563eb":"#d1d5db"}`, background:active?"#2563eb":"#fff", color:active?"#eff6ff":"#111827", cursor:"pointer", fontWeight:active?600:400 }),
    header: { background:"linear-gradient(135deg,#4b7cff,#7b5cff)", borderRadius:18, padding:"16px 14px", color:"#fff", margin:"10px 10px 12px", boxShadow:"0 10px 30px rgba(15,23,42,.18)" },
    bigBtn: (bg, color, active) => ({ flex:1, minWidth:110, borderRadius:999, border: active ? "3px solid #fff" : "none", padding:"9px 12px", fontSize:14, fontWeight:600, background:bg, color, cursor:"pointer", display:"flex", alignItems:"center", justifyContent:"center", gap:6 }),
    card: { background:"#fff", borderRadius:18, padding:"14px 12px", boxShadow:"0 10px 30px rgba(15,23,42,.12)" },
    toolBtn: { borderRadius:14, border:"1px solid #e5e7eb", background:"#f9fafb", padding:"9px", cursor:"pointer", display:"flex", flexDirection:"column", gap:4, minHeight:70, textAlign:"left", width:"100%" },
    bubble: (role) => ({ background:role==="helper"?"#e0f2fe":"#e5e7eb", borderRadius:14, padding:"7px 9px", marginBottom:2 }),
    pill: (variant) => ({ borderRadius:999, border:`1px solid ${variant==="primary"?"#2563eb":variant==="danger"?"#ef4444":"#d1d5db"}`, padding:"6px 10px", fontSize:12, background:"#fff", color:variant==="primary"?"#1d4ed8":variant==="danger"?"#b91c1c":"#111827", cursor:"pointer", display:"inline-flex", alignItems:"center", gap:5 }),
    sendBtn: { borderRadius:14, border:"none", padding:"0 14px", fontSize:14, fontWeight:600, background:"#2563eb", color:"#eff6ff", cursor:"pointer" },
    toast: { position:"fixed", bottom:16, left:"50%", transform:"translateX(-50%)", background:"#111827", color:"#f9fafb", padding:"8px 16px", borderRadius:999, fontSize:13, border:"1px solid #4b5563", zIndex:9999, display:"inline-flex", alignItems:"center", gap:6, whiteSpace:"nowrap" },
  };

  return (
    <div style={s.wrap}>
      {/* TOP BAR */}
      <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between", gap:10, padding:"10px 12px 0", flexWrap:"wrap" }}>
        <div style={{ display:"flex", alignItems:"center", gap:10 }}>
          <div style={{ width:52, height:52, borderRadius:"50%", background:"radial-gradient(circle at 30% 20%,#fde68a,#facc15 40%,#f97316 80%)", display:"flex", alignItems:"center", justifyContent:"center", fontWeight:800, fontSize:24, boxShadow:"0 0 0 3px rgba(15,23,42,.35)" }}>H</div>
          <div>
            <div style={{ fontSize:18, fontWeight:700 }}>Helper Workspace</div>
            <div style={{ fontSize:13, color:"#4b5563" }}>Welcome back. I will keep things simple.</div>
          </div>
        </div>
        <div style={{ display:"flex", alignItems:"center", gap:8, flexWrap:"wrap" }}>
          <span style={{ borderRadius:999, padding:"5px 10px", fontSize:12, border:"1px solid #d1d5db", background:"#fff" }}>Role: {user?.role || "Student"}</span>
          <span style={{ borderRadius:999, padding:"6px 10px", fontSize:13, border:"1px solid #d1d5db", background:"#fff" }}>👤 {user?.name || user?.email || "Signed in"}</span>
        </div>
      </div>

      {/* NAV */}
      <div style={{ display:"flex", gap:6, padding:"8px 12px", flexWrap:"wrap" }}>
        {["home","tasks","messages","profile"].map(n => (
          <button key={n} style={s.navPill(activeNav===n)} onClick={() => setActiveNav(n)}>
            {n.charAt(0).toUpperCase()+n.slice(1)}
          </button>
        ))}
      </div>

      {/* HEADER CARD */}
      <div style={s.header}>
        <div style={{ fontSize:20, fontWeight:700, marginBottom:4 }}>I am here to be your HELPER inside WAI-Institute.</div>
        <div style={{ fontSize:14, lineHeight:1.4, marginBottom:12 }}>Your private workspace — read documents, draft letters, manage appointments, stay safe from scams.</div>
        <div style={{ display:"flex", flexWrap:"wrap", gap:8 }}>
          <button style={s.bigBtn(listening ? "#dc2626" : "#2563eb", "#eff6ff", listening)} onClick={toggleMic}>
            <span>{listening ? "🔴" : "🎙️"}</span>{listening ? "Listening... tap to stop" : "Speak to me"}
          </button>
          <button style={s.bigBtn(audioEnabled ? "#059669" : "#6b7280", "#fff", audioEnabled)}
            onClick={() => { setAudioEnabled(a => !a); if(speaking) stopSpeech(); }}>
            <span>{audioEnabled ? "🔊" : "🔇"}</span>{audioEnabled ? "Audio: ON" : "Audio: OFF"}
          </button>
          <button style={s.bigBtn("#ef4444","#fee2e2", false)}
            onClick={() => { setContext("Scam check"); sendText("Check this for scam signs."); }}>
            🛡️ Scam check
          </button>
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
                  <button key={tool} style={s.toolBtn}
                    onClick={() => { setContext(title); sendText("I need help with: " + title); }}>
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
          <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between", marginBottom:8, flexWrap:"wrap", gap:6 }}>
            <div style={{ fontSize:15, fontWeight:700 }}>💬 Conversation and guidance</div>
            <span style={{ fontSize:11, border:"1px solid #d1d5db", borderRadius:999, padding:"3px 8px" }}>Context: {context}</span>
          </div>

          <div style={{ border:"1px solid #e5e7eb", borderRadius:14, background:"#f9fafb", padding:9, maxHeight:320, overflowY:"auto", fontSize:14, marginBottom:8 }}>
            {msgs.map((m,i) => (
              <div key={i} style={{ marginBottom:8 }}>
                <div style={s.bubble(m.role)}>
                  {m.text}
                  {m.role === "helper" && (
                    <button onClick={() => speak(m.text)}
                      style={{ marginLeft:8, background:"none", border:"none", cursor:"pointer", fontSize:14, opacity:0.6 }}
                      title="Read this aloud">🔊</button>
                  )}
                </div>
                <div style={{ fontSize:11, color:"#6b7280", marginTop:2 }}>{m.role==="helper"?"Helper":"You"} • {m.time}</div>
              </div>
            ))}
            {loading && <div style={{ color:"#6b7280", fontStyle:"italic" }}>Thinking...</div>}
            <div ref={endRef} />
          </div>

          <div style={{ display:"flex", gap:6, marginBottom:6 }}>
            <textarea value={input} onChange={e=>setInput(e.target.value)}
              onKeyDown={e=>{ if(e.key==="Enter"&&!e.shiftKey){e.preventDefault(); sendText(input); }}}
              placeholder="Type here, or tap Speak to me..."
              style={{ flex:1, minHeight:60, maxHeight:120, resize:"vertical", borderRadius:14, border:"1px solid #d1d5db", padding:"8px 10px", fontSize:14, fontFamily:"system-ui" }} />
            <button onClick={() => sendText(input)} disabled={loading} style={s.sendBtn}>Send</button>
          </div>

          <div style={{ display:"flex", flexWrap:"wrap", gap:6 }}>
            <button style={s.pill("primary")} onClick={() => { if(lastFull){ addMsg("helper",lastFull); if(audioEnabled) speak(lastFull); }}}>➕ Tell me more</button>
            <button style={s.pill("none")} onClick={() => { setMsgs([]); addMsg("helper","Chat cleared. Tap any tool to start."); setContext("General"); }}>🧹 Clear</button>
            <button style={s.pill("none")} onClick={saveChat}>💾 Save chat</button>
            <button style={s.pill("danger")} onClick={() => { setContext("General"); addMsg("helper","Back to home tools. What do you need help with?"); }}>🏠 Home tools</button>
            {speaking && <button style={s.pill("none")} onClick={stopSpeech}>⏹ Stop audio</button>}
          </div>

          <div style={{ marginTop:10, fontSize:11, color:"#4b5563", textAlign:"center" }}>
            This authenticated helper is part of WAI-Institute. Actions may be logged for safety and training.
          </div>
        </div>
      </div>

      {toast && <div style={s.toast}><span>{toast.icon}</span><span>{toast.msg}</span></div>}
    </div>
  );
}
