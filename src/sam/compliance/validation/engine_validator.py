"""Engine validator — validates compliance engine integrity."""

from __future__ import annotations

from typing import List, Tuple

from ..models.session_state import SessionState
from ..engine.compliance_engine import ComplianceEngine
from ..registry.check_registry import ComplianceRegistry


class EngineValidator:
    """Validates compliance engine integrity and behavior."""

    @staticmethod
    def validate_engine_structure(engine: ComplianceEngine) -> List[str]:
        """Validate engine structural integrity. Returns list of issues (empty = valid)."""
        issues = []

        if not isinstance(engine, ComplianceEngine):
            issues.append("Not a ComplianceEngine instance")
            return issues

        if not isinstance(engine.registry, ComplianceRegistry):
            issues.append("Registry is not a ComplianceRegistry instance")

        return issues

    @staticmethod
    def validate_state_transitions(
        engine: ComplianceEngine,
    ) -> Tuple[bool, str]:
        """Validate that engine state transitions follow the lifecycle.

        Returns (is_valid, message).
        """
        # After reset, engine should be INITIATED
        engine.reset()
        if engine.state != SessionState.INITIATED:
            return False, "After reset, expected INITIATED, got %s" % engine.state.value

        return True, "State transitions valid"
