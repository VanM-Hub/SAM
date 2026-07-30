"""Alert Engine — rule evaluation & alert generation."""
from __future__ import annotations
from typing import Dict, List, Optional, Tuple
from sam.execution.runtime.alerts import Alert, AlertRule, AlertHistory, AlertSummary


class AlertEngine:
    """Engine untuk evaluasi aturan dan generate alert."""

    def __init__(self) -> None:
        self._rules: Dict[str, AlertRule] = {}
        self._alerts: List[Alert] = []

    def register_rule(self, rule: AlertRule) -> None:
        self._rules[rule.rule_id] = rule

    def unregister_rule(self, rule_id: str) -> None:
        self._rules.pop(rule_id, None)

    def get_rules(self) -> Dict[str, AlertRule]:
        return dict(self._rules)

    def evaluate_value(self, metric_name: str, value: float,
                       timestamp: float) -> List[Alert]:
        """Evaluasi satu metric terhadap semua aturan yang cocok."""
        triggered: List[Alert] = []
        for rule in self._rules.values():
            if rule.metric != metric_name:
                continue
            triggered_val = False
            if rule.operator == "gt":
                triggered_val = value > rule.threshold
            elif rule.operator == "gte":
                triggered_val = value >= rule.threshold
            elif rule.operator == "lt":
                triggered_val = value < rule.threshold
            elif rule.operator == "lte":
                triggered_val = value <= rule.threshold
            elif rule.operator == "eq":
                triggered_val = abs(value - rule.threshold) < 0.001
            if triggered_val:
                alert = Alert(
                    alert_id=f"alert_{len(self._alerts)}_{len(triggered)}",
                    timestamp=timestamp,
                    severity=rule.severity,
                    message=f"{rule.name}: {value} {rule.operator} {rule.threshold}",
                    source="execution_runtime",
                )
                triggered.append(alert)
                self._alerts.append(alert)
        return triggered

    def get_history(self) -> AlertHistory:
        """Ambil riwayat alert."""
        alerts = tuple(self._alerts)
        return AlertHistory(
            alerts=alerts,
            total_alerts=len(alerts),
            latest_timestamp=alerts[-1].timestamp if alerts else 0.0,
        )

    def acknowledge(self, alert_id: str) -> None:
        """Tandai alert sebagai acknowledged."""
        self._alerts = [
            Alert(
                alert_id=a.alert_id,
                timestamp=a.timestamp,
                severity=a.severity,
                message=a.message,
                source=a.source,
                candidate_id=a.candidate_id,
                acknowledged=(True if a.alert_id == alert_id else a.acknowledged),
            )
            for a in self._alerts
        ]

    def get_summary(self) -> AlertSummary:
        """Buat ringkasan alert."""
        crit = sum(1 for a in self._alerts if a.severity == "critical")
        warn = sum(1 for a in self._alerts if a.severity == "warning")
        info = sum(1 for a in self._alerts if a.severity == "info")
        ack = sum(1 for a in self._alerts if a.acknowledged)

        if crit > 0:
            status = "critical"
        elif warn > 0:
            status = "warning"
        else:
            status = "clear"

        return AlertSummary(
            total_alerts=len(self._alerts),
            critical_count=crit,
            warning_count=warn,
            info_count=info,
            acknowledged_count=ack,
            status=status,
        )
