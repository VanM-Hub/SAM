"""
Operational Alerting — DTO (state).

DTO immutable (ADR-023) untuk model operational alerting dalam mekanisme
alerting/notification AKTIF (gap D4-G1, High): platform mengobservasi kondisi
kritis (Observation layer) tetapi TIDAK memberi tahu operator dengan alert
teragregasi & ter-route.

Modul ini mendefinisikan bentuk data dasar:
- AlertSeverity: tingkat keparahan alert.
- AlertStatus: lifecycle state sebuah alert (open/acknowledged/resolved).
- AlertChannel: kanal tujuan (placeholder; tidak melakukan efek eksternal).
- AlertRecord: satu alert operational (immutable payload + status mutable).
- AlertPriority: nilai prioritas deterministik turunan dari severity.

Menutup H4/Program D. Stand-alone capability — TIDAK mengubah runtime existing
(constraint EA-002). Tidak melakukan efek eksternal (network/host).
"""
from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


def _canonical_json(value: Any) -> str:
    """Representasi JSON kanonik (terurut, ASCII) untuk checksum deterministik."""
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":"))


def _utcnow_iso() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()


class AlertSeverity(str, Enum):
    """Tingkat keparahan alert operational (urutan naik = kritis)."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

    @property
    def rank(self) -> int:
        return {"info": 0, "warning": 1, "error": 2, "critical": 3}[self.value]


class AlertStatus(str, Enum):
    """Lifecycle state sebuah alert di sink operator."""

    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


class AlertChannel(str, Enum):
    """Kanal tujuan alert (target operator).

    Placeholder/dispatch-only — TIDAK melakukan efek eksternal (tidak
    mengirim email/SMS/HTTP). Kanal adalah label target; pengiriman nyata
    adalah tanggung jawab operator/sink eksternal di luar capability ini.
    """

    CONSOLE = "console"
    LOG = "log"
    OPERATOR = "operator"
    NOTIFICATION_CENTER = "notification_center"

    @classmethod
    def has_value(cls, value: str) -> bool:
        return value in cls._value2member_map_


@dataclass(frozen=True)
class AlertRecord:
    """Satu alert operational (payload immutable).

    - alert_id: unik (uuid).
    - title/message: deskripsi kondisi kritis.
    - severity: keparahan.
    - source: identitas subsystem/objek sumber kondisi.
    - source_kind: kategori sumber ("platform_health"|"audit"|"learning"|...).
    - occurred_at: ISO timestamp saat kondisi terdeteksi.
    - fingerprint: checksum kanonik (untuk dedup).
    - metadata: konteks tambahan (tidak menyimpan rahasia).

    Status lifecycle (status/acknowledged_by/acknowledged_at/resolved_at)
    TIDAK bagian DTO immutable ini; dipegang AlertStore.
    """

    alert_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    message: str = ""
    severity: AlertSeverity = AlertSeverity.WARNING
    source: str = ""
    source_kind: str = ""
    occurred_at: str = field(default_factory=_utcnow_iso)
    fingerprint: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if isinstance(self.severity, str):
            object.__setattr__(self, "severity", AlertSeverity(self.severity))
        if not self.fingerprint:
            object.__setattr__(
                self,
                "fingerprint",
                hashlib.sha256(
                    _canonical_json(
                        {
                            "title": self.title,
                            "severity": self.severity.value,
                            "source": self.source,
                            "source_kind": self.source_kind,
                        }
                    ).encode("utf-8")
                ).hexdigest(),
            )

    def as_dict(self) -> Dict[str, Any]:
        return {
            "alert_id": self.alert_id,
            "title": self.title,
            "message": self.message,
            "severity": self.severity.value,
            "source": self.source,
            "source_kind": self.source_kind,
            "occurred_at": self.occurred_at,
            "fingerprint": self.fingerprint,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class AlertPolicy:
    """Kebijakan alert: aturan naik/turun & kanal tujuan.

    Stand-alone policy data — tidak mengeksekusi efek eksternal.

    - policy_id: unik.
    - min_severity: alert di bawah ini diabaikan (tidak diroute).
    - channels: kanal tujuan sesuai severity (default mapping).
    - enabled: apakah policy aktif.
    - description: keterangan ringkas.
    """

    policy_id: str
    min_severity: AlertSeverity = AlertSeverity.WARNING
    channels: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    description: str = ""

    def __post_init__(self) -> None:
        if isinstance(self.min_severity, str):
            object.__setattr__(self, "min_severity", AlertSeverity(self.min_severity))
        if not self.channels:
            # default: semua severity > min diroute ke OPERATOR
            object.__setattr__(
                self,
                "channels",
                {
                    "info": [AlertChannel.LOG.value],
                    "warning": [AlertChannel.CONSOLE.value, AlertChannel.LOG.value],
                    "error": [AlertChannel.CONSOLE.value, AlertChannel.OPERATOR.value],
                    "critical": [AlertChannel.OPERATOR.value, AlertChannel.NOTIFICATION_CENTER.value],
                },
            )

    def as_dict(self) -> Dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "min_severity": self.min_severity.value,
            "channels": self.channels,
            "enabled": self.enabled,
            "description": self.description,
        }


def default_policy(policy_id: str = "default") -> AlertPolicy:
    """Policy default: route alert severity >= warning ke operator."""
    return AlertPolicy(policy_id=policy_id)
