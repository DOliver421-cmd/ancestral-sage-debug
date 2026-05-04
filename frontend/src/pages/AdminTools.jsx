import { useEffect, useState } from "react";
import AppShell from "../components/AppShell";
import { api } from "../lib/api";
import { toast } from "sonner";
import { Building2, Boxes, ArrowDownToLine, ArrowUpFromLine, Plus } from "lucide-react";

export default function AdminTools() {
  const [tab, setTab] = useState("sites");
  const [sites, setSites] = useState([]);
  const [inv, setInv] = useState([]);
  const [users, setUsers] = useState([]);
  const [checkouts, setCheckouts] = useState([]);

  const load = () => {
    api.get("/admin/sites").then((r) => setSites(r.data));
    api.get("/admin/inventory").then((r) => setInv(r.data));
    api.get("/admin/users").then((r) => setUsers(r.data.filter((u) => u.role === "student")));
    api.get("/admin/checkouts").then((r) => setCheckouts(r.data));
  };
  useEffect(() => { load(); /* eslint-disable-next-line react-hooks/exhaustive-deps */ }, []);

  return (
    <AppShell>
      <div className="px-10 py-10 max-w-6xl">
        <div className="overline text-copper">Program-Level Admin</div>
        <h1 className="font-heading text-4xl font-bold mt-2">Sites · Inventory · Tool Checkout</h1>
        <p className="text-ink/60 mt-2">Multi-site deployment, equipment inventory, and student tool checkout — one place.</p>

        <div className="flex gap-2 mt-8 flex-wrap" data-testid="admin-tabs">
          {[["sites", "Sites", Building2], ["inventory", "Inventory", Boxes], ["checkout", "Checkout", ArrowDownToLine]].map(([k, label, Icon]) => (
            <button key={k} onClick={() => setTab(k)}
              className={`flex items-center gap-2 px-5 py-3 text-sm font-bold uppercase tracking-widest border ${tab === k ? "bg-ink text-white border-ink" : "bg-white text-ink border-ink/20 hover:border-ink"}`}
              data-testid={`admin-tab-${k}`}>
              <Icon className="w-4 h-4" /> {label}
            </button>
          ))}
        </div>

        {tab === "sites" && <SitesPanel sites={sites} onChange={load} />}
        {tab === "inventory" && <InventoryPanel inv={inv} sites={sites} onChange={load} />}
        {tab === "checkout" && <CheckoutPanel inv={inv} users={users} checkouts={checkouts} onChange={load} />}
      </div>
    </AppShell>
  );
}

function SitesPanel({ sites, onChange }) {
  const [form, setForm] = useState({ slug: "", name: "", address: "", capacity: 0 });
  const create = async () => {
    if (!form.slug || !form.name) { toast.error("Slug + name required"); return; }
    try { await api.post("/admin/sites", form); toast.success("Site created"); setForm({ slug: "", name: "", address: "", capacity: 0 }); onChange(); }
    catch (e) { toast.error(e?.response?.data?.detail || "Failed"); }
  };
  return (
    <div className="mt-6 space-y-6">
      <div className="card-flat p-6">
        <h3 className="font-heading text-xl font-bold mb-4">All Sites ({sites.length})</h3>
        <div className="grid md:grid-cols-3 gap-4" data-testid="sites-grid">
          {sites.map((s) => (
            <div key={s.id} className="p-4 border border-ink/10 bg-bone" data-testid={`site-${s.slug}`}>
              <div className="overline text-copper">{s.slug}</div>
              <div className="font-heading font-bold mt-1">{s.name}</div>
              <div className="text-xs text-ink/60 mt-1">{s.address}</div>
              <div className="overline text-ink/60 mt-2">Capacity: {s.capacity}</div>
            </div>
          ))}
        </div>
      </div>
      <div className="card-flat p-6">
        <h3 className="font-heading text-xl font-bold mb-4 flex items-center gap-2"><Plus className="w-5 h-5 text-copper" /> New Site</h3>
        <div className="grid sm:grid-cols-2 gap-3">
          <Input label="Slug" value={form.slug} onChange={(v) => setForm({ ...form, slug: v })} testid="site-slug" />
          <Input label="Name" value={form.name} onChange={(v) => setForm({ ...form, name: v })} testid="site-name" />
          <Input label="Address" value={form.address} onChange={(v) => setForm({ ...form, address: v })} testid="site-address" />
          <Input label="Capacity" type="number" value={form.capacity} onChange={(v) => setForm({ ...form, capacity: parseInt(v) || 0 })} testid="site-capacity" />
        </div>
        <button onClick={create} className="btn-primary mt-4" data-testid="btn-create-site">Create Site</button>
      </div>
    </div>
  );
}

