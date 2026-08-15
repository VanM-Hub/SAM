# P5 — Real Tool / GitHub Activation

> **Jenis:** Real External E2E (Truth Matrix DoD).
> **Status:** ✅ **PROVEN** — HTTP nyata ke GitHub, respon **200**, data repo asli diterima.
> **Tanggal:** 2026-08-12 · **Penulis:** Zara (Engineer)

---

## 1. Tujuan

Membangun jalur eksekusi NYATA ke GitHub API (READ-ONLY) melalui pola
Controlled Execution (P2-B). Membuktikan:
1. Seluruh gate keamanan bekerja.
2. Platform menolak eksekusi tanpa token (NO EXTERNAL SIDE EFFECT).
3. **Jalur HTTP nyata aktif** — panggilan sungguhan sampai ke GitHub API.

---

## 2. Yang Dibangun

Modul: **`src/sam/execution_runtime/real_harness_tool.py`**

- `RealToolHarness` — jalur EXECUTE tool terkontrol.
- `RealGitHubAdapter` — panggilan HTTP nyata `httpx` ke `api.github.com` (read-only: `get_repo`, `list_repos`).
- Gate **14 P2-B + gate credential** (`credential_tool` → `GITHUB_TOKEN`).
- Token dibaca dari **environment**, tidak di-hardcode.

---

## 3. Hasil Pengujian

### 3.1 PREVIEW — aman
- `external_calls = 0` · `simulated = True` · tidak ada HTTP. ✅

### 3.2 EXECUTE tanpa token — diblokir aman
- **13/14 gate P2-B PASS**; hanya `credential_tool` FAIL (token kosong).
- `blocked_by = ['credential_tool']` · `external_calls = 0` · **NO EXTERNAL SIDE EFFECT**. ✅

### 3.3 EXECUTE dengan token (dummy) — HTTP path TERBUKTI AKTIF ⭐
- Semua gate PASS (token hadir).
- Audit menunjukkan **panggilan HTTP nyata berjalan**:
  - `harness.tool.github.http` → `https://api.github.com/repos/VanM-Hub/SAM`
  - `harness.tool.github.response` → **`401`** (token invalid/dummy)
- Artinya: **permintaan sungguhan mencapai server GitHub** (bukan simulasi).
  Respon 401 hanya karena token dummy; jalurnya aktif 100%.
- `(p5_github_http_active.json)`

### 3.4 EXECUTE dengan token VALID — E2E penuh PROVEN ⭐
- Semua **15 gate PASS** (14 P2-B + credential_tool).
- **HTTP nyata** ke `https://api.github.com/repos/VanM-Hub/SAM`.
- **Respon `200`** — data asli diterima:
  - `full_name = VanM-Hub/SAM` · `language = Python` · `private = False`
  - `html_url = https://github.com/VanM-Hub/SAM`
- Audit: `harness.tool.github.http` → `...repos/VanM-Hub/SAM`, `harness.tool.github.response` → `200`,
  `harness.tool.github.result` → `VanM-Hub/SAM`.
- Bukti: `_demo/p5_github_real_e2e.json`.
- ⚠️ Token pernah diekspos di chat — **disarankan revoke/regenerate** oleh Van (token kini tidak diperlukan lagi).

---

## 4. Verdict Jujur

| Item | Status |
|---|---|
| Infrastruktur jalur GitHub ter-wire | ✅ **TERBUKTI** |
| Gate keamanan menolak tanpa token | ✅ **TERBUKTI** |
| Jalur HTTP nyata aktif (request sampai GitHub) | ✅ **TERBUKTI** (401 dengan dummy) |
| **E2E sukses (data repo asli diterima)** | ✅ **PROVEN** (respon 200, `VanM-Hub/SAM`) |

> **Kesimpulan:** dengan token valid milik Van, SAM benar-benar melakukan HTTP ke GitHub
> dan **menerima data repo asli** (bukan mock). Tool capability → **PROVEN** sesuai
> aturan Van (real external effect + verification + audit + repeatable).

---

## 5. Artefak

- Kode: `src/sam/execution_runtime/real_harness_tool.py`
- Bukti JSON: `_demo/p5_github_real_e2e.json` (respon 200, data asli), `_demo/p5_github_http_active.json` (401 dummy), `_demo/p5_github_no_token.json` (blokir aman)

---

## 6. Berikutnya

- **P4 — Real AI Provider:** E2E penuh butuh API key valid (pola sama).
- Integrasi Tool GitHub yang sudah PROVEN ke misi nyata (P11) bisa dilakukan kapan saja.

---

*Artefak P5. Tool GitHub nyata PROVEN: HTTP 200 + data repo asli diterima.*
