import { useState, useEffect, useCallback } from "react";
import AppShell from "../components/AppShell";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import { toast } from "sonner";
import { Music2, MapPin, DollarSign, Calendar, Users, RefreshCw, X, CheckCircle, Clock, XCircle } from "lucide-react";

/* ── tokens ── */
const T = {
  bg:     "#080508",
  card:   "#100a10",
  orange: "#f97316",
  gold:   "#d4af37",
  green:  "#22c55e",
  text:   "#ede8e0",
  muted:  "#6b5e60",
  border: "rgba(249,115,22,0.2)",
};

const S = {
  page:  { background: T.bg, color: T.text, minHeight: "100vh", padding: "2rem 1.5rem", maxWidth: 1000, margin: "0 auto" },
  card:  { background: T.card, border: `1px solid ${T.border}`, borderRadius: 14, padding: "1.2rem 1.4rem", marginBottom: "0.9rem" },
  label: { fontSize: "0.68rem", color: T.gold, textTransform: "uppercase", letterSpacing: "0.09em", display: "block", marginBottom: "0.25rem" },
  input: { background: "#050305", border: `1px solid rgba(249,115,22,0.25)`, borderRadius: 8, color: T.text, padding: "0.5rem 0.75rem", fontSize: "0.83rem", width: "100%", outline: "none", fontFamily: "inherit" },
  btn:   { background: T.orange, color: "#fff", border: "none", borderRadius: 8, padding: "0.5rem 1.1rem", fontSize: "0.82rem", fontWeight: "bold", cursor: "pointer" },
  btnGold: { background: T.gold, color: "#1a1100", border: "none", borderRadius: 8, padding: "0.5rem 1.1rem", fontSize: "0.82rem", fontWeight: "bold", cursor: "pointer" },
};

function fmtCents(c) {
  if (!c) return null;
  return `$${(c / 100).toLocaleString("en-US", { minimumFractionDigits: 0 })}`;
}

const STATUS_STYLE = {
  pending:   { color: "#fbbf24", bg: "rgba(251,191,36,0.1)",  border: "rgba(251,191,36,0.3)",  icon: Clock },
  accepted:  { color: "#22c55e", bg: "rgba(34,197,94,0.1)",   border: "rgba(34,197,94,0.3)",   icon: CheckCircle },
  declined:  { color: "#ef4444", bg: "rgba(239,68,68,0.1)",   border: "rgba(239,68,68,0.3)",   icon: XCircle },
  cancelled: { color: "#6b7280", bg: "rgba(107,114,128,0.1)", border: "rgba(107,114,128,0.25)", icon: X },
};

