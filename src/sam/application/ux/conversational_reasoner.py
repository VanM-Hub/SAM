"""conversational_reasoner.py — Port aplikasi ConversationalReasoner (AD-ENG-004).

Canonical application port utk menghasilkan RESPONS PERCAKAPAN (CHAT) di
application boundary (Clean Architecture). AD-ENG-004 (ACCEPTED FOR
IMPLEMENTATION, 2026-08-16).

Prinsip:
  - Application bergantung pada ABSTRAKSI ini, bukan pada provider/LLM/httpx.
  - Port READ-ONLY: hanya `converse(ctx) -> ConversationalResponse`. Tidak ada
    run/execute/approve/mutation. LLM response = data/text; TIDAK pernah
    menjadi command/execution request.
  - `ConversationalResponse` = APA yang SAM katakan (application response),
    BERSIH dari metadata observability (provider/model). Metadata observability
    (provider_id/model_id) hidup TERPISAH utk audit/trace, bukan bagian contract
    application response (Refinement Van, AD-ENG-004 rev 1.1).
  - `history <= N turn` adalah APPLICATION POLICY (diatur orchestrator), BUKAN
    bagian semantic contract. Contract menerima tuple; batas jumlah di luar.
  - `active_mission` & `evidence` hanya disertakan BILA RELEVAN (tidak dump
    seluruh state ke prompt).

Kontrak (frozen/immutable):
  - ConversationContext : input port (persistensi apa yg dibutuhkan).
  - ConversationalResponse: output port (apa yg SAM katakan + status jujur).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Protocol, Tuple, runtime_checkable

from sam.governed_reasoning.structured_reasoning import EvidenceRef  # canonical frozen contract


@dataclass(frozen=True)
class MessageTurn:
    """Satu giliran pesan utk konteks percakapan (non-secret, di-sanitize).

    Hanya memuat role + content ringkas kiriman/answer. TIDAK memuat
    conversation/session ref penuh, TIDAK memuat secret. Jumlah turn dibatasi
    APPLICATION POLICY oleh orchestrator (bukan semantic contract).
    """

    role: str  # "user" | "assistant"
    content: str


@dataclass(frozen=True)
class MissionBrief:
    """Ringkasan misi aktif yang aman untuk prompt (tersanitasi).

    Hanya field ringkas tanpa secret: operation, approved state, status, dan
    ringkasan target — bukan dump state mission. Disertakan HANYA bila relevan
    (Refinement Van / D-12).
    """

    operation: str = ""
    status: str = ""  # mis. "waiting_approval" / "approved" / "running"
    target: str = ""  # external target ringkas (repo/url) jika ada
    summary: str = ""  # kalimat ringkas apa yg sedang dilakukan


@dataclass(frozen=True)
class ConversationContext:
    """Input port: konteks penuh yg dibutuhkan utk satu respons percakapan.

    Immutable. `conversation_id` utk trace; `user_message` pesan terbaru user;
    `history` giliran sebelumnya (di-sanitize, jumlah dibatasi oleh policy);
    `evidence_refs` referensi bukti yang RELEVAN; `active_mission` ringkas bila
    ada; `language_hint` preferensi bahasa (default id).
    """

    conversation_id: str
    user_message: str
    history: Tuple[MessageTurn, ...] = field(default_factory=tuple)
    evidence_refs: Tuple[EvidenceRef, ...] = field(default_factory=tuple)
    active_mission: Optional[MissionBrief] = None
    language_hint: str = "id"


@dataclass(frozen=True)
class ConversationalResponse:
    """Output port: apa yang SAM katakan + status jujur.

    BERSIH dari metadata observability (provider/model) — Refinement Van.
    `ok=True` bila berhasil menyusun jawaban; `ok=False` + `error_kind` +
    content teks jujur (fail-closed) bila provider unavailable/invalid/blocked.
    `warnings` = catatan non-blokir (mis. konten di-truncate).
    """

    content: str
    ok: bool = True
    error_kind: str = ""  # "" | "unavailable" | "invalid" | "blocked"
    warnings: Tuple[str, ...] = field(default_factory=tuple)


@runtime_checkable
class ConversationalReasoner(Protocol):
    """Application port (interface).

    Application/UI HANYA melihat protokol ini. Implementasi nyata
    (adapter infrastructure membungkus ProviderExecutor) di-inject via DI.
    Port read-only: satu method `converse`, tidak ada aksi/eksekusi.
    """

    def converse(self, ctx: ConversationContext) -> ConversationalResponse: ...
