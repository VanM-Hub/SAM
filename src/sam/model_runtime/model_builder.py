"""Model Builder — builder deterministik untuk model foundation (Sprint 239).

Program B — Model Runtime Integration.
Immutable hasil, deterministik, preview-only, external_calls=0.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from .model_descriptor import ModelDescriptor
from .model_contract import ModelContract
from .model_metadata import ModelMetadata


@dataclass(frozen=True)
class ModelBuilder:
    """Builder deterministik untuk mendaftarkan sebuah model."""

    def build_descriptor(
        self,
        model_id: str,
        name: str,
        model_type: str = "chat",
        description: str = "",
        tags: List[str] | None = None,
        integrated_runtimes: List[str] | None = None,
    ) -> ModelDescriptor:
        return ModelDescriptor(
            id=model_id,
            name=name,
            model_type=model_type,
            description=description,
            tags=list(tags or []),
            integrated_runtimes=list(integrated_runtimes or []),
        )

    def build_contract(
        self,
        contract_id: str,
        owner_id: str,
        operations: List[str] | None = None,
    ) -> ModelContract:
        return ModelContract(
            contract_id=contract_id,
            owner_id=owner_id,
            operations=list(operations or []),
            preview_only=True,
            external_calls=0,
        )

    def build_metadata(self, owner_id: str) -> ModelMetadata:
        return ModelMetadata(owner_id=owner_id, preview_only=True, no_inference=True)


class ModelFoundationBuilder:
    """Alias fasilitas: mengkomposisi descriptor + contract + metadata.

    Deterministis dan read-only; tidak melakukan apa pun ke eksternal.
    """

    def __init__(self) -> None:
        self._builder = ModelBuilder()

    def compose(
        self,
        model_id: str,
        name: str,
        model_type: str = "chat",
        operations: List[str] | None = None,
    ) -> dict:
        descriptor = self._builder.build_descriptor(model_id, name, model_type)
        contract = self._builder.build_contract(
            contract_id=f"c-{model_id}",
            owner_id=model_id,
            operations=operations or ["preview"],
        )
        metadata = self._builder.build_metadata(model_id)
        return {
            "descriptor": descriptor,
            "contract": contract,
            "metadata": metadata,
        }