export default function BandOnPage() {
  const { user } = useAuth();
  const [tab,       setTab]       = useState("browse");
  const [listings,  setListings]  = useState([]);
  const [bookings,  setBookings]  = useState({ as_artist: [], as_requester: [] });
  const [myListing, setMyListing] = useState(null);
  const [loading,   setLoading]   = useState(true);
  const [booking,   setBooking]   = useState(null); // listing to book

  const [search, setSearch]   = useState({ genre: "", location: "" });
  const [listForm, setListForm] = useState({
    artist_name: "", bio: "", genres_text: "", location: "",
    rate_min: "", rate_max: "", available: true, social_links_text: ""
  });
  const [bookForm, setBookForm] = useState({
    event_name: "", event_date: "", venue_name: "", venue_city: "", offer: "", message: ""
  });
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ available_only: "false" });
      if (search.genre)    params.set("genre",    search.genre);
      if (search.location) params.set("location", search.location);

      const [lR, bR, mR] = await Promise.allSettled([
        api.get(`/band/listings?${params}`),
        api.get("/band/bookings"),
        api.get("/band/my-listing"),
      ]);
      if (lR.status === "fulfilled") setListings(lR.value.data?.listings || []);
      if (bR.status === "fulfilled") setBookings(bR.value.data || { as_artist: [], as_requester: [] });
      if (mR.status === "fulfilled") {
        const ml = mR.value.data;
        setMyListing(ml && ml.id ? ml : null);
        if (ml?.id) {
          setListForm({
            artist_name: ml.artist_name || "",
            bio: ml.bio || "",
            genres_text: (ml.genres || []).join(", "),
            location: ml.location || "",
            rate_min: ml.rate_min ? String(ml.rate_min / 100) : "",
            rate_max: ml.rate_max ? String(ml.rate_max / 100) : "",
            available: ml.available !== false,
            social_links_text: ml.social_links ? JSON.stringify(ml.social_links) : ""
          });
        }
      }
    } catch(e) { toast.error("Failed to load"); }
    finally { setLoading(false); }
  }, [search.genre, search.location]);

  useEffect(() => { load(); }, [load]);

  async function saveListing() {
    if (!listForm.artist_name.trim()) return toast.error("Artist name required");
    setSaving(true);
    try {
      await api.post("/band/listings", {
        artist_name: listForm.artist_name,
        bio:         listForm.bio,
        genres:      listForm.genres_text.split(",").map(s => s.trim()).filter(Boolean),
        location:    listForm.location,
        rate_min:    listForm.rate_min ? Math.round(parseFloat(listForm.rate_min) * 100) : null,
        rate_max:    listForm.rate_max ? Math.round(parseFloat(listForm.rate_max) * 100) : null,
        available:   listForm.available,
        social_links: {},
      });
      toast.success(myListing ? "Listing updated!" : "You're on the page!");
      load();
      setTab("browse");
    } catch(e) { toast.error(e?.response?.data?.detail || "Failed"); }
    finally { setSaving(false); }
  }

  async function submitBooking() {
    if (!booking) return;
    if (!bookForm.event_name || !bookForm.event_date || !bookForm.venue_name)
      return toast.error("Event name, date, and venue required");
    setSaving(true);
    try {
      await api.post("/band/book", {
        listing_id:  booking.id,
        event_name:  bookForm.event_name,
        event_date:  bookForm.event_date,
        venue_name:  bookForm.venue_name,
        venue_city:  bookForm.venue_city,
        offer_cents: bookForm.offer ? Math.round(parseFloat(bookForm.offer) * 100) : null,
        message:     bookForm.message,
      });
      toast.success(`Booking request sent to ${booking.artist_name}!`);
      setBooking(null);
      setBookForm({ event_name: "", event_date: "", venue_name: "", venue_city: "", offer: "", message: "" });
      load();
    } catch(e) { toast.error(e?.response?.data?.detail || "Failed"); }
    finally { setSaving(false); }
  }

  async function updateBookingStatus(bookingId, status) {
    try {
      await api.patch(`/band/bookings/${bookingId}/status`, { status });
      toast.success(`Booking ${status}`);
      load();
    } catch(e) { toast.error(e?.response?.data?.detail || "Failed"); }
  }

  const totalBookings = bookings.as_artist.length + bookings.as_requester.length;

  return (
    <AppShell>
      <div style={S.page}>

        {/* Header */}
        <div style={{ marginBottom: "1.75rem" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.3rem" }}>
            <Music2 size={18} color={T.orange} />
            <span style={{ fontSize: "0.7rem", textTransform: "uppercase", letterSpacing: "0.12em", color: T.orange, fontFamily: "Trebuchet MS, sans-serif" }}>Band on Page</span>
          </div>
          <h1 style={{ fontSize: "1.7rem", fontWeight: "bold", color: "#ffe8d0", fontFamily: "Trebuchet MS, sans-serif" }}>
            Live Music Booking
          </h1>
          <p style={{ fontSize: "0.8rem", color: T.muted, marginTop: "0.25rem" }}>
            Artists: get booked. Venues & promoters: book live talent.
          </p>
        </div>

        {/* Tabs */}
        <div style={{ display: "flex", gap: "0.5rem", marginBottom: "1.5rem", flexWrap: "wrap" }}>
          {[["browse","Browse Artists"],["list","My Listing"],["bookings",`Bookings${totalBookings ? ` (${totalBookings})` : ""}`]].map(([t,l]) => (
            <button key={t} onClick={() => setTab(t)} style={{
              ...S.btn,
              background: tab === t ? T.orange : "rgba(249,115,22,0.1)",
              border: `1px solid ${tab === t ? T.orange : T.border}`,
            }}>{l}</button>
          ))}
        </div>

        {/* ── BROWSE ── */}
        {tab === "browse" && (
          <>
            <div style={{ display: "flex", gap: "0.6rem", marginBottom: "1rem", flexWrap: "wrap" }}>
              <input value={search.genre} onChange={e => setSearch(s => ({ ...s, genre: e.target.value }))}
                style={{ ...S.input, maxWidth: 200 }} placeholder="Genre…" />
              <input value={search.location} onChange={e => setSearch(s => ({ ...s, location: e.target.value }))}
                style={{ ...S.input, maxWidth: 200 }} placeholder="City / State…" />
              <button onClick={load} style={{ ...S.btn, padding: "0.5rem 0.7rem", background: "none", border: `1px solid ${T.border}` }}>
                <RefreshCw size={14} color={T.orange} />
              </button>
            </div>

            {loading
              ? <div style={{ color: T.muted, fontSize: "0.85rem" }}>Loading artists…</div>
              : listings.length === 0
                ? <div style={{ ...S.card, textAlign: "center", color: T.muted, padding: "2.5rem" }}>
                    <p>No artists listed yet. Be the first.</p>
                    <button onClick={() => setTab("list")} style={{ ...S.btnGold, marginTop: "1rem" }}>Create My Listing</button>
                  </div>
                : listings.map(l => (
                    <ArtistCard key={l.id} listing={l} currentUserId={user?.id}
                      onBook={() => setBooking(l)} />
                  ))
            }
          </>
        )}

        {/* ── MY LISTING ── */}
        {tab === "list" && (
          <div style={S.card}>
            <h2 style={{ fontSize: "1.05rem", fontWeight: "bold", color: "#ffe8d0", marginBottom: "1rem", fontFamily: "Trebuchet MS, sans-serif" }}>
              {myListing ? "Update Your Listing" : "Create Your Artist Listing"}
            </h2>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem", marginBottom: "0.75rem" }}>
              <div>
                <label style={S.label}>Artist / Band Name *</label>
                <input value={listForm.artist_name} onChange={e => setListForm(f => ({ ...f, artist_name: e.target.value }))} style={S.input} placeholder="Your artist name" />
              </div>
              <div>
                <label style={S.label}>Location</label>
                <input value={listForm.location} onChange={e => setListForm(f => ({ ...f, location: e.target.value }))} style={S.input} placeholder="City, State" />
              </div>
            </div>

            <div style={{ marginBottom: "0.75rem" }}>
              <label style={S.label}>Bio</label>
              <textarea value={listForm.bio} onChange={e => setListForm(f => ({ ...f, bio: e.target.value }))}
                rows={4} style={{ ...S.input, resize: "vertical" }} placeholder="Tell bookers who you are, your sound, your energy…" />
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "0.75rem", marginBottom: "0.75rem" }}>
              <div>
                <label style={S.label}>Genres (comma-separated)</label>
                <input value={listForm.genres_text} onChange={e => setListForm(f => ({ ...f, genres_text: e.target.value }))} style={S.input} placeholder="R&B, Soul, Jazz" />
              </div>
              <div>
                <label style={S.label}>Rate Min ($/show)</label>
                <input type="number" min="0" value={listForm.rate_min} onChange={e => setListForm(f => ({ ...f, rate_min: e.target.value }))} style={S.input} placeholder="500" />
              </div>
              <div>
                <label style={S.label}>Rate Max ($/show)</label>
                <input type="number" min="0" value={listForm.rate_max} onChange={e => setListForm(f => ({ ...f, rate_max: e.target.value }))} style={S.input} placeholder="2000" />
              </div>
            </div>

            <div style={{ display: "flex", alignItems: "center", gap: "1rem", marginBottom: "1rem" }}>
              <label style={{ ...S.label, marginBottom: 0 }}>Available for Bookings:</label>
              <button onClick={() => setListForm(f => ({ ...f, available: !f.available }))} style={{
                background: listForm.available ? "rgba(34,197,94,0.12)" : "rgba(107,100,128,0.1)",
                border: `1px solid ${listForm.available ? "rgba(34,197,94,0.35)" : "rgba(107,100,128,0.25)"}`,
                borderRadius: 8, padding: "0.3rem 0.75rem", cursor: "pointer",
                color: listForm.available ? "#86efac" : T.muted, fontSize: "0.78rem", fontWeight: "bold"
              }}>{listForm.available ? "✓ Available" : "Unavailable"}</button>
            </div>

            <button onClick={saveListing} disabled={saving} style={{ ...S.btnGold, opacity: saving ? 0.5 : 1 }}>
              {saving ? "Saving…" : myListing ? "Update Listing" : "Go Live"}
            </button>
          </div>
        )}

        {/* ── BOOKINGS ── */}
        {tab === "bookings" && (
          <>
            {bookings.as_artist.length > 0 && (
              <>
                <div style={{ fontSize: "0.72rem", color: T.orange, textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: "0.6rem" }}>Requests for You</div>
                {bookings.as_artist.map(b => (
                  <BookingRow key={b.id} booking={b} asArtist onStatus={updateBookingStatus} />
                ))}
              </>
            )}
            {bookings.as_requester.length > 0 && (
              <>
                <div style={{ fontSize: "0.72rem", color: T.gold, textTransform: "uppercase", letterSpacing: "0.1em", margin: "1rem 0 0.6rem" }}>Bookings You've Requested</div>
                {bookings.as_requester.map(b => (
                  <BookingRow key={b.id} booking={b} asArtist={false} onStatus={updateBookingStatus} />
                ))}
              </>
            )}
            {totalBookings === 0 && (
              <div style={{ ...S.card, textAlign: "center", color: T.muted, padding: "2.5rem" }}>
                <p>No bookings yet. Browse artists and send a request.</p>
              </div>
            )}
          </>
        )}

        {/* ── BOOKING MODAL ── */}
        {booking && (
          <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.8)", zIndex: 9000, display: "flex", alignItems: "center", justifyContent: "center" }}>
            <div style={{ ...S.card, width: "min(520px, 92vw)", position: "relative", maxHeight: "90vh", overflowY: "auto" }}>
              <button onClick={() => setBooking(null)} style={{ position: "absolute", top: "0.75rem", right: "0.75rem", background: "none", border: "none", cursor: "pointer", color: T.muted }}>
                <X size={18} />
              </button>
              <h3 style={{ fontFamily: "Trebuchet MS, sans-serif", color: "#ffe8d0", marginBottom: "0.25rem" }}>Book {booking.artist_name}</h3>
              <p style={{ color: T.muted, fontSize: "0.78rem", marginBottom: "1rem" }}>
                {booking.location && <><MapPin size={11} style={{ display: "inline" }} /> {booking.location} · </>}
                {booking.rate_min && fmtCents(booking.rate_min)}{booking.rate_max && ` – ${fmtCents(booking.rate_max)}`}
              </p>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.65rem", marginBottom: "0.65rem" }}>
                <div>
                  <label style={S.label}>Event Name *</label>
                  <input value={bookForm.event_name} onChange={e => setBookForm(f => ({ ...f, event_name: e.target.value }))} style={S.input} placeholder="Summer Fest 2025" />
                </div>
                <div>
                  <label style={S.label}>Date *</label>
                  <input type="date" value={bookForm.event_date} onChange={e => setBookForm(f => ({ ...f, event_date: e.target.value }))} style={S.input} />
                </div>
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.65rem", marginBottom: "0.65rem" }}>
                <div>
                  <label style={S.label}>Venue *</label>
                  <input value={bookForm.venue_name} onChange={e => setBookForm(f => ({ ...f, venue_name: e.target.value }))} style={S.input} placeholder="The Venue Name" />
                </div>
                <div>
                  <label style={S.label}>City</label>
                  <input value={bookForm.venue_city} onChange={e => setBookForm(f => ({ ...f, venue_city: e.target.value }))} style={S.input} placeholder="Atlanta, GA" />
                </div>
              </div>
              <div style={{ marginBottom: "0.65rem" }}>
                <label style={S.label}>Offer ($/show)</label>
                <input type="number" min="0" value={bookForm.offer} onChange={e => setBookForm(f => ({ ...f, offer: e.target.value }))} style={S.input} placeholder="1500" />
              </div>
              <div style={{ marginBottom: "1rem" }}>
                <label style={S.label}>Message to Artist</label>
                <textarea value={bookForm.message} onChange={e => setBookForm(f => ({ ...f, message: e.target.value }))}
                  rows={3} style={{ ...S.input, resize: "vertical" }} placeholder="Tell them about the event, audience, vibe…" />
              </div>
              <div style={{ display: "flex", gap: "0.6rem" }}>
                <button onClick={submitBooking} disabled={saving} style={{ ...S.btnGold, opacity: saving ? 0.5 : 1 }}>
                  {saving ? "Sending…" : "Send Booking Request"}
                </button>
                <button onClick={() => setBooking(null)} style={{ ...S.btn, background: "none", border: `1px solid ${T.border}` }}>Cancel</button>
              </div>
            </div>
          </div>
        )}

      </div>
    </AppShell>
  );
}

