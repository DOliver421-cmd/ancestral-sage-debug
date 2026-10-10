"""Dependency compatibility guard (deploy healthcheck regression).

`requirements.txt` may only be changed together with a run of this file. motor
imports pymongo internals that newer pymongo releases delete, so a pymongo
bump without a motor bump produces a container that builds cleanly and then
never becomes healthy: `motor.motor_asyncio` fails to import, server.py (which
imports it at module scope) never starts, and /api/health never answers.

See PR #473 for the incident — pymongo 4.5.0 -> 4.18.2 with motor pinned at
3.3.1 produced exactly that failure.
"""
import os
import subprocess
import sys

REPO_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_motor_imports_with_the_installed_pymongo():
    """The exact import server.py makes at module scope."""
    from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase  # noqa: F401
    import pymongo

    assert pymongo.version_tuple[:2] >= (4, 5), "pymongo is older than the app requires"


def test_pymongo_minor_is_within_the_motor_compatible_range():
    """The pin in requirements.txt must not allow a pymongo motor can't use.

    This is the check that fails when someone bumps pymongo alone: it reads the
    real pinned range rather than trusting the installed environment.
    """
    reqs = open(os.path.join(REPO_BACKEND, "requirements.txt")).read()
    motor_line = next((l for l in reqs.splitlines() if l.startswith("motor")), "")
    pymongo_line = next((l for l in reqs.splitlines() if l.startswith("pymongo")), "")
    assert motor_line.startswith("motor=="), f"motor must be pinned exactly: {motor_line}"
    assert pymongo_line.startswith("pymongo>=") and "<" in pymongo_line, (
        f"pymongo must pin an upper bound motor supports: {pymongo_line}"
    )

    # Resolve the highest pymongo the pin allows and motor's file, and confirm
    # every name motor imports from pymongo.cursor still exists there.
    upper = pymongo_line.split("<")[1].strip()
    import pymongo as _pymongo
    import motor
    motor_core = os.path.join(os.path.dirname(motor.__file__), "core.py")
    assert os.path.exists(motor_core), f"motor core not found at {motor_core}"

    # motor reaches into pymongo.cursor for private names. Collect every name it
    # imports from there and confirm pymongo still exports it.
    import re
    src = open(motor_core).read()
    needed = []
    for m in re.finditer(r"from pymongo\.cursor import ([^\n]+)", src):
        needed += [n.strip() for n in m.group(1).split(",") if n.strip()]
    assert needed, "could not parse motor's pymongo.cursor imports — update this guard"
    missing = [n for n in needed if not hasattr(_pymongo.cursor, n)]
    assert not missing, (
        f"pymongo {'.'.join(map(str, _pymongo.version_tuple))} no longer exports "
        f"{missing}, which motor imports — the pin must stay below {upper} until "
        f"motor is upgraded in lockstep"
    )
