import pytest
import asyncio

from sam.evolution.policy import EvolutionPolicy, ProposalType, ProposalStatus
from sam.evolution.params import ParamManager
from sam.evolution.optimizer import OptimizationSuggestion


class DummyParamManager:
    def __init__(self):
        self._vals = {}

    def get(self, name):
        return self._vals.get(name)


class DummyOptimizer:
    def __init__(self):
        self.applied = []

    async def apply_suggestion(self, suggestion):
        self.applied.append(suggestion)
        return f"hist_{suggestion.param_name}"


class DummyConfidence:
    def __init__(self, score=100):
        self._score = score

    def get_current_score(self):
        return self._score


@pytest.mark.asyncio
async def test_create_evaluate_approve_parameter_tune():
    pm = DummyParamManager()
    conf = DummyConfidence(score=80)
    policy = EvolutionPolicy(param_manager=pm, confidence_calculator=conf)

    prop = await policy.create_proposal(
        proposal_type=ProposalType.PARAMETER_TUNE,
        description="tune x",
        param_name="x",
        current_value=1,
        proposed_value=2,
        expected_improvement=2.0,
        confidence=0.5,
    )

    ok = await policy.evaluate(prop)
    assert ok is True
    assert prop.status == ProposalStatus.APPROVED

    optimizer = DummyOptimizer()
    await policy.approve(prop, optimizer=optimizer)
    assert len(optimizer.applied) == 1
    assert optimizer.applied[0].param_name == "x"


@pytest.mark.asyncio
async def test_reject_low_confidence():
    pm = DummyParamManager()
    conf = DummyConfidence(score=10)
    policy = EvolutionPolicy(param_manager=pm, confidence_calculator=conf)

    prop = await policy.create_proposal(
        proposal_type=ProposalType.PARAMETER_TUNE,
        description="tune y",
        param_name="y",
        current_value=1,
        proposed_value=2,
        expected_improvement=0.5,
        confidence=0.1,
    )

    ok = await policy.evaluate(prop)
    assert ok is False
    assert prop.status == ProposalStatus.REJECTED


@pytest.mark.asyncio
async def test_from_suggestion_creates_proposal():
    pm = DummyParamManager()
    policy = EvolutionPolicy(param_manager=pm)
    sugg = OptimizationSuggestion(
        param_name="p1",
        current_value=10,
        suggested_value=11,
        expected_improvement=3.0,
        confidence=0.6,
        evidence=["e1"],
    )
    prop = await policy.from_suggestion(sugg)
    assert prop.param_name == "p1"
    assert "Auto-optimize" in prop.description


@pytest.mark.asyncio
async def test_approve_requires_optimizer_for_param_tune():
    pm = DummyParamManager()
    policy = EvolutionPolicy(param_manager=pm)
    prop = await policy.create_proposal(
        proposal_type=ProposalType.PARAMETER_TUNE,
        description="tune z",
        param_name="z",
        current_value=1,
        proposed_value=2,
        expected_improvement=5.0,
        confidence=0.9,
    )
    # Evaluate to approved
    ok = await policy.evaluate(prop)
    assert ok
    with pytest.raises(ValueError):
        await policy.approve(prop, optimizer=None)


@pytest.mark.asyncio
async def test_concurrent_limit_enforced():
    pm = DummyParamManager()
    policy = EvolutionPolicy(param_manager=pm)

    # Create max pending proposals
    rules = policy.get_rule(ProposalType.PARAMETER_TUNE)
    maxp = rules.max_concurrent_proposals
    props = []
    for i in range(maxp):
        p = await policy.create_proposal(
            proposal_type=ProposalType.PARAMETER_TUNE,
            description=f"p{i}",
            param_name=f"a{i}",
            current_value=0,
            proposed_value=1,
            expected_improvement=2.0,
            confidence=0.9,
        )
        props.append(p)

    newp = await policy.create_proposal(
        proposal_type=ProposalType.PARAMETER_TUNE,
        description="overflow",
        param_name="overflow",
        current_value=0,
        proposed_value=1,
        expected_improvement=2.0,
        confidence=0.9,
    )
    ok = await policy.evaluate(newp)
    assert ok is False
    assert newp.status == ProposalStatus.REJECTED
