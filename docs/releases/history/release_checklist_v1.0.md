# Release Checklist — v1.0.0

**Target Date:** 2026-07-25

---

## ⬜ Pre-Release

- [ ] **All tests pass**
  ```bash
  cd src && PYTHONPATH=. pytest -q
  ```
  Expected: ~1824 passed, 0 failed, 0 errors

- [ ] **Test suite clean** (no unexpected skips)
  ```bash
  pytest -q --tb=short -rs
  ```

- [ ] **Database migrations verified**
  ```bash
  pytest test_template_evolution.py -q
  ```
  Expected: 28 passed, 0 errors

- [ ] **Backup/restore validated**
  ```bash
  python scripts/validate_backup.py ./sam.db
  ```

- [ ] **Documentation reviewed**
  - [ ] `README.md` — accurate and up-to-date
  - [ ] `docs/architecture/` — all modules covered
  - [ ] `docs/sprint-reports/` — Sprint 28–32 complete
  - [ ] `docs/operations/` — backup, disaster recovery
  - [ ] `docs/release/` — compatibility, upgrade
  - [ ] `docs/security/` — audit report

- [ ] **Compatibility matrix verified**
  - [ ] Python 3.8 tested
  - [ ] Python 3.12 tested (recommended)
  - [ ] Dependencies checked for CVEs

- [ ] **Security audit reviewed**
  - [ ] No hardcoded secrets
  - [ ] No `eval()` / `exec()` usage
  - [ ] All SQL parameterized
  - [ ] Dependencies scanned

---

## ⬜ Release Candidate

- [ ] **Version bumped** in:
  - [ ] `src/sam/__init__.py` or version module
  - [ ] `pyproject.toml`
  - [ ] `docs/release/release_checklist.md` (this file)

- [ ] **Changelog prepared**
  ```markdown
  ## v1.0.0 (2026-07-25)
  
  ### Added
  - Self-Optimization Engine (Sprint 28)
  - Cognitive Runtime (Sprint 29)
  - Cross-Cluster Intelligence (Sprint 30)
  - Knowledge Federation (Sprint 31)
  - Autonomous Runtime & Safety (Sprint 32)
  
  ### Fixed
  - Python 3.8 asyncio.to_thread compatibility
  
  ### Changed
  - All modules now follow stable API contract
  ```

- [ ] **API stability document finalized**
  - [ ] Stable exports listed
  - [ ] Deprecation policy documented

- [ ] **Release branch created**
  ```bash
  git checkout -b release/v1.0.0
  ```

---

## ⬜ Release

- [ ] **Tag created**
  ```bash
  git tag -a v1.0.0 -m "SAM Framework v1.0.0"
  git push origin v1.0.0
  ```

- [ ] **Package built**
  ```bash
  pip install build
  python -m build
  ```

- [ ] **Package uploaded** (if publishing to PyPI)
  ```bash
  twine upload dist/*
  ```

- [ ] **Release notes published**
  - [ ] GitHub Release created
  - [ ] Release notes include changelog
  - [ ] Known issues documented

---

## ⬜ Post-Release

- [ ] **Verify installed from package**
  ```bash
  pip install sam-framework
  sam --help
  sam health
  ```

- [ ] **Update main branch**
  ```bash
  git checkout main
  git merge release/v1.0.0
  git push origin main
  ```

- [ ] **Announce release**
  - [ ] Internal team notification
  - [ ] Documentation updated on website/wiki

---

*Document prepared for SAM v1.0.0 release.*
