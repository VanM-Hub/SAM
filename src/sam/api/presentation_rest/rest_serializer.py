"""REST Serializer - Program J (Presentation Host).

`RESTSerializer` memetakan hasil capability (dict / DTO immutable) ke bentuk
dict JSON yang aman untuk respons HTTP. Murni mekanis (composition-only), TIDAK
ada business logic, TIDAK ada keputusan bisnis.

Contoh input yang diserialisasi:
- `PreviewOutcomeView` (via `as_dict()`)
- dict hasil capability `ConversationPreviewGateway.preview_with_*` (execution,
  knowledge, workflow, artifact, memory, policy, audit)
- dict status/health dari `RuntimeAPI.status()`/`health()`

TIDAK mengimpor Runtime/Registry/Provider/Connector/ExecutionRuntime.
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional


class RESTSerializer:
    """Serializer hasil capability -> dict JSON (composition-only)."""

    def serialize(self, data: Any) -> Dict[str, Any]:
        """Serialisasi satu nilai (dict / DTO immutable / scalar)."""
        if data is None:
            return {}
        if isinstance(data, dict):
            return {k: self._clean(v) for k, v in data.items()}
        if hasattr(data, "as_dict") and callable(getattr(data, "as_dict")):
            return self.serialize(data.as_dict())
        return {"value": data}

    def serialize_many(self, items: List[Any], key_name: str = "items") -> Dict[str, Any]:
        """Serialisasi daftar ke bentuk {"<key>": [...]}."""
        return {key_name: [self.serialize(i) for i in items]}

    def _clean(self, value: Any) -> Any:
        """Pembersihan nilai agar aman JSON (rekursif, tanpa business logic)."""
        if isinstance(value, dict):
            return {str(k): self._clean(v) for k, v in value.items()}
        if isinstance(value, (list, tuple)):
            return [self._clean(v) for v in value]
        if isinstance(value, (str, int, float, bool)) or value is None:
            return value
        if hasattr(value, "as_dict") and callable(getattr(value, "as_dict")):
            return self._clean(value.as_dict())
        return str(value)

    def item(self, value: Any) -> Dict[str, Any]:
        """Serialize satu item (alias untuk `serialize`)."""
        return self.serialize(value)

    def items(self, values: List[Any], key_name: str = "items") -> Dict[str, Any]:
        """Serialize daftar item."""
        return self.serialize_many(values, key_name=key_name)
