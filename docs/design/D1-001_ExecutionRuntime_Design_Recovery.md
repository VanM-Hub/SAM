D1-001 — Execution Runtime Design Recovery
Version: v1.0
Owner: 🦋 Zara
Architecture Authority: ✦ Aster
Status: APPROVED — Design Recovery (READ-ONLY) [final recovery, per batas analysis-paralysis]
Priority: ⭐⭐⭐⭐⭐
Category: Architecture / Design Recovery (terakhir dalam rangkaian)

=====================================================================
TUJUAN (DARI ASTER)
=====================================================================
Jawab SATU pertanyaan:
  "Bagaimana Program C mendesain hubungan RuntimeService dengan Execution Runtime?"

Sub-pertanyaan:
1. Siapa yang membuat ExecutionRequest?
2. Siapa yang membuat ApprovalRequest?
3. Siapa yang memanggil Execution Runtime?
4. Apakah RuntimeService pernah dirancang membuat ExecutionRequest?
5. Apakah Execution Runtime mengharapkan caller tertentu?
6. Apakah ada Dispatcher yang hilang?
7. Apakah Program C belum selesai, atau wiring belum selesai?
8. Kalau seluruh Program C selesai, call graph seharusnya seperti apa?

READ-ONLY. Tidak ada perubahan kode.

=====================================================================
KONTEKS & SUMBER
=====================================================================
Sumber yang diperiksa (semua dari repository):
- OP-2700 (Program D RuntimeServices); OP-3000 (Presentation); ROADMAP (pipeline)
- D0-001 (RuntimeService = Constitutional Gateway, bukan executor)
- ADR-024_Preview_Only_Execution.md (Execution Runtime = preview-only sampai Assembly)
- Implementasi:
  * sam/execution_runtime/  (Program C, v26, Sprint 250-260, commit b9ae710)
  * sam/execution/runtime/  (Phase IX v9.x, Sprint 95-99) — dunia lama
  * sam/execution/dispatch/ (ConnectorDispatcher — world lama)
  * sam/runtime_service/    (Program D gateway)
  * sam/reasoning/engine.py (pemakai execution graph world lama)
  * sam/execution/approval_execution.py (ApprovalRequest world lama)

CATATAN PENTING — DUA DUNIA:
Repository berisi DUA "Execution Runtime" dan DUA "ExecutionRequest".
Membedakannya adalah KUNCI menjawab D1-001.

DUNIA B (baru, Program C, tahap Foundation 0.26):
- Folder: src/sam/execution_runtime/  (60+ modul, Sprint 250-260, commit b9ae710)
- ExecutionRequest: execution_id/provider_id/operation/payload/mode
  mode default = "preview" | execute | rollback
- ExecutionRuntime.run(runtime_id, request) -> ExecutionOutcome
- Punya: approval_gate, approval_pipeline, execution_pipeline, provider_dispatcher,
  rollback, monitoring, safety, certification, provider_activation.

DUNIA A (lama, Phase IX, v9.x):
- Folder: src/sam/execution/ (runtime/, dispatch/, adapters/, connectors/, providers/)
- ExecutionRequest: request_id/context_id/timestamp/task_type
- ExecutionGraphEngine (sam/execution/engine.py) — dipakai reasoning/engine.py
- ExecutionRuntime lama (sam/execution/runtime/runtime.py)
- ConnectorDispatcher (sam/execution/dispatch/dispatcher.py) — route connector
- ApprovalExecutionBridge (sam/execution/approval_execution.py)

=====================================================================
1. SIAPA YANG MEMBUAT ExecutionRequest?
=====================================================================
DUA jawaban, sesuai dua dunia.

DUNIA A (lama, v9.x) — MEMBUAT & MEMAKAI sendiri:
- connector_protocol.py:167  -> return ExecutionRequest(...)
- integration_execution.py:116
- dispatch/conversation_dispatch.py:120, 159, 233 (req = ExecutionRequest(...))
- Ini request world lama untuk pipeline Phase IX.

