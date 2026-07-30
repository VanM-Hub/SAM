"""Protocol Mapper — mapping protokol."""
from __future__ import annotations
from typing import Dict, List
from sam.runtime_kernel.runtime_adapter import ProtocolMap, InteropResult


class ProtocolMapper:
    """Mapper protokol — preview-only."""

    def __init__(self) -> None:
        self._maps: Dict[str, ProtocolMap] = {}

    def register(self, pmap: ProtocolMap) -> None:
        self._maps[pmap.map_id] = pmap

    def get(self, map_id: str) -> ProtocolMap | None:
        return self._maps.get(map_id)

    def check_interop(self, result_id: str, map_a: ProtocolMap, map_b: ProtocolMap) -> InteropResult:
        compatible = map_a.protocol == map_b.protocol
        messages: List[str] = []
        if not compatible:
            messages.append(
                f"Protocol mismatch: {map_a.protocol} vs {map_b.protocol}"
            )
        if map_a.version != map_b.version:
            messages.append(
                f"Version mismatch: {map_a.version} vs {map_b.version}"
            )
        return InteropResult(
            result_id=result_id,
            compatible=compatible and map_a.version == map_b.version,
            messages=messages,
        )

    def count(self) -> int:
        return len(self._maps)
