# AD-S03-001 — Provider Preview Integration (Provider Resolution)

**Status:** Accepted · **Tanggal:** 2026-08-04 · **Tipe:** Engineering Decision (Session 03)

## Keputusan
- Opsi A: hubungkan ExecutionRuntime ke Provider layer sampai **Provider Resolution**.
- Preview = "Execution validated → Provider resolved → Provider selected → Execution skipped".
- **BUKAN** Provider Simulation; **BUKAN** fake result.

## Yang TIDAK boleh dibuat (Session 03)
PreviewProviderExecutor · Fake Provider · Mock Provider Production · Provider Simulator ·
Provider Result Generator · hasil preview sintetis.

## Yang boleh dilakukan
- Pastikan: dependency injection benar, binding benar, provider dapat dipilih,
  provider identity diketahui, provider metadata tersedia.
- `provider.execute()` TIDAK boleh dipanggil.

## Responsibility
- Session 03 berhenti pada **Provider Resolution**, bukan Provider Simulation.

## Activation Path
```
Conversation → RuntimeService → ExecutionRuntime → Provider Resolution → STOP
```
