# EC-006 — Operational Heat Map

## Tujuan

Menunjukkan area repository berdasarkan tingkat aktivitas engineering sehingga engineer mengetahui area yang paling sensitif terhadap perubahan.

Catatan: "HOT/WARM/COOL/COLD" menggambarkan intensitas aktivasi & sensitivitas perubahan, bukan klaim "seluruhnya operational".

---

## HOT

runtime/

Status
Operational core (dipakai per-request CLI/Web/API).

RuntimeCoordinator menjadi titik berat direct wiring.

Perubahan pada folder ini berdampak ke hampir seluruh aplikasi.

Regression Risk
Sangat Tinggi.

guardian/

Status
Available.
Monitoring, observer, pipeline.

Regression Risk
Tinggi.

launcher/

Status
Operational core untuk pemilihan host.

Startup seluruh host.

Masing-masing host punya status launcher sendiri (tidak semua berhasil hidup).

Regression Risk
Sangat Tinggi.

cli/

Status
Operational core per-perintah.
Consumer RuntimeCoordinator terbesar.
Direct wiring.

Regression Risk
Tinggi.

---

## WARM

web/

Available.
Masih direct wiring per-request.

api/

Available.
Read-only.
Direct wiring per-request.

execution/

Available but not fully activated (preview).
Sandbox.
Approval.

autonomous/

Available but not fully activated.
Automation.
Eksekusi masih simulasi.

---

## COOL

presentation/

Ready but not primary.
Sedikit consumer.

runtime_root/

Composition Root.
Belum menjadi root tunggal.
0 consumer produksi di luar package.

runtime_service/

Framework selesai.
Consumer = 0.
Menunggu activation.

execution_runtime/

Pipeline selesai.
Producer = 0.
Menunggu request.

---

## COLD

connector/
orchestrator/
provider/
model/

Sebagian besar framework siap.
Aktivasi masih terbatas.

operations/

Catatan: operations justru merupakan jalur hidup desktop/conversation (lihat EC-003).
Tidak dimasukkan sebagai COLD.

---

## DORMANT

workflow_runtime/
knowledge_runtime/
memory_runtime/
artifact_runtime/
audit_runtime/
mission_runtime/
policy_runtime/
cognitive_runtime/
model_runtime/
intelligence_runtime/
skills_runtime/

Semua memiliki fondasi.
Sebagian besar belum memiliki activation path.
Bukan dead code.

---

## Engineering Insight

Folder yang paling sering berubah bukan berarti paling bermasalah.

Folder HOT justru paling stabil karena menjadi jalur operasional utama.

Perubahan terbesar berikutnya seharusnya terjadi pada area COOL, bukan HOT.

---

## Jangan Dilakukan

- Refactor besar pada runtime/.
- Mengaktifkan seluruh DORMANT sekaligus.
- Menganggap folder DORMANT sebagai dead code.

---

## Fokus Engineering

Naikkan area COOL menjadi WARM.

Naikkan area WARM menjadi HOT.

Kurangi ketergantungan pada runtime/.

---

## Exit Criteria

runtime_service dan execution_runtime berpindah dari COOL menjadi HOT melalui consumer nyata.

---

## Referensi

O0-001
RSR-001
RSR-002