DUNIA B (Program C, v26) — MEMILIKI builder TAPI TIDAK ADA pemanggil luar:
- conversation_execution_request.py, dashboard_execution_request.py (builder)
- execution_request.py (DTO, mode default "preview")
- TIDAK ada file di luar execution_runtime/ yang memanggil builder ini.
=> Program C tahu cara membuat ExecutionRequest, tapi tidak ada entry/conduit
   yang memicunya dari luar.

=====================================================================
2. SIAPA YANG MEMBUAT ApprovalRequest?
=====================================================================
DUA approval gate terpisah, masing-masing di dunianya:

DUNIA A: sam/execution/approval_execution.py
  - ApprovalItem, ApprovalRequest, ApprovalResult
  - Komentar: "All execution MUST go through approval - no auto-submit"
  - Build dari ExecutionPlan (world lama).

DUNIA B: sam/execution_runtime/approval_gate.py
  - ApprovalGate.evaluate(request) -> ApprovalDecision
  - ApprovalGate.may_execute(request) -> bool
  - Dipanggil dari ExecutionPipeline.run (baris 105: approval = self._approval.run(...))
  - Dan dari ExecutionRuntime.run (self._gate.may_execute(request))

=> Program C PUNYA approval gate internal (ApprovalGate) yang terintegrasi di
   pipeline. Ia TIDAK memakai approval gate world lama (approval_execution).
   Dua sistem approval yang berbeda, tidak bertemu.

=====================================================================
3. SIAPA YANG MEMANGGIL EXECUTION RUNTIME?
=====================================================================
DI DALAM Program C (self-contained, sehat):
  ExecutionEngine.execute(request)         [execution_engine.py:29]
    -> self._runtime.run(f"eng-{id}", req) [execution_engine.py:30]
       -> ExecutionRuntime.run(...)        [execution_runtime.py:48]
          -> self._pipeline.run(...)       [execution_runtime.py:49]
             -> approval = self._approval.run(...)   [execution_pipeline.py:105]
             -> provider = self._provider.run(...)   [execution_pipeline.py:109]
          -> approved = self._gate.may_execute(req)  [execution_runtime.py:50]

DARI LUAR Program C: TIDAK ADA (0 konsumen).
- Scan seluruh src+tests: tidak ada file di luar execution_runtime/ yang
  memanggil ExecutionEngine.execute / ExecutionRuntime.run dari Program C.
- Entry point (CLI/Web/Desktop/Conversation/REST) memanggil RuntimeCoordinator
  (world lama, dari C0-001/A0-001), BUKAN Program C.
- reasoning/engine.py memakai ExecutionGraphEngine (world lama), bukan Program C.

=====================================================================
4. APAKAH RUNTIMESERVICE PERNAH DIRANCANG MEMBUAT ExecutionRequest?
=====================================================================
TIDAK.

Bukti:
- sam/runtime_service/ 0 impor ke sam/execution_runtime maupun sam/execution
  (scan: tidak ada file runtime_service yang menyentuh execution).
- RuntimeServiceContract: network_allowed=False, deterministic=True,
  synchronous=True, approval_required=True, preview_first=True.
  Ia DEKLARATIF; tidak mungkin sekaligus pembuat ExecutionRequest (eksekusi).
- D0-001: RuntimeService = Constitutional Gateway (kontrak+lifecycle+health),
  BUKAN executor. Ia tidak membuat ExecutionRequest.
- Dalam pipeline 14 tahap (runtime_pipeline.py), RuntimeService adalah tahap 13
  yang "menerima hasil Execution Runtime" — bukan yang memicu eksekusi.

=> RuntimeService TIDAK dirancang membuat ExecutionRequest.
   Ia adalah gerbang kontrak; pembuatan ExecutionRequest adalah tanggung jawab
   Execution Runtime / layer eksekusi, bukan gateway.

=====================================================================
5. APAKAH EXECUTION RUNTIME MENGHARAPKAN CALLER TERTENTU?
=====================================================================
API Program C sangat sederhana & tidak menuntut caller spesifik:
  ExecutionRuntime.run(runtime_id: str, request: ExecutionRequest) -> ExecutionOutcome
  ExecutionEngine.execute(request: ExecutionRequest) -> ExecutionOutcome

TIDAK ada dependency ke RuntimeService / presentation / entry tertentu.
Ia siap dipanggil oleh siapa saja yang punya ExecutionRequest.

