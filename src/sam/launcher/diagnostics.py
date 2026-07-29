"""
OP-366 — Diagnostics
=====================

Read-only diagnostics for the runtime environment.
Captures snapshots of subsystem availability and health.
"""

import os
import sys
import time
import sqlite3
from typing import Any, Dict, List, Optional


class DiagnosticsSummary:
    """Summary of a diagnostics snapshot."""

    __slots__ = ("total_checks", "passed", "failed", "elapsed")

    def __init__(
        self,
        total_checks: int = 0,
        passed: int = 0,
        failed: int = 0,
        elapsed: float = 0.0,
    ) -> None:
        self.total_checks = total_checks
        self.passed = passed
        self.failed = failed
        self.elapsed = elapsed

    @property
    def success(self) -> bool:
        return self.failed == 0

    def __repr__(self) -> str:
        return (
            f"<DiagSummary {self.passed}/{self.total_checks} pass "
            f"fail={self.failed} in {self.elapsed:.2f}s>"
        )


class DiagnosticsSnapshot:
    """A point-in-time diagnostics capture. Immutable."""

    __slots__ = ("timestamp", "checks", "summary")

    def __init__(
        self,
        timestamp: float,
        checks: Dict[str, str],
        summary: DiagnosticsSummary,
    ) -> None:
        self.timestamp = timestamp
        self.checks = checks
        self.summary = summary

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "checks": dict(self.checks),
            "summary": {
                "total": self.summary.total_checks,
                "passed": self.summary.passed,
                "failed": self.summary.failed,
                "elapsed": self.summary.elapsed,
            },
        }

    def __repr__(self) -> str:
        return f"<Snapshot checks={len(self.checks)} at {self.timestamp:.0f}>"


class DiagnosticsEngine:
    """Read-only diagnostics engine.

    Does NOT modify any subsystem.
    """

    def __init__(self, workspace: str = "") -> None:
        self._workspace = workspace or os.getcwd()

    def snapshot(self) -> DiagnosticsSnapshot:
        """Capture a point-in-time diagnostics snapshot."""
        start = time.time()
        checks: Dict[str, str] = {}
        passed = 0
        failed = 0

        for method_name in sorted(dir(self)):
            if method_name.startswith("_check_"):
                key = method_name.replace("_check_", "").replace("_", " ").title()
                try:
                    result = getattr(self, method_name)()
                    checks[key] = result
                    if result.startswith("OK"):
                        passed += 1
                    else:
                        failed += 1
                except Exception as exc:
                    checks[key] = f"ERROR: {exc}"
                    failed += 1

        elapsed = time.time() - start
        summary = DiagnosticsSummary(
            total_checks=len(checks),
            passed=passed,
            failed=failed,
            elapsed=elapsed,
        )
        return DiagnosticsSnapshot(time.time(), checks, summary)

    # ── checks ─────────────────────────────────

    def _check_guardian_status(self) -> str:
        try:
            import importlib
            importlib.import_module("sam.guardian.engine")
            return "OK (module available)"
        except ImportError:
            return "UNAVAILABLE (module not found)"

    def _check_conversation(self) -> str:
        try:
            import importlib
            importlib.import_module("sam.operations.conversation")
            return "OK (module available)"
        except ImportError:
            return "UNAVAILABLE (module not found)"

    def _check_desktop_availability(self) -> str:
        try:
            import PySide6  # noqa: F401
            return "OK (PySide6 available)"
        except ImportError:
            return "UNAVAILABLE (PySide6 not installed)"

    def _check_console_availability(self) -> str:
        try:
            import rich  # noqa: F401
            return "OK (Rich available)"
        except ImportError:
            return "DEGRADED (Rich not installed)"

    def _check_provider_availability(self) -> str:
        providers_path = os.path.join(self._workspace, "providers.json")
        if os.path.isfile(providers_path):
            return "OK (provider file found)"
        try:
            import importlib
            importlib.import_module("sam.operations.providers.runtime")
            return "OK (provider module available)"
        except ImportError:
            return "UNAVAILABLE (no provider config)"

    def _check_database(self) -> str:
        db = os.path.join(self._workspace, "data", "sam.db")
        if os.path.isfile(db):
            try:
                conn = sqlite3.connect(db)
                conn.execute("SELECT 1")
                conn.close()
                return "OK (database reachable)"
            except Exception as exc:
                return f"ERROR: {exc}"
        return "NOT_FOUND (first run or missing)"

    def _check_workspace(self) -> str:
        ws = self._workspace
        if os.path.isdir(ws):
            return "OK"
        return "NOT_FOUND"

    def _check_performance_baseline(self) -> str:
        import time as t
        start = t.time()
        _ = [x * x for x in range(10000)]
        elapsed = t.time() - start
        return f"OK ({elapsed*1000:.1f}ms for 10K iterations)"
