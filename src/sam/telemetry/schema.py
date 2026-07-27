"""
JSON Schema validation for TelemetryEvent.
"""

import json
from pathlib import Path
from typing import Dict, Any


def load_event_schema(path: str = None) -> Dict[str, Any]:
    """Load the TelemetryEvent JSON Schema.

    Args:
        path: Override path to event_schema.json. Defaults to
              ``src/sam/contracts/event_schema.json`` relative to this file.

    Returns:
        The parsed JSON Schema dict.
    """
    if path is None:
        path = str(Path(__file__).resolve().parent.parent / "contracts" / "event_schema.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_against_schema(event_dict: Dict[str, Any], schema: Dict[str, Any] = None) -> bool:
    """Validate an event dict against the JSON Schema.

    Uses a lightweight manual validation as a fast check.
    For full JSON Schema compliance, use ``jsonschema`` when available.

    Args:
        event_dict: The event as a plain dict.
        schema: Schema dict. Loaded automatically if None.

    Returns:
        True if valid, False otherwise.
    """
    if schema is None:
        schema = load_event_schema()

    required = schema.get("required", [])
    properties = schema.get("properties", {})

    # Check required fields
    for field in required:
        if field not in event_dict or event_dict[field] is None:
            return False

    # Check enums
    type_enum = properties.get("type", {}).get("enum", [])
    if type_enum and event_dict.get("type") not in type_enum:
        return False

    component_enum = properties.get("component", {}).get("enum", [])
    if component_enum and event_dict.get("component") not in component_enum:
        return False

    severity_enum = properties.get("severity", {}).get("enum", [])
    if severity_enum and event_dict.get("severity") not in severity_enum:
        return False

    category_enum = properties.get("category", {}).get("enum", [])
    if category_enum and event_dict.get("category") not in category_enum:
        return False

    # Check message length
    message = event_dict.get("message", "")
    max_length = properties.get("message", {}).get("maxLength", 500)
    if len(message) > max_length:
        return False

    return True
