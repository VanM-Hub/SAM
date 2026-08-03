"""NegotiatorService — version negotiation between two parties.

Per CONTRACT_SPEC 'Version Negotiation':
    1. Both Citizens SHALL agree on a single version
    2. A compatible version SHALL be chosen
    3. Preference to non-deprecated versions
    4. No mutually compatible version → defined failure

Deterministic, repeatable, side-effect free.
"""

from typing import List, Optional

from sam.runtime.contracts import ContractIdentity
from sam.runtime.contract_enforcer.models.negotiation_result import (
    NegotiationResult,
    NegotiationStatus,
)


class NegotiatorService:
    """Version negotiation service.

    Implements CONTRACT_SPEC negotiation protocol deterministically.
    """

    def negotiate(
        self,
        offered: ContractIdentity,
        supported_versions: List[ContractIdentity],
        deprecated_ids: Optional[set] = None,
    ) -> NegotiationResult:
        """Negotiate a compatible Contract version.

        Algorithm:
        1. Find intersection of versions (same contract_id, mutually supported)
        2. Separate deprecated from non-deprecated
        3. If non-deprecated intersection exists -> pick highest version
        4. If only deprecated exists -> DEPRECATED_ONLY
        5. If no intersection -> NO_INTERSECTION

        The offered version counts as supported only if it also appears in
        supported_versions (both parties must agree).
        """
        if deprecated_ids is None:
            deprecated_ids = set()

        # Find versions of the offered contract_id that are in supported_versions
        candidates: List[ContractIdentity] = []
        for sv in supported_versions:
            if sv.contract_id == offered.contract_id:
                candidates.append(sv)

        # Also include the offered version if it appears in supported
        offered_in_supported = any(
            sv.contract_id == offered.contract_id and sv.version == offered.version
            for sv in supported_versions
        )
        if offered_in_supported:
            # Ensure offered version is in the list (may already be via supported)
            if not any(
                c.contract_id == offered.contract_id and c.version == offered.version
                for c in candidates
            ):
                candidates.append(offered)

        if not candidates:
            return NegotiationResult.no_intersection()

        # Separate by deprecated status
        non_deprecated: List[tuple] = []
        deprecated: List[tuple] = []
        seen: set = set()

        for c in candidates:
            key = (c.contract_id, c.version)
            if key in seen:
                continue
            seen.add(key)

            is_dep = key in deprecated_ids or c.version in {
                d[1] for d in deprecated_ids if d[0] == c.contract_id
            }

            if is_dep:
                deprecated.append((c, c.version))
            else:
                non_deprecated.append((c, c.version))

        # Phase 1: non-deprecated candidates
        if non_deprecated:
            # Sort by version string (deterministic tie-break)
            non_deprecated.sort(key=lambda x: self._version_tuple(x[1]))
            best = non_deprecated[-1]  # highest version
            return NegotiationResult.resolved(
                contract_id=offered.contract_id,
                version=best[1],
                reason=f"Agreed on non-deprecated version {best[1]}",
            )

        # Phase 2: deprecated-only
        if deprecated:
            deprecated.sort(key=lambda x: self._version_tuple(x[1]))
            # Pick highest deprecated version
            best = deprecated[-1]
            return NegotiationResult.deprecated_only(
                contract_id=offered.contract_id,
                version=best[1],
            )

        # Phase 3: no version found
        return NegotiationResult.no_compatible(
            f"No compatible version of '{offered.contract_id}' found"
        )

    @staticmethod
    def _version_tuple(version: str) -> tuple:
        """Convert semver string to a sortable tuple."""
        try:
            return tuple(int(x) for x in version.split("."))
        except (ValueError, IndexError):
            return (0, 0, 0)
