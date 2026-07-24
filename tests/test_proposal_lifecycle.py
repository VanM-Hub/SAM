"""Test proposal lifecycle: pending -> approve, pending -> reject, CLI commands."""

import asyncio
import pytest
from typer.testing import CliRunner

from sam.cli.main import app
from sam.evolution.policy import EvolutionPolicy, ProposalType, ProposalStatus
from sam.evolution.params import OptimizableParam


@pytest.fixture
def fresh_policy():
    """Create a fresh policy with a mock param 'x' registered."""
    from sam.cli.evolution_app import _InMemoryParamManager
    pm = _InMemoryParamManager()
    pm._params['x'] = OptimizableParam(
        id='x', name='x', current_value=0,
        min_value=0, max_value=10, step=1,
        category='RANKING', description='test x',
    )
    return EvolutionPolicy(param_manager=pm)


@pytest.mark.asyncio
async def test_proposal_pending_approve_reject_lifecycle(fresh_policy):
    policy = fresh_policy
    # Create proposal
    prop = await policy.create_proposal(
        ProposalType.PARAMETER_TUNE,
        description="tune x",
        param_name="x",
        current_value=0,
        proposed_value=5,
        expected_improvement=10.0,
        confidence=0.9,
        risk_level="low",
    )
    assert prop.status == ProposalStatus.PENDING

    # Evaluate -> should pass
    ok = await policy.evaluate(prop)
    assert ok is True
    assert prop.status == ProposalStatus.APPROVED

    # Reject after approval
    await policy.reject(prop)
    assert prop.status == ProposalStatus.REJECTED


@pytest.mark.asyncio
async def test_proposal_approve_apply_parameter(fresh_policy):
    policy = fresh_policy
    prop = await policy.create_proposal(
        ProposalType.PARAMETER_TUNE,
        description="tune x up",
        param_name="x",
        current_value=0,
        proposed_value=5,
        expected_improvement=10.0,
        confidence=0.9,
        risk_level="low",
    )
    await policy.evaluate(prop)

    # Need optimizer
    from sam.cli.evolution_app import _InMemoryInstitutionalMemory, _InMemoryParamManager
    from sam.evolution.optimizer import SelfOptimizer
    pm = policy._param_manager
    optimizer = SelfOptimizer(
        institutional_memory=_InMemoryInstitutionalMemory(),
        param_manager=pm,
    )
    await policy.approve(prop, optimizer=optimizer)
    param = await pm.get("x")
    assert param is not None
    assert param.current_value == 5


@pytest.mark.asyncio
async def test_proposal_rejected_by_policy(fresh_policy):
    policy = fresh_policy
    prop = await policy.create_proposal(
        ProposalType.PARAMETER_TUNE,
        description="bad proposal",
        param_name="x",
        current_value=0,
        proposed_value=1,
        expected_improvement=0.1,  # below min_improvement=1.0
        confidence=0.1,  # below min_confidence=0.3
        risk_level="high",  # above max_risk=2 (medium)
    )
    ok = await policy.evaluate(prop)
    assert ok is False
    assert prop.status == ProposalStatus.REJECTED


@pytest.mark.asyncio
async def test_proposal_query_filters(fresh_policy):
    policy = fresh_policy
    p1 = await policy.create_proposal(ProposalType.PARAMETER_TUNE, "a",
                                       param_name="x", confidence=0.9,
                                       expected_improvement=20.0, risk_level="low")
    p2 = await policy.create_proposal(ProposalType.STRATEGY_SHIFT, "b",
                                       confidence=0.9, expected_improvement=20.0,
                                       risk_level="low")
    await policy.evaluate(p1)
    await policy.evaluate(p2)
    # Both approved
    assert p1.status == ProposalStatus.APPROVED, f"p1 status={p1.status.value}"
    assert p2.status == ProposalStatus.APPROVED, f"p2 status={p2.status.value}"

    # Filter by type
    params = policy.get_proposals(proposal_type=ProposalType.PARAMETER_TUNE)
    assert len(params) == 1
    assert params[0].id == p1.id

    # Filter by status
    approved = policy.get_proposals(status=ProposalStatus.APPROVED)
    assert len(approved) == 2, f"approved count={len(approved)}"
