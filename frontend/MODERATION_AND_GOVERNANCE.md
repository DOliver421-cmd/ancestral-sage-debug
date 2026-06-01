# Moderation & Governance System

## Overview

WAI has two complementary dashboards for threat management:

1. **AdminDashboard** (Moderation & Governance) — for Moderators, Stewards, Elders
2. **ExecutiveDirectorDashboard** (Crisis Management) — for Directors/CEOs only

---

## Dashboard Responsibilities

### AdminDashboard (Moderators, Stewards, Elders)

**Purpose:** Daily community moderation and governance decisions.

**Three Main Sections:**

#### 1. Reported Content Tab
- Shows all community reports (hate speech, harassment, spam, fraud)
- Severity levels: CRITICAL, HIGH, MEDIUM
- Report count tracking (how many users reported the same issue)
- **Available Actions:**
  - **DELETE CONTENT** (all moderators) — Remove the post/comment immediately
  - **BAN USER** (all moderators) — Remove user from platform
  - **WARN USER** (all moderators) — Issue community guideline violation notice
  - **ESCALATE TO DIRECTOR** (Stewards+) — Flag for platform-level action

#### 2. Suspicious Users Tab
- Automated risk scoring (0-100) based on behavior patterns
- Flags: `fraud_pattern`, `coordinated_harassment`, `ban_evasion`, `account_3_days_old`
- Report count per user
- **Available Actions:**
  - **WARN** — Send community guideline warning
  - **BAN USER** — Remove from platform
  - **ESCALATE** (Stewards+) — Refer to Director

#### 3. Action Log Tab
- Complete audit trail of all moderation decisions
- Who took action, what action, when, and why
- Status tracking (completed, pending_director)

---

### ExecutiveDirectorDashboard (Directors/Admins)

**Purpose:** Emergency response and platform-level threat mitigation.

**Four Main Sections:**

#### 1. Critical Alert Banner
- Shows when critical threats exist (critical severity reports)
- Fast-access EMERGENCY MODE button

#### 2. Threats Tab (from escalations)
- Same reported content, but director can see escalated reports
- **Unrestricted Actions:**
  - Delete content immediately (no confirmation)
  - Ban users with no appeal process
  - Lock accounts
  - Disable features
  - Issue IP-level bans

#### 3. Emergency Controls Tab
- **Lock Platform (Read-Only Mode)** — Users can view but not post/enroll/publish
- **Shut Down Marketplace** — Prevent new course enrollments and publishing
- **Ban by IP Address** — Block IP ranges for coordinated attacks
- **Disable Feature** — Instantly disable comments, messaging, reviews, marketplace
- **Broadcast Emergency Message** — Send notification to all users explaining situation

#### 4. Audit Logs Tab
- Shows all control actions (locks, bans, shutdowns, feature disables)
- Timestamps and status

---

## Permission Hierarchy

| Action | Moderator | Steward | Elder | Director | Admin |
|--------|-----------|---------|-------|----------|-------|
| Delete content | ✓ | ✓ | ✓ | ✓ | ✓ |
| Ban user | ✓ | ✓ | ✓ | ✓ | ✓ |
| Warn user | ✓ | ✓ | ✓ | ✓ | ✓ |
| Escalate to Director | ✗ | ✓ | ✓ | — | ✓ |
| **Lock Platform** | ✗ | ✗ | ✗ | ✓ | ✓ |
| **Ban by IP** | ✗ | ✗ | ✗ | ✓ | ✓ |
| **Disable Feature** | ✗ | ✗ | ✗ | ✓ | ✓ |
| **Broadcast Message** | ✗ | ✗ | ✗ | ✓ | ✓ |

---

## Threat Response Workflow

### Scenario 1: Spam/Low-Risk Content
**Moderator Flow:**
1. User reports spam in community forum (5+ reports)
2. Moderator sees it in "Reported Content" tab
3. Clicks **DELETE CONTENT** → post removed
4. Post author gets automated warning
5. Action logged in audit trail

### Scenario 2: Coordinated Harassment
**Escalation Flow:**
1. Multiple reports come in (15+ reports for same user)
2. Risk scoring flags: `coordinated_harassment`, `ban_evasion_suspected`
3. Moderator can delete individual posts, warn user, or **ESCALATE**
4. Steward reviews escalation and can:
   - Ban the user themselves
   - Escalate again to Director if it's part of larger threat pattern

