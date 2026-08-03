"""Integration + executable smoke tests (E1-001 + E1-002).

Covers the full lifecycle through the public API and the E1-002 executable
contract (create_runtime / run_runtime / shutdown_runtime), plus the CLI smoke
sequence. Verifies no regression in the seven-unit composition.

Authority: E1-001 COMPOSITION ROOT | E1-002 REFERENCE RUNTIME EXECUTABLE.
"""

import subprocess
import sys

import pytest

from sam.runtime_root import (
    PIPELINE,
    RuntimeBuilder,
    RuntimeRoot,
    create_runtime,
    run_runtime,
    shutdown_runtime,
)
from sam.runtime_root.exceptions import RuntimeCompositionError
from sam.runtime_root.lifecycle import RuntimeState


# ---------------------------------------------------------------------------
# full lifecycle through the public API (E1-001)
# ---------------------------------------------------------------------------


def test_full_lifecycle_build_start_health_stop_dispose():
    root = RuntimeBuilder().build()
    assert root.lifecycle.state == RuntimeState.BUILT
    root.start()
    assert root.lifecycle.state == RuntimeState.STARTED
    assert root.is_running()
    assert root.health() is not None
    root.stop()
    assert root.lifecycle.state == RuntimeState.STOPPED
    root.dispose()
    assert root.lifecycle.state == RuntimeState.DISPOSED


def test_units_are_wired_in_canonical_pipeline_order():
    root = RuntimeBuilder().build()
    units = root.container().units()
    assert list(units.keys()) == list(PIPELINE)
    # lazy-factory wiring means each unit is a distinct service instance
    assert len({id(v) for v in units.values()}) == 7


def test_container_per_unit_accessors_match_pipeline():
    root = RuntimeBuilder().build()
    c = root.container()
    assert c.citizen_host is c.units()["citizen_host"]
    assert c.audit_recorder is c.units()["audit_recorder"]
    assert c.approval_coordinator is c.units()["approval_coordinator"]


def test_immutable_container_rejects_mutation():
    root = RuntimeBuilder().build()
    container = root.container()
    with pytest.raises((AttributeError, RuntimeCompositionError)):
        container.citizen_host = object()


# ---------------------------------------------------------------------------
# E1-002 executable
# ---------------------------------------------------------------------------


def test_create_runtime_builds_root():
    root = create_runtime()
    assert isinstance(root, RuntimeRoot)
    assert root.lifecycle.state == RuntimeState.BUILT


def test_run_runtime_builds_and_starts():
    root = run_runtime()
    assert isinstance(root, RuntimeRoot)
    assert root.is_running()
    assert root.health() is not None


def test_shutdown_runtime_stops_and_disposes():
    root = create_runtime()
    root.start()
    shutdown_runtime(root)
    assert root.lifecycle.state == RuntimeState.DISPOSED


def test_shutdown_runtime_from_built():
    root = create_runtime()
    shutdown_runtime(root)  # BUILT -> STOPPED -> DISPOSED
    assert root.lifecycle.state == RuntimeState.DISPOSED


def test_restart_via_executable_handlers():
    first = run_runtime()
    shutdown_runtime(first)
    assert first.lifecycle.state == RuntimeState.DISPOSED
    second = run_runtime()
    assert second.is_running()
    shutdown_runtime(second)


def test_shutdown_runtime_after_dispose_raises():
    root = create_runtime()
    shutdown_runtime(root)
    with pytest.raises(RuntimeCompositionError):
        shutdown_runtime(root)


# ---------------------------------------------------------------------------
# CLI smoke (python -m sam.runtime_root)
# ---------------------------------------------------------------------------


def test_cli_smoke_sequence():
    """python -m sam.runtime_root must build, start, health, stop, dispose."""
    result = subprocess.run(
        [sys.executable, "-m", "sam.runtime_root"],
        capture_output=True,
        text=True,
        cwd=None,
    )
    out = (result.stdout or "") + (result.stderr or "")
    assert result.returncode == 0, out
    assert "built" in out
    assert "started" in out
    assert "health=" in out
    assert "stopped" in out
    assert "disposed" in out


def test_cli_reports_seven_units_and_pipeline():
    result = subprocess.run(
        [sys.executable, "-m", "sam.runtime_root"],
        capture_output=True,
        text=True,
    )
    out = (result.stdout or "") + (result.stderr or "")
    assert "units=7" in out
    assert "pipeline=7" in out
