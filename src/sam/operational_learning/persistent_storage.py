"""Persistent Storage - WP-02 (MISSION-4.3 / IP-4.3-001).

Menyediakan mekanisme penyimpanan persisten yang tahan terhadap restart.

Data tetap tersedia setelah restart, persistence tervalidasi, data recovery
berhasil, dan storage dapat diaudit. Append-only & immutable (record tidak
diubah setelah ditulis); anti-tamper via hash SHA-256.
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple


def _now_utc() -> str:
    return datetime.utcnow().isoformat() + "Z"


@dataclass(frozen=True)
class StorageConfig:
    """Konfigurasi storage."""

    base_dir: str = ""
    collection: str = "experience"
    filename: str = "store.json"
    atomic_write: bool = True

    @property
    def store_path(self) -> Path:
        base = Path(self.base_dir) if self.base_dir else Path(tempfile.gettempdir())
        return base / f"{self.collection}_{self.filename}"


class SerializationLayer:
    """Konversi record <-> JSON (deterministik, sort_keys, UTF-8)."""

    @staticmethod
    def dumps(record: Dict[str, Any]) -> str:
        return json.dumps(
            record, ensure_ascii=False, sort_keys=True, indent=2
        )

    @staticmethod
    def loads(text: str) -> Dict[str, Any]:
        return json.loads(text)

    @staticmethod
    def canonical_hash(record: Dict[str, Any]) -> str:
        payload = SerializationLayer.dumps(record)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class StoredRecord:
    """Satu record yang tersimpan (immutable, hash-verified)."""

    record_id: str
    payload: Dict[str, Any]
    record_hash: str
    stored_at: str = ""

    def as_dict(self) -> dict:
        return {
            "record_id": self.record_id,
            "record_hash": self.record_hash,
            "stored_at": self.stored_at,
            "payload": self.payload,
        }

    def verify(self) -> bool:
        canonical = dict(self.payload)
        canonical.pop("_hash", None)
        return SerializationLayer.canonical_hash(canonical) == self.record_hash


class StorageHealth:
    """Verifikasi kesehatan storage."""

    @staticmethod
    def check(store_path: Path) -> Dict[str, Any]:
        if not store_path.exists():
            return {"ok": False, "reason": "missing", "size": 0}
        try:
            size = store_path.stat().st_size
            with open(store_path, "r", encoding="utf-8") as fh:
                json.load(fh)
            return {"ok": True, "size": size}
        except Exception as exc:
            return {"ok": False, "reason": str(exc), "size": 0}


class DataRecovery:
    """Pemulihan data dari file persisten."""

    @staticmethod
    def load_records(store_path: Path) -> Tuple[Dict[str, Any], ...]:
        if not store_path.exists():
            return ()
        try:
            with open(store_path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
        except Exception:
            return ()
        if isinstance(data, list):
            return tuple(
                item for item in data if isinstance(item, dict)
            )
        if isinstance(data, dict) and "records" in data:
            return tuple(
                item for item in data["records"] if isinstance(item, dict)
            )
        return ()


class PersistenceEngine:
    """Mesin penyimpanan persisten (append-only, atomic write)."""

    def __init__(self, config: StorageConfig) -> None:
        self.config = config
        self._records: Dict[str, StoredRecord] = {}
        self._recover()

    @property
    def store_path(self) -> Path:
        return self.config.store_path

    def _recover(self) -> None:
        records = DataRecovery.load_records(self.store_path)
        for raw in records:
            rid = raw.get("record_id") or raw.get("id") or ""
            if not rid:
                continue
            record_hash = raw.get("record_hash") or raw.get("_hash") or ""
            stored_at = raw.get("stored_at") or ""
            payload = {
                k: v
                for k, v in raw.items()
                if k not in ("record_hash", "_hash", "stored_at")
            }
            record = StoredRecord(rid, payload, record_hash, stored_at)
            if record.verify():
                self._records[rid] = record

    def append(
        self, record_id: str, payload: Dict[str, Any]
    ) -> StoredRecord:
        if record_id in self._records:
            raise ValueError(f"Record already exists: {record_id}")
        canonical = dict(payload)
        canonical["record_id"] = record_id
        record_hash = SerializationLayer.canonical_hash(canonical)
        record = StoredRecord(
            record_id=record_id,
            payload=canonical,
            record_hash=record_hash,
            stored_at=_now_utc(),
        )
        self._records[record_id] = record
        self._write()
        return record

    def get(self, record_id: str) -> Optional[StoredRecord]:
        return self._records.get(record_id)

    def all(self) -> Tuple[StoredRecord, ...]:
        return tuple(self._records.values())

    def count(self) -> int:
        return len(self._records)

    def _write(self) -> None:
        serialized = [
            {
                **r.payload,
                "record_hash": r.record_hash,
                "stored_at": r.stored_at,
            }
            for r in self._records.values()
        ]
        data = json.dumps(
            {"records": serialized},
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        )
        if self.config.atomic_write:
            # atomic write: tulis file temp lalu rename
            fd, tmp = tempfile.mkstemp(
                dir=str(self.store_path.parent), suffix=".tmp"
            )
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as fh:
                    fh.write(data)
                    fh.flush()
                    os.fsync(fh.fileno())
                os.replace(tmp, str(self.store_path))
            finally:
                if os.path.exists(tmp):
                    os.remove(tmp)
        else:
            self.store_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.store_path, "w", encoding="utf-8") as fh:
                fh.write(data)

    def audit_report(self) -> Dict[str, Any]:
        return {
            "store_path": str(self.store_path),
            "record_count": self.count(),
            "healthy": StorageHealth.check(self.store_path),
            "verified": all(r.verify() for r in self._records.values()),
        }
