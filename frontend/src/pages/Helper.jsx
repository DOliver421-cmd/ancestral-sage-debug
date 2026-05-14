import { useEffect, useRef, useState, useCallback } from "react";
import { useAuth } from "../lib/auth";
import { useNavigate } from "react-router-dom";

const BACKEND = "https://ancestral-sage-backend.onrender.com";

function useKeepAlive() {
  useEffect(() => {
    const ping = () => fetch(`${BACKEND}/api/health`, { method:"GET" }).catch(()=>{});
    ping();
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
    <div style={{display:"flex",alignItems:"center",justifyContent:"center",height:"100vh",fontFamily:"system-ui"}}>
      Loading...
    </div>
  );
  if (requireAuth && !user) { navigate("/login"); return null; }
  return requireAuth ? <AuthHelper user={user} /> : <PublicHelper />;
}

// ---------------------------------------------------------------------------
// Shared API hook — uses /api/ai/chat (same endpoint as AI Tutor)
// Falls back to built-in answers if backend unreachable or not authed
// ---------------------------------------------------------------------------
function useHelperAPI(requireAuth) {
  const { user } = useAuth();
  return useCallback(async (endpoint, body, showToast) => {
    // Only "ask" is supported — all other calls (save, etc.) are no-ops for now
    if (endpoint !== "ask" && endpoint !== "conversations/save") return null;
    if (endpoint === "conversations/save") return { ok: true }; // stub

    // Build AI chat payload from the helper question
    const question = body.question || body.message || "";
    const token = localStorage.getItem("lce_token");

    // For auth helper: use real token. For public: attempt anyway (will 401, triggers fallback)
    const headers = { "Content-Type": "application/json" };
    if (token) headers["Authorization"] = `Bearer ${token}`;

    try {
      const r = await fetch("/api/ai/chat", {
        method: "POST",
        headers,
        body: JSON.stringify({
          session_id: "helper-" + Date.now(),
          message: question,
          mode: "tutor",
        }),
      });
      if (!r.ok) {
        if (r.status === 401 || r.status === 403) {
          // Not logged in — return null to trigger fallback answers
          return null;
        }
        return null;
      }
      const data = await r.json();
      // Normalize to the shape the helper expects
      return { answer: data.reply, short: data.reply, full: data.reply };
    } catch {
      return null; // trigger fallback
    }
  }, [requireAuth, user]);
}

// ---------------------------------------------------------------------------
// Built-in fallback answers when backend is unavailable
// ---------------------------------------------------------------------------
const FALLBACK_ANSWERS = {
  default: {
    short: "I can help you with that. Could you tell me a bit more about your situation so I can give you the most useful information?",
    full: "I am here to help. The more details you share, the better I can assist you. Please describe your situation and I will do my best to explain things clearly and simply."
  },
  mail: {
    short: "I can help you understand your mail. Please type or paste what the letter says and I will explain it in simple words.",
    full: "Mail can be confusing, especially official letters. Paste the key parts of the letter here and I will tell you what it means, what action you may need to take, and whether it looks legitimate or like a scam."
  },
  bills: {
    short: "I can help you understand your bill. What does it say you owe, and who sent it?",
    full: "Bills can be hard to understand. Tell me who sent the bill, what the amount is, and what it is for. I will explain each charge in simple words and let you know if anything looks unusual."
  },
  credit: {
    short: "Your credit score is a number from 300 to 850 that shows lenders how reliably you pay back money. Higher is better.",
    full: "Your credit score is calculated based on payment history, how much debt you carry, length of credit history, types of credit, and recent applications. Scores above 700 are generally considered good. You can check your score for free at annualcreditreport.com once a year."
  },
  custody: {
    short: "Custody papers are serious legal documents. I can help you understand what they say. Please type the key parts.",
    full: "Custody documents describe who has legal and physical custody of a child. Legal custody means who makes decisions. Physical custody means where the child lives. If you have received papers, you may have a deadline to respond. I strongly recommend contacting a legal aid organization in your area as soon as possible."
  },
  medicines: {
    short: "I can help you understand medicine labels. What does the label say? Type the name and instructions.",
    full: "Medicine labels include the drug name, dosage, how often to take it, and warnings. I can help explain what the instructions mean. I am not a doctor — for medical decisions always consult your healthcare provider or pharmacist."
  },
  food: {
    short: "I can give simple food guidance. What would you like to know — meal ideas, what to eat for a condition, or something else?",
    full: "Good nutrition does not have to be complicated. Focus on vegetables, fruits, whole grains, and lean proteins. Limit processed foods and sugary drinks. If you have a specific health condition, your doctor or a registered dietitian can give you personalized guidance."
  },
  appointments: {
    short: "I can help you prepare for an appointment. What kind of appointment is it and when is it?",
    full: "To prepare for an appointment: write down your questions beforehand, bring any relevant documents or insurance cards, arrive 10-15 minutes early, and do not be afraid to ask the provider to explain things in simple words. Would you like help making a list of questions?"
  },
  legal: {
    short: "I can help explain legal papers in simple words. Please type or paste what the document says.",
    full: "Legal documents can be intimidating but I can help break them down. Paste the key sections here. For anything involving court dates, signatures, or deadlines, please also contact a legal aid organization in your area — many offer free help."
  },
  employment: {
    short: "I can help you understand job papers, offers, or work documents. What do you have?",
    full: "Employment documents include job offers, contracts, pay stubs, and termination letters. Each has important details about your rights. Tell me what type of document you have and I will explain what to look for."
  },
  education: {
    short: "I can help with school forms and letters. What do you need help with?",
    full: "School documents can include enrollment forms, financial aid letters, grade reports, and disciplinary notices. Tell me what type of document you have and I will explain it clearly."
  },
  housing: {
    short: "I can help you understand rent, lease, or housing letters. What does the document say?",
    full: "Housing documents include leases, eviction notices, rent increase letters, and utility agreements. An eviction notice is serious — if you received one, you may have only a few days to respond. Contact a local tenant rights organization or legal aid immediately. I can help you understand what the document says."
  },
  emergency: {
    short: "Emergency numbers: 911 for police, fire, or medical emergency. 988 for mental health crisis. 1-800-222-1222 for Poison Control.",
    full: "Key emergency contacts: 911 for any immediate danger, fire, or medical emergency. 988 Suicide and Crisis Lifeline for mental health emergencies. 1-800-222-1222 for Poison Control. 211 connects you to local social services. If you are in danger right now, please call 911 immediately."
  },
  scam: {
    short: "If someone demands money urgently, threatens you, or asks for gift cards or wire transfers — that is almost certainly a scam.",
    full: "Common scam signs: pressure to act immediately, threats of arrest or legal action, requests for gift cards, wire transfers, or cryptocurrency, claims to be from the IRS or Social Security, requests for personal information like your Social Security number. Real government agencies never demand immediate payment by gift card. If unsure, hang up and call the official number from the agency's real website."
  }
};

function getFallback(topic) {
  return FALLBACK_ANSWERS[topic] || FALLBACK_ANSWERS.default;
}

// ---------------------------------------------------------------------------
// Mic hook
// ---------------------------------------------------------------------------
function useMic({ onResult, onError }) {
  const [listening, setListening] = useState(false);
  const recogRef = useRef(null);

  const start = useCallback(async () => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) { onError("Voice input is not supported in this browser. Please use Chrome or Edge."); return; }
    try {
      await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch {
      onError("Microphone access was denied. Please allow mic access in your browser settings.");
      return;
    }
    const rec = new SR();
    rec.lang = "en-US"; rec.continuous = false; rec.interimResults = false; rec.maxAlternatives = 1;
    rec.onstart = () => setListening(true);
    rec.onend = () => setListening(false);
    rec.onresult = (e) => { const t = e.results[0]?.[0]?.transcript || ""; if (t.trim()) onResult(t.trim()); };
    rec.onerror = (e) => {
      setListening(false);
      if (e.error === "not-allowed") onError("Microphone access denied. Please allow mic access and try again.");
      else if (e.error === "no-speech") onError("No speech detected. Please try again.");
      else onError("Microphone error: " + e.error);
    };
    recogRef.current = rec;
    rec.start();
  }, [onResult, onError]);

  const stop = useCallback(() => { recogRef.current?.stop(); setListening(false); }, []);
  const toggle = useCallback(() => { if (listening) stop(); else start(); }, [listening, start, stop]);
  return { listening, toggle };
}

