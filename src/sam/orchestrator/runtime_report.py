# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 132 - Runtime Engine: runtime_report.

Report of the orchestration runtime engine. Pure DTO, immutable.
"""
from __future__ import annotations

from dataclasses import dataclass

from .runtime_status import RuntimeStatus
from .runtime_snapshot import RuntimeSnapshot


@dataclass(frozen=True)
class RuntimeReport:
    """Immutable report of engine readiness."""

    status: RuntimeStatus
    snapshot: RuntimeSnapshot
    engine_ready: bool = True

    @property
    def ok(self) -> bool:
        return self.engine_ready and self.status.is_ready and self.snapshot.ready
