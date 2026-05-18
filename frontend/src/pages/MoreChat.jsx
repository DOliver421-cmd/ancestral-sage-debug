import { useState, useEffect, useRef, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import AppShell from "../components/AppShell";
import { useAuth } from "../lib/auth";
import { api } from "../lib/api";
import { Send, Clock, ArrowLeft, Loader2, Shield, PlusCircle } from "lucide-react";
import { toast } from "sonner";

const ROOMS = [
  { id: "general", label: "General", desc: "Open community conversation" },
  { id: "skills", label: "Skills Exchange", desc: "Offer or request skills and knowledge" },
  { id: "needs", label: "Help Needed", desc: "Immediate needs and mutual support" },
  { id: "elders", label: "Elder Support", desc: "Resources and support for elders" },
  { id: "youth", label: "Youth Space", desc: "Youth-safe community space" },
];

function ChatMessage({ msg, currentUserId }) {
  const isOwn = msg.author_id === currentUserId;
  const expiresIn = Math.max(0, Math.round(
    (new Date(msg.expires_at) - Date.now()) / 60000
  ));

  return (
    <div className={`flex flex-col gap-0.5 ${isOwn ? "items-end" : "items-start"}`}>
      <div className="flex items-center gap-2 text-xs text-ink/40 px-1">
        {!isOwn && <span className="font-medium text-ink/60">{msg.author_name}</span>}
        <span className="flex items-center gap-1">
          <Clock className="w-3 h-3" />
          {expiresIn}m
        </span>
      </div>
      <div className={`max-w-sm px-4 py-2.5 text-sm leading-relaxed ${
        isOwn
          ? "bg-ink text-white"
          : "bg-white border border-ink/10 text-ink"
      }`}>
        {msg.content}
      </div>
    </div>
  );
}

export default function MoreChat() {
  const { user } = useAuth();
  const { roomId = "general" } = useParams();
  const navigate = useNavigate();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const [oliver, setOliver] = useState(null);
  const bottomRef = useRef(null);
  const pollRef = useRef(null);

  const currentRoom = ROOMS.find(r => r.id === roomId) || ROOMS[0];

  const loadMessages = useCallback(async () => {
    try {
      const r = await api.get(`/more/chat/${roomId}`);
      setMessages(r.data.messages || []);
    } catch {
      // silent poll failure
    }
  }, [roomId]);

  useEffect(() => {
    setMessages([]);
    setLoading(true);
    loadMessages().finally(() => setLoading(false));

    pollRef.current = setInterval(loadMessages, 15000);
    return () => clearInterval(pollRef.current);
  }, [roomId, loadMessages]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const send = async () => {
    if (!input.trim() || sending) return;
    setSending(true);
    setOliver(null);
    try {
      const r = await api.post("/more/chat/send", { session_id: roomId, message: input.trim() });
      setInput("");
      if (r.data.oliver_response) setOliver(r.data.oliver_response);
      await loadMessages();
    } catch (err) {
      const msg = err?.response?.data?.detail || "Could not send";
      toast.error(msg);
      if (msg.length > 30) setOliver(msg);
    } finally {
      setSending(false);
    }
  };

  const handleKey = e => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  return (
    <AppShell>
      <div className="flex h-screen flex-col">
        {/* Header */}
        <div className="border-b border-ink/10 bg-bone px-6 py-4 flex items-center gap-4">
          <button
            onClick={() => navigate("/more")}
            className="text-ink/50 hover:text-ink transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div className="flex-1">
            <h1 className="font-heading font-bold">{currentRoom.label}</h1>
            <p className="text-xs text-ink/50">{currentRoom.desc} · Messages expire in 60 min</p>
          </div>
          {/* Room selector */}
          <select
            value={roomId}
            onChange={e => navigate(`/more/chat/${e.target.value}`)}
            className="text-sm border border-ink/20 bg-white px-3 py-1.5 focus:outline-none focus:border-copper"
          >
            {ROOMS.map(r => (
              <option key={r.id} value={r.id}>{r.label}</option>
            ))}
          </select>
        </div>

        {/* Oliver warning */}
        {oliver && (
          <div className="flex items-start gap-3 bg-amber-50 border-b border-amber-200 px-6 py-3">
            <Shield className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
            <p className="text-sm text-amber-800 flex-1">
              <span className="font-bold">Oliver Guardian: </span>{oliver}
            </p>
            <button onClick={() => setOliver(null)} className="text-amber-400 text-xs font-bold">✕</button>
          </div>
        )}

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-6 py-6 space-y-4">
          {loading ? (
            <div className="flex justify-center py-10">
              <Loader2 className="w-5 h-5 animate-spin text-copper" />
            </div>
          ) : messages.length === 0 ? (
            <div className="text-center py-16 text-ink/60">
              <p className="text-sm">No messages yet. Start the conversation.</p>
              <p className="text-xs mt-2 italic">All messages expire after 60 minutes.</p>
            </div>
          ) : (
            messages.map(m => (
              <ChatMessage key={m.id} msg={m} currentUserId={user?.id} />
            ))
          )}
          <div ref={bottomRef} />
        </div>

        {/* Input */}
        <div className="border-t border-ink/10 bg-bone px-6 py-4">
          <div className="flex gap-3 items-end">
            <textarea
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKey}
              maxLength={1000}
              rows={2}
              placeholder="Message the community… (Enter to send · no money · no personal info)"
              className="flex-1 border border-ink/20 bg-white px-4 py-2.5 text-sm resize-none focus:outline-none focus:border-copper"
            />
            <button
              onClick={send}
              disabled={sending || !input.trim()}
              className="btn-copper p-3 flex items-center justify-center disabled:opacity-50"
            >
              {sending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
            </button>
          </div>
          <p className="text-xs text-ink/30 mt-2 flex items-center gap-1">
            <Shield className="w-3 h-3" />
            Protected by Oliver Guardian · Auto-purges after 60 min
          </p>
        </div>
      </div>
    </AppShell>
  );
}
