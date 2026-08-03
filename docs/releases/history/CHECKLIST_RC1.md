# RC1 Release Checklist

**Tanggal:** 2026-07-25  
**Target:** SAM Framework v1.0.0-rc1

---

## ✅ Sebelum Tagging

- [x] Semua test lulus (~1824+ passed)
- [x] Tidak ada regresi
- [x] Semua migration (001–047) diterapkan
- [x] Semua artefak diverifikasi (15 root files, 24 modules, 16 docs folders, 80 capability files)
- [x] Dokumen final lengkap:
  - [x] ADRs (14 keputusan arsitektur)
  - [x] Architecture Freeze
  - [x] RFC Process
  - [x] 3 audit (architecture, contracts, documentation)
  - [x] Compatibility matrix, upgrade path
  - [x] Backup/restore validation script
  - [x] Disaster recovery procedures
  - [x] Performance benchmark
  - [x] Security audit
  - [x] API stability & deprecation policy
- [x] Tidak ada file kritis yang hilang
- [x] Migration 037 (evolutionary architecture) dibuat untuk mengisi gap

## ✅ Saat Tagging

- [x] Semua perubahan terakhir di-commit
- [x] Commit message: `chore: finalize v1.0.0-rc1 — all artifacts verified, docs complete`
- [x] Tag `v1.0.0-rc1` dibuat dengan anotasi
- [x] Tag mengarah ke commit yang benar (23aee8c)
- [x] Release notes (`docs/release/v1.0_release_notes.md`) diperiksa
- [x] Checklist ini dibuat (`docs/release/CHECKLIST_RC1.md`)

## ⏳ Setelah Tagging (Untuk RC1 Validation)

- [ ] Fresh install dari source
  ```bash
  git clone https://github.com/your-org/sam.git
  cd sam
  pip install -e .
  ```
- [ ] Migration berjalan
  ```bash
  sam daemon migrate
  ```
- [ ] CLI help berfungsi
  ```bash
  sam --help
  ```
- [ ] Health check berfungsi
  ```bash
  sam health
  ```
- [ ] Plugin loading berhasil
- [ ] Workflow dasar berjalan
- [ ] Cognitif functions berfungsi (state, attention, arbitration)
- [ ] Autonomy commands berfungsi
  ```bash
  sam autonomy status
  sam autonomy set supervise
  ```
- [ ] Evolution commands berfungsi
  ```bash
  sam evolution list
  ```
- [ ] Cluster commands berfungsi
  ```bash
  sam cluster status
  ```
- [ ] Federation commands berfungsi
  ```bash
  sam federation status
  ```
- [ ] Backup/restore terverifikasi
  ```bash
  python scripts/validate_backup.py ./sam.db
  ```
- [ ] Soak test (opsional untuk RC1, wajib untuk RC2)

## 📌 Catatan Penting

1. **RC1 adalah versi pratinjau.** Rilis final v1.0.0 akan menyusul setelah validasi RC1–RC3.
2. **Push tag ke remote** dilakukan oleh Van setelah review.
3. **Branch saat ini:** `feature/sprint13-plugin-runtime` — akan di-merge ke `main` sebelum rilis final.
4. **Dokumentasi tambahan** mungkin diperlukan untuk RC2 berdasarkan feedback dari validasi.

---

*Checklist prepared for SAM v1.0.0-rc1.*
