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

        # Scan approval_coordinator source files for forbidden imports
        import os
        import inspect as _inspect
        pkg_dir = os.path.dirname(os.path.dirname(
            _inspect.getfile(coordinator_service)
        ))
        violations = []
        for root, _dirs, files in os.walk(pkg_dir):
            for f in files:
                if f.endswith('.py'):
                    path = os.path.join(root, f)
                    with open(path, 'r', encoding='utf-8') as fh:
                        content = fh.read()
                    for forbidden_mod in forbidden:
                        # Check for import patterns
                        if f'sam.runtime.{forbidden_mod}' in content:
                            violations.append(
                                f'{os.path.relpath(path, pkg_dir)}: '
                                f'imports {forbidden_mod}'
                            )
        if violations:
            pytest.fail(
                f'approval_coordinator has forbidden imports: '
                f'{violations}'
            )
