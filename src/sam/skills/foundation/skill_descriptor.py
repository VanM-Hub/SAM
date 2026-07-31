"""Skill Descriptor — deskripsi skill (immutable DTO, Sprint 164).

Phase XVI — Skill Runtime.
Field sesuai blueprint: id, name, version, category, description, author,
tags, capabilities, inputs, outputs, constraints, metadata.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class SkillDescriptor:
    """Deskripsi skill (immutable)."""
    id: str
    name: str = ""
    version: str = "1.0.0"
    category: str = "general"
    description: str = ""
    author: str = ""
    tags: List[str] = field(default_factory=list)
    capabilities: List[str] = field(default_factory=list)
    inputs: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
