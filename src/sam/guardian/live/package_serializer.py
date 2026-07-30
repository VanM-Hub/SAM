"""
Guardian Package Serializer.

Read-only serialization for DecisionPackage.
No file IO. DTO only.
"""

from typing import Dict, Any
import json

from .decision_package import DecisionPackage, PackageMetadata, PackageVersion


class PackageSerializer:
    """Read-only serializer for DecisionPackage."""

    def to_dict(self, package: DecisionPackage) -> Dict[str, Any]:
        """Convert package to dict."""
        return package.to_dict()

    def to_json(self, package: DecisionPackage) -> str:
        """Convert package to JSON string."""
        return json.dumps(package.to_dict(), indent=2, default=str)

    def summary(self, package: DecisionPackage) -> Dict[str, Any]:
        """Get a lightweight summary dict."""
        return {
            "package_id": package.package_id,
            "version": package.metadata.version if package.metadata else "unknown",
            "created_at": package.metadata.created_at if package.metadata else 0.0,
            "total_sections": package.total_sections,
            "section_names": list(package.sections.keys()),
            "has_decision_input": bool(package.decision_input_id),
            "has_justification": bool(package.justification_id),
        }

    def metadata(self, package: DecisionPackage) -> Dict[str, Any]:
        """Get just the metadata dict."""
        return package.metadata.to_dict() if package.metadata else {}
