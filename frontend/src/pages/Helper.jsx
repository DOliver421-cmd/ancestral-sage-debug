import { useEffect, useRef, useState, useCallback } from "react";
import { useAuth } from "../lib/auth";
import { useNavigate, useSearchParams } from "react-router-dom";
import { BACKEND_URL } from "../lib/api";

function useKeepAlive() {
  useEffect(() => {
    const ping = () => fetch(`${BACKEND_URL}/api/health`, { method:"GET" }).catch(()=>{});
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

  if (loading) return <div style={{display:"flex",alignItems:"center",justifyContent:"center",height:"100vh",fontFamily:"'IBM Plex Sans', sans-serif"}}>Loading...</div>;
  if (requireAuth && !user) { navigate("/login"); return null; }
  return requireAuth ? <AuthHelper user={user} /> : <PublicHelper />;
}

// ===========================================================================
// KNOWLEDGE BASE
// ===========================================================================
const KB = {
  mail: {
    keywords: ["mail","letter","notice","envelope","received","document","paper","sent me"],
    response: (q) => {
      const ql = q.toLowerCase();
      if (ql.includes("irs") || ql.includes("tax")) return "IRS letters always come by postal mail - never email or phone. The letter has your partial SSN and a notice number top-right. Real IRS letters give you 30-60 days to respond. If someone called demanding immediate payment, that is a scam. Call 1-800-829-1040 to verify any IRS contact.";
      if (ql.includes("jury")) return "Jury duty notices are real legal obligations from your local courthouse. You can request a postponement online or by mail if you have a hardship. Missing jury duty without response can result in a fine. Call the number on the notice to ask about your options.";
      if (ql.includes("debt") || ql.includes("collection")) return "Debt collection letters must identify the creditor, the amount, and your right to dispute. You have 30 days to send a written dispute. Once you dispute in writing, the collector must stop contact until they verify the debt. Never pay a debt you do not recognize without getting written verification first.";
      if (ql.includes("evict") || ql.includes("landlord")) return "An eviction notice starts a legal process - it does not mean you must leave immediately. Most states require 3-30 days notice. You have the right to respond and contest in court. Contact a tenant rights organization or legal aid immediately - many offer free help.";
      return "To help you understand this letter, tell me: Who sent it? What is the main thing it is asking you to do? Is there a deadline? Once you share those details I can explain exactly what it means and what steps to take.";
    }
  },
  bills: {
    keywords: ["bill","owe","charge","payment","balance","invoice","overdue","utility","electric","water","gas","phone"],
    response: (q) => {
      const ql = q.toLowerCase();
      if (ql.includes("medical") || ql.includes("hospital")) return "Medical bills can be negotiated and often contain errors. Request an itemized bill listing every charge. Most hospitals have financial assistance programs - ask for the financial assistance office. You can often negotiate the total down 20-50% if you offer a lump sum payment.";
      if (ql.includes("electric") || ql.includes("utility") || ql.includes("gas") || ql.includes("water")) return "Utility companies cannot shut off service without 10-14 days written notice. Before shut-off you have the right to a payment plan. The LIHEAP program provides federal help with energy bills - call 211 to apply.";
      if (ql.includes("collection")) return "When a bill goes to collections, request debt verification in writing within 30 days. Once you dispute in writing, they must stop collecting until they verify. After 7 years, most debts fall off your credit report. You can negotiate a settlement for less than the full amount.";
      return "Tell me who sent the bill, what the amount is, and if anything looks wrong. Everyone has the right to an itemized bill and to dispute charges they do not recognize. If you cannot pay the full amount, most companies have payment plans.";
    }
  },
  housing: {
    keywords: ["evict","eviction","rent","lease","landlord","tenant","apartment","housing","deposit","repair","maintenance","mold","heat"],
    response: (q) => {
      const ql = q.toLowerCase();
      if (ql.includes("evict") || ql.includes("notice to vacate")) return "An eviction notice is the start of a legal process - not an order to leave immediately. The landlord must file in court and a judge must issue an order before you legally have to leave. Contact legal aid today - many will represent you for free. Call 211 for local resources.";
      if (ql.includes("deposit")) return "Security deposits must be returned within 14-30 days of move-out depending on your state. Landlords can only deduct for unpaid rent, damage beyond normal wear and tear, and cleaning if in your lease. Document move-in and move-out conditions with photos.";
      if (ql.includes("repair") || ql.includes("broken") || ql.includes("heat") || ql.includes("mold")) return "Landlords must maintain habitable conditions including working heat, running water, no mold, and structural safety. Send repair requests in writing by email or text. If the landlord does not respond, report to your local housing authority or code enforcement.";
      return "Tell me more about your housing situation - eviction notice, landlord not making repairs, deposit problem, or something else? You have more rights than most people realize.";
    }
  },
  legal: {
    keywords: ["court","lawyer","attorney","lawsuit","legal","judge","summons","rights","arrested","criminal","civil","small claims","divorce","custody","bankruptcy"],
    response: (q) => {
      const ql = q.toLowerCase();
      if (ql.includes("summons") || ql.includes("sued") || ql.includes("served")) return "If you received a summons, do not ignore it - ignoring results in a default judgment against you which can lead to wage garnishment. You typically have 20-30 days to respond. Contact legal aid immediately - many provide free help for people facing lawsuits.";
      if (ql.includes("arrest") || ql.includes("criminal") || ql.includes("charged")) return "If facing criminal charges: you have the right to remain silent, the right to an attorney, and the right to a hearing before a judge. Do not discuss your case with anyone except your attorney. Public defenders are available for criminal cases if you cannot afford a lawyer.";
      if (ql.includes("small claims")) return "Small claims court handles disputes up to $2,500-$25,000 depending on your state. No lawyer needed. Filing fee is usually $30-100. You present your case directly to a judge with evidence like photos, receipts, and texts. Go to your local courthouse and ask for the small claims clerk.";
      return "Legal situations can feel overwhelming but you have rights and there is free help available. Tell me more about what is happening - did you receive a court document, or do you need to find free legal help?";
    }
  },
  scam: {
    keywords: ["scam","fraud","fake","suspicious","gift card","wire transfer","lottery","prize","winner","urgent","threat","arrest","phishing","email","text","call","robocall"],
    response: (q) => {
      const ql = q.toLowerCase();
      if (ql.includes("gift card")) return "Anyone asking you to pay with gift cards is running a scam. This includes people claiming to be the IRS, Social Security, your utility company, or even family members. Real government agencies never accept gift cards as payment. Do not buy the cards. Report to the FTC at reportfraud.ftc.gov.";
      if (ql.includes("irs") || ql.includes("tax")) return "The real IRS never calls, emails, or texts demanding immediate payment. The IRS always sends a letter first by postal mail. If someone called claiming to be the IRS threatening arrest, that is a scam. Hang up. Real IRS number: 1-800-829-1040.";
      if (ql.includes("social security")) return "Social Security never suspends your SSN or demands payment over the phone. This is one of the most common scams. Hang up on anyone making these claims. Real SSA number: 1-800-772-1213. Report scams at oig.ssa.gov.";
      return "What you are describing raises serious scam warning signs. Key signals are: demanding immediate action, threatening arrest, asking for gift cards or wire transfers, claiming to be IRS or Social Security, and offering prizes you did not enter. Do not send any money. Tell me specifically what happened.";
    }
  },
  employment: {
    keywords: ["job","work","fired","laid off","termination","unemployment","employer","wage","salary","overtime","discrimination","harassment","workplace","paystub"],
    response: (q) => {
      const ql = q.toLowerCase();
      if (ql.includes("fired") || ql.includes("terminated") || ql.includes("laid off")) return "Being fired or laid off is stressful but you likely have options. Apply for unemployment benefits right away at your state workforce website. Request your final paycheck in writing if you have not received it. Review any severance agreement carefully before signing - once you sign you usually waive your right to sue.";
      if (ql.includes("unemployment")) return "Apply for unemployment at your state workforce or labor department website. You need your work history for the past 18 months, your SSN, and bank account for direct deposit. Apply as soon as possible - there is usually a waiting week before benefits begin. If your claim is denied, you have the right to appeal.";
      if (ql.includes("wage") || ql.includes("overtime") || ql.includes("not paid")) return "Wage theft is illegal. File a complaint with your state labor board and the federal Department of Labor Wage and Hour Division at dol.gov. Federal law requires time-and-a-half pay for hours over 40 per week for non-exempt workers. Your employer cannot retaliate against you for filing a complaint.";
      return "I can help you understand your employment situation. Tell me more - are you dealing with a termination, a paycheck issue, or a workplace problem?";
    }
  },
  medicines: {
    keywords: ["medicine","medication","pill","drug","prescription","dosage","dose","side effect","pharmacy","label","refill"],
    response: (q) => {
      const ql = q.toLowerCase();
      if (ql.includes("cost") || ql.includes("afford") || ql.includes("expensive")) return "To reduce medication costs: 1) Ask for the generic version. 2) Use GoodRx.com to compare prices - it can save 80%. 3) Ask the doctor for samples. 4) Check NeedyMeds.org for manufacturer assistance programs. 5) Community health centers often have lower-cost prescriptions.";
      if (ql.includes("side effect") || ql.includes("reaction")) return "If you are experiencing side effects, do not stop the medication without calling your doctor or pharmacist first - some medications must be tapered slowly. Serious reactions like difficulty breathing, severe rash, or face swelling are emergencies - call 911.";
      return "I can help you understand medication labels and instructions. I am not a doctor so for medical decisions always check with your pharmacist or healthcare provider. Tell me what medicine you are asking about.";
    }
  },
  food: {
    keywords: ["food","eat","hungry","snap","ebt","food stamp","nutrition","meal","grocery","wic","pantry"],
    response: (q) => {
      const ql = q.toLowerCase();
      if (ql.includes("snap") || ql.includes("food stamp") || ql.includes("ebt")) return "SNAP provides monthly benefits on an EBT card to buy groceries. Apply at your state SNAP website or local Department of Social Services. You need proof of identity, income, and address. Benefits can begin within 7-30 days. Call 211 for help applying.";
      if (ql.includes("food bank") || ql.includes("pantry") || ql.includes("hungry")) return "Food banks provide free groceries with no income verification in most cases. Call 211 or text your ZIP code to 898-211 to find the nearest food pantry. Feeding America at feedingamerica.org also has a locator. Most allow you to visit once a week or month.";
      return "Food assistance is available and there is no shame in using it. Tell me more - are you looking for emergency food today, help with grocery costs long term, or information about a specific program?";
    }
  },
  appointments: {
    keywords: ["appointment","doctor","meeting","court","interview","prepare","upcoming","schedule","bring"],
    response: (q) => {
      const ql = q.toLowerCase();
      if (ql.includes("doctor") || ql.includes("medical")) return "For a medical appointment: write down your symptoms and when they started, list all your current medications, write down your questions. At the appointment say 'I do not understand, can you explain that differently?' Ask: What is the diagnosis? What are my options? What are the side effects?";
      if (ql.includes("court") || ql.includes("hearing")) return "For a court hearing: arrive 30 minutes early, dress professionally, bring all documents organized in a folder, bring any evidence like photos or receipts. Address the judge as 'Your Honor.' Turn your phone completely off. Be brief and stick to facts.";
      return "I can help you prepare for your appointment. Tell me what kind it is and when it is - I will help you know what to bring, what to expect, and what questions to ask.";
    }
  },
  emergency: {
    keywords: ["emergency","danger","911","hurt","violence","domestic","abuse","crisis","suicide","mental health","988","poison","overdose","fire"],
    response: (q) => {
      const ql = q.toLowerCase();
      if (ql.includes("suicid") || ql.includes("kill myself") || ql.includes("want to die")) return "I am concerned about you. Please call or text 988 right now - that is the Suicide and Crisis Lifeline, available 24 hours a day. You can also text HOME to 741741. If you are in immediate danger, call 911. Please reach out to 988 now.";
      if (ql.includes("domestic") || ql.includes("abuse") || ql.includes("violence")) return "Your safety is the most important thing. The National Domestic Violence Hotline is 1-800-799-7233, available 24 hours a day. Text START to 88788 if it is not safe to call. If in immediate danger, call 911. Local shelters provide safe housing and free advocacy.";
      if (ql.includes("poison") || ql.includes("overdose")) return "Call Poison Control immediately at 1-800-222-1222. Available 24 hours a day. If the person is unconscious or not breathing, call 911 first. Tell them what was taken, how much, and when.";
      return "If you are in immediate danger, call 911 now. For crisis support: 988 for mental health crisis, 1-800-799-7233 for domestic violence, 1-800-222-1222 for poison, 211 for local emergency resources.";
    }
  },
  credit: {
    keywords: ["credit","score","report","fico","equifax","experian","transunion","credit card","dispute","improve credit","build credit"],
    response: (q) => {
      const ql = q.toLowerCase();
      if (ql.includes("dispute") || ql.includes("error") || ql.includes("wrong")) return "You can dispute any error on your credit report for free. Get your free reports at annualcreditreport.com. File a dispute directly with the bureau online, by mail, or by phone. The bureau must investigate within 30 days and correct or remove information they cannot verify.";
      if (ql.includes("improve") || ql.includes("build") || ql.includes("raise")) return "Most effective ways to improve your credit: 1) Pay every bill on time - set up autopay for minimums. 2) Keep credit card balances below 30% of your limit. 3) Do not close old credit cards. 4) Limit new credit applications. Most people see improvement within 3-6 months.";
      return "Tell me more about your credit situation - are you trying to understand your score, dispute something on your report, or figure out how to improve your credit?";
    }
  },
};

function getSmartFallback(question) {
  const q = (question || "").toLowerCase();
  let bestCategory = null;
  let bestScore = 0;
  for (const [cat, data] of Object.entries(KB)) {
    const score = data.keywords.filter(kw => q.includes(kw)).length;
    if (score > bestScore) { bestScore = score; bestCategory = cat; }
  }
  if (bestCategory && bestScore > 0) return KB[bestCategory].response(question);
  return "I want to help you with that. Can you tell me a little more - like who sent the document, what it says, or what is confusing you? The more you share, the better I can explain things in plain words.";
}

// ---------------------------------------------------------------------------
// API hook - backend helper endpoint (works for both public and auth users),
// then KB fallback if backend is unreachable
// ---------------------------------------------------------------------------
function useHelperAPI() {
  return useCallback(async (question, topicKey) => {
    // Primary: backend /api/ai/helper — works for everyone, no auth required
    try {
      const headers = { "Content-Type": "application/json" };
      const token = localStorage.getItem("lce_token");
      if (token) headers["Authorization"] = "Bearer " + token;
      const r = await fetch(`${BACKEND_URL}/api/ai/helper`, {
        method: "POST",
        headers,
        body: JSON.stringify({ message: question }),
      });
      if (r.ok) { const d = await r.json(); if (d.reply) return d.reply; }
    } catch {}
    // Fallback: local knowledge base (offline / backend down)
    return getSmartFallback(question);
  }, []);
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
    try { await navigator.mediaDevices.getUserMedia({ audio: true }); }
    catch { onError("Microphone access was denied. Please allow mic access in your browser settings."); return; }
    if (recogRef.current) { recogRef.current.stop(); recogRef.current = null; }
    const rec = new SR();
    rec.lang = "en-US"; rec.continuous = false; rec.interimResults = false; rec.maxAlternatives = 1;
    rec.onstart = () => setListening(true);
    rec.onend = () => { recogRef.current = null; setListening(false); };
    rec.onresult = (e) => { const t = e.results[0]?.[0]?.transcript || ""; if (t.trim()) onResult(t.trim()); };
    rec.onerror = (e) => { recogRef.current = null; setListening(false); onError(e.error === "not-allowed" ? "Microphone access denied." : "Microphone error: " + e.error); };
    recogRef.current = rec;
    try { rec.start(); }
    catch { recogRef.current = null; onError("Microphone error: could not start."); }
  }, [onResult, onError]);

  const stop = useCallback(() => { recogRef.current?.stop(); recogRef.current = null; setListening(false); }, []);
  const toggle = useCallback(() => { if (listening) stop(); else start(); }, [listening, start, stop]);
  return { listening, toggle };
}

