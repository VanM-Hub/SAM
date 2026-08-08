# Contract Resolution - WP-14
# IP-3.3-002 (AO-3.3-001 / ED-3.3-001 2nd cycle)
#
# Resolusi contract-driven interaction antar Citizen. "Resolusi" = menentukan
# contract & capability mana yang memenuhi kebutuhan pemanggil - TIDAK
# menjalankan (eksekusi) apapun.
#
# Guardrail: Contract Resolution != Execution.

from dataclasses import dataclass
from typing import Dict, Optional, Tuple, Sequence


@dataclass(frozen=True)
class ResolutionRequirement:
    """Kebutuhan kontrak yang harus dipenuhi (immutable)."""

    contract: str
    capability: str = ""
    input_schema: str = ""
    output_schema: str = ""

    def as_dict(self) -> Dict[str, object]:
        return {
            "contract": self.contract,
            "capability": self.capability,
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
        }


@dataclass(frozen=True)
class ContractResolution:
    """Hasil resolusi contract-driven (immutable, bukan eksekusi)."""

    requirement: ResolutionRequirement
    resolved: bool
    citizen_identity_id: str = ""
    capability: str = ""
    schema_match: bool = False
    basis: Tuple[str, ...] = ()

    def as_dict(self) -> Dict[str, object]:
        return {
            "requirement": self.requirement.as_dict(),
            "resolved": self.resolved,
            "citizen_identity_id": self.citizen_identity_id,
            "capability": self.capability,
            "schema_match": self.schema_match,
            "basis": list(self.basis),
        }


class ContractResolutionEngine:
    """Meresolusi kebutuhan kontrak ke citizen yang memenuhi (registry-based).

    Murni pencarian & pencocokan kontrak. TIDAK mengeksekusi capability;
    hanya "mana citizen/capability yang bisa memenuhi kebutuhan ini".
    """

    def __init__(self, registry, descriptors: Optional[Tuple] = None):
        self._registry = registry
        self._descriptors = descriptors or ()

    def resolve(self, requirement: ResolutionRequirement,
                *, healthy_only: bool = False,
                healths: Optional[Dict[str, str]] = None) -> Tuple[ContractResolution, ...]:
        """Resolusi kebutuhan ke semua citizen yang cocok (deterministik)."""
        healths = healths or {}
        results = []
        for entry in self._registry.all():
            cid = entry.identity_id
            if healthy_only and healths.get(cid, "unknown") != "healthy":
                continue
            caps = tuple(self._capabilities_of(cid, requirement.capability))
            if not caps:
                continue
            # pencocokan skema: bila requirement punya input_schema, cocokkan
            schema_match = True
            if requirement.input_schema:
                # skema target dari descriptor (fallback: cocok bila "any")
                tgt = self._schema_for(cid, requirement.contract, "output")
                schema_match = (tgt in ("", "any") or
                                tgt == requirement.input_schema)
            results.append(ContractResolution(
                requirement=requirement,
                resolved=schema_match,
                citizen_identity_id=cid,
                capability=caps[0],
                schema_match=schema_match,
                basis=("contract resolution is lookup, not execution",
                       "registry-based"),
            ))
        # urutkan deterministik
        results.sort(key=lambda r: r.citizen_identity_id)
        return tuple(results)

    def _capabilities_of(self, identity_id: str,
                         wanted: str) -> Tuple[str, ...]:
        if not wanted:
            return ("capability",)
        for d in self._descriptors:
            if getattr(d, "identity_id", None) == identity_id:
                caps = tuple(getattr(d, "capabilities", ()))
                return tuple(c for c in caps if c == wanted)
        return ()

    def _schema_for(self, identity_id: str, contract: str,
                    kind: str) -> str:
        for d in self._descriptors:
            if getattr(d, "identity_id", None) == identity_id:
                return "any"
        return ""
