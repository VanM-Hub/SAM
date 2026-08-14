# M13 Architecture Certification — Universal Governance of External Wards

- **Milestone:** M13 (M13-001 s/d M13-014 terbukti; **M13-015 Certification resmi**)
- **Status:** CERTIFIED (17/17 checklist M13-015 berbasis bukti nyata, 2026-08-14)
- **Order asli Van:** `ZaraNote\ZN_SAM\M13_Universal_Governance_Order.md` (disimpan dari transcript agar tak hilang)
- **Tanggal:** 2026-08-14
- **Subjek sertifikasi:** lapisan Ward (external entrusted entities) pada arsitektur tiga lapis **SAM → Wards → External World**
- **Prinsip acuan:** Clean Architecture · Repository Pattern · Connector tetap infrastructure · Domain tidak tahu infrastruktur · Registered ≠ mutation permission · Mutation selalu canonical execution + approval · Revoked Ward langsung kehilangan akses · TIDAK ada executor kedua · TIDAK duplicate capability

---

## M13-015 Architecture Certification — 17 Checklist (RESMI) — ALL PASS

| # | Checklist | Tingkat | Bukti | Hasil |
|---|---|---|---|---|
| 1 | Citizen tetap internal | A | `src/sam/citizen/**` tidak berubah; M13 hanya menambah `src/sam/ward/**`; aturan #14 non-negotiable | ✅ |
| 2 | Ward tetap external | A | `src/sam/ward/**` = model entitas eksternal (identitas + entrustment); domain tahu kontrak, bukan infra | ✅ |
| 3 | Ward tidak memiliki SAM authority | A | `as_dict()` WardIdentity hanya identitas+metadata; tidak ada method execute/restart/mutate | ✅ |
| 4 | Owner consent diperlukan | A | `WardRepository.set_entrustment`; `test_registered_ward_without_entrustment_not_authorized` | ✅ |
| 5 | Observation gunakan capability existing | A | contract `ObservationTarget` realizable Citizen/Ward; `test_observation_contract_realizable` | ✅ |
| 6 | Investigation gunakan engine existing | A | `test_investigation_reuses_contract_not_new_engine`; tidak ada ExternalInvestigationEngine | ✅ |
| 7 | Recovery gunakan canonical execution | A | governor execute butuh `canonical_executor`; `test_governor_execute_requires_canonical_executor` | ✅ |
| 8 | Learning gunakan model existing | A | `test_experience_has_subject` (Experience punya subject_id/type); tidak ada engine baru | ✅ |
| 9 | Verification gunakan existing verification | A | verifikasi recycle `verified_read`/GET issue independen; adapter read-only | ✅ |
| 10 | Tidak ada external executor kedua | A | adapter tanpa method mutate/create_issue; mutation via `run_github_real_mission` (m8_002 PROVEN) | ✅ |
| 11 | Tidak ada external capability duplicate | A | satu `WardGovernor` utk semua jenis Ward (M13-014); `test_one_engine_not_duplicated_per_ward_type` | ✅ |
| 12 | Connector tetap infrastructure adapter | A | `ward/adapters/http_observation.py` (httpx infrastructure); domain tak impor httpx | ✅ |
| 13 | Mission dapat memiliki Ward sebagai subject | A | `test_mission_has_subject`; Mission = objective+subject+observation+... | ✅ |
| 14 | Audit menyimpan Ward identity | REAL | evidence M13-013: **setiap** langkah audit punya `subject.ward_id=ward-6ac79332cfe42c2a` (7/7) | ✅ REAL |
| 15 | Evidence menyimpan Ward identity | REAL | `evidence.subject` = {ward_id, ward_type=repository, name=VanM-Hub/test-issues} + step CERTIFY_SUBJECT | ✅ REAL |
| 16 | Access dapat direvoke | A | `test_entrustment_revoked_blocks_all`; `test_boundary_revoked_blocks_observation_and_mutation` | ✅ |
| 17 | Revoked Ward tidak dapat diakses | A | `test_boundary_revoked_blocks_governor`; M13-014 `test_multi_ward_revoke_isolated` | ✅ |

