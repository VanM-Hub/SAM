"""
H2 — Runtime Checkpoint & Recovery Evidence Tests.

Menutup gap H2 (Priority P3, Program D / MISSION-2D, EA-001-002 D2-G1):
- Capture state -> persist ke disk (atomic write, ber-checksum).
- Restore/resume state setelah "crash/restart" dari checkpoint terbaru.
- Deteksi korupsi/tamper via checksum (tidak memakai state korup).
- Index/manifest checkpoint (latest, list, get).
- Retensi / ring buffer.
- Audit recovery (create/restore/delete, tanpa payload state).

Constraint EA-002 dijaga: modul recovery stand-alone, memakai tmp_path
(bukan folder repo), TIDAK mengubah runtime existing.
"""

import json
import os

import pytest

from sam.recovery.audit import CheckpointAuditLog
from sam.recovery.checkpoint import CheckpointManager, RetentionPolicy
from sam.recovery.manifest import CheckpointIndex, CheckpointNotFound, CorruptCheckpointError
from sam.recovery.restore import RestoreManager
from sam.recovery.state import CheckpointState


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mgr(tmp_path):
    """CheckpointManager memakai tmp_path (bukan folder repo)."""
    return CheckpointManager(state_dir=str(tmp_path))


@pytest.fixture
def scope(mgr):
    return "runtime:mission"


# ---------------------------------------------------------------------------
# Capture & Persist
# ---------------------------------------------------------------------------

class TestCapturePersist:
    def test_capture_computes_metadata(self, mgr, scope):
        cp_state = mgr.capture(scope, {"phase": 2, "odo": 42})
        assert cp_state.metadata.scope == scope
        assert cp_state.metadata.checksum_sha256  # checksum terisi
        assert cp_state.metadata.checkpoint_id.startswith("ckpt-")

    def test_persist_writes_file_to_disk(self, mgr, scope):
        cp = mgr.persist(mgr.capture(scope, {"phase": 2}))
        path = mgr.checkpoint_path(scope, cp.checkpoint_id)
        assert os.path.isfile(path)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data["checkpoint_id"] == cp.checkpoint_id
        assert data["state"]["phase"] == 2

    def test_persist_creates_scope_dir(self, mgr, scope):
        mgr.persist(mgr.capture(scope, {"a": 1}))
        assert os.path.isdir(os.path.join(str(mgr._dir), scope.replace(":", "_")))

    def test_safe_scope_dir_maps_colon(self, mgr):
        mgr.persist(mgr.capture("runtime:mission", {"a": 1}))
        # ':' disanitasi jadi '_' agar aman lintas filesystem
        scopedir = os.path.join(str(mgr._dir), "runtime_mission")
        assert os.path.isdir(scopedir)

    def test_multiple_checkpoints_sorted(self, mgr, scope):
        for i in range(3):
            mgr.persist(mgr.capture(scope, {"i": i}, checkpoint_id=f"c{i}"))
        assert mgr.list_checkpoints(scope) == ["c0", "c1", "c2"]

    def test_atomic_write_leaves_clean_file(self, mgr, scope):
        # Simulasi: setelah persist, tidak ada file temp tersisa
        cid = "atom-1"
        mgr.persist(mgr.capture(scope, {"x": 1}, checkpoint_id=cid))
        leftovers = [n for n in os.listdir(os.path.join(str(mgr._dir), "runtime_mission"))
                     if n.endswith(".tmp")]
        assert leftovers == []


# ---------------------------------------------------------------------------
# Restore & Checksum
# ---------------------------------------------------------------------------

class TestRestoreChecksum:
    def test_restore_latest_returns_state(self, mgr, scope):
        mgr.persist(mgr.capture(scope, {"i": 1}, checkpoint_id="c1"))
        mgr.persist(mgr.capture(scope, {"i": 2}, checkpoint_id="c2"))
        rm = RestoreManager(mgr)
        res = rm.restore_latest(scope)
        assert res.ok is True
        assert res.state == {"i": 2}
        assert res.checksum_verified is True

    def test_restore_specific_checkpoint(self, mgr, scope):
        mgr.persist(mgr.capture(scope, {"i": 1}, checkpoint_id="c1"))
        mgr.persist(mgr.capture(scope, {"i": 2}, checkpoint_id="c2"))
        rm = RestoreManager(mgr)
        res = rm.restore(scope, "c1")
        assert res.ok is True
        assert res.state == {"i": 1}

    def test_restore_no_checkpoint_fails(self, mgr, scope):
        rm = RestoreManager(mgr)
        res = rm.restore_latest(scope)
        assert res.ok is False
        assert res.reason == "no checkpoint"

    def test_restore_missing_id_fails(self, mgr, scope):
        mgr.persist(mgr.capture(scope, {"i": 1}, checkpoint_id="c1"))
        rm = RestoreManager(mgr)
        res = rm.restore(scope, "nope")
        assert res.ok is False
        assert res.reason == "not found"

    def test_verify_checksum_detects_tamper(self, mgr, scope):
        cp = mgr.persist(mgr.capture(scope, {"i": 1}, checkpoint_id="c1"))
        # Tamper file: ubah payload state tanpa update checksum
        path = mgr.checkpoint_path(scope, cp.checkpoint_id)
        data = json.load(open(path, "r", encoding="utf-8"))
        data["state"]["i"] = 999
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f)
        rm = RestoreManager(mgr)
        res = rm.restore_latest(scope)
        assert res.ok is False
        assert "checksum mismatch" in res.reason

    def test_verify_checksum_ok_for_legit(self, mgr, scope):
        cp = mgr.persist(mgr.capture(scope, {"i": 1}, checkpoint_id="c1"))
        rm = RestoreManager(mgr)
        assert rm.verify_checksum(cp) is True


