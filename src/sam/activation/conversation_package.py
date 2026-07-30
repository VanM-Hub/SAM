"""Conversation Package Bridge — Sprint 85, 8 queries."""
from typing import Any, Dict, List, Optional
from sam.activation.package_builder import PackageBuilder
from sam.activation.package_validator import PackageValidator, PackageValidation
from sam.activation.package_registry import PackageRegistry
from sam.activation.package_export import PackageExporter, PackageExport
from sam.activation.activation_package import ActivationPackage
from sam.activation.activation_sequence import ActivationSequence
from sam.activation.activation_strategy import ActivationStrategy


class ConversationPackage:
    """Conversation bridge untuk Package module — 8 queries."""

    def __init__(self, registry: PackageRegistry):
        self._pkg_reg = registry

    @property
    def query_count(self) -> int:
        return 8

    def query_build(self, builder: PackageBuilder, seq: ActivationSequence,
                     strat: ActivationStrategy) -> Dict[str, Any]:
        pkg = builder.build(seq, strat)
        self._pkg_reg.register(pkg)
        return {
            "package_id": pkg.package_id,
            "total_candidates": pkg.total_candidates,
            "confidence": pkg.confidence,
            "status": pkg.status,
        }

    def query_package(self, pid: str) -> Optional[Dict[str, Any]]:
        pkg = self._pkg_reg.get(pid)
        if pkg is None:
            return None
        return {
            "package_id": pkg.package_id,
            "strategy_ref": pkg.strategy_ref,
            "total_candidates": pkg.total_candidates,
            "confidence": pkg.confidence,
            "status": pkg.status,
        }

    def query_list(self) -> List[Dict[str, Any]]:
        return [
            {"package_id": p.package_id, "total_candidates": p.total_candidates,
             "confidence": p.confidence, "status": p.status}
            for p in self._pkg_reg.list()
        ]

    def query_validate(self, validator: PackageValidator,
                        package: ActivationPackage) -> Dict[str, Any]:
        val = validator.validate(package)
        self._pkg_reg.register_validation(package.package_id, val)
        return {
            "valid": val.valid,
            "has_candidates": val.has_candidates,
            "has_strategy": val.has_strategy,
            "has_sequence": val.has_sequence,
            "errors": val.errors,
        }

    def query_validation_status(self, pid: str) -> Optional[Dict[str, Any]]:
        val = self._pkg_reg.get_validation(pid)
        if val is None:
            return None
        return {"valid": val.valid, "errors": val.errors}

    def query_export(self, exporter: PackageExporter,
                      package: ActivationPackage) -> Dict[str, Any]:
        exp = exporter.export(package)
        return {
            "package_id": exp.package_id,
            "content": exp.content,
            "exported_at": exp.exported_at,
        }

    def query_export_summary(self, exporter: PackageExporter) -> Dict[str, Any]:
        return exporter.export_summary(self._pkg_reg.list())

    def query_package_count(self) -> Dict[str, Any]:
        validated = sum(
            1 for p in self._pkg_reg.list()
            if self._pkg_reg.get_validation(p.package_id) is not None
        )
        return {
            "total": self._pkg_reg.count,
            "validated": validated,
        }
