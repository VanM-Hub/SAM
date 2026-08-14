"""Environment-adaptive: model entitas generik.

Entitas adalah representasi dari apa pun yang SAM temukan di environment
(process, port, service, file, mount, config, network). Entitas TIDAK
terikat pada jenis aplikasi tertentu - hanya pada fakta observasi.

Word/PDF/OpenClaw adalah FIKSIUR untuk menguji kemampuan ini, bukan
katalog yang SAM andalkan.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List


class EntityKind(str, Enum):
    """Jenis generik entitas (bukan nama aplikasi)."""

    PROCESS = "process"
    SERVICE = "service"
    PORT = "port"
    FILE = "file"
    VOLUME = "volume"
    CONFIG = "config"
    NETWORK = "network"
    ENV = "env"
    UNKNOWN = "unknown"


class EntitySource(str, Enum):
    """Dari mana entitas ditemukan (mekanisme discovery, bukan aplikasi)."""

    PROCESS_TABLE = "process_table"
    PORT_TABLE = "port_table"
    FILE_TABLE = "file_table"
    SERVICE_TABLE = "service_table"
    MOUNT_TABLE = "mount_table"
    ENV_TABLE = "env_table"
    CONFIG_SCAN = "config_scan"
    NETWORK_SCAN = "network_scan"
    PROVIDER = "provider"   # dari capability provider / probe terdaftar
    FIXTURE = "fixture"     # entitas buatan untuk pengujian (bukan produksi)


@dataclass
class Entity:
    """Satu entitas terobservasi di environment.

    id        : identitas stabil (hash fakta observasi, bukan nama aplikasi).
    kind      : jenis generik.
    source    : mekanisme discovery.
    label     : label kanonik (dari fakta, mis. nama proses/service).
    attributes: fakta terobservasi (deterministik, jujur).
    confidence: 0.0..1.0 seberapa yakin fakta ini (dari evidence).
    """

    id: str
    kind: EntityKind
    source: EntitySource
    label: str
    attributes: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0

    def as_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind.value,
            "source": self.source.value,
            "label": self.label,
            "attributes": self.attributes,
            "confidence": self.confidence,
        }


def stable_entity_id(kind: EntityKind, source: EntitySource, key: str) -> str:
    """Id stabil dari fakta observasi (deterministik, bukan nama aplikasi).

    key harus unik per (kind, source) - mis. pid, port num, path file.
    """
    import hashlib

    raw = f"{kind.value}|{source.value}|{key}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:20]


def entity_id(kind: EntityKind, source: EntitySource, key: str) -> str:
    return stable_entity_id(kind, source, key)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class DiscoveryScan:
    """Hasil satu pass discovery (auditable)."""

    entities: List[Entity] = field(default_factory=list)
    started_at: str = field(default_factory=_utc_now)
    finished_at: str = field(default_factory=_utc_now)
    attributes: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "entity_count": len(self.entities),
            "entities": [e.as_dict() for e in self.entities],
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "attributes": self.attributes,
        }
