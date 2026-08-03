"""Shared fixtures for concrete checker tests (P1-008)."""

import pytest

from sam.compliance.catalog import ComplianceCheckCatalog
from sam.compliance.baseline import BaselineLoader
from sam.compliance.checks.base.check_context import CheckContext
from sam.compliance.checks.concrete.builder import Builder


@pytest.fixture
def catalog():
    return ComplianceCheckCatalog()


@pytest.fixture
def baseline():
    return BaselineLoader().load()


@pytest.fixture
def builder(catalog):
    return Builder(catalog)


@pytest.fixture
def context(baseline):
    """A CheckContext carrying the project baseline snapshot."""
    return CheckContext(
        target_path=r"D:\Project AI\SAM",
        options={"baseline": baseline, "baseline_root": r"D:\Project AI\SAM"},
    )


@pytest.fixture
def all_checks(builder):
    """All concrete checkers built by the current Builder."""
    return builder.build_all()
