import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../lib/auth";
import { WAI_LOGO, BRAND } from "../lib/brand";
import { toast } from "sonner";

export default function Register() {
  const { register } = useAuth();
  const nav = useNavigate();
  const [form, setForm] = useState({ full_name: "", email: "", password: "", role: "student", associate: "Associate-Alpha" });
  const [loading, setLoading] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const u = await register(form);
      toast.success(`Welcome, ${u.full_name}`);
      nav(u.role === "admin" ? "/admin" : u.role === "instructor" ? "/instructor" : "/dashboard");
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Registration failed");
    } finally { setLoading(false); }
  };

  return (
    <div className="min-h-screen bg-bone flex items-center justify-center p-8">
      <form onSubmit={submit} className="w-full max-w-md" data-testid="register-form">
        <Link to="/" className="flex items-center gap-3 mb-8" data-testid="register-brand">
          <img src={WAI_LOGO} alt="W.A.I." className="w-12 h-12 object-contain bg-white border border-ink/10 p-1" />
          <div>
            <div className="overline text-copper">{BRAND.short}</div>
            <div className="font-heading font-bold">{BRAND.name}</div>
          </div>
        </Link>

        <div className="overline text-copper">Enroll</div>
        <h2 className="font-heading text-3xl font-bold mt-2">Start your apprenticeship.</h2>
        <p className="text-ink/60 text-sm mt-2">Skills, safety, and a certificate you can carry.</p>

        <div className="mt-8 space-y-4">
          <div>
            <label className="overline text-ink/60">Full name</label>
            <input type="text" required value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })}
              className="w-full mt-2 px-4 py-3 bg-white border border-ink/20 focus:border-ink focus:outline-none focus:ring-2 focus:ring-signal"
              data-testid="input-name" />
          </div>
          <div>
            <label className="overline text-ink/60">Email</label>
            <input type="email" required value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })}
              className="w-full mt-2 px-4 py-3 bg-white border border-ink/20 focus:border-ink focus:outline-none focus:ring-2 focus:ring-signal"
              data-testid="input-email" />
          </div>
          <div>
            <label className="overline text-ink/60">Password</label>
            <input type="password" required minLength={6} value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })}
              className="w-full mt-2 px-4 py-3 bg-white border border-ink/20 focus:border-ink focus:outline-none focus:ring-2 focus:ring-signal"
              data-testid="input-password" />
          </div>
          <div>
            <label className="overline text-ink/60">Track</label>
            <select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}
              className="w-full mt-2 px-4 py-3 bg-white border border-ink/20 focus:border-ink focus:outline-none focus:ring-2 focus:ring-signal"
              data-testid="select-role">
              <option value="student">Student / Apprentice</option>
              <option value="instructor">Instructor</option>
            </select>
          </div>
          <div>
            <label className="overline text-ink/60">Associate</label>
            <input type="text" value={form.associate} onChange={(e) => setForm({ ...form, associate: e.target.value })}
              className="w-full mt-2 px-4 py-3 bg-white border border-ink/20 focus:border-ink focus:outline-none focus:ring-2 focus:ring-signal"
              data-testid="input-associate" />
          </div>
        </div>

        <button type="submit" disabled={loading} className="btn-copper w-full mt-6" data-testid="btn-submit">
          {loading ? "Creating account…" : "Create account"}
        </button>

        <div className="mt-6 text-sm">
          Already enrolled? <Link to="/login" className="text-copper font-semibold hover:underline" data-testid="link-login">Sign in</Link>
        </div>
      </form>
    </div>
  );
}
