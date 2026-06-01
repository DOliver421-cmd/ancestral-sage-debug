# Security & Role-Based Access Control (RBAC)

## Overview

WAI has a multi-tiered security model:
1. **Role-Based Access Control (RBAC)** — Who can do what
2. **Partnership-Based Permissions** — Governance access tied to partnership level
3. **Data Visibility** — Who can see what
4. **Audit Logging** — Track all sensitive actions

---

## User Roles & Hierarchy

```
Guest
  ↓
Student
  ↓
Creator/Mentor
  ↓
Moderator (parallel to Creator)
  ↓
Steward (has both Creator + Moderator powers)
  ↓
Elder (Steward + Board access)
  ↓
Admin (all permissions)
```

### Role Definitions

| Role | Can Do | Example |
|------|--------|---------|
| **Guest** | Browse marketplace, view public profiles | New user exploring |
| **Student** | Enroll courses, write reviews, post in community | Active learner |
| **Creator** | Publish courses, view earnings, mentor | Teacher/artist |
| **Mentor** | All Creator + structure mentorship programs | Senior guide |
| **Moderator** | Delete harmful content, ban users, pin posts | Community guardian |
| **Steward** | All Creator + Moderator + vote on decisions | Leadership |
| **Elder** | All Steward + board advisory, shape platform | Founder-level |
| **Admin** | Everything + system configuration | Staff only |

---

## Permission Matrix

### Content Creation
```
Action              | Guest | Student | Creator | Mentor | Steward | Elder | Admin
─────────────────────────────────────────────────────────────────────────────────
Create Post         |       |    ✓    |    ✓    |   ✓    |    ✓    |   ✓   |  ✓
Publish Course      |       |         |    ✓    |   ✓    |    ✓    |   ✓   |  ✓
Upload Media        |       |         |    ✓    |   ✓    |    ✓    |   ✓   |  ✓
```

### Moderation
```
Action              | Guest | Student | Creator | Mentor | Steward | Elder | Admin
─────────────────────────────────────────────────────────────────────────────────
Delete Comment      |       |         |         |        |    ✓    |   ✓   |  ✓
Ban User            |       |         |         |        |    ✓    |   ✓   |  ✓
Pin Discussion      |       |         |         |        |    ✓    |   ✓   |  ✓
Review Reports      |       |         |         |        |    ✓    |   ✓   |  ✓
```

### Governance
```
Action              | Guest | Student | Creator | Mentor | Steward | Elder | Admin
─────────────────────────────────────────────────────────────────────────────────
Vote on Decisions   |       |         |         |        |    ✓    |   ✓   |  ✓
Propose Changes     |       |         |         |        |    ✓    |   ✓   |  ✓
Allocate Fund       |       |         |         |        |    ✓    |   ✓   |  ✓
Board Advisory      |       |         |         |        |         |   ✓   |  ✓
```

### Admin
```
Action              | Guest | Student | Creator | Mentor | Steward | Elder | Admin
─────────────────────────────────────────────────────────────────────────────────
Manage Users        |       |         |         |        |         |       |  ✓
Modify Settings     |       |         |         |        |         |       |  ✓
View All Analytics  |       |         |         |        |         |       |  ✓
Access Database     |       |         |         |        |         |       |  ✓
```

---

## Partnership-Based Permissions

In addition to role, users earn governance rights through partnership milestones:

| Partnership | Can Do |
|-------------|--------|
| **Seed** (0-100 pts) | Only basic features |
| **Rooted** (100-300 pts) | Vote on discussions, apply for mentorship |
| **Builder** (300-800 pts) | Vote on minor proposals, propose small changes |
| **Steward** (800-2000 pts) | Full governance voting, allocate funds |
| **Elder** (2000+ pts) | Board advisory access, shape platform direction |

**Example:** A Creator with 350 partnership points (Builder level) can:
- All Creator permissions
- Vote on minor platform proposals
- Propose changes to course categories

