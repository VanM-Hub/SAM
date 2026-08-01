"""Sprint 273 - Desktop Workspace: validator (service, tanpa IO)."""
from __future__ import annotations

from typing import List, Tuple

from .workspace_model import WorkspaceModel


class WorkspaceValidator:
    """Validator deklaratif untuk model/layout workspace.

    Class service (bukan DTO); tidak menyimpan state mutabel.
    """

    @staticmethod
    def validate_model(model: WorkspaceModel) -> List[str]:
        issues: List[str] = []
        if not model.workspace_id:
            issues.append("workspace_id kosong")
        if model.active_panel and model.active_panel not in model.panels:
            issues.append("active_panel tidak ada di panels")
        return issues

    @staticmethod
    def validate_panels(panels: Tuple[str, ...]) -> List[str]:
        issues: List[str] = []
        seen = set()
        for p in panels:
            if not p:
                issues.append("nama panel kosong")
            if p in seen:
                issues.append(f"panel duplikat: {p}")
            seen.add(p)
        return issues
