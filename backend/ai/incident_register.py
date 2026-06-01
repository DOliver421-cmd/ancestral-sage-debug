"""
incident_register.py - Director 4.0
======================================
Persistent session incident tracking for WAI-Institute / M.O.R.E. Help Center.

Director's Brief Rule:
  Any incident open longer than 72 hours is automatically flagged as STALE.

Incident schema:
  title     : str  — short incident name
  type      : str  — 'technical' | 'legal' | 'reputational' | 'safety' | 'financial' | ...
  severity  : str  — 'LOW' | 'ELEVATED' | 'HIGH' | 'CRITICAL'
  source    : str  — origin of the incident
  summary   : str  — human-readable description
  status    : str  — 'open' | 'monitoring' | 'resolved'
  timestamp : datetime — auto-set on add()

Usage:
  from ai.incident_register import incident_register
  incident_register.add({
      "title": "Railway healthcheck failing",
      "type": "technical",
      "severity": "HIGH",
      "source": "railway_dashboard",
      "summary": "Healthcheck /api/version returning timeout.",
  })
  stale = incident_register.stale_incidents()
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional


STALE_HOURS = 72  # Director's Brief — any open incident >72h is STALE


class IncidentRegister:
    def __init__(self):
        self.incidents: List[Dict] = []
        self._id_counter: int = 0

    def add(self, incident: Dict) -> Dict:
        """
        Add a new incident. Automatically stamps timestamp and assigns an id.
        Status defaults to 'open' if not provided.
        """
        self._id_counter += 1
        incident = dict(incident)
        incident.setdefault("status", "open")
        incident["id"] = self._id_counter
        incident["timestamp"] = datetime.now(timezone.utc)
        self.incidents.append(incident)
        return incident

    def list_open(self, include_monitoring: bool = True) -> List[Dict]:
        """Return all non-resolved incidents."""
        statuses = {"open"}
        if include_monitoring:
            statuses.add("monitoring")
        return [i for i in self.incidents if i.get("status") in statuses]

    def stale_incidents(self) -> List[Dict]:
        """Return open incidents that have been open longer than STALE_HOURS."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=STALE_HOURS)
        return [
            i for i in self.list_open()
            if i.get("timestamp") and i["timestamp"] < cutoff
        ]

    def resolve(self, incident_id: int) -> bool:
        """Mark an incident resolved by id. Returns True if found."""
        for i in self.incidents:
            if i.get("id") == incident_id:
                i["status"] = "resolved"
                i["resolved_at"] = datetime.now(timezone.utc)
                return True
        return False

    def update_status(self, incident_id: int, status: str) -> bool:
        """Update status of an incident. Returns True if found."""
        for i in self.incidents:
            if i.get("id") == incident_id:
                i["status"] = status
                return True
        return False

    def get_by_id(self, incident_id: int) -> Optional[Dict]:
        for i in self.incidents:
            if i.get("id") == incident_id:
                return i
        return None

    def summary(self) -> Dict:
        open_list = self.list_open()
        stale_list = self.stale_incidents()
        return {
            "total":   len(self.incidents),
            "open":    len(open_list),
            "stale":   len(stale_list),
            "stale_threshold_hours": STALE_HOURS,
        }


# Singleton
incident_register = IncidentRegister()
