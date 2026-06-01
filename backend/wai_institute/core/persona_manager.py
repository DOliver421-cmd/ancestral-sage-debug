"""
WAI-Institute PersonaManager
=============================
MongoDB-backed management of the full persona lifecycle.
Supports activate / deactivate / evolve / merge / clone / retire.

All state persists to db.persona_activations so the Director can
query, audit, and modify the persona network at runtime.

Works alongside the existing ai/persona_loader.py — the loader
provides the system prompt strings; this manager provides the
governance and lifecycle layer on top.
"""

import uuid
import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger("lcewai.persona_manager")

# Canonical persona tiers (matches persona_loader.py hierarchy)
PERSONA_TIERS = {
    "the_9":                  0,   # Tier 0 — unified mind, above all hierarchy
    "poor_righteous_teacher": 1,   # Tier 1 — doctrinal guardian, reports to Sage + Executive
    "director":               2,
    "revenue_director":       3,
    "ancestral_sage":         3,
    "ambassador":             4,
    "cipher":                 4,
    "oracle":                 4,
    "architect":              4,
}

# Who each persona reports to
REPORTING_LINES = {
    "the_9":                  "poor_righteous_teacher",
    "poor_righteous_teacher": None,   # Reports to Sage + Executive (dual authority — stored separately)
    "director":               None,
    "revenue_director":       "director",
    "ancestral_sage":         "director",
    "ambassador":             "director",
    "cipher":                 "ambassador",
    "oracle":                 "ambassador",
    "architect":              "ambassador",
}


