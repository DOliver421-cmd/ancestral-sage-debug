import { Link } from "react-router-dom";
import BackButton from "../components/BackButton";

/**
 * Refund Policy — DRAFT FOR LEGAL REVIEW.
 *
 * Sections marked [DRAFT — REVIEW] contain the business policy as currently
 * decided and placeholder language that must be reviewed/edited by counsel
 * before the campaign launch. The numbered business rules below are the
 * owner's actual decisions and should be preserved in substance.
 *
 * Business decisions already made (do not weaken without owner approval):
 *   - Refunds are issued as SITE CREDIT, not back to the original payment
 *     method, UNLESS the failure was the platform's fault.
 *   - Platform-fault failures (e.g., we charged you but never delivered the
 *     purchased access) are refunded to the original payment method.
 *   - Subscription features are granted while the subscription is active and
 *     reverted when the subscription ends or is refunded.
 */
export default function RefundPolicy() {
  return (
    <div className="min-h-screen bg-bone">
      <nav className="bg-ink text-white px-6 py-4 flex items-center gap-4">
        <BackButton fallback="/" />
        <span className="font-heading font-bold text-lg">Refund Policy</span>
      </nav>

      <div className="max-w-3xl mx-auto px-6 py-12">
        <div className="prose prose-ink max-w-none">
          <h1>Refund Policy</h1>
          <p className="text-sm text-ink/60">Last updated: August 2026</p>
          <p className="text-xs italic text-ink/50">
            [DRAFT — this document has not been reviewed by legal counsel. Do
            not rely on it as a binding legal commitment until review is
            complete.]
          </p>

          <h2>1. The Short Version</h2>
          <p>
            Refunds are issued as <strong>site credit</strong> usable toward
            future purchases on the platform — <strong>unless</strong> the
            problem was our fault, in which case we refund the original payment
            method.
          </p>

          <h2>2. Site Credit Refunds</h2>
          <p>
            When a refund is approved, the amount is added to your account as
            site credit unless an exception below applies. Site credit is
            applied automatically to your next eligible purchase.
          </p>
          <p>
            [DRAFT — REVIEW: consider adding — expiry of site credit, minimum
            purchase thresholds, whether credit can be withdrawn/transferred,
            and the jurisdiction/applicable-law clause.]
          </p>

          <h2>3. When We Refund the Original Payment Method</h2>
          <p>We refund to the original payment method when the failure is the platform's fault, including:</p>
          <ul>
            <li>You were charged but did not receive the purchased access, entitlement, or product.</li>
            <li>A purchase was granted to the wrong account or the wrong product.</li>
            <li>A technical error on our side prevented the purchase from being delivered.</li>
          </ul>

          <h2>4. Subscriptions</h2>
          <p>
            Membership and subscription plans renew automatically until
            cancelled. You can cancel at any time from your account or the
            payment provider's customer portal; cancellation stops future
            renewals. Features unlocked by a subscription remain available
            while the subscription is active and are reverted when it ends or
            is refunded.
          </p>
          <p>
            [DRAFT — REVIEW: add — proration policy for mid-cycle
            cancellations, notice period, and how refunds interact with
            recurring charges already collected.]
          </p>

          <h2>5. One-Time Purchases</h2>
          <p>
            One-time purchases (including the $3 BYOK unlock, digital
            workbooks, and products) are refundable as site credit within{" "}
            <em>[DRAFT — insert window, e.g. 14 days]</em> of purchase, subject
            to the exceptions in Section 3. Because digital goods are delivered
            instantly, downloads and usage may be suspended or reverted when a
            refund is issued.
          </p>

          <h2>6. How to Request a Refund</h2>
          <p>
            Contact us through the{" "}
            <Link to="/help-center" className="text-copper hover:underline">
              Help Center
            </Link>{" "}
            with your order details. We respond to refund requests within{" "}
            <em>[DRAFT — insert window, e.g. 5 business days]</em>.
          </p>

          <h2>7. Chargebacks and Abuse</h2>
          <p>
            [DRAFT — REVIEW: add — policy on chargebacks, duplicate refund
            requests, and accounts that abuse the refund process.]
          </p>

          <h2>8. Contact</h2>
          <p>
            Questions? Visit our{" "}
            <Link to="/help-center" className="text-copper hover:underline">
              Help Center
            </Link>
            . For legal inquiries, contact{" "}
            <em>[DRAFT — insert support/legal email address]</em>.
          </p>
        </div>

        <div className="mt-6 flex gap-4 justify-center">
          <Link to="/terms" className="text-sm text-copper hover:underline">
            Terms of Service
          </Link>
          <Link to="/privacy" className="text-sm text-copper hover:underline">
            Privacy Policy
          </Link>
          <Link to="/help-center" className="text-sm text-copper hover:underline">
            Help Center
          </Link>
        </div>
      </div>
    </div>
  );
}
