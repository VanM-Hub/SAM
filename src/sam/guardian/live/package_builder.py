"""
Guardian Package Builder.

Builds DecisionPackage from runtime state.
DTO only. Deterministic. No domain knowledge.
"""

import uuid
from datetime import datetime
from typing import Dict, Any, Optional

from .decision_package import DecisionPackage, PackageMetadata, PackageVersion
from .decision_input import DecisionInput
from .justification import DecisionJustification


class PackageBuilder:
    """Builds DecisionPackage from runtime state."""

    def build(
        self,
        decision_input: Optional[DecisionInput] = None,
        justification: Optional[DecisionJustification] = None,
        sections: Optional[Dict[str, Any]] = None,
        runtime_id: str = "",
    ) -> DecisionPackage:
        """Build a complete DecisionPackage."""
        package_id = str(uuid.uuid4())
        all_sections = dict(sections or {})

        if decision_input:
            all_sections["decision_input"] = decision_input.to_dict()
        if justification:
            all_sections["justification"] = justification.to_dict()

        metadata = PackageMetadata(
            package_id=package_id,
            version=str(PackageVersion.current()),
            created_at=datetime.now().timestamp(),
            runtime_id=runtime_id,
            description=f"DecisionPackage v{str(PackageVersion.current())}",
        )

        return DecisionPackage(
            package_id=package_id,
            metadata=metadata,
            sections=all_sections,
            total_sections=len(all_sections),
            decision_input_id=decision_input.input_id if decision_input else "",
            justification_id=justification.justification_id if justification else "",
        )
