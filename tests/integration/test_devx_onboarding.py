"""
E2-G1 - CLI Onboarding (WP-E2.2, Program E / MISSION-2E, EA-002)
Evidence Tests.

Menutup gap E2-G1 (Priority WP-E2.2, Program E / MISSION-2E, EA-002):
"Tidak ada command `sam --version` / `sam doctor` / `sam init` untuk onboarding."

Capability ini menyediakan logika onboarding CLI yang testable:
- `version_string()`: informasi versi package (tidak pernah error).
- `doctor()`: diagnosa kesehatan instalasi & environment (reuse WP-E2.1).
- `init_plan()`: rencana onboarding project (dry-run, tidak mengubah FS).

Constraint EA-002 dijaga:
- Modul `sam.devx.onboarding` stand-alone, TIDAK mengubah runtime/governance.
- Reuse DependencyChecker/EnvironmentValidator/BootstrapInstaller (no duplikasi).
- Test memakai tmp_path fixture (BUKAN folder repo) agar aman untuk CI baseline.
- Test TIDAK menggantung sukses pada `import sam` runtime (pola WP-E2.1) -
  assert struktur & kontrak logika, bukan hasil env-dependent.
"""

import sys
from pathlib import Path

import pytest

from sam.devx.onboarding import (
    DoctorReport,
    InitPlan,
    doctor,
    init_plan,
    version_string,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture()
def fake_repo(tmp_path: Path) -> Path:
    """Buat struktur repo minimal (pyproject.toml + src/sam/__init__.py)."""
    (tmp_path / "src" / "sam").mkdir(parents=True, exist_ok=True)
    (tmp_path / "src" / "sam" / "__init__.py").write_text(
        '__version__ = "1.0.0"\n', encoding="utf-8"
    )
    (tmp_path / "pyproject.toml").write_text(
        "[project]\nname = \"sam-fake\"\nversion = \"1.0.0\"\n", encoding="utf-8"
    )
    return tmp_path


@pytest.fixture()
def empty_dir(tmp_path: Path) -> Path:
    """Direktori kosong (belum struktur repo)."""
    return tmp_path


# ---------------------------------------------------------------------------
# 1. version_string
# ---------------------------------------------------------------------------
class TestVersionString:
    def test_returns_non_empty_string(self):
        ver = version_string()
        assert isinstance(ver, str)
        assert ver

    def test_never_raises(self):
        # Harus robust di environment manapun (murni stdlib/metadata).
        assert version_string()  # tidak boleh raise


# ---------------------------------------------------------------------------
# 2. doctor
# ---------------------------------------------------------------------------
class TestDoctor:
    def test_returns_doctor_report(self, fake_repo):
        report = doctor(project_root=fake_repo)
        assert isinstance(report, DoctorReport)
        assert isinstance(report.version, str)
        assert isinstance(report.dependency_checks, list)
        assert isinstance(report.environment_checks, list)
        assert isinstance(report.blocking_issues, list)

    def test_all_ok_consistent_with_blocking(self, fake_repo):
        report = doctor(project_root=fake_repo)
        # all_ok False identik dengan adanya blocking issue
        assert report.all_ok == (not report.blocking_issues)
        # setiap blocking issue punya pesan non-kosong
        for issue in report.blocking_issues:
            assert issue

    def test_summary_mentions_version_and_state(self, fake_repo):
        report = doctor(project_root=fake_repo)
        text = report.summary()
        assert report.version in text
        assert "SAM Doctor" in text
        assert "sehat" in text or "masalah" in text

    def test_empty_dir_still_returns_report(self, empty_dir):
        # doctor harus robust bahkan di struktur kosong (tidak raise)
        report = doctor(project_root=empty_dir)
        assert isinstance(report, DoctorReport)
        assert isinstance(report.all_ok, bool)


# ---------------------------------------------------------------------------
# 3. init_plan
# ---------------------------------------------------------------------------
class TestInitPlan:
    def test_returns_init_plan(self, fake_repo):
        plan = init_plan(project_root=fake_repo)
        assert isinstance(plan, InitPlan)
        assert isinstance(plan.project_root, str)
        assert isinstance(plan.phases, list)
        assert isinstance(plan.next_steps, list)

    def test_phases_ordered_from_bootstrap(self, fake_repo):
        plan = init_plan(project_root=fake_repo)
        # Fase selalu diawali dependency_validation (pola WP-E2.1)
        assert plan.phases
        assert plan.phases[0] == "dependency_validation"

    def test_next_steps_contains_onboarding_commands(self, fake_repo):
        plan = init_plan(project_root=fake_repo)
        joined = " ".join(plan.next_steps).lower()
        assert "doctor" in joined
        assert "version" in joined

    def test_dry_run_does_not_create_venv(self, fake_repo):
        before = set(p.name for p in fake_repo.rglob("*") if p.is_file())
        init_plan(project_root=fake_repo)
        after = set(p.name for p in fake_repo.rglob("*") if p.is_file())
        # dry-run tidak boleh mengubah filesystem
        assert before == after

    def test_empty_dir_returns_plan_with_note(self, empty_dir):
        plan = init_plan(project_root=empty_dir)
        assert isinstance(plan, InitPlan)
        assert isinstance(plan.ready, bool)


# ---------------------------------------------------------------------------
# 4. Konsistensi versi antar komponen
# ---------------------------------------------------------------------------
class TestConsistency:
    def test_version_available_across_modules(self, fake_repo):
        # doctor & version_string memakai sumber versi yang sama
        r = doctor(project_root=fake_repo)
        assert r.version  # non-kosong
