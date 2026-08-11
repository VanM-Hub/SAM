"""Canonical Tool Contract Adapter - M2 (Canonical Execution Consolidation).

Menyerap kontrak Tool bernilai dari `universal_tool` ke canonical execution
boundary (`RealExecutionHarness`). Non-destruktif: file `universal_tool/*`
tetap ada sebagai LEGACY/MIGRATION SOURCE, tapi contract bernilai kini bisa
dinyatakan & diverifikasi di jalur canonical.

Prinsip arsitektur (keputusan Van 2026-08-12):
- Real Execution Path = CANONICAL.
- `universal_*` = LEGACY / MIGRATION SOURCE (bukan execution authority).
- Satu capability banyak adapter, SATU canonical boundary.
- Tidak ada executor paralel.

Modul ini BUKAN executor. Ia hanya memetakan/ memverifikasi contract sehingga
`RealExecutionHarness` (boundary canonical) dapat memakainya.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

# CapabilityKind yang dimengerti jalur canonical. Ini normalisasi dari
# `universal_tool.tool_descriptor.ToolCapabilityKind` (READ/WRITE/EXECUTE/
# QUERY/NOTIFY/TRANSFORM) ke bentuk seragam, supaya resolver canonical
# tidak bergantung pada import internal universal_tool.
TOOL_KIND_EXECUTE = "execute"
TOOL_KIND_READ = "read"
TOOL_KIND_WRITE = "write"
TOOL_KIND_QUERY = "query"
TOOL_KIND_NOTIFY = "notify"
TOOL_KIND_TRANSFORM = "transform"

ALL_TOOL_KINDS = (
    TOOL_KIND_READ,
    TOOL_KIND_WRITE,
    TOOL_KIND_EXECUTE,
    TOOL_KIND_QUERY,
    TOOL_KIND_NOTIFY,
    TOOL_KIND_TRANSFORM,
)


@dataclass(frozen=True)
class CanonicalToolContract:
    """Kontrak tool dalam bentuk canonical yang dimengerti RealExecutionHarness.

    Memetakan kontrak `universal_tool.ToolContract` (tool_id, capabilities,
    supports_capability, requires_approval, requires_governance) ke satu bentuk
    seragam di jalur execution canonical.
    """

    tool_id: str
    contract_id: str
    supported_kinds: Tuple[str, ...]
    entry_points: Tuple[str, ...] = ()
    requires_approval: bool = True
    requires_governance: bool = True

    @property
    def governed(self) -> bool:
        return self.requires_governance or self.requires_approval

    def allows(self, kind: str) -> bool:
        return kind in self.supported_kinds

    def to_contract_dict(self) -> Dict[str, Any]:
        """Bentuk contract yang disimpan `RealExecutionHarness._contracts[cap_id]`.

        Format ini harus 'truthy' untuk lulus gate `contract` di
        `RealExecutionHarness._evaluate_gates` (lihat gate #3: contract valid).
        """
        return {
            "tool_id": self.tool_id,
            "contract_id": self.contract_id,
            "supported_kinds": list(self.supported_kinds),
            "entry_points": list(self.entry_points),
            "requires_approval": self.requires_approval,
            "requires_governance": self.requires_governance,
            "governed": self.governed,
        }

    def as_dict(self) -> Dict[str, Any]:
        return self.to_contract_dict()


def _normalize_kind(kind: Any) -> Optional[str]:
    """Normalisasi enum/string capability ke string canonical.

    Menerima nilai dari `universal_tool.tool_descriptor.ToolCapabilityKind`
    (Enum) maupun string polos ("execute", dst.).
    """
    if kind is None:
        return None
    value = getattr(kind, "value", kind)
    if isinstance(value, str) and value in ALL_TOOL_KINDS:
        return value
    return None if isinstance(value, str) else None


def from_universal_tool_contract(contract: Any) -> Optional[CanonicalToolContract]:
    """Serap kontrak `universal_tool.ToolContract` / dict menjadi canonical.

    `contract` boleh berupa objek yang punya atribut tool_id, contract_id,
    supports_capability, entry_points, requires_approval, requires_governance
    (kontrak dataclass universal_tool) ATAU dict dengan kunci sama.

    Mengembalikan None jika bentuk tidak dikenali (bukan contract tool valid).
    Ini jembatan MIGRATION: universal_tool -> canonical boundary.
    """
    if contract is None:
        return None

    def _get(obj: Any, key: str, default: Any = None) -> Any:
        if isinstance(obj, dict):
            return obj.get(key, default)
        return getattr(obj, key, default)

    tool_id = _get(contract, "tool_id")
    contract_id = _get(contract, "contract_id")
    if not tool_id or not contract_id:
        return None

    raw_kinds = _get(contract, "supports_capability", ())
    kinds: list = []
    for k in raw_kinds or ():
        norm = _normalize_kind(k)
        if norm:
            kinds.append(norm)
    # fallback: bila supports_capability kosong, turunkan dari capabilities
    if not kinds:
        for cap in (_get(contract, "capabilities", ()) or ()):
            if not isinstance(cap, dict):
                cap = getattr(cap, "as_dict", lambda: {"kind": getattr(cap, "kind", None)})()
            if isinstance(cap, dict):
                norm = _normalize_kind(cap.get("kind"))
                if norm and norm not in kinds:
                    kinds.append(norm)

    return CanonicalToolContract(
        tool_id=str(tool_id),
        contract_id=str(contract_id),
        supported_kinds=tuple(kinds),
        entry_points=tuple(_get(contract, "entry_points", ()) or ()),
        requires_approval=bool(_get(contract, "requires_approval", True)),
        requires_governance=bool(_get(contract, "requires_governance", True)),
    )


def build_tool_contract(
    tool_id: str,
    contract_id: str,
    supported_kinds: Tuple[str, ...],
    entry_points: Tuple[str, ...] = (),
    requires_approval: bool = True,
    requires_governance: bool = True,
) -> CanonicalToolContract:
    """Fabrikasi kontrak tool canonical dari bahan (digunakan harness canonical)."""
    # dedup + validasi kind
    kinds: list = []
    for k in supported_kinds:
        norm = _normalize_kind(k)
        if norm and norm not in kinds:
            kinds.append(norm)
    return CanonicalToolContract(
        tool_id=tool_id,
        contract_id=contract_id,
        supported_kinds=tuple(kinds),
        entry_points=tuple(entry_points),
        requires_approval=requires_approval,
        requires_governance=requires_governance,
    )


def contract_to_registry_dict(contract: CanonicalToolContract) -> Dict[str, Any]:
    """Registry dict yang dikaitkan ke capability di RealExecutionHarness.

    Registry berisi deskripsi contract; sama dengan `register_capability()`.
    """
    return {
        "contract_id": contract.contract_id,
        "tool_id": contract.tool_id,
        "supported_kinds": contract.supported_kinds,
        "entry_points": contract.entry_points,
        "governed": contract.governed,
    }
