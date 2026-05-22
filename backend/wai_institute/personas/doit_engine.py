"""
DoIt Engine — Autonomous Gap-Filling Persona

The DoIt persona is Delon's background system worker. It runs on a schedule or triggered
by events, identifies gaps in what WAI promises vs delivers, and proactively fixes them.

Unlike other personas (which respond to requests), DoIt works autonomously:
- Finds broken things
- Fixes them
- Reports results to Delon
- Requests approval for significant changes

DoIt is relentless, methodical, and detail-oriented. It's the voice saying "that thing
won't work, here's why, here's the fix."
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class GapSeverity(str, Enum):
    """How bad is this gap?"""
    CRITICAL = "critical"      # Blocks revenue or safety
    HIGH = "high"              # Blocks credibility or scaling
    MEDIUM = "medium"          # Affects user experience
    LOW = "low"                # Nice-to-have, not urgent


class GapStatus(str, Enum):
    """Where is this gap in the fix process?"""
    IDENTIFIED = "identified"      # Found it
    PROPOSED = "proposed"          # Here's the fix
    APPROVED = "approved"          # Delon said fix it
    IN_PROGRESS = "in_progress"    # Working on it
    RESOLVED = "resolved"          # Done + tested
    DEFERRED = "deferred"          # Not now


class Gap:
    """A system gap: something promised but not delivered"""

    def __init__(self,
                 gap_id: str,
                 title: str,
                 description: str,
                 severity: GapSeverity,
                 system_areas: List[str],  # ["billing", "frontend", "security"]
                 status: GapStatus = GapStatus.IDENTIFIED,
                 finder_notes: str = "",
                 fix_proposal: str = "",
                 effort_hours: float = 0,
                 blocker_for: List[str] = None,
                 ):
        self.gap_id = gap_id
        self.title = title
        self.description = description
        self.severity = severity
        self.system_areas = system_areas
        self.status = status
        self.finder_notes = finder_notes
        self.fix_proposal = fix_proposal
        self.effort_hours = effort_hours
        self.blocker_for = blocker_for or []
        self.discovered_at = datetime.utcnow()
        self.tags = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "gap_id": self.gap_id,
            "title": self.title,
            "description": self.description,
            "severity": self.severity.value,
            "system_areas": self.system_areas,
            "status": self.status.value,
            "finder_notes": self.finder_notes,
            "fix_proposal": self.fix_proposal,
            "effort_hours": self.effort_hours,
            "blocker_for": self.blocker_for,
            "discovered_at": self.discovered_at.isoformat(),
        }


class DoItEngine:
    """
    Autonomous gap-filler for WAI-Institute system.

    Responsibilities:
    1. Scan system for gaps (broken, missing, incomplete)
    2. Propose fixes (with effort estimates)
    3. Execute fixes (auto-fixable items)
    4. Request Delon approval (high-risk changes)
    5. Report results (daily briefing)

    Runs continuously but respects Delon's approval authority.
    """

    def __init__(self, db=None):
        self.db = db
        self.gaps: Dict[str, Gap] = {}
        self.completed_fixes: List[Dict[str, Any]] = []
        self.pending_approvals: List[Gap] = []

    async def scan_system(self) -> List[Gap]:
        """
        Scan the entire WAI system for gaps.
        Returns list of newly identified gaps.
        """
        new_gaps = []

        # CRITICAL GAPS
        gaps_to_check = [
            self._check_end_to_end_transaction(),
            self._check_marketplace_ui(),
            self._check_refund_policy(),
            self._check_director_brief(),
            self._check_help_center_delivery(),
            self._check_testimonial_system(),
            self._check_public_dashboard(),
            self._check_compliance_audit(),
            self._check_account_recovery(),
            self._check_revenue_forecast(),
        ]

        for gap in gaps_to_check:
            if gap and gap.gap_id not in self.gaps:
                self.gaps[gap.gap_id] = gap
                new_gaps.append(gap)
                logger.info(f"DoIt discovered gap: {gap.title} ({gap.severity.value})")

        return new_gaps

    # ── INDIVIDUAL GAP DETECTORS ───────────────────────────────────────────────

    def _check_end_to_end_transaction(self) -> Optional[Gap]:
        """Are students actually able to complete a transaction?"""
        return Gap(
            gap_id="g001_e2e_transaction",
            title="End-to-End Transaction Not Tested",
            description=(
                "Billing system deployed but zero live transactions verified. "
                "Students cannot prove they can pay. Revenue is theoretical."
            ),
            severity=GapSeverity.CRITICAL,
            system_areas=["billing", "stripe", "frontend"],
            status=GapStatus.IDENTIFIED,
            finder_notes=(
                "Stripe test mode is configured but never tested with real student flow. "
                "No subscriber data in production database. No invoice generated. "
                "No payout processed."
            ),
            fix_proposal=(
                "1. Create test student account\n"
                "2. Add test payment method\n"
                "3. Subscribe to BASIC tier ($9.99/mo)\n"
                "4. Verify invoice created in MongoDB\n"
                "5. Verify Stripe charge succeeded\n"
                "6. Verify creator payout tracked\n"
                "7. Cancel subscription and test refund\n"
                "8. Document entire flow + create runbook"
            ),
            effort_hours=2.0,
            blocker_for=["revenue", "marketplace", "creator-payouts"],
        )

    def _check_marketplace_ui(self) -> Optional[Gap]:
        """Can students actually discover and enroll in creator courses?"""
        return Gap(
            gap_id="g002_marketplace_ui",
            title="Creator Marketplace Has No Frontend",
            description=(
                "Creator course endpoints exist (/api/creator-courses/create, /dashboard) "
                "but no React component for students to browse, search, or buy courses."
            ),
            severity=GapSeverity.CRITICAL,
            system_areas=["frontend", "react", "ux"],
            status=GapStatus.IDENTIFIED,
            finder_notes=(
                "Backend endpoints are complete and tested. "
                "Frontend has no corresponding component. "
                "Students cannot discover courses. "
                "Zero course purchases will ever happen."
            ),
            fix_proposal=(
                "1. Create CourseMarketplace.tsx component\n"
                "2. Add course search/filter (by category, rating, price)\n"
                "3. Add course detail card (title, description, price, reviews)\n"
                "4. Add 'Enroll Now' button → subscription flow\n"
                "5. Create creator dashboard UI (see my courses, earnings)\n"
                "6. Integrate with payment system\n"
                "7. Add review/rating component\n"
                "8. Test end-to-end"
            ),
            effort_hours=8.0,
            blocker_for=["creator-revenue", "student-courses"],
        )

    def _check_refund_policy(self) -> Optional[Gap]:
        """Is there a documented refund policy?"""
        return Gap(
            gap_id="g003_refund_policy",
            title="No Refund Policy (Legal Risk)",
            description=(
                "Subscription system accepts payments but no refund policy exists. "
                "First customer asks for refund, system has no answer. Legal liability."
            ),
            severity=GapSeverity.CRITICAL,
            system_areas=["billing", "legal", "customer-service"],
            status=GapStatus.IDENTIFIED,
            finder_notes=(
                "Proration math exists but no documented customer-facing policy. "
                "No refund status tracking (approved/pending/denied). "
                "No customer support workflow. "
                "No chargeback handling."
            ),
            fix_proposal=(
                "1. Write refund policy (7-day unconditional refund, then case-by-case)\n"
                "2. Add RefundRequest model (status, reason, approver)\n"
                "3. Create /api/billing/refund-request POST endpoint\n"
                "4. Add customer service queue (email Delon on refund request)\n"
                "5. Implement automatic 7-day refund (no approval needed)\n"
                "6. Add dispute tracking (chargeback, reversal)\n"
                "7. Document in terms of service\n"
                "8. Test refund workflow"
            ),
            effort_hours=4.0,
            blocker_for=["launch"],
        )

    def _check_director_brief(self) -> Optional[Gap]:
        """Does Delon have a clear job description and daily brief?"""
        return Gap(
            gap_id="g004_director_brief",
            title="Director Role Undefined (Delon Doesn't Know What to Do)",
            description=(
                "Director system has 8 tools and 12 personas, but Delon has no manual. "
                "What is he supposed to ask Director to DO each day? "
                "What requires his judgment vs automation?"
            ),
            severity=GapSeverity.CRITICAL,
            system_areas=["director", "roles", "documentation"],
            status=GapStatus.IDENTIFIED,
            finder_notes=(
                "Director prompt is 400+ lines but written for research/writing. "
                "No routing table for different scenarios. "
                "No SLA for response time. "
                "No backup if Director is unavailable. "
                "No daily briefing template."
            ),
            fix_proposal=(
                "Create DIRECTOR_BRIEF.md with:\n"
                "1. Delon's full job description\n"
                "2. Daily briefing template\n"
                "3. Decision routing (what goes to which persona)\n"
                "4. When to ask Director vs human team\n"
                "5. Director's 8 tools and when to use each\n"
                "6. Escalation playbook\n"
                "7. Response time SLA\n"
                "8. Examples of good/bad requests"
            ),
            effort_hours=3.0,
            blocker_for=["director-effectiveness"],
        )

    def _check_help_center_delivery(self) -> Optional[Gap]:
        """How does the community actually ACCESS M.O.R.E. Help Center?"""
        return Gap(
            gap_id="g005_help_center_delivery",
            title="M.O.R.E. Help Center — No Access Method",
            description=(
                "Helper AI is built (400+ lines) but community can't use it. "
                "Is it web-only? Phone? SMS? WhatsApp? "
                "No channels defined."
            ),
            severity=GapSeverity.HIGH,
            system_areas=["help-center", "frontend", "delivery"],
            status=GapStatus.IDENTIFIED,
            finder_notes=(
                "Helper system prompt is comprehensive. "
                "Guardian moderation layer exists. "
                "BUT: No frontend UI. "
                "No SMS integration. "
                "No voice/phone access. "
                "No app. "
                "Community can't find it."
            ),
            fix_proposal=(
                "1. Create Help Center landing page (web)\n"
                "2. Add SMS integration (Twilio)\n"
                "3. Document help center in-app access\n"
                "4. Create 'Ask Helper' button on every page\n"
                "5. Add response time SLA (email results in 24h)\n"
                "6. Create content update workflow\n"
                "7. Monitor Guardian flags daily\n"
                "8. Test all channels"
            ),
            effort_hours=6.0,
            blocker_for=["help-center-launch"],
        )

    def _check_testimonial_system(self) -> Optional[Gap]:
        """Can students leave reviews/testimonials to build community trust?"""
        return Gap(
            gap_id="g006_testimonial_system",
            title="No Testimonial/Review System (Social Proof Missing)",
            description=(
                "199 tests pass but zero student testimonials exist. "
                "No way for community to see 'these real people benefited.' "
                "Hard to attract new communities without proof."
            ),
            severity=GapSeverity.HIGH,
            system_areas=["frontend", "backend", "database"],
            status=GapStatus.IDENTIFIED,
            finder_notes=(
                "No review/rating model in database. "
                "No testimonial capture UI. "
                "No approval workflow. "
                "No public testimonial display."
            ),
            fix_proposal=(
                "1. Create Testimonial model (text, rating, author, status)\n"
                "2. Create /api/testimonials POST endpoint (require auth)\n"
                "3. Create admin approval workflow\n"
                "4. Create /api/testimonials GET (public, approved only)\n"
                "5. Add testimonial display component\n"
                "6. Add review rating (1-5 stars) for courses\n"
                "7. Create testimonial display on landing page\n"
                "8. Test end-to-end"
            ),
            effort_hours=4.0,
            blocker_for=["credibility", "marketing"],
        )

    def _check_public_dashboard(self) -> Optional[Gap]:
        """Can Delon show community the financial health/impact?"""
        return Gap(
            gap_id="g007_public_dashboard",
            title="No Public Financial/Impact Dashboard (Transparency Gap)",
            description=(
                "Financial reporting exists but only for admins. "
                "Community can't see 'how sustainable is this?' "
                "No way to show supporters the impact."
            ),
            severity=GapSeverity.HIGH,
            system_areas=["frontend", "dashboard", "reporting"],
            status=GapStatus.IDENTIFIED,
            finder_notes=(
                "MRR, LTV, churn endpoints exist. "
                "No public-facing dashboard. "
                "No PDF report export. "
                "No impact metrics (students trained, jobs placed)."
            ),
            fix_proposal=(
                "1. Create public dashboard with key metrics:\n"
                "   - Students trained (YTD)\n"
                "   - Certifications issued\n"
                "   - Job placements (if tracked)\n"
                "   - Community trust index\n"
                "2. Add annual report PDF generation\n"
                "3. Create 'State of WAI' newsletter template\n"
                "4. Add impact tracking model\n"
                "5. Create public view URL (no auth)\n"
                "6. Add testimonial showcase\n"
                "7. Test dashboard + report"
            ),
            effort_hours=5.0,
            blocker_for=["fundraising", "community-trust"],
        )

    def _check_compliance_audit(self) -> Optional[Gap]:
        """Is there an audit trail for SOC 2 / GDPR compliance?"""
        return Gap(
            gap_id="g008_compliance_audit",
            title="No Audit Trail Export (SOC 2/GDPR Risk)",
            description=(
                "Audit logging added but no export for compliance audits. "
                "No data retention policy. "
                "No GDPR right-to-be-forgotten workflow."
            ),
            severity=GapSeverity.MEDIUM,
            system_areas=["security", "compliance", "backend"],
            status=GapStatus.IDENTIFIED,
            finder_notes=(
                "Audit logs have 7-year TTL. "
                "But no export endpoint for auditors. "
                "No data deletion workflow. "
                "No PII scrubbing beyond passwords."
            ),
            fix_proposal=(
                "1. Create /api/admin/audit-export endpoint\n"
                "2. Add date range filtering (for audits)\n"
                "3. Add format options (CSV, JSON)\n"
                "4. Create data deletion request workflow\n"
                "5. Add GDPR field masking rules\n"
                "6. Document data retention policy\n"
                "7. Create privacy policy (linked to actual capability)\n"
                "8. Test audit export + compliance"
            ),
            effort_hours=4.0,
            blocker_for=["compliance"],
        )

    def _check_account_recovery(self) -> Optional[Gap]:
        """Are there 3 different passwords for Delon's accounts?"""
        return Gap(
            gap_id="g009_account_recovery",
            title="Account Recovery Is Fragile (3 Passwords, No Unified Identity)",
            description=(
                "HANDOFF lists 3 exec accounts with 3 different passwords. "
                "If Delon forgets, which one? Recovery codes exist but undocumented."
            ),
            severity=GapSeverity.LOW,
            system_areas=["auth", "ux", "documentation"],
            status=GapStatus.IDENTIFIED,
            finder_notes=(
                "3 accounts: delon.oliver@lce, youpickeddoliver@gmail, souppoetry@gmail\n"
                "2 different passwords in HANDOFF\n"
                "EXEC_FORCE_RESET is emergency-only\n"
                "Recovery codes exist but Delon might not know"
            ),
            fix_proposal=(
                "1. Create unified Delon identity (delon@wai-institute.org)\n"
                "2. Migrate all 3 old accounts → new identity\n"
                "3. Document recovery procedure in DELON_QUICK_START.md\n"
                "4. Print recovery codes for offline backup\n"
                "5. Test login → forgot password → recovery flow\n"
                "6. Add SMS recovery code delivery (if phone on file)"
            ),
            effort_hours=2.0,
            blocker_for=["account-safety"],
        )

    def _check_revenue_forecast(self) -> Optional[Gap]:
        """Is there a revenue forecast with new income streams?"""
        return Gap(
            gap_id="g010_revenue_forecast",
            title="Revenue Forecast Missing (No Growth Plan)",
            description=(
                "Billing system exists with student subscriptions, "
                "but no forecast showing what revenue is possible. "
                "No plan for new income streams that can start tomorrow."
            ),
            severity=GapSeverity.HIGH,
            system_areas=["business", "revenue", "planning"],
            status=GapStatus.IDENTIFIED,
            finder_notes=(
                "Subscription tiers: BASIC $9.99/mo, ADVANCED $29.99/mo, PREMIUM $99.99/mo\n"
                "Creator marketplace exists but untested\n"
                "Certification/credentials system exists but not monetized\n"
                "Corporate/enterprise training not offered\n"
                "No affiliate/partnership revenue\n"
                "No workshop/event revenue"
            ),
            fix_proposal=(
                "Create REVENUE_FORECAST.md with:\n"
                "1. Current revenue (subscriptions by tier)\n"
                "2. Creator course revenue (70% creator, 30% platform)\n"
                "3. Corporate training ($5K/cohort, 4/year)\n"
                "4. Certification exam fees ($49/attempt)\n"
                "5. Premium support ($99/mo)\n"
                "6. Affiliate partnerships (tools, materials)\n"
                "7. Grant funding (social impact)\n"
                "8. Detailed projections + launch dates"
            ),
            effort_hours=3.0,
            blocker_for=["business-planning"],
        )

    # ── FIX AUTOMATION ─────────────────────────────────────────────────────────

    async def auto_fix(self) -> List[Dict[str, Any]]:
        """
        Auto-fix gaps that don't require Delon approval.
        Return list of completed fixes.
        """
        auto_fixable = [
            # These can be created/updated without changing business logic
        ]
        # Currently, all critical gaps require Delon approval.
        # Future: Add auto-fixable items (like documentation generation)
        return self.completed_fixes

    async def request_approval(self, gap: Gap) -> None:
        """
        Request Delon's approval for a gap fix.
        Adds to approval queue.
        """
        self.pending_approvals.append(gap)
        logger.warning(f"DoIt requesting approval for: {gap.title}")

    async def approve_fix(self, gap_id: str) -> None:
        """Delon approves a fix. Mark as approved and ready to execute."""
        if gap_id in self.gaps:
            gap = self.gaps[gap_id]
            gap.status = GapStatus.APPROVED
            logger.info(f"DoIt approved to fix: {gap.title}")

    def daily_report(self) -> Dict[str, Any]:
        """Generate Delon's daily DoIt report."""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "total_gaps": len(self.gaps),
            "by_severity": {
                "critical": sum(1 for g in self.gaps.values() if g.severity == GapSeverity.CRITICAL),
                "high": sum(1 for g in self.gaps.values() if g.severity == GapSeverity.HIGH),
                "medium": sum(1 for g in self.gaps.values() if g.severity == GapSeverity.MEDIUM),
                "low": sum(1 for g in self.gaps.values() if g.severity == GapSeverity.LOW),
            },
            "pending_approval": [g.gap_id for g in self.pending_approvals],
            "completed_fixes": len(self.completed_fixes),
            "all_gaps": [g.to_dict() for g in self.gaps.values()],
        }


# Singleton instance
_doit_instance = None


def get_doit_engine(db=None) -> DoItEngine:
    """Get or create DoIt engine instance."""
    global _doit_instance
    if not _doit_instance:
        _doit_instance = DoItEngine(db=db)
    return _doit_instance
