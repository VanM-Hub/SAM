"""ServiceMonitor (Sprint 269).

Program D - Runtime Services & Deployment.
Monitor service: mencatat metrics & health check.
"""
from __future__ import annotations
from typing import Dict, Optional

from .metrics import RuntimeMetrics


class ServiceMonitor:
    """Monitor service (sync, deterministic)."""

    def __init__(self, name: str = "runtime-monitor") -> None:
        self._name = name
        self._metrics: Dict[str, RuntimeMetrics] = {}
        self._events: list = []

    @property
    def name(self) -> str:
        return self._name

    def record(self, service: str, key: str, value: int = 1) -> None:
        if service not in self._metrics:
            self._metrics[service] = RuntimeMetrics(name=service)
        current = self._metrics[service].get(key, 0)
        counters = dict(self._metrics[service].counters)
        counters[key] = current + value
        self._metrics[service] = RuntimeMetrics(name=service, counters=counters)

    def log(self, level: str, message: str) -> None:
        self._events.append({"level": level, "message": message})

    def get_metrics(self, service: str) -> Optional[RuntimeMetrics]:
        return self._metrics.get(service)

    def services(self) -> list:
        return sorted(self._metrics.keys())

    def events(self) -> list:
        return list(self._events)
