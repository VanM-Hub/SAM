"""CheckFactory — builds compliance checks from configuration dictionaries.

The factory maintains a type registry. New check types can be registered
at any time. Checks are built from dict configs like:

    {
        "type": "FileExistsCheck",
        "check_id": "L0-01",
        "level": "L0",
        "category": "Foundation",
        "path": "src/sam/__init__.py",
        ...
    }

Framework does NOT need modification to add new check types.
"""

from __future__ import annotations

from typing import Dict, List, Type

from ..base.base_check import BaseComplianceCheck
from ..base.composite_check import CompositeComplianceCheck, CompositeMode
from ...models.level import ComplianceLevel
from ...models.category import ComplianceCategory
from ...models.severity import Severity
from ...models.evidence_type import EvidenceType


class CheckFactoryError(Exception):
    """Raised when factory cannot build a check from config."""


class CheckFactory:
    """Builds checks from configuration dictionaries.

    Type registration is open: new check types can be added
    without modifying the factory itself.
    """

    _types: Dict[str, Type[BaseComplianceCheck]] = {}

    @classmethod
    def register_type(cls, name: str, check_cls: Type[BaseComplianceCheck]) -> None:
        """Register a check type for factory construction.

        Args:
            name: Unique type name (convention: class name, e.g. 'FileExistsCheck').
            check_cls: The BaseComplianceCheck subclass.

        Raises:
            CheckFactoryError: If type name already registered.
        """
        if name in cls._types:
            raise CheckFactoryError("Type already registered: %s" % name)
        cls._types[name] = check_cls

    @classmethod
    def unregister_type(cls, name: str) -> None:
        """Remove a check type from the type registry."""
        cls._types.pop(name, None)

    @classmethod
    def registered_types(cls) -> List[str]:
        """Return sorted list of registered type names."""
        return sorted(cls._types.keys())

    @classmethod
    def create(cls, config: Dict) -> BaseComplianceCheck:
        """Build a check from a configuration dictionary.

        Config must contain at minimum:
        - type: registered type name
        - check_id: unique check identifier

        Common metadata is extracted from config, type-specific
        fields are passed through.

        Args:
            config: Configuration dictionary.

        Returns:
            A BaseComplianceCheck instance.

        Raises:
            CheckFactoryError: If type not found or config is invalid.
        """
        if "type" not in config:
            raise CheckFactoryError("Config missing required field: 'type'")

        if "check_id" not in config:
            raise CheckFactoryError("Config missing required field: 'check_id'")

        type_name = config["type"]

        if type_name == "CompositeComplianceCheck":
            return cls._create_composite(config)

        if type_name not in cls._types:
            raise CheckFactoryError(
                "Unknown check type: '%s'. Registered: %s"
                % (type_name, ", ".join(cls.registered_types()))
            )

        check_cls = cls._types[type_name]
        return cls._build_check(check_cls, config)

    @classmethod
    def create_all(cls, configs: List[Dict]) -> List[BaseComplianceCheck]:
        """Build multiple checks from a list of configurations.

        Args:
            configs: List of configuration dictionaries.

        Returns:
            List of BaseComplianceCheck instances.

        Raises:
            CheckFactoryError: If any config fails to build.
        """
        return [cls.create(cfg) for cfg in configs]

    @classmethod
    def clear_types(cls) -> None:
        """Remove all registered types. For testing only."""
        cls._types = {}

    # -- Internal helpers ----------------------------------------------------

    @classmethod
    def _extract_metadata(cls, config: Dict) -> Dict:
        """Extract common metadata fields from config, applying defaults."""
        return {
            "check_id": config["check_id"],
            "level": ComplianceLevel.from_str(config.get("level", "L0")),
            "category": ComplianceCategory.from_str(
                config.get("category", "Foundation")
            ),
            "description": config.get("description", ""),
            "evidence_type": EvidenceType.from_str(
                config.get("evidence_type", "FILE_EXISTS")
            ),
            "severity": Severity.from_str(config.get("severity", "INFO")),
            "baseline_ref": config.get("baseline_ref", ""),
            "recommendation": config.get("recommendation", ""),
        }

    @classmethod
    def _build_check(
        cls, check_cls: Type[BaseComplianceCheck], config: Dict
    ) -> BaseComplianceCheck:
        """Build a single check instance from config."""
        metadata = cls._extract_metadata(config)
        # Strip factory-reserved keys before passing to constructor
        extra = {k: v for k, v in config.items()
                 if k not in ("type", "check_id", "level", "category",
                              "description", "evidence_type", "severity",
                              "baseline_ref", "recommendation", "mode", "checks")}
        return check_cls(**{**metadata, **extra})

    @classmethod
    def _create_composite(cls, config: Dict) -> BaseComplianceCheck:
        """Build a CompositeComplianceCheck from config."""
        metadata = cls._extract_metadata(config)
        sub_configs = config.get("checks", [])
        sub_checks = [cls.create(sc) for sc in sub_configs]
        mode = CompositeMode.ALL
        if config.get("mode", "ALL") == "ANY":
            mode = CompositeMode.ANY

        return CompositeComplianceCheck(
            checks=sub_checks,
            mode=mode,
            **metadata,
        )
