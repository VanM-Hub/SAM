"""
H3 — Deployment Rollback Evidence Tests.

Menutup gap H3 (Priority P4, Program D / MISSION-2D, EA-001-003 D3-G1):
- Tidak ada prosedur/artefak rollback deployment terstandar.
- Rollback saat ini hanya berbasis Git source.

Modul: src/sam/deploy_rollback/ (stand-alone capability).
Menyediakan: riwayat deployment ber-version, pointer aktif, snapshot state,
rollback ke versi sebelumnya yang deterministik & terverifikasi.

Constraint EA-002: stand-alone; tidak ubah runtime existing; memakai tmp_path
(bukan folder repo); tidak melakukan efek eksternal.
"""

import json
import os

import pytest

from sam.deploy_rollback.audit import DeploymentAuditLog
from sam.deploy_rollback.manifest import (
    CorruptDeploymentError,
    DeploymentIndex,
    DeploymentNotFound,
)
from sam.deploy_rollback.rollback import DeploymentManager
from sam.deploy_rollback.state import DeploymentSnapshot, DeploymentVersion


@pytest.fixture
def mgr(tmp_path):
    return DeploymentManager(state_dir=str(tmp_path))


@pytest.fixture
def art():
    return "app:web"


# ---------------------------------------------------------------------------
# Deploy
# ---------------------------------------------------------------------------

