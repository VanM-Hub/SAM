"""Resolution Service — core ADR-002 implementation.

Implements the full ADR-002 resolution policy:
    1. Exact match preferred (identity + version).
    2. Compatible fallback (same identity, same major).
    3. Deterministic tie-break (sort by identity, then version).

Side-effect free and deterministic by design — all lookups are
read-only operations on an internal registry dictionary.

Authority: ADR-002 Decision | REGISTRY_SPEC L143-L160 | R5-001 §2.3
"""

from typing import Dict, List, Optional, Tuple

from sam.runtime.discovery_resolver.models.capability_request import (
    CapabilityRequest,
)
from sam.runtime.discovery_resolver.models.resolution_result import (
    ResolutionResult,
    ResolutionStatus,
)
from sam.runtime.discovery_resolver.models.registry_entry import (
    RegistryEntry,
)
from sam.runtime.discovery_resolver.lifecycle.resolver_lifecycle import (
    ResolverLifecycle,
    ResolverLifecycleState,
)
from sam.runtime.discovery_resolver.validation.request_validator import (
    RequestValidator,
)
from sam.runtime.discovery_resolver.validation.registry_validator import (
    RegistryValidator,
)
from sam.runtime.discovery_resolver.services.health_service import (
    HealthService,
)
from sam.runtime.discovery_resolver.exceptions.resolution_errors import (
    InvalidRequest,
    InvalidRegistryEntry,
    ResolverNotOperational,
)


