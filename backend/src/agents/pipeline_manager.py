"""
PipelineManager — LLM intent routing for social/media posts.

Provides:
- PipelineResult: structured result with .to_dict()
- PipelineManager: process() / process_batch() with LLM + keyword fallback
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional


class PipelineResult:
    """Single-item pipeline result."""

    def __init__(self, text: str, source: str, intent: str, confidence: float, entities: Optional[List[str]] = None):
        self.text = text
        self.source = source
        self.intent = intent
        self.confidence = confidence
        self.entities = entities or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "source": self.source,
            "intent": self.intent,
            "confidence": self.confidence,
            "entities": self.entities,
        }


class PipelineManager:
    """Routes text through LLM intent analysis with keyword fallback."""

    def __init__(self, db: Optional[Any] = None):
        self.db = db

    async def process(self, text: str, source: str = "api") -> PipelineResult:
        intent, confidence, entities = await self._analyze(text)
        return PipelineResult(text=text, source=source, intent=intent, confidence=confidence, entities=entities)

    async def process_batch(self, texts: List[str], source: str = "api") -> List[PipelineResult]:
        return [await self.process(t, source=source) for t in texts]

    async def _analyze(self, text: str) -> tuple[str, float, List[str]]:
        lowered = text.lower()
        intent = "general"
        confidence = 0.5
        entities: List[str] = []

        if any(k in lowered for k in ("buy", "purchase", "price", "cost", "$")):
            intent = "purchase_intent"
            confidence = 0.7
        elif any(k in lowered for k in ("help", "support", "issue", "problem", "broken")):
            intent = "support_request"
            confidence = 0.7
        elif any(k in lowered for k in ("join", "member", "sign up", "register")):
            intent = "conversion"
            confidence = 0.7
        elif any(k in lowered for k in ("event", "workshop", "class", "webinar")):
            intent = "event_interest"
            confidence = 0.65

        entities = [m.group(0) for m in re.finditer(r"@\w+", text)] or [w for w in text.split() if w.startswith("#")][:5]

        try:
            from ai.llm_gateway import call_llm
            result = await call_llm(
                system="You are an intent classifier. Return JSON with fields intent, confidence (0-1), entities (list).",
                messages=[{"role": "user", "content": text}],
                persona_label="pipeline:intent",
                user_id=None,
                max_tokens=200,
            )
            parsed = self._parse_llm_json((result or {}).get("text") or "")
            if parsed:
                intent = parsed.get("intent", intent)
                confidence = float(parsed.get("confidence", confidence))
                entities = parsed.get("entities", entities)
        except Exception:
            pass

        return intent, min(1.0, max(0.0, confidence)), entities[:10]

    @staticmethod
    def _parse_llm_json(raw: str) -> Optional[Dict[str, Any]]:
        import json
        try:
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if match:
                return json.loads(match.group(0))
        except Exception:
            pass
        return None
