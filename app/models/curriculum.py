"""app/models/curriculum.py — Module, Progress, and Quiz Pydantic models.

Extracted from backend/server.py lines 513–551.
No logic changed.
"""
import uuid
from datetime import datetime, timezone
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class QuizQ(BaseModel):
    q: str
    options: List[str]
    answer: int


class Module(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    order: int
    slug: str
    title: str
    summary: str
    objectives: List[str]
    safety: List[str]
    tools: List[str]
    scripture: dict
    tasks: List[str]
    competencies: List[str]
    hours: int
    quiz: List[QuizQ] = []


class ProgressEntry(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    module_slug: str
    status: Literal["not_started", "in_progress", "completed"] = "in_progress"
    quiz_score: Optional[float] = None
    completed_at: Optional[datetime] = None
    hours_logged: int = 0
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class QuizSubmit(BaseModel):
    module_slug: str
    answers: List[int]