class DiscoveryResolver:
    """ADR-002 Capability Resolution implementation.

    Resolves CapabilityRequests against a registry of published
    capabilities using the exact-preferred → compatible fallback
    → deterministic tie-break policy.

    Deterministic guarantees:
        - Same registry content + same request → always same result.
        - No hidden randomness, no implicit context.
        - Resolution is read-only — registry never modified during resolve().
    """

    def __init__(self) -> None:
        """Initialize an empty Discovery Resolver."""
        self._registry: Dict[tuple, RegistryEntry] = {}
        self._request_validator = RequestValidator()
        self._entry_validator = RegistryValidator()
        self.lifecycle = ResolverLifecycle()
        self._health = HealthService(lifecycle=self.lifecycle)

    # ── Public: Registry management ──────────────────────────────

    def register_entry(self, entry: RegistryEntry) -> None:
        """Register a capability entry for resolution.

        Args:
            entry: The RegistryEntry to register.

        Raises:
            ResolverNotOperational: If resolver is not in RUNNING state.
            InvalidRegistryEntry: If entry fails validation.
        """
        self._check_operational()
        self._entry_validator.validate(entry)
        self._registry[(entry.identity, entry.version)] = entry

    def list_entries(self) -> List[RegistryEntry]:
        """List all registered entries (for testing/diagnostics).

        Returns:
            List of all RegistryEntry objects in the registry.
        """
        return list(self._registry.values())

    # ── Public: Resolution ───────────────────────────────────────

    def resolve(self, request: CapabilityRequest) -> ResolutionResult:
        """Resolve a Capability Request using ADR-002 policy.

        Algorithm:
            1. Validate request (empty → NOT_FOUND).
            2. Find exact identity+version match.
            3. If exact + non-suspended/removed → prefer non-deprecated → FOUND.
            4. If exact deprecated-only → DEPRECATED_ONLY.
            5. No exact → find compatible (same identity, same major).
            6. Compatible non-suspended/removed → prefer non-deprecated → tie-break → FOUND.
            7. No compatible non-deprecated → DEPRECATED_ONLY.
            8. No identity match at all → NOT_FOUND.

        Args:
            request: The CapabilityRequest to resolve.

        Returns:
            ResolutionResult with status and resolved capability.

        Raises:
            InvalidRequest: If request is malformed.
            ResolverNotOperational: If resolver is not RUNNING.
        """
        self._check_operational()
        self._request_validator.validate(request)

        # Find all entries matching the requested identity
        candidates = [
            e for e in self._registry.values()
            if e.identity == request.identity
        ]

        # No matching identity at all
        if not candidates:
            return ResolutionResult(
                status=ResolutionStatus.NOT_FOUND,
                reason=f"No capability registered with identity "
                        f"'{request.identity}'",
            )

        # Step 1: Try exact match (identity + version)
        exact = [
            c for c in candidates
            if c.version == request.requested_version
        ]

        if exact:
            return self._select_from_exact(exact, request)

        # Step 2: No exact — try compatible (same major version)
        return self._select_from_compatible(candidates, request)

    def resolve_exact(
        self,
        identity: str,
        version: str,
    ) -> Optional[RegistryEntry]:
        """Look up an exact capability match.

        Args:
            identity: The capability identity.
            version: The exact version.

        Returns:
            RegistryEntry if found, None otherwise.
        """
        for entry in self._registry.values():
            if entry.identity == identity and entry.version == version:
                return entry
        return None

    def resolve_compatible(
        self,
        identity: str,
        major_version: int,
    ) -> List[RegistryEntry]:
        """Find all compatible entries for identity with same major version.

        Args:
            identity: The capability identity.
            major_version: The major version to match.

        Returns:
            List of compatible RegistryEntry objects, sorted
            deterministically by version.
        """
        compatible = [
            e for e in self._registry.values()
            if e.identity == identity
            and e.major_version() == major_version
            and not e.is_not_candidate()
        ]
        compatible.sort(key=self._tie_break_key)
        return compatible

    def get_health(self) -> str:
        """Report the health status of the Discovery Resolver.

        Returns:
            'available', 'degraded', or 'unavailable'.
        """
        return self._health.get_health()

    # ── Internal: Selection logic ────────────────────────────────

    def _select_from_exact(
        self,
        exact: List[RegistryEntry],
        request: CapabilityRequest,
    ) -> ResolutionResult:
        """Select from exact-match candidates.

        Args:
            exact: List of exact matches (identity + version).
            request: The original request (for context).

        Returns:
            ResolutionResult.
        """
        # Filter out suspended/removed
        valid = [e for e in exact if not e.is_not_candidate()]

        if not valid:
            return ResolutionResult(
                status=ResolutionStatus.NOT_FOUND,
                reason=f"Exact match '{request.identity}@{request.requested_version}' "
                        f"found but suspended or removed",
            )

        # Prefer non-deprecated
        non_deprecated = [e for e in valid if not e.is_deprecated()]
        if non_deprecated:
            # Tie-break deterministically
            non_deprecated.sort(key=self._tie_break_key)
            winner = non_deprecated[0]
            return ResolutionResult(
                status=ResolutionStatus.FOUND,
                descriptor=winner,
                reason=f"Exact match: {winner.identity}@{winner.version} "
                        f"({winner.lifecycle_state})",
            )

        # Only deprecated
        valid.sort(key=self._tie_break_key)
        winner = valid[0]
        return ResolutionResult(
            status=ResolutionStatus.DEPRECATED_ONLY,
            descriptor=winner,
            reason=f"Exact match deprecated: {winner.identity}@{winner.version}",
        )

    def _select_from_compatible(
        self,
        candidates: List[RegistryEntry],
        request: CapabilityRequest,
    ) -> ResolutionResult:
        """Select from version-compatible candidates.

        Compatible = same identity, same major version.

        Args:
            candidates: All entries matching the identity.
            request: The original request.

        Returns:
            ResolutionResult.
        """
        requested_major = request.major_version()
        if requested_major == 0:
            return ResolutionResult(
                status=ResolutionStatus.VERSION_MISMATCH,
                reason=f"Cannot parse major version from "
                        f"'{request.requested_version}'",
            )

        # Filter: same major + not suspended/removed
        compatible = [
            c for c in candidates
            if c.major_version() == requested_major
            and not c.is_not_candidate()
        ]

        if not compatible:
            return ResolutionResult(
                status=ResolutionStatus.VERSION_MISMATCH,
                reason=f"No version-compatible capability for "
                        f"'{request.identity}' with major={requested_major} "
                        f"(available majors: {self._list_majors(candidates)})",
            )

        # Prefer non-deprecated
        non_deprecated = [c for c in compatible if not c.is_deprecated()]
        if non_deprecated:
            non_deprecated.sort(key=self._tie_break_key)
            winner = non_deprecated[0]
            return ResolutionResult(
                status=ResolutionStatus.FOUND,
                descriptor=winner,
                reason=f"Compatible fallback: {winner.identity}@{winner.version} "
                        f"(requested {request.requested_version}, "
                        f"state={winner.lifecycle_state})",
            )

        # Only deprecated compatible
        compatible.sort(key=self._tie_break_key)
        winner = compatible[0]
        return ResolutionResult(
            status=ResolutionStatus.DEPRECATED_ONLY,
            descriptor=winner,
            reason=f"Only deprecated compatible: {winner.identity}@{winner.version}",
        )

    # ── Internal: Helpers ────────────────────────────────────────

    @staticmethod
    def _tie_break_key(entry: RegistryEntry) -> Tuple[str, str]:
        """Deterministic tie-break: sort by identity, then version.

        Per ADR-002: basis urutan identity → version.

        Args:
            entry: The registry entry.

        Returns:
            Tuple of (identity, version) for sorting.
        """
        return (entry.identity, entry.version)

    @staticmethod
    def _list_majors(candidates: List[RegistryEntry]) -> str:
        """Format available major versions for error messages.

        Args:
            candidates: Registry entries.

        Returns:
            Comma-separated major versions.
        """
        majors = sorted(set(
            c.major_version() for c in candidates
        ))
        return ", ".join(str(m) for m in majors)

    def _check_operational(self) -> None:
        """Raise if resolver is not operational.

        Raises:
            ResolverNotOperational: If lifecycle state is not RUNNING.
        """
        if not self.lifecycle.is_operational():
            raise ResolverNotOperational(
                f"Resolver is not operational "
                f"(state={self.lifecycle.state.name})"
            )
