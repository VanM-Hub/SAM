from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ConfigValue(BaseModel):
    """Model for a configuration value with metadata about its source."""

    value: Any
    source: str = "json"


class ConfigSchema(BaseModel):
    """Simple schema for configuration validation."""

    required: List[str] = Field(default_factory=list)
    types: Dict[str, str] = Field(default_factory=dict)

    def validate(self, data: Dict[str, Any]) -> None:
        """Validate data against this schema.

        Args:
            data: Configuration dictionary to validate.

        Raises:
            ValueError: If required fields are missing or types don't match.
        """
        # Check required fields
        for field in self.required:
            if field not in data:
                raise ValueError(f"Required configuration field missing: {field}")

        # Check types for fields that have type declarations
        type_map = {
            "str": str,
            "string": str,
            "int": int,
            "integer": int,
            "bool": bool,
            "boolean": bool,
            "float": float,
            "list": list,
            "dict": dict,
        }

        for field, expected_type in self.types.items():
            if field in data:
                value = data[field]
                expected_cls = type_map.get(expected_type.lower())
                if expected_cls is not None and not isinstance(value, expected_cls):
                    raise ValueError(
                        f"Configuration field '{field}' expected type '{expected_type}', "
                        f"got '{type(value).__name__}'"
                    )