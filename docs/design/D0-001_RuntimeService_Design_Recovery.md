D0-001 — RuntimeService Design Recovery
Version: v1.0
Owner: 🦋 Zara
Architecture Authority: ✦ Aster
Status: APPROVED — Design Recovery (READ-ONLY)
Priority: ⭐⭐⭐⭐⭐
Category: Architecture / Design Recovery

=====================================================================
TUJUAN (DARI ASTER)
=====================================================================
Jawab pertanyaan: "Program D sebenarnya mendesain RuntimeService menjadi apa?"
Berdasarkan repository — BUKAN asumsi.
Cari dari: commit history, specification, design note, roadmap, ADR, implementation, TODO.

Pertanyaan yang dijawab:
1. Mengapa RuntimeService dibuat?
2. Mengapa subclass ada?
3. Mengapa hanya metadata?
4. Mengapa tidak ada delegation?
5. Apakah memang belum selesai, atau memang sengaja begitu?
6. Apakah RuntimeService dirancang sebagai Gateway atau State Object?
7. Kalau Program D selesai, bagaimana RuntimeService seharusnya bekerja?
8. Apa buktinya?

READ-ONLY. Tidak ada perubahan kode.

=====================================================================
METODOLOGI & SUMBER
=====================================================================
Sumber yang diperiksa (semua dari repository):
- Commit history: src/sam/runtime_service (1 commit: 51a68e7)
- OP-2700_Runtime_Services_Complete.md (Program D complete report, v27)
- OP-3000_Presentation_Layer_ProgramF_Complete.md (Presentation Layer, v30)
- ROADMAP.md (Program D & Program F — pipeline visualisasi)
- Article XVI Constitution (Presentation Principle)
- G1-003_ADR_Architecture_Audit.md (Dependency graph correction)
- Public_API.md (RuntimeService = API publik)
- Implementasi aktual: runtime_service/*.py, execution/approval_execution.py

=====================================================================
1. MENGAPA RUNTIMESERVICE DIBUAT?
=====================================================================
JAWABAN: Untuk menjadi lapisan kontrak/lifecycle/health/readiness yang
DETERMINISTIK dan SYNC — gerbang masuk resmi bagi presentation/entry point,
sesuai yang dimanatkan Article XVI Constitution dan pipeline Program F.

Bukti (OP-2700):
> "HTTP server nyata (fastapi/uvicorn) tetap berada di docs/dependency server,
>  bukan di runtime_service — service ini menyiapkan kontrak, lifecycle, health,
>  dan readiness secara internal/deterministik tanpa membuka port."
> "Import layer lain dari runtime_service: NONE (hanya runtime_service internal + stdlib)"
> "Runtime service = lapisan baru di atasnya" (tidak memodifikasi subsystem legacy)

Bukti (Article XVI Constitution / OP-3000):
> "Presentation Layer berkomunikasi hanya melalui RuntimeService."
> "Semua operasi menuju RuntimeService."

Bukti (Public_API.md): `RuntimeService` tercantum sebagai API publik.

BUAT APA? = GATEWAY/PINTU MASUK presentation → Runtime (deklaratif, bukan eksekutor).

=====================================================================
2. MENGAPA SUBCLASS ADA?
=====================================================================
JAWABAN: Setiap subclass = satu JENIS SERVICE per-capability yang menerapkan
kontrak Program D yang sama. ConversationRuntimeService & DashboardRuntimeService
mewakili dua capability inti (percakapan & dashboard).

Bukti:
- ConversationRuntimeService: capabilities=["conversation","preview","execute"],
  channels=("conversation",)
- DashboardRuntimeService: capabilities=["dashboard","monitoring","preview"],
  views=("mission","workflow","execution","approval")

Ini pola REGISTRATION/DESCRIPTOR per service — BUKAN pola eksekusi.
Subclass mengisi descriptor/metadata/capabilities, lalu memakai lifecycle base
(initialize/status/status_dict). Tidak ada yang me-delegasi.

=====================================================================
3. MENGAPA HANYA METADATA? (tidak ada jalur eksekusi)
=====================================================================
JAWABAN: SENGAJA (by design). RuntimeService dirancang sebagai lapisan
kontrak/lifecycle/preview yang DETERMINISTIK, SYNC, NO-NETWORK — ia TIDAK
boleh menjadi executor. Eksekusi nyata dipisahkan ke Execution Runtime
di belakang Approval Gate.

Bukti (RuntimeServiceContract, src/sam/runtime_service/contract.py):
- immutable=True, synchronous=True, deterministic=True, network_allowed=False
- approval_required=True, preview_first=True (DEFAULT!)
- validate() -> memastikan immutable & sync & deterministic & not network

Bukti (OP-2700):
> "Plugin metadata-only, tidak melakukan execution call"
> "Synchronous, deterministic, tanpa async/thread/socket/http/subprocess"
> "Import layer lain dari runtime_service: NONE"

Kesimpulan: metadata-only adalah KEPUTUSAN DESAIN, bukan kelalaian.
Boundary (network_allowed=False + approval_required=True + preview_first=True)
sengaja menjaga RuntimeService tetap deklaratif/preview, eksekusi di tempat lain.

=====================================================================
4. MENGAPA TIDAK ADA DELEGATION?
=====================================================================
JAWABAN: Karena target delegasi yang benar bukan "RuntimeCoordinator" langsung,
melainkan Execution Runtime di belakang Approval Gate — dan RuntimeService
dirancang UNTUK TIDAK memegang delegasi eksekusi itu. Ia mendelegasikan secara
KONSEPSUAL (dalam pipeline) ke Execution Runtime, tapi implementasinya bersih.

Bukti pipeline internal (runtime_pipeline.py, 14 tahap):
Mission->Workflow->Policy->Agent->Skill->Memory->Knowledge->Cognitive
->Orchestrator->Connector->Provider->[Execution Runtime]->[Runtime Service]
->External Provider
=> RuntimeService = tahap KE-13, MENDAPATI hasil Execution Runtime, lalu kontrak
   keluar ke External Provider.

Bukti pipeline visualisasi (ROADMAP baris 199):
Desktop UI -> PresentationController -> RuntimeService -> Unified Intelligence Runtime
-> Execution Runtime -> Provider
=> RuntimeService = tahap KEDUA (gateway masuk), Execution Runtime di belakangnya.

Approval gate NYATA ada di sam.execution.approval_execution.py:
> "All execution MUST go through approval - no auto-submit"
=> Terpisah dari runtime_service. runtime_service 0 impor ke execution.

DELEGATION YANG TIDAK ADA = keputusan arsitektur: RuntimeService tidak
menyentuh coordinator/execution; ia kontrak + pipeline-aware.

=====================================================================
5. APAKAH "BELUM SELESAI" ATAU "SENGAJA BEGITU"?
=====================================================================
JAWABAN: KEDUANYA, pada lapisan berbeda.

A. RuntimeService SEBAGAI LAPISAN KONTRAK/LIFECYCLE = SUDAH SELESAI.
   - 0.27 (11 sprint 261-271), 187 test - tahap Foundation 0.27 (Program D).
   - OP-2700 status: Released.
   - 0 forbidden imports, ruff clean, 0 layer violation.
   - Contract, descriptor, metadata, lifecycle, pipeline, registry semua ada.

B. RuntimeService SEBAGAI GERBANG YANG DIPAKAI ENTRY/Presentation = BELUM
   TERHUBUNG (0 consumer). Inilah kesenjangan nyata.
   - OP-3000 klaim "semua operasi menuju RuntimeService" TAPI implementasi
     presentation/entry TIDAK meng-import sam.runtime_service (0 konsumen).
   - Entry point (CLI/Web/Desktop/Conversation/REST) memanggil RuntimeCoordinator
     langsung (14 titik dari C0-001), bukan RuntimeService.
   - konsumen sam.runtime_service di src+tests = NOL.

=> "Belum selesai" BUKAN soal isi RuntimeService (itu genap), melainkan soal
   WIRING: presentation/entry belum disambungkan ke RuntimeService.

=====================================================================
6. RUNTIMESERVICE = GATEWAY ATAU STATE OBJECT?
=====================================================================
JAWABAN: GATEWAY — dalam arti "GATEWAY KONTRAK / PREVIEW", BUKAN "GATEWAY EKSEKUSI".

Alasan GATEWAY (bukan murni state object):
- approval_required=True + preview_first=True di level kontrak = ciri gerbang
  yang mengawal eksekusi ber-approval.
- ROADMAP: "semua action -> RuntimeService".
- Article XVI: presentation "comunicates only through RuntimeService".
- Public_API.md: tercantum sebagai API publik.
- Pipeline menempatkannya sebagai gerbang (masuk UI, dan keluar ke provider).

Namun GATEWAY TIDAK LANGSUNG (tidak memegang eksekusi):
- Bersifat deklaratif (descriptor/contract/metadata/lifecycle/health/readiness).
- Eksekusi NYATA diserahkan ke Execution Runtime + Approval Gate (sam.execution).
- network_allowed=False => tidak membuka port, tidak connector langsung.
- preview_first=True => selalu preview sebelum eksekusi.

Klasifikasi tepat: RuntimeService = "GATEWAY KONTRAK & LIFE-CYCLE" (deklaratif,
deterministik, approval/preview-aware) yang MENGARAHKAN ke Execution Runtime.
Ia BUKAN state object pasif (punya lifecycle + kontrak + pipeline-awareness),
TAPI juga BUKAN eksekutor (tidak memegang delegasi eksekusi).

=====================================================================
7. KALAU PROGRAM D SELESAI, BAGAIMANA SEHARUSNYA RUNTIMESERVICE BEKERJA?
=====================================================================
Alur yang didesain (dari pipeline visualisasi + contract + Article XVI):

   Entry Point (CLI/Web/Desktop/Conversation/REST)
        │  (semua action -> RuntimeService, Article XVI)
        ▼
   RuntimeService  <-- GATEWAY KONTRAK
        │  * validasi kontrak (RuntimeServiceContract.validate)
        │  * lifecycle: Created->Initializing->Ready->Running->Stopping->Stopped|Failed
        │  * health/readiness report
        │  * approval_required=True, preview_first=True
        │
        ▼  (mengarahkan, bukan mengeksekusi)
   Execution Runtime  <-- sam.execution (approval gate, "no auto-submit")
        │  * ExecutionPlan -> ApprovalRequest -> ApprovalResult
        │
        ▼
   Provider (External Provider via pipeline)

Peran pembeda (agar tidak rancu):
- RuntimeService = GATEWAY MASUK + KONTRAK + LIFECYCLE + HEALTH. Deklaratif.
- Execution Runtime = EKSEKUSI NYATA, di belakang Approval Gate.
- RuntimeCoordinator (Legacy) = KERNEL INTERNAL lama; BUKAN target.
- Provider = tujuan akhir.

Kapan RuntimeService dianggap BEKERJA: saat entry/presentation memanggilnya
(BUKAN memanggil coordinator langsung), RuntimeService validasi kontrak +
lifecycle + health, lalu meneruskan ke Execution Runtime di belakang approval.
Implementasi saat ini: entry masih ke coordinator, Execution Runtime sudah ada
di sam.execution tapi belum di-wire sebagai "belakang RuntimeService".

=====================================================================
8. BUKTI (RANGKUMAN)
=====================================================================
| Pernyataan                      | Bukti (lokasi)                        |
|---------------------------------|---------------------------------------|
| Dibuat sbg gateway presentation | Article XVI; OP-3000; ROADMAP baris193/195/199; Public_API |
| Metadata-only = sengaja         | contract.py (approval_required, preview_first, network_allowed); OP-2700 |
| Tidak delegasi = keputusan      | OP-2700 "Import layer else: NONE"; "lapisan baru di atasnya" |
| pipeline 14 tahap esp. Exec      | runtime_pipeline.py; server_runtime.py (Runtime+Connector+Provider+Execution) |
| Approval gate nyata di execution| sam/execution/approval_execution.py ("no auto-submit") |
| RuntimeService 0 konsumen       | scan src+tests: 0 import sam.runtime_service |
| Entry masih ke coordinator      | C0-001: 14 titik RuntimeCoordinator langsung |
| Presentation tdk ke service     | scan: konsumen sam.presentation hanya compliance larangan |

=====================================================================
KESIMPULAN
=====================================================================
1. RuntimeService didesain sebagai GATEWAY KONTRAK/LIFECYCLE yang DETERMINISTIK,
   SYNC, NO-NETWORK, APPROVAL/PREVIEW-AWARE — bukan state object pasif, bukan
   juga eksekutor.
2. Metadata-only & tanpa delegasi = KEPUTUSAN DESAIN (boundary kontrak), bukan
   belum selesai.
3. Yang "belum selesai" BUKAN isi RuntimeService (v27 Released, 187 test), TAPI
   WIRING: presentation/entry belum menyambungkannya (0 consumer).
4. Target "belakang" RuntimeService yang benar adalah Execution Runtime
   (sam.execution) + Approval Gate, BUKAN RuntimeCoordinator.
5. I0 (Entry Point Unification) versi baru harus didasarkan pada desain ini:
   presentation -> RuntimeService -> Execution Runtime -> Provider.
   Operator konsep "RuntimeService menjadi Gateway" TEPAT secara desain intent;
   tinggal menyambungkan wiring sesuai pipeline yang sudah dirancang.

=====================================================================
IMPLIKASI UNTUK I0 (v BERIKUTNYA)
=====================================================================
- JANGAN menjadikan RuntimeService eksekutor/executor (melanggar contract
  network_allowed/approval_required). Ia tetap kontrak+lifecycle+health.
- Entry point sebaiknya memanggil RuntimeService (Article XVI), yang lalu
  mengarahkan ke Execution Runtime + Approval Gate — bukan coordinator langsung.
- Approval gate yang dipakai adalah sam.execution.approval_execution
  ("no auto-submit"), konsisten dengan contract preview_first=True.
- Konfirmasi ke Aster: apakah RuntimeService perlu "menyediakan jalur ke
  Execution Runtime" (facade delegasi tipis) atau cukup presentation memanggil
  Execution Runtime langsung setelah melewati kontrak RuntimeService.
  KEPUTUSAN DESAIN INI MILIK ASTER, BUKAN ZARA.

=====================================================================
ACCEPTANCE CRITERIA
=====================================================================
- [x] READ-ONLY: tidak ada perubahan kode.
- [x] Semua jawaban berbasis repository (commit, spec, roadmap, ADR, implementasi).
- [x] Menjawab 8 pertanyaan Aster secara eksplisit.
- [x] Bedakan Design Intent (gateway) vs Implementation Reality (0 consumer).
- [x] Memberi dasar evidence untuk I0 versi berikutnya.
