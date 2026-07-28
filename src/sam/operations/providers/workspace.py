"""
WorkspaceProvider — Observation Provider untuk data workspace.

Menyediakan informasi disk, workspace path, database, cache, temporary files.
TIDAK membuat keputusan — hanya mengamati.

Source data: shutil, os, pathlib (no external dependencies).
Platform: Windows (WSL-aware).

Alur:
  1. observe() → snapshot workspace + disk + db + cache + temp
  2. Snapshot → TelemetryService (via RuntimeProvider._poll)
  3. get_latest() → ConversationObject
"""

import os
import shutil
import structlog
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from pathlib import Path

logger = structlog.get_logger()


# ============================================================================
# Models
# ============================================================================

@dataclass
class DiskSnapshot:
    """Status disk dalam satu titik observasi."""
    total_gb: float
    used_gb: float
    free_gb: float
    percent: float
    path: str = ""
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "total_gb": round(self.total_gb, 1),
            "used_gb": round(self.used_gb, 1),
            "free_gb": round(self.free_gb, 1),
            "percent": round(self.percent, 1),
            "path": self.path,
            "timestamp": self.timestamp,
        }

    @property
    def near_full(self) -> bool:
        """Disk hampir penuh (>90%)."""
        return self.percent > 90.0

    @property
    def summary(self) -> str:
        if self.near_full:
            return "Storage critical: {:.1f}% used ({:.1f} GB / {:.1f} GB)".format(
                self.percent, self.used_gb, self.total_gb
            )
        return "Storage: {:.1f}% used ({:.1f} GB free)".format(self.percent, self.free_gb)


@dataclass
class WorkspaceSnapshot:
    """Status workspace path."""
    path: str = ""
    exists: bool = False
    writable: bool = False
    size_mb: float = 0.0
    file_count: int = 0
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "exists": self.exists,
            "writable": self.writable,
            "size_mb": round(self.size_mb, 1),
            "file_count": self.file_count,
            "timestamp": self.timestamp,
        }

    @property
    def healthy(self) -> bool:
        return self.exists and self.writable


@dataclass
class DatabaseSnapshot:
    """Status database connection (placeholder — dibaca dari environment)."""
    connected: bool = False
    unavailable: bool = False
    readonly: bool = False
    path: str = ""
    size_mb: float = 0.0
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "connected": self.connected,
            "unavailable": self.unavailable,
            "readonly": self.readonly,
            "path": self.path,
            "size_mb": round(self.size_mb, 1),
            "timestamp": self.timestamp,
        }

    @property
    def status(self) -> str:
        if self.unavailable:
            return "unavailable"
        if self.readonly:
            return "readonly"
        if self.connected:
            return "connected"
        return "unknown"


@dataclass
class CacheSnapshot:
    """Status cache directory."""
    path: str = ""
    size_mb: float = 0.0
    file_count: int = 0
    last_cleanup: str = ""
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "size_mb": round(self.size_mb, 1),
            "file_count": self.file_count,
            "last_cleanup": self.last_cleanup,
            "timestamp": self.timestamp,
        }


@dataclass
class TempFilesSnapshot:
    """Status temporary files."""
    count: int = 0
    size_mb: float = 0.0
    oldest_days: float = 0.0
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "count": self.count,
            "size_mb": round(self.size_mb, 1),
            "oldest_days": round(self.oldest_days, 1),
            "timestamp": self.timestamp,
        }


