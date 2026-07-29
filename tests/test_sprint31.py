"""
OP-370 — Sprint 31 Validation
==============================

Tests for the SAM Launcher & Bootstrap Runtime.

Constraint verification (AST scan):
  0 domain import
  0 repository import
  0 storage import
  0 Guardian modification
  0 Conversation API modification
  0 host modification
"""

import os
import sys
import ast
import time
import json
import shutil
import tempfile
import unittest
from typing import Any, Dict, List, Optional, Set, Tuple

# ──────────────────────────────────────────────
# Ensure src is on path
# ──────────────────────────────────────────────
SAM_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if SAM_ROOT not in sys.path:
    sys.path.insert(0, SAM_ROOT)

# ──────────────────────────────────────────────
# AST scan utilities
# ──────────────────────────────────────────────

LAUNCHER_DIR = os.path.join(SAM_ROOT, "src", "sam", "launcher")

FORBIDDEN_IMPORTS: Set[str] = {
    # Domain layer
    "sam.domain",
    "sam.contracts",
    "sam.contracts.mission",
    "sam.contracts.runtime",
    "sam.contracts.dos",
    "sam.mission.models",
    "sam.dos.models",
    # Repository / Storage
    "sam.storage",
    "sam.storage.decision_repo",
    "sam.storage.mission_repo",
    "sam.storage.trust_repo",
    # Guardian (the launcher must NOT know Guardian)
    "sam.guardian",
    "sam.guardian.engine",
    # Conversation API
    "sam.operations.conversation",
    "sam.operations.conversation_api",
    "sam.operations.conversation_session",
    # Operational Brain
    "sam.operations.brain",
    "sam.operations.decision",
    "sam.operations.reasoning",
    # Decision Runtime
    "sam.operations.dashboard",
    "sam.operations.scoring",
    # Provider
    "sam.operations.providers",
    # Public API
    "sam.api",
    "sam.api.routes",
    "sam.api.server",
    # Existing hosts
    "sam.render",
    "sam.render.cli",
    "sam.render.desktop",
}


def ast_scan_launcher() -> List[Tuple[str, int, str]]:
    """Scan launcher source files for forbidden imports.

    Returns list of (filename, line_number, import_statement).
    """
    violations: List[Tuple[str, int, str]] = []

    for fname in os.listdir(LAUNCHER_DIR):
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
            # Direct imports: import X
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if _is_forbidden(alias.name):
                        violations.append(
                            (fname, node.lineno, f"import {alias.name}")
                        )
            # From imports: from X import Y
            elif isinstance(node, ast.ImportFrom):
                if node.module and _is_forbidden(node.module):
                    names = ", ".join(a.name for a in node.names)
                    violations.append(
                        (fname, node.lineno, f"from {node.module} import {names}")
                    )

    return violations


def _is_forbidden(module: str) -> bool:
    for forbidden in FORBIDDEN_IMPORTS:
        if module == forbidden or module.startswith(forbidden + "."):
            return True
    return False


# ──────────────────────────────────────────────
# Tests
# ──────────────────────────────────────────────

class TestApplication(unittest.TestCase):
    """OP-361: Launcher Application"""

    def test_launcher_application_creates(self):
        from sam.launcher.application import LauncherApplication
        app = LauncherApplication()
        self.assertIsNotNone(app)

    def test_launcher_context(self):
        from sam.launcher.application import LauncherContext, LauncherState
        ctx = LauncherContext()
        self.assertEqual(ctx.state, LauncherState.INIT)
        self.assertGreater(ctx.elapsed, -1)

    def test_launcher_result_ok(self):
        from sam.launcher.application import LauncherResult
        r = LauncherResult.ok("done")
        self.assertTrue(r.success)
        self.assertEqual(r.message, "done")

    def test_launcher_result_fail(self):
        from sam.launcher.application import LauncherResult
        r = LauncherResult.fail("error")
        self.assertFalse(r.success)

    def test_launcher_lifecycle(self):
        from sam.launcher.application import LauncherApplication, LauncherState
        app = LauncherApplication()
        observed: List[LauncherState] = []
        app.on(LauncherState.BOOTSTRAP, lambda ctx: observed.append(ctx.state))
        code = app.run()
        self.assertEqual(code, 0)
        self.assertIn(LauncherState.BOOTSTRAP, observed)


