"""
system_health_monitor.py - Director 4.0
==========================================
Platform stability tracking and operational flag system.

The Director reads this at any moment to get a snapshot of system health.
Metrics are updated by the backend as events occur.
Flags are raised by any subsystem that detects a problem.

Usage:
  from ai.system_health_monitor import health_monitor
  health_monitor.flag("TTS circuit breaker opened — 5 failures in 60s")
  health_monitor.update_metric("errors_last_24h", 12)
  status = health_monitor.get_status()
"""

from typing import Dict, List, Any


class SystemHealthMonitor:
    def __init__(self):
        self.flags: List[str] = []
        self.metrics: Dict[str, Any] = {
            "uptime_pct":          100.0,   # platform uptime percentage
            "errors_last_24h":     0,       # server errors in last 24h
            "latency_ms":          0,       # most recent API latency
            "persona_drift_flags": 0,       # persona mandate violations detected
            "open_incidents":      0,       # incidents in incident_register
            "tts_circuit_open":    False,   # TTS circuit breaker state
            "db_connected":        True,    # MongoDB connection state
            "ai_api_reachable":    True,    # Anthropic API reachability
        }

    def flag(self, message: str) -> None:
        """Raise an operational flag for Director review."""
        self.flags.append(message)

    def clear_flags(self) -> None:
        """Clear all flags (call after Director has reviewed)."""
        self.flags = []

    def update_metric(self, key: str, value: Any) -> None:
        """
        Update a specific metric.
        Key must be one of the metric keys defined in __init__,
        or a new key (dynamically added metrics are permitted).
        """
        self.metrics[key] = value

    def get_status(self) -> Dict:
        """Return full status snapshot for the Director."""
        health = "nominal"
        if self.flags:
            health = "warning"
        if (
            self.metrics.get("errors_last_24h", 0) > 50
            or not self.metrics.get("db_connected", True)
            or not self.metrics.get("ai_api_reachable", True)
            or self.metrics.get("open_incidents", 0) > 3
        ):
            health = "critical"
        return {
            "health":  health,
            "metrics": dict(self.metrics),
            "flags":   list(self.flags),
        }

    def is_nominal(self) -> bool:
        return self.get_status()["health"] == "nominal"


# Singleton
health_monitor = SystemHealthMonitor()
