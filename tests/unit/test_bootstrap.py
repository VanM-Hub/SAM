"""
Unit tests — Bootstrap Manager (Phase 0)
"""

import pytest
from sam.runtime.state import RuntimeState
from sam.runtime.bootstrap import BootstrapManager
from sam.runtime.coordinator import RuntimeCoordinator


class TestBootstrapManager:
    def test_init(self):
        coord = RuntimeCoordinator()
        bs = BootstrapManager(coord)
        assert len(bs.steps) == 10
        assert bs.steps[0] == "load_config"
        assert bs.steps[-1] == "health_check"

    @pytest.mark.asyncio
    async def test_bootstrap_success(self):
        coord = RuntimeCoordinator()
        bs = BootstrapManager(coord)
        result = await bs.bootstrap()
        assert result is True
        assert coord.state == RuntimeState.READY

    @pytest.mark.asyncio
    async def test_bootstrap_sets_bootstrapping_state(self):
        coord = RuntimeCoordinator()
        bs = BootstrapManager(coord)
        # Before bootstrap, state should be INITIALIZING
        assert coord.state == RuntimeState.INITIALIZING
        await bs.bootstrap()
        # After, should be READY
        assert coord.state == RuntimeState.READY

    @pytest.mark.asyncio
    async def test_step_failure_returns_false(self):
        coord = RuntimeCoordinator()
        bs = BootstrapManager(coord)

        # Inject failure into step 5 (discover_plugins)
        original_step = bs._step_discover_plugins
        async def failing_step():
            raise RuntimeError("Simulated failure")
        bs._step_discover_plugins = failing_step

        result = await bs.bootstrap()
        assert result is False
        # State should remain at BOOTSTRAPPING (didn't complete)
        assert coord.state == RuntimeState.BOOTSTRAPPING


class TestBootstrapIntegration:
    @pytest.mark.asyncio
    async def test_coordinator_start_triggers_bootstrap(self):
        coord = RuntimeCoordinator()
        assert coord.state == RuntimeState.INITIALIZING
        state = await coord.start()
        assert state == RuntimeState.READY
        assert coord.state == RuntimeState.READY
        # Session should be created
        session = coord.session_manager.get_current_session()
        assert session is not None
        assert session["state"] == "RUNNING"

    @pytest.mark.asyncio
    async def test_coordinator_start_to_run(self):
        coord = RuntimeCoordinator()
        await coord.start()
        assert coord.state == RuntimeState.READY
        state = await coord.run()
        assert state == RuntimeState.RUNNING

    @pytest.mark.asyncio
    async def test_full_lifecycle(self):
        coord = RuntimeCoordinator()
        # Start
        await coord.start()
        assert coord.state == RuntimeState.READY
        # Run
        await coord.run()
        assert coord.state == RuntimeState.RUNNING
        # Degrade
        await coord.degrade()
        assert coord.state == RuntimeState.DEGRADED
        # Recover
        await coord.recover()
        assert coord.state == RuntimeState.RUNNING
        # Stop
        await coord.stop()
        assert coord.state == RuntimeState.SHUTDOWN
