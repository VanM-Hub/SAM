"""CapabilityRequest validator.

Validates request completeness and structure.

Authority: REGISTRY_SPEC Discovery Protocol
"""

import re

from sam.runtime.discovery_resolver.models.capability_request import (
    CapabilityRequest,
)
from sam.runtime.discovery_resolver.exceptions.resolution_errors import (
    InvalidRequest,
)


class RequestValidator:
    """Validates CapabilityRequest structure and content."""

    # Semver pattern: Major.Minor.Patch
    _SEMVER = re.compile(r"^\d+\.\d+\.\d+$")

    def validate(self, request: CapabilityRequest) -> bool:
        """Validate a capability request.

        Checks:
            - Non-empty identity
            - Non-empty version
            - Non-empty requester
            - Version matches Major.Minor.Patch format

        Args:
            request: The CapabilityRequest to validate.

        Returns:
            True if valid.

        Raises:
            InvalidRequest: If any validation check fails.
        """
        if not request.identity.strip():
            raise InvalidRequest(
                f"Capability identity is required (got: '{request.identity}')"
            )
        if not request.requested_version.strip():
            raise InvalidRequest(
                "Requested version is required"
            )
        if not request.requester.strip():
            raise InvalidRequest(
                "Requester identity is required"
            )
        if not self._SEMVER.match(request.requested_version):
            raise InvalidRequest(
                f"Version '{request.requested_version}' is not in "
                f"Major.Minor.Patch format"
            )
        return True
