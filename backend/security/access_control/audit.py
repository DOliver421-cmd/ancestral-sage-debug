"""audit.py — Write-only, encrypted denial audit buffer (compliance trail).

The ONLY way into this buffer is DenialAuditBuffer.record(). There is no
update/delete API anywhere in the app — records are:

  1. appended to the MongoDB collection ``access_control_denials``
     (append-only by construction; the app never updates or deletes them), and
  2. appended to ``backend/logs/access_denials.log`` (opened in append mode
     with 0600 permissions; the file is never rewritten or truncated).

Encryption: Fernet from the ``cryptography`` package (already a pinned backend
dependency).  The key is a base64 32-byte Fernet key supplied via the
``AUDIT_ENCRYPTION_KEY`` environment variable.  When the key is absent the
buffer still records (compliance must never break the gate) but every record
is flagged ``encrypted: false`` and a compliance warning is logged at startup.

Reads exist ONLY for the executive dashboard (decrypt + display); there is no
mutation path.

Typical record entry (already PII-free — the gateway strips/never includes
emails, passwords, IPs or tokens):

    {
        "actor_id": "uuid" | None,
        "control": "exec_control_layer",
        "control_label": "Exec Control Layer",
        "path": "/api/exec/control/state",
        "method": "GET",
        "reason": "insufficient_tier",
        "user_role": "student",
        "user_tier": "user",
        "required_tier": "executive",
    }
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger("lcewai.access_control.audit")

# Non-sensitive query fields kept PLAINTEXT so the dashboard can aggregate and
# filter without decrypting every row.  Everything else lives in `payload`.
_PLAINTEXT_FIELDS = ("at", "control", "reason")


class DenialAuditBuffer:
    """Append-only, encrypted compliance buffer for access denials."""

    def __init__(self, file_path: Path | None = None) -> None:
        self._db = None
        self._fernet = None
        self.encrypted = False
        self._file_path = Path(file_path) if file_path else (
            Path(__file__).resolve().parents[2] / "logs" / "access_denials.log"
        )

    # ── Wiring ────────────────────────────────────────────────────────────────
    def bind(self, db, encryption_key: str | None = None) -> None:
        """Attach the DB handle and (optionally) enable Fernet encryption."""
        self._db = db
        if encryption_key:
            try:
                from cryptography.fernet import Fernet

                self._fernet = Fernet(
                    encryption_key.encode("ascii")
                    if isinstance(encryption_key, str)
                    else encryption_key
                )
                self.encrypted = True
            except Exception:
                self._fernet = None
                self.encrypted = False
                logger.error(
                    "AUDIT COMPLIANCE: invalid AUDIT_ENCRYPTION_KEY — "
                    "denial records will be stored PLAINTEXT"
                )
        if not self.encrypted:
            logger.warning(
                "AUDIT COMPLIANCE: AUDIT_ENCRYPTION_KEY is not set — denial "
                "records are stored UNENCRYPTED. Set it to a Fernet key "
                "(python -c 'from cryptography.fernet import Fernet; "
                "print(Fernet.generate_key().decode())') before go-live."
            )

    # ── Write path (the ONLY mutation in this module) ─────────────────────────
    async def record(self, entry: dict) -> None:
        """Append one denial record to the encrypted, write-only buffer."""
        entry = dict(entry or {})
        now = datetime.now(timezone.utc).isoformat()
        control = entry.get("control") or "unknown"
        record = {
            "id": str(uuid.uuid4()),
            "at": now,
            "control": control,
            "reason": entry.get("reason"),
            "encrypted": self.encrypted,
            "payload": self._encrypt(entry),
        }

        # 1) MongoDB — append-only collection (never updated/deleted by the app)
        if self._db is not None:
            try:
                await self._db.access_control_denials.insert_one(dict(record))
            except Exception:
                logger.exception("AUDIT: mongo append failed (denial still logged to file)")

        # 2) Local append-only file — 0600, opened 'a' only, never rewritten
        try:
            self._file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._file_path, "a", encoding="utf-8") as fh:
                os.fchmod(fh.fileno(), 0o600)
                fh.write(json.dumps(record, default=str) + "\n")
        except Exception:
            logger.exception("AUDIT: file append failed")

    # ── Read paths (dashboard only; strictly read-only) ───────────────────────
    async def recent(self, limit: int = 50) -> list:
        """Most recent denials, decrypted. Prefers Mongo, falls back to the file."""
        if self._db is not None:
            try:
                docs = (
                    await self._db.access_control_denials.find(
                        {}, {"_id": 0}
                    ).sort("at", -1).limit(limit).to_list(length=limit)
                )
                return [self._decrypt_row(d) for d in docs]
            except Exception:
                logger.exception("AUDIT: mongo read failed (falling back to file)")
        return self._recent_from_file(limit)

    async def stats(self, limit: int = 500) -> dict:
        """Per-control denial counts + last-denied timestamp (plaintext fields)."""
        counts: dict = {}
        if self._db is not None:
            try:
                docs = (
                    await self._db.access_control_denials.find(
                        {}, {"_id": 0, "at": 1, "control": 1}
                    ).sort("at", -1).limit(limit).to_list(length=limit)
                )
            except Exception:
                logger.exception("AUDIT: stats query failed")
                docs = []
            for d in docs:
                c = d.get("control") or "unknown"
                s = counts.setdefault(c, {"denials": 0, "last_denied_at": None})
                s["denials"] += 1
                if s["last_denied_at"] is None:
                    s["last_denied_at"] = d.get("at")
            return counts

        # File fallback
        rows = self._recent_from_file(limit * 4)
        for row in rows:
            c = row.get("control") or "unknown"
            s = counts.setdefault(c, {"denials": 0, "last_denied_at": None})
            s["denials"] += 1
            if s["last_denied_at"] is None:
                s["last_denied_at"] = row.get("at")
        return counts

    # ── Internals ─────────────────────────────────────────────────────────────
    def _encrypt(self, entry: dict) -> str:
        blob = json.dumps(entry, default=str)
        if self._fernet is None:
            return blob
        return self._fernet.encrypt(blob.encode("utf-8")).decode("ascii")

    def _decrypt_row(self, row: dict) -> dict:
        out = {k: v for k, v in row.items() if k in _PLAINTEXT_FIELDS}
        payload = row.get("payload")
        if payload and row.get("encrypted"):
            if self._fernet is not None:
                try:
                    payload = self._fernet.decrypt(payload.encode("ascii")).decode("utf-8")
                except Exception:
                    payload = None
            else:
                payload = None  # key unavailable — never leak ciphertext as plaintext
        if payload:
            try:
                out.update(json.loads(payload))
            except (TypeError, ValueError):
                out["_decrypt_error"] = True
        else:
            out["_masked"] = True  # encrypted and key unavailable
        return out

    def _recent_from_file(self, limit: int) -> list:
        try:
            if not self._file_path.exists():
                return []
            lines = self._file_path.read_text(encoding="utf-8").splitlines()
        except Exception:
            logger.exception("AUDIT: file read failed")
            return []
        rows = []
        for line in reversed(lines[-limit * 4:]):
            try:
                rows.append(self._decrypt_row(json.loads(line)))
            except (ValueError, TypeError):
                continue
            if len(rows) >= limit:
                break
        return rows
