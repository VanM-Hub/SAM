"""Tests: Construction — instantiation and cross-unit independence."""

import pytest
from src.sam.runtime.execution_scheduler.services.scheduler_service import (
    SchedulerService,
)
from src.sam.runtime.execution_scheduler.lifecycle.scheduler_lifecycle import (
    SchedulerLifecycleState,
)


class TestConstruction:
    def test_instantiate_without_external_deps(self):
        svc = SchedulerService()
        assert svc is not None

    def test_initial_state_is_uninitialized(self):
        svc = SchedulerService()
        assert svc.lifecycle_state == SchedulerLifecycleState.UNINITIALIZED

    def test_initial_health_is_unavailable(self):
        svc = SchedulerService()
        health = svc.get_health()
        assert health["status"] == "unavailable"

    def test_initial_registry_empty(self):
        svc = SchedulerService()
        assert svc.record_count == 0

    def test_instantiate_and_initialize(self):
        svc = SchedulerService()
        svc.initialize()
        assert svc.lifecycle_state == SchedulerLifecycleState.RUNNING
        assert svc.get_health()["status"] == "available"

    def test_instantiate_multiple_independent(self):
        svc1 = SchedulerService()
        svc2 = SchedulerService()
        assert svc1 is not svc2
        svc1.initialize()
        assert svc2.lifecycle_state == SchedulerLifecycleState.UNINITIALIZED

    def test_no_import_from_other_units(self):
        """Execution Scheduler must not import from other runtime units."""
        import inspect
        import src.sam.runtime.execution_scheduler as es

        forbidden = [
            "citizen_host", "capability_manager",
            "discovery_resolver", "contract_enforcer",
            "approval_coordinator", "audit_recorder",
            "registry", "internal",
        ]

        # Check the actual source files, not runtime imports
        import os
        src_dir = os.path.dirname(es.__file__)
        violations = []
        for root, dirs, files in os.walk(src_dir):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", encoding="utf-8") as fh:
                        content = fh.read()
                    for forbidden_mod in forbidden:
                        # Check for "from sam.runtime.<forbidden>" imports
                        pattern = f"sam.runtime.{forbidden_mod}"
                        if pattern in content:
                            violations.append(f"{f}: imports {forbidden_mod}")
        assert len(violations) == 0, f"Forbidden imports found: {violations}"
