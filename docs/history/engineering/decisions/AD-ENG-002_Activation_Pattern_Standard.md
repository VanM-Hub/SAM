# AD-ENG-002 — Activation Pattern Standard

**Status:** Accepted · **Tanggal:** 2026-08-04 · **Tipe:** Engineering Decision (permanen)

Aturan permanen Project SAM: seluruh capability baru WAJIB mengikuti satu pola aktivasi.

## Aturan

```
Conversation
  -> RuntimeService
  -> ExecutionRuntime
  -> <Capability>PreviewConsumer
  -> <Capability>Registry
  -> Conversation<Capability>Bridge
  -> STOP
```

Jika satu capability TIDAK bisa mengikuti pola ini → ia **bukan** target Engineering
Session → masuk **Architecture Backlog**.

## Ketentuan Terkait
- **S07 Artifact**: pola S05/S06 identik (ArtifactPreviewConsumer → ArtifactRegistry →
  ConversationArtifactBridge). JANGAN hubungkan ke Mission/Contract/Intelligence/Dashboard.
- **S08 Memory**: aktivasi PENUH sebagai capability mandiri (bukan cuma namespace payload).
- **S10 Model**: ADR-024 berlaku penuh — hanya preview/resolve/metadata/contract/validation;
  TIDAK invoke LLM/inference/embedding/network/provider execute.
- **Intelligence/Agent/Reasoning**: Architecture Backlog (final); keluar hanya bila activation
  path nyata + consumer nyata + Architecture Decision baru.

## Prioritas Technical Debt Reduction (S10 = TDR)
1. Kurangi consumer RuntimeCoordinator (TD terbesar aktif).
2. Kurangi wiring dunia lama (execution/, reasoning/): pindah ke jalur resmi atau deprecate.
3. Launcher & CLI: bersihkan dependency, JANGAN redesign.
4. Cleanup kecil (duplicate wiring/registry, import tak terpakai). Bukan refactor besar.

Metrik TDR: RuntimeCoordinator Consumer turun · Direct Wiring turun · Legacy Execution
Dependency turun · Activation Coverage naik.

## Nilai
Pola universal SAM — kriteria tetap menilai capability baru secara objektif.
