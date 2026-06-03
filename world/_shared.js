// ═══════════════════════════════════════════════════════════
//  SOVEREIGN WORLD — Shared Intelligence Layer
//  All pages load this. Handles: state, LLM gateway, TTS, STT.
// ═══════════════════════════════════════════════════════════

const SW = (() => {

  // ── STATE ──────────────────────────────────────────────────
  let _state = {
    userName: "",
    keys: {},
    voiceOut: true,
    worldVisits: {},   // personaId → count
    globalMemory: [],  // cross-persona memory snippets
  };

  function load() {
    try {
      const s = JSON.parse(localStorage.getItem("sw_state") || "{}");
      _state = { ..._state, ...s };
    } catch(e) {}
  }

  function save() {
    localStorage.setItem("sw_state", JSON.stringify(_state));
  }

  function get(k)    { return _state[k]; }
  function set(k, v) { _state[k] = v; save(); }

  function getKeys()      { return _state.keys || {}; }
  function setKeys(keys)  { _state.keys = keys; save(); }

  function hasKey() {
    const k = _state.keys || {};
    return !!(k.groq || k.gemini || k.openai || k.mistral || k.cohere);
  }

  function recordVisit(personaId) {
    if (!_state.worldVisits) _state.worldVisits = {};
    _state.worldVisits[personaId] = (_state.worldVisits[personaId] || 0) + 1;
    save();
  }

  function addMemory(text, personaId) {
    if (!_state.globalMemory) _state.globalMemory = [];
    _state.globalMemory.push({ text: text.slice(0, 120), persona: personaId, ts: Date.now() });
    if (_state.globalMemory.length > 40) _state.globalMemory.shift();
    save();
  }

  function getMemory(personaId) {
    if (!_state.globalMemory) return [];
    return _state.globalMemory.filter(m => m.persona === personaId).slice(-6);
  }

  function getAllMemory() {
    return (_state.globalMemory || []).slice(-12);
  }

  // ── PERSONA MESSAGES (per-page localStorage) ──────────────
  function getMessages(personaId) {
    try {
      return JSON.parse(localStorage.getItem(`sw_msgs_${personaId}`) || "[]");
    } catch(e) { return []; }
  }

  function saveMessages(personaId, msgs) {
    localStorage.setItem(`sw_msgs_${personaId}`, JSON.stringify(msgs.slice(-60)));
  }

  function clearMessages(personaId) {
    localStorage.removeItem(`sw_msgs_${personaId}`);
  }

  // ── LLM GATEWAY ────────────────────────────────────────────
  async function callLLM(systemPrompt, messages) {
    const keys = _state.keys || {};

    if (keys.groq)   { try { return await _groq(systemPrompt, messages, keys.groq); }   catch(e) { console.warn("Groq:", e.message); } }
    if (keys.gemini) { try { return await _gemini(systemPrompt, messages, keys.gemini); } catch(e) { console.warn("Gemini:", e.message); } }
    if (keys.openai) { try { return await _openai(systemPrompt, messages, keys.openai); } catch(e) { console.warn("OpenAI:", e.message); } }
    if (keys.mistral){ try { return await _mistral(systemPrompt, messages, keys.mistral); } catch(e) { console.warn("Mistral:", e.message); } }
    if (keys.cohere) { try { return await _cohere(systemPrompt, messages, keys.cohere); }  catch(e) { console.warn("Cohere:", e.message); } }

    throw new Error("No working API key found. Open 🔑 to add one.");
  }

  async function _groq(sys, msgs, key) {
    const r = await fetch("https://api.groq.com/openai/v1/chat/completions", {
      method: "POST",
      headers: { "Content-Type": "application/json", "Authorization": `Bearer ${key}` },
      body: JSON.stringify({ model: "llama-3.3-70b-versatile", messages: [{role:"system",content:sys}, ...msgs], max_tokens: 1200, temperature: 0.85 })
    });
    if (!r.ok) throw new Error(`${r.status} ${(await r.text()).slice(0,200)}`);
    return (await r.json()).choices[0].message.content.trim();
  }

  async function _gemini(sys, msgs, key) {
    const contents = msgs.map(m => ({ role: m.role === "assistant" ? "model" : "user", parts: [{text: m.content}] }));
    const r = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${key}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ contents, system_instruction: { parts: [{text: sys}] } })
    });
    if (!r.ok) throw new Error(`${r.status} ${(await r.text()).slice(0,200)}`);
    return (await r.json()).candidates[0].content.parts[0].text.trim();
  }

  async function _openai(sys, msgs, key) {
    const r = await fetch("https://api.openai.com/v1/chat/completions", {
      method: "POST",
      headers: { "Content-Type": "application/json", "Authorization": `Bearer ${key}` },
      body: JSON.stringify({ model: "gpt-4o-mini", messages: [{role:"system",content:sys}, ...msgs], max_tokens: 1200, temperature: 0.85 })
    });
    if (!r.ok) throw new Error(`${r.status} ${(await r.text()).slice(0,200)}`);
    return (await r.json()).choices[0].message.content.trim();
  }

  async function _mistral(sys, msgs, key) {
    const r = await fetch("https://api.mistral.ai/v1/chat/completions", {
      method: "POST",
      headers: { "Content-Type": "application/json", "Authorization": `Bearer ${key}` },
      body: JSON.stringify({ model: "mistral-small-latest", messages: [{role:"system",content:sys}, ...msgs], max_tokens: 1200, temperature: 0.85 })
    });
    if (!r.ok) throw new Error(`${r.status} ${(await r.text()).slice(0,200)}`);
    return (await r.json()).choices[0].message.content.trim();
  }

  async function _cohere(sys, msgs, key) {
    const chatHistory = msgs.slice(0,-1).map(m => ({ role: m.role === "assistant" ? "CHATBOT" : "USER", message: m.content }));
    const lastMsg = msgs[msgs.length - 1]?.content || "";
    const r = await fetch("https://api.cohere.ai/v1/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json", "Authorization": `Bearer ${key}` },
      body: JSON.stringify({ model: "command-r", preamble: sys, chat_history: chatHistory, message: lastMsg, max_tokens: 1200, temperature: 0.85 })
    });
    if (!r.ok) throw new Error(`${r.status} ${(await r.text()).slice(0,200)}`);
    return (await r.json()).text.trim();
  }

  // ── TTS ────────────────────────────────────────────────────
  let _synth = window.speechSynthesis;
  let _speaking = false;

  function speak(text, voiceParams = {}, onEnd) {
    if (!_state.voiceOut || !text) return;
    stopSpeech();
    const utt = new SpeechSynthesisUtterance(text.slice(0, 2200));
    utt.pitch  = voiceParams.pitch  ?? 1.0;
    utt.rate   = voiceParams.rate   ?? 0.92;
    utt.volume = voiceParams.volume ?? 1;
    const voices = _synth.getVoices();
    const v = voices.find(v => v.name.includes("Google") && v.lang.startsWith("en")) || voices.find(v => v.lang.startsWith("en")) || voices[0];
    if (v) utt.voice = v;
    _speaking = true;
    utt.onend  = () => { _speaking = false; onEnd?.(); };
    utt.onerror= () => { _speaking = false; };
    _synth.speak(utt);
  }

  function stopSpeech() {
    if (_synth) _synth.cancel();
    _speaking = false;
  }

  function isSpeaking() { return _speaking; }

  // ── STT ────────────────────────────────────────────────────
  let _rec = null;
  let _micActive = false;

  async function startMic(onResult, onEnd, onError) {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) { onError?.("Voice input requires Chrome or Edge."); return; }
    try { await navigator.mediaDevices.getUserMedia({ audio: true }); } catch(e) { onError?.("Microphone access denied."); return; }

    _rec = new SR();
    _rec.continuous = false;
    _rec.interimResults = false;
    _rec.lang = "en-US";
    _rec.onresult = (e) => { onResult?.(Array.from(e.results).map(r => r[0].transcript).join(" ").trim()); };
    _rec.onend  = () => { _micActive = false; onEnd?.(); };
    _rec.onerror= () => { _micActive = false; onEnd?.(); };
    _rec.start();
    _micActive = true;
  }

  function stopMic() {
    if (_rec) { try { _rec.stop(); } catch(e) {} _rec = null; }
    _micActive = false;
  }

  function isMicActive() { return _micActive; }

  // ── EXPORT ─────────────────────────────────────────────────
  return { load, save, get, set, getKeys, setKeys, hasKey, recordVisit, addMemory, getMemory, getAllMemory, getMessages, saveMessages, clearMessages, callLLM, speak, stopSpeech, isSpeaking, startMic, stopMic, isMicActive };

})();

window.SW = SW;
