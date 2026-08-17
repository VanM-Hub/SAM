# W3 — Audit Pre-Coding: Representasi Proposal & Clarification

Tanggal: 2026-08-17. Status: AUDIT (belum coding).

## Tujuan
Tentukan apakah ConversationService + MissionUXService + UxMissionState +
MissionPlan + decision lifecycle dapat merepresentasikan proposal & clarification
untuk skenario W3: user -> "Periksa OpenClaw saya."

## 10 Poin Wajib vs Dukungan Model Existing

| # | Wajib W3 | Dukungan model | Verdict |
|---|----------|----------------|---------|
| 1 | SAM paham intent | `MissionUXService._interpret("Periksa OpenClaw saya")` -> `environment.observe`, target `OpenClaw` (via LLM fallback; regex offline tak kenal "openclaw") | ADA |
| 2 | SAM temukan Ward tersedia | `resolve_ward(name)` + `list()` + `auth_ward` (tenant+status+scope) | ADA |
| 3 | Target ambigu -> bertanya | **TIDAK ada state/status clarification/ambiguous/awaiting di src/sam** | **HILANG** |
| 4 | Target jelas -> proposal | `submit()` -> MissionPlan (PENDING/DRAFT) + UxMissionState | ADA |
| 5 | User konfirmasi | `decide()` approve/reject; read-only `environment.observe` punya `approval_required=False` -> TIDAK ada gate konfirmasi | **SEBAGIAN** |
| 6 | Mission -> lifecycle canonical | `_execute_mission` -> `run_mission` (SAMA boundary) | ADA |
| 7 | Ward governance dilalui | `_maybe_resolve_ward` -> `auth_ward` (tenant+status+capability scope) | ADA |
| 8 | OpenClaw diobservasi | `OpenClawObservationAdapter` (M14 canonical, `_run_ward_openclaw_observe`) | ADA |
| 9 | Evidence nyata | timeline evidence `openclaw_ward_observation` (components/runtime_status) | ADA |
| 10 | SAM jelaskan hasil | `_state_to_assistant_text` | ADA |

## Boundary yang Hilang / Sebagian

### Poin 3 — clarification / target-ambigu
- `UxStateStatus`: NONE/RECEIVED/UNDERSTOOD/WAITING_APPROVAL/APPROVED/REJECTED/
  RUNNING/COMPLETED/BLOCKED/FAILED/RETRYABLE. TIDAK ada "clarification".
- `UxMissionState`: tidak ada field utk pertanyaan klarifikasi / pilihan target.
- Tidak ada mekanisme bertanya di seluruh `src/sam` (cari "clarif|ambigu|ask").

### Poin 5 — konfirmasi user utk read-only
- `_operation_is_read_only("environment.observe")` = True -> approval_required=False.
- W2 (Option C) SUDAH memutuskan read-only TIDAK butuh approval (execute_policy_authorized).
- W3 Van bilang "user mengonfirmasi" -> potensi konflik dgn W2.

## Keputusan Audit (belum final - usulan)

Model existing CUKUP menampung 8/10. Poin 3 & 5 TIDAK butuh state machine baru;
dapat direalisasikan memakai jalur CHAT yang SUDAH ADA (percakapan bertanya &
konfirmasi), lalu perintah yang sudah jelas diteruskan ke mission canonical:

- Poin 3 (ambigu -> tanya): saat target tak jelas, ConversationService mengeluarkan
  pertanyaan via jalur CHAT (bukan mission state). User menjawab -> barulah mission.
  TIDAK menambah state machine baru.
- Poin 5 (konfirmasi): SAM bertanya via chat "SAM akan mengobservasi OpenClaw,
  lanjut?" -> user "ya" -> eksekusi canonical. Ini konfirmasi perCAKAPAN, bukan
  approval gate formal -> tidak mengubah perilaku read-only W2.

## Yang Perlu Keputusan Van
1. Apakah konfirmasi W3 poin 5 = konfirmasi percakapan (chat) ATAU approval gate
   formal? (Rekomendasi: percakapan, agar tidak bentrok dgn W2 read-only.)
2. Diterima usulan "clarification via jalur CHAT existing, tanpa state machine baru"?

Bila Van setuju -> TIDAK STOP -> lanjut coding W3.
Bila Van ingin clarification jadi state machine tersendiri -> telaah ulang scope.