class PersonaManager:
    """
    Lifecycle manager for all WAI-Institute personas.

    Usage:
        pm = PersonaManager(db)
        await pm.activate("cipher", config={...}, activated_by="director")
        await pm.evolve("cipher", add_capabilities=["shopify_publish"])
        status = await pm.status("cipher")
    """

    def __init__(self, db=None):
        self.db = db

    # ── Activate ──────────────────────────────────────────────────────────────

    async def activate(
        self,
        name: str,
        config: dict = None,
        mode: str = "active",
        scope: list = None,
        activated_by: str = "director",
    ) -> dict:
        """
        Activate or re-activate a persona. Upserts state in db.persona_activations.
        mode: active | limited | internal
        """
        now = datetime.now(timezone.utc).isoformat()
        name = name.lower().strip()

        doc = {
            "persona":       name,
            "status":        "active",
            "mode":          mode,
            "scope":         scope or ["internal_ops", "public_facing", "revenue"],
            "config":        config or {},
            "tier":          PERSONA_TIERS.get(name, 4),
            "reports_to":    REPORTING_LINES.get(name),
            "activated_by":  activated_by,
            "activated_at":  now,
            "updated_at":    now,
            "evolution_log": [],
        }

        if self.db is not None:
            try:
                existing = await self.db.persona_activations.find_one({"persona": name})
                if existing:
                    await self.db.persona_activations.update_one(
                        {"persona": name},
                        {"$set": {
                            "status":       "active",
                            "mode":         mode,
                            "config":       config or existing.get("config", {}),
                            "activated_by": activated_by,
                            "updated_at":   now,
                        }},
                    )
                    logger.info("PersonaManager: re-activated %s", name)
                else:
                    await self.db.persona_activations.insert_one({"_id": name, **doc})
                    logger.info("PersonaManager: activated new persona %s", name)
            except Exception as e:
                logger.warning("PersonaManager.activate DB error: %s", e)

        return {"status": "activated", "persona": name, "mode": mode}

    # ── Deactivate ────────────────────────────────────────────────────────────

    async def deactivate(
        self,
        name: str,
        reason: str = "",
        archive_memory: bool = True,
        can_reactivate: bool = True,
        deactivated_by: str = "director",
    ) -> dict:
        """Deactivate a persona. Sets status=inactive, preserves record."""
        name = name.lower().strip()
        now = datetime.now(timezone.utc).isoformat()

        if self.db is not None:
            try:
                await self.db.persona_activations.update_one(
                    {"persona": name},
                    {"$set": {
                        "status":          "inactive",
                        "deactivated_by":  deactivated_by,
                        "deactivated_at":  now,
                        "deactivation_reason": reason,
                        "can_reactivate":  can_reactivate,
                        "archive_memory":  archive_memory,
                        "updated_at":      now,
                    }},
                    upsert=True,
                )
                logger.info("PersonaManager: deactivated %s — %s", name, reason)
            except Exception as e:
                logger.warning("PersonaManager.deactivate DB error: %s", e)

        return {"status": "deactivated", "persona": name, "reason": reason}

    # ── Evolve ────────────────────────────────────────────────────────────────

    async def evolve(
        self,
        name: str,
        add_capabilities: list = None,
        remove_capabilities: list = None,
        update_mandate: str = None,
        update_audio_profile: dict = None,
        evolved_by: str = "director",
    ) -> dict:
        """
        Evolve a persona by adding/removing capabilities.
        Appends an entry to the persona's evolution_log.
        """
        name = name.lower().strip()
        now = datetime.now(timezone.utc).isoformat()

        evolution_entry = {
            "timestamp":          now,
            "evolved_by":         evolved_by,
            "added_capabilities": add_capabilities or [],
            "removed_capabilities": remove_capabilities or [],
            "mandate_updated":    update_mandate is not None,
        }

        update = {
            "$push": {"evolution_log": evolution_entry},
            "$set":  {"updated_at": now},
        }

        if add_capabilities:
            update["$addToSet"] = {"config.capabilities": {"$each": add_capabilities}}
        if remove_capabilities:
            update.setdefault("$pull", {})["config.capabilities"] = {"$in": remove_capabilities}
        if update_mandate:
            update["$set"]["config.mandate"] = update_mandate
        if update_audio_profile:
            update["$set"]["config.audio_profile"] = update_audio_profile

        if self.db is not None:
            try:
                await self.db.persona_activations.update_one(
                    {"persona": name}, update, upsert=True
                )
                logger.info("PersonaManager: evolved %s — added %s", name, add_capabilities)
            except Exception as e:
                logger.warning("PersonaManager.evolve DB error: %s", e)

        return {
            "status":   "evolved",
            "persona":  name,
            "added":    add_capabilities or [],
            "removed":  remove_capabilities or [],
        }

    # ── Clone ─────────────────────────────────────────────────────────────────

    async def clone(
        self,
        source: str,
        new_name: str,
        overrides: dict = None,
        cloned_by: str = "director",
    ) -> dict:
        """Clone a persona config under a new name."""
        source = source.lower().strip()
        new_name = new_name.lower().strip()
        now = datetime.now(timezone.utc).isoformat()

        source_doc = {}
        if self.db is not None:
            try:
                source_doc = await self.db.persona_activations.find_one(
                    {"persona": source}
                ) or {}
            except Exception: pass

        config = dict(source_doc.get("config", {}))
        if overrides:
            config.update(overrides)

        clone_doc = {
            "_id":          new_name,
            "persona":      new_name,
            "status":       "active",
            "mode":         "active",
            "scope":        source_doc.get("scope", ["internal_ops"]),
            "config":       config,
            "tier":         PERSONA_TIERS.get(new_name, 4),
            "reports_to":   REPORTING_LINES.get(new_name, "ambassador"),
            "cloned_from":  source,
            "cloned_by":    cloned_by,
            "activated_at": now,
            "updated_at":   now,
            "evolution_log": [],
        }

        if self.db is not None:
            try:
                await self.db.persona_activations.replace_one(
                    {"persona": new_name}, clone_doc, upsert=True
                )
                logger.info("PersonaManager: cloned %s → %s", source, new_name)
            except Exception as e:
                logger.warning("PersonaManager.clone DB error: %s", e)

        return {"status": "cloned", "source": source, "new_persona": new_name}

    # ── Merge ─────────────────────────────────────────────────────────────────

    async def merge(
        self,
        source_a: str,
        source_b: str,
        new_name: str,
        merged_by: str = "director",
    ) -> dict:
        """
        Merge two personas into a new one.
        Capabilities = union. Constraints = strictest (intersection).
        Memory policy = combined (both semantic+episodic if either has it).
        """
        source_a = source_a.lower().strip()
        source_b = source_b.lower().strip()
        new_name = new_name.lower().strip()

        doc_a, doc_b = {}, {}
        if self.db is not None:
            try:
                doc_a = await self.db.persona_activations.find_one({"persona": source_a}) or {}
                doc_b = await self.db.persona_activations.find_one({"persona": source_b}) or {}
            except Exception: pass

        cfg_a = doc_a.get("config", {})
        cfg_b = doc_b.get("config", {})

        # Union capabilities
        caps_a = set(cfg_a.get("capabilities", []))
        caps_b = set(cfg_b.get("capabilities", []))
        merged_caps = list(caps_a | caps_b)

        # Combined memory policy
        mem_a = cfg_a.get("memory_policy", {})
        mem_b = cfg_b.get("memory_policy", {})
        merged_memory = {
            "semantic":        mem_a.get("semantic", False) or mem_b.get("semantic", False),
            "episodic":        mem_a.get("episodic", False) or mem_b.get("episodic", False),
            "retention_rules": f"{mem_a.get('retention_rules', '')} | {mem_b.get('retention_rules', '')}".strip(" |"),
        }

        now = datetime.now(timezone.utc).isoformat()
        merged_doc = {
            "_id":      new_name,
            "persona":  new_name,
            "status":   "active",
            "mode":     "active",
            "scope":    list(set(doc_a.get("scope", []) + doc_b.get("scope", []))),
            "config": {
                "capabilities": merged_caps,
                "memory_policy": merged_memory,
            },
            "tier":           max(
                PERSONA_TIERS.get(source_a, 4),
                PERSONA_TIERS.get(source_b, 4),
            ),
            "reports_to":    REPORTING_LINES.get(new_name, "ambassador"),
            "merged_from":   [source_a, source_b],
            "merged_by":     merged_by,
            "activated_at":  now,
            "updated_at":    now,
            "evolution_log": [],
        }

        if self.db is not None:
            try:
                await self.db.persona_activations.replace_one(
                    {"persona": new_name}, merged_doc, upsert=True
                )
            except Exception as e:
                logger.warning("PersonaManager.merge DB error: %s", e)

        return {
            "status":    "merged",
            "new_persona": new_name,
            "sources":   [source_a, source_b],
            "capabilities_count": len(merged_caps),
        }

    # ── Status / Query ────────────────────────────────────────────────────────

    async def status(self, name: str) -> dict:
        """Get current activation status for a persona."""
        name = name.lower().strip()
        if self.db is not None:
            try:
                doc = await self.db.persona_activations.find_one(
                    {"persona": name}, {"_id": 0}
                )
                if doc:
                    return doc
            except Exception: pass
        return {"persona": name, "status": "not_found"}

    async def list_active(self) -> list:
        """Return all currently active personas."""
        personas = []
        if self.db is not None:
            try:
                cursor = self.db.persona_activations.find(
                    {"status": "active"},
                    {"_id": 0, "persona": 1, "mode": 1, "tier": 1, "reports_to": 1, "updated_at": 1},
                )
                async for doc in cursor:
                    personas.append(doc)
            except Exception: pass
        return personas

    async def bootstrap_core_personas(self, activated_by: str = "system") -> dict:
        """
        Ensure all 7 core personas exist in db.persona_activations.
        Safe to call on startup — uses upsert, won't overwrite existing configs.
        """
        from ai.persona_loader import _PERSONA_MAP

        results = []
        for name in _PERSONA_MAP.keys():
            existing = None
            if self.db is not None:
                try:
                    existing = await self.db.persona_activations.find_one({"persona": name})
                except Exception: pass

            if not existing:
                result = await self.activate(
                    name=name,
                    config={
                        "source": "persona_loader",
                        "capabilities": [],
                        "bootstrapped": True,
                    },
                    activated_by=activated_by,
                )
                results.append(result)

        logger.info("PersonaManager.bootstrap: %d personas bootstrapped", len(results))
        return {"bootstrapped": len(results), "personas": [r["persona"] for r in results]}
