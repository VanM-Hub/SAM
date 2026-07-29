"""
OP-318 — Guardian Runtime State

State management untuk Guardian runtime.
DTO immutable.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime


class GuardianStateHolder:
    """
    Menyimpan state runtime guardian.
    """

    def __init__(self):
        from .state import GuardianState, GuardianHealth, GuardianStatistics

        self.state = GuardianState(
            status="active",
            pipeline_running=False,
            gate_active=True,
            policy_enabled=True,
            audit_active=True,
            started_at=datetime.now().isoformat(timespec="seconds"),
        )
        self.health = GuardianHealth(
            overall="green",
            last_health_check=datetime.now().isoformat(timespec="seconds"),
        )
        self.statistics = GuardianStatistics()

    def update_state(self, **kwargs: Any) -> None:
        current = self.state.to_dict()
        current.update(kwargs)
        from .state import GuardianState
        self.state = GuardianState(**{k: v for k, v in current.items()
                                       if hasattr(GuardianState, k)})

    def update_health(self, **kwargs: Any) -> None:
        current = self.health.to_dict()
        current.update(kwargs)
        from .state import GuardianHealth
        self.health = GuardianHealth(**{k: v for k, v in current.items()
                                         if hasattr(GuardianHealth, k)})

    def increment_stat(self, attr: str, delta: int = 1) -> None:
        current = self.statistics.to_dict()
        current[attr] = current.get(attr, 0) + delta
        from .state import GuardianStatistics
        valid_keys = {f.name for f in __import__("dataclasses").fields(GuardianStatistics)}
        self.statistics = GuardianStatistics(**{k: v for k, v in current.items() if k in valid_keys})

    def snapshot(self) -> Any:
        from .state import GuardianSnapshot
        return GuardianSnapshot(
            state=self.state,
            health=self.health,
            statistics=self.statistics,
            timestamp=datetime.now().isoformat(timespec="seconds"),
        )
