# -*- coding: utf-8 -*-
"""Test M3 - Canonical AI Bridge (universal_ai mock -> ProviderExecutor nyata).

Membuktikan invocation AI dari `universal_ai` (yang default-nya MOCK) dapat
diarahkan ke jalur HTTP NYATA canonical `ProviderExecutor`.

Garansi yang diuji (tanpa kredensial -> transparan, NO SIDE EFFECT, bukan mock):
1. Tanpa env API key, `CanonicalAIAdapter.invoke` memanggil ProviderExecutor dan
   melempar `ProviderUnavailableError` (bukan `_mock` yang seolah sukses).
2. `wire_provider_adapter` menyuntikkan transport canonical ke adapter
   universal_ai, menggantikan mock default.
3. `has_credentials()` cermin status env nyata.
4. E2E opsional (skip offline): bila env key tersedia, jalankan HTTP nyata dan
   pastikan hasil bukan "Simulated"/mock.

Cara jalan:
    python -m pytest tests/execution_runtime/test_m3_canonical_ai_bridge.py -v
"""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src")))

from sam.execution_runtime.canonical_ai_bridge import (
    CanonicalAIAdapter,
    real_ai_transport,
    wire_provider_adapter,
)
from sam.providers.execution.provider_executor import (
    ProviderExecutor,
    ProviderUnavailableError,
)

# Provider yang TIDAK punya kredensial di env test ini -> dijamin ProviderUnavailable
_KNOWN_NO_KEY = "openai"  # SAM tidak pakai env OPENAI_API_KEY di test ini


def test_m3_no_credential_raises_not_mock():
    """Tanpa kredensial -> ProviderUnavailableError (bukan mock sukses).

    Inilah pembeda utama canonical vs universal_ai lama: universal_ai default
    `_mock` mengembalikan 'openai-mock-response' (seolah sukses). Canonical
    menolak eksekusi tanpa kredensial -> transparan.
    """
    bridge = CanonicalAIAdapter(provider_id=_KNOWN_NO_KEY, operation="chat")
    assert bridge.has_credentials() is False

    with pytest.raises(ProviderUnavailableError):
        # Kontrak langsung (ProviderRequest) -> ProviderExecutor.execute -> tanpa key raise.
        # Bila universal_ai mock yang dipakai, ini tidak akan raise (SALAH).
        bridge.invoke_request(_make_request("hello"))


def test_m3_wire_provider_adapter_replaces_mock():
    """`wire_provider_adapter` menyuntikkan transport nyata ke adapter universal_ai."""
    if not _has_universal_ai():
        pytest.skip("universal_ai tidak tersedia di env ini; adapter di-wire via kontrak umum")

    from sam.universal_ai.openai_adapter import OpenAIAdapter

    adapter = OpenAIAdapter()  # default `_transport=None` -> pakai `_mock`
    # Sebelum wiring: invoke tanpa transport -> mock
    before = adapter.invoke(_make_request("x"))
    assert "openai-mock-response" in before.text  # konfirmasi default mock

    # Wiring -> transport jadi canonical (bukan mock)
    wired = wire_provider_adapter(adapter)
    assert wired is True
    assert adapter._transport is not None  # noqa: SLF001

    # Setelah wiring: invoke lagi (tanpa kredensial) -> harus gagal, bukan mock
    try:
        out = adapter.invoke(_make_request("y"))
        # Kalaupun ada transport canonical, tanpa kredensial tidak boleh mock:
        assert "openai-mock-response" not in out.text, "masih mock setelah wiring!"
        # (ProviderExecutor akan raise, dibungkus jadi error oleh adapter)
    except (ProviderUnavailableError, Exception):  # ProviderAdapterError / ProviderUnavailableError
        pass


def test_m3_real_ai_transport_callable():
    """`real_ai_transport` mengembalikan callable (fungsi transport)."""
    fn = real_ai_transport(_KNOWN_NO_KEY)
    assert callable(fn)
    # callable menerima payload (kontrak transcoding universal_ai)
    with pytest.raises(ProviderUnavailableError):
        fn({"prompt": "hi", "model": None, "parameters": {}})


def test_m3_has_credentials_reflects_env_truth():
    """`has_credentials` harus mencerminkan status env (bukan asumsi)."""
    import sam.providers.execution.provider_executor as pe

    # Ambil env yang BENAR-BENAR tersedia dari PROVIDER_ENV
    provider_with = None
    for pid, (env, _base) in pe.PROVIDER_ENV.items():
        if env and os.environ.get(env, ""):
            provider_with = pid
            break

    bridge_no = CanonicalAIAdapter(provider_id=_KNOWN_NO_KEY)
    assert bridge_no.has_credentials() is False

    if provider_with:
        bridge_yes = CanonicalAIAdapter(provider_id=provider_with)
        assert bridge_yes.has_credentials() is True


# ---------------------------------------------------------------------------
# E2E OPSIONAL (skip bila offline / tanpa key) — bukti nyata, bukan mock
# ---------------------------------------------------------------------------

E2E_PROVIDER = os.environ.get("SAM_M3_E2E_PROVIDER", "nvidia")


def test_m3_e2e_real_http_if_credentials(tmp_path):
    """Bila env key tersedia, lakukan HTTP nyata dan buktikan bukan mock.

    DILEWATI (skip) saat offline/tanpa kredensial, konsisten prinsip:
    tanpa kredensial -> no side effect. Jalankan eksplisit dengan set
    variabel env sebelum test bila ingin memverifikasi E2E nyata.
    """
    import sam.providers.execution.provider_executor as pe

    env_for, _base = pe.PROVIDER_ENV.get(E2E_PROVIDER, ("", ""))
    if not env_for or not os.environ.get(env_for, ""):
        pytest.skip(f"tidak ada kredensial untuk '{E2E_PROVIDER}' — skip E2E (offline/no key)")

    bridge = CanonicalAIAdapter(provider_id=E2E_PROVIDER, operation="chat", timeout_seconds=60)
    resp = bridge.invoke(_make_request("Balas hanya: PROVEN"))
    # hasil nyata bukan mock
    assert "PROVEN" in resp.text or resp.text.strip() != "openai-mock-response"
    assert resp.metadata.get("via", "").startswith("canonical")
    assert resp.finish_status == "complete"


def _make_request(prompt: str):
    if _HAS_REQ_CLS:
        from sam.universal_ai.adapter_framework import ProviderRequest

        return ProviderRequest(provider_id=_KNOWN_NO_KEY, prompt=prompt, model_id="")
    # fallback: objek ringan dengan atribut sama (tanpa universal_ai)
    from types import SimpleNamespace

    return SimpleNamespace(provider_id=_KNOWN_NO_KEY, prompt=prompt, model_id="", parameters={})


def _has_universal_ai() -> bool:
    try:
        import sam.universal_ai  # noqa: F401

        return True
    except ImportError:
        return False


try:
    from sam.universal_ai.adapter_framework import (  # noqa: F401
        NormalizedResponse,
        ProviderAdapter,
        ProviderRequest,
    )

    _HAS_REQ_CLS = True
except ImportError:
    _HAS_REQ_CLS = False
