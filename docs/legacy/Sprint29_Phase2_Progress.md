# Sprint 29 Fase 2 — Attention Manager (Progress Report)

**Tanggal:** 2026-07-25
**Branch:** `feature/sprint13-plugin-runtime`
**Status:** ✅ SELESAI — 46 test baru, 0 regresi

---

## Ringkasan

Membangun **Attention Manager** yang menentukan fokus runtime SAM berdasarkan kondisi sistem, operational confidence, health metrics, dan konteks. Fokus memengaruhi keputusan Self-Healing, Autotuning, dan Evolution.

### Komponen

| Komponen | File | Test | Status |
|---|---|---|---|
| **FocusArea enum** (6 values) | `src/sam/cognition/attention.py` | 2 | ✅ |
| **AttentionProfile model** | `src/sam/cognition/attention.py` | 9 | ✅ |
| **AttentionManager** | `src/sam/cognition/attention.py` | 35 | ✅ |
| **Migration 039** | `src/sam/persistence/migrations/039_add_attention_tables.sql` | — | ✅ |
| **Total** | **2 source files, 1 test file** | **46** | ✅ **All pass** |

### Detail Implementasi

#### 1. FocusArea Enum
6 fokus: `AVAILABILITY`, `LATENCY`, `COST`, `SECURITY`, `FEATURES`, `BALANCED`

#### 2. AttentionProfile
- **Fields:** id (UUID), primary_focus, secondary_focus (optional), weights (5-area dict), reason, confidence (0–1), timestamp
- **Weight presets per focus:** AVAILABILITY→0.6 avail, LATENCY→0.5 latency, COST→0.55 cost, dll.
- **Secondary focus suggestion:** complementary area (AVAILABILITY→LATENCY, LATENCY→COST, COST→AVAILABILITY, dll.)
- **Serialization:** `to_dict()` / `from_dict()` roundtrip

#### 3. AttentionManager — Focus Determination Logic
Urutan prioritas (first match wins):

| # | Kondisi | Fokus | Threshold |
|---|---|---|---|
| 1 | Operational Confidence < 70 | AVAILABILITY | 70% |
| 2 | Health < 50 | AVAILABILITY | 50% |
| 3 | Health drop > 20 points | AVAILABILITY | 20pp |
| 4 | CPU >= 80% atau Memory >= 85%, tanpa failure aktif | LATENCY | 80%/85% |
| 5 | Operational Cost >= 200 | COST | 200 |
| 6 | Default | BALANCED | — |

**Sumber data:**
- CognitiveState (health, confidence)
- Context dict (override keys: operational_confidence, health, cpu_usage, memory_usage, operational_cost, has_active_failure)
- Working Memory (fallsback to WM keys: cpu_usage, memory_usage, operational_cost)

#### 4. Key Methods

| Method | Description |
|---|---|
| `determine_focus(context)` | Return FocusArea based on rules |
| `apply_focus(focus, reason)` | Create AttentionProfile, archive previous, update CognitiveState.focus |
| `determine_and_apply(context)` | Convenience: determine + apply in one call |
| `get_current_profile()` | Get current profile (creates default BALANCED if none) |
| `update_weights(weights)` | Update weight distribution (auto-normalized) |
| `get_focus_history(limit)` | Archived profiles, newest first |

#### 5. Integration
- **AttentionManager → CognitiveStateManager:** `apply_focus()` calls `update_state({"focus": ...})` automatically
- **AttentionManager → WorkingMemoryManager:** reads `cpu_usage`, `memory_usage`, `operational_cost` from WM as fallback
- **Secondary focus suggestion:** e.g. AVAILABILITY → LATENCY as secondary

#### 6. Migration 039
- `attention_profiles` — id, primary_focus, secondary_focus, weights (JSON), reason, confidence, timestamp

### Test Results

| Kategori | Tests | Contoh |
|---|---|---|
| FocusArea enum | 2 | All 6 values, correct names |
| AttentionProfile | 9 | Default, custom, serialization, weight, clamp |
| Focus determination (rule 1) | 3 | Low/high/at-threshold confidence |
| Focus determination (rule 2) | 2 | Low/healthy health |
| Focus determination (rule 3) | 2 | Big/small health drop |
| Focus determination (rule 4) | 4 | High CPU, high memory, failure blocks, low CPU |
| Focus determination (rule 5) | 2 | High/low cost |
| Focus determination (rule 6) | 1 | Default=balanced |
| apply_focus | 4 | Create, update current, archive, sync cognitive state |
| determine_and_apply | 2 | Low confidence, healthy |
| get_current_profile | 2 | Initial default, after apply |
| update_weights | 2 | Update, auto-normalize |
| History | 4 | Empty, transitions, limit, count |
| Weights map | 4 | Availability, latency, cost, balanced weights |
| Integration | 3 | State sync, priority, WM reading |
| **Total** | **46** | ✅ **All pass** |

### Struktur File

```
src/sam/cognition/
├── __init__.py              ← MODIFIED: added attention exports
├── attention.py             ← NEW: FocusArea, AttentionProfile, AttentionManager
├── state.py                 ← EXISTING: CognitiveStateManager
└── memory.py                ← EXISTING: WorkingMemoryManager

src/sam/persistence/migrations/
└── 039_add_attention_tables.sql  ← NEW

tests/
└── test_attention.py        ← NEW: 46 tests
```

---

*Prepared by ZARA 🦋*
