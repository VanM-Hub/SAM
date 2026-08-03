"""Resolution determinism validator.

Verifies that IDENTICAL requests produce IDENTICAL results.

Authority: REGISTRY_SPEC L147/L149 | ADR-002
"""

from typing import Any, List

from sam.runtime.discovery_resolver.exceptions.resolution_errors import (
    ResolutionNotDeterministic,
)


class ResolutionValidator:
    """Validates resolution determinism guarantees."""

    @staticmethod
    def validate_determinism(
        service: Any,
        request: Any,
        iterations: int = 10,
    ) -> bool:
        """Verify N identical calls produce identical results.

        Args:
            service: The resolution service to test.
            request: The CapabilityRequest to resolve.
            iterations: Number of identical calls to make.

        Returns:
            True if all results match.

        Raises:
            ResolutionNotDeterministic: If any result differs.
        """
        results: List[Any] = []
        for _ in range(iterations):
            results.append(service.resolve(request))

        first = results[0]
        for i, r in enumerate(results[1:], start=2):
            if r.status != first.status:
                raise ResolutionNotDeterministic(
                    f"Determinism violation: iteration {i} status "
                    f"'{r.status.name}' != first '{first.status.name}'"
                )
            if (r.descriptor is not None
                    and first.descriptor is not None
                    and r.descriptor.identity != first.descriptor.identity):
                raise ResolutionNotDeterministic(
                    f"Determinism violation: iteration {i} identity "
                    f"'{r.descriptor.identity}' != '{first.descriptor.identity}'"
                )

        return True

    @staticmethod
    def validate_side_effect_free(
        service: Any,
        initial_count: int,
    ) -> bool:
        """Verify resolution does not modify registry.

        Args:
            service: The resolution service to test.
            initial_count: Registry entry count before resolution.

        Returns:
            True if count unchanged.

        Raises:
            ResolutionNotDeterministic: If registry was modified.
        """
        current_count = len(service.list_entries())
        if current_count != initial_count:
            raise ResolutionNotDeterministic(
                f"Side-effect violation: registry modified "
                f"({initial_count} → {current_count} entries)"
            )
        return True
