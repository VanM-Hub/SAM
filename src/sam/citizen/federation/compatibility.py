# Federation Compatibility - WP-15
# IP-3.4-002 (AO-3.4-001 / ED-3.4-001, paket kedua)
#
# Analisis kompatibilitas antar Federation Member.
#
# Mencakup:
#   contract version
#   capability version
#   certification level
#   protocol compatibility
#
# Guardrail IP-3.4-002:
#   Compatibility != Approval  - approval tetap lokal
#   Interoperability != Execution - kompatibilitas TIDAK memicu aksi
#   Deterministic
#
# Hasil = penilaian kompatibilitas (read-only). Tidak memberi kewenangan
# untuk bertindak; hanya menyatakan seberapa cocok dua member.

from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

_COMPAT_LEVELS = ("incompatible", "partial", "compatible")


def _norm(level: Optional[str]) -> str:
    if not level:
        return "partial"
    lvl = level.strip().lower()
    if lvl not in _COMPAT_LEVELS:
        return "partial"
    return lvl


@dataclass(frozen=True)
class FederationCompatibilityItem:
    """Kompatibilitas satu dimensi (contract/capability/certification/protocol)."""

    dimension: str
    level: str = "partial"
    detail: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "level", _norm(self.level))

    def as_dict(self) -> Dict[str, Any]:
        return {
            "dimension": self.dimension,
            "level": self.level,
            "detail": self.detail,
        }


@dataclass(frozen=True)
class FederationCompatibility:
    """Keseluruhan kompatibilitas dua member Federation."""

    source_id: str
    target_id: str
    items: Tuple[FederationCompatibilityItem, ...] = ()

    def __post_init__(self) -> None:
        items = tuple(sorted(self.items, key=lambda i: i.dimension))
        object.__setattr__(self, "items", items)

    @property
    def overall(self) -> str:
        if not self.items:
            return "incompatible"
        levels = [i.level for i in self.items]
        if "incompatible" in levels:
            return "incompatible"
        if "partial" in levels:
            return "partial"
        return "compatible"

    @property
    def is_compatible(self) -> bool:
        return self.overall == "compatible"

    def dimension_level(self, dimension: str) -> Optional[str]:
        for i in self.items:
            if i.dimension == dimension:
                return i.level
        return None

    def as_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "overall": self.overall,
            "items": [i.as_dict() for i in self.items],
        }


class FederationCompatibilityAnalyzer:
    """Menganalisis kompatibilitas dua member (deterministik)."""

    def analyze(
        self,
        source_id: str,
        target_id: str,
        source_contracts: Tuple[str, ...],
        target_contracts: Tuple[str, ...],
        source_capabilities: Tuple[str, ...],
        target_capabilities: Tuple[str, ...],
        source_cert: Optional[str] = None,
        target_cert: Optional[str] = None,
        source_protocol: Optional[str] = None,
        target_protocol: Optional[str] = None,
    ) -> FederationCompatibility:
        # contract compatibility
        shared = set(source_contracts) & set(target_contracts)
        if shared:
            contract_item = FederationCompatibilityItem(
                "contract", "compatible",
                ";".join(sorted(shared)))
        else:
            contract_item = FederationCompatibilityItem(
                "contract", "incompatible", "no-shared-contract")

        # capability compatibility
        shared_caps = set(source_capabilities) & set(target_capabilities)
        if shared_caps:
            cap_item = FederationCompatibilityItem(
                "capability", "compatible",
                ";".join(sorted(shared_caps)))
        else:
            cap_item = FederationCompatibilityItem(
                "capability", "incompatible", "no-shared-capability")

        # certification level
        if source_cert and target_cert and source_cert == target_cert:
            cert_item = FederationCompatibilityItem(
                "certification", "compatible",
                "level={}".format(source_cert))
        elif source_cert and target_cert:
            cert_item = FederationCompatibilityItem(
                "certification", "partial",
                "{} vs {}".format(source_cert, target_cert))
        else:
            cert_item = FederationCompatibilityItem(
                "certification", "partial", "certification-unknown")

        # protocol
        if source_protocol and target_protocol \
                and source_protocol == target_protocol:
            proto_item = FederationCompatibilityItem(
                "protocol", "compatible",
                "protocol={}".format(source_protocol))
        elif source_protocol and target_protocol:
            proto_item = FederationCompatibilityItem(
                "protocol", "incompatible",
                "{} vs {}".format(source_protocol, target_protocol))
        else:
            proto_item = FederationCompatibilityItem(
                "protocol", "partial", "protocol-unknown")

        return FederationCompatibility(
            source_id=source_id,
            target_id=target_id,
            items=(contract_item, cap_item, cert_item, proto_item),
        )
