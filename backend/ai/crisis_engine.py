"""
crisis_engine.py - Director 4.0
=================================
Recovery / crisis coordination for WAI-Institute / M.O.R.E. Help Center.

CrisisLevel severity scale:
  NONE   — Normal operations
  YELLOW — Elevated (patterns, conflicts, content risks)
  ORANGE — High (security, legal, reputational threats)
  RED    — Critical (data breach, existential or active threat)

CrisisEngine automatically recalculates level after every incident is raised
and syncs with ModeSystem (RED/ORANGE → RECOVERY mode).

Usage:
  from ai.crisis_engine import crisis_engine, CrisisLevel
  crisis_engine.raise_incident({
      "type": "reputational",
      "severity": "HIGH",
      "source": "social_media",
      "summary": "Misleading article about WAI-Institute published."
  })
  print(crisis_engine.get_level())
"""

from enum import Enum
from typing import List, Dict


class CrisisLevel(str, Enum):
    NONE   = "none"
    YELLOW = "yellow"   # elevated
    ORANGE = "orange"   # high
    RED    = "red"      # critical


class CrisisEngine:
    def __init__(self):
        self.level: CrisisLevel = CrisisLevel.NONE
        self.incidents: List[Dict] = []

    def raise_incident(self, incident: Dict) -> None:
        """
        Record a new incident and recalculate crisis level.

        incident schema:
            type     : str  — 'technical' | 'legal' | 'reputational' | 'safety' | 'financial' | ...
            severity : str  — 'LOW' | 'ELEVATED' | 'HIGH' | 'CRITICAL'
            source   : str  — origin of the threat
            summary  : str  — brief human-readable description
        """
        self.incidents.append(incident)
        self._recalculate_level()
        self._sync_mode()

    def _recalculate_level(self) -> None:
        severities = {i.get("severity", "").upper() for i in self.incidents}
        if "CRITICAL" in severities:
            self.level = CrisisLevel.RED
        elif "HIGH" in severities:
            self.level = CrisisLevel.ORANGE
        elif "ELEVATED" in severities:
            self.level = CrisisLevel.YELLOW
        else:
            self.level = CrisisLevel.NONE

    def _sync_mode(self) -> None:
        """Automatically shift ModeSystem to RECOVERY when level warrants it."""
        try:
            from ai.mode_system import mode_system, Mode
            if self.level in {CrisisLevel.ORANGE, CrisisLevel.RED}:
                if mode_system.get_mode() != Mode.RECOVERY:
                    mode_system.set_mode(
                        Mode.RECOVERY,
                        reason=f"crisis_engine auto-sync: level={self.level}"
                    )
        except ImportError:
            pass  # mode_system not available in this context

    def resolve_incident(self, index: int) -> None:
        """Remove an incident by list index and recalculate level."""
        if 0 <= index < len(self.incidents):
            self.incidents.pop(index)
            self._recalculate_level()

    def clear_all(self) -> None:
        """Clear all incidents and reset to NONE."""
        self.incidents = []
        self.level = CrisisLevel.NONE

    def get_level(self) -> CrisisLevel:
        return self.level

    def is_recovery_mode_required(self) -> bool:
        return self.level in {CrisisLevel.ORANGE, CrisisLevel.RED}

    def summary(self) -> Dict:
        return {
            "level": self.level,
            "incident_count": len(self.incidents),
            "recovery_required": self.is_recovery_mode_required(),
            "incidents": list(self.incidents),
        }


# Singleton
crisis_engine = CrisisEngine()
