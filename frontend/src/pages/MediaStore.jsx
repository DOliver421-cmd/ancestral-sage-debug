import { useState, useEffect, useRef } from "react";
import { useSearchParams, Link } from "react-router-dom";
import AppShell from "../components/AppShell";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import { toast } from "sonner";
import {
  Music, FileText, Package, PlayCircle, Upload, ShoppingBag,
  Library, Plus, Trash2, Eye, EyeOff, CheckCircle2, Loader2,
  Download, RefreshCw, Tag,
} from "lucide-react";

const TYPE_LABELS = {
  track: "Track",
  album: "Album",
  pdf: "PDF",
  bundle: "Bundle",
  other: "File",
  video: "Video",
};

const TYPE_COLORS = {
  track: "bg-amber-100 text-amber-800",
  album: "bg-emerald-100 text-emerald-800",
  pdf: "bg-blue-100 text-blue-800",
  bundle: "bg-purple-100 text-purple-800",
  video: "bg-rose-100 text-rose-800",
  other: "bg-gray-100 text-gray-600",
};

function TypeBadge({ type }) {
  const cls = TYPE_COLORS[type] || TYPE_COLORS.other;
  return (
    <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${cls}`}>
      {TYPE_LABELS[type] || type}
    </span>
  );
}

function formatPrice(cents) {
  if (!cents || cents === 0) return "Free";
  return `$${(cents / 100).toFixed(2)}`;
}

function formatBytes(bytes) {
  if (!bytes) return "";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

// ── Browse Tab ────────────────────────────────────────────────────────────────
function BrowseTab({ user }) {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("all");
  const [checkingOut, setCheckingOut] = useState(null);

  useEffect(() => {
    api.get("/media/products")
      .then(r => setProducts(r.data))
      .catch(() => toast.error("Failed to load store"))
      .finally(() => setLoading(false));
  }, []);

  async function handleBuy(product) {
    if (!user) { toast.error("Sign in to purchase"); return; }
    setCheckingOut(product.id);
    try {
      const r = await api.post(`/media/products/${product.id}/checkout`);
      window.location.href = r.data.checkout_url;
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Checkout failed");
      setCheckingOut(null);
    }
  }

  async function handleFreeDownload(product) {
    if (!user) { toast.error("Sign in to download"); return; }
    try {
      const r = await api.get(`/media/products/${product.id}/download`, { responseType: "blob" });
      const url = URL.createObjectURL(r.data);
      const a = document.createElement("a");
      a.href = url;
      a.download = product.title;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      toast.error("Download failed");
    }
  }

  const filters = ["all", "track", "album", "pdf", "bundle"];
  const shown = filter === "all" ? products : products.filter(p => p.product_type === filter);

  if (loading) return (
    <div className="flex justify-center py-20">
      <Loader2 className="animate-spin text-[#b5651d]" size={32} />
    </div>
  );

  return (
    <div>
      {/* Filter chips */}
      <div className="flex gap-2 flex-wrap mb-6">
        {filters.map(f => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-4 py-1.5 rounded-full text-sm font-medium border transition-all ${
              filter === f
                ? "bg-[#b5651d] text-white border-[#b5651d]"
                : "border-[#b5651d]/30 text-[#b5651d] hover:border-[#b5651d]"
            }`}
          >
            {f === "all" ? "All" : TYPE_LABELS[f]}
          </button>
        ))}
      </div>

      {shown.length === 0 && (
        <div className="text-center py-16 text-[#1a1a1a]/50">
          <ShoppingBag size={48} className="mx-auto mb-3 opacity-30" />
          <p>No products available yet.</p>
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {shown.map(product => (
          <div
            key={product.id}
            className="bg-white rounded-xl border border-[#b5651d]/15 shadow-sm hover:shadow-md transition-shadow overflow-hidden flex flex-col"
          >
            {/* Cover */}
            <div className="aspect-square relative overflow-hidden bg-gradient-to-br from-[#b5651d]/20 to-[#1a1a1a]/10">
              {product.cover_url ? (
                <img
                  src={product.cover_url}
                  alt={product.title}
                  className="w-full h-full object-cover"
                  onError={e => { e.target.style.display = "none"; }}
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center">
                  <Music size={48} className="text-[#b5651d]/40" />
                </div>
              )}
              <div className="absolute top-2 left-2">
                <TypeBadge type={product.product_type} />
              </div>
            </div>

            {/* Info */}
            <div className="p-4 flex-1 flex flex-col">
              <h3 className="font-bold text-[#1a1a1a] text-base mb-1 line-clamp-2">{product.title}</h3>
              {product.description && (
                <p className="text-[#1a1a1a]/60 text-sm mb-2 line-clamp-2">{product.description}</p>
              )}
              <p className="text-xs text-[#1a1a1a]/40 mb-3">by {product.seller_display_name}</p>

              <div className="mt-auto flex items-center justify-between">
                <span className="font-bold text-[#b5651d] text-lg">
                  {formatPrice(product.price_cents)}
                </span>
                {product.price_cents > 0 ? (
                  <button
                    onClick={() => handleBuy(product)}
                    disabled={checkingOut === product.id}
                    className="flex items-center gap-1.5 bg-[#b5651d] text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-[#9a5418] transition-colors disabled:opacity-60"
                  >
                    {checkingOut === product.id ? <Loader2 size={14} className="animate-spin" /> : <ShoppingBag size={14} />}
                    Buy
                  </button>
                ) : (
                  <button
                    onClick={() => handleFreeDownload(product)}
                    className="flex items-center gap-1.5 bg-emerald-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-emerald-700 transition-colors"
                  >
                    <Download size={14} />
                    Free
                  </button>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Library Tab ───────────────────────────────────────────────────────────────
function LibraryTab({ user }) {
  const [purchases, setPurchases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [downloading, setDownloading] = useState(null);

  useEffect(() => {
    if (!user) return;
    api.get("/media/purchases")
      .then(r => setPurchases(r.data))
      .catch(() => toast.error("Failed to load library"))
      .finally(() => setLoading(false));
  }, [user]);

  async function handleDownload(purchase) {
    setDownloading(purchase.id);
    try {
      const r = await api.get(`/media/products/${purchase.product_id}/download`, { responseType: "blob" });
      const url = URL.createObjectURL(r.data);
      const a = document.createElement("a");
      a.href = url;
      a.download = purchase.product?.title || "download";
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      toast.error("Download failed");
    } finally {
      setDownloading(null);
    }
  }

  if (!user) return (
    <div className="text-center py-16 text-[#1a1a1a]/50">
      <Library size={48} className="mx-auto mb-3 opacity-30" />
      <p>Sign in to view your library.</p>
      <Link to="/login" className="mt-3 inline-block text-[#b5651d] underline">Sign in</Link>
    </div>
  );

  if (loading) return (
    <div className="flex justify-center py-20">
      <Loader2 className="animate-spin text-[#b5651d]" size={32} />
    </div>
  );

  if (purchases.length === 0) return (
    <div className="text-center py-16 text-[#1a1a1a]/50">
      <Library size={48} className="mx-auto mb-3 opacity-30" />
      <p>No purchases yet.</p>
      <Link to="/store" className="mt-3 inline-block text-[#b5651d] underline">Browse the store</Link>
    </div>
  );

  return (
    <div className="space-y-3">
      {purchases.map(p => {
        const prod = p.product;
        return (
          <div key={p.id} className="bg-white rounded-xl border border-[#b5651d]/15 p-4 flex items-center gap-4">
            <div className="w-14 h-14 rounded-lg bg-gradient-to-br from-[#b5651d]/20 to-[#1a1a1a]/10 flex items-center justify-center flex-shrink-0">
              {prod?.cover_url
                ? <img src={prod.cover_url} alt="" className="w-full h-full object-cover rounded-lg" />
                : <Music size={22} className="text-[#b5651d]/50" />
              }
            </div>
            <div className="flex-1 min-w-0">
              <p className="font-semibold text-[#1a1a1a] truncate">{prod?.title || "Unknown product"}</p>
              <div className="flex items-center gap-2 mt-0.5">
                {prod && <TypeBadge type={prod.product_type} />}
                <span className="text-xs text-[#1a1a1a]/40">
                  {new Date(p.created_at).toLocaleDateString()}
                </span>
              </div>
            </div>
            {prod?.file_id && (
              <button
                onClick={() => handleDownload(p)}
                disabled={downloading === p.id}
                className="flex items-center gap-1.5 bg-[#b5651d] text-white px-3 py-1.5 rounded-lg text-sm font-medium hover:bg-[#9a5418] transition-colors disabled:opacity-60"
              >
                {downloading === p.id ? <Loader2 size={13} className="animate-spin" /> : <Download size={13} />}
                Download
              </button>
            )}
          </div>
        );
      })}
    </div>
  );
}

// ── Sell Tab ──────────────────────────────────────────────────────────────────
function SellTab({ user }) {
  const [step, setStep] = useState(1); // 1=upload, 2=listing
  const [uploadedFile, setUploadedFile] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploading, setUploading] = useState(false);
  const [myProducts, setMyProducts] = useState([]);
  const [loadingProducts, setLoadingProducts] = useState(true);
  const [confirmDeleteProduct, setConfirmDeleteProduct] = useState(null);
  const [form, setForm] = useState({
    title: "", description: "", price: "", cover_url: "",
    product_type: "track", published: false,
  });
  const [saving, setSaving] = useState(false);
  const fileRef = useRef();

  useEffect(() => {
    if (!user) return;
    fetchMyProducts();
  }, [user]);

  async function fetchMyProducts() {
    try {
      const r = await api.get("/media/products/mine");
      setMyProducts(r.data);
    } catch { } finally {
      setLoadingProducts(false);
    }
  }

  async function handleFileUpload(e) {
    const file = e.target.files[0];
    if (!file) return;
    if (file.size > 500 * 1024 * 1024) {
      toast.error("File too large (max 500 MB)");
      return;
    }
    setUploading(true);
    setUploadProgress(0);
    const fd = new FormData();
    fd.append("file", file);
    fd.append("title", file.name);
    fd.append("description", "");
    fd.append("file_type", "other");
    fd.append("is_public", "false");
    try {
      const r = await api.post("/media/upload", fd, {
        headers: { "Content-Type": "multipart/form-data" },
        onUploadProgress: (ev) => {
          setUploadProgress(Math.round((ev.loaded / ev.total) * 100));
        },
      });
      setUploadedFile(r.data);
      setForm(f => ({ ...f, title: r.data.title || file.name }));
      toast.success("File uploaded!");
      setStep(2);
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Upload failed");
    } finally {
      setUploading(false);
    }
  }

  async function handleSave(publish) {
    if (!form.title) { toast.error("Title required"); return; }
    setSaving(true);
    try {
      const payload = {
        title: form.title,
        description: form.description,
        price_cents: Math.round(parseFloat(form.price || "0") * 100),
        cover_url: form.cover_url || null,
        product_type: form.product_type,
        file_id: uploadedFile?.id || null,
        published: publish,
      };
      await api.post("/media/products", payload);
      toast.success(publish ? "Published!" : "Saved as draft");
      setStep(1);
      setUploadedFile(null);
      setForm({ title: "", description: "", price: "", cover_url: "", product_type: "track", published: false });
      fetchMyProducts();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Save failed");
    } finally {
      setSaving(false);
    }
  }

  async function togglePublish(product) {
    try {
      await api.patch(`/media/products/${product.id}`, { published: !product.published });
      fetchMyProducts();
    } catch { toast.error("Update failed"); }
  }

  async function handleDelete(product) {
    setConfirmDeleteProduct(product);
  }

  async function doDeleteProduct() {
    const product = confirmDeleteProduct;
    setConfirmDeleteProduct(null);
    try {
      await api.delete(`/media/products/${product.id}`);
      fetchMyProducts();
      toast.success("Deleted");
    } catch { toast.error("Delete failed"); }
  }

  if (!user) return (
    <div className="text-center py-16 text-[#1a1a1a]/50">
      <Upload size={48} className="mx-auto mb-3 opacity-30" />
      <p>Sign in to sell your music.</p>
      <Link to="/login" className="mt-3 inline-block text-[#b5651d] underline">Sign in</Link>
    </div>
  );

  return (
    <div className="max-w-2xl mx-auto space-y-8">
      {/* Upload Form */}
      <div className="bg-white rounded-xl border border-[#b5651d]/15 shadow-sm overflow-hidden">
        {/* Steps header */}
        <div className="bg-[#f5f0e8] border-b border-[#b5651d]/10 px-6 py-4 flex gap-6">
          {[1, 2].map(s => (
            <button
              key={s}
              onClick={() => s < step || uploadedFile ? setStep(s) : null}
              className={`flex items-center gap-2 text-sm font-medium transition-colors ${
                step === s ? "text-[#b5651d]" : "text-[#1a1a1a]/40"
              }`}
            >
              <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                step >= s ? "bg-[#b5651d] text-white" : "bg-[#1a1a1a]/10 text-[#1a1a1a]/40"
              }`}>{s}</span>
              {s === 1 ? "Upload File" : "Create Listing"}
            </button>
          ))}
        </div>

        <div className="p-6">
          {step === 1 && (
            <div>
              <p className="text-[#1a1a1a]/60 text-sm mb-4">Upload a track, album, PDF, or any file. Max 500 MB.</p>
              {uploading ? (
                <div className="space-y-3">
                  <div className="flex items-center gap-3">
                    <Loader2 className="animate-spin text-[#b5651d]" size={20} />
                    <span className="text-sm text-[#1a1a1a]/70">Uploading… {uploadProgress}%</span>
                  </div>
                  <div className="w-full bg-[#b5651d]/10 rounded-full h-2">
                    <div
                      className="bg-[#b5651d] h-2 rounded-full transition-all"
                      style={{ width: `${uploadProgress}%` }}
                    />
                  </div>
                </div>
              ) : (
                <label className="block cursor-pointer border-2 border-dashed border-[#b5651d]/30 rounded-xl p-10 text-center hover:border-[#b5651d]/60 transition-colors">
                  <Upload size={32} className="mx-auto mb-3 text-[#b5651d]/50" />
                  <p className="text-[#1a1a1a]/70 font-medium">Click to choose a file</p>
                  <p className="text-[#1a1a1a]/40 text-sm mt-1">Audio, PDF, ZIP, video — any format</p>
                  <input ref={fileRef} type="file" className="hidden" onChange={handleFileUpload} />
                </label>
              )}
              {uploadedFile && (
                <div className="mt-3 flex items-center gap-2 text-emerald-700 text-sm">
                  <CheckCircle2 size={16} />
                  <span>{uploadedFile.original_filename} ({formatBytes(uploadedFile.size_bytes)}) — uploaded</span>
                  <button onClick={() => setStep(2)} className="ml-auto text-[#b5651d] font-medium hover:underline">
                    Create listing →
                  </button>
                </div>
              )}
            </div>
          )}

          {step === 2 && (
            <div className="space-y-4">
              {uploadedFile && (
                <div className="flex items-center gap-2 text-emerald-700 text-sm bg-emerald-50 rounded-lg px-3 py-2">
                  <CheckCircle2 size={15} />
                  <span>{uploadedFile.original_filename} ({formatBytes(uploadedFile.size_bytes)})</span>
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-[#1a1a1a]/70 mb-1">Title *</label>
                <input
                  type="text"
                  value={form.title}
                  onChange={e => setForm(f => ({ ...f, title: e.target.value }))}
                  className="w-full border border-[#b5651d]/20 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#b5651d]"
                  placeholder="Track or album title"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-[#1a1a1a]/70 mb-1">Description</label>
                <textarea
                  value={form.description}
                  onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
                  rows={2}
                  className="w-full border border-[#b5651d]/20 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#b5651d] resize-none"
                  placeholder="Tell people about this release…"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-[#1a1a1a]/70 mb-1">Price (USD)</label>
                  <div className="relative">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-[#1a1a1a]/40 text-sm">$</span>
                    <input
                      type="number"
                      min="0"
                      step="0.01"
                      value={form.price}
                      onChange={e => setForm(f => ({ ...f, price: e.target.value }))}
                      className="w-full border border-[#b5651d]/20 rounded-lg pl-7 pr-3 py-2 text-sm focus:outline-none focus:border-[#b5651d]"
                      placeholder="0.00"
                    />
                  </div>
                  <p className="text-xs text-[#1a1a1a]/40 mt-0.5">Leave 0 for free</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-[#1a1a1a]/70 mb-1">Type</label>
                  <select
                    value={form.product_type}
                    onChange={e => setForm(f => ({ ...f, product_type: e.target.value }))}
                    className="w-full border border-[#b5651d]/20 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#b5651d] bg-white"
                  >
                    <option value="track">Track</option>
                    <option value="album">Album</option>
                    <option value="bundle">Bundle</option>
                    <option value="pdf">PDF</option>
                    <option value="video">Video</option>
                    <option value="other">Other</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-[#1a1a1a]/70 mb-1">Cover Image URL (optional)</label>
                <input
                  type="url"
                  value={form.cover_url}
                  onChange={e => setForm(f => ({ ...f, cover_url: e.target.value }))}
                  className="w-full border border-[#b5651d]/20 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#b5651d]"
                  placeholder="https://…"
                />
              </div>

              <div className="flex gap-3 pt-2">
                <button
                  onClick={() => handleSave(false)}
                  disabled={saving}
                  className="flex-1 border border-[#b5651d] text-[#b5651d] py-2 rounded-lg text-sm font-medium hover:bg-[#b5651d]/5 transition-colors disabled:opacity-60"
                >
                  {saving ? <Loader2 size={14} className="animate-spin mx-auto" /> : "Save as Draft"}
                </button>
                <button
                  onClick={() => handleSave(true)}
                  disabled={saving}
                  className="flex-1 bg-[#b5651d] text-white py-2 rounded-lg text-sm font-medium hover:bg-[#9a5418] transition-colors disabled:opacity-60"
                >
                  {saving ? <Loader2 size={14} className="animate-spin mx-auto" /> : "Publish Now"}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* My products table */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-bold text-[#1a1a1a] text-base">My Products</h3>
          <button onClick={fetchMyProducts} className="text-[#1a1a1a]/40 hover:text-[#b5651d] transition-colors">
            <RefreshCw size={15} />
          </button>
        </div>

        {loadingProducts ? (
          <div className="flex justify-center py-8"><Loader2 className="animate-spin text-[#b5651d]" size={24} /></div>
        ) : myProducts.length === 0 ? (
          <p className="text-[#1a1a1a]/40 text-sm text-center py-8">No products yet. Create your first listing above.</p>
        ) : (
          <div className="bg-white rounded-xl border border-[#b5651d]/15 overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-[#f5f0e8] border-b border-[#b5651d]/10">
                <tr>
                  <th className="text-left px-4 py-2.5 font-semibold text-[#1a1a1a]/70">Title</th>
                  <th className="text-left px-4 py-2.5 font-semibold text-[#1a1a1a]/70 hidden sm:table-cell">Type</th>
                  <th className="text-left px-4 py-2.5 font-semibold text-[#1a1a1a]/70 hidden sm:table-cell">Price</th>
                  <th className="text-center px-4 py-2.5 font-semibold text-[#1a1a1a]/70">Published</th>
                  <th className="text-center px-4 py-2.5 font-semibold text-[#1a1a1a]/70 hidden sm:table-cell">Sales</th>
                  <th className="px-4 py-2.5" />
                </tr>
              </thead>
              <tbody className="divide-y divide-[#b5651d]/5">
                {myProducts.map(prod => (
                  <tr key={prod.id} className="hover:bg-[#f5f0e8]/50 transition-colors">
                    <td className="px-4 py-3 font-medium text-[#1a1a1a] max-w-[200px] truncate">{prod.title}</td>
                    <td className="px-4 py-3 hidden sm:table-cell">
                      <TypeBadge type={prod.product_type} />
                    </td>
                    <td className="px-4 py-3 hidden sm:table-cell text-[#1a1a1a]/70">{formatPrice(prod.price_cents)}</td>
                    <td className="px-4 py-3 text-center">
                      <button
                        onClick={() => togglePublish(prod)}
                        className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium transition-colors ${
                          prod.published
                            ? "bg-emerald-100 text-emerald-700 hover:bg-emerald-200"
                            : "bg-[#1a1a1a]/5 text-[#1a1a1a]/50 hover:bg-[#1a1a1a]/10"
                        }`}
                      >
                        {prod.published ? <Eye size={11} /> : <EyeOff size={11} />}
                        {prod.published ? "Live" : "Draft"}
                      </button>
                    </td>
                    <td className="px-4 py-3 text-center text-[#1a1a1a]/50 hidden sm:table-cell">
                      {prod.sales_count ?? 0}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() => handleDelete(prod)}
                        className="text-[#1a1a1a]/30 hover:text-red-500 transition-colors"
                      >
                        <Trash2 size={14} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {confirmDeleteProduct && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-sm p-6">
            <h2 className="font-heading font-bold text-lg text-slate-900 mb-2">Delete Product</h2>
            <p className="text-sm text-slate-600 mb-6">Delete &ldquo;{confirmDeleteProduct.title}&rdquo;? This cannot be undone.</p>
            <div className="flex justify-end gap-3">
              <button onClick={() => setConfirmDeleteProduct(null)} className="text-sm px-4 py-2 rounded-lg text-slate-600 hover:bg-slate-50">Cancel</button>
              <button onClick={doDeleteProduct} className="text-sm px-4 py-2 rounded-lg bg-red-600 text-white font-bold hover:bg-red-700">Delete</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Main MediaStore Page ───────────────────────────────────────────────────────
export default function MediaStore() {
  const [searchParams, setSearchParams] = useSearchParams();
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState("browse");
  const success = searchParams.get("success") || searchParams.get("session_id");

  const tabs = [
    { id: "browse", label: "Browse", icon: ShoppingBag },
    { id: "library", label: "My Library", icon: Library },
    { id: "sell", label: "Sell", icon: Upload },
  ];

  return (
    <AppShell>
      <div className="min-h-screen bg-[#f5f0e8]">
        {/* Header */}
        <div className="bg-white border-b border-[#b5651d]/15 px-4 py-6">
          <div className="max-w-5xl mx-auto">
            <div className="flex items-center gap-3 mb-1">
              <Music size={22} className="text-[#b5651d]" />
              <h1 className="text-2xl font-bold text-[#1a1a1a]">Store</h1>
            </div>
            <p className="text-[#1a1a1a]/50 text-sm">Music, albums, PDFs — directly from the creator</p>
          </div>
        </div>

        {/* Success banner */}
        {success && (
          <div className="bg-emerald-50 border-b border-emerald-200 px-4 py-3">
            <div className="max-w-5xl mx-auto flex items-center gap-2 text-emerald-800 text-sm">
              <CheckCircle2 size={16} />
              <span>Purchase complete! Check your </span>
              <button
                onClick={() => setActiveTab("library")}
                className="font-semibold underline"
              >library</button>.
            </div>
          </div>
        )}

        {/* Tab bar */}
        <div className="bg-white border-b border-[#b5651d]/10 sticky top-0 z-10">
          <div className="max-w-5xl mx-auto px-4">
            <div className="flex gap-0">
              {tabs.map(tab => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-2 px-5 py-3.5 text-sm font-medium border-b-2 transition-all ${
                    activeTab === tab.id
                      ? "border-[#b5651d] text-[#b5651d]"
                      : "border-transparent text-[#1a1a1a]/50 hover:text-[#1a1a1a]/80"
                  }`}
                >
                  <tab.icon size={15} />
                  {tab.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="max-w-5xl mx-auto px-4 py-8">
          {activeTab === "browse" && <BrowseTab user={user} />}
          {activeTab === "library" && <LibraryTab user={user} />}
          {activeTab === "sell" && <SellTab user={user} />}
        </div>
      </div>
    </AppShell>
  );
}
