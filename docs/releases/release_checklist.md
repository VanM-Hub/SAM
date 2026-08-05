# Release Checklist

> **SAM v30.0.0 — Baseline Stabil (Production / Release Ready, 2026-08-06)**
> Quality gates berikut terverifikasi pada v30.0.0 pasca-engineering (L1/L2/L6, EP-001/EP-002):

---

## Status kesiapan v30.0.0 Baseline

- [x] CI GREEN (ci.yml 7/7: validation, server, desktop, core 3.10/3.11/3.12, coverage)
- [x] Regression hijau (unit + runtime_service + presentation + api + e2e + integration + runtime)
- [x] Compliance 99/99 PASS, verdict A, 0 deviation
- [x] Build reproducible (whl + tar.gz)
- [x] Repository bersih
- [x] Tidak ada implementation gap (L1 Closed, L2 Completed, L6 Completed)
- [x] Baseline Architecture stabil (tidak ada perubahan Architecture/ADR/Spec)

---

---

## 1. Pre-release

- [ ] CI GREEN (core + desktop jobs)
- [ ] Architecture Validation GREEN
- [ ] Semua validation scripts pass (imports, layers, dto, pipeline, structure, docs)
- [ ] Semua unit tests pass
- [ ] Tidak ada open issues/blockers untuk versi ini
- [ ] All subsystems documented

## 2. Version

- [ ] `pyproject.toml` → update `version = "X.Y.Z"`
- [ ] `README.md` → update versi di header + badges
- [ ] `CHANGELOG.md` → tambah entry baru dengan format:
  ```markdown
  ## vX.Y.Z (YYYY-MM-DD) - Title

  ### Added
  - ...

  ### Changed
  - ...

  ### Fixed
  - ...
  ```
- [ ] Git tag: `git tag vX.Y.Z`
- [ ] Tag pushed: `git push origin vX.Y.Z`

## 3. Documentation

- [ ] `docs/releases/version-history.md` → tambah entry versi baru
- [ ] `docs/releases/manifest.md` → update manifest
- [ ] `ROADMAP.md` → update roadmap (jika milestone tercapai)
- [ ] `SPRINT_TRACKER.md` → update sprint tracker
- [ ] `docs/history/reports/Architecture_Health.md` → update score
- [ ] `docs/history/reports/Repository_Metrics.md` → update metrics

## 4. Quality Gates

- [ ] No runtime modification
- [ ] No DTO modification
- [ ] No pipeline modification
- [ ] No behaviour change
- [ ] No forbidden imports
- [ ] No cyclic dependencies
- [ ] No layer violations
- [ ] No API break

## 5. GitHub Release

- [ ] Create release di GitHub
- [ ] Title: `vX.Y.Z — Release Title`
- [ ] Description: ringkasan perubahan dari CHANGELOG
- [ ] Attach tag yang sudah ada

## 6. Post-release

- [ ] Verify release page: `https://github.com/VanM-Hub/SAM/releases/tag/vX.Y.Z`
- [ ] Verify CI post-release (trigger re-run if needed)
- [ ] Update sprint completion report di `docs/history/sprint-reports/`
- [ ] Update `ZN_SAM/01_CURRENT_STATUS.md` dengan versi baru

## Quick Commands

```powershell
# Before release — run full validation suite
$env:PYTHONPATH = "D:\Project AI\SAM\src"
Set-Location "D:\Project AI\SAM"

python scripts/validation/validate_imports.py
python scripts/validation/validate_layers.py
python scripts/validation/validate_dto.py
python scripts/validation/validate_pipeline.py
python scripts/validation/validate_structure.py
python scripts/validation/validate_docs.py

# Full test suite
python -m pytest tests/unit/ -v --tb=short

# Tag and push
git add -A
git commit -m "Version bump to vX.Y.Z"
git tag vX.Y.Z
git push origin main --tags
```
