# Pull Request Template — SAM Architecture Locked

## Description

<!-- Jelaskan perubahan secara singkat -->

Closes #ISSUE_NUMBER

## Type of Change

- [ ] Bugfix (non-breaking, fixes issue)
- [ ] Feature (non-breaking, adds capability)
- [ ] Breaking change (existing functionality breaks)
- [ ] Documentation (no code changes)
- [ ] Governance/Validation (scripts, CI, checklists)
- [ ] Architecture (README, ADR)

## Architecture

- [ ] Tidak mengubah runtime behavior
- [ ] Tidak mengubah pipeline
- [ ] Tidak mengubah DTO
- [ ] Semua komunikasi tetap via bridge DTO
- [ ] Tidak ada cross-runtime import baru

## Tests

- [ ] All tests pass: `python -m pytest tests/unit/ -v --tb=short`
- [ ] New tests added for new code

## CI

- [ ] Core job GREEN
- [ ] Desktop job GREEN
- [ ] Architecture Validation stage GREEN
- [ ] All validation scripts pass:
  ```powershell
  python scripts/validation/validate_imports.py
  python scripts/validation/validate_layers.py
  python scripts/validation/validate_dto.py
  python scripts/validation/validate_pipeline.py
  python scripts/validation/validate_structure.py
  python scripts/validation/validate_docs.py
  ```

## Documentation

- [ ] README.md updated (if needed)
- [ ] CHANGELOG.md updated
- [ ] `docs/architecture/` updated (if architecture changed)
- [ ] ADR created (if significant architectural decision)

## Breaking Changes

- [ ] No breaking changes
- [ ] Breaking changes documented in CHANGELOG

## Dependencies

- [ ] No forbidden imports
- [ ] No cyclic dependencies
- [ ] Dependency map updated (if new dependencies added)

## Checklist (wajib isi)

- [ ] Saya sudah menjalankan validation scripts
- [ ] Saya sudah menjalankan test suite
- [ ] Saya sudah update dokumentasi yang relevan
- [ ] PR ini siap di-merge