class TestBootstrap(unittest.TestCase):
    """OP-362: Bootstrap Runtime"""

    def test_bootstrap_manager_creates(self):
        from sam.launcher.bootstrap import BootstrapManager
        mgr = BootstrapManager()
        self.assertIsNotNone(mgr)

    def test_bootstrap_report(self):
        from sam.launcher.bootstrap import BootstrapReport, BootstrapStep
        report = BootstrapReport()
        self.assertEqual(len(report.steps), 0)
        report.add_step(BootstrapStep.CONFIG_LOAD, "PASS", "ok", 0.01)
        self.assertEqual(len(report.steps), 1)
        report.finalize()
        self.assertTrue(report.success)

    def test_bootstrap_run(self):
        from sam.launcher.bootstrap import BootstrapManager
        mgr = BootstrapManager()
        report = mgr.run(None)
        self.assertIsNotNone(report)
        self.assertGreater(len(report.steps), 0)
        report.finalize()


class TestEnvironment(unittest.TestCase):
    """OP-363: Environment Validator"""

    def test_env_validator_creates(self):
        from sam.launcher.environment import EnvironmentValidator
        v = EnvironmentValidator()
        self.assertIsNotNone(v)

    def test_env_report(self):
        from sam.launcher.environment import (
            EnvironmentReport, EnvironmentItem, EnvStatus,
        )
        report = EnvironmentReport()
        report.add(EnvironmentItem("Python", EnvStatus.PASS))
        self.assertEqual(report.passed, 1)
        self.assertTrue(report.success)

    def test_env_validate_python(self):
        from sam.launcher.environment import EnvironmentValidator
        v = EnvironmentValidator()
        report = v.validate()
        # Python check should always pass in 3.8+
        py_item = [i for i in report.items if i.name == "Python"]
        self.assertEqual(len(py_item), 1)
        self.assertEqual(py_item[0].status.value, "PASS")


class TestConfig(unittest.TestCase):
    """OP-365: Configuration Loader"""

    def test_config_defaults(self):
        from sam.launcher.config_loader import LauncherConfig
        cfg = LauncherConfig()
        self.assertEqual(cfg.theme, "dark")
        self.assertEqual(cfg.host, "console")
        self.assertFalse(cfg.readonly)

    def test_config_from_dict(self):
        from sam.launcher.config_loader import LauncherConfig
        cfg = LauncherConfig.from_dict({"theme": "light", "host": "desktop"})
        self.assertEqual(cfg.theme, "light")
        self.assertEqual(cfg.host, "desktop")

    def test_config_validator_passes(self):
        from sam.launcher.config_loader import LauncherConfig, ConfigValidator
        cfg = LauncherConfig()
        errors = ConfigValidator.validate(cfg)
        self.assertEqual(len(errors), 0)

    def test_config_validator_fails(self):
        from sam.launcher.config_loader import LauncherConfig, ConfigValidator
        cfg = LauncherConfig(theme="neon", log_level="SUPER")
        errors = ConfigValidator.validate(cfg)
        self.assertGreater(len(errors), 0)

    def test_config_loader(self):
        from sam.launcher.config_loader import ConfigLoader
        loader = ConfigLoader()
        config, errors = loader.load()
        self.assertIsNotNone(config)
        self.assertIsInstance(errors, list)


class TestDiagnostics(unittest.TestCase):
    """OP-366: Diagnostics"""

    def test_diagnostics_engine(self):
        from sam.launcher.diagnostics import DiagnosticsEngine
        engine = DiagnosticsEngine()
        self.assertIsNotNone(engine)

    def test_diagnostics_snapshot(self):
        from sam.launcher.diagnostics import DiagnosticsEngine
        engine = DiagnosticsEngine()
        snap = engine.snapshot()
        self.assertIsNotNone(snap)
        self.assertGreater(len(snap.checks), 0)
        self.assertGreater(snap.summary.total_checks, 0)

    def test_diagnostics_summary(self):
        from sam.launcher.diagnostics import DiagnosticsSummary
        s = DiagnosticsSummary(total_checks=5, passed=5)
        self.assertTrue(s.success)
        s2 = DiagnosticsSummary(total_checks=5, passed=4, failed=1)
        self.assertFalse(s2.success)


class TestHostManager(unittest.TestCase):
    """OP-364: Host Manager"""

    def test_host_manager_creates(self):
        from sam.launcher.host_manager import HostManager
        mgr = HostManager()
        self.assertGreater(len(mgr.hosts), 0)

    def test_host_types(self):
        from sam.launcher.host_manager import HostType
        self.assertIsNotNone(HostType.CONSOLE)
        self.assertIsNotNone(HostType.DESKTOP)
        self.assertIsNotNone(HostType.HEADLESS)
        self.assertIsNotNone(HostType.API_SERVER)

    def test_select_available(self):
        from sam.launcher.host_manager import HostManager, HostType
        mgr = HostManager()
        host = mgr.select(HostType.CONSOLE)
        self.assertIsNotNone(host)
        self.assertTrue(host.available)

    def test_select_unavailable(self):
        from sam.launcher.host_manager import HostManager, HostType
        mgr = HostManager()
        mgr.mark_unavailable(HostType.API_SERVER)
        host = mgr.select(HostType.API_SERVER)
        self.assertIsNone(host)


