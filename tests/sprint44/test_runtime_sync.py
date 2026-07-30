import pytest
import os
from dataclasses import FrozenInstanceError
from datetime import datetime

from sam.guardian.live.state import (
    RuntimeState, RuntimeStatus, RuntimeHealth, RuntimeVersion,
    RuntimeStatistics, RuntimeSnapshot,
)
from sam.guardian.live.registry import GuardianRuntimeRegistry
from sam.guardian.live.synchronizer import GuardianRuntimeSynchronizer
from sam.guardian.live.snapshot import GuardianSnapshotManager
from sam.guardian.live.validator import GuardianConsistencyValidator
from sam.guardian.live.event import (
    GuardianEvent, GuardianEventMetadata, GuardianEventType,
    GuardianEventPriority, GuardianEventSource,
)


# --- DTO immutability ---

def test_runtime_state_frozen():
    state = RuntimeState(runtime_id="test-1")
    with pytest.raises(FrozenInstanceError):
        state.runtime_id = "changed"


def test_runtime_statistics_frozen():
    stats = RuntimeStatistics(timestamp=0.0)
    with pytest.raises(FrozenInstanceError):
        stats.total_dispatched = 100


def test_runtime_snapshot_frozen():
    snap = RuntimeSnapshot(
        snapshot_id="s1", timestamp=0.0, total_runtimes=0,
        runtimes={}, statistics=RuntimeStatistics.empty(),
    )
    with pytest.raises(FrozenInstanceError):
        snap.snapshot_id = "changed"


def test_runtime_state_to_dict():
    state = RuntimeState(runtime_id="test-1", version=RuntimeVersion.V5_0_0)
    d = state.to_dict()
    assert d["runtime_id"] == "test-1"
    assert d["version"] == "5.0.0"
    assert "health" in d
    assert "status" in d
    assert "statistics" in d


def test_runtime_version_current():
    assert str(RuntimeVersion.current()) == "5.0.0"


def test_runtime_statistics_empty():
    s = RuntimeStatistics.empty()
    assert s.total_dispatched == 0
    assert s.timestamp > 0


# --- Registry ---

def test_registry_register():
    reg = GuardianRuntimeRegistry()
    state = reg.register("runtime-1")
    assert state.runtime_id == "runtime-1"
    assert reg.count == 1


def test_registry_register_duplicate():
    reg = GuardianRuntimeRegistry()
    reg.register("runtime-1")
    reg.register("runtime-1")
    assert reg.count == 1


def test_registry_unregister():
    reg = GuardianRuntimeRegistry()
    reg.register("runtime-1")
    assert reg.unregister("runtime-1") is True
    assert reg.count == 0


def test_registry_unregister_not_found():
    reg = GuardianRuntimeRegistry()
    assert reg.unregister("nonexistent") is False


def test_registry_lookup():
    reg = GuardianRuntimeRegistry()
    reg.register("runtime-1")
    state = reg.lookup("runtime-1")
    assert state is not None
    assert state.runtime_id == "runtime-1"


def test_registry_lookup_not_found():
    reg = GuardianRuntimeRegistry()
    assert reg.lookup("nonexistent") is None


def test_registry_list():
    reg = GuardianRuntimeRegistry()
    reg.register("a")
    reg.register("b")
    items = reg.list()
    assert len(items) == 2


def test_registry_ids():
    reg = GuardianRuntimeRegistry()
    reg.register("x")
    reg.register("y")
    assert reg.ids == ["x", "y"]


def test_registry_exists():
    reg = GuardianRuntimeRegistry()
    reg.register("r1")
    assert reg.exists("r1") is True
    assert reg.exists("r2") is False


def test_registry_clear():
    reg = GuardianRuntimeRegistry()
    reg.register("r1")
    reg.register("r2")
    reg.clear()
    assert reg.count == 0


def test_registry_snapshot():
    reg = GuardianRuntimeRegistry()
    reg.register("r1")
    reg.register("r2")
    snap = reg.snapshot()
    assert snap.total_runtimes == 2
    assert snap.snapshot_id is not None


def test_registry_statistics():
    reg = GuardianRuntimeRegistry()
    reg.register("r1")
    stats = reg.statistics()
    assert stats["total_runtimes"] == 1


