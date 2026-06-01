"""
mode_system.py - Director 4.0
==============================
Director-controlled global mode for the entire AI ecosystem.

Modes:
  NAM        — Full creative + growth alignment (NAM Oshun declaration)
  BALANCED   — Default steady state
  CREATIVE   — Innovation-first
  AGGRESSIVE — Growth-first
  CONSERVATIVE — Protection-first
  RECOVERY   — Crisis stabilization (auto-set by CrisisEngine when ORANGE/RED)

Usage:
  from ai.mode_system import mode_system, Mode
  mode_system.set_mode(Mode.RECOVERY)
  current = mode_system.get_mode()
"""

from enum import Enum


class Mode(str, Enum):
    NAM          = "nam"
    BALANCED     = "balanced"
    CREATIVE     = "creative"
    AGGRESSIVE   = "aggressive"
    CONSERVATIVE = "conservative"
    RECOVERY     = "recovery"


class ModeSystem:
    def __init__(self):
        self.current_mode: Mode = Mode.BALANCED
        self._history: list = []

    def set_mode(self, mode: Mode, reason: str = "") -> None:
        """Switch the ecosystem mode. Appends previous state to history."""
        self._history.append({
            "from": self.current_mode,
            "to": mode,
            "reason": reason,
        })
        self.current_mode = mode

    def get_mode(self) -> Mode:
        return self.current_mode

    def get_history(self) -> list:
        return list(self._history)

    def reset(self) -> None:
        """Return to BALANCED mode."""
        self.set_mode(Mode.BALANCED, reason="manual reset")


# Singleton — import and use directly.
mode_system = ModeSystem()
