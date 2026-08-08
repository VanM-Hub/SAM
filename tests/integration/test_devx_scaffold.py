"""Test evidence untuk WP-E2.4 E5-G1 Starter Project scaffold.

Sasaran: `sam.devx.scaffold` - membuat starter project SAM baru
(Mission + Workflow + Runtime minimum + pyproject + package).

Scope test:
- build_files menghasilkan struktur lengkap & valid.
- Dry-run (default) TIDAK menulis apa pun ke disk.
- apply=True menulis file dengan konten yang benar.
- Idempotent: apply dua kali tidak menimpa / tidak error.
- Validasi nama & target (ValueError).
- Konten YAML mission/workflow valid & berisi bagian inti.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from sam.devx.scaffold import build_files, scaffold_project


class TestBuildFiles:
    def test_generates_complete_structure(self):
        files = build_files("myapp", "0.1.0")
        assert "pyproject.toml" in files
        assert "README.md" in files
        assert "mission.yaml" in files
        assert "workflow.yaml" in files
        # package + subpackage (mission/workflow/runtime)
        src = [k for k in files if k.startswith("src/")]
        assert any("__init__.py" in k for k in src)
        assert any("/mission/" in k for k in src)
        assert any("/workflow/" in k for k in src)
        assert any("/runtime/" in k for k in src)

    def test_package_name_uses_underscore_for_dash(self):
        files = build_files("my-app", "0.1.0")
        assert any("src/my_app/__init__.py" == k for k in files)

    def test_pyproject_contains_name_and_dependency(self):
        files = build_files("sam-demo", "0.1.0")
        py = files["pyproject.toml"]
        assert 'name = "sam-demo"' in py
        assert "sam-ops>=1.0.0" in py
        assert 'where = ["src"]' in py

    def test_mission_yaml_has_name_and_objectives(self):
        files = build_files("demo", "0.1.0")
        m = files["mission.yaml"]
        assert "demo-mission" in m
        assert "objectives:" in m

    def test_workflow_yaml_has_steps_and_transition(self):
        files = build_files("demo", "0.1.0")
        w = files["workflow.yaml"]
        assert "hello-demo" in w
        assert "steps:" in w
        assert "transition:" in w
        assert "on_success" in w


class TestScaffoldDryRun:
    def test_default_is_dry_run_and_writes_nothing(self, tmp_path: Path):
        target = tmp_path / "out"
        result = scaffold_project("demo", target_dir=target)
        assert result.dry_run is True
        assert result.ok is True
        assert result.validated is True
        assert result.created  # daftar file "akan dibuat"
        # tidak ada yang tertulis
        assert not target.exists()

    def test_dry_run_does_not_create_parent(self, tmp_path: Path):
        target = tmp_path / "nonexistent" / "out"
        result = scaffold_project("demo", target_dir=target)
        assert result.dry_run
        assert not target.exists()


class TestScaffoldApply:
    def test_apply_writes_files(self, tmp_path: Path):
        target = tmp_path / "out"
        result = scaffold_project("demo", target_dir=target, apply=True)
        assert result.dry_run is False
        assert (target / "pyproject.toml").exists()
        assert (target / "mission.yaml").exists()
        assert (target / "workflow.yaml").exists()
        assert (target / "README.md").exists()
        pkg = target / "src" / "demo"
        assert (pkg / "__init__.py").exists()
        assert (pkg / "mission" / "__init__.py").exists()
        assert (pkg / "workflow" / "__init__.py").exists()
        assert (pkg / "runtime" / "__init__.py").exists()

    def test_apply_is_idempotent(self, tmp_path: Path):
        target = tmp_path / "out"
        first = scaffold_project("demo", target_dir=target, apply=True)
        created = len(first.created)
        second = scaffold_project("demo", target_dir=target, apply=True)
        # detik: semua dilewati (sudah ada), tidak ada yang dibuat baru
        assert second.created == []
        assert len(second.skipped) == created

    def test_apply_content_correct(self, tmp_path: Path):
        target = tmp_path / "out"
        scaffold_project("demo", target_dir=target, apply=True)
        txt = (target / "pyproject.toml").read_text(encoding="utf-8")
        assert 'name = "demo"' in txt
        mission = (target / "mission.yaml").read_text(encoding="utf-8")
        assert "demo-mission" in mission


class TestValidation:
    def test_invalid_name_raises(self):
        with pytest.raises(ValueError):
            scaffold_project("Bad Name!", apply=False)
        with pytest.raises(ValueError):
            scaffold_project("", apply=False)

    def test_target_is_file_raises(self, tmp_path: Path):
        f = tmp_path / "afile"
        f.write_text("x")
        with pytest.raises(ValueError):
            scaffold_project("demo", target_dir=f)

    def test_empty_name_rejected(self):
        with pytest.raises(ValueError):
            scaffold_project("   ", apply=False)


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
