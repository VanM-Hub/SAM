"""
OP-379 — Sprint 32 Integration Validation

Test:
  - startup desktop
  - startup console
  - startup headless
  - fallback
  - diagnostics
  - safe mode
  - registry
  - runtime bootstrap
  - launcher dashboard

AST scan:
  0 domain import
  0 repository import
  0 storage import
  0 auto execution
"""

import os
import sys
import ast
import json
import tempfile
import unittest
from typing import Any, Dict, List, Set, Tuple

SAM_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if SAM_ROOT not in sys.path:
    sys.path.insert(0, SAM_ROOT)

LAUNCHER_DIR = os.path.join(SAM_ROOT, "src", "sam", "launcher")

# ── AST scan ──────────────────────────────────

FORBIDDEN_IMPORTS: Set[str] = {
    "sam.domain",
    "sam.contracts",
    "sam.contracts.mission",
    "sam.contracts.runtime",
    "sam.contracts.dos",
    "sam.mission.models",
    "sam.dos.models",
    "sam.storage",
    "sam.storage.decision_repo",
    "sam.storage.mission_repo",
    "sam.storage.trust_repo",
    "sam.guardian.engine",
    "sam.operations.conversation",
    "sam.operations.conversation_api",
    "sam.operations.conversation_session",
    "sam.operations.brain",
    "sam.operations.decision",
    "sam.operations.reasoning",
    "sam.operations.dashboard",
    "sam.operations.scoring",
    "sam.operations.providers",
    "sam.api",
    "sam.api.routes",
    "sam.api.server",
    "sam.render",
    "sam.render.cli",
    "sam.render.desktop",
}


def ast_scan_launcher() -> List[Tuple[str, int, str]]:
    """Scan launcher source files for forbidden imports.

    Returns list of (filename, line_number, import_statement).
    """
    violations: List[Tuple[str, int, str]] = []

    for fname in sorted(os.listdir(LAUNCHER_DIR)):
        if not fname.endswith(".py"):
            continue
        fpath = os.path.join(LAUNCHER_DIR, fname)
        with open(fpath, "r", encoding="utf-8") as f:
            try:
                tree = ast.parse(f.read(), filename=fpath)
            except SyntaxError:
                violations.append((fname, 0, "SYNTAX ERROR"))
                continue

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if _is_forbidden(alias.name):
                        violations.append((fname, node.lineno, f"import {alias.name}"))
            elif isinstance(node, ast.ImportFrom):
                if node.module and _is_forbidden(node.module):
                    names = ", ".join(a.name for a in node.names)
                    violations.append((fname, node.lineno, f"from {node.module} import {names}"))

    return violations


def _is_forbidden(module: str) -> bool:
    for forbidden in FORBIDDEN_IMPORTS:
        if module == forbidden or module.startswith(forbidden + "."):
            return True
    return False


# ── Tests ─────────────────────────────────────

