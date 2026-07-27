"""
Mission Loader — Phase 0

Reads mission.yaml and returns a validated Mission contract.
Graceful degradation: returns default mission if file missing or invalid.
"""

import structlog
import yaml
from pathlib import Path
from typing import Optional
from sam.contracts import Mission
from .models import MissionModel

logger = structlog.get_logger()


class MissionLoader:
    """Loads and validates Mission from YAML."""

    def __init__(self, workspace_path: str = "workspace"):
        self.workspace_path = Path(workspace_path)

    def load(self, path: Optional[str] = None) -> Mission:
        """Load mission.yaml and return a Mission contract.

        Args:
            path: Optional explicit path. Defaults to workspace/mission.yaml.

        Returns:
            Validated Mission contract object.
            Returns default mission if file missing or corrupt.
        """
        file_path = Path(path) if path else self.workspace_path / "mission.yaml"

        if not file_path.exists():
            logger.warning("mission_file_not_found", path=str(file_path))
            return Mission(
                id="default-mission",
                name="Default Mission",
                description="Default mission (file not found)",
                objectives=[],
            )

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            if not isinstance(data, dict):
                raise ValueError("Mission YAML is not a mapping")
            model = MissionModel(**data)
            return model.to_contract()
        except (yaml.YAMLError, ValueError, TypeError) as e:
            logger.error("mission_file_invalid", path=str(file_path), error=str(e))
            return Mission(
                id="default-mission",
                name="Default Mission",
                description="Invalid mission file, using defaults",
                objectives=[],
            )
