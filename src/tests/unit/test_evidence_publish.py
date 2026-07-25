import uuid

import pytest

from unittest.mock import AsyncMock

from sam.capabilities.health_checks import HealthCheckCapability
from sam.runtime.context import ExecutionContext
from sam.evidence.models import EvidenceType


@pytest.mark.asyncio
async def test_health_check_publishes_evidence():
    """HealthCheckCapability should publish an Evidence record when an EvidenceStore is present.

    We use an AsyncMock for the EvidenceStore.publish coroutine and assert it was awaited
    with an Evidence object that contains the expected capability_id and payload.
    """
    mock_store = AsyncMock()
    # The publish attribute is itself an AsyncMock
    mock_store.publish = AsyncMock()

    execution_id = uuid.uuid4()
    context = ExecutionContext(
        execution_id=execution_id,
        workflow_id="test-workflow",
        step_name="test-step",
        evidence=mock_store,
    )

    cap = HealthCheckCapability()

    result = await cap.execute(context)

    # Ensure publish was awaited once
    mock_store.publish.assert_awaited_once()

    # Inspect the Evidence object passed to publish
    publish_call = mock_store.publish.call_args
    assert publish_call is not None
    ev = publish_call.args[0]

    assert ev.capability_id == cap.metadata.capability_id
    assert ev.type == EvidenceType.HEALTH_CHECK
    assert ev.payload == result
