"""
Unit tests — Phase 0 Contracts & Core Components
"""

import pytest
from sam.contracts import Mission, MissionStatus, Objective, DesiredOperationalState
from sam.runtime.state import RuntimeState
from sam.runtime.coordinator import RuntimeCoordinator
from sam.mission.loader import MissionLoader
from sam.dos.loader import DOSLoader


# ─── Contracts ───────────────────────────────────────────────────────

class TestMissionContract:
    def test_create_minimal(self):
        m = Mission(id="m1", name="Test", description="Test", objectives=[])
        assert m.id == "m1"
        assert m.priority == 1
        assert m.min_health == 0.8

    def test_create_with_objectives(self):
        obj = Objective(id="o1", name="Health Check")
        m = Mission(id="m1", name="Test", description="Test", objectives=[obj])
        assert len(m.objectives) == 1
        assert m.objectives[0].status == MissionStatus.ACTIVE

    def test_mission_status_enum(self):
        assert MissionStatus.ACTIVE.value == "active"
        assert MissionStatus.DEGRADED.value == "degraded"
        assert MissionStatus.FAILED.value == "failed"
        assert MissionStatus.COMPLETED.value == "completed"


class TestDOSContract:
    def test_defaults(self):
        dos = DesiredOperationalState()
        assert dos.runtime_state == "RUNNING"
        assert dos.plugins_expected == 0
        assert dos.min_health_score == 95.0

    def test_custom(self):
        dos = DesiredOperationalState(
            runtime_state="SAFE_MODE",
            plugins_expected=10,
            min_health_score=80.0,
        )
        assert dos.runtime_state == "SAFE_MODE"
        assert dos.plugins_expected == 10
        assert dos.min_health_score == 80.0


# ─── Runtime State ──────────────────────────────────────────────────

class TestRuntimeState:
    def test_all_12_states(self):
        states = [
            RuntimeState.INITIALIZING,
            RuntimeState.BOOTSTRAPPING,
            RuntimeState.RECOVERING,
            RuntimeState.READY,
            RuntimeState.RUNNING,
            RuntimeState.DEGRADED,
            RuntimeState.PAUSED,
            RuntimeState.UPDATING,
            RuntimeState.STOPPING,
            RuntimeState.SHUTDOWN,
            RuntimeState.CRASHED,
            RuntimeState.SAFE_MODE,
        ]
        assert len(states) == 12


# ─── Runtime Coordinator (Phase 0 API: state + async start/stop) ──

class TestRuntimeCoordinator:
    @pytest.mark.asyncio
    async def test_initial_state(self):
        c = RuntimeCoordinator()
        assert c.state == RuntimeState.INITIALIZING

    @pytest.mark.asyncio
    async def test_start_to_ready(self):
        c = RuntimeCoordinator()
        state = await c.start()
        assert state == RuntimeState.READY
        assert c.state == RuntimeState.READY

    @pytest.mark.asyncio
    async def test_start_to_run(self):
        c = RuntimeCoordinator()
        await c.start()
        state = await c.run()
        assert state == RuntimeState.RUNNING
        assert c.state == RuntimeState.RUNNING

    @pytest.mark.asyncio
    async def test_run_and_shutdown(self):
        c = RuntimeCoordinator()
        await c.start()
        await c.run()
        state = await c.stop()
        assert state == RuntimeState.SHUTDOWN
        assert c.state == RuntimeState.SHUTDOWN

    @pytest.mark.asyncio
    async def test_degrade_and_recover(self):
        c = RuntimeCoordinator()
        await c.start()
        await c.run()
        state = await c.degrade()
        assert state == RuntimeState.DEGRADED
        assert c.state == RuntimeState.DEGRADED
        state = await c.recover()
        assert state == RuntimeState.RUNNING
        assert c.state == RuntimeState.RUNNING

    @pytest.mark.asyncio
    async def test_cannot_run_from_initial(self):
        c = RuntimeCoordinator()
        with pytest.raises(RuntimeError, match="Cannot run from state"):
            await c.run()

    @pytest.mark.asyncio
    async def test_shutdown_is_terminal(self):
        c = RuntimeCoordinator()
        await c.start()
        await c.run()
        await c.stop()
        assert c.state == RuntimeState.SHUTDOWN
        # stop again should be safe
        state = await c.stop()
        assert state == RuntimeState.SHUTDOWN

    @pytest.mark.asyncio
    async def test_session_created_on_start(self):
        c = RuntimeCoordinator()
        await c.start()
        session = c.session_manager.get_current_session()
        assert session is not None
        assert session["state"] == "RUNNING"


# ─── Mission Loader ─────────────────────────────────────────────────

class TestMissionLoader:
    def test_load_from_workspace(self):
        ml = MissionLoader("workspace")
        m = ml.load()
        assert m.name == "Protect OpenClaw"
        assert m.priority == 1
        assert len(m.objectives) == 3

    def test_load_file_not_found(self):
        ml = MissionLoader("nonexistent")
        mission = ml.load()
        # Should return default mission, not raise FileNotFoundError
        assert mission.id == "default-mission"


# ─── DOS Loader ─────────────────────────────────────────────────────

class TestDOSLoader:
    def test_load_from_workspace(self):
        dl = DOSLoader("workspace")
        dos = dl.load()
        assert dos.runtime_state == "RUNNING"
        assert dos.plugins_expected == 14
        assert dos.guardian_mode == "autonomous"

    def test_load_file_not_found(self):
        dl = DOSLoader("nonexistent")
        dos = dl.load()
        # Should return default DOS, not raise FileNotFoundError
        assert dos is not None