# ---------------------------------------------------------------------------
# Manifest / Index
# ---------------------------------------------------------------------------

class TestIndex:
    def test_latest_picks_newest(self, mgr, scope):
        mgr.persist(mgr.capture(scope, {"i": 1}, checkpoint_id="a", ))
        mgr.persist(mgr.capture(scope, {"i": 2}, checkpoint_id="b"))
        idx = CheckpointIndex(mgr)
        latest = idx.latest(scope)
        assert latest.checkpoint_id == "b"

    def test_list_scopes(self, mgr):
        mgr.persist(mgr.capture("s1", {"a": 1}))
        mgr.persist(mgr.capture("s2", {"b": 2}))
        idx = CheckpointIndex(mgr)
        assert set(idx.list_scopes()) == {"s1", "s2"}

    def test_get_missing_raises(self, mgr, scope):
        idx = CheckpointIndex(mgr)
        with pytest.raises(CheckpointNotFound):
            idx.get(scope, "ghost")

    def test_corrupt_file_raises_corrupt(self, mgr, scope):
        cp = mgr.persist(mgr.capture(scope, {"i": 1}, checkpoint_id="bad"))
        path = mgr.checkpoint_path(scope, cp.checkpoint_id)
        with open(path, "w", encoding="utf-8") as f:
            f.write("{not valid json")
        idx = CheckpointIndex(mgr)
        with pytest.raises(CorruptCheckpointError):
            idx.load(scope, "bad")


# ---------------------------------------------------------------------------
# Retention / Policy
# ---------------------------------------------------------------------------

class TestRetention:
    def test_retention_removes_oldest(self, mgr, scope):
        for i in range(5):
            mgr.persist(mgr.capture(scope, {"i": i}, checkpoint_id=f"c{i}"))
        removed = mgr.apply_retention(scope, RetentionPolicy(max_checkpoints=3))
        assert set(removed) == {"c0", "c1"}
        assert mgr.list_checkpoints(scope) == ["c2", "c3", "c4"]

    def test_retention_keeps_when_within(self, mgr, scope):
        mgr.persist(mgr.capture(scope, {"i": 1}, checkpoint_id="c1"))
        removed = mgr.apply_retention(scope, RetentionPolicy(max_checkpoints=5))
        assert removed == []

    def test_retention_never_removes_all(self, mgr, scope):
        for i in range(3):
            mgr.persist(mgr.capture(scope, {"i": i}, checkpoint_id=f"c{i}"))
        mgr.apply_retention(scope, RetentionPolicy(max_checkpoints=1, scope=scope))
        assert mgr.list_checkpoints(scope) == ["c2"]


# ---------------------------------------------------------------------------
# Audit
# ---------------------------------------------------------------------------

class TestAudit:
    def test_audit_tracks_events(self):
        log = CheckpointAuditLog()
        log.record("checkpoint_create", "success", scope="runtime:mission", checkpoint_id="c1")
        log.record("restore", "failure", scope="runtime:mission", reason="no checkpoint")
        assert log.count() == 2
        assert len(log.failures()) == 1

    def test_audit_never_contains_state_payload(self):
        log = CheckpointAuditLog()
        log.record("checkpoint_create", "success", scope="s1", checkpoint_id="c1")
        content = str(log.all())
        # Tidak ada dict payload state / data sensitif
        assert "state" not in (r.as_dict().get("reason", "") for r in log.all())
        for rec in log.all():
            d = rec.as_dict()
            assert "state" not in d
            assert "payload" not in d

    def test_audit_ring_buffer(self):
        log = CheckpointAuditLog(max_records=3)
        for i in range(10):
            log.record("restore", "success", checkpoint_id=f"c{i}")
        assert log.count() == 3
        assert log.all()[0].checkpoint_id == "c7"


# ---------------------------------------------------------------------------
# Round-trip penuh (simulasi crash -> restart -> resume)
# ---------------------------------------------------------------------------

class TestRecoveryRoundTrip:
    def test_crash_restart_resume_via_persistence(self, tmp_path):
        """Simulasi: proses 1 simpan, 'crash', proses 2 restore state."""
        # Proses 1: capture + persist
        m1 = CheckpointManager(state_dir=str(tmp_path))
        m1.persist(m1.capture("runtime:mission", {"phase": 3, "odo": 100}, checkpoint_id="ck1"))

        # "Crash" -> proses baru memakai state_dir yang sama
        m2 = CheckpointManager(state_dir=str(tmp_path))
        rm = RestoreManager(m2)
        res = rm.restore_latest("runtime:mission")
        assert res.ok is True
        assert res.state == {"phase": 3, "odo": 100}
