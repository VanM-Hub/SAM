"""CheckRegistration — registers framework checks into the P1-002 engine.

Provides auto-registration: a BaseComplianceCheck can register itself
into a ComplianceRegistry with one method call.
"""

from __future__ import annotations

from typing import List, Optional

from ...registry.check_registry import ComplianceRegistry
from ..base.base_check import BaseComplianceCheck
from ..base.check_context import CheckContext


class CheckRegistration:
    """Registers BaseComplianceCheck instances into a ComplianceRegistry.

    Transforms BaseComplianceCheck objects into ComplianceCheck models
    (via to_compliance_check()) and registers them.

    Deterministic: registration order is preserved.
    """

    def __init__(self, registry: ComplianceRegistry) -> None:
        if not isinstance(registry, ComplianceRegistry):
            raise TypeError("registry must be a ComplianceRegistry instance")
        self._registry = registry

    def register(
        self,
        check: BaseComplianceCheck,
        context: Optional[CheckContext] = None,
    ) -> None:
        """Register a single check.

        Args:
            check: The BaseComplianceCheck to register.
            context: Optional execution context. If None, an empty context
                     is used; execution_fn will receive this context.

        Raises:
            DuplicateCheckError: If check_id already exists in registry.
        """
        if context is None:
            context = CheckContext(target_path=".")

        compliance_check = check.to_compliance_check(context)
        self._registry.register(compliance_check)

    def register_all(
        self,
        checks: List[BaseComplianceCheck],
        context: Optional[CheckContext] = None,
    ) -> int:
        """Register multiple checks.

        Args:
            checks: List of BaseComplianceCheck instances.
            context: Optional shared execution context.

        Returns:
            Number of checks registered.

        Raises:
            DuplicateCheckError: If any check_id is already registered
                                 (with the already-existing check).
        """
        if context is None:
            context = CheckContext(target_path=".")

        compliance_checks = [c.to_compliance_check(context) for c in checks]
        self._registry.register_all(compliance_checks)
        return len(checks)
