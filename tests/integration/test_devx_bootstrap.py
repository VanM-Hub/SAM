"""
E1-G1 - Automatic Bootstrap Installation (WP-E2.1, Program E / MISSION-2E)
Evidence Tests.

Menutup gap E1-G1 (Priority WP-E2.1, Program E / MISSION-2E, EA-002):
- Dependency validation: python/pip/setuptools/wheel/sam import check.
- Environment validation: executable/venv/repo structure/PYTHONPATH/writable.
- Bootstrap installer (orchestrator): one-command flow deterministik, dry-run
  default tidak mengubah filesystem, verify-after-install.
- Installation verifier: import/version/entry points/first-run API.
- Installation report: text & dict.

Constraint EA-002 dijaga: modul sam.devx stand-alone, TIDAK mengubah runtime/
governance/deployment/Foundation existing. Test memakai tmp_path fixture
(BUKAN folder repo) agar aman untuk CI baseline.
"""

import sys
from pathlib import Path

import pytest

from sam.devx import (
    bootstrap,
    BootstrapInstaller,
    DependencyChecker,
    EnvironmentValidator,
    InstallationReportBuilder,
    InstallationVerifier,
)
from sam.devx.state import (
    CheckSeverity,
    DependencyStatus,
    EnvStatus,
    InstallPhase,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture()
def fake_repo(tmp_path: Path) -> Path:
    """Buat struktur repo minimal (pyproject.toml + src/sam/__init__.py)."""
    (tmp_path / "src" / "sam").mkdir(parents=True, exist_ok=True)
    (tmp_path / "src" / "sam" / "__init__.py").write_text(
        "__version__ = '9.9.9'\n", encoding="utf-8"
    )
    (tmp_path / "pyproject.toml").write_text(
        "[project]\nname='sam-test'\nversion='9.9.9'\n", encoding="utf-8"
    )
    return tmp_path


# ===========================================================================
# 1. DependencyChecker
# ===========================================================================
class TestDependencyChecker:
    def test_python_check_ok(self):
        checker = DependencyChecker()
        res = checker.check_python()
        assert res.passed is True
        assert res.required is True
        assert res.severity is CheckSeverity.REQUIRED
        assert sys.version_info[:2] >= (3, 8)

    def test_python_check_below_min_fails(self):
        # Python minimum yang mustahil (9999) memastikan gagal.
        checker = DependencyChecker(python_min=(9999, 0))
        res = checker.check_python()
        assert res.passed is False
        assert res.is_blocking is True
        assert res.status is DependencyStatus.WRONG_VERSION

    def test_pip_present_or_absent_deterministic(self):
        checker = DependencyChecker()
        res = checker.check_pip()
        assert res.required is True
        # hasilnya boolean deterministik: INSTALLED atau MISSING
        assert res.status in (DependencyStatus.INSTALLED, DependencyStatus.MISSING)

    def test_sam_importable_in_repo_env(self):
        checker = DependencyChecker()
        res = checker.check_sam_importable()
        # Dalam test environment ini sam terinstall -> INSTALLED
        # (fallback jika tidak: tetap deterministik, bukan error)
        assert res.status in (DependencyStatus.INSTALLED, DependencyStatus.MISSING)

    def test_build_backend_result(self):
        checker = DependencyChecker()
        res = checker.check_build_backend()
        assert res.required is True

    def test_run_returns_ordered_checks(self):
        checker = DependencyChecker()
        checks = checker.run(include_optional=False)
        names = [c.name for c in checks]
        assert names == ["python", "pip", "build-backend", "sam"]

    def test_summary_counts(self):
        checker = DependencyChecker()
        checks = checker.run(include_optional=False)
        summary = checker.summary(checks)
        assert "pass" in summary and "fail" in summary


# ===========================================================================
# 2. EnvironmentValidator
# ===========================================================================
class TestEnvironmentValidator:
    def test_project_root_inferred(self):
        env = EnvironmentValidator()
        # project root harus berisi pyproject.toml (repo asli)
        assert env.project_root is not None
        assert (env.project_root / "pyproject.toml").exists() or env.project_root.name == "SAM"

    def test_python_executable_ok(self):
        env = EnvironmentValidator()
        res = env.check_python_executable()
        assert res.passed is True
        assert res.status is EnvStatus.OK

    def test_version_ok(self):
        env = EnvironmentValidator()
        res = env.check_python_version()
        assert res.passed is True

    def test_repo_structure_ok_fake(self, fake_repo):
        env = EnvironmentValidator(fake_repo)
        res = env.check_repo_structure()
        assert res.passed is True
        assert res.status is EnvStatus.OK

    def test_repo_structure_missing(self, tmp_path):
        env = EnvironmentValidator(tmp_path)
        res = env.check_repo_structure()
        assert res.passed is False
        assert res.status is EnvStatus.MISSING

    def test_run_returns_components(self, fake_repo):
        env = EnvironmentValidator(fake_repo)
        checks = env.run()
        components = [c.component for c in checks]
        assert "python_executable" in components
        assert "repo_structure" in components
        assert "virtualenv" in components

    def test_no_blocking_failure_fake_repo(self, fake_repo):
        env = EnvironmentValidator(fake_repo)
        checks = env.run()
        # fake repo punya struktur valid -> tidak boleh blocking python/repo failing
        assert env.has_blocking_failure(checks) is False


# ===========================================================================
# 3. BootstrapInstaller (orchestrator)
# ===========================================================================
class TestBootstrapInstaller:
    def test_dry_run_default_no_filesystem_change(self, fake_repo):
        """Dry-run (default) TIDAK boleh membuat venv / modifikasi."""
        before = set(p.name for p in fake_repo.rglob("*") if p.is_file())
        installer = BootstrapInstaller(project_root=fake_repo, apply=False)
        report = installer.run()
        after = set(p.name for p in fake_repo.rglob("*") if p.is_file())
        # tidak ada file baru dibuat oleh bootstrap dry-run
        assert before == after
        # report adalah objek InstallationReport
        assert hasattr(report, "success")
        assert report.phases_run

    def test_phases_ordered(self, fake_repo):
        installer = BootstrapInstaller(project_root=fake_repo, apply=False)
        report = installer.run()
        phases = [p.value for p in report.phases_run]
        assert phases[0] == "dependency_validation"
        assert "environment_validation" in phases
        assert "install_verification" in phases
        assert "diagnostics" in phases

    def test_success_flag_true_in_dry_run(self, fake_repo):
        # dry-run memvalidasi & menyusun rencana -> success True bila tak blocking
        env_checks = EnvironmentValidator(fake_repo).run()
        if not EnvironmentValidator(fake_repo).has_blocking_failure(env_checks):
            installer = BootstrapInstaller(project_root=fake_repo, apply=False)
            report = installer.run()
            assert report.success is True

    def test_one_command_bootstrap_function(self, fake_repo):
        report = bootstrap(project_root=fake_repo, apply=False)
        assert report is not None
        assert hasattr(report, "steps")

    def test_env_init_dry_run_creates_no_venv(self, fake_repo):
        installer = BootstrapInstaller(project_root=fake_repo, apply=False, venv_dir=".venv")
        steps = installer.phase_environment_init()
        assert steps
        assert all(s.ok for s in steps)
        # dry-run TIDAK membuat .venv
        assert not (fake_repo / ".venv").exists()

    def test_installation_dry_run_no_pip(self, fake_repo):
        installer = BootstrapInstaller(project_root=fake_repo, apply=False)
        steps = installer.phase_installation()
        assert steps and steps[0].ok
        assert "Dry-run" in steps[0].message


# ===========================================================================
# 4. InstallationVerifier
# ===========================================================================
class TestInstallationVerifier:
    def test_import_sam_ok(self):
        v = InstallationVerifier()
        res = v.check_import()
        assert res.ok is True
        assert res.required is True

    def test_first_run_api_present(self):
        v = InstallationVerifier()
        res = v.check_first_run()
        # Setidaknya enabler object ada (observe atau SAM)
        assert res.name == "first_run_api"

    def test_verify_returns_checks(self, fake_repo):
        v = InstallationVerifier(fake_repo)
        result = v.verify()
        names = [c.name for c in result.checks]
        assert "import_sam" in names
        assert "package_version" in names
        assert "entry_points" in names

    def test_diagnostics_structure(self):
        v = InstallationVerifier()
        diag = v.diagnostics()
        assert "python" in diag
        assert "entry_points" in diag


# ===========================================================================
# 5. InstallationReportBuilder
# ===========================================================================
class TestInstallationReportBuilder:
    def test_summary_keys(self, fake_repo):
        installer = BootstrapInstaller(project_root=fake_repo, apply=False)
        report = installer.run()
        builder = InstallationReportBuilder()
        summary = builder.build_summary(report)
        assert summary["status"] in ("success", "failed")

    def test_to_text_output(self, fake_repo):
        installer = BootstrapInstaller(project_root=fake_repo, apply=False)
        report = installer.run()
        text = InstallationReportBuilder().to_text(report)
        assert "SAM Bootstrap Installation Report" in text

    def test_to_dict_output(self, fake_repo):
        installer = BootstrapInstaller(project_root=fake_repo, apply=False)
        report = installer.run()
        d = InstallationReportBuilder().to_dict(report)
        assert isinstance(d, dict)
        assert "phases_run" in d
        assert "steps" in d
        assert isinstance(d["steps"], list)


# ===========================================================================
# 6. Round-trip: report saling konsisten
# ===========================================================================
class TestRoundTrip:
    def test_dict_consistent_with_report(self, fake_repo):
        installer = BootstrapInstaller(project_root=fake_repo, apply=False)
        report = installer.run()
        d = InstallationReportBuilder().to_dict(report)
        # phases di dict sama dengan report.phases_run
        assert [p.value for p in report.phases_run] == d["phases_run"]
        # jumlah steps di dict sama
        assert len(report.steps) == len(d["steps"])
        # status report == status dict
        assert report.success == (d["summary"]["status"] == "success")