function ArtistCard({ listing: l, currentUserId, onBook }) {
  const [expanded, setExpanded] = useState(false);
  const isOwn = l.owner_id === currentUserId;

  return (
    <div style={{ background: "#100a10", border: `1px solid ${l.available ? "rgba(249,115,22,0.2)" : "rgba(107,100,128,0.15)"}`, borderRadius: 14, padding: "1.1rem 1.3rem", marginBottom: "0.8rem" }}>
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: "0.75rem" }}>
        <div style={{ flex: 1 }}>
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", flexWrap: "wrap" }}>
            <span style={{ fontWeight: "bold", fontSize: "0.97rem", color: "#ffe8d0", fontFamily: "Trebuchet MS, sans-serif" }}>{l.artist_name}</span>
            <span style={{ fontSize: "0.7rem", color: l.available ? "#86efac" : "#6b7280", background: l.available ? "rgba(34,197,94,0.1)" : "rgba(107,114,128,0.1)", border: `1px solid ${l.available ? "rgba(34,197,94,0.3)" : "rgba(107,114,128,0.25)"}`, borderRadius: 99, padding: "0.15rem 0.5rem" }}>
              {l.available ? "Available" : "Unavailable"}
            </span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginTop: "0.3rem", flexWrap: "wrap" }}>
            {l.location && <span style={{ fontSize: "0.73rem", color: T.muted, display: "flex", alignItems: "center", gap: 3 }}><MapPin size={10} />{l.location}</span>}
            {(l.rate_min || l.rate_max) && (
              <span style={{ fontSize: "0.73rem", color: "#d4af37", display: "flex", alignItems: "center", gap: 3 }}>
                <DollarSign size={10} />
                {l.rate_min && fmtCents(l.rate_min)}{l.rate_min && l.rate_max && " – "}{l.rate_max && fmtCents(l.rate_max)}{l.rate_min || l.rate_max ? "/show" : ""}
              </span>
            )}
          </div>
          {l.genres?.length > 0 && (
            <div style={{ marginTop: "0.35rem" }}>
              {l.genres.map(g => <span key={g} style={{ display: "inline-block", background: "rgba(249,115,22,0.1)", border: "1px solid rgba(249,115,22,0.25)", borderRadius: 99, padding: "0.15rem 0.5rem", fontSize: "0.68rem", color: "#fdba74", marginRight: "0.3rem" }}>{g}</span>)}
            </div>
          )}
        </div>
        <div style={{ display: "flex", gap: "0.4rem", flexShrink: 0 }}>
          {!isOwn && l.available && (
            <button onClick={onBook} style={{ ...S.btnGold, padding: "0.38rem 0.9rem", fontSize: "0.75rem" }}>
              <Calendar size={12} style={{ display: "inline", marginRight: 4 }} />Book
            </button>
          )}
          <button onClick={() => setExpanded(v => !v)} style={{ background: "none", border: "1px solid rgba(249,115,22,0.15)", borderRadius: 8, padding: "0.38rem 0.55rem", cursor: "pointer", color: T.muted }}>
            ▾
          </button>
        </div>
      </div>
      {expanded && l.bio && (
        <p style={{ fontSize: "0.8rem", color: "#c8b8a8", marginTop: "0.7rem", lineHeight: 1.65, whiteSpace: "pre-wrap" }}>{l.bio}</p>
      )}
    </div>
  );
}

