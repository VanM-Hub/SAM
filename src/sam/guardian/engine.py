"""
Guardian Engine — API kompatibilitas untuk import legacy.

Guardian telah dipisah menjadi beberapa modul:
  - action.py → ActionEngine
  - analyzer.py → AnalyzerEngine  
  - pipeline.py → GuardianPipeline

Engine singleton dipertahankan untuk kompatibilitas.
"""

from .pipeline import GuardianPipeline
from .action import ActionEngine
from .analyzer import AnalyzerEngine
from .decision import DecisionEngine

__all__ = ["GuardianEngine"]

# Resolve backward-compat alias
GuardianEngine = None  # defined below


class GuardianEngine:
    """Wrapper backward-compat untuk GuardianPipeline.

    Membuat RuntimeCoordinator minimal jika tidak diberikan.
    """

    def __init__(self, *args, **kwargs):
        from ..runtime.coordinator import RuntimeCoordinator
        if not args and 'coordinator' not in kwargs:
            kwargs['coordinator'] = RuntimeCoordinator()
        self._pipeline = GuardianPipeline(*args, **kwargs)
        self._state = "initialized"

    @property
    def state(self) -> str:
        return self._state

    async def process(self, *args, **kwargs):
        return await self._pipeline.process(*args, **kwargs)
