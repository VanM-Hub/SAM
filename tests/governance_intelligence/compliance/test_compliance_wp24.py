"""WP-24 - Governance Intelligence Compliance tests (IP-3.1-002).

Automatic verification that the capability:
  - never mutates runtime / orchestrates / holds approval authority /
    execution authority (forbidden), and
  - exhibits deterministic reasoning, explainable output, and
    evidence-backed recommendation (required).

Runs the static compliance_check over the whole package and asserts each of
the seven properties.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from sam.governance_intelligence.compliance import compliance_check


@pytest.fixture(scope="module")
def report():
    return compliance_check(Path("src/sam/governance_intelligence"))


class TestForbiddenProperties:
    FORBIDDEN = ["no runtime mutation", "no orchestration", "no approval", "no execution", "no authority"]

    @pytest.mark.parametrize("name", FORBIDDEN)
    def test_forbidden(self, report, name):
        for c in report.checks:
            if c.name == name:
                assert c.passed is True, f"{name} violations: {c.violations}"
                return
        pytest.fail(f"no check named {name}")


class TestRequiredProperties:
    REQUIRED = ["deterministic reasoning", "explainable output", "evidence-backed recommendation"]

    @pytest.mark.parametrize("name", REQUIRED)
    def test_required(self, report, name):
        for c in report.checks:
            if c.name == name:
                assert c.passed is True, f"{name} violations: {c.violations}"
                return
        pytest.fail(f"no check named {name}")

    def test_all_required_present(self, report):
        names = {c.name for c in report.checks}
        assert set(self.REQUIRED) <= names


def test_report_overall_passes(report):
    assert report.passed() is True
