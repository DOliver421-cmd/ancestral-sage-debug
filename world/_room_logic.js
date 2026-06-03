// ═══════════════════════════════════════════════════════════
//  ROOM LOGIC — loaded by every persona page after defining:
//    PID, PNAME, PEMOJI, PVOICE, SYSTEM (function returning string)
// ═══════════════════════════════════════════════════════════

// Remove the placeholder call if any HTML pages used it
function includeRoomLogic() { /* no-op — logic loads on script tag parse */ }

SW.load();

// Redirect to world map if no keys
if (!SW.hasKey()) {
  window.location.replace("index.html");
}

SW.recordVisit(PID);

let messages = SW.getMessages(PID);
let voiceOn  = SW.get("voiceOut") !== false;

// ── DOM READY ──────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  updateVoiceBtn();

  if (messages.length === 0) {
    greet();
  } else {
    messages.forEach(m => renderMsg(m));
  }
});

// ── GREETING ──────────────────────────────────────────────
function greet() {
  const name = SW.get("userName") || "traveler";
  const visits = (SW.get("worldVisits") || {})[PID] || 1;

  const sys = SYSTEM();
  const greeting_prompt = visits === 1
    ? `This is ${name}'s first time in your space. Greet them — introduce yourself, your domain, and invite them to speak. Keep it under 80 words. Be fully in character.`
    : `${name} has returned to your space. Welcome them back briefly. Reference something from a previous exchange if memory exists. Under 60 words.`;

  const mem = SW.getMemory(PID);
  const memContext = mem.length
    ? `\n\nPrevious exchanges you remember:\n${mem.map(m => `- "${m.text}"`).join("\n")}`
    : "";

  callAndRender(greeting_prompt + memContext, sys, true);
}

// ── SEND ──────────────────────────────────────────────────
async function send() {
  const el  = document.getElementById("user-input");
  const txt = el.value.trim();
  if (!txt) return;
  if (document.getElementById("send-btn").disabled) return;

  el.value = ""; el.style.height = "";
  document.getElementById("send-btn").disabled = true;

  addMsg({ role: "user", content: txt });
  showDots();

  try {
    const history = messages.slice(-18).map(m => ({ role: m.role, content: m.content }));
    const reply   = await SW.callLLM(SYSTEM(), history);
    hideDots();
    addMsg({ role: "assistant", content: reply });
    SW.addMemory(txt, PID);
    if (voiceOn) SW.speak(reply, PVOICE, () => document.getElementById("speaking-badge").classList.remove("show"));
    if (voiceOn) document.getElementById("speaking-badge").classList.add("show");
  } catch(e) {
    hideDots();
    addMsg({ role: "assistant", content: `(${e.message})` });
  } finally {
    document.getElementById("send-btn").disabled = false;
    el.focus();
  }
}

async function callAndRender(prompt, sys, isGreeting) {
  document.getElementById("send-btn").disabled = true;
  showDots();
  try {
    const history = isGreeting ? [{ role: "user", content: prompt }] : messages.slice(-18).map(m => ({ role: m.role, content: m.content }));
    const reply   = await SW.callLLM(sys, history);
    hideDots();
    addMsg({ role: "assistant", content: reply });
    if (voiceOn) SW.speak(reply, PVOICE, () => document.getElementById("speaking-badge").classList.remove("show"));
    if (voiceOn) document.getElementById("speaking-badge").classList.add("show");
  } catch(e) {
    hideDots();
    addMsg({ role: "assistant", content: `(I couldn't wake up. Check 🔑 for a valid API key. Error: ${e.message})` });
  } finally {
    document.getElementById("send-btn").disabled = false;
  }
}

// ── MESSAGES ──────────────────────────────────────────────
function addMsg(msg) {
  messages.push(msg);
  SW.saveMessages(PID, messages);
  renderMsg(msg);
}

