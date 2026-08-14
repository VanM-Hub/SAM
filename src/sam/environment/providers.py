"""Environment-adaptive: registry capability provider (instance, bukan katalog).

Ward/fixture spesifik (Word, PDF, OpenClaw, GitHub, Provider, ...) adalah
INSTANCE dari capability provider yang DIDAFTARKAN ke mesin generic, bukan
fondasi yang SAM andalkan. Mesin generic TIDAK membutuhkan provider apapun
untuk discovery/diagnosis; provider hanya menambah observasi/remediasi bila
didapatkan di registry.

Alur konsep:
  DISCOVERY (generik, dari process/port/file/env) -> IDENTIFICATION
  -> OBSERVATION (bila provider terdaftar, probe observasi di-eksekusi)
  -> INVESTIGATION -> DIAGNOSIS -> AUTHORITY -> EXECUTION -> VERIFICATION

CapabilityProvider hanya MENGAMATI dan MENYIAPKAN remediasi; ia TIDAK
mengeksekusi apa pun langsung. Eksekusi tetap lewat canonical (ApprovalGate).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from sam.environment.confidence import Evidence


# observasi dari satu provider: kumpulan evidence + status sumber
@dataclass
class ProviderObservation:
    """Hasil observasi satu provider (fixture instance)."""

    provider: str
    ok: bool
    evidence: List[Evidence] = field(default_factory=list)
    error: str = ""

    def as_dict(self) -> Dict[str, Any]:
        return {
            "provider": self.provider,
            "ok": self.ok,
            "evidence": [e.as_dict() for e in self.evidence],
            "error": self.error,
        }


@dataclass
class CapabilityProvider:
    """Instance capability (Word/PDF/OpenClaw/GitHub/Provider/...).

    Tiga fungsi (semua optional, didaftarkan bila ada):
      - observe_fn: callable() -> List[Evidence]        (read-only)
      - diagnose_fn: callable(entity) -> List[Evidence] (read-only, per-entitas)
      - remediate_fn: callable() -> capability_available(bool)  (TIDAK eksekusi)
    Provider TIDAK punya authority sendiri; segala eksekusi lewat canonical.
    """

    name: str
    kind: str                       # entity kind yang di-observe (word/pdf/...)
    observe_fn: Optional[Callable[[], List[Evidence]]] = None
    diagnose_fn: Optional[Callable[[Any], List[Evidence]]] = None
    remediate_fn: Optional[Callable[[], bool]] = None
    description: str = ""

    def observe(self) -> ProviderObservation:
        """Jalankan observasi (read-only). Menangkap kegagalan -> jujur."""
        if not self.observe_fn:
            return ProviderObservation(self.name, ok=True)
        try:
            return ProviderObservation(
                self.name, ok=True,
                evidence=list(self.observe_fn() or []))
        except Exception as ex:  # noqa: BLE001 - sumber gagal, jangan jatuh
            return ProviderObservation(
                self.name, ok=False,
                error=f"observation failed: {ex}")

    def diagnose(self, entity: Any) -> List[Evidence]:
        if not self.diagnose_fn:
            return []
        try:
            return list(self.diagnose_fn(entity) or [])
        except Exception:  # noqa: BLE001 - defensif
            return []

    def remediation_available(self) -> bool:
        """Apakah provider siap menyediakan remediasi (TIDAK mengeksekusi)."""
        if not self.remediate_fn:
            return False
        try:
            return bool(self.remediate_fn())
        except Exception:  # noqa: BLE001 - defensif
            return False


@dataclass
class ProviderRegistry:
    """Registry provider terdaftar (instance). Mesin generic TIDAK bergantung
    pada daftar ini; digunakan hanya bila provider didaftarkan."""

    _providers: Dict[str, CapabilityProvider] = field(default_factory=dict)

    def register(self, provider: CapabilityProvider) -> None:
        self._providers[provider.name] = provider

    def unregister(self, name: str) -> None:
        self._providers.pop(name, None)

    def get(self, name: str) -> Optional[CapabilityProvider]:
        return self._providers.get(name)

    def names(self) -> List[str]:
        return sorted(self._providers)

    def all(self) -> List[CapabilityProvider]:
        return list(self._providers.values())

    def __len__(self) -> int:
        return len(self._providers)


def provider_from(
    *,
    name: str,
    kind: str,
    observe_fn: Optional[Callable[[], List[Evidence]]] = None,
    diagnose_fn: Optional[Callable[[Any], List[Evidence]]] = None,
    remediate_fn: Optional[Callable[[], bool]] = None,
    description: str = "",
) -> CapabilityProvider:
    """Factory meringkas pembuatan provider (instance)."""
    return CapabilityProvider(
        name=name, kind=kind, observe_fn=observe_fn,
        diagnose_fn=diagnose_fn, remediate_fn=remediate_fn,
        description=description,
    )
