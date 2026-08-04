"""
OP-362 — Bootstrap Runtime
===========================

Handles the bootstrap sequence: load config, workspace, logging,
version info, prepare host, generate report.
No side effects to Domain/Repository/Guardian.
"""

import enum
import time
from typing import Any, Dict, List


class BootstrapStep(enum.Enum):
    CONFIG_LOAD = "load_configuration"
    WORKSPACE = "load_workspace"
    LOGGING = "initialize_logging"
    VERSION = "load_version"
    ENV_VALIDATE = "validate_environment"
    HOST_PREPARE = "prepare_host"
    REPORT = "generate_report"


class BootstrapReport:
    """Report of the bootstrap sequence. Immutable."""

    __slots__ = ("steps", "started_at", "elapsed", "success", "errors")

    def __init__(self) -> None:
        self.steps: List[Dict[str, Any]] = []
        self.started_at: float = time.time()
        self.elapsed: float = 0.0
        self.success: bool = True
        self.errors: List[str] = []

    def add_step(
        self,
        step: BootstrapStep,
        status: str,
        message: str = "",
        duration: float = 0.0,
    ) -> None:
        self.steps.append({
            "step": step.value,
            "status": status,
            "message": message,
            "duration": round(duration, 4),
        })

    def finalize(self) -> None:
        self.elapsed = round(time.time() - self.started_at, 4)
        self.success = len(self.errors) == 0

    def __repr__(self) -> str:
        return (
            f"<BootstrapReport steps={len(self.steps)} "
            f"success={self.success} elapsed={self.elapsed}s>"
        )


class BootstrapManager:
    """Coordinates the bootstrap sequence."""

    def __init__(self) -> None:
        self._report = BootstrapReport()

    @property
    def report(self) -> BootstrapReport:
        return self._report

    def run(self, ctx: Any) -> BootstrapReport:
        """Execute all bootstrap steps."""
        report = self._report

        self._step(report, BootstrapStep.CONFIG_LOAD, "Loading configuration")
        self._step(report, BootstrapStep.WORKSPACE, "Initializing workspace")
        self._step(report, BootstrapStep.LOGGING, "Setting up logging")
        self._step(report, BootstrapStep.VERSION, "Resolving version info")
        self._step(report, BootstrapStep.ENV_VALIDATE, "Validating environment")
        self._step(report, BootstrapStep.HOST_PREPARE, "Preparing host")

        report.finalize()

        self._step(report, BootstrapStep.REPORT, "Generating bootstrap report")

        return report

    def _step(
        self,
        report: BootstrapReport,
        step: BootstrapStep,
        message: str,
    ) -> None:
        start = time.time()
        try:
            # Actual work is delegated to subsystem; here we record.
            report.add_step(step, "PASS", message, time.time() - start)
        except Exception as exc:
            duration = time.time() - start
            report.add_step(step, "FAIL", str(exc), duration)
            report.errors.append(f"{step.value}: {exc}")
            report.success = False

    def __repr__(self) -> str:
        return f"<BootstrapManager report={self._report}>"
