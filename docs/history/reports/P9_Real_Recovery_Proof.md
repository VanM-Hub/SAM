# P9 — Real Recovery

> **Jenis:** Real External E2E (Truth Matrix DoD).
> **Status:** ✅ **PROVEN** — state eksternal berubah NYATA + diverifikasi independen.
> **Tanggal:** 2026-08-12 · **Penulis:** Zara (Engineer)

---

## 1. Prinsip Kunci (per Van)

> **`success=True` TIDAK pernah dianggap bukti recovery.**
> Bukti harus **perubahan state eksternal yang diverifikasi** secara independen.

---

## 2. Skenario

"Service" nyata berbasis file di sandbox `_demo/recovery_sandbox/` (reversible, terisolasi):
- `svc-orders.state` — status service (`running` / `stopped`)
- `svc-orders.health` — health check (`ok` / `fail`)

| Tahap | State file | Health file |
|---|---|---|
| 1. Healthy State | `running` | `ok` |
| 2. Inject Failure | `stopped` | `fail` |
| 3. SAM Detects | anomaly=True | — |
| 4. Recommend | `start` | — |
| 5. Approval | approved=True | — |
| 6. REAL Recovery Action | **tulis `running`** | **tulis `ok`** |
| 7. State Change (NAYATA di disk) | `'stopped' → 'running' changed=True` | — |
| 8. Independent Health Check | `running` | `ok` → **healthy=True** |

---

## 3. Bukti (bukan flag)

- **Perubahan state nyata di disk**: content file `svc-orders.state` berubah dari `stopped` → `running`
  (diverifikasi dengan membaca ulang file `running`).
- **Independent verification**: `independent_health_check` membaca **langsung dari disk**
  `svc-orders.state` & `svc-orders.health` → `state=running`, `health=ok`, `healthy=True`.
- Verified terpisah dari proses eksekusi (baca langsung file system).

---

## 4. Verdict

> **Recovery capability = PROVEN.**
> SAM mendeteksi failure dari state eksternal nyata, merekomendasikan `start`, mendapat approval,
> melakukan **aksi recovery yang mengubah state file di disk**, dan **memverifikasi healthy state
> secara independen**. Ini adalah bukti perubahan state, bukan flag `success=True`.

---

## 5. Batasan (jujur)

- "Service" saat ini adalah file-status tiruan di sandbox (bukan process/systemd/service nyata).
  Konsep & bukti state-change + independent verification **persis sama** dan bisa dipindah ke
  service nyata (mis. start/stop daemon) tanpa mengubah logika.
- Recovery action saat ini hanya `start`; tidak ada rollback kondisi lebih kompleks.
- Belum terhubung ke Learning (P10) & Mission (P11) satu rantai.

---

## 6. Artefak

- Kode: `src/sam/execution_runtime/real_harness_recovery.py`
- State nyata: `_demo/recovery_sandbox/svc-orders.state` (`running`), `svc-orders.health` (`ok`)
- Bukti JSON: `_demo/p9_recovery.json`

---

*Artefak P9. Recovery terbukti lewat perubahan state nyata + verifikasi independen, bukan flag.*
