"""ManifestSerializer — serialize/deserialize a ComplianceManifest.

The manifest is the single source of execution configuration, so it
must round-trip losslessly between the in-memory object and a plain
dict / JSON document. Serialization is deterministic: same manifest
produces identical output.
"""

import json
from typing import Dict, List, Any

from .entry import ManifestEntry
from .manifest import ComplianceManifest


class ManifestSerializer:
    """Serializes and deserializes ComplianceManifest objects."""

    # -- Serialize ------------------------------------------------------------

    def serialize(self, manifest: ComplianceManifest) -> List[Dict[str, Any]]:
        """Serialize manifest entries to a list of dicts.

        Entries are emitted in deterministic order
        (by execution_order, then check_id).
        """
        return [entry.to_dict() for entry in manifest.entries()]

    def to_json(self, manifest: ComplianceManifest, indent: int = 2) -> str:
        """Serialize manifest to a JSON string (deterministic)."""
        return json.dumps(self.serialize(manifest), indent=indent, sort_keys=True)

    # -- Deserialize ----------------------------------------------------------

    def deserialize(self, data: List[Dict[str, Any]]) -> ComplianceManifest:
        """Build a ComplianceManifest from a list of dicts.

        Args:
            data: List of entry dicts (as produced by serialize()).

        Returns:
            ComplianceManifest.

        Raises:
            ManifestError: If a dict is malformed or has a duplicate check_id.
        """
        entries: List[ManifestEntry] = []
        for item in data:
            entries.append(self._entry_from_dict(item))
        return ComplianceManifest(entries)

    def from_json(self, text: str) -> ComplianceManifest:
        """Build a ComplianceManifest from a JSON string."""
        return self.deserialize(json.loads(text))

    # -- Internal -------------------------------------------------------------

    def _entry_from_dict(self, item: Dict[str, Any]) -> ManifestEntry:
        from ..models.severity import Severity

        severity = item.get("severity")
        if severity is not None:
            try:
                severity = Severity.from_str(severity)
            except ValueError:
                severity = None

        return ManifestEntry(
            check_id=str(item["check_id"]),
            enabled=bool(item.get("enabled", True)),
            execution_order=int(item.get("execution_order", 0)),
            checker_class=str(item.get("checker_class", "")),
            configuration=dict(item.get("configuration", {}) or {}),
            timeout=item.get("timeout"),
            retry_policy=str(item.get("retry_policy", "none")),
            severity=severity,
            dependencies=list(item.get("dependencies", []) or []),
            tags=list(item.get("tags", []) or []),
        )