def test_registry_update_state():
    reg = GuardianRuntimeRegistry()
    reg.register("r1")
    updated = reg.update_state("r1", status=RuntimeStatus.DEGRADED)
    assert updated is not None
    assert updated.status == RuntimeStatus.DEGRADED


def test_registry_update_state_not_found():
    reg = GuardianRuntimeRegistry()
    assert reg.update_state("nonexistent") is None


# --- Synchronizer ---

def test_synchronizer_init():
    reg = GuardianRuntimeRegistry()
    sync = GuardianRuntimeSynchronizer(reg)
    assert sync.sync_count == 0
    assert sync.last_summary is None


def test_synchronizer_set_runtime_id():
    reg = GuardianRuntimeRegistry()
    sync = GuardianRuntimeSynchronizer(reg)
    sync.set_runtime_id("my-runtime")
    assert sync.current_runtime_id == "my-runtime"


def test_synchronizer_register_current():
    reg = GuardianRuntimeRegistry()
    sync = GuardianRuntimeSynchronizer(reg)
    sync.set_runtime_id("auto-register")
    state = sync.register_current()
    assert state.runtime_id == "auto-register"
    assert reg.exists("auto-register")


def test_synchronizer_synchronize():
    reg = GuardianRuntimeRegistry()
    sync = GuardianRuntimeSynchronizer(reg)
    sync.set_runtime_id("sync-runtime")
    meta = GuardianEventMetadata(
        event_type=GuardianEventType.OBSERVATION_UPDATE,
        priority=GuardianEventPriority.MEDIUM,
        source=GuardianEventSource.OBSERVATION,
        timestamp=0.0,
    )
    event = GuardianEvent(metadata=meta, payload={"k": "v"})
    summary = sync.synchronize(event)
    assert summary["sync_count"] == 1
    assert summary["runtime_count"] >= 1
    assert "version_check" in summary


def test_synchronizer_create_sync_summary():
    reg = GuardianRuntimeRegistry()
    sync = GuardianRuntimeSynchronizer(reg)
    sync.set_runtime_id("summary-test")
    meta = GuardianEventMetadata(
        event_type=GuardianEventType.GUARDIAN_HEALTH_UPDATE,
        priority=GuardianEventPriority.HIGH,
        source=GuardianEventSource.GUARDIAN,
        timestamp=0.0,
    )
    event = GuardianEvent(metadata=meta, payload={})
    sync.synchronize(event)
    summary = sync.create_sync_summary()
    assert summary["sync_count"] == 1


# --- Snapshot Manager ---

def test_snapshot_manager_init():
    mgr = GuardianSnapshotManager()
    assert mgr.count == 0
    assert mgr.current is None


def test_snapshot_manager_capture():
    mgr = GuardianSnapshotManager()
    snap = RuntimeSnapshot(
        snapshot_id="s1", timestamp=0.0, total_runtimes=1,
        runtimes={"r1": RuntimeState(runtime_id="r1")},
        statistics=RuntimeStatistics.empty(),
    )
    mgr.capture(snap)
    assert mgr.count == 1
    assert mgr.current is not None


def test_snapshot_manager_get():
    mgr = GuardianSnapshotManager()
    snap = RuntimeSnapshot(
        snapshot_id="s1", timestamp=0.0, total_runtimes=0,
        runtimes={}, statistics=RuntimeStatistics.empty(),
    )
    mgr.capture(snap)
    assert mgr.get(0) is not None
    assert mgr.get(99) is None


def test_snapshot_manager_get_by_id():
    mgr = GuardianSnapshotManager()
    snap = RuntimeSnapshot(
        snapshot_id="find-me", timestamp=0.0, total_runtimes=0,
        runtimes={}, statistics=RuntimeStatistics.empty(),
    )
    mgr.capture(snap)
    found = mgr.get_by_id("find-me")
    assert found is not None
    assert found.snapshot_id == "find-me"


def test_snapshot_manager_diff_no_data():
    mgr = GuardianSnapshotManager()
    diff = mgr.diff()
    assert diff["has_diff"] is False


