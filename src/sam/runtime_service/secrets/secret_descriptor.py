"""SecretDescriptor (Sprint 263).

Program D - Runtime Services & Deployment.
Deskripsi secret (immutable). Tidak mengandung nilai secret.
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class SecretDescriptor:
    """Deskripsi secret (immutable). Menyimpan nama & metadata, bukan nilai."""
    key: str
    required: bool = False
    source: str = "env"  # selalu env untuk Program D
    description: str = ""

    def __post_init__(self) -> None:
        if not self.key:
            raise ValueError("key is required")
        if self.source != "env":
            raise ValueError("secret source harus 'env' di Program D")

    def as_dict(self) -> dict:
        return {
            "key": self.key,
            "required": self.required,
            "source": self.source,
            "description": self.description,
        }

    def __repr__(self) -> str:  # jangan bocorkan nilai
        return f"SecretDescriptor(key={self.key}, source=env)"