But cannot:
- Vote on major decisions (requires Steward level)
- Access board meetings
- Approve strategic changes

---

## Data Visibility Rules

### Profile Fields - Who Can See What?

**User's Own Profile:**
- ✓ Email, phone, account settings
- ✓ Total earnings, payout method
- ✓ Private messages
- ✓ Payment methods
- ✓ Login history

**User Viewing Creator's Profile:**
- ✓ Courses published, student count
- ✓ Average rating
- ✓ Bio, website, social links
- ✗ Earnings breakdown
- ✗ Payout method
- ✗ Student list

**Admin Viewing Any Profile:**
- ✓ Everything

**Moderator Viewing Reported User:**
- ✓ Basic info, public activity
- ✓ Report history
- ✓ Previous warnings
- ✗ Payment info
- ✗ Private messages

### Financial Data - Strict Controls

| Viewer | Can See | Cannot See |
|--------|---------|------------|
| Creator (own data) | All earnings, payouts | Others' earnings |
| Steward/Elder | Total volume, trends | Individual payouts, methods |
| Admin | Everything | (nothing restricted) |

**Rule:** Banking info (account numbers, last 4 digits) only visible to account owner and admins.

---

## Sensitive Actions Requiring Audit Log

Every sensitive action gets logged:

```python
# Audit events
- User role changed: admin_id, user_id, old_role, new_role
- Payout requested: creator_id, amount, date
- Course published: creator_id, course_id, price
- User banned: moderator_id, user_id, reason
- Financial report accessed: admin_id, timestamp
- Course deleted: creator_id, admin_id (if force-deleted)
- Fund allocation voted: steward_id, amount, date
```

**Retention:** All audit logs kept for 7 years (compliance).

---

## Implementation: Backend

### FastAPI Middleware
```python
from fastapi import Request, HTTPException
from security.rbac import AccessControl, UserRole

async def check_permission_middleware(request: Request, permission: str):
    """Middleware to enforce permissions"""
    user = request.state.user  # Set by auth middleware
    if not AccessControl.has_permission(user.role, permission):
        raise HTTPException(status_code=403, detail="Permission denied")

# Usage in route
@router.post("/courses/publish")
async def publish_course(
    request: Request,
    course_id: str,
):
    user = request.state.user
    if not AccessControl.has_permission(user.role, "publish_course"):
        raise HTTPException(status_code=403, detail="Not authorized")
    # ... publish logic
```

### Permission Decorator
```python
from functools import wraps

def require_permission(permission: str):
    """Decorator to enforce permission"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, request: Request, **kwargs):
            user = request.state.user
            if not AccessControl.has_permission(user.role, permission):
                raise HTTPException(status_code=403, detail="Permission denied")
            return await func(*args, request=request, **kwargs)
        return wrapper
    return decorator

# Usage
@router.post("/courses/publish")
@require_permission("publish_course")
async def publish_course(request: Request, course_id: str):
    # Logic here
    pass
```

### Data Filtering
```python
from security.rbac import AccessControl

@router.get("/users/{user_id}")
async def get_user_profile(user_id: str, request: Request):
    user = request.state.user
    target = await db.users.find_one({"_id": user_id})
    
    # Determine visible fields
    visible_fields = AccessControl.get_visible_profile_fields(
        user.id, target.id, user.role, target.role
    )
    
    # Filter profile data
    profile = {k: v for k, v in target.items() if k in visible_fields}
    return {"status": "success", "profile": profile}
```

---

## Implementation: Frontend

### Permission Gating
```jsx
import { canPerformAction, canAccessFeature } from "../lib/security";

function PublishCourseButton({ user, partnership }) {
  const canPublish = canPerformAction(user.role, "publish_course");
  const canAccessFeature = canAccessFeature(
    partnership.level,
    "publish_course"
  );

  if (!canPublish || !canAccessFeature) {
    return (
      <button disabled className="btn-disabled">
        Requires Creator role + Builder partnership
      </button>
    );
  }

  return <button onClick={publishCourse}>Publish Course</button>;
}
```

