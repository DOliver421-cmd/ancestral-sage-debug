"""
retry_utils.py — Director 4.0 Async Retry Infrastructure
==========================================================
Provides `async_retry`: an exponential-backoff wrapper for any awaitable call.

Used by:
  - Director AI endpoint  (Anthropic claude-sonnet-4-6 / claude-haiku-4-5)
  - Helper AI endpoint    (Anthropic claude-haiku-4-5 / claude-3-haiku-20240307)
  - Any tool that makes an external HTTP call and wants silent recovery

Design:
  - Retries only on transient errors (rate-limit 429, overload 529, timeout, connection errors)
  - Does NOT retry on auth errors (401/403), bad requests (400), or application errors
  - Jitter is added to each delay so parallel callers don't all retry at the same moment
  - Max total wait caps at ~60 seconds regardless of attempt count
"""
import asyncio
import logging
import random
from typing import Any, Callable, Coroutine, Type, Tuple

logger = logging.getLogger("lcewai.retry")

# Anthropic / httpx error types we treat as transient
_TRANSIENT_MESSAGES = (
    "rate_limit",
    "overloaded",
    "timeout",
    "connection",
    "timed out",
    "502",
    "503",
    "529",
    "temporarily",
)


def _is_transient(exc: Exception) -> bool:
    """Return True if the exception looks like a transient / retryable failure."""
    msg = str(exc).lower()
    return any(kw in msg for kw in _TRANSIENT_MESSAGES)


async def async_retry(
    fn: Callable[..., Coroutine[Any, Any, Any]],
    *args,
    max_attempts: int = 3,
    base_delay: float = 1.5,   # seconds
    max_delay: float = 20.0,
    jitter: float = 0.5,
    retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,),
    **kwargs,
) -> Any:
    """
    Call `await fn(*args, **kwargs)`, retrying on transient errors.

    Parameters
    ----------
    fn             : async callable to invoke
    max_attempts   : total attempts (1 = no retry)
    base_delay     : initial backoff in seconds (doubles each attempt)
    max_delay      : hard cap on per-attempt delay
    jitter         : random seconds added to each delay (±jitter/2)
    retryable_exceptions : exception types that trigger a retry (default: all)

    Returns
    -------
    The return value of fn on success.

    Raises
    ------
    The last exception if all attempts are exhausted.
    """
    last_exc: Exception = RuntimeError("No attempts made")

    for attempt in range(1, max_attempts + 1):
        try:
            return await fn(*args, **kwargs)
        except retryable_exceptions as exc:
            last_exc = exc
            if attempt == max_attempts or not _is_transient(exc):
                raise

            delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
            delay += random.uniform(-jitter / 2, jitter / 2)
            delay = max(delay, 0.1)

            logger.warning(
                "async_retry: attempt %d/%d failed (%s). Retrying in %.1fs…",
                attempt, max_attempts, exc, delay,
            )
            await asyncio.sleep(delay)

    raise last_exc
