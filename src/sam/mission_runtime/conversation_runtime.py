# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 142 - Mission Runtime: conversation_runtime.

Read-only conversation bridge for the mission runtime.
"""
from __future__ import annotations

from typing import Dict

from .mission_runtime import MissionRuntime
from .mission_reporter import MissionReporter
from .mission_snapshot import MissionSnapshot


class ConversationRuntimeBridge:
    """Read-only bridge exposing mission runtime readiness."""

    def __init__(self, runtime: MissionRuntime) -> None:
        self._runtime = runtime

    def report(self) -> MissionReporter:
        return self._runtime.report()

    def snapshot(self) -> MissionSnapshot:
        return self._runtime.snapshot()

    def summary(self) -> Dict[str, object]:
        report = self._runtime.report()
        return {
            "ready": report.ok,
            "stages": report.snapshot.pipeline.stage_count,
            "runtime": self._runtime.RUNTIME_VERSION,
        }
