"""Docker Validator — validasi request docker (deterministik).

Sprint 148 — Docker Provider.
Memvalidasi request container/image/compose tanpa eksekusi.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from .container_request import ContainerRequest
from .image_request import ImageRequest
from .compose_request import ComposeRequest


@dataclass(frozen=True)
class DockerValidation:
    """Hasil validasi request docker (immutable)."""
    valid: bool = True
    issues: List[str] = field(default_factory=list)


class DockerValidator:
    """Validator request docker. Deterministik, build-only."""

    def validate_container(self, request: ContainerRequest) -> DockerValidation:
        issues = []
        if not request.request_id:
            issues.append("request_id required")
        if not request.image:
            issues.append("image required")
        return DockerValidation(valid=not issues, issues=issues)

    def validate_image(self, request: ImageRequest) -> DockerValidation:
        issues = []
        if not request.request_id:
            issues.append("request_id required")
        if not request.reference:
            issues.append("reference required")
        return DockerValidation(valid=not issues, issues=issues)

    def validate_compose(self, request: ComposeRequest) -> DockerValidation:
        issues = []
        if not request.request_id:
            issues.append("request_id required")
        if not request.project:
            issues.append("project required")
        return DockerValidation(valid=not issues, issues=issues)
