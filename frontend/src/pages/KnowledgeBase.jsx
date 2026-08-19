import { Link } from "react-router-dom";
import PublicNav from "../components/PublicNav";
import BackButton from "../components/BackButton";
import { BACKEND_URL } from "../lib/api";
import { BookOpen, MonitorSmartphone, FileBadge, Receipt, ChevronDown, ArrowRight, LifeBuoy } from "lucide-react";

// Public M.O.R.E. Knowledge Base — handbooks, platform guides, and the
// most-asked support answers (browser requirements, certificate delivery,
// refunds & billing). No dead ends: every card links somewhere real.
const HANDBOOKS = [
  { name: "student",    title: "Student Handbook",  desc: "How to enroll, access courses, track progress, and earn certificates.", icon: BookOpen },
  { name: "instructor", title: "Instructor Handbook", desc: "Classroom management, attendance, grading, and lab oversight.", icon: BookOpen },
  { name: "admin",      title: "Admin Handbook",    desc: "Accounts, roles, billing, and platform administration.", icon: BookOpen },
  { name: "persona",    title: "AI Persona Creation Manual", desc: "How the AI personas are built, governed, and kept aligned.", icon: BookOpen },
];

const ARTICLES = [
  {
    id: "browser-requirements",
    icon: MonitorSmartphone,
    title: "Browser & Device Requirements",
    body: (
      <>
        <p>The platform works best in a current version of <strong>Chrome, Edge, Firefox, or Safari</strong> on desktop, laptop, or mobile. Keep your browser updated and enable cookies and JavaScript.</p>
        <ul>
          <li><strong>Minimum internet:</strong> a stable connection of about 5 Mbps for video lessons; slower connections work for text and most labs.</li>
          <li><strong>Phone or tablet:</strong> fully supported. If a page looks off, rotate to landscape or try the desktop site in your browser menu.</li>
          <li><strong>Videos won't play or pages stall?</strong> Clear your browser cache, try a private/incognito window, then reload. If it persists, report it at the M.O.R.E. Help Center.</li>
        </ul>
      </>
    ),
  },
  {
    id: "certificate-delivery",
    icon: FileBadge,
    title: "Where is my certificate?",
    body: (
      <>
        <p>Completed certificates and verified credentials appear in <strong>Credentials</strong> and <strong>Certificates</strong> in your dashboard after your work is graded and marked complete. From there you can view, download, and share them.</p>
        <ul>
          <li><strong>Just finished?</strong> Allow a short processing window for grading to finalize.</li>
          <li><strong>Completed a course but see nothing?</strong> Confirm the course shows 100% progress, then contact the M.O.R.E. Help Center with your name, email, and course — the team can verify and issue it.</li>
          <li><strong>Lost your certificate file?</strong> Certificates can be re-downloaded any time from your dashboard.</li>
        </ul>
      </>
    ),
  },
  {
    id: "refunds-billing",
    icon: Receipt,
    title: "Refunds & Billing",
    body: (
      <>
        <p>Your <strong>Payment History</strong> page shows every purchase, subscription charge, and receipt. Billing and account self-service live on the M.O.R.E. door.</p>
        <ul>
          <li><strong>Update a card or payment method:</strong> use Account Settings, then re-run the checkout for any new purchase.</li>
          <li><strong>Membership questions (renewal, cancel, upgrade):</strong> open the Membership Plans page and follow the manage link on your subscription.</li>
          <li><strong>Digital product issue:</strong> if a purchased product didn't deliver or is defective, contact the M.O.R.E. Help Center within 7 days with your receipt — the team reviews every request personally.</li>
          <li><strong>Checkout error?</strong> Try a different browser or device once; if it still fails, contact help with the exact error message.</li>
        </ul>
      </>
    ),
  },
];

