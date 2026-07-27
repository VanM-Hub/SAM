"""
DOS Models — Phase 0

Mirrors contracts.dos for internal YAML parsing.
"""

from pydantic import BaseModel
from sam.contracts import DesiredOperationalState


class DOSModel(BaseModel):
    """Wrapper model used by DOSLoader for YAML parsing."""
    runtime_state: str = "RUNNING"
    plugins_expected: int = 0
    knowledge_loaded: bool = True
    memory_healthy: bool = True
    session_persistent: bool = True
    min_health_score: float = 95.0
    guardian_mode: str = "autonomous"

    def to_contract(self) -> DesiredOperationalState:
        """Convert to public contract."""
        return DesiredOperationalState(
            runtime_state=self.runtime_state,
            plugins_expected=self.plugins_expected,
            knowledge_loaded=self.knowledge_loaded,
            memory_healthy=self.memory_healthy,
            session_persistent=self.session_persistent,
            min_health_score=self.min_health_score,
            guardian_mode=self.guardian_mode,
        )