class TestSafeMode(unittest.TestCase):
    """OP-367: Safe Mode"""

    def test_safe_mode_normal(self):
        from sam.launcher.safe_mode import SafeModeManager, SafeMode
        mgr = SafeModeManager("NORMAL")
        self.assertEqual(mgr.mode, SafeMode.NORMAL)
        self.assertTrue(mgr.is_normal)

    def test_safe_mode_skip_diagnostics(self):
        from sam.launcher.safe_mode import SafeModeManager
        mgr = SafeModeManager("MINIMAL")
        self.assertTrue(mgr.skip_diagnostics)
        self.assertTrue(mgr.skip_environment_validation)
        self.assertTrue(mgr.skip_plugin_discovery)

    def test_safe_mode_invalid_fallback(self):
        from sam.launcher.safe_mode import SafeModeManager, SafeMode
        mgr = SafeModeManager("INVALID")
        self.assertEqual(mgr.mode, SafeMode.NORMAL)

    def test_safe_mode_readonly(self):
        from sam.launcher.safe_mode import SafeModeManager
        mgr = SafeModeManager("READ_ONLY")
        self.assertTrue(mgr.readonly_filesystem)


class TestVersion(unittest.TestCase):
    """OP-368: Version & Plugin Discovery"""

    def test_version_detect(self):
        from sam.launcher.version import SamVersion
        ver = SamVersion.detect()
        self.assertIsNotNone(ver)
        self.assertGreater(len(ver.python_version), 0)

    def test_version_to_dict(self):
        from sam.launcher.version import SamVersion
        ver = SamVersion.detect()
        d = ver.to_dict()
        self.assertIn("version", d)
        self.assertIn("python", d)

    def test_plugin_discovery_creates(self):
        from sam.launcher.version import PluginDiscovery
        pd = PluginDiscovery()
        self.assertIsNotNone(pd)

    def test_plugin_discovery_empty(self):
        from sam.launcher.version import PluginDiscovery
        with tempfile.TemporaryDirectory() as td:
            pd = PluginDiscovery(td)
            plugins = pd.discover_all()
            self.assertEqual(len(plugins), 0)


class TestIntegration(unittest.TestCase):
    """OP-369: Integration"""

    def test_integrated_launcher_creates(self):
        from sam.launcher.integration import IntegratedLauncher
        app = IntegratedLauncher()
        self.assertIsNotNone(app)

    def test_integrated_launcher_run(self):
        from sam.launcher.integration import IntegratedLauncher
        app = IntegratedLauncher()
        code = app.run()
        self.assertEqual(code, 0)

    def test_create_launcher(self):
        from sam.launcher.integration import create_launcher
        app = create_launcher()
        self.assertIsNotNone(app)

    def test_convenience_launch(self):
        from sam.launcher.integration import launch
        code = launch()
        self.assertEqual(code, 0)

    def test_print_startup_screen(self):
        from sam.launcher.application import LauncherContext
        from sam.launcher.config_loader import LauncherConfig
        from sam.launcher.integration import print_startup_screen
        from sam.launcher.environment import EnvironmentValidator
        import io
        ctx = LauncherContext()
        ctx.config = LauncherConfig()
        ctx.env_report = EnvironmentValidator().validate()
        ctx.metadata["version"] = {
            "version": "4.35.0",
            "commit": "test",
            "python": "3.8",
            "platform": "test",
        }
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        try:
            print_startup_screen(ctx)
            output = captured.getvalue()
            self.assertIn("SAM Launcher", output)
            self.assertIn("Environment", output)
        finally:
            sys.stdout = old_stdout


class TestASTScan(unittest.TestCase):
    """AST scan: verify no forbidden imports in launcher"""

    def test_no_forbidden_imports(self):
        violations = ast_scan_launcher()
        if violations:
            msg_lines = ["Forbidden imports found in launcher:"]
            for fname, lineno, imp in violations:
                msg_lines.append(f"  {fname}:{lineno} - {imp}")
            self.fail("\n".join(msg_lines))


# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────

if __name__ == "__main__":
    unittest.main()
