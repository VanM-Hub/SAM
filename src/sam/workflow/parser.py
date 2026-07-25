"""YAML parser for workflow definitions."""

from pathlib import Path
from typing import Union

import yaml

from .models import WorkflowDefinition


class WorkflowParser:
    """Parses workflow definitions from YAML content or files."""

    def __init__(self) -> None:
        self._loader = yaml.SafeLoader

    async def parse_yaml(self, content: str) -> WorkflowDefinition:
        """Parse workflow definition from YAML string."""
        data = yaml.safe_load(content)
        if data is None:
            raise ValueError("Empty YAML content")
        return WorkflowDefinition(**data)

    async def parse_file(self, path: Union[str, Path]) -> WorkflowDefinition:
        """Parse workflow definition from YAML file."""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Workflow file not found: {path}")
        content = path.read_text(encoding="utf-8")
        return await self.parse_yaml(content)