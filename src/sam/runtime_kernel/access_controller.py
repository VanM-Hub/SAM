"""Access Controller — kontrol akses."""
from __future__ import annotations
from typing import Dict, List
from sam.runtime_kernel.runtime_security import AccessControl


class AccessController:
    """Kontrol akses — preview-only."""

    def __init__(self) -> None:
        self._controls: Dict[str, AccessControl] = {}

    def add(self, control: AccessControl) -> None:
        self._controls[control.access_id] = control

    def get(self, access_id: str) -> AccessControl | None:
        return self._controls.get(access_id)

    def check(self, subject: str, resource: str, permission: str) -> bool:
        for c in self._controls.values():
            if (c.subject == subject and c.resource == resource
                    and c.permission == permission):
                return c.granted
        return False

    def count(self) -> int:
        return len(self._controls)

    def list_granted(self, subject: str) -> List[AccessControl]:
        return [c for c in self._controls.values()
                if c.subject == subject and c.granted]
