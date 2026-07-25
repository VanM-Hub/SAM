# Sprint 29 Fase 3 — Goal Arbitration (Progress Report)

**Tanggal:** 2026-07-25
**Branch:** `feature/sprint13-plugin-runtime`
**Status:** ✅ SELESAI — 40 test baru, 0 regresi

---

## Ringkasan

Membangun **Goal Arbitration** — mekanisme untuk memilih prioritas antar goal kompetitif (HEAL, OPTIMIZE, DEPLOY, SCALE, MONITOR, LEARN) berdasarkan kondisi sistem, fokus perhatian, dan scoring model.

### Komponen

| Komponen | File | Test | Status |
|---|---|---|---|
| **GoalType enum** (6 values) | `src/sam/cognition/arbitration.py` | 2 | ✅ |
| **GoalRequest model** | `src/sam/cognition/arbitration.py` | 4 | ✅ |
| **ArbitrationResult model** | `src/sam/cognition/arbitration.py` | 4 | ✅ |
| **GoalArbitrator** | `src/sam/cognition/arbitration.py` | 30 | ✅ |
| **Migration 040** | `src/sam/persistence/migrations/040_add_arbitration_tables.sql` | — | ✅ |
| **Total** | **2 source files, 1 test file** | **40** | ✅ **All pass** |

### Detail Implementasi

#### 1. GoalType Enum
6 goal types: `HEAL`, `OPTIMIZE`, `DEPLOY`, `SCALE`, `MONITOR`, `LEARN` dengan base priority masing-masing (HEAL=8, OPTIMIZE=6, SCALE=5, DEPLOY=4, MONITOR=3, LEARN=2).

#### 2. GoalRequest Model
- **Fields:** goal_type, priority (1–10), urgency (0–1), resource_estimate, expected_duration (seconds), confidence (0–1), context (dict)
- **Serialization:** `to_dict()` / `from_dict()` roundtrip

#### 3. ArbitrationResult Model
- **Fields:** selected_goal, reason, confidence, scores (dict of goal→score), runner_up, id, timestamp
- **Serialization:** `to_dict()` (generates id via UUID)

#### 4. GoalArbitrator — Scoring Model
Base score formula:
```
score = (priority × 0.3) + (urgency × 0.4) + (1 - resource_estimate/100) × 0.3
```

**Context adjustments per goal type:**

| Goal | Condition | Adjustment |
|---|---|---|
| HEAL | confidence < 70 | +4.0 |
| HEAL | health < 50 | +5.0 |
| HEAL | focus == AVAILABILITY | +3.0 |
| OPTIMIZE | health >= 85 | +2.0 |
| OPTIMIZE | health < 85 | -1.0 |
| DEPLOY | focus == FEATURES | +2.0 |
| DEPLOY | focus == AVAILABILITY | -2.0 |
| SCALE | focus in (LATENCY, AVAILABILITY) | +2.0 |
| LEARN | focus == BALANCED AND health >= 85 | +1.5 |
| LEARN | focus != BALANCED | -1.0 |
| Any | confidence < 0.3 | -2.0 |

**Decision flow:**
1. Compute base score for each goal
2. Apply context adjustments
3. Select highest-scoring goal
4. Record runner-up
5. Calculate confidence: normalized score gap × state confidence

#### 5. Integration
- **GoalArbitrator → CognitiveStateManager:** reads health and confidence
- **GoalArbitrator → AttentionManager:** reads focus via `get_current_profile()`
- SelfHealingLoop dan Autotuner akan menggunakan arbitration untuk menentukan tindakan

#### 6. Migration 040
- `arbitration_history` — id, selected_goal, reason, confidence, scores (JSON), runner_up, timestamp

### Test Results

| Kategori | Tests | Contoh |
|---|---|---|
| Model unit | 10 | GoalType, GoalRequest, ArbitrationResult creation & serialization |
| evaluate: basic | 5 | Empty list, single goal, multiple, runner_up, all 6 types |
| Context: HEAL | 3 | Low confidence, low health, AVAILABILITY focus |
| Context: OPTIMIZE | 1 | Healthy state competitive |
| Context: DEPLOY | 2 | FEATURES boost, AVAILABILITY penalty |
| Context: SCALE | 1 | LATENCY focus boost |
| Context: LEARN | 2 | BALANCED boost, crisis penalty |
| Low confidence penalty | 1 | Goal with confidence < 0.3 |
| Priority history | 5 | Initial, after evaluate, history tracking, limit, count |
| Scoring internals | 4 | Base score comparison, resource penalty, reason strings |
| Integration | 4 | Full cycle, positive scores, HEAL vs OPTIMIZE scenario |

**40/40 passed, 0 failures.**

### Struktur File

```
src/sam/cognition/
├── __init__.py              ← MODIFIED: added arbitration exports
├── arbitration.py           ← NEW: GoalType, GoalRequest, ArbitrationResult, GoalArbitrator
├── state.py                 ← EXISTING
├── memory.py                ← EXISTING
└── attention.py             ← EXISTING

src/sam/persistence/migrations/
└── 040_add_arbitration_tables.sql  ← NEW

tests/
└── test_arbitration.py      ← NEW: 40 tests
```

---

*Prepared by ZARA 🦋*
