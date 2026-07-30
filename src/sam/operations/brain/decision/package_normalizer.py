"""
Decision Runtime Package Normalizer.

Normalizes IncomingDecisionPackage for consistent processing.
Deterministic. Rule-based.
"""

from typing import Dict, Any

from .package_protocol import IncomingDecisionPackage, PackageHeader, PackageBody


class PackageNormalizer:
    """Normalizes package data for consistent processing."""

    REQUIRED_VERSION = "1.0"

    def normalize(self, package: IncomingDecisionPackage) -> IncomingDecisionPackage:
        """Normalize a package."""
        sections = package.body.sections if package.body else {}

        # Normalize version
        version = self.REQUIRED_VERSION
        if package.header:
            raw_version = package.header.version
            if raw_version.startswith("1."):
                version = "1.0"

        # Normalize timestamps
        normalized_sections = {}
        for k, v in sections.items():
            if isinstance(v, dict):
                normalized_sections[k] = self._normalize_dict(v)
            else:
                normalized_sections[k] = v

        normalized_header = PackageHeader(
            source_package_id=package.header.source_package_id if package.header else "",
            source_component="DecisionRuntime",
            received_at=package.header.received_at if package.header else 0.0,
            version=version,
            total_sections=package.header.total_sections if package.header else 0,
            has_input=package.header.has_input if package.header else False,
            has_justification=package.header.has_justification if package.header else False,
        )

        normalized_body = PackageBody(
            sections=normalized_sections,
            decision_input=package.body.decision_input if package.body else None,
            justification=package.body.justification if package.body else None,
            metadata=package.body.metadata if package.body else None,
        )

        return IncomingDecisionPackage(
            package_id=package.package_id,
            header=normalized_header,
            body=normalized_body,
            validation_errors=list(package.validation_errors),
            ready=package.ready,
        )

    def _normalize_dict(self, d: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize a nested dict."""
        return {k: v for k, v in d.items() if v is not None}
