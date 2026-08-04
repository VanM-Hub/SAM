ENGINEERING SESSION REPORT

Session
S02

Capability
Conversation Capability

Tanggal
2026-08-04

Commit
ad85874 (Conversation Execution Builder + Preview Wiring, AD-S02-001)
02b608c (Integrasi Conversation preview ke entry web)

â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

Mission
Menjadikan Conversation sebagai entry point capability pertama yang menggunakan
activation foundation hasil Session 01: Conversation -> RuntimeService ->
ExecutionRuntime (Preview) -> STOP. Masih mengikuti ADR-024 (belum production).

Goal
âœ“ Conversation menggunakan RuntimeService.
âœ“ Conversation membangun ExecutionRequest sesuai desain.
âœ“ Conversation menghasilkan Preview Execution melalui ExecutionRuntime.
âœ“ Approval Boundary dipertahankan.
âœ“ Context tetap terjaga.
âœ“ Tidak ada Runtime baru / perubahan Architecture / pelanggaran Constitution.
âœ“ Regression PASS.

â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

Pekerjaan yang Diselesaikan

â€¢ ConversationExecutionContext (immutable): conversation_id, request, turn_id.
â€¢ ConversationExecutionRequestBuilder: mengubah context -> ExecutionRequest(mode='preview').
â€¢ Payload HANYA namespace 'conversation' (AD-S02-001); pakai 'request' bukan
  'intent' (hindari ambigu Session 07); serializable; DTO tidak diubah.
â€¢ ConversationPreviewGateway: Conversation -> RuntimeAPI(action='execution.preview')
  -> ExecutionRuntime. REUSE PreviewGateway Session 01.
â€¢ Integrasi di entry web: conversation_preview_gateway (provider filesystem).
  Tidak mengubah Desktop/Operations legacy.

â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

Deliverables

â€¢ Commit ad85874 â€” Conversation Execution Builder + Preview Wiring (AD-S02-001).
â€¢ Commit 02b608c â€” Integrasi Conversation preview ke entry web.
â€¢ 6 file; 13 test baru (builder + preview wiring).

â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

Regression

PASS â€” 3417 passed, 1 skipped (unit + integration + presentation + runtime_service).

Modul sesi ini CLEAN (tanpa asyncio/threading/socket/http/subprocess/uvicorn).
Tidak ada runtime/approval/execution baru. Dependency tetap acyclic.

â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

Technical Debt

Sebelum:
Conversation 0 memakai RuntimeService/ExecutionRuntime (jalur legacy Operations).

Sesudah:
Conversation punya jalur resmi preview (Consumer RuntimeService +1, Producer
ExecutionRuntime +1). TD Conversation activation menurun.

â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

Known Issues

â€¢ Conversation masih punya dua dunia: jalur legacy (operations/conversation_api,
  sandbox/simulasi) dan jalur resmi preview (baru). Jalur legacy TIDAK dihapus.
â€¢ Preview masih preview-only (ADR-024); production execution butuh keputusan
  terpisah (bukan scope sesi ini).

â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

Repository Metrics

â€¢ RuntimeService Consumer: 2 (Web + Conversation preview).
â€¢ ExecutionRuntime Producer: 2 (Web preview + Conversation preview).
â€¢ Conversation Activation: Conversation -> RuntimeService -> ExecutionRuntime
  (preview) terbentuk.
â€¢ Technical Debt: TD activation Conversation turun.
â€¢ Regression: 3417 passed, 1 skipped.

Vision Progress

â€¢ Foundation Activation â€” selesai (S01)
â€¢ Conversation Capability â€” selesai (S02)
â€¢ Desktop Experience â€” next (S03)
â€¢ Knowledge & Memory â€” future (S04)
â€¢ Workflow & Automation â€” future (S05)
â€¢ Provider Integration â€” future (S06)
â€¢ Intelligence & Agent â€” future (S07)
â€¢ Plugin & Extension â€” future (S08)
â€¢ Technical Debt Reduction â€” future (S09)
â€¢ Operational Product â€” future (S10)

â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

Handoff

Engineer berikutnya harus mengetahui:
â€¢ Conversation kini bisa preview via ConversationPreviewGateway ->
  RuntimeAPI(execution.preview) -> ExecutionRuntime. Provider tidak dieksekusi.
â€¢ Payload = Execution Context; HANYA namespace 'conversation' diisi (AD-S02-001);
  pakai 'request' bukan 'intent'. Namespace lain (memory/knowledge/workflow/agent/
  telemetry) dibiarkan kosong sampai capability aktif.
â€¢ Jalur legacy operations/conversation tetap ada dan tidak dihapus.
â€¢ Desktop saat ini masih entry Conversation legacy; Desktop Experience = Session 03.

Next Session: Session 03 â€” Desktop Experience (menunggu arahan arsitektur).

â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

EC Update

EC-003
EC-004
EC-007
EC-012
EC-020

â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

01_AKTUAL_STATE

âœ“ Sudah diperbarui