export default function KnowledgeBase() {
  return (
    <div className="min-h-screen bg-bone">
      <PublicNav />
      <div className="max-w-6xl mx-auto px-6 py-10">
        <BackButton to="/" />
        <div className="mt-6">
          <div className="overline text-copper mb-2">M.O.R.E. Knowledge Base</div>
          <h1 className="font-heading text-4xl font-bold text-ink mt-2">Knowledge Base</h1>
          <p className="text-ink/60 mt-3 max-w-2xl">
            Handbooks, platform guides, and straight answers to the questions we hear most —
            so you can help yourself, then help your neighbor.
          </p>
        </div>

        {/* Quick answers */}
        <section className="mt-10">
          <div className="overline text-copper mb-4">Quick Answers</div>
          <div className="space-y-3">
            {ARTICLES.map((a) => {
              const Icon = a.icon;
              return (
                <details key={a.id} className="card-flat bg-white border border-ink/10 rounded-2xl overflow-hidden group">
                  <summary className="flex items-center justify-between gap-4 cursor-pointer px-6 py-4 list-none hover:bg-copper/5 transition-colors">
                    <span className="flex items-center gap-3 font-heading font-bold text-ink">
                      <Icon className="w-5 h-5 text-copper shrink-0" />
                      {a.title}
                    </span>
                    <ChevronDown className="w-5 h-5 text-ink/40 group-open:rotate-180 transition-transform shrink-0" />
                  </summary>
                  <div className="px-6 pb-5 text-sm text-ink/70 leading-relaxed space-y-3 border-t border-ink/5 pt-4">
                    {a.body}
                  </div>
                </details>
              );
            })}
          </div>
        </section>

        {/* Handbooks */}
        <section className="mt-12">
          <div className="overline text-copper mb-4">Guides & Handbooks</div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {HANDBOOKS.map((h) => {
              const Icon = h.icon;
              return (
                <a
                  key={h.name}
                  href={`${BACKEND_URL}/api/handbooks/${h.name}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="card-flat p-6 border border-ink/10 bg-white hover:border-copper transition-all group"
                >
                  <Icon className="w-6 h-6 text-copper" />
                  <div className="font-heading font-bold text-ink mt-3 group-hover:text-copper transition-colors">{h.title}</div>
                  <p className="text-sm text-ink/60 mt-1">{h.desc}</p>
                  <div className="mt-4 text-sm font-bold uppercase tracking-widest text-copper flex items-center gap-1 group-hover:gap-2 transition-all">
                    Read <ArrowRight className="w-3.5 h-3.5" />
                  </div>
                </a>
              );
            })}
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-4">
            <Link to="/site-guide" className="card-flat p-6 border border-ink/10 bg-white hover:border-copper transition-all group">
              <div className="font-heading font-bold text-ink group-hover:text-copper transition-colors">Site Guide</div>
              <p className="text-sm text-ink/60 mt-1">How to use the platform — accounts, navigation, and settings.</p>
              <div className="mt-4 text-sm font-bold uppercase tracking-widest text-copper flex items-center gap-1 group-hover:gap-2 transition-all">
                Open <ArrowRight className="w-3.5 h-3.5" />
              </div>
            </Link>
            <Link to="/help-center" className="card-flat p-6 border border-ink/10 bg-white hover:border-copper transition-all group">
              <div className="font-heading font-bold text-ink group-hover:text-copper transition-colors">Help Center</div>
              <p className="text-sm text-ink/60 mt-1">Housing, legal, food, jobs, education, and health help — free and in plain language.</p>
              <div className="mt-4 text-sm font-bold uppercase tracking-widest text-copper flex items-center gap-1 group-hover:gap-2 transition-all">
                Open <ArrowRight className="w-3.5 h-3.5" />
              </div>
            </Link>
          </div>
        </section>

        {/* Still stuck */}
        <section className="mt-12 rounded-[28px] border border-copper/20 bg-white p-8 flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
          <div className="flex items-start gap-4">
            <LifeBuoy className="w-8 h-8 text-copper shrink-0 mt-1" />
            <div>
              <h2 className="font-heading text-2xl font-bold text-ink">Still stuck?</h2>
              <p className="text-sm text-ink/60 mt-1 max-w-xl">
                Real people answer at the M.O.R.E. Help Center — tickets, troubleshooting, and billing support. Text or DM @namoshun for anything urgent.
              </p>
            </div>
          </div>
          <Link to="/help-center" className="btn-copper inline-flex items-center gap-2 whitespace-nowrap">
            Get Help <ArrowRight className="w-4 h-4" />
          </Link>
        </section>
      </div>
    </div>
  );
}
