"""app/services/llm.py — Shared LLM helper using Groq → Cerebras → Mistral fallback chain."""
import logging
import os
from typing import Optional

import httpx
from fastapi import HTTPException

logger = logging.getLogger("lcewai")

_PROVIDERS = [
    {
        "name": "groq",
        "url": "https://api.groq.com/openai/v1/chat/completions",
        "key_env": "GROQ_API_KEY",
        "model": "llama-3.3-70b-versatile",
    },
    {
        "name": "cerebras",
        "url": "https://api.cerebras.ai/v1/chat/completions",
        "key_env": "CEREBRAS_API_KEY",
        "model": "llama3.1-70b",
    },
    {
        "name": "mistral",
        "url": "https://api.mistral.ai/v1/chat/completions",
        "key_env": "MISTRAL_API_KEY",
        "model": "mistral-large-latest",
    },
]


async def chat(system: str, user: str, max_tokens: int = 2048) -> str:
    """Call AI using Groq → Cerebras → Mistral fallback chain."""
    payload_base = {
        "max_tokens": max_tokens,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    last_err: Optional[Exception] = None
    for provider in _PROVIDERS:
        key = os.environ.get(provider["key_env"], "")
        if not key:
            continue
        try:
            payload = {**payload_base, "model": provider["model"]}
            async with httpx.AsyncClient(timeout=60) as c:
                r = await c.post(
                    provider["url"],
                    headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                    json=payload,
                )
                r.raise_for_status()
                return r.json()["choices"][0]["message"]["content"]
        except Exception as e:
            logger.warning("LLM provider %s failed: %s", provider["name"], e)
            last_err = e
    raise HTTPException(503, f"No AI provider available. Last error: {last_err}")
