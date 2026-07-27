"""
DOS Loader — Phase 0

Reads desired-state.yaml and returns a validated DOS contract.
Graceful degradation: returns default DOS if file missing or invalid.
"""

import structlog
import yaml
from pathlib import Path
from typing import Optional
from sam.contracts import DesiredOperationalState
from .models import DOSModel

logger = structlog.get_logger()


class DOSLoader:
    """Loads and validates Desired Operational State from YAML."""

    def __init__(self, workspace_path: str = "workspace"):
        self.workspace_path = Path(workspace_path)

    def load(self, path: Optional[str] = None) -> DesiredOperationalState:
        """Load desired-state.yaml and return a DOS contract.

        Args:
            path: Optional explicit path. Defaults to workspace/desired-state.yaml.

        Returns:
            Validated DOS contract object.
            Returns default DOS if file missing or corrupt.
        """
        file_path = Path(path) if path else self.workspace_path / "desired-state.yaml"

        if not file_path.exists():
            logger.warning("dos_file_not_found", path=str(file_path))
            return DesiredOperationalState()

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            if not isinstance(data, dict):
                raise ValueError("DOS YAML is not a mapping")
            model = DOSModel(**data)
            return model.to_contract()
        except (yaml.YAMLError, ValueError, TypeError) as e:
            logger.error("dos_file_invalid", path=str(file_path), error=str(e))
            return DesiredOperationalState()
