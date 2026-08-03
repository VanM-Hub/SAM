# OP-490: Guardian Operational Intent — Dokumentasi Sprint 48

## Ringkasan

Sprint 48 melengkapi Guardian Live Runtime dengan **Operational Intent** — usulan tindakan deterministic berbasis rule. Intent adalah DTO, bukan action/mission/execution. Tidak boleh memanggil Decision Runtime.

**Versi:** v5.5.0  **Branch:** sprint-48  **Tag:** v5.5.0

## Pipeline
```
Event → Dispatch → Synchronization → Transition Intelligence
→ Situation Intelligence → Operational Assessment
→ Operational Intent (NEW) → Reasoning → Learning
→ Execution Preview → Dashboard → Conversation
```

## File Baru (7 file)
- `intent.py` — GuardianIntent, IntentType (9 types), IntentPriority, IntentStatus DTOs
- `intent_builder.py` — Build from assessment/situation
- `intent_policy.py` — 9 built-in policies: Observe/Monitor/Escalate/Recommend/Investigate/Review/Wait/NoAction/Blocked
- `intent_ranker.py` — Rank by priority+confidence
- `intent_validator.py` — 7 validation rules
- `conversation_intent.py` — 10 queries
- `dashboard_intent.py` — 6 immutable cards

## Hasil Test
| Area | Tests | Status |
|---|---|---|
| Sprint 48 | 108 passed | ✅ |
| Unit regression | 1282 passed, 1 skipped | ✅ |
| Forbidden imports | Clean | ✅ |
