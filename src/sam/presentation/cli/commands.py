"""CLI Structure - Program I (Presentation Capability).

Komponen host CLI: CLICommand, CLICommandSpec, CLICommandRegistry.

Prinsip:
- Presentasi murni, composition-only, tanpa business logic.
- CLICommand = DTO immutable (ADR-023) yang mendeskripsikan sebuah command
  presentasi; TIDAK mengeksekusi apapun.
- CLICommandRegistry = registry NAMA -> CLICommand, presentation only,
  tanpa import ke Runtime/Registry/Provider/Connector/ExecutionRuntime.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class CLICommandSpec:
    """Spesifikasi parametrik sebuah command (immutable)."""
    name: str
    description: str = ""
    arguments: tuple = ()
    options: tuple = ()
    requires_runtime: bool = True

    def __post_init__(self) -> None:
        # Normalisasi: pastikan tuple, bukan mutable list
        object.__setattr__(self, "arguments", tuple(self.arguments))
        object.__setattr__(self, "options", tuple(self.options))

    def as_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "arguments": list(self.arguments),
            "options": list(self.options),
            "requires_runtime": self.requires_runtime,
        }


@dataclass(frozen=True)
class CLICommand:
    """Command presentasi (immutable, composition-only).

    `handler` adalah callable yang AKAN di-inject via DI saat wiring ke
    RuntimeService (I2). Di struktur ini (I1) handler boleh None - belum
    dihubungkan ke capability. Tidak ada logika eksekusi di sini.
    """
    name: str
    description: str = ""
    spec: Optional[CLICommandSpec] = None
    handler: Optional[Any] = None

    def __post_init__(self) -> None:
        if self.spec is None:
            spec = CLICommandSpec(name=self.name, description=self.description)
            object.__setattr__(self, "spec", spec)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "spec": self.spec.as_dict() if self.spec else None,
            "has_handler": self.handler is not None,
        }


class CLICommandRegistry:
    """Registry command presentasi (presentation only).

    Penyimpanan NAMA -> CLICommand. Tidak mengimpor/bergantung ke lapisan
    Runtime manapun. Composition memanggil registry ini untuk dispatch.
    """

    def __init__(self, commands: Optional[list] = None) -> None:
        self._commands: Dict[str, CLICommand] = {}
        if commands:
            for cmd in commands:
                self.register(cmd)

    def register(self, command: CLICommand) -> None:
        if not isinstance(command, CLICommand):
            raise TypeError("Hanya CLICommand yang bisa didaftarkan")
        self._commands[command.name] = command

    def register_all(self, commands: list) -> None:
        for command in commands:
            self.register(command)

    def get(self, name: str) -> Optional[CLICommand]:
        return self._commands.get(name)

    def has(self, name: str) -> bool:
        return name in self._commands

    def names(self) -> List[str]:
        return sorted(self._commands.keys())

    def all(self) -> List[CLICommand]:
        return [self._commands[n] for n in self.names()]

    def count(self) -> int:
        return len(self._commands)


def build_command(name: str,
                  description: str = "",
                  arguments: tuple = (),
                  options: tuple = (),
                  requires_runtime: bool = True,
                  handler: Optional[Any] = None) -> CLICommand:
    """Fabrication helper command presentasi (composition-only)."""
    spec = CLICommandSpec(
        name=name,
        description=description,
        arguments=arguments,
        options=options,
        requires_runtime=requires_runtime,
    )
    return CLICommand(
        name=name,
        description=description,
        spec=spec,
        handler=handler,
    )
