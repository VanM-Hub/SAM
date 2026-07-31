"""Conversation Model Bridge — 5 read-only queries (Sprint 221)."""
from __future__ import annotations

from .artifact import Artifact
from .artifact_validator import ArtifactValidator


class ConversationModelBridge:
    """Bridge conversation — 5 query model artifact."""

    def __init__(self) -> None:
        self._validator = ArtifactValidator()

    def query_1_sample(self) -> Artifact:
        return Artifact(name="out", kind="report")

    def query_2_validate(self, name: str) -> dict:
        a = Artifact(name=name, kind="report")
        return {"valid": self._validator.validate(a).valid}

    def query_3_tags(self) -> dict:
        return {"required": ["name", "kind", "content"]}

    def query_4_immutable(self) -> bool:
        return Artifact(name="x", kind="y").immutable

    def query_5_kinds(self) -> tuple:
        return ("report", "plan", "decision", "log", "metric")
