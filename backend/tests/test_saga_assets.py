"""
Unit tests for the Vonns Saga media pipeline — pure logic only.

Covers the ffmpeg command builders (Ken Burns segments + xfade concat) and
the saga asset policies. MongoDB/GridFS/ffmpeg execution are integration
concerns exercised in production; these tests pin the deterministic parts.
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from routers.saga import build_segment_command, build_concat_command_explicit  # noqa: E402


# ── Segment command (single image → zoompan clip) ────────────────────────────

def test_segment_command_shape():
    cmd = build_segment_command("img.png", seg_duration=5.0, output="seg.mp4")
    assert cmd[0] == "ffmpeg"
    assert "-y" in cmd
    assert "-loop" in cmd and "1" in cmd
    assert "-t" in cmd and "5.000" in cmd
    assert "-i" in cmd and "img.png" in cmd
    assert "-c:v" in cmd and "libx264" in cmd
    flat = " ".join(cmd)
    assert "zoompan" in flat
    assert "1080x1920" in flat  # default vertical short-form size


def test_segment_zoom_directions_differ():
    zoom_in = build_segment_command("a.png", 5.0, "a.mp4", zoom_in=True)
    zoom_out = build_segment_command("a.png", 5.0, "a.mp4", zoom_in=False)
    zi = next(x for x in zoom_in if "zoompan" in x)
    zo = next(x for x in zoom_out if "zoompan" in x)
    assert zi != zo  # one zooms in, the other out — alternating motion


# ── Concat command (xfade chain) ─────────────────────────────────────────────

def test_concat_single_segment_copies():
    cmd = build_concat_command_explicit(["seg.mp4"], "out.mp4", seg_duration=5.0)
    assert cmd[0] == "ffmpeg"
    assert "-c" in cmd and "copy" in cmd
    assert "filter_complex" not in cmd


def test_concat_multi_segment_offsets():
    cmd = build_concat_command_explicit(
        ["a.mp4", "b.mp4", "c.mp4"], "out.mp4", seg_duration=5.0, fade=0.5
    )
    fc = cmd[cmd.index("-filter_complex") + 1]
    # 2 transitions for 3 segments: offsets at 4.5 and 9.0
    assert "offset=4.500" in fc
    assert "offset=9.000" in fc
    assert "xfade=transition=fade:duration=0.500" in fc
    assert "-map" in cmd and "[vout]" in cmd
    # default color params: h264 + yuv420p for browser playback
    assert "libx264" in cmd
    assert "yuv420p" in cmd


def test_concat_with_soundtrack_maps_audio():
    cmd = build_concat_command_explicit(
        ["a.mp4", "b.mp4"], "out.mp4", seg_duration=5.0, soundtrack="snd.mp3"
    )
    assert "-i" in cmd and "snd.mp3" in cmd
    assert "-map" in cmd and f"{2}:a" in cmd  # inputs: a.mp4(0) b.mp4(1) snd(2)
    assert "-c:a" in cmd and "aac" in cmd
    assert "-shortest" in cmd


def test_concat_fade_clamped_to_segment():
    # fade can never exceed half a segment
    cmd = build_concat_command_explicit(["a.mp4", "b.mp4"], "out.mp4", seg_duration=2.0, fade=1.9)
    fc = cmd[cmd.index("-filter_complex") + 1]
    assert "duration=0.950" in fc  # clamped to seg/2 - 0.05


def test_concat_rejects_empty():
    import pytest
    with pytest.raises(ValueError):
        build_concat_command_explicit([], "out.mp4", seg_duration=5.0)


# ── Asset policies (no fakes allowed) ────────────────────────────────────────

def test_saga_endpoints_never_return_fake_status():
    """The saga router must not fabricate 'processing' records — a video is
    either rendering (queued), ready (real file), or render_failed (reason)."""
    import inspect
    from routers import saga
    src = inspect.getsource(saga)
    # The fake status string from the old implementation must be gone.
    assert '"status": "processing"' not in src
    # The renderer must explicitly handle missing ffmpeg instead of lying.
    assert "ffmpeg is not installed" in src


def test_ai_assisted_disclosure_present():
    """Every video asset records ai_assisted=True (mission: clearly AI-assisted)."""
    import inspect
    from routers import saga
    src = inspect.getsource(saga)
    assert '"ai_assisted": True' in src


def test_saga_writes_are_admin_gated():
    """Track/image/video/concert uploads require staff roles (no anonymous writes)."""
    import inspect
    from routers import saga
    src = inspect.getsource(saga)
    # Every write endpoint carries the staff role gate.
    assert src.count('_require_rank("admin", "executive_admin", "support_staff", "oversight")') >= 4