// ---------------------------------------------------------------------------
// TTS hook
// ---------------------------------------------------------------------------
function useTTS(voice) {
  const [speaking, setSpeaking] = useState(false);
  const audioRef = useRef(null);
  const abortRef = useRef(null);

  const speakBrowser = useCallback((text) => {
    if (!window.speechSynthesis) return;
    window.speechSynthesis.cancel();
    const utt = new SpeechSynthesisUtterance(text);
    utt.lang = "en-US"; utt.rate = 0.88; utt.pitch = 1.05;
    const voices = window.speechSynthesis.getVoices();
    const female = voices.find(v => v.lang.startsWith("en") && (v.name.includes("Samantha") || v.name.includes("Karen") || v.name.includes("Zira") || v.name.toLowerCase().includes("female")));
    if (female) utt.voice = female;
    utt.onstart = () => setSpeaking(true); utt.onend = () => setSpeaking(false); utt.onerror = () => setSpeaking(false);
    window.speechSynthesis.speak(utt);
  }, []);

  const stop = useCallback(() => {
    abortRef.current?.abort();
    if (audioRef.current) { audioRef.current.pause(); audioRef.current = null; }
    window.speechSynthesis?.cancel(); setSpeaking(false);
  }, []);

  const speak = useCallback(async (text) => {
    if (!text) return;
    abortRef.current?.abort();
    if (audioRef.current) { audioRef.current.pause(); audioRef.current = null; }
    window.speechSynthesis?.cancel();
    const token = localStorage.getItem("lce_token");
    if (!token) { speakBrowser(text); return; }
    const controller = new AbortController();
    abortRef.current = controller;
    setSpeaking(true);
    try {
      const r = await fetch(`${BACKEND_URL}/api/ai/sage/tts`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": "Bearer " + token },
        body: JSON.stringify({ text: text.slice(0, 1000), voice: voice || "nova", speed: 0.95, session_id: "helper-tts" }),
        signal: controller.signal,
      });
      if (!r.ok) { setSpeaking(false); speakBrowser(text); return; }
      const blob = await r.blob();
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      audioRef.current = audio;
      audio.onended = () => { URL.revokeObjectURL(url); setSpeaking(false); };
      audio.onpause = () => setSpeaking(false);
      audio.onerror = () => { setSpeaking(false); speakBrowser(text); };
      audio.play().catch(() => { setSpeaking(false); speakBrowser(text); });
    } catch (e) { if (e?.name !== "AbortError") { setSpeaking(false); speakBrowser(text); } }
  }, [voice, speakBrowser]);

  return { speaking, speak, stop };
}

