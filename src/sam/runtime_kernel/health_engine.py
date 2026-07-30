"""Health Engine — agregasi + threshold."""
from __future__ import annotations
from typing import Dict, List
from sam.runtime_kernel.runtime_health import HealthCheck, HealthReport, HealthThreshold, AlertRecord


class HealthEngine:
    """Engine kesehatan — preview-only."""

    def __init__(self) -> None:
        self._thresholds: Dict[str, HealthThreshold] = {}
        self._alerts: List[AlertRecord] = []

    def add_threshold(self, threshold: HealthThreshold) -> None:
        self._thresholds[threshold.threshold_id] = threshold

    def get_threshold(self, threshold_id: str) -> HealthThreshold | None:
        return self._thresholds.get(threshold_id)

    def evaluate_metric(self, alert_id: str, metric: str, value: float) -> AlertRecord:
        threshold = self._thresholds.get(metric)
        if threshold and value >= threshold.critical:
            level = "critical"
        elif threshold and value >= threshold.warning:
            level = "warning"
        else:
            level = "info"
        alert = AlertRecord(alert_id=alert_id, metric=metric, value=value, level=level)
        self._alerts.append(alert)
        return alert

    def get_alerts(self) -> List[AlertRecord]:
        return list(self._alerts)

    def count_alerts(self) -> int:
        return len(self._alerts)

    def overall_health(self, report: HealthReport) -> str:
        return report.overall
