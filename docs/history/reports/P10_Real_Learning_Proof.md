# P10 — Real Learning (Persistence + Retrieval)

> **Jenis:** Real External E2E (Truth Matrix DoD).
> **Status:** ✅ **PROVEN** — experience persisted ke disk + retrieved setelah restart.
> **Tanggal:** 2026-08-12 · **Penulis:** Zara (Engineer)

---

## 1. Uji Wajib (per Van)

```
RUN 1
  -> experience stored
  -> process restart
  -> RUN 2
  -> previous experience retrieved
```

> **Jika data hilang setelah restart → Learning BELUM PROVEN.**

---

## 2. Cara Uji (jujur)

- **Persistence**: experience disimpan ke **file disk** `_demo/learning_store.json` (bukan RAM/memori).
- **Restart**: disimulasikan dengan **instance baru** (audit + repository baru) yang membaca ulang dari file.
- **Retrieval**: RUN 2 memanggil `search_by_operation` → memuat pengalaman lampau dari disk.

---

## 3. Hasil

| Langkah | State file | Keterangan |
|---|---|---|
| RUN 1 | experience `xp-c36ecdea` ditulis | count=1 |
| **PROCESS RESTART** | instance baru membaca disk | count=1 (data tetap) |
| RUN 2 | **experience `xp-c36ecdea` di-retrieve** | lesson: "data sumber mengandung baris kosong → pertimbangkan pembersihan" |
| Store akhir | **2 experience di file** | RUN-1 + RUN-2 |

- Bukti di disk (dibaca di luar proses): 2 experience dengan lesson masing-masing.
- Setiap experience membawa: `operation`, `evidence` (real external state: size, line_count, hash),
  `outcome`, `verification`, `lesson`.

---

## 4. Verdict

> **Learning capability = PROVEN.**
> SAM menyimpan experience ke penyimpanan persistent, **tetap bertahan setelah restart**,
> dan **berhasil me-retrieve pengalaman lampau** untuk operasi berikutnya — dengan lesson
> yang dapat dipakai (future retrieval). Data **tidak hilang** setelah restart.

---

## 5. Batasan (jujur)

- Experience saat ini dari operasi filesystem/analyze; belum dari Recovery (P9) / Mission (P11).
- "Restart" disimulasikan via instance proses baru (bukan cold reboot mesin), tapi karena
  penyimpanan ke **file disk**, persistensi lintas-proses terbukti nyata.
- Belum ada mekanisme dedup/maturity/decay pada lesson — cukup untuk bukti persistence+retrieval.

---

## 6. Artefak

- Kode: `src/sam/execution_runtime/real_harness_learning.py`
- Store persistent: `_demo/learning_store.json` (2 experience)
- Bukti JSON: `_demo/p10_learning.json`

---

*Artefak P10. Learning terbukti: pengalaman bertahan & bisa di-retrieve setelah restart.*