function useMobileKeyboardFix(endRef) {
  useEffect(() => {
    const vv = window.visualViewport;
    if (!vv) return;
    const handler = () => { if (endRef.current) endRef.current.scrollIntoView({ behavior:"smooth", block:"end" }); };
    vv.addEventListener("resize", handler); vv.addEventListener("scroll", handler);
    return () => { vv.removeEventListener("resize", handler); vv.removeEventListener("scroll", handler); };
  }, [endRef]);
}

// ===========================================================================
// PUBLIC HELPER - colorful, full-featured
// ===========================================================================
function PublicHelper() {
  const [searchParams] = useSearchParams();
  const [msgs, setMsgs] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState(null);
  const [name, setName] = useState("Friend");
  const [nameInput, setNameInput] = useState("");
  const [lang, setLang] = useState("English");
  const [audioEnabled, setAudioEnabled] = useState(false);
  const [activeTopic, setActiveTopic] = useState(null);
  const endRef = useRef(null);
  const inputRef = useRef(null);
  const callAPI = useHelperAPI();
  const navigate = useNavigate();
  const { speaking, speak, stop: stopSpeech } = useTTS("nova");
  useMobileKeyboardFix(endRef);

  // Pre-load topic from query param e.g. ?topic=housing
  useEffect(() => {
    const topic = searchParams.get("topic");
    if (!topic) return;
    const topicMap = {
      "housing": { key: "housing", greeting: "I'm here to help with housing — rent notices, eviction letters, applications, and shelter resources. What do you need help with today?" },
      "health and wellness": { key: "health", greeting: "I can help you understand medical bills, insurance paperwork, benefits letters, and connect you to wellness resources. What's going on?" },
      "food and essentials": { key: "food", greeting: "I can help you find food assistance, clothing, and everyday support resources in your area. What do you need?" },
      "legal": { key: "legal", greeting: "I can help you understand legal letters, court notices, and your rights in plain language. What did you receive?" },
    };
    const matched = Object.entries(topicMap).find(([k]) => topic.toLowerCase().includes(k));
    if (matched) {
      const [, { key, greeting }] = matched;
      setActiveTopic(key);
      const time = new Date().toLocaleTimeString([], { hour:"numeric", minute:"2-digit" });
      setMsgs([{ role: "helper", text: greeting, time }]);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const LANGS = ["English","Espanol","Kreyol Ayisyen","Yoruba","Af-Soomaali","Tagalog","Tieng Viet"];

  const showToast = useCallback((msg) => { setToast(msg); setTimeout(() => setToast(null), 3000); }, []);

  const addMsg = useCallback((role, text) => {
    const time = new Date().toLocaleTimeString([], { hour:"numeric", minute:"2-digit" });
    setMsgs(m => [...m, { role, text, time }]);
  }, []);

  const sendText = useCallback(async (text, topicKey) => {
    if (!text.trim() || loading) return;
    addMsg("user", text); setInput(""); setLoading(true);
    const reply = await callAPI(text, topicKey || activeTopic);
    addMsg("helper", reply);
    if (audioEnabled) speak(reply);
    setLoading(false);
    setTimeout(() => endRef.current?.scrollIntoView({ behavior:"smooth" }), 100);
    inputRef.current?.focus();
  }, [loading, callAPI, addMsg, audioEnabled, speak, activeTopic]);

  const startTopic = useCallback((topicKey, title, prompt) => {
    setActiveTopic(topicKey);
    addMsg("helper", prompt);
    if (audioEnabled) speak(prompt);
    setTimeout(() => endRef.current?.scrollIntoView({ behavior:"smooth" }), 100);
    inputRef.current?.focus();
  }, [addMsg, audioEnabled, speak]);

  const { listening, toggle: toggleMic } = useMic({
    onResult: (t) => sendText(t, activeTopic),
    onError: (msg) => showToast(msg),
  });

  useEffect(() => {
    addMsg("helper", "Hello! I am here to help you understand mail, bills, legal papers, housing, medicines, and more - all in plain, simple words. Choose a topic below or type your question.");
  }, [addMsg]);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior:"smooth" }); }, [msgs]);

  const cycleLang = () => {
    const i = LANGS.indexOf(lang);
    const next = LANGS[(i+1) % LANGS.length];
    setLang(next);
    showToast("I will try to respond in " + next);
  };

  // suppress unused navigate warning - navigate is available for subcomponent use
  void navigate;

  const TOPICS = [
    { key:"mail", icon:"📬", title:"Understand a Letter", prompt:"I can help you understand any letter or official document. Please type or paste what it says and I will explain it in plain words." },
    { key:"bills", icon:"💡", title:"Explain My Bill", prompt:"I can help with your bills. Tell me who sent it, the amount, and what it says. I will explain each part clearly." },
    { key:"credit", icon:"💳", title:"Credit Score", prompt:"I can explain your credit score and what affects it. What would you like to know?" },
    { key:"custody", icon:"👶", title:"Custody Help", prompt:"I can help you understand custody papers. Please type the key parts of the document." },
    { key:"medicines", icon:"💊", title:"Understand Medicines", prompt:"I can help you read medicine labels and understand instructions. What medicine do you need help with?" },
    { key:"food", icon:"🍽️", title:"Food Assistance", prompt:"I can help with food assistance programs or nutrition questions. What do you need?" },
    { key:"appointments", icon:"📅", title:"Prepare for Appointment", prompt:"I can help you prepare for an appointment. What kind is it and when is it?" },
    { key:"legal", icon:"⚖️", title:"Explain Legal Papers", prompt:"I can help explain legal papers in simple words. Please type or paste the key parts." },
    { key:"employment", icon:"💼", title:"Employment Help", prompt:"I can help you understand job papers or employment situations. What do you have?" },
    { key:"housing", icon:"🏠", title:"Housing Issues", prompt:"I can help with rent, lease, eviction notices, and housing letters. Please tell me what the document says." },
    { key:"scam", icon:"🛡️", title:"Check for Scams", prompt:"I can check something for scam signs. Paste or type what you received and I will tell you what I see." },
    { key:"emergency", icon:"🚨", title:"Emergency Numbers", prompt:"Emergency: 911 for danger. 988 for mental health crisis. 1-800-222-1222 for Poison Control. Are you safe right now?" },
  ];

  const activeTitle = TOPICS.find(t => t.key === activeTopic)?.title;

  return (
    <div style={{ display:"flex", flexDirection:"column", height:"100dvh", background:"#f5f7fb", fontFamily:"'IBM Plex Sans', -apple-system, sans-serif", color:"#1f2933", overflow:"hidden" }}>
      {/* COLORFUL GRADIENT HEADER */}
      <div style={{ background:"linear-gradient(135deg,#4b7cff,#7b5cff)", padding:"14px 16px", flexShrink:0, color:"#fff" }}>
        <div style={{ display:"flex", alignItems:"center", gap:12, marginBottom:10 }}>
          <div style={{ width:52, height:52, borderRadius:"50%", background:"radial-gradient(circle at 30% 20%,#fde68a,#facc15 40%,#f97316 80%)", display:"flex", alignItems:"center", justifyContent:"center", fontWeight:800, fontSize:24, flexShrink:0, boxShadow:"0 0 0 3px rgba(255,255,255,0.3)" }}>H</div>
          <div style={{ flex:1 }}>
            <div style={{ fontSize:20, fontWeight:800, lineHeight:1.2 }}>I am here to be your HELPER.</div>
            <div style={{ fontSize:13, opacity:0.9, marginTop:2 }}>I can help you understand mail, bills, legal papers, housing and more — in plain, simple words.</div>
            <div style={{ display:"inline-flex", alignItems:"center", gap:4, marginTop:5, background:"rgba(255,255,255,0.15)", borderRadius:999, padding:"2px 10px", fontSize:11, fontWeight:700, letterSpacing:"0.5px" }}>⚡ AI-Powered — Real answers, not scripts</div>
          </div>
        </div>
        {/* BIG ACTION BUTTONS */}
        <div style={{ display:"flex", flexWrap:"wrap", gap:8, marginBottom:8 }}>
          <button onClick={toggleMic} style={{ flex:1, minWidth:120, borderRadius:999, border:listening?"3px solid #fff":"none", padding:"10px 12px", fontSize:14, fontWeight:700, background:listening?"#dc2626":"#2563eb", color:"#fff", cursor:"pointer", display:"flex", alignItems:"center", justifyContent:"center", gap:6 }}>
            <span>{listening ? "🔴" : "🎙️"}</span>{listening ? "Listening..." : "Speak to me"}
          </button>
          <button onClick={() => showToast("Type or paste what the document says and I will explain it.")} style={{ flex:1, minWidth:120, borderRadius:999, border:"none", padding:"10px 12px", fontSize:14, fontWeight:700, background:"#facc15", color:"#78350f", cursor:"pointer", display:"flex", alignItems:"center", justifyContent:"center", gap:6 }}>
            <span>📷</span>Scan and read
          </button>
          <button onClick={() => sendText("Is this a scam? Help me check.", "scam")} style={{ flex:1, minWidth:120, borderRadius:999, border:"none", padding:"10px 12px", fontSize:14, fontWeight:700, background:"#ef4444", color:"#fff", cursor:"pointer", display:"flex", alignItems:"center", justifyContent:"center", gap:6 }}>
            <span>🛡️</span>Scam check
          </button>
        </div>
        <div style={{ display:"flex", flexWrap:"wrap", gap:8 }}>
          <button onClick={cycleLang} style={{ flex:1, minWidth:120, borderRadius:999, border:"none", padding:"9px 12px", fontSize:13, fontWeight:700, background:"#7c3aed", color:"#ede9fe", cursor:"pointer", display:"flex", alignItems:"center", justifyContent:"center", gap:6 }}>
            <span>🌎</span>Language: {lang}
          </button>
          <button onClick={() => { setAudioEnabled(a => !a); if (speaking) stopSpeech(); }} style={{ flex:1, minWidth:120, borderRadius:999, border:"none", padding:"9px 12px", fontSize:13, fontWeight:700, background:audioEnabled?"#059669":"rgba(255,255,255,0.2)", color:"#fff", cursor:"pointer", display:"flex", alignItems:"center", justifyContent:"center", gap:6 }}>
            <span>{audioEnabled ? "🔊" : "🔇"}</span>{audioEnabled ? "Audio: ON" : "Audio: OFF"}
          </button>
          <button onClick={() => window.print()} style={{ flex:1, minWidth:100, borderRadius:999, border:"none", padding:"9px 12px", fontSize:13, fontWeight:700, background:"rgba(255,255,255,0.15)", color:"#fff", cursor:"pointer", display:"flex", alignItems:"center", justifyContent:"center", gap:6 }}>
            <span>🖨️</span>Print
          </button>
        </div>
        {/* NAME ROW */}
        <div style={{ display:"flex", gap:8, alignItems:"center", marginTop:10, flexWrap:"wrap" }}>
          <span style={{ fontSize:15, fontWeight:700 }}>Hello, {name}!</span>
          <input value={nameInput} onChange={e => setNameInput(e.target.value)}
            onKeyDown={e => { if (e.key==="Enter" && nameInput.trim()) { setName(nameInput.trim()); setNameInput(""); }}}
            placeholder="Tell me your name..." style={{ padding:"6px 12px", borderRadius:999, border:"none", fontSize:13, width:160, background:"rgba(255,255,255,0.2)", color:"#fff", outline:"none" }} />
          {nameInput.trim() && <button onClick={() => { setName(nameInput.trim()); setNameInput(""); }} style={{ borderRadius:999, border:"none", padding:"6px 12px", fontSize:12, background:"#22c55e", color:"#064e3b", cursor:"pointer", fontWeight:700 }}>Save</button>}
        </div>
      </div>

      {/* SCROLLABLE AREA */}
      <div style={{ flex:1, overflowY:"auto", padding:"0 10px 8px", WebkitOverflowScrolling:"touch" }}>
        {/* TOPIC GRID */}
        <div style={{ background:"#fff", borderRadius:14, padding:"12px", margin:"10px 0", boxShadow:"0 2px 12px rgba(15,23,42,.08)" }}>
          <div style={{ fontSize:13, fontWeight:700, color:"#374151", marginBottom:8 }}>
            {activeTopic ? "Topic: " + activeTitle + " — tap another to switch" : "Choose a topic to get started, or just type your question below"}
          </div>
          <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fill,minmax(130px,1fr))", gap:8 }}>
            {TOPICS.map(({ key, icon, title, prompt }) => (
              <button key={key} onClick={() => startTopic(key, title, prompt)}
                style={{ borderRadius:10, border:"2px solid " + (activeTopic===key?"#2563eb":"#e5e7eb"), background:activeTopic===key?"#eff6ff":"#f9fafb", padding:"10px 8px", cursor:"pointer", display:"flex", flexDirection:"column", gap:4, textAlign:"left", transition:"all 0.15s" }}>
                <span style={{ fontSize:22 }}>{icon}</span>
                <span style={{ fontSize:12, fontWeight:600, color:"#1f2933" }}>{title}</span>
              </button>
            ))}
          </div>
        </div>

        {/* CONVERSATION */}
        <div style={{ background:"#fff", borderRadius:14, padding:"12px", margin:"10px 0", boxShadow:"0 2px 12px rgba(15,23,42,.08)" }}>
          <div style={{ display:"flex", flexDirection:"column", gap:10 }}>
            {msgs.map((m, i) => (
              <div key={i} style={{ display:"flex", flexDirection:"column", alignItems:m.role==="helper"?"flex-start":"flex-end" }}>
                <div style={{ maxWidth:"88%", background:m.role==="helper"?"#dbeafe":"#f3f4f6", borderRadius:14, padding:"11px 14px", fontSize:14, lineHeight:1.6 }}>
                  {m.text}
                  {m.role==="helper" && <button onClick={() => speak(m.text)} title="Read aloud" style={{ background:"none", border:"none", cursor:"pointer", fontSize:14, opacity:0.5, marginLeft:6, padding:0, verticalAlign:"middle" }}>🔊</button>}
                </div>
                <div style={{ fontSize:11, color:"#9ca3af", marginTop:2, marginLeft:4, marginRight:4 }}>{m.role==="helper"?"Helper":name} — {m.time}</div>
              </div>
            ))}
            {loading && <div style={{ color:"#6b7280", fontSize:13, fontStyle:"italic" }}>Helper is thinking...</div>}
            <div ref={endRef} style={{ height:1 }} />
          </div>
          <div style={{ display:"flex", flexWrap:"wrap", gap:6, marginTop:10 }}>
            <button onClick={() => { setMsgs([]); setActiveTopic(null); addMsg("helper","Back to the start. Choose a topic or type your question."); }} style={{ borderRadius:999, border:"1px solid #d1d5db", padding:"6px 12px", fontSize:12, background:"#fff", cursor:"pointer" }}>🏠 Start over</button>
            {speaking && <button onClick={stopSpeech} style={{ borderRadius:999, border:"1px solid #d1d5db", padding:"6px 12px", fontSize:12, background:"#fff", cursor:"pointer" }}>⏹ Stop audio</button>}
          </div>
          <div style={{ marginTop:10, fontSize:11, color:"#c4c9d4", textAlign:"center" }}>
            WAI-Institute members get saved notes, more tools, and a private workspace.
          </div>
        </div>
        <div style={{ height:20 }} />
      </div>

      {/* INPUT ROW */}
      <div style={{ display:"flex", gap:6, alignItems:"flex-end", padding:"8px 10px", background:"#fff", borderTop:"1px solid #e5e7eb", flexShrink:0 }}>
        <button onClick={toggleMic} style={{ borderRadius:12, border:"none", padding:"12px 12px", fontSize:18, background:listening?"#dc2626":"#f3f4f6", color:listening?"#fff":"#374151", cursor:"pointer", flexShrink:0 }} title={listening?"Stop":"Speak"}>
          {listening ? "🔴" : "🎙️"}
        </button>
        <button onClick={() => { setAudioEnabled(a => !a); if (speaking) stopSpeech(); }} style={{ borderRadius:12, border:"none", padding:"12px 12px", fontSize:18, background:audioEnabled?"#059669":"#f3f4f6", color:audioEnabled?"#fff":"#374151", cursor:"pointer", flexShrink:0 }} title={audioEnabled?"Audio ON":"Audio OFF"}>
          {audioEnabled ? "🔊" : "🔇"}
        </button>
        <textarea
          ref={inputRef}
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => { if (e.key==="Enter" && !e.shiftKey) { e.preventDefault(); sendText(input, activeTopic); }}}
          onFocus={() => setTimeout(() => endRef.current?.scrollIntoView({ behavior:"smooth" }), 300)}
          placeholder={listening ? "Listening... speak now" : activeTopic ? "Ask about " + activeTitle + "..." : "Type your question here..."}
          style={{ flex:1, minHeight:44, maxHeight:100, resize:"none", borderRadius:12, border:"1px solid #d1d5db", padding:"10px 12px", fontSize:15, fontFamily:"'IBM Plex Sans', sans-serif", outline:"none", lineHeight:1.4 }}
          rows={1}
        />
        <button onClick={() => sendText(input, activeTopic)} disabled={loading} style={{ borderRadius:12, border:"none", padding:"12px 16px", fontSize:14, fontWeight:700, background:"#2563eb", color:"#fff", cursor:"pointer", flexShrink:0 }}>Send</button>
      </div>
      {toast && <div style={{ position:"fixed", top:16, left:"50%", transform:"translateX(-50%)", background:"#111827", color:"#f9fafb", padding:"10px 18px", borderRadius:999, fontSize:13, zIndex:9999, whiteSpace:"nowrap", boxShadow:"0 4px 20px rgba(0,0,0,.3)" }}>{toast}</div>}
    </div>
  );
}