@dataclass
class WorkspaceSnapshotFull:
    """Snapshot lengkap workspace dalam satu observasi."""
    disk: DiskSnapshot
    workspace: WorkspaceSnapshot
    database: DatabaseSnapshot = field(default_factory=DatabaseSnapshot)
    cache: CacheSnapshot = field(default_factory=CacheSnapshot)
    temp: TempFilesSnapshot = field(default_factory=TempFilesSnapshot)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "disk": self.disk.to_dict(),
            "workspace": self.workspace.to_dict(),
            "database": self.database.to_dict(),
            "cache": self.cache.to_dict(),
            "temp": self.temp.to_dict(),
            "timestamp": self.timestamp,
        }

    def get_facts(self) -> list:
        """Facts untuk ConversationObject."""
        facts = []
        # Disk
        facts.append(self.disk.summary)
        # Workspace
        if self.workspace.healthy:
            if self.workspace.file_count > 0:
                facts.append("Workspace: {} files ({:.1f} MB)".format(
                    self.workspace.file_count, self.workspace.size_mb
                ))
        else:
            facts.append("Workspace path issue: {}".format(
                "missing" if not self.workspace.exists else "not writable"
            ))
        # Database
        if self.database.unavailable:
            facts.append("Database: unavailable")
        elif self.database.readonly:
            facts.append("Database: readonly")
        elif not self.database.connected:
            facts.append("Database: not connected")
        # Cache
        if self.cache.size_mb > 500:
            facts.append("Cache: {:.1f} MB ({}, consider cleanup)".format(
                self.cache.size_mb, self.cache.file_count
            ))
        elif self.cache.size_mb > 100:
            facts.append("Cache: {:.1f} MB".format(self.cache.size_mb))
        # Temp
        if self.temp.count > 100:
            facts.append("Temp files: {} ({:.1f} MB)".format(self.temp.count, self.temp.size_mb))
        return facts

    def get_recommendations(self) -> list:
        """Rekomendasi deterministik berdasarkan evidence."""
        recs = []
        if self.disk.near_full:
            recs.append("Free up storage: {:.1f}% used".format(self.disk.percent))
        if self.cache.size_mb > 500:
            recs.append("Cleanup cache ({:.1f} MB)".format(self.cache.size_mb))
        if self.temp.count > 200:
            recs.append("Remove temp files ({} files)".format(self.temp.count))
        if self.database.unavailable:
            recs.append("Reconnect database")
        if not self.workspace.writable:
            recs.append("Check workspace permissions: {}".format(self.workspace.path))
        return recs

    def get_predictions(self) -> list:
        """Prediksi deterministik berdasarkan evidence.

        Jika evidence tidak cukup, mengatakan 'Insufficient evidence.'
        """
        preds = []
        if self.disk.near_full and self.disk.used_gb > 100:
            preds.append("If storage continues to decrease, future operations may fail.")
        elif self.disk.percent > 95:
            preds.append("Storage is critically low. Write operations may fail soon.")
        elif self.disk.percent > 85:
            preds.append("Storage is trending toward capacity. Monitor closely.")
        else:
            preds.append("Insufficient evidence.")
        return preds

    @property
    def critical_issues(self) -> int:
        """Jumlah isu kritikal."""
        count = 0
        if self.disk.near_full:
            count += 1
        if self.database.unavailable:
            count += 1
        if not self.workspace.writable:
            count += 1
        return count

    @property
    def summary(self) -> str:
        issues = self.critical_issues
        if issues > 0:
            return "Workspace has {} critical issue(s). {}".format(issues, self.disk.summary)
        return "Workspace is operating normally."


# ============================================================================
# Provider
# ============================================================================

