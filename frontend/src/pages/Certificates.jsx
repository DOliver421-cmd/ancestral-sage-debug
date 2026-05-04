import { useEffect, useState } from "react";
import AppShell from "../components/AppShell";
import { api, BACKEND_URL, getToken } from "../lib/api";
import { Award, Download } from "lucide-react";

const CERT_IMG = "https://static.prod-images.emergentagent.com/jobs/bb805589-57e1-4a69-a20a-634e662786be/images/8f50a2e59b62db70517e5b485f379d687b6390c27e13669862b460e3b59513a7.png";

export default function Certificates() {
  const [certs, setCerts] = useState([]);
  useEffect(() => { api.get("/certificates/me").then((r) => setCerts(r.data)); }, []);
  const token = getToken();

  return (
    <AppShell>
      <div className="px-10 py-10 max-w-6xl">
        <div className="overline text-copper">Credentials</div>
        <h1 className="font-heading text-4xl font-bold mt-2">Your Certificates</h1>
        <p className="text-ink/60 mt-2">Earned. Stackable. Printable. Take your proof of work anywhere.</p>

        {certs.length === 0 ? (
          <div className="mt-10 card-flat p-12 text-center">
            <Award className="w-12 h-12 text-ink/30 mx-auto" />
            <div className="font-heading text-xl font-bold mt-4">No certificates yet</div>
            <div className="text-sm text-ink/60 mt-2">Complete a module with 70%+ on the mastery quiz to earn one.</div>
          </div>
        ) : (
          <div className="grid md:grid-cols-2 gap-5 mt-10">
            {certs.map((c) => (
              <div key={c.module_slug} className={`card-flat p-0 overflow-hidden ${c.module_slug === "program" ? "border-copper border-2" : ""}`} data-testid={`cert-${c.module_slug}`}>
                <div className="relative h-40 bg-ink overflow-hidden">
                  <img src={CERT_IMG} alt="" className="w-full h-full object-cover opacity-60" />
                  <div className="absolute inset-0 bg-gradient-to-t from-ink/90 to-ink/20" />
                  {c.module_slug === "program" && <span className="absolute top-3 left-3 badge-signal">Capstone</span>}
                </div>
                <div className="p-6">
                  <div className="overline text-copper">Certificate</div>
                  <div className="font-heading text-xl font-bold mt-2">{c.title}</div>
                  <div className="flex gap-4 text-xs overline text-ink/60 mt-3">
                    <span>{c.hours} hours</span>
                    <span>{c.score != null ? `${Math.round(c.score)}%` : "—"}</span>
                    {c.completed_at && <span>{new Date(c.completed_at).toLocaleDateString()}</span>}
                  </div>
                  <a href={`${BACKEND_URL}/api/certificates/${c.module_slug}.pdf?token=${token}`} target="_blank" rel="noreferrer"
                    className="btn-primary mt-5 inline-flex items-center gap-2 text-sm" data-testid={`download-${c.module_slug}`}>
                    <Download className="w-4 h-4" /> Download PDF
                  </a>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </AppShell>
  );
}