**Hasil: 17/17 PASS** (A = architecture/unit-test terverifikasi; REAL = terbukti via eksekusi eksternal nyata).

---

## Ringkasan Keputusan

M13 membangun **lapisan kontrak tipis** (bukan engine baru) yang memakai ulang capability internal SAM yang sudah PROVEN (observe/investigate/diagnose/recover/learn/verify) agar menerima subjek `Citizen | Ward`. Satu `WardGovernor` + `WardGovernanceBoundary` melayani semua jenis Ward. Mutation lewat adapter ke **real_harness / m8 canonical** (single execution authority) — bukan executor kedua.

---

## Checklist Berbasis Bukti (detail)

### A. Clean Architecture & Boundary

| # | Klaim | Bukti | Hasil |
|---|---|---|---|
| A1 | Domain Ward tidak tahu GitHub / HTTP final | `ward/identity`, `entrustment`, `registry`, `governance` tidak impor httpx/requests; endpoint = konfigurasi (`base_url`/`path`) di adapter | ✅ |
| A2 | Connector tetap infrastructure | `ward/adapters/http_observation.py` memakai httpx (infrastructure), tidak di domain | ✅ |
| A3 | Register ≠ permission mutasi | `register` hanya identitas; izin di `Entrustment`/`ApprovalPolicy` | ✅ |
| A4 | Mutation hanya canonical + approval | `WardGovernor.execute` butuh `approved=True` + `canonical_executor`; tanpa approval DENIED, tanpa executor BLOCKED | ✅ |
| A5 | Revoked langsung kehilangan akses | `repo.revoke` → `can_observe`/`can_mutate` False → semua aksi BLOCKED | ✅ |
| A6 | Tidak ada executor kedua | adapter terjemahkan canonical (`run_github_real_mission` → m8_002 PROVEN); adapter tanpa mutate | ✅ |
| A7 | Tidak duplicate capability | kontrak `ObservationTarget`/`InvestigationTarget` reusable Citizen/Ward; satu governor semua jenis Ward (M13-014) | ✅ |

### B. State-flow & Honesty

| # | Klaim | Bukti | Hasil |
|---|---|---|---|
| B1 | `execute` terima recommendation dari `recommend` | harness lulus `recommendation=r.recommendation`; bila None → BLOCKED "no recommendation to execute" | ✅ |
| B2 | `investigate` reuse evidence dari `observe` | harness lulus `evidence=obs.observation.evidence`; bila kosong → fail honest "subject-unreachable" | ✅ |
| B3 | Honest BLOCKED vs fake success | execute tanpa executor → BLOCKED; observe non-200 → `verified_read=False`; http 503 → "no fake success" | ✅ |

### C. Capability Real (eksekusi nyata, bukan stub)

| # | Klaim | Bukti | Hasil |
|---|---|---|---|
| C1 | Observe real GitHub publik | M13-011: API nyata `VanM-Hub/SAM` → `subject-reachable` | ✅ REAL |
| C2 | Observe real GitHub private | M13-013: API nyata `VanM-Hub/test-issues` (private) via token → `full_name` terbaca | ✅ REAL |
| C3 | Investigate real | M13-011/012/013: `subject-reachable` dari evidence observe real | ✅ REAL |
| C4 | Mutation real + verified eksternal | M13-013: create issue **#91** di `VanM-Hub/test-issues`, read-back independen state=open | ✅ REAL |
| C5 | Token tidak bocor | M13-013: `masked: ********[len=40]`, `leak_free: true` di audit | ✅ |
| C6 | Audit tercatat dengan Ward identity | M13-013: 7/7 langkah audit punya `subject.ward_id` | ✅ REAL |
| C7 | Evidence telusur ke Ward | M13-013: `evidence.subject` = WardIdentity + step CERTIFY_SUBJECT | ✅ REAL |
| C8 | Learn dengan subject | experience `subject_type=ward` direkam | ✅ |

