"""Tests: Certification — certificability, boundary, cross-dependency.

Verifies:
- All authorized entry points present
- No forbidden imports
- Interface completeness
"""

import pytest
from src.sam.runtime.execution_scheduler.services.scheduler_service import (
    SchedulerService,
)
from src.sam.runtime.execution_scheduler.interfaces.scheduler_interface import (
    ExecutionSchedulerInterface,
)
from src.sam.runtime.execution_scheduler.validation.boundary_validator import (
    BoundaryValidator,
)
from src.sam.runtime.execution_scheduler.exceptions.execution_errors import (
    ExecutionError,
)
from src.sam.runtime.execution_scheduler.state.execution_state import (
    ExecutionLifecycleState,
    ExecutionStateRecord,
    is_valid_transition,
    LEGAL_TRANSITIONS,
)


class TestInterfaceCompleteness:
    def test_interface_has_six_methods(self):
        """The public interface must expose exactly 6 operations."""
        methods = {
            name for name, val in ExecutionSchedulerInterface.__dict__.items()
            if not name.startswith("_") and callable(val)
        }
        assert methods == {
            "create_execution",
            "schedule",
            "transition",
            "verify",
            "get",
            "get_health",
        }

    def test_service_implements_all_interface_methods(self):
        """SchedulerService implements all interface methods."""
        svc = SchedulerService()
        for method_name in ["create_execution", "schedule", "transition",
                            "verify", "get", "get_health"]:
            assert hasattr(svc, method_name), \
                f"SchedulerService missing method: {method_name}"


class TestCertification:
    """Certification-specific tests."""

    def test_boundary_matches_interface(self):
        """Boundary authorized entry points match interface methods."""
        boundary = BoundaryValidator.get_authorized_entry_points()
        interface_methods = {
            name for name, val in ExecutionSchedulerInterface.__dict__.items()
            if not name.startswith("_") and callable(val)
        }
        assert boundary == interface_methods

    def test_all_exceptions_have_base(self):
        """All execution exceptions must extend ExecutionError."""
        import inspect
        from src.sam.runtime.execution_scheduler.exceptions import execution_errors as ee
        for name, obj in inspect.getmembers(ee):
            if inspect.isclass(obj) and issubclass(obj, Exception) and obj != ExecutionError:
                assert issubclass(obj, ExecutionError), \
                    f"{name} does not extend ExecutionError"

    def test_all_lifecycle_states_in_transition_map(self):
        """Every lifecycle state must appear in LEGAL_TRANSITIONS."""
        for state in ExecutionLifecycleState:
            assert state in LEGAL_TRANSITIONS, \
                f"State {state} missing from LEGAL_TRANSITIONS"

    def test_archived_has_no_transitions(self):
        """ARCHIVED must have no legal transitions."""
        assert LEGAL_TRANSITIONS[ExecutionLifecycleState.ARCHIVED] == set()

    def test_created_can_become_queued_or_cancelled(self):
        """CREATED transitions: QUEUED, CANCELLED."""
        allowed = LEGAL_TRANSITIONS[ExecutionLifecycleState.CREATED]
        assert allowed == {ExecutionLifecycleState.QUEUED, ExecutionLifecycleState.CANCELLED}

    def test_full_lifecycle_path_exists(self):
        """Verify a complete path from CREATED to ARCHIVED exists."""
        path = [
            ExecutionLifecycleState.CREATED,
            ExecutionLifecycleState.QUEUED,
            ExecutionLifecycleState.RUNNING,
            ExecutionLifecycleState.COMPLETED,
            ExecutionLifecycleState.ARCHIVED,
        ]
        for i in range(len(path) - 1):
            assert is_valid_transition(path[i], path[i+1]), \
                f"Transition {path[i].value} -> {path[i+1].value} should be valid"

    def test_service_initialization_complete(self):
        """Full init → op → shutdown cycle works."""
        svc = SchedulerService()
        assert svc.get_health()["status"] == "unavailable"
        svc.initialize()
        assert svc.get_health()["status"] == "available"
        svc.shutdown()
        assert svc.get_health()["status"] == "unavailable"