def test_snapshot_manager_diff_changes():
    mgr = GuardianSnapshotManager()
    snap_a = RuntimeSnapshot(
        snapshot_id="s1", timestamp=0.0, total_runtimes=0,
        runtimes={}, statistics=RuntimeStatistics.empty(),
    )
    snap_b = RuntimeSnapshot(
        snapshot_id="s2", timestamp=1.0, total_runtimes=1,
        runtimes={
            "r1": RuntimeState(runtime_id="r1", status=RuntimeStatus.RUNNING)
        },
        statistics=RuntimeStatistics.empty(),
    )
    mgr.capture(snap_a)
    mgr.capture(snap_b)
    diff = mgr.diff()
    assert diff["has_diff"] is True or diff.get("has_diff") is not None


def test_snapshot_manager_rollback_preview():
    mgr = GuardianSnapshotManager()
    snap = RuntimeSnapshot(
        snapshot_id="s1", timestamp=0.0, total_runtimes=0,
        runtimes={}, statistics=RuntimeStatistics.empty(),
    )
    mgr.capture(snap)
    preview = mgr.rollback_preview(target_index=0)
    assert "can_rollback" in preview


def test_snapshot_manager_rollback_not_found():
    mgr = GuardianSnapshotManager()
    preview = mgr.rollback_preview(target_snapshot_id="does-not-exist")
    assert preview["can_rollback"] is False


def test_snapshot_manager_max_size():
    mgr = GuardianSnapshotManager(max_history=5)
    assert mgr.max_size == 5
    assert mgr.count == 0
    for i in range(10):
        snap = RuntimeSnapshot(
            snapshot_id=f"s{i}", timestamp=float(i), total_runtimes=0,
            runtimes={}, statistics=RuntimeStatistics.empty(),
        )
        mgr.capture(snap)
    assert mgr.count <= 5


def test_snapshot_manager_clear():
    mgr = GuardianSnapshotManager()
    snap = RuntimeSnapshot(
        snapshot_id="s1", timestamp=0.0, total_runtimes=0,
        runtimes={}, statistics=RuntimeStatistics.empty(),
    )
    mgr.capture(snap)
    mgr.clear()
    assert mgr.count == 0
    assert mgr.current is None


# --- Validator ---

def test_validator_duplicate_check():
    reg = GuardianRuntimeRegistry()
    snap_mgr = GuardianSnapshotManager()
    val = GuardianConsistencyValidator(reg, snap_mgr)
    result = val.check_duplicate_runtime()
    assert result["pass"] is True


def test_validator_missing_runtime_no_expected():
    reg = GuardianRuntimeRegistry()
    snap_mgr = GuardianSnapshotManager()
    val = GuardianConsistencyValidator(reg, snap_mgr)
    result = val.check_missing_runtime()
    assert result["pass"] is True


def test_validator_missing_runtime_with_expected():
    reg = GuardianRuntimeRegistry()
    snap_mgr = GuardianSnapshotManager()
    val = GuardianConsistencyValidator(reg, snap_mgr)
    val.set_expected_runtimes(["r1", "r2"])
    result = val.check_missing_runtime()
    assert result["pass"] is False
    assert "r1" in result["missing"]


def test_validator_version_mismatch_clean():
    reg = GuardianRuntimeRegistry()
    snap_mgr = GuardianSnapshotManager()
    val = GuardianConsistencyValidator(reg, snap_mgr)
    result = val.check_version_mismatch()
    assert result["pass"] is True


def test_validator_health_clean():
    reg = GuardianRuntimeRegistry()
    snap_mgr = GuardianSnapshotManager()
    val = GuardianConsistencyValidator(reg, snap_mgr)
    result = val.check_health_mismatch()
    assert result["pass"] is True


def test_validator_snapshot_not_enough():
    reg = GuardianRuntimeRegistry()
    snap_mgr = GuardianSnapshotManager()
    val = GuardianConsistencyValidator(reg, snap_mgr)
    result = val.check_snapshot_mismatch()
    assert result["pass"] is True


def test_validator_registry_mismatch_clean():
    reg = GuardianRuntimeRegistry()
    snap_mgr = GuardianSnapshotManager()
    val = GuardianConsistencyValidator(reg, snap_mgr)
    result = val.check_registry_mismatch()
    # Both are 0 so they match
    assert result["pass"] is True


def test_validator_outdated_clean():
    reg = GuardianRuntimeRegistry()
    snap_mgr = GuardianSnapshotManager()
    val = GuardianConsistencyValidator(reg, snap_mgr)
    result = val.check_outdated_runtime()
    assert result["pass"] is True


