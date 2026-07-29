"""
OP-377 — CLI Entry Point

Launcher CLI — menjalankan SAM melalui launcher pipeline.
Mendukung: sam, sam-console, sam-desktop, sam-headless, sam-diagnostic

Entry points untuk pyproject.toml:

[project.scripts]
sam = "sam.launcher.cli_entry:sam_main"
sam-console = "sam.launcher.cli_entry:console_main"
sam-desktop = "sam.launcher.cli_entry:desktop_main"
sam-headless = "sam.launcher.cli_entry:headless_main"
sam-diagnostic = "sam.launcher.cli_entry:diagnostic_main"
"""

import os
import sys
import argparse
from typing import Optional

from sam.launcher.startup_pipeline import StartupPipeline, PipelineResult
from sam.launcher.recovery_startup import RecoveryStartup
from sam.launcher.host_manager import HostType
from sam.launcher.safe_mode import SafeMode


def _ensure_path() -> None:
    src = os.path.join(os.path.dirname(__file__), "..", "..", "..", "src")
    src = os.path.abspath(src)
    if src not in sys.path:
        sys.path.insert(0, src)


def _get_workspace() -> str:
    return os.environ.get("SAM_WORKSPACE", os.getcwd())


def _print_report(result: PipelineResult) -> None:
    print("=" * 56)
    print(" SAM Launcher — Startup Report")
    print("=" * 56)
    for s in result.stages:
        icon = "✅" if s.success else "❌"
        print(f" {icon} {s.stage:25s}  {s.duration_ms:>8.1f}ms")
    print("=" * 56)
    summary = f"Total: {result.total_duration_ms:.0f}ms — "
    summary += "SUCCESS" if result.success else "FAILED"
    print(f" {summary}")
    if result.host_result:
        hr = result.host_result
        icon = "✅" if hr.success else "❌"
        print(f" {icon} Host: {hr.host_type}  pid={hr.pid}  ({hr.duration_ms:.0f}ms)")
    print("=" * 56)


def sam_main(argv: Optional[list] = None) -> None:
    """Default SAM launcher — detects host automatically."""
    _ensure_path()
    parser = argparse.ArgumentParser(description="SAM Launcher — Operational Intelligence Platform")
    parser.add_argument("--host", default="auto", choices=["auto", "console", "desktop", "headless", "api_server"])
    parser.add_argument("--safe-mode", default="NORMAL", choices=["NORMAL", "SAFE", "READ_ONLY", "MINIMAL"])
    parser.add_argument("--workspace", default="")
    parser.add_argument("--report", action="store_true", help="Print startup report")
    parser.add_argument("--version", action="store_true")
    args = parser.parse_args(argv)

    if args.version:
        from sam.launcher.version import SamVersion
        ver = SamVersion.detect()
        print(f"SAM Launcher v{ver.version} (commit: {ver.commit})")
        return

    workspace = args.workspace or _get_workspace()

    if args.host == "auto":
        host_map = {
            "desktop": HostType.DESKTOP,
            "console": HostType.CONSOLE,
            "headless": HostType.HEADLESS,
        }
        env_host = os.environ.get("SAM_HOST", "console")
        target = host_map.get(env_host, HostType.CONSOLE)

        recovery = RecoveryStartup(workspace)
        result = recovery.start(target)
        if result.success:
            print(f"SAM ready — host: {result.final_host}  mode: {result.final_safe_mode}")
        else:
            print("SAM — diagnostics mode (no host available)")
        return

    # Explicit host
    env_safe = args.safe_mode
    os.environ.setdefault("SAM_SAFE_MODE", env_safe)

    pipeline = StartupPipeline(workspace)
    result = pipeline.run()

    if args.report:
        _print_report(result)

    sys.exit(0 if result.success else 1)


def console_main() -> None:
    """Launch console mode via launcher."""
    _ensure_path()
    pipeline = StartupPipeline(_get_workspace())
    result = pipeline.run()
    sys.exit(0 if result.success else 1)


def desktop_main() -> None:
    """Launch desktop mode via launcher."""
    _ensure_path()
    os.environ["SAM_HOST"] = "desktop"
    pipeline = StartupPipeline(_get_workspace())
    result = pipeline.run()
    sys.exit(0 if result.success else 1)


def headless_main() -> None:
    """Launch headless mode via launcher."""
    _ensure_path()
    os.environ["SAM_HOST"] = "headless"
    pipeline = StartupPipeline(_get_workspace())
    result = pipeline.run()
    sys.exit(0 if result.success else 1)


def diagnostic_main() -> None:
    """Run diagnostics then exit."""
    _ensure_path()
    from sam.launcher.diagnostics import DiagnosticsEngine
    engine = DiagnosticsEngine(_get_workspace())
    snap = engine.snapshot()
    print(f"SAM Diagnostics — {snap.summary.total_checks} checks")
    print(f"  Passed:   {snap.summary.passed}")
    print(f"  Failed:   {snap.summary.failed}")
    sys.exit(1 if snap.summary.failed > 0 else 0)