### Sensitive Data Filtering
```jsx
function UserProfile({ userId, viewerId, viewerRole }) {
  const [user, setUser] = useState(null);

  useEffect(() => {
    const visibleFields = getVisibleProfileFields(
      { userId: viewerId, role: viewerRole },
      user
    );
    const filtered = filterProfileData(user, visibleFields);
    setUser(filtered);
  }, [user]);

  // Only show what user can see
  return <div>{/* rendered with filtered data */}</div>;
}
```

### Audit Logging (Frontend)
```jsx
function RequestPayout() {
  const handlePayout = async (amount) => {
    logAuditAction(user.id, "payout_requested", "creator_payout", {
      amount,
      timestamp: new Date(),
    });
    // Send to backend...
  };
}
```

---

## Security Best Practices

### 1. Never Trust Frontend
- Frontend security is for UX only (showing/hiding features)
- Backend MUST verify every permission
- Never trust role/partnership level from client

### 2. Audit Everything Sensitive
- Payout requests
- Role changes
- Financial reports
- Course deletions
- User bans

### 3. Rate Limiting
- 10 API calls per minute per user (default)
- 50 posts per day per user
- 5 course publishes per month per user
- Prevent abuse while allowing normal use

### 4. Data Minimization
- Only request data you need
- Don't expose IDs that could be enumerated
- Mask sensitive data in logs

### 5. Encryption
- Payment info encrypted at rest
- TLS for all API calls
- Hash passwords with bcrypt

### 6. Session Security
- JWT tokens expire in 24 hours
- Refresh tokens stored in httpOnly cookies
- No sensitive data in tokens

---

## Role Assignment Rules

**How users get roles:**

| Role | Assignment | Escalation |
|------|-----------|-----------|
| Guest | Default | → Student (email verify) |
| Student | Email verification | → Creator (apply + review) |
| Creator | Application reviewed by steward | Can't escalate |
| Mentor | Steward+ vote | Can't escalate |
| Moderator | Steward+ appointment | Can't escalate |
| Steward | 800+ partnership points | Can't escalate |
| Elder | 2000+ partnership points | Can't escalate |
| Admin | CEO only | (permanent) |

**Key:** Regular roles not self-assigned. Steward/Elder are automatic based on partnership level.

---

## Controversy & Appeals

### If user disputes moderation action:
1. Moderator decision logged with reason
2. User can appeal to Steward+
3. 3 Stewards vote on appeal (majority rules)
4. Decision logged and appealer notified

### If user claims unfair treatment:
1. Audit log reviewed
2. Context provided to user
3. Escalation to Elder if needed
4. Anonymous board review if unresolved

---

## Testing Checklist

- [ ] User can only view own financial data
- [ ] Moderator cannot access payout info
- [ ] Admin can access everything
- [ ] Creator cannot publish without role
- [ ] Steward cannot govern without partnership level
- [ ] Deleted content hidden from non-mods
- [ ] Audit log captures all sensitive actions
- [ ] JWT refresh works correctly
- [ ] Rate limits prevent abuse
- [ ] Permission denial returns 403, not 401

---

## Compliance

- **GDPR:** Users can request/delete data. Logs kept per legal retention.
- **SOC 2:** Audit trails for all access. Encryption at rest.
- **Financial:** Stripe PCI compliance. No raw card data stored.
- **Accessibility:** RBAC transparent to users. Clear "why access denied" messages.

---

## Questions Users Might Ask

**Q: Can creators see my payout method?**
A: No. Only you and our admins can see banking info.

**Q: Can I escalate to Elder faster?**
A: Not artificially. Partnership level = real engagement. Keep building.

**Q: What if I disagree with a moderation decision?**
A: Appeal to a Steward. Your case reviewed by unbiased community leaders.

**Q: Are my conversations private?**
A: Between users and recipient only. We never read unless reported.

**Q: Can I opt out of being featured?**
A: Yes. Privacy settings on your profile.
