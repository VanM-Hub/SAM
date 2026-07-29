"""
OP-369 — Integration
=====================

Hooks the launcher pipeline together.

Launcher → Bootstrap → Environment → Config → Diagnostics
→ HostManager → Console / Desktop / Headless

Does NOT import Guardian, Domain, Repository, Storage,
or Conversation API.
"""

import os
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

# Launcher subsystems
from sam.launcher.application import (
    LauncherApplication,
    LauncherContext,
    LauncherResult,
    LauncherState,
)
from sam.launcher.bootstrap import BootstrapManager, BootstrapReport, BootstrapStep
from sam.launcher.environment import EnvironmentValidator, EnvironmentReport, EnvStatus
from sam.launcher.config_loader import ConfigLoader, LauncherConfig, ConfigValidator
from sam.launcher.diagnostics import DiagnosticsEngine, DiagnosticsSnapshot
from sam.launcher.host_manager import HostManager, HostType, Host
from sam.launcher.safe_mode import SafeModeManager, SafeMode
from sam.launcher.version import SamVersion, PluginDiscovery, PluginInfo


def _find_workspace() -> str:
    """Determine the workspace directory.

    Priority: SAM_WORKSPACE env → CWD → parent of package.
    """
    env_ws = os.environ.get("SAM_WORKSPACE")
    if env_ws and os.path.isdir(env_ws):
        return os.path.abspath(env_ws)

    cwd = os.getcwd()
    if os.path.isfile(os.path.join(cwd, "pyproject.toml")) or os.path.isfile(
        os.path.join(cwd, "sam_config.json")
    ):
        return cwd

    return cwd


# ──────────────────────────────────────────────
# Integrated launcher — wires all subsystems
# ──────────────────────────────────────────────

class IntegratedLauncher(LauncherApplication):
    """Fully wired launcher with all subsystems.

    Overrides the phase stubs from LauncherApplication.
    """

    def __init__(self, workspace: str = "") -> None:
        super().__init__()
        self._workspace = workspace or _find_workspace()

        # Subsystems (lazy init in run())
        self._config_loader: Optional[ConfigLoader] = None
        self._bootstrap: Optional[BootstrapManager] = None
        self._env_validator: Optional[EnvironmentValidator] = None
        self._host_manager: Optional[HostManager] = None
        self._diagnostics: Optional[DiagnosticsEngine] = None
        self._safe_mode: Optional[SafeModeManager] = None
        self._version: Optional[SamVersion] = None
        self._plugins: Optional[PluginDiscovery] = None

    # ── overrides ──────────────────────────────

    def _do_bootstrap(self, ctx: LauncherContext) -> None:
        # Initialize subsystems
        self._config_loader = ConfigLoader(self._workspace)
        self._bootstrap = BootstrapManager()
        self._env_validator = EnvironmentValidator(self._workspace)
        self._host_manager = HostManager()
        self._diagnostics = DiagnosticsEngine(self._workspace)
        self._version = SamVersion.detect()
        self._plugins = PluginDiscovery(self._workspace)

        # Load config
        config, config_errors = self._config_loader.load()
        ctx.config = config
        ctx.metadata["config_errors"] = config_errors

        # Initialize safe mode from config
        self._safe_mode = SafeModeManager(config.safe_mode)
        ctx.safe_mode = self._safe_mode

        # Run bootstrap
        bootstrap_report = self._bootstrap.run(ctx)
        ctx.bootstrap_report = bootstrap_report

    def _do_validation(self, ctx: LauncherContext) -> None:
        if self._safe_mode and self._safe_mode.skip_environment_validation:
            return

        report = self._env_validator.validate()
        ctx.env_report = report

        if report.failed > 0:
            ctx.metadata["env_failures"] = [
                item for item in report.items if item.status == EnvStatus.FAIL
            ]

    def _do_ready(self, ctx: LauncherContext) -> None:
        # Run diagnostics (unless skipped by safe mode)
        if not (self._safe_mode and self._safe_mode.skip_diagnostics):
            snapshot = self._diagnostics.snapshot()
            ctx.diagnostics_snapshot = snapshot
            ctx.metadata["diagnostics"] = snapshot.to_dict()

        # Discover plugins
        if not (self._safe_mode and self._safe_mode.skip_plugin_discovery):
            plugins = self._plugins.discover_all()
            ctx.metadata["plugins_discovered"] = len(plugins)

        # Version info
        ctx.metadata["version"] = self._version.to_dict()

    def _do_start_host(self, ctx: LauncherContext) -> None:
        host_type_str = ctx.config.host if ctx.config else "console"
        host_map = {
            "console": HostType.CONSOLE,
            "desktop": HostType.DESKTOP,
            "headless": HostType.HEADLESS,
            "api_server": HostType.API_SERVER,
            "testing": HostType.TESTING,
        }
        htype = host_map.get(host_type_str, HostType.CONSOLE)
        selected = self._host_manager.select(htype) if self._host_manager else None

        if selected:
            ctx.host_type = selected.host_type.value
            ctx.metadata["selected_host"] = selected.display_name
        else:
            ctx.host_type = htype.value
            ctx.exit_code = 1

    def _do_running(self, ctx: LauncherContext) -> None:
        msg = (
            f"SAM Launcher — Version {ctx.metadata.get('version', {}).get('version', '?')} | "
            f"Host: {ctx.host_type}"
        )
        ctx.metadata["launch_message"] = msg


# ── convenience ───────────────────────────────

def create_launcher(workspace: str = "") -> IntegratedLauncher:
    """Create a fully wired launcher instance."""
    return IntegratedLauncher(workspace)


def launch(workspace: str = "") -> int:
    """Convenience: create and run the launcher in one call.

    Returns exit code (0 = success).
    """
    app = IntegratedLauncher(workspace)
    return app.run()


def print_startup_screen(ctx: LauncherContext) -> None:
    """Print the ASCII startup screen based on launcher context."""
    ver = ctx.metadata.get("version", {})
    env_report = ctx.env_report

    lines: List[str] = []
    lines.append("")
    lines.append("=" * 56)
    lines.append(" SAM Launcher")
    lines.append(" Operational Intelligence Platform")
    lines.append("=" * 56)
    lines.append("")
    lines.append(f"Version      : v{ver.get('version', '?')}")
    lines.append(f"Commit       : {ver.get('commit', '?')}")
    lines.append(f"Workspace    : {ctx.config.workspace if ctx.config else '?'}")
    lines.append("")
    lines.append("Environment")
    lines.append("")

    if env_report:
        for item in env_report.items:
            lines.append(f"  [{item.status.value}] {item.name}")
    else:
        lines.append("  [SKIP] Environment validation skipped")

    lines.append("")
    lines.append("Host")
    lines.append("")
    lines.append("  1 Console")
    lines.append("  2 Desktop")
    lines.append("  3 Headless")
    lines.append("  4 API Server")
    lines.append("  5 Diagnostics")
    lines.append("  6 Exit")
    lines.append("")
    lines.append("=" * 56)

    for line in lines:
        print(line)
