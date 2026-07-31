"""Parameter Builder — membangun parameter skill (Sprint 166).

Phase XVI — Skill Runtime.
Builder hanya membangun parameter DTO. Tidak memilih runtime, tidak execute.
"""
from __future__ import annotations
from typing import List

from ..definition.skill_parameter import SkillParameter


class ParameterBuilder:
    """Builder parameter skill. Deterministik."""

    def build(
        self,
        name: str,
        param_type: str = "string",
        required: bool = False,
        default: object = None,
    ) -> SkillParameter:
        return SkillParameter(
            name=name, param_type=param_type, required=required, default=default,
        )

    def build_many(self, names: List[str]) -> List[SkillParameter]:
        return [self.build(n) for n in names]
