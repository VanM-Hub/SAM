"""
OP-378 — Launcher Dashboard

DTO dashboard yang berisi informasi startup lengkap:

  Version, Host, Environment, Guardian, Diagnostics,
  Startup Time, Plugins, Configuration
"""

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass(frozen=True)
class DashboardVersionInfo:
    """Version section."""

    version: str = "0.0.0"
    commit: str = "unknown"
    python: str = ""
    build_date: str = ""


@dataclass(frozen=True)
class DashboardHostInfo:
    """Host section."""

    type: str = "unknown"
    display_name: str = ""
    available: bool = False


@dataclass(frozen=True)
class DashboardEnvironmentInfo:
    """Environment section."""

    checks: int = 0
    passed: int = 0
    failed: int = 0
    success: bool = True


@dataclass(frozen=True)
class DashboardGuardianInfo:
    """Guardian Runtime section."""

    available: bool = False
    version: str = ""


@dataclass(frozen=True)
class DashboardDiagnostic:
    """Single diagnostic entry."""

    name: str = ""
    status: str = ""
    detail: str = ""


@dataclass(frozen=True)
class DashboardDiagnosticsInfo:
    """Diagnostics section."""

    total_checks: int = 0
    passed: int = 0
    failed: int = 0
    running: bool = False


@dataclass(frozen=True)
class DashboardPluginsInfo:
    """Plugins section."""

    discovered: int = 0


@dataclass(frozen=True)
class DashboardConfigInfo:
    """Configuration section."""

    theme: str = ""
    host: str = ""
    log_level: str = ""
    safe_mode: str = "NORMAL"
    readonly_filesystem: bool = False


@dataclass(frozen=True)
class DashboardStartupInfo:
    """Startup timing section."""

    start_time_iso: str = ""
    duration_ms: float = 0.0
    stages: int = 0
    success: bool = False


@dataclass(frozen=True)
class LauncherDashboard:
    """Complete launcher dashboard — all startup data in one DTO."""

    version: DashboardVersionInfo = field(default_factory=DashboardVersionInfo)
    host: DashboardHostInfo = field(default_factory=DashboardHostInfo)
    environment: DashboardEnvironmentInfo = field(default_factory=DashboardEnvironmentInfo)
    guardian: DashboardGuardianInfo = field(default_factory=DashboardGuardianInfo)
    diagnostics: DashboardDiagnosticsInfo = field(default_factory=DashboardDiagnosticsInfo)
    plugins: DashboardPluginsInfo = field(default_factory=DashboardPluginsInfo)
    configuration: DashboardConfigInfo = field(default_factory=DashboardConfigInfo)
    startup: DashboardStartupInfo = field(default_factory=DashboardStartupInfo)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": {
                "version": self.version.version,
                "commit": self.version.commit,
                "python": self.version.python,
                "build_date": self.version.build_date,
            },
            "host": {
                "type": self.host.type,
                "display_name": self.host.display_name,
                "available": self.host.available,
            },
            "environment": {
                "checks": self.environment.checks,
                "passed": self.environment.passed,
                "failed": self.environment.failed,
                "success": self.environment.success,
            },
            "guardian": {
                "available": self.guardian.available,
                "version": self.guardian.version,
            },
            "diagnostics": {
                "total_checks": self.diagnostics.total_checks,
                "passed": self.diagnostics.passed,
                "failed": self.diagnostics.failed,
                "running": self.diagnostics.running,
            },
            "plugins": {
                "discovered": self.plugins.discovered,
            },
            "configuration": {
                "theme": self.configuration.theme,
                "host": self.configuration.host,
                "log_level": self.configuration.log_level,
                "safe_mode": self.configuration.safe_mode,
                "readonly_filesystem": self.configuration.readonly_filesystem,
            },
            "startup": {
                "start_time_iso": self.startup.start_time_iso,
                "duration_ms": self.startup.duration_ms,
                "stages": self.startup.stages,
                "success": self.startup.success,
            },
        }
