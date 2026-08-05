# L6 — Engineering Exploration Report

**Tanggal:** 2026-08-06
**Status:** Explorasi lanjutan (per arahan Lead Engineer — jangan asumsi hanya 2 solusi).

## Invariant yang harus dipertahankan (semua)
- Registry tetap immutable.
- Ownership tetap.
- Lifecycle tetap.
- Runtime Model tetap.
- Audit terminal observer.
- Tidak ada feedback.
- Tidak ada Runtime Unit baru.
- Tidak ada perubahan Responsibility.

## Fakta kode (konteks)
- `AuditRegistry` immutable (`@dataclass(frozen=True)`, `register()` → instance baru).
- `AuditPreviewConsumer` & `ConversationAuditBridge` mengikat `self._registry` tetap di `__init__` (tidak ada setter/accessor).
- **Belum ada endpoint `/audit` di web** — `audit_consumer` diinstansiasi (Session 09) tapi belum ada jalur yang menampilkan record audit di web saat ini.

## Daftar pendekatan yang dievaluasi

### A. Rebuild consumer per preview
- **Deskripsi:** setelah tiap preview, rekonstruksi `AuditPreviewConsumer(registry=hasil_register)`.
- **Invariant:** registry immutable ✓; audit terminal ✓; no feedback ✓.
- **Diterima/ditolak:** **Ditolak** — merecreate consumer tiap preview mengubah ownership/lifecycle wira & wiring; dilarang arahan.

### B. Shared mutable registry
- **Deskripsi:** jadikan registry mutable agar semua instance melihat record.
- **Invariant:** registry immutable ✗.
- **Diterima/ditolak:** **Ditolak** — melanggar invariant immutable.

### C. Holder referensi registry di Composition Root/Entry (BARU)
- **Deskripsi:** entry (Composition Root) memegang *variabel referensi* ke `AuditRegistry` yang dapat diperbarui ke instance hasil `register()` (registry objeknya tetap immutable; hanya referensi di lapisan wiring yang di-swap). Endpoint audit (yang akan membaca record) membaca **referensi terbaru** dari entry — bukan via `audit_consumer` yang bind-tetap.
- **Invariant:** registry immutable ✓ (objek tak berubah, referensi di-update, bukan objek di-mutasi); ownership = entry/Composition Root ✓ (memang owner wiring); lifecycle ✓; audit terminal ✓; no feedback ✓; no unit baru ✓; no responsibility change ✓.
- **Alasan diterima/ditolak:** **Berpotensi diterima** (tidak merecreate consumer tiap preview, tidak share mutable registry, tidak ubah consumer/bridge, tidak ubah registry immutable). Ini "variasi wiring + representasi" yang diizinkan arahan (titik kepemilikan hasil register() diwariskan ke entry). **Perlu konfirmasi** bahwa pemegangan referensi terbaru di entry tidak dianggap "mengubah ownership" — namun pemahaman: entry memang Composition Root (owner) dan ini mengelola referensi di lapisan wiring, bukan mengubah lifecycle/ownership domain.

### D. Publikasi representasi outcome → snapshot audit di Composition Root (BARU)
- **Deskripsi:** hasil `record_execution_audit` (registry baru berisi 1 record) **disimpan sebagai "snapshot audit terkini" di entry/Composition Root**; endpoint audit membaca snapshot tsb. Bukan lewat consumer bind-tetap, bukan recreate consumer.
- **Invariant:** registry immutable ✓; tidak mengubah consumer/bridge ✓; no rebind tiap preview ✓; owner = entry ✓.
- **Alasan:** **Berpotensi diterima** — setara C tetapi menekankan representasi hasil; titik kepemilikan hasil register() di Composition Root. Konsisten dengan invariant. **Perlu keputusan design-driver** apakah dianggap workaround.

### E. Indirection/holder di dalam consumer/bridge (BARU)
- **Deskripsi:** modifikasi `AuditPreviewConsumer`/bridge agar membaca registry via holder yang bisa berubah.
- **Invariant:** registry immutable ✓; no rebind ✓.
- **Diterima/ditolak:** **Ditolak** — mengubah consumer/bridge (menambah indirection) = mengubah cara dependency di-wire & responsibility → tidak diizinkan (di luar batas C/D yang murni di wiring layer).

## Kesimpulan
- **Ditemukan pendekatan yang berpotensi sesuai invariant:** **(C)** holder referensi registry di Composition Root/Entry, dan **(D)** publikasi snapshot hasil ke entry — keduanya tidak merecreate consumer tiap preview, tidak share mutable registry, tidak mengubah consumer/bridge, dan tetap mempertahankan registry immutable.
- Keduanya bergantung pada interpretasi: bahwa **Composition Root/Entry boleh menyimpan "referensi registry terbaru" dan membacanya saat endpoint audit** (mengeksplorasi "titik kepemilikan hasil register()" yang diizinkan arahan), tanpa dianggap mengubah ownership/lifecycle.
- Karena ini menyentuh pemahaman "ownership di lapisan wiring", dan mengingat keputusan desain sebelumnya sensitif, **direkomendasikan konfirmasi desain** terhadap pendekatan C/D (apakah diterima sebagai variasi wiring, atau memang memerlukan keputusan Software Architect).

## Catatan
- Eksplorasi dilakukan terhadap implementasi aktual; tidak ada code di-commit pada eksplorasi ini.
- Jika Lead Engineer / Software Architect menerima pendekatan C atau D, implementasi L6 dapat dilanjutkan dengan tetap memenuhi invariant.