class TestDeploy:
    def test_deploy_creates_snapshot(self, mgr, art):
        snap = mgr.deploy(art, "1.0.0", {"cfg": {"port": 8080}})
        assert snap.version == "1.0.0"
        assert snap.active is True
        path = mgr.snapshot_path(art, "1.0.0")
        assert os.path.isfile(path)

    def test_deploy_persists_state(self, mgr, art):
        mgr.deploy(art, "1.0.0", {"cfg": {"port": 8080}})
        with open(mgr.snapshot_path(art, "1.0.0"), "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data["state"]["cfg"]["port"] == 8080
        assert data["active"] is True

    def test_deploy_new_version_activates_latest(self, mgr, art):
        mgr.deploy(art, "1.0.0", {"cfg": {"port": 8080}})
        mgr.deploy(art, "1.1.0", {"cfg": {"port": 9090}})
        active = mgr.status(art)
        assert active.version == "1.1.0"
        assert active.active is True

    def test_deploy_deactivates_old_active(self, mgr, art):
        mgr.deploy(art, "1.0.0", {"cfg": {"port": 8080}})
        mgr.deploy(art, "1.1.0", {"cfg": {"port": 9090}})
        idx = DeploymentIndex(mgr._dir)
        old = idx.load(art, "1.0.0")
        assert old.active is False

    def test_version_parse(self):
        assert DeploymentVersion.parse("2.1.3") == DeploymentVersion(2, 1, 3)
        assert DeploymentVersion.parse("v1.0") == DeploymentVersion(1, 0, 0)
        assert str(DeploymentVersion.parse("3.0")) == "3.0.0"


# ---------------------------------------------------------------------------
# Rollback
# ---------------------------------------------------------------------------

class TestRollback:
    def test_rollback_to_previous(self, mgr, art):
        mgr.deploy(art, "1.0.0", {"v": 1})
        mgr.deploy(art, "1.1.0", {"v": 2})
        mgr.deploy(art, "1.2.0", {"v": 3})
        assert mgr.status(art).version == "1.2.0"
        snapped = mgr.rollback(art)
        assert snapped.version == "1.1.0"
        assert mgr.status(art).version == "1.1.0"

    def test_rollback_again_steps_back(self, mgr, art):
        mgr.deploy(art, "1.0.0", {"v": 1})
        mgr.deploy(art, "1.1.0", {"v": 2})
        mgr.deploy(art, "1.2.0", {"v": 3})
        mgr.rollback(art)  # 1.2.0 -> 1.1.0
        mgr.rollback(art)  # 1.1.0 -> 1.0.0
        assert mgr.status(art).version == "1.0.0"

    def test_rollback_no_previous_fails(self, mgr, art):
        mgr.deploy(art, "1.0.0", {"v": 1})
        with pytest.raises(DeploymentNotFound):
            mgr.rollback(art)

    def test_rollback_no_deployment_fails(self, mgr, art):
        with pytest.raises(DeploymentNotFound):
            mgr.rollback(art)

    def test_can_rollback_flag(self, mgr, art):
        mgr.deploy(art, "1.0.0", {"v": 1})
        assert mgr.can_rollback(art) is False
        mgr.deploy(art, "1.1.0", {"v": 2})
        assert mgr.can_rollback(art) is True

    def test_activate_explicit_version(self, mgr, art):
        mgr.deploy(art, "1.0.0", {"v": 1})
        mgr.deploy(art, "1.1.0", {"v": 2})
        # aktifkan kembali 1.0.0 secara eksplisit
        mgr.activate(art, "1.0.0")
        assert mgr.status(art).version == "1.0.0"


# ---------------------------------------------------------------------------
# Manifest / Index
# ---------------------------------------------------------------------------

class TestIndex:
    def test_list_versions_ascending(self, mgr, art):
        for v in ("1.0.0", "1.1.0", "1.2.0"):
            mgr.deploy(art, v, {"i": v})
        idx = DeploymentIndex(mgr._dir)
        assert idx.list_versions(art) == ["1.0.0", "1.1.0", "1.2.0"]

    def test_list_artifacts(self, mgr):
        mgr.deploy("a", "1.0.0", {})
        mgr.deploy("b", "1.0.0", {})
        idx = DeploymentIndex(mgr._dir)
        assert set(idx.list_artifacts()) == {"a", "b"}

    def test_latest_returns_highest(self, mgr, art):
        mgr.deploy(art, "1.0.0", {"v": 1})
        mgr.deploy(art, "1.2.0", {"v": 2})
        idx = DeploymentIndex(mgr._dir)
        assert idx.latest(art).version == "1.2.0"

    def test_load_missing_raises(self, mgr, art):
        mgr.deploy(art, "1.0.0", {"v": 1})
        idx = DeploymentIndex(mgr._dir)
        with pytest.raises(DeploymentNotFound):
            idx.load(art, "9.9.9")

    def test_corrupt_file_raises(self, mgr, art):
        mgr.deploy(art, "1.0.0", {"v": 1})
        path = mgr.snapshot_path(art, "1.0.0")
        with open(path, "w", encoding="utf-8") as f:
            f.write("{not valid json")
        idx = DeploymentIndex(mgr._dir)
        with pytest.raises(CorruptDeploymentError):
            idx.load(art, "1.0.0")


# ---------------------------------------------------------------------------
# Verify / status
# ---------------------------------------------------------------------------

class TestVerifyStatus:
    def test_status_none_when_empty(self, mgr, art):
        assert mgr.status(art) is None

    def test_verify_ok(self, mgr, art):
        mgr.deploy(art, "1.0.0", {"v": 1})
        assert mgr.verify(art, "1.0.0") is True

    def test_history_ascending(self, mgr, art):
        mgr.deploy(art, "1.0.0", {"v": 1})
        mgr.deploy(art, "1.1.0", {"v": 2})
        hist = mgr.history(art)
        assert [h.version for h in hist] == ["1.0.0", "1.1.0"]


# ---------------------------------------------------------------------------
# Audit
# ---------------------------------------------------------------------------

class TestAudit:
    def test_audit_tracks_events(self):
        log = DeploymentAuditLog()
        log.record("deploy", "success", artifact_id="app:web", version="1.0.0")
        log.record("rollback", "failure", artifact_id="app:web", reason="no prev")
        assert log.count() == 2
        assert len(log.failures()) == 1

    def test_audit_no_payload_state(self):
        log = DeploymentAuditLog()
        log.record("deploy", "success", artifact_id="app:web", version="1.0.0")
        for rec in log.all():
            d = rec.as_dict()
            assert "state" not in d
            assert "payload" not in d

    def test_audit_ring_buffer(self):
        log = DeploymentAuditLog(max_records=3)
        for i in range(10):
            log.record("deploy", "success", artifact_id="a", version=f"1.{i}.0")
        assert log.count() == 3
        assert log.all()[0].version == "1.7.0"

    def test_audit_by_artifact(self):
        log = DeploymentAuditLog()
        log.record("deploy", "success", artifact_id="a")
        log.record("deploy", "success", artifact_id="b")
        assert len(log.by_artifact("a")) == 1
        assert len(log.by_artifact("b")) == 1


# ---------------------------------------------------------------------------
# Round-trip penuh: deploy -> "bad release" -> rollback
# ---------------------------------------------------------------------------

class TestRollbackRoundTrip:
    def test_bad_release_rolled_back(self, tmp_path):
        """Simulasi: v1 bagus -> deploy v2 'buruk' -> rollback ke v1."""
        mgr = DeploymentManager(state_dir=str(tmp_path))
        mgr.deploy("app:web", "1.0.0", {"cfg": {"feature_x": False}})

        # rilis v2 ternyata buruk
        mgr.deploy("app:web", "1.1.0", {"cfg": {"feature_x": True, "bug": True}})
        assert mgr.status("app:web").version == "1.1.0"

        # rollback -> kembali ke v1 yang stabil
        rolled = mgr.rollback("app:web")
        assert rolled.version == "1.0.0"
        assert rolled.state["cfg"]["feature_x"] is False
        assert mgr.status("app:web").version == "1.0.0"
        assert mgr.can_rollback("app:web") is False  # sudah paling awal
