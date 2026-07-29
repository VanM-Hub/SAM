"""
OP-352 — 50 Operational Scenarios — Test Runner
"""

import pytest
from tests.e2e.operational_scenarios import all_scenarios, verify


def id_fn(s):
    return s[0]  # scenario name


@pytest.mark.parametrize("scenario", all_scenarios(), ids=id_fn)
def test_scenario(scenario):
    scenario_name, run, exp_gov, exp_ready, exp_risk, exp_pipe, exp_ev = scenario
    ok, msg = verify(scenario_name, run, exp_gov, exp_ready, exp_risk, exp_pipe, exp_ev)
    assert ok, msg
