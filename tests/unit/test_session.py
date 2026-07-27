"""
Unit tests — Session Manager (Phase 0)
"""

import json
import pytest
from pathlib import Path
from sam.runtime.session import SessionManager


class TestSessionManager:
    @pytest.fixture
    def tmp_workspace(self, tmp_path):
        """Fixture: temporary workspace for session testing."""
        ws = tmp_path / "workspace"
        ws.mkdir()
        return str(ws)

    def test_create_session(self, tmp_workspace):
        sm = SessionManager(tmp_workspace)
        session_id = sm.create_session(workspace="test-ws")
        assert len(session_id) == 8
        assert sm.current_session is not None
        assert sm.current_session["id"] == session_id
        assert sm.current_session["workspace"] == "test-ws"
        assert sm.current_session["state"] == "RUNNING"
        assert sm.current_session["checkpoints"] == []

    def test_create_session_saves_to_disk(self, tmp_workspace):
        sm = SessionManager(tmp_workspace)
        session_id = sm.create_session()
        # Check file exists
        session_file = Path(tmp_workspace) / "sessions" / f"{session_id}.json"
        assert session_file.exists()
        with open(session_file, "r") as f:
            data = json.load(f)
        assert data["id"] == session_id

    def test_save_checkpoint(self, tmp_workspace):
        sm = SessionManager(tmp_workspace)
        sm.create_session()
        cp = {"type": "runtime_state", "state": "READY", "timestamp": "2026-07-27T00:00:00"}
        sm.save_checkpoint(cp)
        assert len(sm.current_session["checkpoints"]) == 1
        assert sm.current_session["checkpoints"][0]["type"] == "runtime_state"

    def test_save_checkpoint_no_session(self, tmp_workspace):
        sm = SessionManager(tmp_workspace)
        # Should not crash
        sm.save_checkpoint({"type": "test"})
        assert sm.current_session is None

    def test_get_current_session(self, tmp_workspace):
        sm = SessionManager(tmp_workspace)
        assert sm.get_current_session() is None
        sm.create_session()
        assert sm.get_current_session() is not None
        assert sm.get_current_session()["id"] is not None

    def test_get_session_history_empty(self, tmp_workspace):
        sm = SessionManager(tmp_workspace)
        history = sm.get_session_history()
        assert history == []

    def test_get_session_history(self, tmp_workspace):
        sm = SessionManager(tmp_workspace)
        id1 = sm.create_session(workspace="ws1")
        sm.end_session("COMPLETED")
        id2 = sm.create_session(workspace="ws2")

        history = sm.get_session_history()
        assert len(history) == 2  # both sessions
        # Most recent first
        assert history[0]["id"] == id2
        assert history[1]["id"] == id1

    def test_get_session_by_id(self, tmp_workspace):
        sm = SessionManager(tmp_workspace)
        session_id = sm.create_session()
        found = sm.get_session_by_id(session_id)
        assert found is not None
        assert found["id"] == session_id

    def test_get_session_by_id_not_found(self, tmp_workspace):
        sm = SessionManager(tmp_workspace)
        found = sm.get_session_by_id("nonexistent")
        assert found is None

    def test_end_session(self, tmp_workspace):
        sm = SessionManager(tmp_workspace)
        sm.create_session()
        assert sm.current_session is not None
        sm.end_session("COMPLETED")
        assert sm.current_session is None
        # File should still exist
        # (can't check id since session was ended and current is None)

    def test_multiple_checkpoints(self, tmp_workspace):
        sm = SessionManager(tmp_workspace)
        sm.create_session()
        for i in range(3):
            sm.save_checkpoint({"i": i, "data": f"cp-{i}"})
        assert len(sm.current_session["checkpoints"]) == 3

    def test_session_path_creation(self, tmp_workspace):
        sm = SessionManager(tmp_workspace)
        session_path = Path(tmp_workspace) / "sessions"
        assert session_path.exists()
        assert session_path.is_dir()
