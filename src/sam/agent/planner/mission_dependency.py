"""Mission Dependency — dependensi mission (Sprint 159).

Agent Runtime — melacak dependensi antar langkah. Deterministik.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class MissionDependency:
    """Dependensi antar langkah mission (immutable)."""
    step_id: str
    depends_on: str
    plan_id: str = ""
