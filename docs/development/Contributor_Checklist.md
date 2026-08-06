# Contributor Checklist

> **SAM 1.0 Foundation** - Wajib dicek SEBELUM merge ke main.

---

## 1. API

- [ ] Tidak mengubah public API (`__all__`, bridge signatures)
- [ ] Jika API baru: tambah ke `__init__.py` → `__all__`
- [ ] Jika API diubah: update `docs/architecture/Public_API.md`
- [ ] Bridge baru? Tambah Conversation + Dashboard pair

## 2. Tests

- [ ] Test baru ditambahkan untuk perubahan
- [ ] Semua test PASS: `python -m pytest tests/unit/ -v --tb=short`
- [ ] Tidak ada test yang bergantung pada network
- [ ] Tidak ada test yang menggunakan async/thread

## 3. Documentation

- [ ] README.md — update versi/fitur jika perlu
- [ ] CHANGELOG.md — tambah entry dengan format yang konsisten
- [ ] Jika arsitektur berubah: update docs/architecture/
- [ ] Jika pipeline berubah: update Pipeline_Specification.md

## 4. Dependencies

- [ ] Tidak ada import forbidden (`asyncio`, `threading`, `socket`, `requests`)
- [ ] Tidak ada cross-runtime import (Guardian → Decision langsung)
- [ ] Tidak ada cyclic dependency
- [ ] Jalankan `python scripts/validation/validate_imports.py` — harus 0 violations

## 5. DTO

- [ ] Semua DTO baru adalah `@dataclass(frozen=True)`
- [ ] Tidak ada mutable default value
- [ ] Tidak ada method `process()`, `execute()`, `run()` di DTO
- [ ] Jalankan `python scripts/validation/validate_dto.py` — harus pass

## 6. CI

- [ ] Workflow CI GREEN (core job + desktop job)
- [ ] Workflow CI menjalankan validation scripts
- [ ] Architecture Validation stage GREEN

## 7. ADR

- [ ] Perubahan arsitektur signifikan? Buat ADR baru
- [ ] ADR disimpan di `docs/adr/ADR-NNN_*.md`
- [ ] ADR menyertakan: Context, Decision, Consequences

## 8. Linting & Structure

- [ ] Ruff linting: `python -m ruff check src/sam/`
- [ ] Tidak ada file dengan huruf besar (snake_case wajib)
- [ ] Naming convention sesuai Architecture Rulebook
- [ ] Jalankan `python scripts/validation/validate_structure.py`

## 9. Breaking Changes

- [ ] Jika ada breaking change: tulis di CHANGELOG
- [ ] Update versi minor (vX.Y+1.Z) untuk backward-compatible changes
- [ ] Update versi major (vX+1.Y.Z) untuk breaking changes

## 10. Final Pre-merge

- [ ] Semua validation scripts pass
- [ ] Semua test pass
- [ ] Semua docs up-to-date
- [ ] Git tag sesuai versi
- [ ] Push ke origin, CI GREEN
