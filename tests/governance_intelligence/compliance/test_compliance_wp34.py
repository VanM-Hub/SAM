"""WP-34 - Conversation Compliance tests (IP-3.1-003).

Automatic verification over the whole Intelligence package (including the
new conversation/planner/navigation/relationship/session/interactive modules)
that the capability:
  - no authority
  - no governance mutation
  - no runtime mutation
  - no hidden memory (session-only context)
  - no evidence loss (answers keep the evidence chain)
  - deterministic follow-up
"""

from __future__ import annotations

from pathlib import Path

import pytest

from sam.governance_intelligence.compliance import compliance_check


@pytest.fixture(scope="module")
def report():
    return compliance_check(Path("src/sam/governance_intelligence"))


class TestConversationForbidden:
    FORBIDDEN = [
        "no authority",
        "no governance mutation",
        "no runtime mutation",
        "no hidden memory",
    ]

    @pytest.mark.parametrize("name", FORBIDDEN)
    def test_forbidden(self, report, name):
        for c in report.checks:
            if c.name == name:
                assert c.passed is True, f"{name} violations: {c.violations}"
                return
        pytest.fail(f"no check named {name}")


class TestConversationRequired:
    REQUIRED = [
        "no evidence loss",
        "deterministic follow-up",
    ]

    @pytest.mark.parametrize("name", REQUIRED)
    def test_required(self, report, name):
        for c in report.checks:
            if c.name == name:
                assert c.passed is True, f"{name} violations: {c.violations}"
                return
        pytest.fail(f"no check named {name}")


def test_report_overall_passes(report):
    assert report.passed() is True
    # WP-13 (5) + WP-24 (3) + WP-34 (2 forbidden + 2 required) = 12 checks
    assert len(report.checks) == 12
