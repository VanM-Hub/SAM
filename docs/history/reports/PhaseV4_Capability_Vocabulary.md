# PHASE V4 — Capability Vocabulary (verifikasi + penetapan)

**Tanggal:** 2026-08-14
**Jenis:** Analisis kosakata domain Capability — verifikasi disambiguasi penamaan.
**Status:** ✅ **VERIFIKASI SELESAI — TIDAK ada perubahan kode** (tidak ada duplicate sejati, tidak ada collision nyata → tidak ada rename).
**Cakupan:** 111 definisi class ber-catatan `Capability`, 11 nama berulang (≥2x).

---

## Ringkasan

Tidak ada perubahan kode. 11 nama Capability didefinisikan ≥2x (111 definisi total), **tidak ada duplicate sejati** dan **0 collision runtime aktif**. Semua = representasi beda yang **SAH** di bounded context terpisah.

---

## 1. Nama berulang — verifikasi

| Nama | Definisi | Hasil verifikasi |
|---|---|---|
| `Capability` | 3 | execution connector DTO (`connector_capability`) vs domain `Entity` (`models.models`) vs SDK `ABC` (`sdk/base`) — beda total: DTO field (name/risk_level/requires_approval) vs Entity (capability_id/owner/permissions) vs ABC (`execute()` abstract) |
| `ProviderCapability` | 3 | execution protocol / base / interfaces — layer beda |
| `AgentCapability` | 2 | agent foundation / universal_agent foundation |
| `CapabilityMatrix` | 2 | connectors / observation |
| `CapabilityReport` | 2 | connectors / execution connectors |
| `ConnectorCapability` | 2 | connectors / execution connector protocol |
| `CapabilityStatus` | 2 | delegated_authority (bukti milestone certification) vs observation (runtime availability/readiness/operational) — beda total |
| `CapabilityCard` | 2 | execution dashboard / integration dashboard |
| `CapabilityDescriptor` | 2 | models domain / runtime capability_manager models |
| `ModelCapability` | 2 | model_runtime / universal_ai provider_descriptor |
| `CapabilityBinding` | 2 | universal_tool / universal_workflow |

### Verifikasi contoh (kandidat paling berisiko duplicate sejati)

- **`Capability` (3)**: `execution/connectors/connector_capability.py` = DTO (name/description/risk_level/requires_approval/requires_guardian + `builtin()`); `models/models.py` = `Entity` subclass (capability_id/name/owner/version/permissions/dependencies/risk_level); `sdk/base.py` = `ABC` dengan `@abstractmethod execute()`. **3 representasi beda total — bukan duplicate sejati.**
- **`CapabilityStatus` (2)**: `delegated_authority` = bukti status per-milestone untuk certification (milestone/name/level/unverified|unit|integration|real|blocked); `observation/capability.py` = status runtime (availability/readiness/operational/has_dashboard/has_health...). **Beda domain, beda field — bukan duplicate sejati.**

---

## 2. Verifikasi collision

Scan seluruh src + tests: **0 collision** — tidak ada file yang mengimpor nama Capability yang sama dari ≥2 jalur berbeda dalam satu namespace (11 nama verifikasi).

---

## 3. Keputusan V4 Capability vocabulary

| Pertanyaan | Jawaban |
|---|---|
| Ada duplicate sejati `Capability*`? | **Tidak.** |
| Ada collision runtime aktif? | **Tidak** — 0. |
| Perlu rename? | **Tidak.** |
| Perlu merge/consolidate? | **Tidak.** |

**Catatan:** `Capability` punya makna multi-layer yang sah: deklarasi capability runtime (SDK), representasi domain terdaftar (Entity), dan DTO operational connector. Ini representasi yang benar per layer — bukan cacat.

---

## 4. Lanjut

V4 selesai verifikasi. Lanjut **V5 Mission vocabulary** (deep — melampaui representasi V2, mencakup pipeline/kosakata mission yang lebih luas).
