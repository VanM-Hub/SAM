"""
Session Manager — Phase 0

Menyimpan dan memulihkan session, checkpoint, dan state.
Setiap session tersimpan sebagai file JSON di workspace/sessions/.
"""

import json
import uuid
import structlog
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

logger = structlog.get_logger()


class SessionManager:
    """Session Manager — CRUD untuk session runtime."""

    def __init__(self, workspace_path: str):
        self.workspace = Path(workspace_path)
        self.session_path = self.workspace / "sessions"
        self.session_path.mkdir(parents=True, exist_ok=True)
        self.current_session: Optional[Dict[str, Any]] = None

    def create_session(self, workspace: str = "default") -> str:
        """Buat session baru dan simpan ke disk.

        Args:
            workspace: Nama workspace untuk session ini.

        Returns:
            session_id (string, 8 karakter dari UUID).
        """
        session_id = str(uuid.uuid4())[:8]
        session = {
            "id": session_id,
            "workspace": workspace,
            "started_at": datetime.utcnow().isoformat(),
            "last_activity": datetime.utcnow().isoformat(),
            "state": "RUNNING",
            "checkpoints": [],
        }
        self.current_session = session
        self._save_session(session)
        logger.info("session_created", session_id=session_id)
        return session_id

    def save_checkpoint(self, checkpoint: Dict[str, Any]) -> None:
        """Simpan checkpoint ke session aktif.

        Args:
            checkpoint: Dictionary data checkpoint.
        """
        if not self.current_session:
            logger.warning("no_active_session_for_checkpoint")
            return
        self.current_session["checkpoints"].append(checkpoint)
        self.current_session["last_activity"] = datetime.utcnow().isoformat()
        self._save_session(self.current_session)
        logger.info("checkpoint_saved", session_id=self.current_session["id"])

    def get_current_session(self) -> Optional[Dict[str, Any]]:
        """Ambil session yang sedang aktif."""
        return self.current_session

    def get_session_history(self) -> List[Dict[str, Any]]:
        """Ambil semua session dari disk, urut descending oleh started_at.

        Returns:
            List session dictionaries.
        """
        if not self.session_path.exists():
            return []

        session_files = sorted(self.session_path.glob("*.json"))
        sessions = []
        for f in session_files:
            try:
                with open(f, "r", encoding="utf-8") as fp:
                    sessions.append(json.load(fp))
            except (json.JSONDecodeError, IOError) as e:
                logger.warning("failed_to_read_session_file", file=str(f), error=str(e))

        return sorted(sessions, key=lambda x: x.get("started_at", ""), reverse=True)

    def get_session_by_id(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Ambil session spesifik berdasarkan ID."""
        path = self.session_path / f"{session_id}.json"
        if not path.exists():
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None

    def end_session(self, state: str = "COMPLETED") -> None:
        """Akhiri session aktif."""
        if not self.current_session:
            return
        self.current_session["state"] = state
        self.current_session["last_activity"] = datetime.utcnow().isoformat()
        self._save_session(self.current_session)
        logger.info("session_ended", session_id=self.current_session["id"], state=state)
        self.current_session = None

    def _save_session(self, session: Dict[str, Any]) -> None:
        """Simpan session ke file JSON."""
        path = self.session_path / f"{session['id']}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(session, f, indent=2, ensure_ascii=False)
