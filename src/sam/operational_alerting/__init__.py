"""
Operational Alerting (H4/Program D — gap D4-G1).

Mekanisme alerting/notification AKTIF untuk kondisi kritis operational:
platform tahu kondisi buruk (Observation layer) tetapi tidak memberi tahu
operator. Modul ini menyediakan alert ter-agregasi lintas subsystem dengan:

- AlertPolicy: kebijakan naik/turun & kanal tujuan (severity threshold).
- AlertRecord: satu alert immutable (payload, tanpa rahasia).
- AlertDispatcher: orkestrasi record -> policy -> router -> audit.
- AlertRouter: routing ke store dengan dedup fingerprint + status lifecycle.
- AlertStore: retensi ring buffer + acknowledge/resolve.
- AlertAuditLog: jejak metadata (tanpa payload).

Stand-alone capability — TIDAK mengubah runtime existing (constraint EA-002).
Tidak melakukan efek eksternal (network/host). Konsumen dapat memakainya
tanpa mengubah lapisan existing.
"""
from .audit import AlertAuditLog, AlertAuditRecord
from .dispatcher import AlertDispatcher
from .policy import AlertPolicyEvaluator, AlertRoutingDecision, build_routing
from .router import AlertRouter, AlertStore
from .state import (
    AlertChannel,
    AlertPolicy,
    AlertRecord,
    AlertSeverity,
    AlertStatus,
    default_policy,
)

__all__ = [
    "AlertAuditLog",
    "AlertAuditRecord",
    "AlertChannel",
    "AlertDispatcher",
    "AlertPolicy",
    "AlertPolicyEvaluator",
    "AlertRecord",
    "AlertRouter",
    "AlertRoutingDecision",
    "AlertSeverity",
    "AlertStatus",
    "AlertStore",
    "build_routing",
    "default_policy",
]