function renderMsg(msg) {
  const container = document.getElementById("messages");

  const row = document.createElement("div");
  row.className = `msg-row ${msg.role === "user" ? "user-row" : "ai-row"}`;

  const av = document.createElement("div");
  av.className = "msg-av";

  if (msg.role === "user") {
    const name = SW.get("userName") || "U";
    av.textContent = name.charAt(0).toUpperCase();
    av.style.cssText = "background:#3b1f6e;color:#fff;font-family:'Trebuchet MS',sans-serif;font-weight:bold;font-size:0.85rem;";
  } else {
    av.textContent = PEMOJI;
    av.style.cssText = `background:var(--persona-orb-bg);box-shadow:0 0 8px var(--persona-glow);`;
  }

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = msg.content;

  if (msg.role === "assistant") {
    const foot = document.createElement("div");
    foot.className = "bubble-foot";

    const rBtn = document.createElement("button");
    rBtn.className = "bb";
    rBtn.textContent = "🔊 Read";
    rBtn.onclick = () => {
      SW.speak(msg.content, PVOICE, () => document.getElementById("speaking-badge").classList.remove("show"));
      document.getElementById("speaking-badge").classList.add("show");
    };

    const cBtn = document.createElement("button");
    cBtn.className = "bb";
    cBtn.textContent = "Copy";
    cBtn.onclick = () => { navigator.clipboard?.writeText(msg.content); cBtn.textContent = "✓ Copied"; setTimeout(() => cBtn.textContent = "Copy", 1500); };

    foot.appendChild(rBtn);
    foot.appendChild(cBtn);
    bubble.appendChild(foot);
  }

  row.appendChild(av);
  row.appendChild(bubble);
  container.appendChild(row);
  container.scrollTop = container.scrollHeight;
}

function showDots() {
  const c = document.getElementById("messages");
  if (document.getElementById("__dots")) return;
  const row = document.createElement("div");
  row.className = "thinking-row"; row.id = "__dots";
  const av = document.createElement("div");
  av.className = "msg-av"; av.textContent = PEMOJI;
  av.style.cssText = `background:var(--persona-orb-bg);box-shadow:0 0 6px var(--persona-glow);`;
  const d = document.createElement("div");
  d.className = "dots";
  d.innerHTML = "<span></span><span></span><span></span>";
  row.appendChild(av); row.appendChild(d);
  c.appendChild(row); c.scrollTop = c.scrollHeight;
}

function hideDots() {
  const d = document.getElementById("__dots");
  if (d) d.remove();
}

// ── VOICE ──────────────────────────────────────────────────
function toggleVoice() {
  voiceOn = !voiceOn;
  SW.set("voiceOut", voiceOn);
  if (!voiceOn) { SW.stopSpeech(); document.getElementById("speaking-badge").classList.remove("show"); }
  updateVoiceBtn();
}

function updateVoiceBtn() {
  const btn = document.getElementById("voice-btn");
  btn.textContent = voiceOn ? "🔊" : "🔇";
  btn.classList.toggle("active", voiceOn);
}

// ── MIC ────────────────────────────────────────────────────
function toggleMic() {
  if (SW.isMicActive()) {
    SW.stopMic();
    document.getElementById("mic-btn").classList.remove("recording");
  } else {
    const btn = document.getElementById("mic-btn");
    SW.startMic(
      (txt) => {
        const inp = document.getElementById("user-input");
        inp.value = inp.value ? `${inp.value} ${txt}` : txt;
        autoResize(inp);
      },
      () => { btn.classList.remove("recording"); },
      (err) => { alert(err); btn.classList.remove("recording"); }
    );
    btn.classList.add("recording");
  }
}

// ── KEYS ──────────────────────────────────────────────────
function toggleKeys() {
  const d = document.getElementById("key-drawer");
  d.classList.toggle("open");
  if (d.classList.contains("open")) {
    const k = SW.getKeys();
    document.getElementById("kd-groq").value   = k.groq || "";
    document.getElementById("kd-gemini").value = k.gemini || "";
    document.getElementById("kd-openai").value = k.openai || "";
    document.getElementById("kd-mistral").value= k.mistral || "";
  }
}

function saveKeys() {
  SW.setKeys({
    groq:    document.getElementById("kd-groq").value.trim(),
    gemini:  document.getElementById("kd-gemini").value.trim(),
    openai:  document.getElementById("kd-openai").value.trim(),
    mistral: document.getElementById("kd-mistral").value.trim(),
  });
  document.getElementById("key-drawer").classList.remove("open");
}

// ── CLEAR ──────────────────────────────────────────────────
function clearRoom() {
  if (!confirm(`Clear your conversation with ${PNAME}?`)) return;
  messages = [];
  SW.clearMessages(PID);
  SW.stopSpeech();
  document.getElementById("messages").innerHTML = "";
  document.getElementById("speaking-badge").classList.remove("show");
  greet();
}

// ── UTILS ──────────────────────────────────────────────────
function handleKey(e) {
  if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); }
}

function autoResize(el) {
  el.style.height = "auto";
  el.style.height = Math.min(el.scrollHeight, 120) + "px";
}

document.addEventListener("click", (e) => {
  const d = document.getElementById("key-drawer");
  if (d.classList.contains("open") && !d.contains(e.target) && !e.target.closest(".icon-btn")) {
    d.classList.remove("open");
  }
});
