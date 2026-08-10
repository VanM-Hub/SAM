# AD-P2A — Owner Plan: Kandidat Canonical & Target Aktivasi

**Status:** Accepted (Architecture Discovery diterima)
**Tanggal:** 2026-08-11
**Tipe:** Architecture Decision (P2 Owner Plan Discovery → P2A activation plan)
**Otoritas:** Aster (Chief Architect), diteruskan via Van
**Menggantikan/melengkapi:** AD-P1R (`docs/decisions/AD-P1R_Status_Ownership_MCR_Baseline_P2.md`)

---

## Konteks

P2 investigasi mengidentifikasi beberapa kandidat owner Plan. Dari semua, `sam.agent.planner.MissionBuilder`
paling cocok secara semantik & arsitektural untuk Mission-level planning. Namun Astra menetapkan prinsip
yang sama seperti temuan `reasoning/engine.py`: **komponen yang paling cocok secara semantik BELUM otomatis
canonical owner jika belum operational path.**

## Keputusan Status

`sam.agent.planner.MissionBuilder` ditetapkan sebagai:

```
Canonical Plan Owner Candidate — strongest candidate
```
**(BUKAN) Canonal Plan Owner — ACCEPTED**

### Status per kriteria operational ownership

```
sam.agent.planner.MissionBuilder
    │
    ├── Mission composition        ✅
    ├── Pipeline semantics         ✅
    ├── run_mission_from_provider  ✅
    ├── Production caller          ❌
    └── Mission-reachable          ❌
```

## Alasan

- MissionBuilder ≠ planner generik: ia punya **mission composition → mission lifecycle → provider-aware mission path**.
- Ini lebih dekat dengan Mission-level planning responsibility dibanding
  `reasoning/planner.PlanningEngine`, `strategy.StrategyPlanner`, `autonomy_runtime.planning.PlanningEngine`
  (semua belum terbukti operational).
- Tetapi karena belum CALLED / belum ter-wire ke server/CLI → **belum ACCEPTED**.

## Boundary (keputusan penting anti God Object)

```
                    MCR
                     │
                     │ invokes
                     ▼
              MissionBuilder
                     │
                     ▼
              Action Plan
                     │
                     ▼
                 Governance
                     │
                     ▼
                 Execution
```

- **MCR** = owner **lifecycle orchestration** (tetap).
- **MissionBuilder** = owner **Plan construction**.
- **Governance** = owner **authorization**.
- **Execution** = owner **execution**.
- **Observation** = owner **observation**.
- **Reflection/Learning** = capability masing-masing.

> **Guardrail:** Owner lifecycle ≠ Owner seluruh capability. MCR TIDAK boleh membuat Plan sendiri.
> MissionBuilder TIDAK boleh jadi Cognitive Runtime (MCR/Reason/Plan/Govern/Execute sekaligus).

## Urutan yang Diorisasi (P2A ke depan)

```
P1 Revision ✅
   ↓
P2 Owner Plan Discovery ✅
   ↓
P2A Activate MissionBuilder        ← berikutnya
   ↓
Verify operational ownership
   (CALLED + MISSION-REACHABLE)
   ↓
P3 MCR invokes canonical Plan
   ↓
T1 Confidence contract
   ↓
T2 Observation contract
   ↓
T3 Execution contract
   ↓
End-to-end verification
   ↓
Wire MCR sebagai Mission runtime
```

## Definisi Final

- MCR = owner lifecycle orchestration.
- MissionBuilder = owner Plan construction (kandidat, menunggu aktivasi → verification → acceptance).
- Governance tetap eksternal (mandatory handoff di level MCR).

## Status
- **Menunggu P2A:** ACTIVATE/WIRE MissionBuilder ke Production Mission Path → Verify CALLED + MISSION-REACHABLE → baru Canonical Plan Owner.
- Belum ada perubahan kode (arsitektur/decision murni).
