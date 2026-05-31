"""app/models/user.py — User and auth-related Pydantic models.

Extracted from backend/server.py lines 362–638.
No logic changed.
"""
import uuid
from datetime import datetime, timezone
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

Role = Literal["student", "instructor", "admin", "executive_admin"]


class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    full_name: str
    role: Role = "student"
    associate: Optional[str] = None
    is_active: bool = True
    must_change_password: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class RegisterReq(BaseModel):
    """Public self-registration."""
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=500)
    password: str = Field(..., min_length=8, max_length=128)
    agreed_terms: bool = False
    over_13: bool = False


class AdminCreateUserReq(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=500)
    password: str = Field(..., min_length=8, max_length=128)
    role: Role = "student"
    associate: Optional[str] = Field(None, min_length=1, max_length=200)


class AdminRoleReq(BaseModel):
    role: Role


class AdminEditUserReq(BaseModel):
    full_name: Optional[str] = Field(None, min_length=1, max_length=500)
    email: Optional[EmailStr] = None
    associate: Optional[str] = Field(None, min_length=1, max_length=200)


class AdminActiveReq(BaseModel):
    is_active: bool


class ChangePasswordReq(BaseModel):
    current_password: str = Field(..., min_length=8, max_length=128)
    new_password: str = Field(..., min_length=8, max_length=128)


class AdminResetPasswordReq(BaseModel):
    new_password: str = Field(..., min_length=8, max_length=128)


class ForgotPasswordReq(BaseModel):
    email: EmailStr


class ResetPasswordReq(BaseModel):
    token: str
    new_password: str


class EmergencyRecoveryReq(BaseModel):
    """Executive account emergency recovery via recovery code."""
    email: EmailStr
    recovery_code: str
    new_password: str


class RecoveryCodeStatusReq(BaseModel):
    """Check status of recovery codes for an executive account."""
    email: EmailStr


class SelfEditMeReq(BaseModel):
    """Self-service profile edit."""
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None


class LoginReq(BaseModel):
    email: EmailStr
    password: str


class TokenResp(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: User
