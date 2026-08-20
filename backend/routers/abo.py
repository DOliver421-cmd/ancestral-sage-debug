"""
abo.py — AI Business Office (ABO).

The revenue engine command center for M.O.R.E. Help Center. Mission rule:
no revenue = no business office = no jobs for people or the AI workforce.
This module gives the office the real tools to do the business AI can do —
the actual platform capabilities (Social Blast, Creator Studio, BYOK, AAWAB,
Exec Site Report, the store) — and tracks the money that keeps the mission
funded.

OWNER-FIRST FINANCIAL MODEL (non-negotiable):
  The founder/owner took the risk, invested the capital, and built the
  platform. The financial engine protects them first:

    REVENUE (month) ──► 1. Infrastructure costs (hosting, API tokens, DB)
                     ──► 2. NET PROFIT ──► belongs to the business entity
                          and the owner as retained earnings / owner draw
                          (owner-controlled — nothing is auto-drained)
                     ──► 3. Distributions to any role (human or AI) happen
                          ONLY when the owner records them, ONLY out of
                          net profit, ONLY tied to performance milestones
                          (commissions on closed deals, distributions when
                          net profit is positive). No fixed liabilities.

  There is NO hardcoded mandate that drains the owner's pocket. If the owner
  is not sustained, there is no platform. Until the owner is whole, there is
  no profit unless the owner says there is. The exec control page lets the
  owner change every number and every text string below WITHOUT code.

LABOR MODEL:
  AI jobs create revenue (value_cents). Human roles are performance-linked:
  commissions (commission_pct on closed deals) or distributions that become
  payable only when net profit covers them. The ledger shows the commitment;
  the owner authorizes actual payment.

Division of labor (kept legally sound — human is always the responsible party):
  AI (Autonomous Engine):  executes the work — content, publishing, audits,
                           diagnostics, customer service, product generation.
  Human (Oversight Desk):  holds merchant accounts / EIN, signs supplier and
                           service contracts, reviews exception alerts,
                           authorizes payouts, owns liability — and is paid
                           from profit, not out of pocket.

Data model (MongoDB via Motor):
  abo_goals   — legacy singleton: monthly operating goal (kept in sync).
  abo_config  — OFFICE CONFIG: every number + text override, editable via
                GET/PUT /abo/config by the owner (audited). Source of truth.
  abo_deals   — B2B service pipeline (lead → proposed → won → delivered).
  abo_jobs    — Workforce ledger — people AND AI, performance-linked pay.
  abo_exchange_contracts — Agent-to-agent (A2A) task contracts; the office is
                the clearinghouse and takes a fee on every completed contract.
  abo_redteam_engagements — Shadow IT / red-teaming engagements with a
                human "Merge / Approve" checkpoint before patches ship.

Endpoints (all under /api/abo):
  GET  /abo/overview        — revenue snapshot + mission runway + P&L (auth).
  GET  /abo/tools           — the business tools AI can run (public).
  GET  /abo/divisions       — business divisions w/ status + revenue (auth).
  GET  /abo/deals           — caller's service deals (auth).
  POST /abo/deals           — submit a service request → creates a lead (auth).
  PATCH /abo/deals/{id}     — admin: advance stage, set value, approve, close.
  POST /abo/deals/{id}/propose — admin: AI-draft a deliverable proposal.
  GET  /abo/jobs            — workforce ledger: people & AI (auth).
  POST /abo/jobs            — admin: open a job for the workforce.
  PATCH /abo/jobs/{id}      — admin: update hours / value / status / pay.
  GET  /abo/goals           — mission runway + monthly operating goal (auth).
  POST /abo/goals           — admin: set the monthly operating goal.
  GET  /abo/exchange        — A2A contract board (auth).
  POST /abo/exchange/contracts — create an agent task contract (auth).
  POST /abo/exchange/contracts/{id}/complete — admin: settle; fee booked.
  GET  /abo/redteam         — red-team engagements (auth).
  POST /abo/redteam/engagements — start a red-team engagement (auth).
  POST /abo/redteam/engagements/{id}/approve — admin: human Merge/Approve.
  POST /abo/redteam/engagements/{id}/close   — admin: mark delivered.
  GET  /abo/config          — admin: full editable office config.
  PUT  /abo/config          — admin: save ANY number/text override (audited).
  GET  /abo/admin/overview  — admin: all deals + jobs + revenue by product.

Auth follows the standard router pattern: JWT bearer (`lce_token`) via
`current_user`, admin gates via `_require_rank`. Shared state is bound by
server.py via bind() at include time — no circular imports.
"""

from __future__ import annotations

import hashlib
import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Header, Query, Request
from pydantic import BaseModel, ConfigDict, Field
from roles import Role, ROLE_RANK, role_rank, LEGACY_ROLE_MAP, normalize_role, FREE_BYOK_ROLES

logger = logging.getLogger("lcewai")
router = APIRouter(tags=["abo"])

# ── Shared state, bound by server.py via bind() ──────────────────────────────
db = None
current_user = None
audit = None
check_rate = None


def bind(_db, _current_user, _audit, _check_rate):
    """Called by server.py at include time to inject shared dependencies."""
    global db, current_user, audit, check_rate
    db = _db
    current_user = _current_user
    audit = _audit
    check_rate = _check_rate


# Mirrors server.py's role hierarchy for runtime require_role checks.
from routers.roles import ROLE_RANK, Role


class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    full_name: str
    role: Role = "student"
    associate: Optional[str] = None
    is_active: bool = True
    must_change_password: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    avatar_url: Optional[str] = None
    feature_tier: str = "free"


async def _dep_current_user(authorization: Optional[str] = Header(None)) -> User:
    """Resolve the real current_user at REQUEST time (bind() sets it after import)."""
    return await current_user(authorization)


def _require_rank(*roles):
    """Runtime equivalent of server.py's require_role() — used in Depends()."""
    needed_rank = min(ROLE_RANK[r] for r in roles)

    def dep(user: User = Depends(_dep_current_user)) -> User:
        if ROLE_RANK.get(user.role, 0) < needed_rank:
            raise HTTPException(403, "Insufficient permissions to access this resource.")
        return user

    return dep


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _is_admin(user: User) -> bool:
    return user.role in ("admin", "executive_admin")


def _month_start() -> datetime:
    now = datetime.now(timezone.utc)
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

