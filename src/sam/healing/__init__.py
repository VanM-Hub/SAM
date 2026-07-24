"""SAM Healing — Sprint 28 Fase 2.

Self-healing loop, reflection, and auto-recovery orchestration.
"""

from .reflection import ReflectionRecord, ReflectionManager
from .loop import SelfHealingLoop

__all__ = [
    "ReflectionRecord",
    "ReflectionManager",
    "SelfHealingLoop",
]
