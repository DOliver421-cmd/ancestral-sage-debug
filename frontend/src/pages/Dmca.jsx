import { Link } from "react-router-dom";
import BackButton from "../components/BackButton";

/**
 * DMCA / Copyright Policy — DRAFT FOR LEGAL REVIEW.
 *
 * The copyright safe harbour (17 U.S.C. § 512) requires a designated agent
 * registered with the U.S. Copyright Office and a contact procedure posted on
 * the service. The statutory elements are drafted below; the bracketed
 * [DRAFT — REVIEW] lines are the owner's action items before this page can be
 * relied on. See the plan's phase 2.
 */
export default function Dmca() {
  return (
    <div className="min-h-screen bg-bone">
      <nav className="bg-ink text-white px-6 py-4 flex items-center gap-4">
        <BackButton fallback="/" />
        <span className="font-heading font-bold text-lg">DMCA / Copyright Policy</span>
      </nav>

      <div className="max-w-3xl mx-auto px-6 py-12">
        <h1 className="font-heading text-3xl font-black text-ink">DMCA / Copyright Policy</h1>
        <p className="text-sm text-ink/60 mt-2">Last updated: October 2026</p>

        <p className="text-ink/70 mt-6 leading-relaxed">
          © 2026 Nam Oshun Edutainment LLC (WAI Institute). All rights reserved. Curriculum, lesson
          text, artwork, video embeds, code, and trademarks are owned by Nam Oshun Edutainment LLC
          or used with permission. Nothing on this platform grants you a licence to reproduce our
          materials outside a registered member's personal educational use.
        </p>

        <h2 className="font-heading text-xl font-bold text-ink mt-9">1. Notice and takedown</h2>
        <p className="text-ink/70 mt-3 leading-relaxed">
          If you believe material available through this service infringes a copyright you own or
          control, you may send a written notice to our designated agent. A valid notice must
          include all of the following, as required by 17 U.S.C. § 512(c)(3):
        </p>
        <ol className="list-decimal ml-6 mt-3 space-y-2 text-ink/70">
          <li>A physical or electronic signature of the copyright owner or a person authorised to act on their behalf.</li>
          <li>Identification of the copyrighted work claimed to have been infringed.</li>
          <li>Identification of the material claimed to be infringing and enough detail to locate it (a URL or in-app path).</li>
          <li>Your contact information — postal address, telephone number, and email address.</li>
          <li>A statement that you have a good-faith belief the disputed use is not authorised by the copyright owner, its agent, or the law.</li>
          <li>A statement, made under penalty of perjury, that the information in your notice is accurate and that you are the owner or authorised to act on the owner's behalf.</li>
        </ol>
        <p className="text-xs text-ink/50 mt-3">
          [DRAFT — REVIEW: send notices to the Designated Agent address registered with the U.S.
          Copyright Office — see the compliance plan, step 3.]
        </p>

        <h2 className="font-heading text-xl font-bold text-ink mt-9">2. Counter-notice</h2>
        <p className="text-ink/70 mt-3 leading-relaxed">
          If you believe material was removed in error, you may send a counter-notice with your
          signature, identification of the material and where it appeared before removal, a
          statement under penalty of perjury that you have a good-faith belief the material was
          removed as a result of mistake or misidentification, and your contact information and
          consent to the jurisdiction of the federal district court for your address (or, if outside
          the United States, any district in which we may be found).
        </p>

        <h2 className="font-heading text-xl font-bold text-ink mt-9">3. Repeat infringers</h2>
        <p className="text-ink/70 mt-3 leading-relaxed">
          We terminate the accounts of users who repeatedly infringe the rights of others, in
          appropriate circumstances and at our discretion.
        </p>

        <h2 className="font-heading text-xl font-bold text-ink mt-9">4. Member-uploaded material</h2>
        <p className="text-ink/70 mt-3 leading-relaxed">
          Content you publish (portfolio items, community posts, publisher media, project artifacts)
          remains yours. By publishing it you grant us a licence to host and display it on the
          service. You are responsible for holding the rights to anything you publish.
        </p>

        <h2 className="font-heading text-xl font-bold text-ink mt-9">5. Permitted educational use</h2>
        <p className="text-ink/70 mt-3 leading-relaxed">
          A registered family may print, reproduce, and keep Academy materials for their own
          students' education. Redistribution for a fee, bulk copying for a school or co-op, or
          publication of our materials outside the platform is not permitted without written
          permission.
        </p>

        <h2 className="font-heading text-xl font-bold text-ink mt-9">6. Contact</h2>
        <p className="text-ink/70 mt-3 leading-relaxed">
          Questions? Visit our <Link to="/more-help-center" className="text-copper hover:underline">MORE
          Help Center</Link>, or send copyright questions to our designated agent at the address
          registered with the U.S. Copyright Office.
        </p>

        <div className="mt-10 flex flex-wrap gap-4 text-sm font-bold">
          <Link to="/terms" className="text-copper hover:text-ink">Terms of Service</Link>
          <Link to="/privacy" className="text-copper hover:text-ink">Privacy Policy</Link>
        </div>
      </div>
    </div>
  );
}
