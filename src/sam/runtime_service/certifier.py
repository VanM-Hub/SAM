"""RuntimeCertifier (Sprint 270).

Program D - Runtime Services & Deployment.
Sertifikasi 7 dimensi: Configuration, Security, Lifecycle, Plugin,
Determinism, Immutability, ProductionReadiness.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class DimensionResult:
    """Hasil dimensi (immutable)."""
    dimension: str
    passed: bool
    detail: str = ""


class RuntimeCertifier:
    """Certifier runtime 7 dimensi (sync, deterministic)."""

    DIMENSIONS = (
        "Configuration",
        "Security",
        "Lifecycle",
        "Plugin",
        "Determinism",
        "Immutability",
        "ProductionReadiness",
    )

    def __init__(self) -> None:
        self._checks: Dict[str, bool] = {
            d: False for d in self.DIMENSIONS
        }
        self._detail: Dict[str, str] = {}

    def check(self, dimension: str, passed: bool,
              detail: str = "") -> None:
        if dimension not in self._checks:
            raise ValueError(f"unknown dimension: {dimension}")
        self._checks[dimension] = passed
        self._detail[dimension] = detail

    def results(self) -> List[DimensionResult]:
        return [
            DimensionResult(dimension=d, passed=self._checks[d],
                            detail=self._detail.get(d, ""))
            for d in self.DIMENSIONS
        ]

    def passed(self) -> int:
        return sum(1 for v in self._checks.values() if v)

    def is_certified(self) -> bool:
        return all(self._checks.values())

    def summary(self) -> dict:
        return {
            "dimensions": list(self.DIMENSIONS),
            "passed": self.passed(),
            "total": len(self.DIMENSIONS),
            "certified": self.is_certified(),
        }
