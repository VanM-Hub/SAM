"""Presentation Layer: CLI capability - Program I (AP-MISSION-004-001).

Struktur host CLI presentasi:
- CLIApplication  : host (dispatch + render via formatter)
- CLICommand      : DTO immutable deskripsi command
- CLICommandSpec  : spesifikasi parametrik command (immutable)
- CLICommandRegistry : registry nama -> CLICommand (presentation only)
- CLIFormatter    : formatting output (no business logic)

Capability dihubungkan ke RuntimeService pada I2 via jalur
runtime_service.api (DI). Di sini TIDAK ada business logic dan TIDAK
ada akses langsung ke Runtime/Registry/Provider/Connector/ExecutionRuntime.
"""
from .commands import (
    CLICommand,
    CLICommandSpec,
    CLICommandRegistry,
    build_command,
)
from .formatter import CLIFormatter
from .application import CLIApplication
from .wiring import CLIRuntimeWiring, wire_cli_runtime, CLI_CORE_COMMANDS
from .integration import CLICommandResult, CLIIntegration

__all__ = [
    "CLICommand",
    "CLICommandSpec",
    "CLICommandRegistry",
    "build_command",
    "CLIFormatter",
    "CLIApplication",
    "CLIRuntimeWiring",
    "wire_cli_runtime",
    "CLI_CORE_COMMANDS",
    "CLICommandResult",
    "CLIIntegration",
]