Kenapa tidak ada yang memanggil? = murni WIRING GAP, bukan kekurangan API.

Catatan: mode default request = "preview" (bukan "execute"). Ini disengaja,
konsisten ADR-024 (preview-only). Caller yang ingin eksekusi nyata harus
men-set mode="execute" — mekanisme ini sudah tersedia di DTO.

=====================================================================
6. APAKAH ADA DISPATCHER YANG HILANG?
=====================================================================
YA. Inilah temuan paling penting D1-001.

Yang ADA (tidak ada yang menghubungkan RuntimeService ke ExecutionRuntime):
- ConnectorDispatcher (sam/execution/dispatch/dispatcher.py, world lama):
  select_connector(connector_type) -> route ke ConnectorProtocol. Me-route
  CONNECTOR, bukan eksekusi.
- provider_dispatcher.py (Program C): route request ke PROVIDER di dalam
  ExecutionPipeline. Sudah ada & terhubung di dalam execution_runtime.
- conversation_dispatch / dashboard_dispatch (world lama).

Yang HILANG = KONDUIT antara:
   RuntimeService (Gateway, Program D)
        │
        ?   <-- TIDAK ADA apa pun di sini
        ▼
   Execution Runtime (Program C)

Tidak ada adapter/forwarder/conduit yang menerima kontrak RuntimeService lalu
menyusun ExecutionRequest dan memanggil ExecutionEngine. Itu "sesuatu" di antara
Gateway dan Executor yang Aster tanyakan — dan secara desain, KOSONG.

Catatan: EWO/aturan tidak mengizinkan membuat "Dispatcher/Facade" sebagai
konsep baru. Jadi "yang hilang" ini harus dipahami sebagai KEKOSONGAN WIRING,
mengisi-via-conduit sesuai desain yang ada (bukan menciptakan konsep baru).

=====================================================================
7. APAKAH PROGRAM C "BELUM SELESAI" ATAU "WIRING BELUM SELESAI"?
=====================================================================
KEDUANYA — dua gap yang TERPISAH:

GAP 1 — PRODUCTION-READINESS (belum production-ready):
  ADR-024 (Accepted, 2026-07-30, Architecture Freeze v10):
  - Execution Runtime & Runtime Kernel = preview-only, belum diuji produksi.
  - Execution Runtime hanya berjalan hingga Assembly stage (tidak eksekusi
    aktual). Output = simulation/snapshot.
  - "Butuh Phase XI untuk production-ready."
  => Kode Program C LENGKAP secara struktur, tapi SECARA DESAIN di-freeze
     preview-only sampai Phase XI.

GAP 2 — WIRING (belum disambung ke gateway/entry):
  - 0 konsumen ExecutionEngine/ExecutionRuntime Program C dari luar.
  - 0 konsumen RuntimeService dari presentation/entry (D0-001).
  - RuntimeService dan ExecutionRuntime = DUA pulau terpisah, masing-masing
    lengkap internal, tidak bersentuhan.

Jadi:
- BUKAN "Program C belum ditulis" (kodenya ada & lengkap).
- BUKAN "wiring belum selesai" saja (karena preview-only juga di-freeze ADR).
- = "Program C selesai sebagai kerangka (v26, self-contained) TETAPI
   preview-only (ADR-024) DAN belum di-wire ke gateway/entry (0 consumer)".

=====================================================================
8. CALL GRAPH YANG SEHARUSNYA (KALAU SELURUHNYA SELESAI)
=====================================================================
Berdasarkan pipeline ROADMAP + pipeline 14 tahap + desain Program C/D:

   Entry Point (CLI / Web / Desktop / Conversation / REST)
        │    (Article XVI: semua aksi -> RuntimeService)
        ▼
   RuntimeService  (Constitutional Gateway — kontrak/lifecycle/health,
   │               deterministic, preview-first, approval-aware)
   │               TIDAK membuat ExecutionRequest, TIDAK executor.
   ▼
   ??? (konduit/wiring yang sekarang kosong; isi sesuai desain,
   │     bukan konsep baru)
   ▼
   Execution Runtime (Program C, sam/execution_runtime/)
        │  ExecutionEngine.execute -> ExecutionRuntime.run
        │  -> ExecutionPipeline.run (validation -> approval -> provider)
        │  ApprovalGate.may_execute; mode="preview" default; ADR-024
        ▼
   Provider (external provider via provider_dispatcher / pipeline)
   ▼
   External Provider

