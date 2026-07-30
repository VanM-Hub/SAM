"""
Decision Runtime Package Consumer.

Consumes Guardian DecisionPackage and produces IncomingDecisionPackage.
DTO only. No execution, approvals, or missions.
"""

import uuid
from datetime import datetime
from typing import Dict, Any, Optional

from .package_protocol import IncomingDecisionPackage, PackageHeader, PackageBody


class PackageConsumer:
    """Consumes Guardian DecisionPackage for Decision Runtime."""

    def consume(self, source_package: Dict[str, Any]) -> IncomingDecisionPackage:
        """Convert a Guardian DecisionPackage dict to an IncomingDecisionPackage."""
        meta = source_package.get("metadata", {}) or {}
        sections = source_package.get("sections", {}) or {}

        header = PackageHeader(
            source_package_id=source_package.get("package_id", ""),
            source_component=meta.get("source_component", "GuardianLiveRuntime"),
            received_at=datetime.now().timestamp(),
            version=meta.get("version", "1.0"),
            total_sections=source_package.get("total_sections", 0),
            has_input=bool(source_package.get("decision_input_id")),
            has_justification=bool(source_package.get("justification_id")),
        )

        body = PackageBody(
            sections=sections,
            decision_input=sections.get("decision_input"),
            justification=sections.get("justification"),
            metadata=meta,
        )

        return IncomingDecisionPackage(
            package_id=str(uuid.uuid4()),
            header=header,
            body=body,
            validation_errors=[],
            ready=True,
        )