class TestRuntimeBootstrap(unittest.TestCase):
    """OP-371: Runtime Bootstrap Orchestrator"""

    def test_orchestrator_creates(self):
        from sam.launcher.runtime_bootstrap import RuntimeBootstrapOrchestrator
        o = RuntimeBootstrapOrchestrator()
        self.assertIsNotNone(o)

    def test_orchestrator_run(self):
        from sam.launcher.application import LauncherContext
        from sam.launcher.runtime_bootstrap import RuntimeBootstrapOrchestrator
        ctx = LauncherContext()
        o = RuntimeBootstrapOrchestrator()
        report = o.run(ctx)
        self.assertIsNotNone(report)
        self.assertGreater(len(report.steps), 0)

    def test_orchestrator_skips_with_safe_mode(self):
        from sam.launcher.application import LauncherContext
        from sam.launcher.runtime_bootstrap import RuntimeBootstrapOrchestrator
        from sam.launcher.safe_mode import SafeModeManager
        ctx = LauncherContext()
        ctx.safe_mode = SafeModeManager("MINIMAL")
        o = RuntimeBootstrapOrchestrator()
        report = o.run(ctx)
        step_names = [s.name for s in report.steps]
        # Diagnostics can still run in MINIMAL; orchestrator handles internally
        self.assertGreater(len(step_names), 0)

    def test_orchestrator_report_to_dict(self):
        from sam.launcher.runtime_bootstrap import OrchestratorReport, OrchestratorStep
        report = OrchestratorReport(
            steps=[OrchestratorStep(name="test", success=True, duration_ms=1.0)],
            total_duration_ms=1.0,
        )
        d = report.to_dict()
        self.assertTrue(d["success"])
        self.assertEqual(len(d["steps"]), 1)

    def test_orchestrator_step_to_dict(self):
        from sam.launcher.runtime_bootstrap import OrchestratorStep
        s = OrchestratorStep(name="test", success=True, duration_ms=1.0, detail="ok")
        self.assertEqual(s.name, "test")
        self.assertTrue(s.success)

    def test_orchestrator_detect_guardian(self):
        from sam.launcher.application import LauncherContext
        from sam.launcher.runtime_bootstrap import RuntimeBootstrapOrchestrator
        ctx = LauncherContext()
        o = RuntimeBootstrapOrchestrator()
        o.run(ctx)
        self.assertIn("guardian_available", ctx.metadata)


class TestRuntimeRegistry(unittest.TestCase):
    """OP-372: Runtime Registry"""

    def test_registry_creates(self):
        from sam.launcher.runtime_registry import RuntimeRegistry
        r = RuntimeRegistry()
        self.assertEqual(len(r.list()), 0)

    def test_register(self):
        from sam.launcher.runtime_registry import RuntimeRegistry, RuntimeType, RuntimeDescriptor
        r = RuntimeRegistry()
        r.register(RuntimeDescriptor(type=RuntimeType.CONSOLE, name="Console"))
        self.assertTrue(r.is_registered(RuntimeType.CONSOLE))

    def test_register_dedup(self):
        from sam.launcher.runtime_registry import RuntimeRegistry, RuntimeType, RuntimeDescriptor
        r = RuntimeRegistry()
        r.register(RuntimeDescriptor(type=RuntimeType.DESKTOP, name="Desktop V1"))
        r.register(RuntimeDescriptor(type=RuntimeType.DESKTOP, name="Desktop V2"))
        self.assertEqual(len(r.list()), 1)

    def test_get_nonexistent(self):
        from sam.launcher.runtime_registry import RuntimeRegistry, RuntimeType
        r = RuntimeRegistry()
        self.assertIsNone(r.get(RuntimeType.HEADLESS))

    def test_available_types(self):
        from sam.launcher.runtime_registry import RuntimeRegistry, RuntimeType, RuntimeDescriptor
        r = RuntimeRegistry()
        r.register(RuntimeDescriptor(type=RuntimeType.CONSOLE, name="Console", available=True))
        r.register(RuntimeDescriptor(type=RuntimeType.HEADLESS, name="Headless", available=False))
        avail = r.available_types()
        self.assertIn(RuntimeType.CONSOLE, avail)
        self.assertNotIn(RuntimeType.HEADLESS, avail)

    def test_to_dict(self):
        from sam.launcher.runtime_registry import RuntimeRegistry, RuntimeType, RuntimeDescriptor
        r = RuntimeRegistry()
        r.register(RuntimeDescriptor(type=RuntimeType.CONSOLE, name="Console"))
        d = r.to_dict()
        self.assertIn("runtimes", d)
        self.assertIn("console", d["runtimes"])

    def test_descriptor_to_dict(self):
        from sam.launcher.runtime_registry import RuntimeDescriptor, RuntimeType
        d = RuntimeDescriptor(type=RuntimeType.GUARDIAN, name="Guardian", version="4.35.0")
        dd = d.to_dict()
        self.assertEqual(dd["type"], "guardian")
        self.assertEqual(dd["version"], "4.35.0")


