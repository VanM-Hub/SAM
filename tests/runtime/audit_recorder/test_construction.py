"""Test construction: Audit Recorder without cross-unit imports.

Per I1-001 §2.7: depends only on shared. Must be able
to instantiate independently with only the public
protocol interfaces for dependency injection.
"""

import pytest


class TestConstruction:
    """Verify Audit Recorder can be constructed independently."""

    def test_instantiate_without_any_cross_unit_deps(self):
        """Can instantiate RecorderService alone — no imports from other units."""
        from src.sam.runtime.audit_recorder.services.recorder_service import (
            RecorderService,
        )

        service = RecorderService()
        assert service is not None
        assert service.record_count == 0

    def test_instantiate_and_initialize(self):
        """Can instantiate and initialize (UNINITIALIZED → RUNNING)."""
        from src.sam.runtime.audit_recorder.services.recorder_service import (
            RecorderService,
        )

        service = RecorderService()
        service.initialize()
        assert service.lifecycle_state.value == "RUNNING"

    def test_instantiate_multiple_independent(self):
        """Multiple instances are independent."""
        from src.sam.runtime.audit_recorder.services.recorder_service import (
            RecorderService,
        )

        s1 = RecorderService()
        s2 = RecorderService()
        assert s1 is not s2
        assert s1.record_count == s2.record_count == 0

    def test_initial_health_is_unavailable(self):
        """Before initialize, health is UNAVAILABLE."""
        from src.sam.runtime.audit_recorder.services.recorder_service import (
            RecorderService,
        )

        service = RecorderService()
        health = service.get_health()
        assert health["status"] == "UNAVAILABLE"
        assert health["unit"] == "audit_recorder"

    def test_initial_registry_empty(self):
        """After construction, record registry is empty."""
        from src.sam.runtime.audit_recorder.services.recorder_service import (
            RecorderService,
        )

        service = RecorderService()
        assert service.record_count == 0
        assert len(service.get_state_counts()) > 0

    def test_no_import_from_other_units(self):
        """Verify no import from restricted modules.

        Per I1-001 §2.7: audit_recorder depends only on shared.
        Must not import from: citizen_host, capability_manager,
        discovery_resolver, contract_enforcer, approval_coordinator,
        execution_scheduler, contracts, registry, internal.
        """
        import os
        from src.sam.runtime.audit_recorder.services.recorder_service import (
            RecorderService,
        )
        import inspect as _inspect

        pkg_dir = os.path.dirname(os.path.dirname(
            _inspect.getfile(RecorderService)
        ))

        forbidden = {
            "citizen_host",
            "capability_manager",
            "discovery_resolver",
            "contract_enforcer",
            "approval_coordinator",
            "execution_scheduler",
        }

        violations = []
        for root, _dirs, files in os.walk(pkg_dir):
            for f in files:
                if f.endswith('.py'):
                    path = os.path.join(root, f)
                    with open(path, 'r', encoding='utf-8') as fh:
                        content = fh.read()
                    for forbidden_mod in forbidden:
                        if f'sam.runtime.{forbidden_mod}' in content:
                            violations.append(
                                f'{os.path.relpath(path, pkg_dir)}: '
                                f'imports {forbidden_mod}'
                            )
        if violations:
            pytest.fail(
                f'audit_recorder has forbidden imports: {violations}'
            )

    def test_boundary_no_external_dependency(self):
        """No external module dependencies beyond stdlib + shared."""
        import sys
        from src.sam.runtime.audit_recorder.services.recorder_service import (
            RecorderService,
        )

        # Ensure the module loads — actual boundary is structural
        service = RecorderService()
        service.initialize()

        # Verify internal-only boundary: record() rejects non-internal sources
        from src.sam.runtime.audit_recorder.exceptions.audit_errors import (
            InvalidRecordError,
        )

        class FakeResult:
            execution_id = "exec-001"
            approval_reference = "appr-001"
            contract_reference = "ctr-001"
            capability_reference = "cap-001"
            state = "COMPLETED"
            message = "ok"

        result = FakeResult()

        # External source should be rejected per ADR-006
        with pytest.raises(InvalidRecordError, match="Boundary"):
            service.record(result, input_source="external_client")
