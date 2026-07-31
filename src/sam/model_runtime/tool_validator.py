"""Tool Validator — validasi tool generik (Sprint 245).

Program B — Model Runtime Integration.
Deterministik, no execution, preview-only.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from .tool_descriptor import ToolDescriptor
from .tool_arguments import ToolArguments
from .tool_result import ToolResult


@dataclass(frozen=True)
class ToolValidation:
    """Hasil validasi (immutable)."""
    valid: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {"valid": self.valid, "errors": list(self.errors),
                "warnings": list(self.warnings)}


class ToolValidator:
    """Validator tool. Read-only, tidak pernah mengeksekusi tool."""

    def validate_arguments(self, tool: ToolDescriptor, arguments: ToolArguments) -> ToolValidation:
        errors: List[str] = []
        warnings: List[str] = []
        # pastikan required terpenuhi
        for required in tool.required:
            if required in arguments.missing:
                errors.append(f"missing required param: {required}")
            elif required not in arguments.values:
                errors.append(f"missing required param: {required}")
        if arguments.missing:
            warnings.append(f"missing optional params: {arguments.missing}")
        return ToolValidation(valid=not errors, errors=errors, warnings=warnings)

    def validate_result(self, result: ToolResult) -> ToolValidation:
        errors: List[str] = []
        if result.executed:
            errors.append("tool must not be executed in preview")
        if result.external_calls != 0:
            errors.append("external_calls must be 0")
        return ToolValidation(valid=not errors, errors=errors)
