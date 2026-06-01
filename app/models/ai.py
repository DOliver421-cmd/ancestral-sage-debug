"""app/models/ai.py — AI-related Pydantic request/response models.

Extracted from backend/server.py lines 553–637.
No logic changed.
"""
from typing import List, Literal, Optional

from pydantic import BaseModel


class AIChatReq(BaseModel):
    session_id: str
    message: str
    module_slug: Optional[str] = None
    mode: Literal[
        "tutor",
        "scripture",
        "quiz_gen",
        "explain",
        "nec_lookup",
        "blueprint",
        "ancestral_sage",
    ] = "tutor"
    depth: Optional[Literal["beginner", "intermediate", "advanced"]] = None
    intensity: Optional[Literal["gentle", "moderate", "deep"]] = None
    cultural_focus: Optional[str] = None
    divination_mode: Optional[Literal["teaching", "reading", "practice", "predictive"]] = None
    safety_level: Optional[Literal["conservative", "standard", "exploratory", "extreme"]] = None
    consent_log_id: Optional[str] = None
    scope: Optional[Literal["wai_training_only"]] = None


class OrchestratorHistoryItem(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class OrchestratorReq(BaseModel):
    session_id: str
    message: str
    history: Optional[list[OrchestratorHistoryItem]] = []
    file_b64: Optional[str] = None
    file_name: Optional[str] = None
    file_type: Optional[str] = None
    threat_hint: Optional[str] = None
    protocol: Optional[Literal[
        "rapid_threat_response",
        "full_council_session",
        "curriculum_design",
        "quiet_checkin",
    ]] = None


class ScholarTaskReq(BaseModel):
    session_id: str
    message: str
    history: Optional[list[OrchestratorHistoryItem]] = []
    task_context: Optional[str] = None
    task_type: Optional[Literal[
        "curriculum",
        "assessment",
        "study_plan",
        "path_design",
        "counter_curriculum",
        "general",
    ]] = "general"


class AIConsentReq(BaseModel):
    persona: Literal["ancestral_sage"]
    confirm_yes: str
    comprehension: str
    intensity: Optional[str] = None
    safety_level: Optional[str] = None
    disclaimer1_ack: bool = False
    disclaimer2_ack: bool = False
    disclaimer3_ack: bool = False
    content_type: Optional[Literal[
        "general", "personalization", "high_confidence", "high_consensus"
    ]] = "general"
    confidence_level: Optional[Literal["low", "medium", "high"]] = None
    expert_score: Optional[int] = None
    request_human_review: bool = False
    store_audio: bool = False


class ResolveModeReq(BaseModel):
    session_id: str
    user_intent: str
    recent_topics: Optional[list[str]] = None


class SafetyCapReq(BaseModel):
    """Body for global cap or per-user cap."""
    level: Optional[Literal["conservative", "standard", "exploratory", "extreme"]] = None


class SageTTSReq(BaseModel):
    text: str
    voice: Optional[Literal[
        "alloy", "ash", "coral", "echo", "fable", "nova", "onyx", "sage", "shimmer"
    ]] = "sage"
    speed: Optional[float] = 1.0
    session_id: Optional[str] = None