// ---------------------------------------------------------------------------
// TTS hook
// ---------------------------------------------------------------------------
function useTTS() {
  const [speaking, setSpeaking] = useState(false);
  const speak = useCallback((text) => {
    if (!window.speechSynthesis) return;
    window.speechSynthesis.cancel();
    const utt = new SpeechSynthesisUtterance(text);
    utt.lang = "en-US"; utt.rate = 0.92;
    utt.onstart = () => setSpeaking(true);
    utt.onend = () => setSpeaking(false);
    utt.onerror = () => setSpeaking(false);
    window.speechSynthesis.speak(utt);
  }, []);
  const stop = useCallback(() => { window.speechSynthesis?.cancel(); setSpeaking(false); }, []);
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
  const [activeTopic, setActiveTopic] = useState(null);
  const endRef = useRef(null);
  const inputRef = useRef(null);
  const callAPI = useHelperAPI(false);
  const navigate = useNavigate();
  const { speaking, speak, stop: stopSpeech } = useTTS();

  const LANGS = ["English","Espanol","Kreyol Ayisyen","Yoruba","Af-Soomaali","Tagalog","Tieng Viet"];

  const showToast = useCallback((msg, icon="ℹ️", dur=2500) => {
    setToast({ msg, icon });
    setTimeout(() => setToast(null), dur);
  }, []);

  const addMsg = useCallback((role, text) => {
    const time = new Date().toLocaleTimeString([], { hour:"numeric", minute:"2-digit" });
    setMsgs(m => [...m, { role, text, time }]);
    return text;
  }, []);

  useEffect(() => {
    addMsg("helper", "Good to see you. I will keep my answers short and simple. You can tap any topic below, speak to me, or type your question.");
  }, []);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior:"smooth" }); }, [msgs]);

  // Core send — tries API first, falls back to built-in answers
  const sendText = useCallback(async (text, topicKey) => {
    if (!text.trim() || loading) return;
    addMsg("user", text);
    setInput("");
    setLoading(true);

    const data = await callAPI("ask", { question: text }, showToast);
    let reply, full;
    if (data?.answer || data?.reply || data?.short) {
      reply = data.short || data.answer || data.reply;
      full = data.full || reply;
    } else {
      // Use built-in fallback answer for this topic
      const fb = getFallback(topicKey || "default");
      reply = fb.short;
      full = fb.full;
    }
    setLastFull(full);
    addMsg("helper", reply);
    if (audioEnabled) speak(reply);
    setLoading(false);
    inputRef.current?.focus();
  }, [loading, callAPI, showToast, addMsg, audioEnabled, speak]);

  // Topic button — sets context, sends a greeting for that topic, focuses input
  const startTopic = useCallback((topicKey, title, prompt) => {
    setActiveTopic(topicKey);
    addMsg("helper", prompt);
    if (audioEnabled) speak(prompt);
    inputRef.current?.focus();
  }, [addMsg, audioEnabled, speak]);

  const { listening, toggle: toggleMic } = useMic({
    onResult: (transcript) => sendText(transcript, activeTopic),
    onError: (msg) => showToast(msg, "🔇", 4000),
  });

  const cycleLang = () => {
    const i = LANGS.indexOf(lang);
    const next = LANGS[(i+1) % LANGS.length];
    setLang(next);
    showToast("I will try to respond in " + next, "🌎", 3000);
  };

  const TOPICS = [
    { key:"mail",   icon:"📬", title:"Read My Mail",      prompt:"I can help you understand your mail. Please type or paste what the letter says — or describe who it is from — and I will explain it in plain words." },
    { key:"bills",  icon:"💡", title:"My Bills",           prompt:"I can help with your bills. Tell me who sent the bill, what amount it shows, and what it says it is for. I will explain each part clearly." },
    { key:"credit", icon:"💳", title:"Credit Score",       prompt:"I can explain your credit score. Do you have a specific score you want to understand, or would you like me to explain how credit scores work in general?" },
    { key:"custody",icon:"👶", title:"Custody Help",       prompt:"I can help you understand custody papers. Please type the key parts of the document — especially any dates, names, or actions required — and I will explain what they mean." },
    { key:"medicines",icon:"💊",title:"My Medicines",      prompt:"I can help you read medicine labels. Type the medicine name and what the label says, and I will explain the instructions in simple words. I am not a doctor." },
    { key:"food",   icon:"🍽️", title:"What Should I Eat?", prompt:"I can give simple food guidance. What would you like to know — general healthy eating, food for a specific condition, or meal ideas on a budget?" },
    { key:"appointments",icon:"📅",title:"My Appointments",prompt:"I can help you prepare for an appointment. What kind of appointment is it — doctor, school, court, or something else? When is it?" },
    { key:"legal",  icon:"⚖️", title:"Legal Help",         prompt:"I can help explain legal papers in simple words. Please type or paste the key parts of the document. For anything with a deadline or court date, I will also tell you to seek free legal aid." },
    { key:"employment",icon:"💼",title:"Employment",       prompt:"I can help you understand job papers. What do you have — a job offer, a pay stub, a termination letter, or something else?" },
    { key:"education",icon:"🎓",title:"Education",         prompt:"I can help with school forms and letters. What type of document do you have, and what part is confusing you?" },
    { key:"housing",icon:"🏠", title:"Housing",            prompt:"I can help with rent, lease, or housing letters. This includes eviction notices, which are urgent. Please type what the document says and when it was dated." },
    { key:"emergency",icon:"🚨",title:"Emergency Info",    prompt:"Emergency numbers: 911 for immediate danger, fire, or medical. 988 for mental health crisis. 1-800-222-1222 for Poison Control. 211 for local social services. Are you in a safe situation right now?" },
  ];

  const C = {
    wrap: { minHeight:"100vh", background:"#f5f7fb", fontFamily:"system-ui,-apple-system,sans-serif", color:"#1f2933", paddingBottom:32 },
    header: { background:"linear-gradient(135deg,#4b7cff,#7b5cff)", padding:"18px 16px", color:"#fff" },
    card: { background:"#fff", margin:"12px 10px 0", borderRadius:16, padding:"14px 12px", boxShadow:"0 4px 20px rgba(15,23,42,.10)" },
    topicBtn: (active) => ({ borderRadius:12, border:`2px solid ${active?"#2563eb":"#e5e7eb"}`, background:active?"#eff6ff":"#f9fafb", padding:"10px 10px", cursor:"pointer", display:"flex", flexDirection:"column", gap:3, textAlign:"left", transition:"all 0.15s" }),
    bubble: (role) => ({ background:role==="helper"?"#dbeafe":"#f3f4f6", borderRadius:14, padding:"10px 12px", fontSize:14, lineHeight:1.5, display:"flex", justifyContent:"space-between", alignItems:"flex-start", gap:8 }),
    inputArea: { display:"flex", gap:8, alignItems:"flex-end" },
    textarea: { flex:1, minHeight:52, maxHeight:120, resize:"vertical", borderRadius:12, border:"1px solid #d1d5db", padding:"10px 12px", fontSize:14, fontFamily:"system-ui", outline:"none" },
    sendBtn: { borderRadius:12, border:"none", padding:"12px 18px", fontSize:14, fontWeight:700, background:"#2563eb", color:"#fff", cursor:"pointer", flexShrink:0 },
    micBtn: (active) => ({ borderRadius:12, border:"none", padding:"12px 14px", fontSize:18, background:active?"#dc2626":"#f3f4f6", color:active?"#fff":"#374151", cursor:"pointer", flexShrink:0, transition:"all 0.15s" }),
    pill: { borderRadius:999, border:"1px solid #d1d5db", padding:"6px 12px", fontSize:12, background:"#fff", color:"#374151", cursor:"pointer", display:"inline-flex", alignItems:"center", gap:4 },
    toast: { position:"fixed", bottom:20, left:"50%", transform:"translateX(-50%)", background:"#111827", color:"#f9fafb", padding:"10px 18px", borderRadius:999, fontSize:13, zIndex:9999, display:"inline-flex", alignItems:"center", gap:8, boxShadow:"0 4px 20px rgba(0,0,0,0.3)", whiteSpace:"nowrap" },
  };

  return (
    <div style={C.wrap}>
      {/* HEADER */}
      <div style={C.header}>
        <div style={{ display:"flex", alignItems:"center", gap:12, maxWidth:900, margin:"0 auto" }}>
          <div style={{ width:56, height:56, borderRadius:"50%", background:"radial-gradient(circle at 30% 20%,#fde68a,#facc15 40%,#f97316 80%)", display:"flex", alignItems:"center", justifyContent:"center", fontWeight:800, fontSize:26, flexShrink:0 }}>H</div>
          <div style={{ flex:1 }}>
            <div style={{ fontSize:20, fontWeight:700 }}>I am here to be your HELPER.</div>
            <div style={{ fontSize:13, opacity:0.9, marginTop:2 }}>Read mail, understand bills, explain legal papers — in plain, simple words.</div>
          </div>
          <button onClick={() => navigate("/login")} style={{ borderRadius:999, border:"1px solid rgba(255,255,255,0.6)", padding:"8px 14px", fontSize:13, background:"transparent", color:"#fff", cursor:"pointer", flexShrink:0 }}>
            Sign in for more tools
          </button>
        </div>
      </div>

      <div style={{ maxWidth:900, margin:"0 auto" }}>
        {/* NAME ROW */}
        <div style={{ ...C.card, display:"flex", flexWrap:"wrap", alignItems:"center", gap:10, justifyContent:"space-between" }}>
          <div style={{ display:"flex", gap:6, alignItems:"center", flexWrap:"wrap" }}>
            <div style={{ fontSize:16, fontWeight:700 }}>Hello, {name}!</div>
            <input value={nameInput} onChange={e=>setNameInput(e.target.value)}
              onKeyDown={e=>{ if(e.key==="Enter"&&nameInput.trim()){setName(nameInput.trim()); showToast("Nice to meet you, "+nameInput.trim()+"!","😊");}}}
              placeholder="Type your name..." style={{ padding:"6px 10px", borderRadius:999, border:"1px solid #d1d5db", fontSize:13, width:150 }} />
            <button onClick={()=>{ if(nameInput.trim()){setName(nameInput.trim()); showToast("Nice to meet you, "+nameInput.trim()+"!","😊");}}}
              style={{ borderRadius:999, border:"none", padding:"6px 12px", fontSize:13, background:"#2563eb", color:"#fff", cursor:"pointer" }}>Save</button>
          </div>
          <div style={{ display:"flex", gap:6, flexWrap:"wrap" }}>
            <button onClick={cycleLang} style={{ ...C.pill, background:"#7c3aed", color:"#fff", border:"none" }}>🌎 {lang}</button>
            <button onClick={()=>{ setAudioEnabled(a=>!a); if(speaking) stopSpeech(); }}
              style={{ ...C.pill, background:audioEnabled?"#059669":"#f3f4f6", color:audioEnabled?"#fff":"#374151", border:"none", fontWeight:600 }}>
              {audioEnabled?"🔊 Audio ON":"🔇 Audio OFF"}
            </button>
            <button onClick={()=>window.print()} style={C.pill}>🖨️ Print</button>
          </div>
        </div>

        {/* TOPIC GRID */}
        <div style={C.card}>
          <div style={{ fontSize:14, fontWeight:700, marginBottom:10, color:"#374151" }}>
            {activeTopic ? `Topic: ${TOPICS.find(t=>t.key===activeTopic)?.title || activeTopic} — tap a different topic to switch` : "Choose a topic to get started, or just type your question below"}
          </div>
          <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fill,minmax(160px,1fr))", gap:8 }}>
            {TOPICS.map(({ key, icon, title, prompt }) => (
              <button key={key} style={C.topicBtn(activeTopic===key)}
                onClick={() => startTopic(key, title, prompt)}>
                <div style={{ fontSize:20 }}>{icon}</div>
                <div style={{ fontSize:13, fontWeight:600, color:"#1f2933" }}>{title}</div>
              </button>
            ))}
          </div>
        </div>

        {/* CONVERSATION */}
        <div style={C.card}>
          <div style={{ maxHeight:320, overflowY:"auto", marginBottom:12, display:"flex", flexDirection:"column", gap:8 }}>
            {msgs.map((m,i) => (
              <div key={i} style={{ display:"flex", flexDirection:"column", alignItems:m.role==="user"?"flex-end":"flex-start" }}>
                <div style={{ maxWidth:"85%", ...C.bubble(m.role) }}>
                  <span>{m.text}</span>
                  {m.role==="helper" && (
                    <button onClick={()=>speak(m.text)} title="Read aloud"
                      style={{ background:"none", border:"none", cursor:"pointer", fontSize:16, opacity:0.5, flexShrink:0, padding:0 }}>🔊</button>
                  )}
                </div>
                <div style={{ fontSize:11, color:"#9ca3af", marginTop:2 }}>{m.role==="helper"?"Helper":name} • {m.time}</div>
              </div>
            ))}
            {loading && (
              <div style={{ display:"flex", alignItems:"center", gap:8, color:"#6b7280", fontSize:13, fontStyle:"italic" }}>
                <span style={{ animation:"spin 1s linear infinite", display:"inline-block" }}>⏳</span> Helper is thinking...
              </div>
            )}
            <div ref={endRef} />
          </div>

          {/* INPUT ROW — mic sits right next to textarea */}
          <div style={C.inputArea}>
            <button onClick={toggleMic} style={C.micBtn(listening)} title={listening?"Stop listening":"Tap to speak"}>
              {listening ? "🔴" : "🎙️"}
            </button>
            <textarea
              ref={inputRef}
              value={input}
              onChange={e=>setInput(e.target.value)}
              onKeyDown={e=>{ if(e.key==="Enter"&&!e.shiftKey){e.preventDefault(); sendText(input, activeTopic);}}}
              placeholder={listening ? "Listening... speak now" : activeTopic ? "Ask your question about " + (TOPICS.find(t=>t.key===activeTopic)?.title||"") + "..." : "Type your question here, or tap the mic to speak..."}
              style={C.textarea}
            />
            <button onClick={()=>sendText(input,activeTopic)} disabled={loading} style={C.sendBtn}>Send</button>
          </div>

          {/* QUICK ACTIONS */}
          <div style={{ display:"flex", flexWrap:"wrap", gap:6, marginTop:8 }}>
            {lastFull && (
              <button style={C.pill} onClick={()=>{ addMsg("helper",lastFull); if(audioEnabled) speak(lastFull); }}>➕ Tell me more</button>
            )}
            <button style={C.pill} onClick={()=>{ setMsgs([]); setActiveTopic(null); addMsg("helper","Back to the start. Choose a topic or type your question."); }}>🏠 Start over</button>
            <button style={{ ...C.pill, background:"#fef2f2", color:"#b91c1c", border:"1px solid #fecaca" }}
              onClick={()=>sendText("What are the signs of a scam?","scam")}>🛡️ Is this a scam?</button>
            {speaking && <button style={C.pill} onClick={stopSpeech}>⏹ Stop audio</button>}
          </div>

          <div style={{ marginTop:10, fontSize:11, color:"#9ca3af", textAlign:"center" }}>
            Public helper — no data saved. <button style={{ background:"none",border:"none",color:"#2563eb",cursor:"pointer",fontSize:11,padding:0 }} onClick={()=>navigate("/login")}>Sign in</button> for saved notes and advanced tools.
          </div>
        </div>
      </div>

      {toast && <div style={C.toast}><span>{toast.icon}</span><span>{toast.msg}</span></div>}
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
  const [activeTopic, setActiveTopic] = useState(null);
  const [activeNav, setActiveNav] = useState("home");
  const [audioEnabled, setAudioEnabled] = useState(false);
  const endRef = useRef(null);
  const inputRef = useRef(null);
  const callAPI = useHelperAPI(true);
  const { speaking, speak, stop: stopSpeech } = useTTS();

  const showToast = useCallback((msg, icon="ℹ️", dur=2500) => {
    setToast({ msg, icon });
    setTimeout(() => setToast(null), dur);
  }, []);

  const addMsg = useCallback((role, text) => {
    const time = new Date().toLocaleTimeString([], { hour:"numeric", minute:"2-digit" });
    setMsgs(m => [...m, { role, text, time }]);
  }, []);

  const sendText = useCallback(async (text, topicKey) => {
    if (!text.trim() || loading) return;
    addMsg("user", text);
    setInput("");
    setLoading(true);
    const data = await callAPI("ask", { question: text, context: topicKey || "general" }, showToast);
    let reply, full;
    if (data?.answer || data?.reply || data?.short) {
      reply = data.short || data.answer || data.reply;
      full = data.full || reply;
    } else {
      const fb = getFallback(topicKey || "default");
      reply = fb.short; full = fb.full;
    }
    setLastFull(full);
    addMsg("helper", reply);
    if (audioEnabled) speak(reply);
    setLoading(false);
    inputRef.current?.focus();
  }, [loading, callAPI, showToast, addMsg, audioEnabled, speak]);

  const startTopic = useCallback((topicKey, title, prompt) => {
    setActiveTopic(topicKey);
    addMsg("helper", prompt);
    if (audioEnabled) speak(prompt);
    inputRef.current?.focus();
  }, [addMsg, audioEnabled, speak]);

  const { listening, toggle: toggleMic } = useMic({
    onResult: (transcript) => sendText(transcript, activeTopic),
    onError: (msg) => showToast(msg, "🔇", 4000),
  });

  useEffect(() => {
    addMsg("helper", "This is your private helper inside WAI-Institute. Choose a topic from the tools or type your question. I will keep answers short and clear.");
  }, []);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior:"smooth" }); }, [msgs]);

  const saveChat = async () => {
    const transcript = msgs.map(m=>"["+m.role+"] "+m.text).join("\n\n");
    const data = await callAPI("conversations/save", { transcript, context: activeTopic||"general" }, showToast);
    if (data) showToast("Chat saved successfully.", "💾");
  };

  const AUTH_TOOLS = [
    { section:"Daily tools", items:[
      { key:"mail", icon:"📬", title:"Read my mail", prompt:"I can help you read and understand your mail. Paste or type the key parts of the letter and I will explain what it means and what you need to do." },
      { key:"bills", icon:"💡", title:"My bills", prompt:"I can help with your bills. Tell me who sent it, the amount, and what it says. I will break it down line by line." },
      { key:"appointments", icon:"📅", title:"Appointments", prompt:"I can help you prepare for an upcoming appointment. What kind is it — doctor, school, court, or something else? When is it?" },
      { key:"notes", icon:"📝", title:"Notes", prompt:"I can help you keep simple notes. What would you like to write down or remember?" },
      { key:"documents", icon:"🗂️", title:"Saved documents", prompt:"I can help you find or review documents saved for you. What are you looking for?" },
    ]},
    { section:"Legal tools", items:[
      { key:"legal-draft", icon:"📄", title:"Draft legal form", prompt:"I can help you draft a simple legal form or pleading in plain language. What type of form do you need, and what is the situation?" },
      { key:"letter-draft", icon:"✉️", title:"Draft a letter", prompt:"I can help you write a clear, respectful letter. Who is the letter to, and what do you need to say?" },
      { key:"legal", icon:"⚖️", title:"Understand legal papers", prompt:"I can explain legal documents in plain words. Paste or type the key parts and I will walk you through what they mean." },
      { key:"scam", icon:"🛡️", title:"Scam check", prompt:"I can check for scam signs. Paste the message, email, or letter you received and I will flag anything suspicious." },
    ]},
    { section:"Health and life", items:[
      { key:"medicines", icon:"💊", title:"My medicines", prompt:"I can help you understand medicine labels and instructions. What is the medicine name and what does the label say?" },
      { key:"food", icon:"🍽️", title:"Food and nutrition", prompt:"I can give simple food guidance — not medical advice. Are you looking for general healthy eating tips, or guidance for a specific situation?" },
      { key:"housing", icon:"🏠", title:"Housing", prompt:"I can help with housing documents. Do you have a lease, eviction notice, rent increase letter, or something else?" },
      { key:"employment", icon:"💼", title:"Employment", prompt:"I can help with job papers and employment documents. What type of document do you have?" },
    ]},
    { section:"Support and safety", items:[
      { key:"trusted-contacts", icon:"📇", title:"Trusted contacts", prompt:"I can help you review or update your trusted contacts — the people you rely on for help. What would you like to do?" },
      { key:"caregiver-mode", icon:"❤️", title:"Caregiver mode", prompt:"Caregiver mode lets a trusted person work alongside you in this space. Is a caregiver present with you right now?" },
      { key:"saved-conversations", icon:"💬", title:"Saved conversations", prompt:"I can help you review your past helper conversations. What are you looking for?" },
      { key:"emergency", icon:"🚨", title:"Emergency info", prompt:"Emergency: 911 for immediate danger. 988 for mental health crisis. 1-800-222-1222 for Poison Control. 211 for local services. Are you safe right now?" },
    ]},
  ];

  const C = {
    wrap: { minHeight:"100vh", background:"#f5f7fb", fontFamily:"system-ui,-apple-system,sans-serif", color:"#1f2933", paddingBottom:32 },
    topBar: { background:"#fff", borderBottom:"1px solid #e5e7eb", padding:"10px 16px", display:"flex", alignItems:"center", justifyContent:"space-between", gap:10, flexWrap:"wrap" },
    card: { background:"#fff", borderRadius:16, padding:"14px 12px", boxShadow:"0 4px 20px rgba(15,23,42,.08)" },
    toolBtn: (active) => ({ borderRadius:12, border:`2px solid ${active?"#2563eb":"#e5e7eb"}`, background:active?"#eff6ff":"#f9fafb", padding:"9px 9px", cursor:"pointer", display:"flex", flexDirection:"column", gap:3, textAlign:"left", width:"100%", transition:"all 0.15s" }),
    bubble: (role) => ({ background:role==="helper"?"#dbeafe":"#f3f4f6", borderRadius:14, padding:"10px 12px", fontSize:14, lineHeight:1.5, display:"flex", justifyContent:"space-between", alignItems:"flex-start", gap:8 }),
    textarea: { flex:1, minHeight:52, maxHeight:120, resize:"vertical", borderRadius:12, border:"1px solid #d1d5db", padding:"10px 12px", fontSize:14, fontFamily:"system-ui", outline:"none" },
    sendBtn: { borderRadius:12, border:"none", padding:"12px 18px", fontSize:14, fontWeight:700, background:"#2563eb", color:"#fff", cursor:"pointer", flexShrink:0 },
    micBtn: (active) => ({ borderRadius:12, border:"none", padding:"12px 14px", fontSize:18, background:active?"#dc2626":"#f3f4f6", color:active?"#fff":"#374151", cursor:"pointer", flexShrink:0 }),
    pill: { borderRadius:999, border:"1px solid #d1d5db", padding:"6px 12px", fontSize:12, background:"#fff", color:"#374151", cursor:"pointer", display:"inline-flex", alignItems:"center", gap:4 },
    navPill: (a) => ({ borderRadius:999, padding:"6px 12px", fontSize:13, border:`1px solid ${a?"#2563eb":"#d1d5db"}`, background:a?"#2563eb":"#fff", color:a?"#fff":"#111827", cursor:"pointer", fontWeight:a?600:400 }),
    toast: { position:"fixed", bottom:20, left:"50%", transform:"translateX(-50%)", background:"#111827", color:"#f9fafb", padding:"10px 18px", borderRadius:999, fontSize:13, zIndex:9999, display:"inline-flex", alignItems:"center", gap:8, boxShadow:"0 4px 20px rgba(0,0,0,0.3)", whiteSpace:"nowrap" },
  };

  const activeTopicTitle = AUTH_TOOLS.flatMap(s=>s.items).find(t=>t.key===activeTopic)?.title;

  return (
    <div style={C.wrap}>
      {/* TOP BAR */}
      <div style={C.topBar}>
        <div style={{ display:"flex", alignItems:"center", gap:10 }}>
          <div style={{ width:40, height:40, borderRadius:"50%", background:"radial-gradient(circle at 30% 20%,#fde68a,#facc15 40%,#f97316 80%)", display:"flex", alignItems:"center", justifyContent:"center", fontWeight:800, fontSize:20 }}>H</div>
          <div>
            <div style={{ fontSize:16, fontWeight:700 }}>Helper Workspace</div>
            <div style={{ fontSize:12, color:"#6b7280" }}>WAI-Institute — private and secure</div>
          </div>
        </div>
        <div style={{ display:"flex", gap:6, alignItems:"center", flexWrap:"wrap" }}>
          {["home","tasks","messages","profile"].map(n=>(
            <button key={n} style={C.navPill(activeNav===n)} onClick={()=>setActiveNav(n)}>
              {n.charAt(0).toUpperCase()+n.slice(1)}
            </button>
          ))}
          <span style={{ borderRadius:999, padding:"5px 10px", fontSize:12, border:"1px solid #d1d5db", background:"#f9fafb" }}>
            {user?.role||"Student"}
          </span>
          <button onClick={()=>{ setAudioEnabled(a=>!a); if(speaking) stopSpeech(); }}
            style={{ ...C.pill, background:audioEnabled?"#059669":"#f3f4f6", color:audioEnabled?"#fff":"#374151", border:"none", fontWeight:600 }}>
            {audioEnabled?"🔊 Audio ON":"🔇 Audio OFF"}
          </button>
        </div>
      </div>

      {/* MAIN LAYOUT */}
      <div style={{ display:"grid", gridTemplateColumns:"300px 1fr", gap:12, padding:"12px 12px 0", maxWidth:1100, margin:"0 auto" }}>

        {/* LEFT — TOOLS */}
        <div style={{ display:"flex", flexDirection:"column", gap:10 }}>
          {AUTH_TOOLS.map(({ section, items }) => (
            <div key={section} style={C.card}>
              <div style={{ fontSize:13, fontWeight:700, color:"#6b7280", marginBottom:8, textTransform:"uppercase", letterSpacing:"0.05em" }}>{section}</div>
              <div style={{ display:"flex", flexDirection:"column", gap:6 }}>
                {items.map(({ key, icon, title, prompt }) => (
                  <button key={key} style={C.toolBtn(activeTopic===key)}
                    onClick={()=>startTopic(key,title,prompt)}>
                    <div style={{ display:"flex", alignItems:"center", gap:8, fontSize:13, fontWeight:600 }}>
                      <span style={{ fontSize:16 }}>{icon}</span>{title}
                    </div>
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>

        {/* RIGHT — CONVERSATION */}
        <div style={{ display:"flex", flexDirection:"column", gap:10 }}>
          {/* Context banner */}
          {activeTopic && (
            <div style={{ ...C.card, background:"#eff6ff", border:"1px solid #bfdbfe", padding:"10px 14px", display:"flex", justifyContent:"space-between", alignItems:"center" }}>
              <div style={{ fontSize:14, fontWeight:600, color:"#1d4ed8" }}>
                Topic: {activeTopicTitle}
              </div>
              <button onClick={()=>{ setActiveTopic(null); addMsg("helper","Topic cleared. Choose a new topic or type your question."); }}
                style={{ ...C.pill, fontSize:11 }}>Clear topic</button>
            </div>
          )}

          <div style={C.card}>
            {/* Messages */}
            <div style={{ maxHeight:400, overflowY:"auto", marginBottom:12, display:"flex", flexDirection:"column", gap:8 }}>
              {msgs.map((m,i) => (
                <div key={i} style={{ display:"flex", flexDirection:"column", alignItems:m.role==="user"?"flex-end":"flex-start" }}>
                  <div style={{ maxWidth:"88%", ...C.bubble(m.role) }}>
                    <span>{m.text}</span>
                    {m.role==="helper" && (
                      <button onClick={()=>speak(m.text)} title="Read aloud"
                        style={{ background:"none", border:"none", cursor:"pointer", fontSize:16, opacity:0.5, flexShrink:0, padding:0 }}>🔊</button>
                    )}
                  </div>
                  <div style={{ fontSize:11, color:"#9ca3af", marginTop:2 }}>{m.role==="helper"?"Helper":"You"} • {m.time}</div>
                </div>
              ))}
              {loading && (
                <div style={{ color:"#6b7280", fontSize:13, fontStyle:"italic", padding:"4px 0" }}>Helper is thinking...</div>
              )}
              <div ref={endRef} />
            </div>

            {/* INPUT ROW — mic next to input */}
            <div style={{ display:"flex", gap:8, alignItems:"flex-end" }}>
              <button onClick={toggleMic} style={C.micBtn(listening)} title={listening?"Stop":"Speak"}>
                {listening?"🔴":"🎙️"}
              </button>
              <textarea
                ref={inputRef}
                value={input}
                onChange={e=>setInput(e.target.value)}
                onKeyDown={e=>{ if(e.key==="Enter"&&!e.shiftKey){e.preventDefault(); sendText(input,activeTopic);}}}
                placeholder={listening?"Listening... speak now": activeTopic ? "Ask about "+activeTopicTitle+"..." : "Type your question, or tap the mic to speak..."}
                style={C.textarea}
              />
              <button onClick={()=>sendText(input,activeTopic)} disabled={loading} style={C.sendBtn}>Send</button>
            </div>

            {/* QUICK ACTIONS */}
            <div style={{ display:"flex", flexWrap:"wrap", gap:6, marginTop:8 }}>
              {lastFull && <button style={C.pill} onClick={()=>{ addMsg("helper",lastFull); if(audioEnabled) speak(lastFull); }}>➕ Tell me more</button>}
              <button style={C.pill} onClick={()=>{ setMsgs([]); setActiveTopic(null); addMsg("helper","Cleared. Choose a tool or type your question."); }}>🧹 Clear</button>
              <button style={C.pill} onClick={saveChat}>💾 Save chat</button>
              {speaking && <button style={C.pill} onClick={stopSpeech}>⏹ Stop audio</button>}
            </div>
          </div>

          <div style={{ fontSize:11, color:"#9ca3af", textAlign:"center" }}>
            This authenticated helper is part of WAI-Institute. Actions may be logged for safety and training. Not a lawyer, doctor, or emergency service.
          </div>
        </div>
      </div>

      {toast && <div style={C.toast}><span>{toast.icon}</span><span>{toast.msg}</span></div>}
    </div>
  );
}
