"""
Unit tests — Shutdown Manager (Phase 0)
"""

import pytest
from sam.runtime.shutdown import ShutdownManager
from sam.runtime.state import RuntimeState
from sam.runtime.coordinator import RuntimeCoordinator


class TestShutdownManager:
    @pytest.mark.asyncio
    async def test_init(self):
        coord = RuntimeCoordinator()
        sm = ShutdownManager(coord)
        assert len(sm.steps) == 6
        assert sm.steps[0] == "_stop_accepting_work"
        assert sm.steps[-1] == "_close_database"

    @pytest.mark.asyncio
    async def test_shutdown_success(self):
        coord = RuntimeCoordinator()
        await coord.start()
        await coord.run()
        sm = ShutdownManager(coord)
        result = await sm.shutdown()
        assert result is True
        assert coord.state == RuntimeState.SHUTDOWN

    @pytest.mark.asyncio
    async def test_shutdown_sets_stopping_state(self):
        coord = RuntimeCoordinator()
        await coord.start()
        sm = ShutdownManager(coord)
        assert coord.state == RuntimeState.READY
        await sm.shutdown()
        assert coord.state == RuntimeState.SHUTDOWN

    @pytest.mark.asyncio
    async def test_shutdown_ends_session(self):
        coord = RuntimeCoordinator()
        await coord.start()
        assert coord.session_manager.current_session is not None
        sm = ShutdownManager(coord)
        await sm.shutdown()
        assert coord.session_manager.current_session is None

    @pytest.mark.asyncio
    async def test_coordinator_stop_triggers_shutdown(self):
        coord = RuntimeCoordinator()
        await coord.start()
        await coord.run()
        state = await coord.stop()
        assert state == RuntimeState.SHUTDOWN
        assert coord.state == RuntimeState.SHUTDOWN


class TestShutdownEdgeCases:
    @pytest.mark.asyncio
    async def test_shutdown_from_initializing(self):
        coord = RuntimeCoordinator()
        sm = ShutdownManager(coord)
        result = await sm.shutdown()
        assert result is True
        assert coord.state == RuntimeState.SHUTDOWN

    @pytest.mark.asyncio
    async def test_double_shutdown(self):
        coord = RuntimeCoordinator()
        await coord.start()
        await coord.run()
        sm = ShutdownManager(coord)
        result1 = await sm.shutdown()
        assert result1 is True
        # Second shutdown should be safe (state already SHUTDOWN)
        result2 = await sm.shutdown()
        assert result2 is True
        assert coord.state == RuntimeState.SHUTDOWN