Bentuk "???" yang benar secara desain TIDAK boleh menjadi:
- RuntimeService menjadi executor (melanggar contract).
- Konsep "Dispatcher/Facade" baru (melanggar aturan no-new-concept).
Bentuk yang konsisten dengan arsitektur: RUNTIMESERVICE menyediakan jalur
kontrak yang menghasilkan/via ExecutionRuntime — di mana execution tetap
milik Program C. Persis apa yang nanti dijawab I1 (Constitutional Entry Wiring)
ATAU dikoreksi Aster jika desain memang menuntut sesuatu yang lain.

=====================================================================
KESIMPULAN
=====================================================================
1. RuntimeService (Program D) dan Execution Runtime (Program C) adalah DUA
   lapisan yang masing-masing LENGKAP secara internal TAPI TIDAK TERHUBUNG.
2. Ada DUA dunia eksekusi: world lama (Phase IX v9.x, dipakai entry + reasoning)
   dan Program C (v26, self-contained, 0 consumer). Ini sumber utama "gap".
3. Siapa membuat ExecutionRequest = Program C (builder ada) / world lama (dipakai);
   Siapa membuat ApprovalRequest = ApprovalGate (Program C) vs approval_execution
   (world lama) — dua sistem approval terpisah.
4. Siapa memanggil Execution Runtime = dalam Program C (Engine->Runtime->Pipeline);
   dari luar = TIDAK ADA.
5. RuntimeService TIDAK dirancang membuat ExecutionRequest (gateway, bukan executor).
6. ADA dispatcher yang hilang (konduit RuntimeService->ExecutionRuntime kosong).
7. Program C = kerangka selesai + preview-only (ADR-024) + wiring belum ada.
8. Call graph target = Entry -> RuntimeService -> (konduit) -> Execution Runtime
   -> Provider; konduit tidak boleh jadi executor & tidak boleh konsep baru.

=====================================================================
IMPLIKASI UNTUK I1 (Constitutional Entry Wiring) & ARAH
=====================================================================
- I1 harus menyambungkan RuntimeService ke Execution Runtime dengan cara yang
  menjaga RuntimeService tetap gateway (bukan executor) dan tidak menciptakan
  konsep baru.
- Duplikasi dua dunia (sam/execution vs sam/execution_runtime) adalah technical
  debt nyata yang harus dikelola, bukan diabaikan.
- ADR-024 (preview-only, butuh Phase XI) membatasi eksekusi nyata; I1 tidak
  boleh mencabut ini tanpa keputusan terpisah.
- Keputusan desain tentang bentuk "konduit" antara Gateway dan Executor
  adalah milik Aster (architect), bukan Zara (engineer).

=====================================================================
KEBENARAN (sesuai kerangka 3-jenis Aster)
=====================================================================
- Constitutional Truth: Presentation hanya melalui RuntimeService (Article XVI);
  execution di belakang Approval Gate; preview-first.
- Design Truth: RuntimeService = Gateway (D0-001); Execution Runtime = Program C
  (v26, approval gate internal, mode preview default, ADR-024 preview-only).
- Implementation Truth: kedua lapisan 0 consumer; entry masih ke RuntimeCoordinator
  (world lama); dua dunia eksekusi paralel; konduit Gateway->Executor HILANG.

Ketiga kebenaran BELUM sejajar => gap nyata, dijawab dengan bukti, bukan asumsi.

=====================================================================
ACCEPTANCE CRITERIA
=====================================================================
- [x] READ-ONLY: tidak ada perubahan kode.
- [x] Menjawab 8 sub-pertanyaan Aster dengan bukti repository.
- [x] Mengungkap 2 dunia eksekusi (v9.x vs Program C) + 2 sistem approval.
- [x] Mengidentifikasi konduit RuntimeService->ExecutionRuntime yang hilang.
- [x] Menghubungkan ADR-024 (preview-only) dengan status Program C.
- [x] Memberikan call graph target + batasan bentuk konduit (bukan konsep baru).
