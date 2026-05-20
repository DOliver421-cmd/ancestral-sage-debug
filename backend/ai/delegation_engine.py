"""
delegation_engine.py - Director 4.0
======================================
Structured task assignment from The Director to individual personas.

When The Director assigns work, every task requires:
  - persona    : which persona receives the task
  - assignment : what they must do
  - deliverable: the expected output format and content
  - timeframe  : deadline or relative timing
  - owner      : accountability holder (usually 'director' or 'NAM_Oshun')

Usage:
  from ai.delegation_engine import delegation_engine
  task = delegation_engine.assign(
      persona="savant_scholar",
      assignment="Design a 4-week study plan for Market Literacy 101",
      deliverable="Structured week-by-week plan with objectives and assessments",
      timeframe="48 hours",
      owner="director",
  )
  print(delegation_engine.list_tasks())
"""

from typing import Dict, List, Optional


class DelegationEngine:
    def __init__(self):
        self.active_tasks: List[Dict] = []
        self._task_counter: int = 0

    def assign(
        self,
        persona: str,
        assignment: str,
        deliverable: str,
        timeframe: str,
        owner: str = "director",
        priority: str = "normal",
        notes: str = "",
    ) -> Dict:
        """
        Assign a structured task to a persona.
        Returns the task dict with a unique task_id.
        """
        self._task_counter += 1
        task = {
            "task_id": self._task_counter,
            "persona": persona,
            "assignment": assignment,
            "deliverable": deliverable,
            "timeframe": timeframe,
            "owner": owner,
            "priority": priority,
            "notes": notes,
            "status": "active",
        }
        self.active_tasks.append(task)
        return task

    def list_tasks(self, persona: Optional[str] = None) -> List[Dict]:
        """Return all active tasks, optionally filtered by persona."""
        if persona:
            return [t for t in self.active_tasks if t["persona"] == persona]
        return list(self.active_tasks)

    def complete_task(self, task_id: int) -> bool:
        """Mark a task as completed (removes from active list)."""
        for i, t in enumerate(self.active_tasks):
            if t["task_id"] == task_id:
                self.active_tasks.pop(i)
                return True
        return False

    def clear_persona(self, persona: str) -> int:
        """Remove all tasks for a specific persona. Returns count removed."""
        before = len(self.active_tasks)
        self.active_tasks = [t for t in self.active_tasks if t["persona"] != persona]
        return before - len(self.active_tasks)

    def clear_all(self) -> None:
        """Clear the entire task queue."""
        self.active_tasks = []

    def summary(self) -> Dict:
        personas = {}
        for t in self.active_tasks:
            personas[t["persona"]] = personas.get(t["persona"], 0) + 1
        return {
            "total_active": len(self.active_tasks),
            "by_persona": personas,
        }


# Singleton
delegation_engine = DelegationEngine()