### Scenario 3: Fraud/Payment Manipulation
**Director-Level Flow:**
1. Creator submits 3 payouts in 1 hour (automated fraud detection)
2. Report appears as CRITICAL severity
3. Moderators can't directly access payout data (permission boundary)
4. **ESCALATE TO DIRECTOR** button
5. Director sees full financial data in ExecutiveDirectorDashboard
6. Director can:
   - Ban creator immediately
   - Lock their account to prevent further payouts
   - Delete all their posts
   - Issue IP ban if coordinated attack

### Scenario 4: Coordinated Attack
**Emergency Mode Flow:**
1. Multiple accounts posting hate speech simultaneously (50+ reports in 2 min)
2. Director triggered (escalated by Stewards or auto-flagged)
3. Director can **LOCK PLATFORM** to read-only immediately
4. Broadcasts: "We detected a coordinated attack. We're investigating. You can view but posting is disabled."
5. Once threat assessed: ban the accounts, re-enable posting
6. Or **BAN BY IP** to block the entire attack source

---

## Implementation Details

### Frontend Permission Gating

```jsx
// In AdminDashboard.jsx
const canDelete = ["moderator", "steward", "elder", "admin"].includes(userRole);
const canBan = ["moderator", "steward", "elder", "admin"].includes(userRole);
const canEscalate = ["steward", "elder", "admin"].includes(userRole);
const canLockPlatform = ["elder", "admin"].includes(userRole); // Director-only
```

Buttons are shown/hidden based on user's role.

### Backend Enforcement (RBAC)

```python
# backend/security/rbac.py
UserRole.MODERATOR can:
  - moderate_posts
  - delete_harmful_content
  - ban_users
  - issue_warnings

UserRole.STEWARD can:
  - All moderator permissions +
  - vote_on_decisions
  - propose_changes
  - allocate_creator_fund

UserRole.ADMIN can:
  - All permissions (unrestricted)
  - manage_users, modify_system_settings, access_database
```

Every API endpoint checks permissions:
```python
@router.post("/moderation/content/{content_id}/delete")
@require_permission("delete_harmful_content")
async def delete_content(request: Request, content_id: str):
    # Backend verifies user.role has permission before deleting
    # Logs action to audit trail
```

### Audit Logging

All moderation actions logged with:
- User ID who took action
- Action type (delete, ban, warn, escalate, lock_platform)
- Target (content_id or user_id)
- Reason provided
- Timestamp
- Result (success/failure)

**7-year retention** for compliance (GDPR, SOC 2).

---

## What Escalation Looks Like

When a **Steward escalates to Director:**

1. Report status changes from `open` → `escalated_to_director`
2. Report appears in Director's ExecutiveDirectorDashboard marked "ESCALATED"
3. Director's action log shows: "Awaiting Director action"
4. Director has access to:
   - Full user profile (including payout methods, IP address, login history)
   - All user's posts/comments
   - Financial data (if fraud related)
   - Platform-level controls

---

## Why Two Dashboards?

**AdminDashboard** is for **daily operations:**
- Fast, focused moderation workflow
- Clear permission boundaries
- Prevents accidental platform-wide actions
- Moderators don't see sensitive data they don't need

**ExecutiveDirectorDashboard** is for **emergencies:**
- Unrestricted access (you're the CEO/Director)
- Can immediately shut down threats
- Has access to all sensitive data
- Can take platform-level actions (lock, disable features)

This separation of concerns ensures:
- ✓ Moderators can't accidentally lock the entire platform
- ✓ Directors have what they need in an emergency
- ✓ Clear audit trail of who did what and when
- ✓ Role-based permissions enforced on both frontend and backend

---

## Testing the System

```
[ ] User with moderator role sees AdminDashboard only
[ ] User with steward role sees AdminDashboard + escalate option
[ ] User with director role sees both dashboards
[ ] Moderator cannot see escalate button
[ ] Steward CAN see escalate button
[ ] Director cannot "escalate" (they're the final level)
[ ] Deleted content hidden from non-mods
[ ] All actions appear in audit log within 1 second
[ ] IP ban actually blocks requests from that range
[ ] Platform lock prevents all posts/enrollments/publishing
[ ] Feature disable works (e.g., comments disabled, messaging disabled)
[ ] Broadcast message appears to all users
```

---

## Security Notes

1. **Frontend is UX only** — Backend MUST verify every permission
2. **Never trust role from client** — Verify in backend every time
3. **All sensitive actions logged** — Bans, deletions, escalations
4. **Rate limits on moderation** — Prevent bulk actions (100 deletes/hour max)
5. **Escalation email alerts** — Director gets notified when steward escalates
