"""
Operational Alerting — Dispatcher (orchestrator).

Menutup gap D4-G1 (High): jalur masuk tunggal untuk mengubah kondisi kritis
yang terdeteksi (Observation layer / telemetry / health) menjadi alert
ter-agregasi yang di-route ke operator.

Alur: AlertRecord -> AlertPolicyEvaluator -> AlertRouter (dedup+store)
       -> AlertAuditLog (metadata).

Murni in-process & stand-alone; TIDAK mengubah runtime existing. Tidak
melakukan efek eksternal (network/host) — kanal adalah label, pengiriman nyata
oleh sink eksternal.

Konsisten EA-002: capability baru, tidak menyentuh execution_runtime,
runtime_kernel, atau operations notification store yang existing.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .audit import AlertAuditLog
from .policy import AlertPolicyEvaluator, AlertRoutingDecision
from .router import AlertRouter, AlertStore
from .state import (
    AlertPolicy,
    AlertRecord,
    AlertSeverity,
    default_policy,
)


class AlertDispatcher:
    """Orkestrasi alert: record -> policy -> route -> audit.

    - emit(): terima satu AlertRecord, evaluasi terhadap policy aktif,
      route ke router, catat audit. Kembalikan AlertRoutingDecision.
    - trigger(): convenience untuk membungkus kondisi mentah (title, severity,
      source) menjadi AlertRecord lalu emit.
    - Helper status: open_alerts()/critical_open()/count().
    """

    def __init__(
        self,
        policy: Optional[AlertPolicy] = None,
        router: Optional[AlertRouter] = None,
        audit: Optional[AlertAuditLog] = None,
    ) -> None:
        self._policy = policy or default_policy()
        self._router = router or AlertRouter()
        self._audit = audit or AlertAuditLog()
        self._evaluator = AlertPolicyEvaluator(self._policy)

    @property
    def policy(self) -> AlertPolicy:
        return self._policy

    @property
    def router(self) -> AlertRouter:
        return self._router

    @property
    def audit(self) -> AlertAuditLog:
        return self._audit

    def set_policy(self, policy: AlertPolicy) -> None:
        self._policy = policy
        self._evaluator = AlertPolicyEvaluator(policy)

    def emit(self, record: AlertRecord) -> AlertRoutingDecision:
        decision = self._evaluator.evaluate(record)
        if decision.routed:
            dispatched = self._router.route(decision)
            outcome = "deduped" if not dispatched else "success"
            self._audit.record(
                event="route",
                alert_id=record.alert_id,
                severity=record.severity,
                source=record.source,
                outcome=outcome,
            )
        else:
            self._audit.record(
                event="route",
                alert_id=record.alert_id,
                severity=record.severity,
                source=record.source,
                outcome="rejected",
            )
        return decision

    def trigger(
        self,
        title: str,
        severity: AlertSeverity,
        source: str,
        source_kind: str = "operational",
        message: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AlertRoutingDecision:
        record = AlertRecord(
            title=title,
            message=message,
            severity=severity,
            source=source,
            source_kind=source_kind,
            metadata=metadata or {},
        )
        return self.emit(record)

    def acknowledge(self, alert_id: str, by: str = "operator") -> bool:
        ok = self._router.acknowledge(alert_id, by=by)
        a = self._router.store.by_id(alert_id)
        self._audit.record(
            event="acknowledge",
            alert_id=alert_id,
            severity=a.record.severity if a else AlertSeverity.INFO,
            source=a.record.source if a else "",
            outcome="success" if ok else "rejected",
            operator=by,
        )
        return ok

    def resolve(self, alert_id: str) -> bool:
        ok = self._router.resolve(alert_id)
        a = self._router.store.by_id(alert_id)
        self._audit.record(
            event="resolve",
            alert_id=alert_id,
            severity=a.record.severity if a else AlertSeverity.INFO,
            source=a.record.source if a else "",
            outcome="success" if ok else "rejected",
        )
        return ok

    # ---- status convenience ----
    def open_alerts(self) -> int:
        return self._router.store.open_count()

    def critical_open(self) -> int:
        return self._router.store.critical_open()

    def dispatched(self) -> int:
        return self._router.dispatched_count

    def deduped(self) -> int:
        return self._router.deduped_count
