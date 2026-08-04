"""
OP-363 — Environment Validator
===============================

Checks Python, SQLite, workspace, permissions, dependencies,
configuration files, database, temp/log folders, provider config,
plugin folder.

Output: EnvironmentReport with PASS/WARNING/FAIL per item.
"""

import os
import sys
import enum
import time
import sqlite3
from typing import Dict, List


class EnvStatus(enum.Enum):
    PASS = "PASS"
    WARNING = "WARNING"
    FAIL = "FAIL"


class EnvironmentItem:
    """A single environment check result. Immutable."""

    __slots__ = ("name", "status", "message", "detail")

    def __init__(
        self,
        name: str,
        status: EnvStatus,
        message: str = "",
        detail: str = "",
    ) -> None:
        self.name = name
        self.status = status
        self.message = message
        self.detail = detail

    def __repr__(self) -> str:
        return f"<EnvItem {self.name}={self.status.value}>"

    def to_dict(self) -> Dict[str, str]:
        return {
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
        }


class EnvironmentReport:
    """Report of environment validation. Immutable after generation."""

    __slots__ = ("items", "passed", "warnings", "failed", "timestamp")

    def __init__(self) -> None:
        self.items: List[EnvironmentItem] = []
        self.passed: int = 0
        self.warnings: int = 0
        self.failed: int = 0
        self.timestamp: float = time.time()

    def add(self, item: EnvironmentItem) -> None:
        self.items.append(item)
        if item.status == EnvStatus.PASS:
            self.passed += 1
        elif item.status == EnvStatus.WARNING:
            self.warnings += 1
        else:
            self.failed += 1

    @property
    def success(self) -> bool:
        return self.failed == 0

    def __repr__(self) -> str:
        return (
            f"<EnvReport pass={self.passed} warn={self.warnings} "
            f"fail={self.failed}>"
        )


