"""CLI Application - Program I (Presentation Capability).

Host CLI presentasi. `CLIApplication` menerima `CLICommandRegistry` +
`CLIFormatter` (composition via DI di entry). Bertanggung jawab:
- dispatch command by nama (lewat registry),
- menampilkan bantuan/daftar command,
- merender hasil (result DTO) via formatter.

TIDAK ada business logic. Eksekusi command dilakukan oleh handler yang
di-inject saat wiring ke RuntimeService (I2). Aplikasi TIDAK mengimpor
Runtime/Registry/Provider/Connector/ExecutionRuntime.
"""
from __future__ import annotations
from typing import Any, List, Optional

from .commands import CLICommand, CLICommandRegistry
from .formatter import CLIFormatter


class CLIApplication:
    """Host CLI presentasi (composition-only)."""

    def __init__(self,
                 registry: Optional[CLICommandRegistry] = None,
                 formatter: Optional[CLIFormatter] = None,
                 name: str = "sam",
                 description: str = "") -> None:
        self._registry = registry if registry is not None else CLICommandRegistry()
        self._formatter = formatter if formatter is not None else CLIFormatter()
        self._name = name
        self._description = description

    # -- properties (composition) --
    @property
    def registry(self) -> CLICommandRegistry:
        return self._registry

    @property
    def formatter(self) -> CLIFormatter:
        return self._formatter

    @property
    def name(self) -> str:
        return self._name

    # -- dispatch --

    def command_names(self) -> List[str]:
        return self._registry.names()

    def has(self, name: str) -> bool:
        return self._registry.has(name)

    def execute(self, name: str, *args: Any, **kwargs: Any) -> Any:
        """Dispatch command by nama. Handler di-inject via DI (I2)."""
        command = self._registry.get(name)
        if command is None:
            raise KeyError("Command tidak dikenal: '{}'".format(name))
        if command.handler is None:
            raise NotImplementedError(
                "Command '{}' belum di-wire ke handler (I2)".format(name)
            )
        # Eksekusi oleh handler inject; aplikasi hanya perantara.
        return command.handler(*args, **kwargs)

    # -- output --

    def render_help(self) -> str:
        """Daftar command untuk output help (composition-only)."""
        rows = [self._formatter.rule("SAM CLI - {}".format(self._name))]
        for name in self.command_names():
            cmd = self._registry.get(name)
            desc = cmd.description if cmd else ""
            rows.append("  {:<14} {}".format(name, desc))
        return self._formatter.render(rows)

    def render_result(self, result: Any) -> str:
        """Render satu hasil (str/dict/DTO) via formatter."""
        if result is None:
            return ""
        if isinstance(result, dict):
            return self._formatter.render(self._formatter.dict_rows(result))
        if hasattr(result, "as_dict") and callable(getattr(result, "as_dict")):
            return self._formatter.render(self._formatter.dict_rows(result.as_dict()))
        return self._formatter.line(result)
