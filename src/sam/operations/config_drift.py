"""
ConfigurationDriftDetector — Deteksi perubahan konfigurasi.

Observation:
  - added
  - removed
  - modified
  - secret changed
  - permission changed

Saat ini: pattern-based dari workspace dan runtime.
Future: integrasi dengan config management.
"""

import structlog
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Set
from datetime import datetime, timedelta
import os
import hashlib


logger = structlog.get_logger()


@dataclass
class ConfigChange:
    """Satu perubahan konfigurasi."""
    change_type: str        # added, removed, modified, secret_changed, permission_changed
    path: str               # Path atau key konfigurasi
    old_value: str = ""
    new_value: str = ""
    severity: str = "information"
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_text(self) -> str:
        return "[{type}] {path}{old}{new}".format(
            type=self.change_type.upper(),
            path=self.path,
            old=(": {} -> ".format(self.old_value)) if self.old_value else ": ",
            new=self.new_value if self.new_value else "",
        )


class ConfigurationDriftDetector:
    """Deteksi perubahan konfigurasi dari snapshot ke snapshot.

    Menyimpan baseline untuk perbandingan.
    Jika belum ada baseline, hanya mencatat state awal tanpa alarm.
    """

    def __init__(self, workspace_provider=None):
        self._wp = workspace_provider
        self._baseline: Dict[str, str] = {}
        self._current: Dict[str, str] = {}
        self._changes: List[ConfigChange] = []

    def observe(self) -> List[ConfigChange]:
        """Observasi perubahan konfigurasi sejak baseline terakhir."""
        changes = []

        # Ambil state saat ini
        state = self._capture_state()

        if not self._baseline:
            # Pertama kali — catat sebagai baseline, bukan perubahan
            self._baseline = dict(state)
            self._current = dict(state)
            logger.info("config_baseline_captured", keys=len(state))
            return changes  # Tidak ada perubahan

        # Bandingkan
        old_keys = set(self._baseline.keys())
        new_keys = set(state.keys())

        added = new_keys - old_keys
        removed = old_keys - new_keys
        common = old_keys & new_keys

        for key in sorted(added):
            changes.append(ConfigChange(
                change_type="added",
                path=key,
                new_value=str(state[key])[:100],
            ))

        for key in sorted(removed):
            changes.append(ConfigChange(
                change_type="removed",
                path=key,
                old_value=str(self._baseline.get(key, ""))[:100],
                severity="warning",
            ))

        for key in sorted(common):
            old_val = str(self._baseline.get(key, ""))
            new_val = str(state.get(key, ""))
            if old_val != new_val:
                ctype = "secret_changed" if self._is_secret(key) else "modified"
                changes.append(ConfigChange(
                    change_type=ctype,
                    path=key,
                    old_value=old_val[:100],
                    new_value=new_val[:100],
                    severity="warning" if ctype == "secret_changed" else "information",
                ))

        # Update baseline
        self._baseline = dict(state)
        self._current = dict(state)
        self._changes.extend(changes)

        if changes:
            logger.info("config_drift_detected",
                changes=len(changes),
                types=[c.change_type for c in changes],
            )

        return changes

    def get_recent_changes(self, limit: int = 10) -> List[ConfigChange]:
        """Ambil perubahan konfigurasi terbaru."""
        return self._changes[-limit:] if len(self._changes) > limit else list(self._changes)

    def get_summary(self) -> str:
        """Ringkasan drift."""
        if not self._changes:
            return "No configuration drift detected."
        recent = self._changes[-1]
        return "Configuration drift: {} ({})".format(recent.change_type, recent.path)

    def _capture_state(self) -> Dict[str, str]:
        """Capture state konfigurasi dari sumber yang tersedia."""
        state = {}

        # Environment variables (relevant subset)
        for key in ("PYTHONPATH", "PYTHONIOENCODING", "SAM_DEBUG", "SAM_CONFIG"):
            val = os.environ.get(key, "")
            state["env." + key] = val if val else "<not set>"

        # Config files
        for path in self._find_config_files():
            try:
                content = open(path, "r", encoding="utf-8", errors="ignore").read(5000)
                h = hashlib.md5(content.encode()).hexdigest()
                state["file." + path] = h
            except Exception:
                pass

        # Permission state dari workspace
        if self._wp:
            try:
                ws = self._wp.observe()
                state["workspace.writable"] = str(getattr(ws.workspace, 'writable', 'unknown'))
                state["workspace.disk_percent"] = str(getattr(ws.disk, 'percent', 'unknown'))
            except Exception:
                pass

        return state

    def _find_config_files(self) -> List[str]:
        """Cari file konfigurasi yang relevan."""
        candidates = []
        for root in [".", os.path.expanduser("~")]:
            for fname in (".env", ".sam.yml", "sam.json", "pyproject.toml", "setup.cfg"):
                path = os.path.join(root, fname)
                if os.path.isfile(path):
                    candidates.append(os.path.abspath(path))
        return candidates

    def _is_secret(self, key: str) -> bool:
        """Apakah key mengandung secret/token/password."""
        secrets = ("secret", "token", "password", "key", "credential", "auth")
        return any(s in key.lower() for s in secrets)
