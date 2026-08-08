# EA-003-003 — Runtime Dependency Promotion Plan (Program B)

**Program:** MISSION-2B / Program B · **Package:** EA-003 · **WP:** WP-03 Runtime Dependency Promotion Plan
**Mode:** Planning (blueprint, read-only) · **Authority:** Lead Engineer · **Tanggal:** 2026-08-08
**Aturan:** tidak ada dependency baru · tidak ada perubahan dependency · hanya urutan realisasi.

---

## 1. Prinsip

BA_YANG dependency EA-001 **tidak diubah** (11 runtime independen; Runtime Service orchestrator ke 7). EA-003 hanya menyusun **urutan aktivasi realisasi** agar runtime yang menjadi dependensi dicapai readiness dulu.

## 2. Dependency Activation Order

Urutan realisasi mengikuti arah dependency (dependent pertama kali dimatangkan setelah dependensinya siap):

| Order | Runtime | Prerequisite (dipromosikan dulu) | Alasan |
|---|---|---|---|
| 1 | **Memory** | — (independen) | dependensi Knowledge/Product: bridge harus matur |
| 2 | **Artifact** | — (independen) | penyimpanan artefak dasar |
| 3 | **Audit** | — (independen) | rekam jejak immutable dasar |
| 4 | **Policy** | — (independen) | aturan governan |
| 5 | **Workflow** | — (independen) | alur kerja |
| 6 | **Mission** | — (independen) | discovery/lifecycle |
| 7 | **Knowledge** | Memory (1) | konsumen memory bridge |
| 8 | **Registry** | — (kernel) | fasilitas kernel |
| 9 | **Execution** | Registry, Kernel | eksekusi perlu kernel |
| 10 | **Approval** | Registry, Execution | gate approval perlu eksekusi |
| 11 | **Provider** | Secret (eksternal-internal) | network perlu secret |
| 12 | **Runtime Service** | semua di atas (orchestrator) | penilai teratas |

## 3. Verification Order

Verifikasi dilakukan dari dependensi ke dependee:
1. Memory → 2. Artifact → 3. Audit → 4. Policy → 5. Workflow → 6. Mission → 7. Knowledge → 8. Registry → 9. Execution → 10. Approval → 11. Provider → 12. Runtime Service.

> Verification order = urutan yang sama seperti activation (DAG hasilkan topologi).

## 4. Rollback Dependency

| Skema Rollback | Keterangan |
|---|---|
| Per-runtime reversibel | Setiap promotion bisa di-rollback ke status Preview tanpa dampak runtime yang belum bergantung padanya |
| Runtime Service = last | Karena orchestrator bergantung semua, rollback dimulai dari RS dulu, lalu runtime leaf |
| Penyimpanan state | Memastikan setiap activation menyimpan snapshot state readiness (input EA-004) |

## 5. Validasi
- **Tidak ada dependency baru** ✅ (memakai graph EA-001-004 yang sama).
- **Tidak ada perubahan dependency** ✅ (hanya urutan, bukan modifikasi).
- **Tidak ada sirkular** ✅ (urutan topologis valid, DAG asiklik).
- **Hanya urutan realisasi** ✅.

## 6. Kesimpulan
- Urutan aktivasi & verifikasi 12 runtime telah ditetapkan secara topologis tanpa mengubah dependency.
- Rollback per-runtime reversibel; Runtime Service agent terakhir.

---

*— Akhir EA-003-003 —*