class EnvironmentValidator:
    """Validates the runtime environment.

    Read-only — does NOT modify anything.
    """

    def __init__(self, workspace: str = "") -> None:
        self._workspace = workspace or os.getcwd()

    def validate(self) -> EnvironmentReport:
        """Run all environment checks."""
        report = EnvironmentReport()

        self._check_python(report)
        self._check_sqlite(report)
        self._check_workspace(report)
        self._check_permissions(report)
        self._check_pyside6(report)
        self._check_rich(report)
        self._check_config(report)
        self._check_database(report)
        self._check_temp_folder(report)
        self._check_log_folder(report)
        self._check_provider_config(report)
        self._check_plugin_folder(report)

        return report

    # ── individual checks ──────────────────────

    def _check_python(self, report: EnvironmentReport) -> None:
        ver = sys.version_info
        if ver.major >= 3 and ver.minor >= 8:
            report.add(EnvironmentItem(
                "Python",
                EnvStatus.PASS,
                f"{ver.major}.{ver.minor}.{ver.micro}",
            ))
        else:
            report.add(EnvironmentItem(
                "Python",
                EnvStatus.FAIL,
                f"Need 3.8+, got {ver.major}.{ver.minor}",
            ))

    def _check_sqlite(self, report: EnvironmentReport) -> None:
        try:
            ver = sqlite3.sqlite_version
            report.add(EnvironmentItem("SQLite", EnvStatus.PASS, ver))
        except Exception as exc:
            report.add(EnvironmentItem(
                "SQLite", EnvStatus.FAIL, str(exc),
            ))

    def _check_workspace(self, report: EnvironmentReport) -> None:
        ws = self._workspace
        if os.path.isdir(ws):
            report.add(EnvironmentItem(
                "Workspace", EnvStatus.PASS, ws,
            ))
        else:
            report.add(EnvironmentItem(
                "Workspace", EnvStatus.WARNING,
                f"Directory not found: {ws}",
            ))

    def _check_permissions(self, report: EnvironmentReport) -> None:
        ws = self._workspace
        if not os.path.isdir(ws):
            report.add(EnvironmentItem(
                "Permissions", EnvStatus.WARNING,
                "Workspace does not exist, cannot verify",
            ))
            return
        readable = os.access(ws, os.R_OK)
        writable = os.access(ws, os.W_OK)
        if readable and writable:
            report.add(EnvironmentItem(
                "Permissions", EnvStatus.PASS, "Read+Write",
            ))
        elif readable:
            report.add(EnvironmentItem(
                "Permissions", EnvStatus.WARNING, "Read-only",
            ))
        else:
            report.add(EnvironmentItem(
                "Permissions", EnvStatus.FAIL, "No access",
            ))

    def _check_pyside6(self, report: EnvironmentReport) -> None:
        try:
            import PySide6  # noqa: F401
            report.add(EnvironmentItem(
                "PySide6", EnvStatus.PASS, "Available",
            ))
        except ImportError:
            report.add(EnvironmentItem(
                "PySide6", EnvStatus.WARNING,
                "Not installed — Desktop host unavailable",
            ))

    def _check_rich(self, report: EnvironmentReport) -> None:
        try:
            import rich  # noqa: F401
            report.add(EnvironmentItem(
                "Rich", EnvStatus.PASS, "Available",
            ))
        except ImportError:
            report.add(EnvironmentItem(
                "Rich", EnvStatus.WARNING,
                "Not installed — Console output degraded",
            ))

    def _check_config(self, report: EnvironmentReport) -> None:
        config_path = os.path.join(self._workspace, "sam_config.json")
        if os.path.isfile(config_path):
            report.add(EnvironmentItem(
                "Configuration", EnvStatus.PASS, config_path,
            ))
        else:
            report.add(EnvironmentItem(
                "Configuration", EnvStatus.WARNING,
                "Not found, using defaults",
            ))

    def _check_database(self, report: EnvironmentReport) -> None:
        db_path = os.path.join(self._workspace, "data", "sam.db")
        if os.path.isfile(db_path):
            report.add(EnvironmentItem(
                "Database", EnvStatus.PASS, db_path,
            ))
        else:
            report.add(EnvironmentItem(
                "Database", EnvStatus.WARNING,
                "Not found — first run or missing",
            ))

    def _check_temp_folder(self, report: EnvironmentReport) -> None:
        temp = os.path.join(self._workspace, "temp")
        if os.path.isdir(temp):
            report.add(EnvironmentItem(
                "Temp Folder", EnvStatus.PASS, temp,
            ))
        else:
            report.add(EnvironmentItem(
                "Temp Folder", EnvStatus.WARNING,
                "Not found — will be created on demand",
            ))

    def _check_log_folder(self, report: EnvironmentReport) -> None:
        log = os.path.join(self._workspace, "logs")
        if os.path.isdir(log):
            report.add(EnvironmentItem(
                "Log Folder", EnvStatus.PASS, log,
            ))
        else:
            report.add(EnvironmentItem(
                "Log Folder", EnvStatus.WARNING,
                "Not found — will be created on demand",
            ))

    def _check_provider_config(self, report: EnvironmentReport) -> None:
        providers = os.path.join(self._workspace, "providers.json")
        if os.path.isfile(providers):
            report.add(EnvironmentItem(
                "Provider Config", EnvStatus.PASS, providers,
            ))
        else:
            report.add(EnvironmentItem(
                "Provider Config", EnvStatus.WARNING,
                "Not found — using defaults",
            ))

    def _check_plugin_folder(self, report: EnvironmentReport) -> None:
        plugins = os.path.join(self._workspace, "plugins")
        if os.path.isdir(plugins):
            report.add(EnvironmentItem(
                "Plugin Folder", EnvStatus.PASS, plugins,
            ))
        else:
            report.add(EnvironmentItem(
                "Plugin Folder", EnvStatus.WARNING,
                "Not found — will be created on demand",
            ))
