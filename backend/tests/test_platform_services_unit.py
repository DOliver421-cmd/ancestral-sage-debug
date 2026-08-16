"""Unit tests for platform_services (CORS origin policy + security headers).

These pin the security posture extracted from server.py (slice 3) so a future
edit cannot silently re-break the Gumroad storefront iframe (CSP frame-src) or
the first-party CORS allowlist that unblocks login from www.morehelp.center.
No database or live server required.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import platform_services  # noqa: E402

PERF_TAG = "pytest_platform_services_unit"


class FakeResponse:
    def __init__(self):
        self.headers = {}


async def fake_call_next(request):
    return FakeResponse()


def test_auto_origins_include_first_party():
    assert "https://www.morehelp.center" in platform_services.AUTO_CORS_ORIGINS
    assert "https://morehelp.center" in platform_services.AUTO_CORS_ORIGINS
    assert "https://wai-institute.org" in platform_services.AUTO_CORS_ORIGINS
    assert "https://www.wai-institute.org" in platform_services.AUTO_CORS_ORIGINS
    assert "https://ancestral-sage-debug-production.up.railway.app" in platform_services.AUTO_CORS_ORIGINS


def test_build_cors_origins_auto_appends_first_party_when_env_partial():
    # Simulates Railway where CORS_ORIGINS may be set to a partial list.
    origins = platform_services.build_cors_origins(
        "https://ancestral-sage-debug-production.up.railway.app", backup_origin=""
    )
    assert "https://www.morehelp.center" in origins
    assert "https://morehelp.center" in origins
    assert "https://wai-institute.org" in origins
    assert "https://ancestral-sage-debug-production.up.railway.app" in origins


def test_build_cors_origins_keeps_backup_origin():
    origins = platform_services.build_cors_origins(
        "https://x.example.com", backup_origin="https://your-tunnel.trycloudflare.com"
    )
    assert "https://your-tunnel.trycloudflare.com" in origins


def test_build_cors_origins_wildcard_does_not_append():
    # "*" means allow everything — no point appending first-party origins.
    origins = platform_services.build_cors_origins("*", backup_origin="https://tunnel.example.com")
    assert origins == ["*"]


def test_build_cors_origins_empty_env_gets_full_first_party_set():
    origins = platform_services.build_cors_origins("", backup_origin="")
    assert set(platform_services.AUTO_CORS_ORIGINS) <= set(origins)


def _collect_headers():
    import asyncio

    async def _run():
        resp = await platform_services.security_headers(None, fake_call_next)
        return resp.headers

    return asyncio.run(_run())


def test_security_headers_pin_csp_and_frame_ancestors():
    headers = _collect_headers()
    csp = headers["Content-Security-Policy"]
    # The Gumroad storefront iframe must stay framable (the fix that unblocked the store).
    assert "frame-src https://namoshun.gumroad.com https://gumroad.com" in csp
    # The platform itself must not be framable elsewhere.
    assert "frame-ancestors 'none'" in csp
    # TTS audio (createObjectURL) stays allowed.
    assert "media-src 'self' blob:" in csp


def test_security_headers_basic_set():
    headers = _collect_headers()
    assert headers["X-Frame-Options"] == "DENY"
    assert headers["X-Content-Type-Options"] == "nosniff"
    assert headers["Strict-Transport-Security"] == "max-age=31536000; includeSubDomains"
    assert headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert headers["Permissions-Policy"] == "geolocation=(), microphone=(self), camera=()"
