"""Execution Report (Sprint 254).

Program C - Real Execution Runtime.
Laporan immutable hasil eksekusi (per stage pipeline). Read-only.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class StageTrace:
    """Jejak satu stage pipeline (immutable)."""
    stage: str
    status: str
    external_calls: int = 0
    detail: str = ""

    def as_dict(self) -> dict:
        return {"stage": self.stage, "status": self.status,
                "external_calls": self.external_calls, "detail": self.detail}


@dataclass(frozen=True)
class ExecutionReport:
    """Laporan eksekusi (immutable)."""
    report_id: str
    execution_id: str
    stages: tuple = field(default_factory=tuple)
    status: str = "pending"
    external_calls: int = 0

    def stage(self, name: str) -> StageTrace | None:
        for s in self.stages:
            if s.stage == name:
                return s
        return None

    def all_ok(self) -> bool:
        return all(s.status == "ok" for s in self.stages)

    def as_dict(self) -> dict:
        return {
            "report_id": self.report_id,
            "execution_id": self.execution_id,
            "stages": [s.as_dict() for s in self.stages],
            "status": self.status,
            "external_calls": self.external_calls,
        }
