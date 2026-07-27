"""
Desired Operational State Contracts — Phase 0
"""

from pydantic import BaseModel


class DesiredOperationalState(BaseModel):
    runtime_state: str = "RUNNING"
    plugins_expected: int = 0
    knowledge_loaded: bool = True
    memory_healthy: bool = True
    session_persistent: bool = True
    min_health_score: float = 95.0
    guardian_mode: str = "autonomous"