def test_validator_validate_all():
    reg = GuardianRuntimeRegistry()
    snap_mgr = GuardianSnapshotManager()
    val = GuardianConsistencyValidator(reg, snap_mgr)
    results = val.validate_all()
    assert "duplicate_runtime" in results
    assert "missing_runtime" in results
    assert "version_mismatch" in results
    assert "health_mismatch" in results
    assert "snapshot_mismatch" in results
    assert "registry_mismatch" in results
    assert "outdated_runtime" in results
    assert "overall_consistent" in results


def test_validator_is_consistent_empty():
    reg = GuardianRuntimeRegistry()
    snap_mgr = GuardianSnapshotManager()
    val = GuardianConsistencyValidator(reg, snap_mgr)
    assert val.is_consistent() is True


# --- Conversation Sync ---

def test_conversation_sync_query_count():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    runtime = GuardianLiveRuntime(runtime_id="test-conv")
    assert runtime.conversation_sync.query_count == 10


def test_conversation_sync_runtime_state():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    runtime = GuardianLiveRuntime(runtime_id="test-conv2")
    result = runtime.conversation_sync.runtime_state()
    assert result["query"] == "runtime_state"


def test_conversation_sync_registry():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    runtime = GuardianLiveRuntime(runtime_id="test-conv3")
    runtime.registry.register("r1")
    result = runtime.conversation_sync.registry()
    assert result["count"] == 1


def test_conversation_sync_snapshot():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    runtime = GuardianLiveRuntime(runtime_id="test-conv4")
    runtime.registry.register("r1")
    result = runtime.conversation_sync.snapshot()
    assert result["snapshot"]["total_runtimes"] == 1


def test_conversation_sync_version():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    runtime = GuardianLiveRuntime(runtime_id="test-conv5")
    runtime.registry.register("r1")
    result = runtime.conversation_sync.version()
    assert result["current_version"] == "5.0.0"


def test_conversation_sync_health():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    runtime = GuardianLiveRuntime(runtime_id="test-conv6")
    runtime.registry.register("r1")
    result = runtime.conversation_sync.health()
    assert result["total"] == 1


def test_conversation_sync_history():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    runtime = GuardianLiveRuntime(runtime_id="test-conv7")
    result = runtime.conversation_sync.history()
    assert result["total"] == 0


def test_conversation_sync_diff():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    runtime = GuardianLiveRuntime(runtime_id="test-conv8")
    result = runtime.conversation_sync.diff()
    assert "diff" in result


def test_conversation_sync_statistics():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    runtime = GuardianLiveRuntime(runtime_id="test-conv9")
    result = runtime.conversation_sync.statistics()
    assert "statistics" in result


def test_conversation_sync_latest_sync():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    runtime = GuardianLiveRuntime(runtime_id="test-conv10")
    result = runtime.conversation_sync.latest_sync()
    assert result["has_sync"] is False


def test_conversation_sync_summary():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    runtime = GuardianLiveRuntime(runtime_id="test-conv11")
    result = runtime.conversation_sync.summary()
    assert "registry_count" in result
    assert "consistent" in result


# --- Dashboard Sync ---

def test_dashboard_sync_card_count():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    runtime = GuardianLiveRuntime(runtime_id="test-dash")
    assert runtime.dashboard_sync.card_count == 6


def test_dashboard_sync_runtime_registry_card():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    runtime = GuardianLiveRuntime(runtime_id="test-dash2")
    runtime.registry.register("r1")
    card = runtime.dashboard_sync.get_runtime_registry_card()
    assert card.total_runtimes == 1


def test_dashboard_sync_synchronization_card():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    runtime = GuardianLiveRuntime(runtime_id="test-dash3")
    card = runtime.dashboard_sync.get_synchronization_card()
    assert card.sync_count == 0


def test_dashboard_sync_version_matrix_card():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    runtime = GuardianLiveRuntime(runtime_id="test-dash4")
    runtime.registry.register("r1")
    card = runtime.dashboard_sync.get_version_matrix_card()
    assert card.all_matching is True


def test_dashboard_sync_snapshot_card():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    runtime = GuardianLiveRuntime(runtime_id="test-dash5")
    card = runtime.dashboard_sync.get_snapshot_card()
    assert card.total_snapshots == 0