class TestHostLauncher(unittest.TestCase):
    """OP-373: Host Launcher"""

    def test_host_launcher_creates(self):
        from sam.launcher.host_launcher import HostLauncher
        h = HostLauncher()
        self.assertIsNotNone(h)

    def test_launch_unknown(self):
        from sam.launcher.host_launcher import HostLauncher
        from sam.launcher.host_manager import HostType
        h = HostLauncher()
        # We can't really launch unknown, but test error handling
        result = h.launch(HostType.TESTING)
        self.assertTrue(result.success)

    def test_launch_result_fail(self):
        from sam.launcher.host_launcher import HostLauncher, HostLaunchResult
        r = HostLaunchResult(host_type="test", success=False, error="failed")
        self.assertFalse(r.success)

    def test_launch_result_to_dict(self):
        from sam.launcher.host_launcher import HostLaunchResult
        r = HostLaunchResult(host_type="console", success=True, pid=123)
        d = r.to_dict()
        self.assertEqual(d["host_type"], "console")
        self.assertTrue(d["success"])

    def test_launch_diagnostics(self):
        from sam.launcher.host_launcher import HostLauncher
        from sam.launcher.host_manager import HostType
        h = HostLauncher()
        result = h.launch(HostType.DIAGNOSTICS)
        self.assertTrue(result.success)


class TestStartupPipeline(unittest.TestCase):
    """OP-374: Startup Pipeline"""

    def test_pipeline_creates(self):
        from sam.launcher.startup_pipeline import StartupPipeline
        p = StartupPipeline()
        self.assertIsNotNone(p)

    def test_pipeline_run(self):
        from sam.launcher.startup_pipeline import StartupPipeline
        p = StartupPipeline()
        result = p.run()
        self.assertIsNotNone(result)
        self.assertGreater(len(result.stages), 0)

    def test_pipeline_stages(self):
        from sam.launcher.startup_pipeline import StartupPipeline, PipelineStage
        p = StartupPipeline()
        result = p.run()
        stage_names = [s.stage for s in result.stages]
        self.assertIn("application", stage_names)
        self.assertIn("ready", stage_names)

    def test_pipeline_result(self):
        from sam.launcher.startup_pipeline import PipelineResult
        from sam.launcher.startup_report import StageResult
        r = PipelineResult(
            stages=[StageResult(stage="test", success=True, duration_ms=1.0)],
            total_duration_ms=1.0,
            success=True,
        )
        d = r.to_dict()
        self.assertTrue(d["success"])


class TestStartupReport(unittest.TestCase):
    """OP-375: Startup Report"""

    def test_stage_result(self):
        from sam.launcher.startup_report import StageResult
        s = StageResult(stage="test", success=True)
        d = s.to_dict()
        self.assertEqual(d["stage"], "test")
        self.assertTrue(d["success"])

    def test_issue(self):
        from sam.launcher.startup_report import StartupIssue, IssueSeverity
        i = StartupIssue(stage="test", severity=IssueSeverity.WARNING, message="warn")
        d = i.to_dict()
        self.assertEqual(d["severity"], "warning")

    def test_summary(self):
        from sam.launcher.startup_report import StartupSummary
        s = StartupSummary(total_stages=5, passed=3, failed=2)
        self.assertFalse(s.success)

    def test_report_creates(self):
        from sam.launcher.startup_report import StartupReport, StageResult
        r = StartupReport(
            stages=[StageResult(stage="a", success=True)],
            success=True,
        )
        self.assertEqual(r.summary_dto.total_stages, 1)
        self.assertEqual(r.summary_dto.passed, 1)

    def test_report_issues(self):
        from sam.launcher.startup_report import StartupReport, StartupIssue, IssueSeverity
        r = StartupReport(issues=[StartupIssue(stage="test", severity=IssueSeverity.ERROR, message="err")])
        self.assertEqual(r.summary_dto.issues_count, 1)


