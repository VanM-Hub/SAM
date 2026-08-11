"""Canonical AI Bridge - M3 (Canonical Execution Consolidation).

Mengarahkan invocation AI dari `universal_ai` (yang default-nya MOCK) ke
jalur HTTP NYATA canonical `ProviderExecutor` (providers/execution/
provider_executor.py). Non-destruktif: file `universal_ai/*` tetap ada sebagai
LEGACY; adapter tidak diubah di tempat — transport nyata disuntikkan saat
run-time.

Prinsip:
- Tanpa kredensial (env API key kosong / offline) -> ProviderUnavailableError
  -> NO EXTERNAL SIDE EFFECT (aman, bukan mock yang seolah sukses).
- Dengan kredensial -> HTTP nyata via httpx -> hasil nyata ter-verifikasi.
- Tidak ada kredensial di-hardcode (baca dari env saat execute).

Modul ini BUKAN executor paralel; ia hanya JEMBATAN agar invocation dari
universal_ai berjalan lewat ProviderExecutor canonical.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from sam.providers.execution.provider_executor import (
    ProviderExecutor,
    ProviderUnavailableError,
)

# Import kontrak universal_ai hanya untuk tipe mapping (akan diarahkan ke nyata).
try:  # pragma: no cover - import opsional bila universal_ai tersedia
    from sam.universal_ai.adapter_framework import (
        NormalizedResponse,
        ProviderAdapter,
        ProviderRequest,
        ProviderAdapterError,
    )
    _HAS_UNIVERSAL_AI = True
except ImportError:  # pragma: no cover
    _HAS_UNIVERSAL_AI = False


class CanonicalAIAdapter:
    """Transport nyata untuk adapter universal_ai -> ProviderExecutor HTTP.

    Memenuhi kontrak `ProviderAdapter.invoke()` (universal_ai) dengan memanggil
    jalur HTTP NYATA canonical. Bisa dipakai langsung sebagai `transport`
    adapter openai/anthropic/google universal_ai (menggantikan mock default).
    """

    def __init__(
        self,
        *,
        provider_id: str,
        operation: str = "chat",
        timeout_seconds: int = 60,
        executor: Optional[ProviderExecutor] = None,
    ) -> None:
        self._provider_id = provider_id
        self._operation = operation
        self._timeout = timeout_seconds
        self._executor = executor or ProviderExecutor()

    # -- kontrak mapping ProviderAdapter (universal_ai) --

    def invoke(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Transport universal_ai: terima payload OpenAI-style (dict) -> dict nyata.

        Kontrak adapter universal_ai memanggil `self._transport(payload)` dengan
        `payload` berupa dict OpenAI wire (`model`, `messages`, ...). Jalur ini
        meneruskan ke `ProviderExecutor.execute()` (HTTP nyata) dan mengembalikan
        dict OpenAI-style sehingga `_normalize` universal_ai tetap berfungsi.

        Melempar ProviderUnavailableError bila tak ada kredensial (transparan:
        NO SIDE EFFECT, bukan mock sukses).
        """
        prompt = self._extract_prompt(payload)
        provider_payload: Dict[str, Any] = {
            "prompt": prompt,
            "model": payload.get("model") or payload.get("model_id") or None,
            "parameters": {
                k: v for k, v in payload.items()
                if k not in ("model", "messages", "prompt", "model_id")
            },
        }
        raw = self._executor.execute(
            self._provider_id,
            self._operation,
            provider_payload,
            timeout_seconds=self._timeout,
        )
        # Normalisasi hasil nyata ke bentuk OpenAI-style untuk `_normalize`.
        choices = raw.get("choices")
        if not choices and "content" in raw:
            choices = [{"message": {"content": raw["content"]}}]
        return {
            "choices": choices or [{"message": {"content": self._extract_text(raw)}}],
            "model": raw.get("model") or provider_payload.get("model"),
            "usage": raw.get("usage", {}),
            "_canonical_meta": {
                "via": "canonical ProviderExecutor (HTTP)",
                "raw": raw,
            },
        }

    def invoke_request(self, request: "ProviderRequest") -> "NormalizedResponse":
        """Pemakaian langsung dengan kontrak ProviderRequest (bukan transport)."""
        payload = {
            "model": request.model_id or "",
            "messages": [{"role": "user", "content": request.prompt}],
            "prompt": request.prompt,
            **dict(request.parameters),
        }
        raw_dict = self.invoke(payload)
        text = self._extract_text(raw_dict)
        return NormalizedResponse(
            text=text,
            provider_id=self._provider_id,
            model_id=str(payload.get("model") or ""),
            metadata={
                "operation": self._operation,
                "raw": raw_dict.get("_canonical_meta", {}),
                "via": "canonical ProviderExecutor (HTTP)",
            },
            finish_status="complete",
            error=None,
        )

    @staticmethod
    def _extract_prompt(payload: Dict[str, Any]) -> str:
        if "prompt" in payload:
            return str(payload["prompt"])
        messages = payload.get("messages") or []
        if messages and isinstance(messages[-1], dict):
            return str(messages[-1].get("content") or "")
        return ""

    @staticmethod
    def _extract_text(raw: Dict[str, Any]) -> str:
        """Ekstrak teks dari respons HTTP nyata provider (OpenAI-compatible)."""
        try:
            choices = raw.get("choices") or []
            if choices:
                msg = choices[0].get("message") or {}
                return str(msg.get("content") or "")
            content = raw.get("content")
            if content is not None:
                return str(content)
        except Exception:  # noqa: BLE001
            pass
        return str(raw)  # fallback: seluruh respons sebagai teks bukti

    # -- membantu credential gate (P4) --

    def has_credentials(self) -> bool:
        try:
            cfg = self._executor.config(self._provider_id)
            return cfg.has_credentials()
        except Exception:  # noqa: BLE001
            return False


def real_ai_transport(
    provider_id: str,
    operation: str = "chat",
    timeout_seconds: int = 60,
) -> Any:
    """Suntikkan transport nyata untuk adapter universal_ai (menggantikan mock).

    Returns object yang bisa di-assign ke `adapter._transport` atau diteruskan
    sebagai `transport=` saat membangun adapter openai/anthropic/google.
    """
    bridge = CanonicalAIAdapter(
        provider_id=provider_id,
        operation=operation,
        timeout_seconds=timeout_seconds,
    )
    return bridge.invoke


def wire_provider_adapter(adapter: Any) -> bool:
    """Ganti transport mock adapter universal_ai dengan jalur canonical HTTP.

    `adapter` = instance universal_ai adapter (OpenAIAdapter/GoogleAdapter/...).
    Meng-`setattr` internal `_transport` ke jembatan canonical (jika ada).

    Returns True bila berhasil di-wire, False bila adapter tidak punya slot
    transport (mis. bentuk tidak dikenali).
    """
    provider_id = getattr(adapter, "provider_id", "")
    if not provider_id:
        return False
    transport = real_ai_transport(provider_id)
    if hasattr(adapter, "_transport"):
        adapter._transport = transport  # noqa: SLF001 - injeksi transport canonical
        return True
    return False
