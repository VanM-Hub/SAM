import pytest
import asyncio

from sam.confidence.operational import (
    OperationalConfidenceCalculator,
    ConfidenceInput,
)


class InMemoryDB:
    def __init__(self):
        self.rows = []

    async def execute(self, sql, params=None):
        if params:
            # Map params according to insertion order in operational.record
            row = {
                "id": params[0],
                "score": params[1],
                "health_status": params[2],
                "success_rate": params[3],
                "failure_rate": params[4],
                "rollback_rate": params[5],
                "pending_approvals": params[6],
                "runtime_stability": params[7],
                "resource_pressure": params[8],
                "cluster_stability": params[9],
                "knowledge_freshness": params[10],
                "reasoning_confidence": params[11],
                "component_breakdown": params[12],
            }
            self.rows.append(row)

    async def fetch_one(self, sql, params=None):
        if "ORDER BY timestamp DESC LIMIT 1" in sql:
            if not self.rows:
                return None
            return self.rows[-1]
        return None

    async def fetch_all(self, sql, params=None):
        return list(self.rows)


@pytest.mark.asyncio
async def test_confidence_perfect_system():
    db = InMemoryDB()
    calc = OperationalConfidenceCalculator(db=db)
    inputs = ConfidenceInput()
    score, breakdown = await calc.calculate(inputs)
    assert score == 100
    assert breakdown.health == 10.0
    assert breakdown.success_rate == 10.0


@pytest.mark.asyncio
async def test_confidence_degraded_system():
    db = InMemoryDB()
    calc = OperationalConfidenceCalculator(db=db)
    inputs = ConfidenceInput(
        health_status="degraded",
        success_rate=0.6,
        failure_rate=0.4,
        rollback_rate=0.1,
        pending_approvals=5,
        runtime_stability=0.7,
        resource_pressure=0.5,
        cluster_stability=0.8,
        knowledge_freshness=0.9,
        reasoning_confidence=0.7,
    )
    score, breakdown = await calc.calculate(inputs)
    assert isinstance(score, int)
    assert 0 <= score <= 100
    # Expect score less than perfect
    assert score < 100


@pytest.mark.asyncio
async def test_record_and_get_latest():
    db = InMemoryDB()
    calc = OperationalConfidenceCalculator(db=db)
    inputs = ConfidenceInput()
    score, breakdown = await calc.calculate_and_record(inputs)
    latest = await calc.get_latest()
    assert latest is not None
    # When backed by db, get_latest returns a dict with score
    assert isinstance(latest, dict)
    assert "score" in latest or "id" in latest
