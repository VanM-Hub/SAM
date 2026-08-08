# Ecosystem Intelligence - WP-23
# IP-3.3-003 (AO-3.3-001 / ED-3.3-001 cycle 3)
#
# Agregasi pengetahuan tingkat ekosistem TANPA authority. Merangkum keragaman
# Citizen (kind, capability, contract, health, maturity, compliance) ke dalam
# gambaran kolektif yang deterministic. Intelligence BUKAN governance:
# ia tidak mengambil keputusan, tidak mengubah apa pun.

from typing import Dict, Optional, Sequence, Tuple

from sam.citizen.ecosystem.models import CertificationResult


class EcosystemSnapshot:
    """Ringkasan agregat ekosistem Citizen (immutable)."""

    def __init__(self, citizen_count: int,
                 kinds: Dict[str, int],
                 capability_count: int,
                 contract_count: int,
                 health_breakdown: Dict[str, int],
                 maturity_breakdown: Optional[Dict[str, int]] = None,
                 compliance_breakdown: Optional[Dict[str, int]] = None,
                 total_capabilities: int = 0,
                 total_contracts: int = 0):
        self._citizen_count = citizen_count
        self._kinds = dict(kinds)
        self._capability_count = capability_count
        self._contract_count = contract_count
        self._health = dict(health_breakdown)
        self._maturity = dict(maturity_breakdown or {})
        self._compliance = dict(compliance_breakdown or {})
        self._total_caps = total_capabilities
        self._total_contracts = total_contracts

    @property
    def citizen_count(self) -> int:
        return self._citizen_count

    @property
    def kinds(self) -> Dict[str, int]:
        return dict(self._kinds)

    @property
    def capability_count(self) -> int:
        return self._capability_count

    @property
    def contract_count(self) -> int:
        return self._contract_count

    @property
    def total_capabilities(self) -> int:
        return self._total_caps

    @property
    def total_contracts(self) -> int:
        return self._total_contracts

    @property
    def health(self) -> Dict[str, int]:
        return dict(self._health)

    @property
    def maturity(self) -> Dict[str, int]:
        return dict(self._maturity)

    @property
    def compliance(self) -> Dict[str, int]:
        return dict(self._compliance)

    def as_dict(self) -> Dict[str, object]:
        return {
            "citizen_count": self._citizen_count,
            "kinds": dict(self._kinds),
            "capability_kind_count": self._capability_count,
            "contract_kind_count": self._contract_count,
            "total_capabilities": self._total_caps,
            "total_contracts": self._total_contracts,
            "health": dict(self._health),
            "maturity": dict(self._maturity),
            "compliance": dict(self._compliance),
        }


class EcosystemIntelligenceEngine:
    """Menghasilkan snapshot intelligence ekosistem (deterministik, read-only)."""

    def __init__(self, registry=None):
        self._registry = registry

    def snapshot(self, identity_ids: Sequence[str], *,
                 kinds=None, healths=None, maturity=None, compliance=None,
                 capabilities=None, contracts=None) -> EcosystemSnapshot:
        """Agregasi deterministik atas sekumpulan Citizen.

        Argumen opsional berupa mapping identity_id -> nilai; fallback
        membaca dari registry bila tersedia.
        """
        kinds = kinds or {}
        healths = healths or {}
        maturity = maturity or {}
        compliance = compliance or {}
        capabilities = capabilities or {}
        contracts = contracts or {}

        kind_count: Dict[str, int] = {}
        health_count: Dict[str, int] = {}
        maturity_count: Dict[str, int] = {}
        compliance_count: Dict[str, int] = {}
        total_caps = 0
        total_contracts = 0
        cap_kinds = set()
        contract_kinds = set()

        for cid in identity_ids:
            k = kinds.get(cid, "unknown")
            if self._registry is not None and cid not in kinds:
                e = self._registry.get(cid)
                if e is not None:
                    ed = e.as_dict()
                    k = ed.get("kind", "unknown")
            kind_count[k] = kind_count.get(k, 0) + 1

            h = healths.get(cid, "unknown")
            if h:
                health_count[h] = health_count.get(h, 0) + 1

            m = maturity.get(cid, "unassessed")
            if m:
                maturity_count[m] = maturity_count.get(m, 0) + 1

            cp = compliance.get(cid, "noncompliant")
            if cp:
                compliance_count[cp] = compliance_count.get(cp, 0) + 1

            caps = tuple(capabilities.get(cid, ()))
            cts = tuple(contracts.get(cid, ()))
            total_caps += len(caps)
            total_contracts += len(cts)
            cap_kinds.update(caps)
            contract_kinds.update(cts)

        return EcosystemSnapshot(
            citizen_count=len(identity_ids),
            kinds=kind_count,
            capability_count=len(cap_kinds),
            contract_count=len(contract_kinds),
            health_breakdown=health_count,
            maturity_breakdown=maturity_count,
            compliance_breakdown=compliance_count,
            total_capabilities=total_caps,
            total_contracts=total_contracts,
        )

    def most_common_capability(self, identity_ids: Sequence[str],
                               capabilities=None) -> Optional[str]:
        """Capability paling umum di ekosistem (deterministik tie-break)."""
        capabilities = capabilities or {}
        freq: Dict[str, int] = {}
        for cid in identity_ids:
            for cap in tuple(capabilities.get(cid, ())):
                freq[cap] = freq.get(cap, 0) + 1
        if not freq:
            return None
        # tie-break alfabetis
        return max(sorted(freq), key=lambda cap: (freq[cap], cap))