function BookingRow({ booking: b, asArtist, onStatus }) {
  const st = STATUS_STYLE[b.status] || STATUS_STYLE.pending;
  const Icon = st.icon;
  return (
    <div style={{ background: "#100a10", border: `1px solid ${st.border}`, borderRadius: 12, padding: "0.9rem 1.1rem", marginBottom: "0.6rem" }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "0.75rem", flexWrap: "wrap" }}>
        <div>
          <div style={{ fontWeight: "bold", fontSize: "0.9rem", color: "#ffe8d0" }}>{b.event_name}</div>
          <div style={{ fontSize: "0.73rem", color: T.muted, marginTop: "0.2rem" }}>
            {asArtist ? `from ${b.requester_name}` : `for ${b.artist_name}`} · {b.venue_name}{b.venue_city ? `, ${b.venue_city}` : ""} · {b.event_date}
            {b.offer_cents ? <span style={{ color: "#d4af37", marginLeft: 8 }}>{fmtCents(b.offer_cents)}</span> : null}
          </div>
          {b.message && <div style={{ fontSize: "0.73rem", color: T.muted, marginTop: "0.2rem", fontStyle: "italic" }}>"{b.message.slice(0, 80)}{b.message.length > 80 ? "…" : ""}"</div>}
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <span style={{ background: st.bg, border: `1px solid ${st.border}`, borderRadius: 99, padding: "0.2rem 0.65rem", fontSize: "0.7rem", color: st.color, display: "flex", alignItems: "center", gap: 4 }}>
            <Icon size={10} />{b.status}
          </span>
          {asArtist && b.status === "pending" && (
            <>
              <button onClick={() => onStatus(b.id, "accepted")} style={{ background: "rgba(34,197,94,0.12)", border: "1px solid rgba(34,197,94,0.3)", borderRadius: 7, padding: "0.28rem 0.65rem", fontSize: "0.72rem", color: "#86efac", cursor: "pointer", fontWeight: "bold" }}>Accept</button>
              <button onClick={() => onStatus(b.id, "declined")} style={{ background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.25)", borderRadius: 7, padding: "0.28rem 0.65rem", fontSize: "0.72rem", color: "#fca5a5", cursor: "pointer" }}>Decline</button>
            </>
          )}
          {!asArtist && b.status === "pending" && (
            <button onClick={() => onStatus(b.id, "cancelled")} style={{ background: "rgba(107,114,128,0.1)", border: "1px solid rgba(107,114,128,0.25)", borderRadius: 7, padding: "0.28rem 0.65rem", fontSize: "0.72rem", color: "#9ca3af", cursor: "pointer" }}>Cancel</button>
          )}
        </div>
      </div>
    </div>
  );
}
