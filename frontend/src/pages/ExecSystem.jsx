import { useEffect, useState } from "react";
import AppShell from "../components/AppShell";
import { LoadingState } from "../components/LoadingState";
import { api } from "../lib/api";
import { Crown, Database, Users, Shield, Settings as Cog } from "lucide-react";

export default function ExecSystem() {
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  useEffect(() => {
    api.get("/exec/system").then((r) => setData(r.data)).catch((e) => setErr(e?.response?.data?.detail || "Forbidden"));
  }, []);

  if (err) return <AppShell><div className="p-10 text-destructive font-heading" data-testid="exec-error">{err}</div></AppShell>;
  if (!data) return <LoadingState label="Executive System" />;

  return (
    <AppShell>
      <div className="px-10 py-10 max-w-5xl">
        <div className="overline text-copper">Executive Authority</div>
        <h1 className="font-heading text-4xl font-bold mt-2 flex items-center gap-3" data-testid="exec-title">
          <Crown className="w-8 h-8 text-signal" /> System Governance
        </h1>
        <p className="text-ink/60 mt-2 max-w-2xl">
          Top-level visibility for executive admins. Role distribution, audit footprint, runtime configuration.
        </p>

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mt-8">
          <Card icon={Crown} label="Executive Admins" value={data.role_counts.executive_admin || 0} testid="card-execs" />
          <Card icon={Shield} label="Admins" value={data.role_counts.admin || 0} testid="card-admins" />
          <Card icon={Users} label="Instructors" value={data.role_counts.instructor || 0} testid="card-instructors" />
          <Card icon={Users} label="Students" value={data.role_counts.student || 0} testid="card-students" />
        </div>

        <div className="grid lg:grid-cols-2 gap-6 mt-8">
          <div className="card-flat p-6" data-testid="card-runtime">
            <h2 className="font-heading text-xl font-bold flex items-center gap-2"><Cog className="w-5 h-5 text-copper" /> Runtime</h2>
            <dl className="mt-4 space-y-2 text-sm">
              <Row k="App version" v={data.version} />
              <Row k="Database" v={data.env.db_name} />
              <Row k="JWT lifetime (hours)" v={data.env.jwt_expire_hours} />
              <Row k="CORS origins" v={data.env.cors_origins} />
              <Row k="Audit-log entries" v={data.audit_log_total} />
            </dl>
          </div>

          <div className="card-flat p-6" data-testid="card-collections">
            <h2 className="font-heading text-xl font-bold flex items-center gap-2"><Database className="w-5 h-5 text-copper" /> Collections</h2>
            <ul className="mt-4 grid grid-cols-2 gap-1 text-xs font-mono text-ink/70">
              {data.collections.map((c) => <li key={c}>· {c}</li>)}
            </ul>
          </div>
        </div>

        <div className="mt-8 text-xs text-ink/50">
          Executive admins inherit every admin permission. Use the <a href="/admin/users" className="text-copper underline">Users</a> page for promotions, deactivations, and password resets.
        </div>
      </div>
    </AppShell>
  );
}

function Card({ icon: Icon, label, value, testid }) {
  return (
    <div className="card-flat p-5" data-testid={testid}>
      <Icon className="w-5 h-5 text-copper" />
      <div className="font-heading text-3xl font-black mt-2">{value}</div>
      <div className="overline text-ink/60 mt-1">{label}</div>
    </div>
  );
}
const Row = ({ k, v }) => (
  <div className="flex justify-between gap-4 border-b border-ink/5 pb-2">
    <dt className="overline text-ink/60">{k}</dt>
    <dd className="font-mono text-xs text-ink truncate max-w-xs">{String(v)}</dd>
  </div>
);
