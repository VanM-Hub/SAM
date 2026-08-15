# PHASE V2 — Mission Representation (verifikasi + penetapan)

**Tanggal:** 2026-08-14
**Jenis:** Analisis kontrak + consumer — verifikasi disambiguasi penamaan domain Mission.
**Status:** ✅ **VERIFIKASI SELESAI — TIDAK ada perubahan kode** (tidak ada duplicate sejati, tidak ada collision nyata → tidak ada rename).
**Cakupan:** Semua class bernama `Mission*` yang berulang antar bounded context.

---

## Ringkasan

Tidak ada perubahan kode. Meskipun banyak class `Mission*` bernama sama di berbagai paket, **tidak ada satupun yang duplicate sejati** (definisi identik untuk konsep sama) dan **tidak ada collision runtime aktif**. Semua = representasi beda yang **SAH** di bounded context terpisah. Konsisten dengan keputusan Van (tidak rename kecuali ada duplicate sejati + collision nyata).

**Temuan kunci:** pola penamaan `*Preview` sudah dipakai secara konsisten di seluruh codebase — `PolicyPreview`, `WorkflowPreview`, `MissionPreview`, dan (hasil V2-EXEC-001) `KnowledgeFactPreview`/`KnowledgeRelationPreview`. Ini mengonfirmasi keputusan Van (Opsi B) sebagai pola yang sudah established, bukan inovasi baru.

---

## 1. Nama yang berulang (multi-definisi) — verifikasi

Berikut nama class `Mission*` yang didefinisikan di ≥2 paket berbeda. Semua diverifikasi = **bukan duplicate sejati** (struktur/domain beda), tanpa collision.

| Nama | Definisi (jumlah) | Bounded context | Bentuk |
|---|---|---|---|
| `Mission` | 3 | contracts / execution_runtime / operations | pydantic BaseModel (deklarasi) vs runtime executor vs aggregate dataclass |
| `MissionStatus` | 3 | contracts / mission_runtime / operations.brain.guardian | str Enum (lifecycle) vs dataclass (readiness) vs dataclass (counters) |
| `MissionState` | 3 | agent.session / mission_runtime / operations | dataclass (Created...) vs dataclass (open/active/closed) vs Enum (CREATED...) |
| `MissionContext` | 4 | agent.session / execution_runtime / mission_runtime / platform | — |
| `MissionPlan` | 3 | agent.planner / application.ux / operations.orchestrator | — |
| `MissionRegistry` | 3 | agent.session / application.ux / mission_runtime | — |
| `MissionRequest` | 3 | api.routes / application.ux / mission_runtime | — |
| `MissionSnapshot` | 3 | agent.session / mission_runtime / platform | — |
| `MissionStep` | 3 | agent.planner / execution_runtime.m7 / operations | — |
| `MissionSummary` | 3 | governance_intelligence / mission_runtime / operations.brain.reasoning | — |
| `MissionRepository` | 3 | application.ux (Protocol) / governance_intelligence / storage | Protocol vs QueryOnlyRepository vs AbstractRepository |
| `MissionBuilder` | 2 | agent.planner / mission_runtime | — |
| `MissionSession` | 2 | agent.session / operations | — |
| `MissionTimeline` | 2 | mission_runtime / operations | — |
| `MissionTimelineView` | 2 | observation / platform | — |
| `MissionReadiness` | 2 | governance_intelligence / platform | — |
| `MissionDashboardDTO` | 2 | operations.dashboard_model / operations.brain.reasoning | — |

### Butir verifikasi contoh (yang paling berpotensi duplicate sejati)

- **`Mission`** (3): `contracts/mission.py` = pydantic `BaseModel` (id/name/description/objectives/priority/min_health — **deklarasi**); `execution_runtime/m7_mission_framework.py` = class runtime (mission_id/title/audit/steps/artifact_path + `.add()`/`.run()` — **executor**); `operations/mission_controller.py` = frozen dataclass (mission_id/name/state/state_history/tags — **aggregate state**). Struktur beda total, konsep beda.
- **`MissionStatus`** (3): `contracts` = `str, Enum` (active/degraded/failed/completed — lifecycle); `mission_runtime` = frozen dataclass (state:"ready" + `is_ready` — readiness); `operations/brain/guardian` = frozen dataclass (active/completed/failed/stalled counters — monitoring). Bukan enum identik (beda dari pola duplicate RuntimeState/EvidenceType V1).
- **`MissionState`** (3): nilai state beda (Created... vs open/active/closed vs CREATED...), struktur beda.

---

## 2. Verifikasi collision

Scan seluruh src + tests: **TIDAK ada file yang mengimpor nama `Mission` yang sama dari ≥2 jalur berbeda dalam satu namespace** (untuk semua 17 nama berulang di atas).

Menariknya: `MissionPreview` & `MissionPreviewConsumer` (`runtime_service/api/mission_preview.py`) sudah memakai pola `*Preview` — konsisten dengan `PolicyPreview`/`WorkflowPreview`/`KnowledgeFactPreview`. Tidak ada rename diperlukan; pola penamaan preview sudah diselaraskan.

---

## 3. Keputusan V2 Mission representation

| Pertanyaan | Jawaban |
|---|---|
| Ada duplicate sejati `Mission*`? | **Tidak** (semua representasi beda, struktur/domain beda). |
| Ada collision runtime aktif? | **Tidak** — 0 untuk 17 nama berulang. |
| Perlu rename? | **Tidak.** Tidak ada alasan arsitektural. |
| Perlu merge/consolidate? | **Tidak.** |

**Catatan:** cakupan Mission sangat luas (100+ class Mission* di banyak paket). Ini sesuai — SAM memiliki banyak layer mission (contracts → agent planner → mission_runtime → operations → platform → UX → governance). Setiap layer = bounded context sah dengan representasi mission-nya sendiri. Memaksa satu nama unik global = melanggar prinsip "Folder ≠ Semantic Identity" dan "duplicate name ≠ duplicate concept".

---

## 4. Kaitannya dengan V5

Sequence Van menaruh **V5 Mission vocabulary** setelah V3/V4. V2 ini memverifikasi `Mission`/`MissionStatus`/`MissionState` dst. Bila V5 menemukan collision nyata atau semantic ambiguity di kosakata mission yang lebih luas (mis. antar layer contract/execution/operations), itu akan menjadi scope V5, bukan sekarang.
