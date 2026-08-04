ENGINEERING SESSION REPORT

Session
S01

Capability
Foundation Activation

Tanggal
2026-08-04

Commit
dac0b1c (Web -> RuntimeService)
d551c36 (RuntimeAPI -> ExecutionRuntime preview)

â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

Mission
Mengaktifkan activation foundation pertama sehingga jalur arsitektur resmi mulai
dipakai aplikasi: Presentation -> RuntimeService -> ExecutionRuntime (Preview) -> STOP.
Bukan capability baru; menghidupkan komponen yang sudah ada (sesuai kondisi aktual repo).

Goal
âœ“ RuntimeService memperoleh consumer produksi pertama (Web Runtime/Lifecycle/Status).
âœ“ ExecutionRuntime memperoleh producer preview pertama (mode=preview).
âœ“ Activation foundation pertama terbentuk.
âœ“ Tidak ada Runtime baru; tidak ada perubahan Architecture / Constitution / ADR.
âœ“ Regression PASS.

â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

Pekerjaan yang Diselesaikan

â€¢ WebRuntimeService: subclass RuntimeService (gateway kontrak & lifecycle) untuk
  Web Runtime/Lifecycle/Status endpoint; diekspor sebagai API publik runtime_service.
â€¢ Web '/' dan '/runtime' mengonsumsi WebRuntimeService (consumer produksi pertama).
â€¢ PreviewGateway + ExecutionPreviewProducer: RuntimeAPI mendaftarkan handler action
  'execution.preview' yang membangun ExecutionRequest(mode="preview") lalu memanggil
  ExecutionRuntime via ExecutionEngine (dependency injection).
â€¢ Routing/composition dilakukan di entry (web/server), bukan di dalam RuntimeService,
  sehingga RuntimeService tetap gateway (tidak mengimpor execution/coordinator/provider).
â€¢ Provider TIDAK pernah dieksekusi: mode selalu 'preview', external_calls=0,
  executed=False (konsisten ADR-024).

â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

Deliverables

â€¢ Commit dac0b1c â€” Web sebagai consumer pertama RuntimeService.
â€¢ Commit d551c36 â€” RuntimeAPI -> ExecutionRuntime producer preview pertama.
â€¢ 8 file berubah, +566 insertions; 17 test baru (9 web-runtime + 8 execution-preview).

â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

Regression

PASS â€” 3404 passed, 1 skipped (unit + integration + presentation + runtime_service).

Modul sesi ini CLEAN: tanpa asyncio/threading/socket/http/subprocess/uvicorn.
validate_imports failure = baseline pre-existing (asyncio di web/telemetry/tuning/service),
bukan regresi sesi.

â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

Technical Debt

Sebelum:
RuntimeService consumer = 0; ExecutionRuntime producer = 0.

Sesudah:
RuntimeService consumer = 1 (Web); ExecutionRuntime producer = 1 (preview).
TD-002 (RuntimeService 0 consumer) & TD-003 (ExecutionRuntime 0 producer) menurun.

â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

Known Issues

â€¢ Endpoint Web lain (/workflow, /incidents, /autonomous, /openclaw, /knowledge,
  /settings) TIDAK dimigrasi â€” di luar scope Session 01 (sesuai RSR-003).
â€¢ Producer masih PREVIEW (bukan production) â€” ADR-024 dipertahankan.

â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

Handoff

Engineer berikutnya harus mengetahui:
â€¢ Jalur resmi baru: Web Runtime/Lifecycle -> WebRuntimeService (consumer), dan
  RuntimeAPI action='execution.preview' -> ExecutionRequest(preview) ->
  ExecutionRuntime (producer preview). Provider tidak dieksekusi.
â€¢ Konduit di-compose di entry (web/server), menjaga RuntimeService tetap gateway (D0-001).
â€¢ Activation penuh (production execution) butuh keputusan terpisah (ADR-024),
  bukan scope sesi ini.

Next Session: Session 02 â€” Conversation Capability (menunggu arahan arsitektur).

â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

EC Update

EC-002
EC-003
EC-004
EC-007
EC-012
EC-020

â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

01_AKTUAL_STATE

âœ“ Sudah diperbarui