### D. Multi-Ward Generalization (M13-014)

| Klaim | Bukti | Hasil |
|---|---|---|
| Satu governor utk banyak jenis Ward (repository/external_api/process/database/container) | `test_multi_ward_one_engine_all_observable`; reuse `WardGovernor` | ✅ |
| Revoke terisolasi per-Ward (tidak domino) | `test_multi_ward_revoke_isolated` | ✅ |
| Failure satu Ward tidak menjatuhkan yang lain | `test_multi_ward_failure_not_universal` | ✅ |
| Same capability, different adapter (bukan engine beda) | `test_multi_ward_same_capability_different_adapter` | ✅ |

---

## Hasil Eksekusi Real

| Run | Target | Hasil | Verdict |
|---|---|---|---|
| M13-011/012 | `VanM-Hub/SAM` (publik) | register→observe→investigate→report, tanpa mutation | **PASS** (exit 0) |
| M13-013 | `VanM-Hub/test-issues` (private) | register→observe→investigate→recommend→approve→**EXECUTE issue →verify eksternal→learn | **PASS** (exit 0) |

Bukti mutasi nyata M13-013 (multiple run, issue berbeda tiap run — efek flow protect, bukan bug):
- Issue **#89** → https://github.com/VanM-Hub/test-issues/issues/89 (state=open)
- Issue **#91** (final certified run) → https://github.com/VanM-Hub/test-issues/issues/91 (state=open)

Catatan jujur: tiap re-run harness membuat issue baru (create_issue = proteksi imperatif, bukan idempotent business). Ini sesuai desain flow protect, tapi penting untuk dicatat — bukan klaim idempotency.

## Test Suite

- `tests/ward/test_m13_001_003_010.py` — foundation (21)
- `tests/ward/test_m13_004_010.py` — contracts + governor + boundary (15)
- `tests/ward/test_m13_013_http_header_env.py` — adapter env fallback (6)
- `tests/ward/test_m13_014_multi_ward.py` — multi-Ward generalization (5)
- **Total: 47 test ward PASS**

---

## Gap & Catatan Jujur

1. **M13-016 / M13-017 belum dirinci** dalam order yang Van berikan (hanya M13-001..015 dirinci). Dokumen ini belum menilai keduanya; keduanya menunggu arahan Van.
2. **Satu regression test `test_ux_runner_connectors::test_http_endpoint_routes_to_http_readonly` merah** karena **httpbin.org sedang HTTP 503** (server eksternal down) — perilaku harness benar (honest fail "no fake success"), **bukan regresi kode M13**.
3. **Mutation M13-013 memakai repo private `VanM-Hub/test-issues`** milik Van (repo TEST, bukan produksi) — sesuai prinsip M13 dan pola M8/M9.
4. **Token GitHub dibaca dari file yang Van tunjuk** (`Tokken GitHub.txt`), di-set via env di SAME exec, tidak pernah ditampilkan/di-commit; di audit di-mask `********[len=40]`.

---

## Verdict

M13 arsitektur Ward + external governance **CERTIFIED 17/17** berbasis bukti kode + 47 test ward + real external E2E (observe/investigate GitHub publik & private, protect/create issue nyata terverifikasi eksternal). SAM kini punya satu semantic governance engine untuk subject `Citizen | Ward`, tanpa executor kedua, tanpa duplikasi capability, tanpa authority leakage. Tercapai "mata ke dunia luar + tangan terkendali" sesuai tujuan M13.

---

## Rekomendasi

- Tentukan scope resmi M13-016/017 (belum ada arahan).
- Ganti harness `--title` agar unik per run bila ingin idempotent (opsional, bukan requirement).
- Update 5 file publik (README, pyproject, CHANGELOG, ROADMAP, ATLAS) untuk mencerminkan M13 selesai.