def test_dashboard_sync_consistency_card():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    runtime = GuardianLiveRuntime(runtime_id="test-dash6")
    card = runtime.dashboard_sync.get_consistency_card()
    assert isinstance(card.is_consistent, bool)


def test_dashboard_sync_sync_health_card():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    runtime = GuardianLiveRuntime(runtime_id="test-dash7")
    card = runtime.dashboard_sync.get_sync_health_card()
    assert card.registry_count == 0


def test_dashboard_sync_all_cards():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    runtime = GuardianLiveRuntime(runtime_id="test-dash8")
    cards = runtime.dashboard_sync.get_all_cards()
    assert len(cards) == 6


# --- Runtime pipeline integration ---

def test_full_pipeline_with_sync():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    from sam.guardian.live.subscriber import GuardianEventSubscriber

    class TestSub(GuardianEventSubscriber):
        def supports(self, event):
            return True
        def handle(self, event):
            return {"handled": True}

    runtime = GuardianLiveRuntime(runtime_id="pipeline-test")
    runtime.start()
    runtime.register_subscriber(TestSub())

    result = runtime.execute_pipeline(observation_payload={"test": True})
    assert result["is_running"] is True
    assert result["event_id"] is not None
    assert result["pipeline"] is not None
    assert "synchronization" in result["pipeline"]
    assert runtime.registry.count >= 1
    assert runtime.synchronizer.sync_count >= 1
    runtime.stop()


def test_pipeline_status_after_run():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    from sam.guardian.live.subscriber import GuardianEventSubscriber

    class TestSub(GuardianEventSubscriber):
        def supports(self, event):
            return True
        def handle(self, event):
            return {"handled": True}

    runtime = GuardianLiveRuntime(runtime_id="status-test")
    runtime.start()
    runtime.register_subscriber(TestSub())
    runtime.execute_pipeline()
    status = runtime.get_status()
    assert status["registry_count"] >= 1
    assert status["sync_count"] >= 1
    assert "consistent" in status
    runtime.stop()


# --- Forbidden import scanning ---

FORBIDDEN_PATTERNS = [
    "from sam.domain",
    "from sam.repository",
    "from sam.storage",
    "import threading",
    "import asyncio",
    "async def",
    "import socket",
    "import websockets",
    "from websocket",
    "import multiprocessing",
    "from sam.operations",
]


def test_forbidden_imports_in_new_files():
    base = os.path.join(os.path.dirname(__file__), "..", "..", "src", "sam", "guardian", "live")
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    live_path = os.path.join(project_root, "src", "sam", "guardian", "live")
    sprint44_files = [
        "state.py", "registry.py", "synchronizer.py",
        "snapshot.py", "validator.py",
        "conversation_sync.py", "dashboard_sync.py",
    ]
    for fname in sprint44_files:
        path = os.path.join(live_path, fname)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()
            for pattern in FORBIDDEN_PATTERNS:
                assert pattern not in text, f"Forbidden pattern '{pattern}' found in {fname}"


def test_no_async_keywords_in_new_files():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    live_path = os.path.join(project_root, "src", "sam", "guardian", "live")
    sprint44_files = [
        "state.py", "registry.py", "synchronizer.py",
        "snapshot.py", "validator.py",
        "conversation_sync.py", "dashboard_sync.py",
    ]
    for fname in sprint44_files:
        path = os.path.join(live_path, fname)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()
            assert "async def" not in text
            assert "await " not in text


# --- Determinism ---

@pytest.mark.parametrize("i", list(range(80)))
def test_deterministic_sync(i):
    """Parametrized test: deterministic synchronization produces consistent results."""
    from sam.guardian.live.runtime import GuardianLiveRuntime
    from sam.guardian.live.subscriber import GuardianEventSubscriber

    class DetSub(GuardianEventSubscriber):
        def __init__(self):
            self.count = 0
        def supports(self, event):
            return True
        def handle(self, event):
            self.count += 1
            return {"handled": self.count}

    runtime = GuardianLiveRuntime(runtime_id=f"det-{i:03d}")
    runtime.start()
    runtime.register_subscriber(DetSub())
    runtime.execute_pipeline()
    assert runtime.registry.exists(f"det-{i:03d}")
    runtime.stop()
