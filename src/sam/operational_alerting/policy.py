"""
Operational Alerting — Policy evaluation.

Menutup gap D4-G1 (High): keputusan apakah sebuah kondisi kritis harus
mengangkat alert, dan ke kanal mana alert di-route, ditentukan OLEH kebijakan
yang eksplisit & stand-alone.

Policy evaluator bekerja pada data (AlertRecord) dan kebijakan (AlertPolicy),
murni deterministik, TANPA efek eksternal. Hasil evaluasi = kumpulan
AlertRoutingDecision yang siap dikonsumsi AlertRouter.

Konsisten EA-002: stand-alone capability; TIDAK mengubah runtime existing.
Tidak melakukan efek eksternal (network/host).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .state import (
    AlertChannel,
    AlertPolicy,
    AlertRecord,
    AlertSeverity,
)


@dataclass(frozen=True)
class AlertRoutingDecision:
    """Keputusan routing hasil evaluasi policy untuk satu alert.

    - record: alert terkait.
    - target_channels: kanal tujuan (label; tidak ada pengiriman nyata).
    - routed: apakah alert memenuhi min_severity policy (layak route).
    - reason: alasan keputusan (untuk audit/observability).
    """

    record: AlertRecord
    target_channels: List[str] = field(default_factory=list)
    routed: bool = False
    reason: str = ""

    def as_dict(self) -> Dict[str, Any]:
        return {
            "alert_id": self.record.alert_id,
            "severity": self.record.severity.value,
            "source": self.record.source,
            "target_channels": self.target_channels,
            "routed": self.routed,
            "reason": self.reason,
        }


class AlertPolicyEvaluator:
    """Mengevaluasi satu alert terhadap satu kebijakan.

    Aturan:
    - Policy dinonaktifkan (enabled=False) -> alert di-drop (tidak di-route).
    - Severity alert < policy.min_severity -> alert di-drop (below threshold).
    - Severity memenuhi threshold -> route ke kanal sesuai severity mapping;
      jika kanal untuk severity kosong, pakai default ke [OPERATOR].
    """

    def __init__(self, policy: AlertPolicy) -> None:
        self._policy = policy

    @property
    def policy(self) -> AlertPolicy:
        return self._policy

    def evaluate(self, record: AlertRecord) -> AlertRoutingDecision:
        if not self._policy.enabled:
            return AlertRoutingDecision(
                record=record,
                routed=False,
                reason=f"policy {self._policy.policy_id} disabled",
            )
        if record.severity.rank < self._policy.min_severity.rank:
            return AlertRoutingDecision(
                record=record,
                routed=False,
                reason=(
                    f"severity {record.severity.value} below "
                    f"min {self._policy.min_severity.value}"
                ),
            )
        channels = self._channels_for(record.severity)
        return AlertRoutingDecision(
            record=record,
            target_channels=channels,
            routed=True,
            reason="threshold met",
        )

    def _channels_for(self, severity: AlertSeverity) -> List[str]:
        mapping = self._policy.channels
        if not mapping:
            return [AlertChannel.OPERATOR.value]
        raw = mapping.get("info", [])
        # gunakan kanal yang paling spesifik untuk severity & selalu
        # sertakan operator untuk error/critical
        candidates = []
        for sev in (AlertSeverity.INFO, AlertSeverity.WARNING,
                    AlertSeverity.ERROR, AlertSeverity.CRITICAL):
            got = mapping.get(sev.value, [])
            if isinstance(got, list):
                candidates.extend(got)
            if sev == severity:
                break
        if severity.rank >= AlertSeverity.ERROR.rank:
            for ch in (AlertChannel.OPERATOR.value, AlertChannel.NOTIFICATION_CENTER.value):
                if ch not in candidates:
                    candidates.append(ch)
        # dedup & jaga urutan
        seen = set()
        ordered = []
        for ch in candidates:
            if ch not in seen and AlertChannel.has_value(ch):
                seen.add(ch)
                ordered.append(ch)
        return ordered or [AlertChannel.OPERATOR.value]


def build_routing(
    record: AlertRecord,
    policy: AlertPolicy,
) -> AlertRoutingDecision:
    """Convenience: evaluasi satu alert terhadap satu policy."""
    return AlertPolicyEvaluator(policy).evaluate(record)
