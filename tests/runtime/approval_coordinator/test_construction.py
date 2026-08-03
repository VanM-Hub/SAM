"""Tests: Construction independence — no cross-unit dependencies."""

import pytest

from src.sam.runtime.approval_coordinator.services.coordinator_service import (
    ApprovalCoordinator,
)


class TestConstruction:
    """Tests for independent construction."""

    def test_instantiate_without_any_cross_unit_deps(self):
        """Approval Coordinator must instantiate without importing
        other unit modules."""
        c = ApprovalCoordinator()
        assert c is not None

    def test_instantiate_and_initialize(self):
        c = ApprovalCoordinator()
        c.initialize()
        assert c.lifecycle.state.value == "RUNNING"

    def test_instantiate_multiple_independent(self):
        c1 = ApprovalCoordinator()
        c2 = ApprovalCoordinator()
        assert c1 is not c2

    def test_initial_health_is_unavailable(self):
        c = ApprovalCoordinator()
        health = c.get_health()
        assert health["status"] == "UNAVAILABLE"

    def test_initial_registry_empty(self):
        c = ApprovalCoordinator()
        c.initialize()
        assert c.approval_count == 0

    def test_no_import_from_other_units(self):
        """Verify no import from restricted modules."""
        import sys

        # Import the coordinator module
        from src.sam.runtime.approval_coordinator.services import (
            coordinator_service,
        )

        # List all imported names in the module
        module_globals = set(
            key.split(".")[0]
            for key in coordinator_service.__dict__
        )

        forbidden = {
            "citizen_host",
            "capability_manager",
            "discovery_resolver",
            "contract_enforcer",
            "execution_scheduler",
            "audit_recorder",
        }

        # Check sys.modules for forbidden imports
        for mod_name in list(sys.modules.keys()):
            for forbidden_mod in forbidden:
                if f"src.sam.runtime.{forbidden_mod}" in mod_name:
                    pytest.fail(
                        f"approval_coordinator imports forbidden module: "
                        f"{forbidden_mod}"
                    )
