"""Package Registry — registry khusus paket."""
from typing import Any, Dict, List, Optional
from sam.activation.activation_package import ActivationPackage
from sam.activation.package_validator import PackageValidation


class PackageRegistry:
    """Registry khusus ActivationPackage."""

    def __init__(self):
        self._packages: Dict[str, ActivationPackage] = {}
        self._validations: Dict[str, PackageValidation] = {}

    def register(self, package: ActivationPackage) -> None:
        self._packages[package.package_id] = package

    def get(self, pid: str) -> Optional[ActivationPackage]:
        return self._packages.get(pid)

    def list(self) -> List[ActivationPackage]:
        return list(self._packages.values())

    @property
    def count(self) -> int:
        return len(self._packages)

    def register_validation(self, pid: str, validation: PackageValidation) -> None:
        self._validations[pid] = validation

    def get_validation(self, pid: str) -> Optional[PackageValidation]:
        return self._validations.get(pid)

    def clear(self) -> None:
        self._packages.clear()
        self._validations.clear()
