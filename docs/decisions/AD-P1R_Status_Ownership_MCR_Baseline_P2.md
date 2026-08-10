# AD-P1R — Status Ownership MCR & Baseline P2 (Revisi P1)

**Status:** Accepted
**Tanggal:** 2026-08-11
**Tipe:** Architecture Decision (P1 Revision — pengganti P1 lama yang superseded)
**Otoritas:** Aster (Chief Architect), diteruskan via Van
**Status P1 lama:** ❌ SUPERSEDED / HOLD

---

## Konteks

Dokumen P1 lama ("Contract Mission → ReasoningEngine") dibangun di atas fakta repository
sebelum temuan namespace-shadowing `sam.execution.engine` (folder) vs `reasoning/engine.py` (file).
Temuan ini membatalkan premis P1 lama (`reasoning/engine.py` = canonical owner, ~90% siap).

Audit operasional berbasis **runtime nyata** (execution trace `sys.setprofile`, siklus COMPLETED)
membuktikan `mission_cognition/runtime.py` benar-benar menjalankan orchestration path:
`Reason → Govern → Execute → Observe → Reflect → Learn`. Namun ditemukan **2 gap material**.

## Status Per Tahap (terverifikasi runtime)

```
Mission → Reason ✅ → Plan ❌ → Govern ✅ → Execute ✅ → Observe ✅ → Reflect ✅ → Learn ✅
                                                                          ↓
                                                    Next Decision ⚠️ (lesson ada, belum mission caller)
```

## Keputusan

### 1. Status arsitektur komponen (baseline P2)

| Komponen | Status |
|---|---|
| `reasoning/engine.py` | ❌ legacy/backlog candidate |
| `healing/loop.py` | ❌ bukan canonical Mission owner |
| `sam.execution.engine.py` (FILE) | ❌ shadowed legacy |
| `sam.execution.engine/` (FOLDER) | ✅ active execution boundary |
| `mission_cognition/runtime.py` | 🟡 **MCR candidate** — executable, governance-compliant, belum Plan, belum production-called |

**Definisi final:**
> `mission_cognition/runtime.py` = strongest current MCR candidate, operationally executable
> but **not yet mission-reachable** and **not yet complete**.

Kriteria operational MCR: IMPORTABLE ✅ · CALLED ❌ · MISSION-REACHABLE ❌ · ACTIVE ❌

### 2. Opsi yang dipilih — Opsi A (lengkapi dulu, lalu wire)

```
P1 Revision → G1 (Plan) → T1 → T2 → T3 → Runtime verification
   → Architecture acceptance → Wire MCR ke Mission consumer → Production verification
```

### 3. Guardrail — owner Plan (KEPUTUSAN PENTING)

**JANGAN** membuat Plan sebagai implementasi bebas di dalam MCR (risiko God Object).
MCR harus berperan sebagai **lifecycle orchestrator**, memanggil owner Plan — bukan memilikinya:

```
Mission Cognitive Runtime
    ├── invokes Reasoning
    ├── invokes Planning       ← diserahkan ke owner, bukan dimiliki MCR
    ├── hands off Governance
    ├── hands off Execution
    ├── consumes Observation
    ├── invokes Reflection
    └── consumes Learning
```

## Konsekuensi (Investigasi Owner Plan — P2)

Hasil audit kandidat owner Plan:
- `reasoning/planner.py` (v1) → ❌ bukan canonical (strategy/healing/reasoning semua tidak CALLED).
- `strategy.StrategyPlanner` → ❌ tidak ada pemanggil produksi.
- `autonomy_runtime.planning.PlanningEngine` → ⚠️ composition-ready, PlanningAPI ❌ CALLED.
- `agent.planner.MissionBuilder` → ⚠️ composition-ready via `AgentRuntime`+`llm_wiring`, 
  **belum ter-wire ke server/CLI** — candidate terkuat.

**TIDAK ADA planning capability yang ACTIVE di jalur produksi saat ini.**
Owner Plan canonical **BELUM ditetapkan** — menunggu keputusan Aster.
(Daftar rinci: `ZN_SAM/P2_Investigasi_Owner_Plan.md`)

## Status
- **Menunggu keputusan Aster:** siapa owner Plan canonical yang akan MCR *invokes*.
- Belum ada perubahan kode (investigasi/audit murni). Repo bersih.