// ===========================================================================
// AUTH HELPER - two-panel desktop: persistent sidebar + tabbed right panel
// ===========================================================================
function AuthHelper({ user }) {
  const [tab, setTab] = useState("home");
  const [msgs, setMsgs] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState(null);
  const [activeTopic, setActiveTopic] = useState(null);
  const [audioEnabled, setAudioEnabled] = useState(false);
  const [tasks, setTasks] = useState([
    { id:1, text:"Review any new mail or letters", done:false },
    { id:2, text:"Check upcoming appointments", done:false },
  ]);
  const [newTask, setNewTask] = useState("");
  const endRef = useRef(null);
  const inputRef = useRef(null);
  const callAPI = useHelperAPI();
  const { speaking, speak, stop: stopSpeech } = useTTS("shimmer");
  useMobileKeyboardFix(endRef);

  const showToast = useCallback((msg) => { setToast(msg); setTimeout(() => setToast(null), 3000); }, []);

  const addMsg = useCallback((role, text) => {
    const time = new Date().toLocaleTimeString([], { hour:"numeric", minute:"2-digit" });
    setMsgs(m => [...m, { role, text, time }]);
  }, []);

  const sendText = useCallback(async (text, topicKey) => {
    if (!text.trim() || loading) return;
    addMsg("user", text); setInput(""); setLoading(true);
    const reply = await callAPI(text, topicKey || activeTopic);
    addMsg("helper", reply);
    if (audioEnabled) speak(reply);
    setLoading(false);
    setTimeout(() => endRef.current?.scrollIntoView({ behavior:"smooth" }), 100);
    inputRef.current?.focus();
  }, [loading, callAPI, addMsg, audioEnabled, speak, activeTopic]);

  const startTopic = useCallback((topicKey, title, prompt) => {
    setActiveTopic(topicKey);
    setTab("messages");
    addMsg("helper", prompt);
    if (audioEnabled) speak(prompt);
    setTimeout(() => endRef.current?.scrollIntoView({ behavior:"smooth" }), 100);
    setTimeout(() => inputRef.current?.focus(), 200);
  }, [addMsg, audioEnabled, speak]);

  const { listening, toggle: toggleMic } = useMic({
    onResult: (t) => sendText(t, activeTopic),
    onError: (msg) => showToast(msg),
  });

  useEffect(() => {
    addMsg("helper", "Welcome back, " + (user?.full_name?.split(" ")[0] || "there") + ". I am your private helper inside WAI-Institute. Choose a tool from the sidebar or just type your question.");
  }, [addMsg, user?.full_name]);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior:"smooth" }); }, [msgs]);

  const AUTH_TOOLS = [
    { section:"Daily Tools", color:"#2563eb", items:[
      { key:"mail", icon:"📬", title:"Understand a letter", prompt:"I can help you understand your mail. Paste or type what the letter says and I will explain what it means and what you need to do." },
      { key:"bills", icon:"💡", title:"Explain my bill", prompt:"I can help with your bills. Tell me who sent it, the amount, and what it says. I will break it down clearly." },
      { key:"appointments", icon:"📅", title:"Prepare for appointment", prompt:"I can help you prepare for an upcoming appointment. What kind is it and when is it?" },
    ]},
    { section:"Legal Tools", color:"#7c3aed", items:[
      { key:"legal", icon:"⚖️", title:"Explain legal papers", prompt:"I can explain legal documents in plain words. Paste or type the key parts and I will walk you through them." },
      { key:"letter-draft", icon:"✉️", title:"Help write a letter", prompt:"I can help you write a clear, respectful letter. Who is it to and what do you need to say?" },
      { key:"scam", icon:"🛡️", title:"Check for scams", prompt:"I can check for scam signs. Paste the message, email, or letter you received and I will flag anything suspicious." },
    ]},
    { section:"Health & Life", color:"#059669", items:[
      { key:"medicines", icon:"💊", title:"Understand medicines", prompt:"I can help you understand medicine labels and instructions. What is the medicine and what does the label say?" },
      { key:"food", icon:"🍽️", title:"Food assistance", prompt:"I can give simple food guidance or help with food assistance programs. What do you need?" },
      { key:"housing", icon:"🏠", title:"Housing issues", prompt:"I can help with housing documents. Do you have a lease, eviction notice, rent increase letter, or something else?" },
      { key:"employment", icon:"💼", title:"Employment help", prompt:"I can help with job papers and employment situations. What type of document or situation do you have?" },
      { key:"credit", icon:"💳", title:"Credit score", prompt:"I can explain your credit score and what affects it. What would you like to know?" },
    ]},
    { section:"Support & Safety", color:"#dc2626", items:[
      { key:"emergency", icon:"🚨", title:"Emergency numbers", prompt:"Emergency: 911 for immediate danger. 988 for mental health crisis. 1-800-222-1222 for Poison Control. Are you safe right now?" },
      { key:"caregiver-mode", icon:"❤️", title:"Caregiver mode", prompt:"Caregiver mode lets a trusted person work alongside you. Is a caregiver present with you right now?" },
    ]},
  ];

  const activeTopicTitle = AUTH_TOOLS.flatMap(s => s.items).find(t => t.key === activeTopic)?.title;
  const firstName = user?.full_name?.split(" ")[0] || "there";

  const TABS = [
    { id:"home", label:"🏠 Home" },
    { id:"tasks", label:"✅ Tasks" },
    { id:"messages", label:"💬 Messages" },
    { id:"profile", label:"👤 Profile" },
  ];

  return (
    <div style={{ display:"flex", flexDirection:"column", height:"100dvh", fontFamily:"'IBM Plex Sans', -apple-system, sans-serif", color:"#1f2933", overflow:"hidden", background:"#f8fafc" }}>
      {/* TOP HEADER */}
      <div style={{ background:"linear-gradient(135deg,#1e3a5f,#2563eb,#7c3aed)", padding:"12px 20px", flexShrink:0, color:"#fff" }}>
        <div style={{ display:"flex", alignItems:"center", gap:14, marginBottom:12 }}>
          <div style={{ width:44, height:44, borderRadius:"50%", background:"radial-gradient(circle at 30% 20%,#fde68a,#facc15 40%,#f97316 80%)", display:"flex", alignItems:"center", justifyContent:"center", fontWeight:900, fontSize:20, flexShrink:0, boxShadow:"0 0 0 3px rgba(255,255,255,0.25)" }}>H</div>
          <div style={{ flex:1 }}>
            <div style={{ display:"flex", alignItems:"center", gap:8 }}>
              <span style={{ fontSize:15, fontWeight:800, lineHeight:1.2 }}>Personal Help Center</span>
              <span style={{ background:"rgba(255,255,255,0.15)", borderRadius:999, padding:"1px 8px", fontSize:10, fontWeight:700, letterSpacing:"0.5px" }}>⚡ AI</span>
            </div>
            <div style={{ fontSize:12, opacity:0.85 }}>Hello, {firstName} — your private workspace</div>
          </div>
          <div style={{ display:"flex", gap:8 }}>
            <button onClick={toggleMic} style={{ borderRadius:999, border:listening?"2px solid #fff":"1px solid rgba(255,255,255,0.4)", padding:"7px 14px", fontSize:13, fontWeight:700, background:listening?"#dc2626":"rgba(255,255,255,0.12)", color:"#fff", cursor:"pointer" }}>
              {listening ? "🔴 Stop" : "🎙️ Speak"}
            </button>
            <button onClick={() => { setAudioEnabled(a => !a); if (speaking) stopSpeech(); }} style={{ borderRadius:999, border:"1px solid rgba(255,255,255,0.4)", padding:"7px 14px", fontSize:13, fontWeight:700, background:audioEnabled?"#059669":"rgba(255,255,255,0.12)", color:"#fff", cursor:"pointer" }}>
              {audioEnabled ? "🔊 ON" : "🔇 OFF"}
            </button>
          </div>
        </div>
        {/* Tabs */}
        <div style={{ display:"flex", gap:4 }}>
          {TABS.map(t => (
            <button key={t.id} onClick={() => setTab(t.id)}
              style={{ borderRadius:999, border:"none", padding:"7px 18px", fontSize:13, fontWeight:700, cursor:"pointer", background:tab===t.id?"rgba(255,255,255,0.95)":"rgba(255,255,255,0.12)", color:tab===t.id?"#1e3a5f":"rgba(255,255,255,0.9)", transition:"all 0.15s" }}>
              {t.label}
            </button>
          ))}
          {msgs.length > 0 && tab !== "messages" && (
            <button onClick={() => setTab("messages")} style={{ marginLeft:"auto", borderRadius:999, border:"1px solid rgba(255,255,255,0.5)", padding:"5px 12px", fontSize:12, fontWeight:600, cursor:"pointer", background:"transparent", color:"rgba(255,255,255,0.8)" }}>
              Back to chat →
            </button>
          )}
        </div>
      </div>

      {/* MAIN BODY — sidebar + content */}
      <div style={{ flex:1, display:"flex", overflow:"hidden" }}>
        {/* LEFT SIDEBAR */}
        <div style={{ width:252, background:"#fff", borderRight:"1px solid #e5e7eb", overflowY:"auto", flexShrink:0, display:"flex", flexDirection:"column" }}>
          {/* Quick actions */}
          <div style={{ padding:"12px", borderBottom:"1px solid #f1f5f9" }}>
            <div style={{ fontSize:10, fontWeight:800, color:"#94a3b8", textTransform:"uppercase", letterSpacing:"0.06em", marginBottom:8 }}>Quick Actions</div>
            <button onClick={() => setTab("tasks")} style={{ width:"100%", borderRadius:10, border:"none", padding:"10px 12px", fontSize:13, fontWeight:700, background:"linear-gradient(135deg,#eff6ff,#dbeafe)", color:"#1e40af", cursor:"pointer", textAlign:"left", marginBottom:6, display:"flex", alignItems:"center", gap:8 }}>
              ✅ Focus on today's tasks
            </button>
            <button onClick={() => startTopic("mail", "Understand a letter", "I can help you understand your mail. Paste or type what the letter says and I will explain what it means and what you need to do.")} style={{ width:"100%", borderRadius:10, border:"none", padding:"10px 12px", fontSize:13, fontWeight:700, background:"linear-gradient(135deg,#fef3c7,#fde68a)", color:"#92400e", cursor:"pointer", textAlign:"left", display:"flex", alignItems:"center", gap:8 }}>
              📷 Quick scan & read
            </button>
          </div>
          {/* Tool categories */}
          <div style={{ padding:"8px", flex:1 }}>
            {AUTH_TOOLS.map(({ section, color, items }) => (
              <div key={section} style={{ marginBottom:14 }}>
                <div style={{ fontSize:10, fontWeight:800, color:"#94a3b8", textTransform:"uppercase", letterSpacing:"0.08em", padding:"6px 6px 4px", display:"flex", alignItems:"center", gap:6 }}>
                  <span style={{ width:7, height:7, borderRadius:"50%", background:color, display:"inline-block", flexShrink:0 }} />
                  {section}
                </div>
                {items.map(({ key, icon, title, prompt }) => (
                  <button key={key} onClick={() => startTopic(key, title, prompt)}
                    style={{ width:"100%", borderRadius:8, border:"none", padding:"8px 10px", fontSize:13, cursor:"pointer", textAlign:"left", display:"flex", alignItems:"center", gap:8, background:activeTopic===key ? color+"18" : "transparent", color:activeTopic===key ? color : "#374151", fontWeight:activeTopic===key ? 700 : 400, borderLeft:activeTopic===key ? `3px solid ${color}` : "3px solid transparent", transition:"all 0.12s" }}>
                    <span style={{ fontSize:16 }}>{icon}</span>
                    <span>{title}</span>
                  </button>
                ))}
              </div>
            ))}
          </div>
        </div>

        {/* RIGHT CONTENT PANEL */}
        <div style={{ flex:1, display:"flex", flexDirection:"column", overflow:"hidden" }}>
          {/* HOME TAB */}
          {tab === "home" && (
            <div style={{ flex:1, overflowY:"auto", padding:"28px 32px" }}>
              <div style={{ marginBottom:28 }}>
                <div style={{ fontSize:28, fontWeight:900, color:"#0f172a", lineHeight:1.2 }}>Good to see you, {firstName}.</div>
                <div style={{ fontSize:15, color:"#64748b", marginTop:6 }}>Your private help center is ready. What do you need today?</div>
              </div>
              <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fill,minmax(190px,1fr))", gap:12, marginBottom:28 }}>
                {[
                  { icon:"📬", title:"Understand mail", desc:"Paste any letter and I'll explain it", color:"#2563eb", key:"mail", prompt:"I can help you understand your mail. Paste or type what the letter says and I will explain what it means and what you need to do." },
                  { icon:"⚖️", title:"Legal papers", desc:"Plain-language legal document help", color:"#7c3aed", key:"legal", prompt:"I can explain legal documents in plain words. Paste or type the key parts and I will walk you through them." },
                  { icon:"💡", title:"Explain my bill", desc:"Break down any bill or charge", color:"#f59e0b", key:"bills", prompt:"I can help with your bills. Tell me who sent it, the amount, and what it says." },
                  { icon:"🛡️", title:"Check for scams", desc:"Flag suspicious messages or calls", color:"#dc2626", key:"scam", prompt:"I can check for scam signs. Paste the message, email, or letter you received." },
                  { icon:"🏠", title:"Housing help", desc:"Leases, eviction, repairs", color:"#059669", key:"housing", prompt:"I can help with housing documents. Do you have a lease, eviction notice, rent increase letter, or something else?" },
                  { icon:"✅", title:"Today's tasks", desc:"Stay on top of what matters", color:"#0891b2", toTab:"tasks" },
                ].map(item => (
                  <button key={item.key || item.toTab}
                    onClick={() => item.key ? startTopic(item.key, item.title, item.prompt) : setTab(item.toTab)}
                    style={{ borderRadius:14, border:`1.5px solid ${item.color}22`, padding:"16px", cursor:"pointer", textAlign:"left", background:"#fff", transition:"all 0.15s", boxShadow:"0 1px 4px rgba(0,0,0,.05)" }}>
                    <div style={{ width:40, height:40, borderRadius:10, background:item.color+"1a", display:"flex", alignItems:"center", justifyContent:"center", fontSize:20, marginBottom:10 }}>{item.icon}</div>
                    <div style={{ fontSize:14, fontWeight:700, color:"#0f172a", marginBottom:4 }}>{item.title}</div>
                    <div style={{ fontSize:12, color:"#64748b", lineHeight:1.4 }}>{item.desc}</div>
                  </button>
                ))}
              </div>
              {msgs.length > 1 && (
                <div style={{ background:"#fff", borderRadius:14, padding:"16px", border:"1px solid #e2e8f0" }}>
                  <div style={{ fontSize:13, fontWeight:700, color:"#374151", marginBottom:10 }}>Recent conversation</div>
                  {msgs.slice(-3).map((m, i) => (
                    <div key={i} style={{ fontSize:13, color:m.role==="helper"?"#1e40af":"#374151", background:m.role==="helper"?"#eff6ff":"#f8fafc", borderRadius:8, padding:"8px 12px", marginBottom:6 }}>
                      <span style={{ fontWeight:700 }}>{m.role==="helper"?"Helper":"You"}:</span>{" "}{m.text.slice(0,120)}{m.text.length>120?"...":""}
                    </div>
                  ))}
                  <button onClick={() => setTab("messages")} style={{ borderRadius:999, border:"1px solid #dbeafe", padding:"6px 14px", fontSize:12, fontWeight:700, background:"#eff6ff", color:"#1e40af", cursor:"pointer", marginTop:6 }}>Continue conversation →</button>
                </div>
              )}
            </div>
          )}

          {/* TASKS TAB */}
          {tab === "tasks" && (
            <div style={{ flex:1, overflowY:"auto", padding:"28px 32px" }}>
              <div style={{ marginBottom:20 }}>
                <div style={{ fontSize:24, fontWeight:900, color:"#0f172a" }}>Today's Tasks</div>
                <div style={{ fontSize:14, color:"#64748b", marginTop:4 }}>Keep track of what you need to do or follow up on.</div>
              </div>
              <div style={{ background:"#fff", borderRadius:14, padding:"16px", border:"1px solid #e2e8f0", marginBottom:16 }}>
                <div style={{ display:"flex", gap:8 }}>
                  <input value={newTask} onChange={e => setNewTask(e.target.value)}
                    onKeyDown={e => { if (e.key==="Enter" && newTask.trim()) { setTasks(t => [...t, {id:Date.now(),text:newTask.trim(),done:false}]); setNewTask(""); }}}
                    placeholder="Add a task or reminder..."
                    style={{ flex:1, borderRadius:8, border:"1px solid #d1d5db", padding:"10px 12px", fontSize:14, outline:"none", fontFamily:"'IBM Plex Sans', sans-serif" }} />
                  <button onClick={() => { if (newTask.trim()) { setTasks(t => [...t, {id:Date.now(),text:newTask.trim(),done:false}]); setNewTask(""); }}}
                    style={{ borderRadius:8, border:"none", padding:"10px 16px", fontSize:13, fontWeight:700, background:"#2563eb", color:"#fff", cursor:"pointer" }}>Add</button>
                </div>
              </div>
              <div style={{ display:"flex", flexDirection:"column", gap:8 }}>
                {tasks.map(task => (
                  <div key={task.id} style={{ background:"#fff", borderRadius:12, padding:"12px 16px", border:"1px solid #e2e8f0", display:"flex", alignItems:"center", gap:12, opacity:task.done?0.5:1, transition:"opacity 0.2s" }}>
                    <input type="checkbox" checked={task.done} onChange={() => setTasks(t => t.map(tk => tk.id===task.id?{...tk,done:!tk.done}:tk))} style={{ width:18, height:18, cursor:"pointer", flexShrink:0 }} />
                    <span style={{ flex:1, fontSize:14, textDecoration:task.done?"line-through":"none", color:"#374151" }}>{task.text}</span>
                    <button onClick={() => setTasks(t => t.filter(tk => tk.id!==task.id))} style={{ borderRadius:6, border:"none", padding:"4px 8px", fontSize:12, background:"#fee2e2", color:"#dc2626", cursor:"pointer" }}>✕</button>
                  </div>
                ))}
                {tasks.length === 0 && (
                  <div style={{ textAlign:"center", padding:"48px 20px", color:"#94a3b8" }}>
                    <div style={{ fontSize:36, marginBottom:8 }}>✅</div>
                    <div style={{ fontSize:16, fontWeight:700 }}>All clear!</div>
                    <div style={{ fontSize:13, marginTop:4 }}>Add something above to keep track of it.</div>
                  </div>
                )}
              </div>
              {tasks.filter(t=>t.done).length > 0 && (
                <button onClick={() => setTasks(t => t.filter(tk => !tk.done))} style={{ marginTop:16, borderRadius:8, border:"1px solid #d1d5db", padding:"8px 14px", fontSize:13, background:"#fff", cursor:"pointer", color:"#6b7280" }}>Clear completed</button>
              )}
            </div>
          )}

          {/* MESSAGES TAB */}
          {tab === "messages" && (
            <div style={{ flex:1, display:"flex", flexDirection:"column", overflow:"hidden" }}>
              {activeTopic && (
                <div style={{ padding:"8px 20px", background:"#eff6ff", borderBottom:"1px solid #dbeafe", display:"flex", alignItems:"center", gap:10, flexShrink:0 }}>
                  <span style={{ fontSize:13, color:"#1e40af" }}>Topic: <strong>{activeTopicTitle}</strong></span>
                  <button onClick={() => setActiveTopic(null)} style={{ fontSize:11, background:"none", border:"1px solid #93c5fd", borderRadius:999, padding:"2px 8px", color:"#1e40af", cursor:"pointer" }}>Clear</button>
                  <span style={{ marginLeft:"auto", fontSize:12, color:"#64748b" }}>← Pick a new tool from the sidebar anytime</span>
                </div>
              )}
              <div style={{ flex:1, overflowY:"auto", padding:"16px 20px", WebkitOverflowScrolling:"touch" }}>
                <div style={{ display:"flex", flexDirection:"column", gap:12 }}>
                  {msgs.map((m, i) => (
                    <div key={i} style={{ display:"flex", flexDirection:"column", alignItems:m.role==="helper"?"flex-start":"flex-end" }}>
                      <div style={{ maxWidth:"80%", background:m.role==="helper"?"#dbeafe":"#f1f5f9", borderRadius:m.role==="helper"?"4px 16px 16px 16px":"16px 4px 16px 16px", padding:"12px 16px", fontSize:14, lineHeight:1.65, color:"#0f172a" }}>
                        {m.text}
                        {m.role==="helper" && <button onClick={() => speak(m.text)} title="Read aloud" style={{ background:"none", border:"none", cursor:"pointer", fontSize:13, opacity:0.45, marginLeft:8, padding:0, verticalAlign:"middle" }}>🔊</button>}
                      </div>
                      <div style={{ fontSize:11, color:"#94a3b8", marginTop:3, marginLeft:4, marginRight:4 }}>{m.role==="helper"?"Helper":"You"} · {m.time}</div>
                    </div>
                  ))}
                  {loading && (
                    <div style={{ display:"flex", alignItems:"center", gap:8, padding:"4px 0" }}>
                      <div style={{ width:8, height:8, borderRadius:"50%", background:"#2563eb", opacity:0.6 }} />
                      <span style={{ color:"#64748b", fontSize:13 }}>Helper is thinking...</span>
                    </div>
                  )}
                  <div ref={endRef} style={{ height:1 }} />
                </div>
                {msgs.length > 0 && (
                  <div style={{ display:"flex", flexWrap:"wrap", gap:6, marginTop:14 }}>
                    <button onClick={() => { setMsgs([]); setActiveTopic(null); addMsg("helper","Cleared. Choose a tool from the sidebar or type your question."); }} style={{ borderRadius:999, border:"1px solid #e2e8f0", padding:"6px 12px", fontSize:12, background:"#fff", cursor:"pointer", color:"#374151" }}>Clear chat</button>
                    {speaking && <button onClick={stopSpeech} style={{ borderRadius:999, border:"1px solid #e2e8f0", padding:"6px 12px", fontSize:12, background:"#fff", cursor:"pointer", color:"#374151" }}>Stop audio</button>}
                  </div>
                )}
              </div>
              <div style={{ display:"flex", gap:8, alignItems:"flex-end", padding:"10px 20px", background:"#fff", borderTop:"1px solid #e5e7eb", flexShrink:0 }}>
                <button onClick={toggleMic} style={{ borderRadius:10, border:"none", padding:"12px", fontSize:18, background:listening?"#dc2626":"#f1f5f9", color:listening?"#fff":"#374151", cursor:"pointer", flexShrink:0 }}>{listening?"🔴":"🎙️"}</button>
                <textarea
                  ref={inputRef}
                  value={input}
                  onChange={e => setInput(e.target.value)}
                  onKeyDown={e => { if (e.key==="Enter" && !e.shiftKey) { e.preventDefault(); sendText(input, activeTopic); }}}
                  onFocus={() => setTimeout(() => endRef.current?.scrollIntoView({ behavior:"smooth" }), 300)}
                  placeholder={listening ? "Listening... speak now" : activeTopic ? "Ask about " + activeTopicTitle + "..." : "Type your question here..."}
                  style={{ flex:1, minHeight:46, maxHeight:120, resize:"none", borderRadius:10, border:"1px solid #d1d5db", padding:"11px 14px", fontSize:15, fontFamily:"'IBM Plex Sans', sans-serif", outline:"none", lineHeight:1.45 }}
                  rows={1}
                />
                <button onClick={() => sendText(input, activeTopic)} disabled={loading} style={{ borderRadius:10, border:"none", padding:"12px 20px", fontSize:14, fontWeight:700, background:loading?"#94a3b8":"#2563eb", color:"#fff", cursor:loading?"not-allowed":"pointer", flexShrink:0 }}>Send</button>
              </div>
            </div>
          )}

          {/* PROFILE TAB */}
          {tab === "profile" && (
            <div style={{ flex:1, overflowY:"auto", padding:"28px 32px" }}>
              <div style={{ marginBottom:20 }}>
                <div style={{ fontSize:24, fontWeight:900, color:"#0f172a" }}>Your Profile</div>
                <div style={{ fontSize:14, color:"#64748b", marginTop:4 }}>Helper preferences and account information.</div>
              </div>
              <div style={{ background:"#fff", borderRadius:14, padding:"20px", border:"1px solid #e2e8f0", marginBottom:14 }}>
                <div style={{ fontSize:10, fontWeight:800, color:"#94a3b8", textTransform:"uppercase", letterSpacing:"0.06em", marginBottom:12 }}>Account</div>
                <div style={{ fontSize:16, fontWeight:700, color:"#0f172a" }}>{user?.full_name}</div>
                <div style={{ fontSize:13, color:"#64748b", marginTop:2 }}>{user?.email}</div>
                <div style={{ fontSize:12, color:"#94a3b8", marginTop:4, textTransform:"capitalize" }}>Role: {(user?.role||"").replace("_"," ")}</div>
              </div>
              <div style={{ background:"#fff", borderRadius:14, padding:"20px", border:"1px solid #e2e8f0", marginBottom:14 }}>
                <div style={{ fontSize:10, fontWeight:800, color:"#94a3b8", textTransform:"uppercase", letterSpacing:"0.06em", marginBottom:12 }}>Audio Settings</div>
                <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between" }}>
                  <div>
                    <div style={{ fontSize:14, fontWeight:600, color:"#374151" }}>Read replies aloud</div>
                    <div style={{ fontSize:12, color:"#94a3b8" }}>Helper will speak each response as it arrives</div>
                  </div>
                  <button onClick={() => { setAudioEnabled(a => !a); if (speaking) stopSpeech(); }}
                    style={{ borderRadius:999, border:"none", padding:"8px 22px", fontSize:13, fontWeight:700, background:audioEnabled?"#059669":"#e5e7eb", color:audioEnabled?"#fff":"#374151", cursor:"pointer", transition:"all 0.15s" }}>
                    {audioEnabled ? "ON" : "OFF"}
                  </button>
                </div>
              </div>
              <div style={{ background:"#fff", borderRadius:14, padding:"20px", border:"1px solid #e2e8f0" }}>
                <div style={{ fontSize:10, fontWeight:800, color:"#94a3b8", textTransform:"uppercase", letterSpacing:"0.06em", marginBottom:10 }}>Privacy Note</div>
                <div style={{ fontSize:13, color:"#374151", lineHeight:1.65 }}>This helper is part of WAI-Institute. Conversations may be logged for safety and quality improvement. No information is shared outside the institute without your consent.</div>
              </div>
            </div>
          )}
        </div>
      </div>

      {toast && <div style={{ position:"fixed", top:16, left:"50%", transform:"translateX(-50%)", background:"#111827", color:"#f9fafb", padding:"10px 18px", borderRadius:999, fontSize:13, zIndex:9999, whiteSpace:"nowrap", boxShadow:"0 4px 20px rgba(0,0,0,.3)" }}>{toast}</div>}
    </div>
  );
}
