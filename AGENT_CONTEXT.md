# SAM Framework — Agent Operating Context

> File ini adalah **sumber kebenaran** untuk agen AI (ZARA atau agen lain) yang bekerja pada proyek SAM Framework.  
> **Baca file ini UTUH sebelum memulai tugas apa pun.**  
> Setiap ada perubahan konteks/perintah baru dari Axel/Aster/Van, **update file ini.**

---

## 1. IDENTITAS PROYEK

| Atribut | Nilai |
|---|---|
| Nama | SAM Framework (System Administration Manager) |
| Versi | v1.0.0 (release 2026-07-25) |
| Status | ✅ Released. Sekarang: **RC2 validation** |
| Repo | `https://github.com/VanM-Hub/SAM` (public) |
| Path Lokal | `D:\Project AI\SAM\` |
| Branch | `feature/sprint13-plugin-runtime` (sudah di-merge ke `main`) |
| Tag | `v1.0.0` (release final), `v1.0.0-rc1` (RC lama) |
| Python | **3.8.7** (wajib — gunakan ini, jangan asumsi 3.12) |
| Shell | **PowerShell** (bukan cmd — `&&` tidak jalan) |

---

## 2. PERINTAH TERAKHIR (Dari Axel / Aster)

**Dari:** Aster (via Van)  
**Tanggal:** 2026-07-25  
**Perintah:** "Lanjut ke RC2 — focus: cross-platform Linux testing + failure injection scenarios"  

**Konversi ke task:**
1. [ ] Siapkan environment Linux (atau dokumentasikan langkah-langkah untuk dijalankan Van)
2. [ ] Jalankan fresh installation di Linux (manual oleh Van, ZARA bantu dokumentasi)
3. [ ] Failure injection: plugin rusak, workflow invalid, migration gagal, DB terkunci, config hilang
4. [ ] Buat laporan RC2

---

## 3. SIAPA BERPERAN APA

| Peran | Orang | Tanggung Jawab |
|---|---|---|
| **Chief Architect** | Aster | Review arsitektur, keputusan desain besar, standar teknis |
| **Lead Engineer** | Axel | Arah teknis harian, prioritas fitur, review implementasi |
| **Lead Assistant** | ZARA | Implementasi kode, debug, test, dokumentasi, laporan |
| **Project Manager** | Van | Tujuan, prioritas, keputusan akhir, rilis |

**Aturan komunikasi:**
- Jika pertanyaan datang dari **Axel** atau **Aster**, selalu cantumkan `ZARA di Bawah` di akhir pesan.
- Jika Van yang ngomong langsung, panggil "Van" saja.

---

## 4. ARSITEKTUR CEPAT

### Layer (dari bawah ke atas):
```
Infrastructure  → plugin, events, messaging
Persistence     → database (sqlite3), migrations (001-047)
Domain          → cognition, healing, evolution, tuning, autonomy, cluster, federation, governance
Application     → runtime, services, capabilities
CLI             → main.py + sub-apps
```

### Semua Modul (24 total):

| Modul | Path | Fungsi | Public API |
|---|---|---|---|
| `cognition` | `src/sam/cognition/` | Cognitive state, working memory, attention, arbitration, context, session | ✅ 18 items |
| `healing` | `src/sam/healing/` | 9-phase self-healing loop | ✅ 6 items |
| `evolution` | `src/sam/evolution/` | Policy, optimizer, params | ✅ 8 items |
| `tuning` | `src/sam/tuning/` | Autotuner, metrics collector | ✅ 4 items |
| `autonomy` | `src/sam/autonomy/` | 5-level autonomy, safety, guardrails, escalation, degradation, assessment | ✅ 10 items |
| `cluster` | `src/sam/cluster/` | Knowledge share, insight broker, strategy sync, cognitive state | ✅ 10 items |
| `federation` | `src/sam/federation/` | Manager, protocol, trust, conflict, provenance, consensus, sovereignty | ✅ 14 items |
| `governance` | `src/sam/governance/` | 7 evaluators, engine | ✅ 5 items |
| `cli` | `src/sam/cli/` | 10 sub-apps | ✅ 10 commands |
| `runtime` | `src/sam/runtime/` | Registry, discovery, runtime | Internal |
| `persistence` | `src/sam/persistence/` | Database, migrations, repositories | Internal |
| `plugin` | `src/sam/plugin/` | Manifest, loader, registry, lifecycle | Internal |

---

## 5. DOKUMEN KUNCI

| File | Isi | Wajib Dibaca? |
|---|---|---|
| `README.md` | Gambaran proyek, fitur, instalasi | ✅ |
| `docs/release/v1.0_release_notes.md` | Release notes lengkap 33 sprint | ✅ |
| `docs/release/ARCHITECTURE_FREEZE.md` | Kontrak yang dibekukan | ✅ Sebelum ubah API |
| `docs/development/api_stability.md` | API mana yang stabil/eksperimental/internal | ✅ Sebelum ubah public API |
| `docs/development/RFC_PROCESS.md` | Tata kelola perubahan setelah v1.0 | ✅ Sebelum tambah fitur besar |
| `docs/audit/public_contracts.md` | Daftar lengkap public contracts | ✅ Referensi |
| `docs/architecture/ARCHITECTURAL_DECISIONS.md` | 14 ADRs — alasan keputusan arsitektur | ✅ Referensi |
| `pyproject.toml` | Dependencies, packaging | ✅ |
| `CONTRIBUTING.md` | Panduan kontribusi | ✅ |

---

## 6. ALUR KERJA W AJIB (Jangan Dilewati!)

### Alur Edit VBA (khusus proyek PDIP LUTIM — bukan SAM):
> **Hanya relevan jika Van minta bantuan VBA. Jangan lakukan untuk SAM.**

1. Edit file `.txt` di `D:\MyProjectApps\Aplikasi_PDIP_LUTIM\VBA_Modules\` SAJA
2. Van paste manual ke Macro Editor
3. Van tutup Excel
4. Jalankan `Sync_VBA.bat` (export .xlsm → .frm/.bas ke repo + push)
5. JANGAN edit `.frm`/`.bas` repo

### Alur Kerja SAM:
1. **Edit** file source di `src/sam/` atau `tests/`
2. **Test** dengan:
   ```powershell
   $env:PYTHONPATH="D:\Project AI\SAM\src"
   python -m pytest tests/test_xxx.py -v --tb=short
   ```
3. **Commit** dengan format:
   ```
   <type>(<scope>): <description>
   Contoh: feat(sprint29): Cognitive Runtime - Working Memory
           fix(database): relative path bug in Database.__init__
           chore(sprint33): Production readiness docs
   ```
4. **Push** (hanya Van yang bisa):
   ```powershell
   git push origin feature/sprint13-plugin-runtime
   ```

### Aturan Emas:
- **JANGAN** edit `pyproject.toml` dependencies tanpa konfirmasi
- **JANGAN** ubah public API tanpa RFC Process
- **JANGAN** hapus migration yang sudah ada
- **KONFIRMASI** dulu sebelum aksi berisiko/destruktif/eksternal
- **Gunakan PowerShell**, bukan cmd (perhatikan `&&` tidak jalan)

---

## 7. TESTING

| Perintah | Kegunaan |
|---|---|
| `python -m pytest tests/test_xxx.py -q` | Test 1 file |
| `python -m pytest tests/ -q` | Semua test di folder tests/ |
| `python -m pytest -q --tb=short` | Semua test (short traceback) |
| **WAJIB** `$env:PYTHONPATH="D:\Project AI\SAM\src"` | **Set before every pytest run!** |

### Test Files per Sprint:

| Sprint | File | Jumlah Test |
|---|---|---|
| 28 | `test_policy.py, test_reflection.py, test_confidence.py, test_healing_loop.py, test_proposal_lifecycle.py, test_metrics.py, test_autotuner.py` | ~140 |
| 29 | `test_cognitive_state.py, test_working_memory.py, test_cognitive_manager.py, test_attention.py, test_arbitration.py, test_context.py, test_session.py` | ~249 |
| 30 | `test_cluster_intelligence.py` | ~62 |
| 31 | `test_federation.py` | ~56 |
| 32 | `test_autonomy.py` | ~68 |
| 33 | — (dokumentasi) | — |

---

## 8. PRIORITAS MENDATANG

| Sprint / Rilis | Target | Detail |
|---|---|---|
| **RC2** | Cross-platform + Failure injection | Testing di Linux, simulasi kegagalan |
| **RC3** | Soak test + Performance tuning | Extended runtime, benchmark final |
| **v1.0.0 final** | Production release | — |
| **v1.1** | REST API + Web Dashboard | Network endpoint, GUI |
| **v1.2** | PostgreSQL | Multi-writer, production DB |

---

## 9. COMMIT PALING AKHIR

```
11b05df chore: RC1 validation — 559 tests passed, 3 bugs fixed
```

---

## 10. MASALAH YANG DIKETAHUI (Known Issues)

| Issue | Status | Workaround |
|---|---|---|
| Python 3.8 `asyncio.to_thread` | ✅ Fixed (polyfill di `database.py`) | — |
| `sam cluster status` butuh DB | 🟡 Minor | Butuh setup infrastruktur cluster |
| Pydantic V2 deprecation warnings (69) | 🟡 Cosmetic | Ignore; tidak pengaruh fungsional |
| **Current:** `test_session.py::test_list_sessions` flaky | ✅ Fixed | Sorting by timestamp |

---

> **Update file ini SETIAP KALI ada perintah baru dari Axel/Aster atau perubahan status proyek.**  
> Ini adalah **single source of truth** untuk agent context.
