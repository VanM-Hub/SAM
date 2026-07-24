import asyncio
import sys
import uuid
from unittest.mock import AsyncMock

from sam.capabilities.health_checks import HealthCheckCapability
from sam.runtime.context import ExecutionContext
from sam.evidence.models import EvidenceType

async def main():
    mock_store = AsyncMock()
    mock_store.publish = AsyncMock()

    execution_id = uuid.uuid4()
    context = ExecutionContext(
        execution_id=execution_id,
        workflow_id="test-workflow",
        step_name="test-step",
        evidence=mock_store,
    )

    cap = HealthCheckCapability()
    try:
        result = await cap.execute(context)
    except Exception as e:
        print('ERROR: execute raised', e)
        return 2

    # Check that publish was awaited once
    try:
        if mock_store.publish.await_count != 1:
            print('FAIL: publish was not awaited exactly once, await_count=', mock_store.publish.await_count)
            return 1
        ev = mock_store.publish.call_args.args[0]
        if ev.capability_id != cap.metadata.capability_id:
            print('FAIL: capability_id mismatch', ev.capability_id, cap.metadata.capability_id)
            return 1
        if ev.type != EvidenceType.HEALTH_CHECK:
            print('FAIL: evidence type mismatch', ev.type)
            return 1
        if ev.payload != result:
            print('FAIL: payload mismatch')
            return 1
    except Exception as e:
        print('ERROR inspecting publish call:', e)
        return 2

    print('PASS: HealthCheckCapability published evidence as expected')
    return 0

if __name__ == '__main__':
    rc = asyncio.run(main())
    sys.exit(rc)
