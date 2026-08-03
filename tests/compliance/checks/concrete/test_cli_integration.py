"""Integration tests for BaselineBackedSessionRunner (P1-008 CLI wiring).

Validates the additive subclass wires all 99 concrete checkers into the
engine run path: every catalog check id resolves to a real checker and
runs to a conforming result on the reference runtime (no placeholders,
no crashes, no deviating findings). P1-006 is never modified.
"""

import pytest

from sam.compliance.checks.concrete.baseline_backed_runner import (
    BaselineBackedSessionRunner,
)
from sam.compliance.cli.session_runner import SessionFilter


@pytest.fixture(scope="module")
def runner():
    return BaselineBackedSessionRunner()


def test_builder_has_99_concrete_checkers(runner):
    assert len(runner._concrete) == 99


def test_every_catalog_check_maps_to_concrete_execution_fn(runner):
    """Every enabled manifest/catalog id must get a real execution_fn."""
    manifest_ids = set(runner._manifest.check_ids())
    concrete_ids = set(runner._concrete.keys())
    # All catalog check ids are backed by a concrete checker.
    assert manifest_ids == concrete_ids
    assert len(manifest_ids) == 99


def test_full_engine_run_all_99_checkers_conform(runner):
    """run() with no filter executes all 99 and produces no deviations."""
    result = runner.run(
        target_runtime="runtime",
        baseline_commit="HEAD",
        suite_version="P1-001",
    )
    assert result.executed_checks == 99
    assert result.skipped_checks == 0
    assert result.total_checks == 99

    evidence = getattr(result.report, "evidence", [])
    assert len(evidence) == 99
    assert len([e for e in evidence if e.value is not None]) == 99

    # No deviating / failed findings.
    findings = getattr(result.report, "findings", [])
    deviating = [
        f for f in findings
        if getattr(f, "status", None) == "deviating"
    ]
    assert deviating == []
    assert result.verdict == "A"


def test_single_check_id_run(runner):
    """A single check filter still executes the real checker."""
    result = runner.run(
        target_runtime="runtime",
        baseline_commit="HEAD",
        suite_version="P1-001",
        check_filter=SessionFilter(check_id="L0-01"),
    )
    assert result.executed_checks == 1
    assert result.verdict == "A"


def test_filter_by_level_runs_subset(runner):
    """Level filter selects only that level's checks."""
    result = runner.run(
        target_runtime="runtime",
        baseline_commit="HEAD",
        suite_version="P1-001",
        check_filter=SessionFilter(level="L4"),
    )
    # L4 has 8 checks.
    assert result.executed_checks == 8


def test_base_session_runner_untouched():
    """P1-006 base method still creates placeholders (no monkeypatch)."""
    from sam.compliance.cli.session_runner import SessionRunner
    from sam.compliance.catalog.catalog import ComplianceCheckCatalog

    base = SessionRunner.__dict__["_to_compliance_check"]
    assert callable(base)
    catalog = ComplianceCheckCatalog()
    metadata = catalog.get("L0-01")
    assert metadata is not None
    placeholder = base(object.__new__(SessionRunner), metadata)
    # The base class produces a placeholder with no execution_fn.
    assert placeholder.is_executable() is False