function InventoryPanel({ inv, sites, onChange }) {
  const [filter, setFilter] = useState("");
  const filtered = filter ? inv.filter((i) => i.site_slug === filter) : inv;
  return (
    <div className="mt-6 card-flat p-6" data-testid="inventory-table">
      <div className="flex items-center justify-between mb-4 flex-wrap gap-3">
        <h3 className="font-heading text-xl font-bold">Inventory ({filtered.length})</h3>
        <select value={filter} onChange={(e) => setFilter(e.target.value)}
          className="px-3 py-2 border border-ink/20 text-sm" data-testid="inv-filter-site">
          <option value="">All sites</option>
          {sites.map((s) => <option key={s.slug} value={s.slug}>{s.name}</option>)}
        </select>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-ink text-white">
            <tr><Th>SKU</Th><Th>Name</Th><Th>Category</Th><Th>Site</Th><Th>Avail / Total</Th></tr>
          </thead>
          <tbody>
            {filtered.map((i) => (
              <tr key={i.id} className="border-b border-ink/10 hover:bg-bone" data-testid={`inv-${i.sku}`}>
                <Td><span className="font-mono text-xs">{i.sku}</span></Td>
                <Td><span className="font-heading font-bold">{i.name}</span></Td>
                <Td><span className="badge-outline">{i.category}</span></Td>
                <Td>{i.site_slug}</Td>
                <Td><span className={`font-mono ${i.quantity_available === 0 ? "text-destructive" : "text-ink"}`}>{i.quantity_available} / {i.quantity_total}</span></Td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function CheckoutPanel({ inv, users, checkouts, onChange }) {
  const [sku, setSku] = useState("");
  const [userId, setUserId] = useState("");
  const [qty, setQty] = useState(1);

  const checkout = async () => {
    if (!sku || !userId) { toast.error("Pick item and student"); return; }
    try { await api.post("/admin/checkout", { sku, user_id: userId, quantity: qty }); toast.success("Checked out"); onChange(); }
    catch (e) { toast.error(e?.response?.data?.detail || "Failed"); }
  };
  const returnTool = async (id) => {
    try { await api.post(`/admin/checkout/${id}/return`, {}); toast.success("Returned"); onChange(); }
    catch { toast.error("Return failed"); }
  };

  return (
    <div className="mt-6 space-y-6">
      <div className="card-flat p-6">
        <h3 className="font-heading text-xl font-bold mb-4 flex items-center gap-2"><ArrowDownToLine className="w-5 h-5 text-copper" /> New Checkout</h3>
        <div className="grid sm:grid-cols-3 gap-3">
          <select value={sku} onChange={(e) => setSku(e.target.value)} className="px-3 py-2 border border-ink/20 text-sm" data-testid="co-sku">
            <option value="">Select item</option>
            {inv.filter((i) => i.quantity_available > 0).map((i) => <option key={i.sku} value={i.sku}>{i.sku} — {i.name} ({i.quantity_available})</option>)}
          </select>
          <select value={userId} onChange={(e) => setUserId(e.target.value)} className="px-3 py-2 border border-ink/20 text-sm" data-testid="co-user">
            <option value="">Select student</option>
            {users.map((u) => <option key={u.id} value={u.id}>{u.full_name}</option>)}
          </select>
          <Input label="Qty" type="number" value={qty} onChange={(v) => setQty(parseInt(v) || 1)} testid="co-qty" />
        </div>
        <button onClick={checkout} className="btn-primary mt-4" data-testid="btn-checkout">Check Out</button>
      </div>

      <div className="card-flat p-6 overflow-x-auto" data-testid="checkout-table">
        <h3 className="font-heading text-xl font-bold mb-4">Active & Recent ({checkouts.length})</h3>
        <table className="w-full text-sm">
          <thead className="bg-ink text-white">
            <tr><Th>Item</Th><Th>Student</Th><Th>Qty</Th><Th>Checked Out</Th><Th>Status</Th><Th></Th></tr>
          </thead>
          <tbody>
            {checkouts.length === 0 && <tr><td colSpan={6} className="p-6 text-center text-ink/50">No checkouts yet.</td></tr>}
            {checkouts.map((c) => (
              <tr key={c.id} className="border-b border-ink/10" data-testid={`co-${c.id}`}>
                <Td><span className="font-heading font-bold">{c.item?.name}</span><div className="text-xs text-ink/50 font-mono">{c.sku}</div></Td>
                <Td>{c.user?.full_name}</Td>
                <Td>{c.quantity}</Td>
                <Td>{new Date(c.checked_out_at).toLocaleDateString()}</Td>
                <Td><span className={c.status === "out" ? "badge-copper" : "badge-signal"}>{c.status}</span></Td>
                <Td>{c.status === "out" && (
                  <button onClick={() => returnTool(c.id)} className="text-xs font-bold uppercase text-copper hover:underline inline-flex items-center gap-1" data-testid={`return-${c.id}`}>
                    <ArrowUpFromLine className="w-3 h-3" /> Return
                  </button>
                )}</Td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function Input({ label, value, onChange, type = "text", testid }) {
  return (
    <label className="block">
      <span className="overline text-ink/60">{label}</span>
      <input type={type} value={value} onChange={(e) => onChange(e.target.value)}
        className="w-full mt-1 px-3 py-2 bg-white border border-ink/20 focus:border-ink focus:outline-none focus:ring-2 focus:ring-signal text-sm"
        data-testid={testid} />
    </label>
  );
}
const Th = ({ children }) => <th className="text-left px-3 py-2 overline text-xs">{children}</th>;
const Td = ({ children }) => <td className="px-3 py-2">{children}</td>;
