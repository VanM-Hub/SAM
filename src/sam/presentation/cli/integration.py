"""CLI Integration - Program I (I11).

Mengintegrasikan capability CLI yang selesai (I3-I9) menjadi satu alur
presentasi CLI yang executable oleh host entry.

Service composition-only: menggabungkan hasil dari command (yang sudah
ter-wire ke jalur resmi runtime_service.api) - TANPA bypass, TANPA akses
langsung Runtime/Provider/Connector/Registry/ExecutionRuntime, TANPA
business logic eksekusi.

Command dengan activation path resmi (I3-I9):
  workflow - policy - audit - preview - knowledge - memory - artifact
Approval (I9) = pass-through (visualisasi status approved saja).
Mission (I10) = Deferred/Escalation - TIDAK dijalankan, dilaporkan status.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .commands import CLICommandRegistry
from .application import CLIApplication
from .formatter import CLIFormatter

__all__ = ["CLICommandResult", "CLIIntegration"]


@dataclass(frozen=True)
class CLICommandResult:
    """Hasil satu command terintegrasi (immutable, composition)."""
    command: str
    ok: bool = False
    data: Any = None
    error: str = ""
    mode: str = "preview"
    source: str = "runtime_service.api"

    def as_dict(self) -> dict:
        return {
            "command": self.command,
            "ok": self.ok,
            "data": _simplify(self.data),
            "error": self.error,
            "mode": self.mode,
            "source": self.source,
        }


def _simplify(value: Any) -> Any:
    if hasattr(value, "as_dict") and callable(getattr(value, "as_dict")):
        return value.as_dict()
    if isinstance(value, dict):
        return dict(value)
    return value


class CLIIntegration:
    """Integrasi CLI - menjalankan command via registry (composition-only).

    Command handler sudah ter-wire ke jalur resmi runtime_service.api pada
    I2 (CLIRuntimeWiring). Integrasi hanya menyusun & mengeksekusi by-name.
    Mission (I10) selalu dilaporkan 'deferred' - TIDAK ada handler.
    """

    DEFERRED = {"mission"}

    def __init__(self,
                 registry: CLICommandRegistry,
                 formatter: Optional[CLIFormatter] = None) -> None:
        self._registry = registry
        self._formatter = formatter if formatter is not None else CLIFormatter()

    @property
    def registry(self) -> CLICommandRegistry:
        return self._registry

    def available_commands(self) -> List[str]:
        return self._registry.names()

    def run(self, name: str, *args: Any, **kwargs: Any) -> CLICommandResult:
        """Jalankan satu command by-name (composition-only)."""
        # Mission/Deferred: tanpa jalur -> laporkan status, tidak dijalankan
        if name in self.DEFERRED:
            return CLICommandResult(command=name, ok=False,
                                    data={"status": "deferred"},
                                    mode="deferred",
                                    error="no activation path")

        cmd = self._registry.get(name)
        if cmd is None:
            return CLICommandResult(command=name, ok=False, error="unknown command")
        if cmd.handler is None:
            return CLICommandResult(command=name, ok=False, error="unwired")

        try:
            data = cmd.handler(*args, **kwargs)
            return CLICommandResult(command=name, ok=True, data=data)
        except Exception as exc:  # noqa: BLE001 - composition boundary
            return CLICommandResult(command=name, ok=False,
                                    error="{}: {}".format(type(exc).__name__, exc))

    def render(self, result: CLICommandResult) -> str:
        """Render hasil command via formatter (output console)."""
        app = CLIApplication(registry=self._registry, formatter=self._formatter)
        if result.ok:
            return self._formatter.render([
                self._formatter.rule("sam {}".format(result.command)),
                app.render_result(result.data),
            ])
        # error / deferred
        rows = [self._formatter.rule("sam {}".format(result.command))]
        if result.mode == "deferred":
            rows.append(self._formatter.kv(
                "status", "deferred (no activation path)"))
            if result.data:
                rows.append(self._formatter.line(
                    "  " + _simplify_str(result.data)))
        else:
            rows.append(self._formatter.kv("status", "error"))
        if result.error and result.mode != "deferred":
            rows.append(self._formatter.line("  " + result.error))
        return self._formatter.render(rows)


def _simplify_str(value: Any) -> str:
    d = _simplify(value)
    if isinstance(d, dict):
        return str(d)
    return str(d)