class WorkspaceProvider:
    """Observation Provider untuk data workspace.

    Mengamati:
      - Disk: total, used, free, percent (shutil.disk_usage)
      - Workspace: path, exists, writable, file count, size
      - Database: connection status (dari environment)
      - Cache: cache directory size
      - Temp files: temporary directory contents

    TIDAK membuat keputusan. TIDAK mengubah state.
    """

    def __init__(self, workspace_path: Optional[str] = None,
                 db_path: Optional[str] = None,
                 cache_path: Optional[str] = None):
        self._workspace_path = workspace_path or os.getcwd()
        self._db_path = db_path or ""
        self._cache_path = cache_path or ""
        self._latest: Optional[WorkspaceSnapshotFull] = None
        # Cache TTL: 30 detik — dalam satu burst conversation, tidak perlu scan ulang
        self._cache: Optional[WorkspaceSnapshotFull] = None
        self._cache_time: float = 0.0
        self._cache_ttl: float = 30.0

    def observe(self) -> WorkspaceSnapshotFull:
        """Observasi workspace — kumpulkan semua data dengan cache."""
        now = time.time()
        if self._cache and (now - self._cache_time) < self._cache_ttl:
            self._latest = self._cache
            return self._cache

        disk = self._observe_disk()
        workspace = self._observe_workspace()
        database = self._observe_database()
        cache = self._observe_cache()
        temp = self._observe_temp()

        snap = WorkspaceSnapshotFull(
            disk=disk,
            workspace=workspace,
            database=database,
            cache=cache,
            temp=temp,
        )
        self._latest = snap
        self._cache = snap
        self._cache_time = now
        return snap

    def get_latest(self) -> Optional[WorkspaceSnapshotFull]:
        """Snapshot observasi terakhir."""
        return self._latest

    # ====================================================================
    # Internal observers
    # ====================================================================

    def _observe_disk(self) -> DiskSnapshot:
        """Observasi disk usage."""
        try:
            path = self._workspace_path
            usage = shutil.disk_usage(path)
            total_gb = usage.total / (1024 ** 3)
            used_gb = usage.used / (1024 ** 3)
            free_gb = usage.free / (1024 ** 3)
            percent = (usage.used / usage.total) * 100 if usage.total > 0 else 0.0
            return DiskSnapshot(
                total_gb=total_gb,
                used_gb=used_gb,
                free_gb=free_gb,
                percent=percent,
                path=path,
            )
        except (OSError, FileNotFoundError, PermissionError) as e:
            logger.warning("workspace_provider.disk_error", error=str(e))
            return DiskSnapshot(
                total_gb=0, used_gb=0, free_gb=0, percent=0, path=self._workspace_path
            )

    def _observe_workspace(self, max_scan: int = 2000) -> WorkspaceSnapshot:
        """Observasi workspace path — scan cepat, max maks file."""
        try:
            p = Path(self._workspace_path)
            exists = p.exists()
            writable = os.access(str(p), os.W_OK) if exists else False

            # File count + size (limited scan — max max_scan files)
            count = 0
            total_size = 0
            if exists:
                for f in p.rglob("*"):
                    if count >= max_scan:
                        break
                    if f.is_file():
                        count += 1
                        try:
                            total_size += f.stat().st_size
                        except (OSError, PermissionError):
                            pass

            return WorkspaceSnapshot(
                path=self._workspace_path,
                exists=exists,
                writable=writable,
                size_mb=total_size / (1024 * 1024),
                file_count=count,
            )
        except (OSError, PermissionError) as e:
            logger.warning("workspace_provider.workspace_error", error=str(e))
            return WorkspaceSnapshot(path=self._workspace_path, exists=False)

    def _observe_database(self) -> DatabaseSnapshot:
        """Observasi database — berdasarkan path environment."""
        db_path = self._db_path
        if not db_path:
            # Cari dari env atau default
            for env_key in ["SAM_DB_PATH", "DATABASE_URL", "DB_PATH"]:
                val = os.environ.get(env_key)
                if val:
                    db_path = val
                    break

        if not db_path:
            return DatabaseSnapshot(connected=False, unavailable=True)

        try:
            p = Path(db_path)
            if not p.exists():
                return DatabaseSnapshot(path=db_path, unavailable=True, connected=False)

            # Cek writable
            writable = os.access(str(p), os.W_OK)
            size_mb = p.stat().st_size / (1024 * 1024)

            return DatabaseSnapshot(
                connected=True,
                readonly=not writable,
                path=db_path,
                size_mb=size_mb,
            )
        except (OSError, PermissionError) as e:
            logger.warning("workspace_provider.db_error", error=str(e))
            return DatabaseSnapshot(path=db_path, unavailable=True, connected=False)

    def _observe_cache(self, max_scan: int = 500) -> CacheSnapshot:
        """Observasi cache directory — cepat, shallow scan."""
        cache_path = self._cache_path or os.environ.get("SAM_CACHE_PATH", "")
        if not cache_path:
            # Default: __pycache__ atau cache/ di workspace
            candidates = [
                os.path.join(self._workspace_path, "__pycache__"),
                os.path.join(self._workspace_path, "cache"),
                os.path.join(self._workspace_path, ".cache"),
            ]
            for c in candidates:
                if os.path.isdir(c):
                    cache_path = c
                    break

        if not cache_path or not os.path.isdir(cache_path):
            return CacheSnapshot()

        try:
            count = 0
            total_size = 0
            last_mod = None
            p = Path(cache_path)
            for f in p.rglob("*"):
                if count >= max_scan:
                    break
                if f.is_file():
                    count += 1
                    try:
                        total_size += f.stat().st_size
                        mtime = f.stat().st_mtime
                        if last_mod is None or mtime > last_mod:
                            last_mod = mtime
                    except (OSError, PermissionError):
                        pass

            last_cleanup = ""
            if last_mod:
                last_cleanup = datetime.fromtimestamp(last_mod, tz=timezone.utc).isoformat()

            return CacheSnapshot(
                path=cache_path,
                size_mb=total_size / (1024 * 1024),
                file_count=count,
                last_cleanup=last_cleanup,
            )
        except (OSError, PermissionError) as e:
            logger.warning("workspace_provider.cache_error", error=str(e))
            return CacheSnapshot(path=cache_path)

    def _observe_temp(self, max_scan: int = 500) -> TempFilesSnapshot:
        """Observasi temporary files — shallow scan, fast."""
        temp_dir = os.environ.get("TEMP") or os.environ.get("TMP") or "/tmp"
        if not os.path.isdir(temp_dir):
            return TempFilesSnapshot()

        try:
            count = 0
            total_size = 0
            oldest_time = None
            now = time.time()
            p = Path(temp_dir)
            for f in p.iterdir():  # Langsung, tidak rekursif
                if count >= max_scan:
                    break
                if f.is_file():
                    count += 1
                    try:
                        total_size += f.stat().st_size
                        mtime = f.stat().st_mtime
                        if oldest_time is None or mtime < oldest_time:
                            oldest_time = mtime
                    except (OSError, PermissionError):
                        pass

            oldest_days = 0.0
            if oldest_time:
                oldest_days = (now - oldest_time) / 86400.0

            return TempFilesSnapshot(
                count=count,
                size_mb=total_size / (1024 * 1024),
                oldest_days=oldest_days,
            )
        except (OSError, PermissionError) as e:
            logger.warning("workspace_provider.temp_error", error=str(e))
            return TempFilesSnapshot()