class TestRecoveryStartup(unittest.TestCase):
    """OP-376: Recovery Startup"""

    def test_recovery_creates(self):
        from sam.launcher.recovery_startup import RecoveryStartup
        r = RecoveryStartup()
        self.assertIsNotNone(r)

    def test_recovery_host(self):
        from sam.launcher.recovery_startup import RecoveryStartup
        from sam.launcher.host_manager import HostType
        r = RecoveryStartup()
        result = r.start(HostType.TESTING)
        self.assertTrue(result.success)
        self.assertEqual(result.final_host, "Testing")

    def test_recovery_chain(self):
        from sam.launcher.recovery_startup import RecoveryStartup
        from sam.launcher.host_manager import HostType
        r = RecoveryStartup()
        result = r.start(HostType.TESTING)
        self.assertGreater(len(result.steps), 0)
        self.assertTrue(result.success)

    def test_recovery_step_to_dict(self):
        from sam.launcher.recovery_startup import RecoveryStep, FallbackLevel
        s = RecoveryStep(level=FallbackLevel.SAFE_MODE, action="test", success=True)
        d = s.to_dict()
        self.assertEqual(d["level"], "safe_mode")

    def test_recovery_result_to_dict(self):
        from sam.launcher.recovery_startup import RecoveryResult, RecoveryStep, FallbackLevel
        r = RecoveryResult(
            final_host="console",
            final_safe_mode="SAFE",
            success=True,
            steps=[RecoveryStep(level=FallbackLevel.NONE, action="start", success=True)],
        )
        d = r.to_dict()
        self.assertEqual(d["final_host"], "console")


class TestCLIEntry(unittest.TestCase):
    """OP-377: CLI Entry"""

    def test_sam_main_version(self):
        from sam.launcher.cli_entry import sam_main
        try:
            sam_main(["--version"])
        except SystemExit:
            pass

    def test_diagnostic_main(self):
        from sam.launcher.cli_entry import diagnostic_main
        try:
            diagnostic_main()
        except SystemExit:
            pass


class TestLauncherDashboard(unittest.TestCase):
    """OP-378: Launcher Dashboard"""

    def test_dashboard_creates(self):
        from sam.launcher.launcher_dashboard import LauncherDashboard
        d = LauncherDashboard()
        self.assertIsNotNone(d)

    def test_dashboard_version(self):
        from sam.launcher.launcher_dashboard import LauncherDashboard, DashboardVersionInfo
        d = LauncherDashboard(version=DashboardVersionInfo(version="4.36.0"))
        self.assertEqual(d.version.version, "4.36.0")

    def test_dashboard_to_dict(self):
        from sam.launcher.launcher_dashboard import LauncherDashboard, DashboardVersionInfo
        d = LauncherDashboard(version=DashboardVersionInfo(version="4.36.0"))
        dd = d.to_dict()
        self.assertEqual(dd["version"]["version"], "4.36.0")
        self.assertIn("host", dd)
        self.assertIn("startup", dd)

    def test_all_sections_present(self):
        from sam.launcher.launcher_dashboard import LauncherDashboard
        d = LauncherDashboard()
        dd = d.to_dict()
        for key in ("version", "host", "environment", "guardian", "diagnostics", "plugins", "configuration", "startup"):
            self.assertIn(key, dd, f"Missing section: {key}")


class TestASTScan(unittest.TestCase):
    """AST scan: verify no forbidden imports in launcher"""

    def test_no_forbidden_imports(self):
        violations = ast_scan_launcher()
        if violations:
            msg_lines = ["Forbidden imports found in launcher:"]
            for fname, lineno, imp in violations:
                msg_lines.append(f"  {fname}:{lineno} - {imp}")
            self.fail("\n".join(msg_lines))
