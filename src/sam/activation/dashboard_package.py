"""Dashboard Package Bridge — Sprint 85, 5 cards."""
from typing import Any, Dict, List
from dataclasses import dataclass, field
from sam.activation.package_registry import PackageRegistry
from sam.activation.package_builder import PackageBuilder
from sam.activation.package_validator import PackageValidator
from sam.activation.package_export import PackageExporter
from sam.activation.activation_sequence import ActivationSequence
from sam.activation.activation_strategy import ActivationStrategy
from sam.activation.activation_package import ActivationPackage


@dataclass(frozen=True)
class PackageCard:
    card_type: str = ""
    title: str = ""
    items: List[str] = field(default_factory=list)


class DashboardPackage:
    """Dashboard bridge untuk Package — 5 cards."""

    def __init__(self, pkg_reg: PackageRegistry):
        self._pkg_reg = pkg_reg

    @property
    def card_count(self) -> int:
        return 5

    def get_cards(self, builder: PackageBuilder, seq: ActivationSequence,
                  strat: ActivationStrategy) -> List[PackageCard]:
        pkg = builder.build(seq, strat)
        self._pkg_reg.register(pkg)
        return [
            self._package_card(pkg),
            self._validation_card(pkg),
            self._registry_card(),
            self._export_card(pkg),
            self._summary_card(pkg, seq, strat),
        ]

    def _package_card(self, pkg: ActivationPackage) -> PackageCard:
        return PackageCard(
            "package", "Activation Package",
            [f"ID: {pkg.package_id}", f"Status: {pkg.status}",
             f"Candidates: {pkg.total_candidates}", f"Confidence: {pkg.confidence}"],
        )

    def _validation_card(self, pkg: ActivationPackage) -> PackageCard:
        validator = PackageValidator()
        val = validator.validate(pkg)
        return PackageCard(
            "validation", "Package Validation",
            [f"Valid: {val.valid}", f"Candidates: {val.has_candidates}",
             f"Strategy: {val.has_strategy}", f"Sequence: {val.has_sequence}",
             f"Errors: {len(val.errors)}"],
        )

    def _registry_card(self) -> PackageCard:
        return PackageCard(
            "registry", "Package Registry",
            [f"Total: {self._pkg_reg.count}",
             f"Validated: {sum(1 for p in self._pkg_reg.list() if self._pkg_reg.get_validation(p.package_id) is not None)}"],
        )

    def _export_card(self, pkg: ActivationPackage) -> PackageCard:
        exporter = PackageExporter()
        exp = exporter.export(pkg)
        return PackageCard(
            "export", "Package Export",
            [f"Format: {exp.format}", f"Exported: {exp.exported_at > 0}",
             f"Content keys: {len(exp.content)}"],
        )

    def _summary_card(self, pkg: ActivationPackage, seq: ActivationSequence,
                      strat: ActivationStrategy) -> PackageCard:
        return PackageCard(
            "summary", "Package Summary",
            [f"Package: {pkg.package_id}", f"Strategy: {strat.name}",
             f"Sequence steps: {seq.total_steps}", f"Duration: {pkg.estimated_duration:.0f}s"],
        )
