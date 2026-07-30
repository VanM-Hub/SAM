"""Package Export — ekspor paket."""
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from sam.activation.activation_package import ActivationPackage


@dataclass(frozen=True)
class PackageExport:
    package_id: str = ""
    format: str = "json"
    content: Dict[str, Any] = field(default_factory=dict)
    exported_at: float = 0.0


class PackageExporter:
    """Mengekspor ActivationPackage ke format dictionary."""

    def export(self, package: ActivationPackage, fmt: str = "json",
               timestamp: float = 0.0) -> PackageExport:
        content = {
            "package_id": package.package_id,
            "plan_ref": package.plan_ref,
            "strategy_ref": package.strategy_ref,
            "sequence_ref": package.sequence_ref,
            "candidates": list(package.candidate_refs),
            "total_candidates": package.total_candidates,
            "estimated_duration": package.estimated_duration,
            "confidence": package.confidence,
            "status": package.status,
        }
        return PackageExport(
            package_id=package.package_id,
            format=fmt,
            content=content,
            exported_at=timestamp,
        )

    def export_summary(self, packages: List[ActivationPackage]) -> Dict[str, Any]:
        return {
            "total_packages": len(packages),
            "total_candidates": sum(p.total_candidates for p in packages),
            "avg_confidence": sum(p.confidence for p in packages) / len(packages) if packages else 0.0,
            "statuses": list({p.status for p in packages}),
        }
