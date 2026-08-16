"""conversational_reasoner_adapter.py — Adapter infra ConversationalReasoner (AD-ENG-004).

INFRASTRUCTURE adapter yang membungkus existing `ProviderExecutor` (provider
layer) utk menghasilkan respons percakapan. Memenuhi application port
`ConversationalReasoner` (Clean Architecture: application bergantung port;
infrastructure mengimplementasikan & di-inject via DI).

AD-ENG-004 (ACCEPTED FOR IMPLEMENTATION):
  - Strategi adapter: ProviderConversationalReasonerAdapter -> existing
    ProviderExecutor. BUKAN meng-inject LLM sbg `reasoning_fn` ke
    StructuredReasoningEngine.
  - Hanya menyentuh provider name + ProviderExecutor. TIDAK memanggil
    MissionUXService / decide() / runner / canonical connector.
  - `execute("...", "chat", ...)` = panggilan LLM non-mutating utk TEKS;
    bukan jalur eksekusi misi, bukan m8_002_build.
  - Provider unavailable/invalid -> ConversationalResponse(ok=False,
    error_kind, content=<teks jujur fail-closed>). TIDAK kembali ke empty
    mission state.
  - Metada ta observability (provider_id/model_id) di-EXPOSE TERPISAH
    (observability trace) — BUKAN bagian ConversationalResponse (Refinement
    Van, rev 1.1). Application response = apa yg SAM katakan.
  - Normalisasi di adapter: ekstrak teks, sanitasi secret, length guard,
    fallback fail-closed (reuse pola `_extract_ai_text` / M8-005 / M10-002 /
    M10-006 / M14-005).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, Optional

from sam.application.ux.conversational_reasoner import (
    ConversationContext,
    ConversationalReasoner,
    ConversationalResponse,
)

# Panjang konten maksimum (application guard agar teks LLM tidak tak-berbatas).
_MAX_CONTENT_CHARS = 4000
# Marker secret yg WAJIB tidak pernah bocor ke content (defensive; M8-005/M10-002).
_SECRET_MARKERS = (
    "ghp_",
    "gho_",
    "ghs_",
    "sk-",
    "sk_",
    "Bearer ",
    "authorization:",
    "api_key",
    "api-key",
    "password",
    "secret",
    "DEEPSEEK_API_KEY",
)


@dataclass(frozen=True)
class ConversationalTrace:
    """Observability metadata SEPARATE (bukan application response).

    Bagaimana response dihasilkan: provider/model yang dipakai, durasi, jumlah
    warning. Application TIDAK membacanya utk logic; ini utk AUDIT/TRACE di
    infrastructure. (Refinement Van, AD-ENG-004 rev 1.1.)
    """

    provider_id: str = ""
    model_id: str = ""
    elapsed_ms: int = 0
    external_calls: int = 0
    ok: bool = True
    error_kind: str = ""


def _sanitize(text: str) -> str:
    """Hapus/tutupi marker secret yg mungkin bocor di teks LLM (defensive)."""
    out = text or ""
    for marker in _SECRET_MARKERS:
        out = re.sub(re.escape(marker), "[redacted]", out, flags=re.IGNORECASE)
    return out


def _normalize(raw: Dict[str, Any]) -> str:
    """Ekstrak kolom content dari respons ProviderExecutor (chat completion).

    Menangani keragaman wire: `payload.raw.choices[].message.content` (OpenAI-
    compatible) maupun fallback `payload.raw.content` / `raw.content`. Reuse
    pola `MissionUXService._extract_ai_text` (pola yang sama di service.py).
    """
    payload = raw.get("payload") or {}
    cand = payload.get("raw") or raw
    if not isinstance(cand, dict):
        cand = {}
    choices = cand.get("choices") or []
    if choices and isinstance(choices[0], dict):
        msg = choices[0].get("message") or {}
        content = msg.get("content")
        if content:
            return str(content)
    direct = cand.get("content") or payload.get("content")
    if direct:
        return str(direct)
    # Model response API mirip `{"payload": {"raw": {"content": ...}}}`.
    if not choices and cand.get("message") and isinstance(cand["message"], dict):
        content = cand["message"].get("content")
        if content:
            return str(content)
    return ""


class ProviderConversationalReasonerAdapter(ConversationalReasoner):
    """Adapter infrastructure: existing ProviderExecutor -> ConversationalResponse.

    DI: `executor` adalah instance `ProviderExecutor` (di-inject dari composition
    root). Default dibuat saat runtime (lazy import dai provider layer). Provider/
    model untuk CHAT dipilih DI SINI (infrastructure), BUKAN di application.
    """

    def __init__(
        self,
        executor: Optional[Any] = None,
        provider_id: str = "deepseek",
        model_id: str = "deepseek-chat",
        fallback_provider_id: Optional[str] = "ollama",
        fallback_model_id: str = "gemma3:1b",
        max_content_chars: int = _MAX_CONTENT_CHARS,
        temperature: float = 0.4,
        max_tokens: int = 512,
        timeout_seconds: int = 45,
        system_prompt: str = (
            "Kamu adalah asisten percakapan SAM. Jawab singkat, ramah, dan "
            "jujur dalam Bahasa Indonesia. Jangan pernah mengarang perintah, "
            "tindakan, atau hasil eksekusi. Jawabanmu HANYA teks respons; "
            "jangan berpura-pura SAM telah menjalankan apa pun."
        ),
    ) -> None:
        """Wire executor provider + konfigurasi CHAT (infrastructure).

        provider/model id hanya ADA di adapter + composition root (D-04):
        application layer tidak pernah membaca nama provider/model dari ini.
        """
        self._executor = executor
        self._provider_id = provider_id
        self._model_id = model_id
        self._fallback_provider_id = fallback_provider_id
        self._fallback_model_id = fallback_model_id
        self._max_content_chars = int(max_content_chars)
        self._temperature = float(temperature)
        self._max_tokens = int(max_tokens)
        self._timeout_seconds = int(timeout_seconds)
        self._system_prompt = system_prompt

    # ------------------------------------------------------------------
    # lifecycle: executor dibentuk eksekusi (lazy) bila belum di-inject
    # ------------------------------------------------------------------
    def _resolve_executor(self) -> Any:
        if self._executor is not None:
            return self._executor
        # Lazy import infra layer (provider). Default = ProviderExecutor nyata.
        # Bila TIDAK punya kredensial -> execute() threw ProviderUnavailableError.
        from sam.providers.execution.provider_executor import ProviderExecutor

        self._executor = ProviderExecutor()
        return self._executor

    # ------------------------------------------------------------------
    # helpers pemilihan provider (infrastructure-only, honest)
    # ------------------------------------------------------------------
    def _provider_available(self, executor: Any, provider_id: str) -> bool:
        try:
            return bool(executor.available(provider_id))
        except Exception:  # noqa: BLE001 — defensive: avoid crash
            return False

    def _build_prompt(self, ctx: ConversationContext) -> str:
        """Rakit prompt dari ConversationContext (application policy: history
        terbatas; evidence & active_mission HANYA bila relevan)."""
        lines: list[str] = []
        # Konteks misi aktif bila relevan (ringkas, tanpa secret).
        if ctx.active_mission is not None and ctx.active_mission.operation:
            m = ctx.active_mission
            brief = []  # type: list[str]
            brief.append(f"operation:{m.operation}")
            if m.status:
                brief.append(f"status:{m.status}")
            if m.target:
                brief.append(f"target:{m.target}")
            lines.append("SAM sedang memiliki misi aktif: " + "; ".join(brief))
        # History terbatas (application policy; angka diputuskan orchestrator).
        for turn in ctx.history:
            who = "user" if turn.role == "user" else "assistant"
            lines.append(f"{who}: {turn.content}")
        lines.append(f"user: {ctx.user_message}")
        return "\n".join(lines) if lines else ctx.user_message

    # ------------------------------------------------------------------
    # PORT METHOD — implementasi `ConversationalReasoner.converse`
    # ------------------------------------------------------------------
    def converse(self, ctx: ConversationContext) -> ConversationalResponse:
        """Hasilkan respons percakapan dari existing ProviderExecutor.

        Fail-closed: provider unavailable/invalid/output gagal dinormalisasi
        -> ConversationalResponse(ok=False, error_kind, content=<teks jujur>).
        TIDAK kembali ke empty mission state (keputusan Van).
        """
        if not ctx.user_message.strip():
            return ConversationalResponse(
                content="SAM menunggu pesan Anda.",
                ok=True,
            )

        executor = self._resolve_executor()
        provider_id = self._provider_id
        model_id = self._model_id
        # Fail-closed: provider utama tidak tersedia -> coba fallback lokal.
        # Bila keduanya tidak tersedia -> unavailable (jujur).
        if not self._provider_available(executor, provider_id):
            if self._fallback_provider_id and self._provider_available(
                executor, self._fallback_provider_id
            ):
                provider_id = self._fallback_provider_id
                model_id = self._fallback_model_id
            else:
                return ConversationalResponse(
                    content=(
                        "SAM tidak dapat menyusun jawaban saat ini karena "
                        "penyedia AI tidak tersedia. Silakan coba lagi nanti."
                    ),
                    ok=False,
                    error_kind="unavailable",
                )

        prompt = self._build_prompt(ctx)
        try:
            raw = executor.execute(
                provider_id,
                "chat",
                {
                    "prompt": prompt,
                    "model": model_id,
                    "max_tokens": self._max_tokens,
                    "temperature": self._temperature,
                    "system": self._system_prompt,
                },
                timeout_seconds=self._timeout_seconds,
            )
        except Exception as exc:  # noqa: BLE001 — provider/network failure
            return ConversationalResponse(
                content=(
                    "SAM tidak dapat menyusun jawaban saat ini karena "
                    f"penyedia AI gagal ({type(exc).__name__}). Coba lagi."
                ),
                ok=False,
                error_kind="unavailable",
            )

        content = _normalize(raw)
        if not content.strip():
            return ConversationalResponse(
                content="SAM tidak menerima jawaban yang valid dari penyedia AI.",
                ok=False,
                error_kind="invalid",
            )

        content = _sanitize(content).strip()
        warnings: list[str] = []
        if len(content) > self._max_content_chars:
            content = content[: self._max_content_chars]
            warnings.append("Konten dipotong karena melebihi batas aman.")

        # Observability trace (SEPARATE dari contract response — tersedia utk
        # audit/trace di infrastructure; TIDAK dibaca application utk logic).
        # Simpan sebagai atribut non-contract (diakses penguji/observability).
        self.last_trace = ConversationalTrace(
            provider_id=provider_id,
            model_id=model_id,
            external_calls=1,
            ok=True,
            error_kind="",
        )
        return ConversationalResponse(
            content=content,
            ok=True,
            warnings=tuple(warnings),
        )
