"""CLI Formatter - Program I (Presentation Capability).

Menyajikan hasil (result DTO) sebagai teks/baris yang rapi untuk output
console. Composition-only: TIDAK ada business logic, hanya formatting
representasi dari DTO yang sudah jadi.
"""
from __future__ import annotations
from typing import Any, Dict, List


class CLIFormatter:
    """Formats result (DTO/str/dict) menjadi baris output konsisten."""

    def __init__(self, width: int = 48) -> None:
        self._width = width
        self._sep = "-" * width

    def rule(self, title: str = "") -> str:
        if title:
            return "=" * self._width + "\n  " + title + "\n" + self._sep
        return "=" * self._width

    def kv(self, key: str, value: Any) -> str:
        return "  {}:  {}".format(str(key), _stringify(value))

    def section(self, title: str) -> str:
        return "\n" + title + "\n" + self._sep

    def line(self, text: str = "") -> str:
        return str(text)

    def dict_rows(self, data: Dict[str, Any]) -> List[str]:
        rows = []
        for k, v in data.items():
            rows.append(self.kv(k, v))
        return rows

    def bullets(self, items: list) -> List[str]:
        return ["  - {}".format(_stringify(i)) for i in items]

    def render(self, parts: list) -> str:
        """Gabungkan baris/bagian menjadi satu blok output."""
        return "\n".join(str(p) for p in parts)


def _stringify(value: Any) -> str:
    if isinstance(value, dict):
        return _dict_to_line(value)
    if hasattr(value, "as_dict") and callable(getattr(value, "as_dict")):
        return str(value.as_dict())
    return str(value)


def _dict_to_line(data: Dict[str, Any]) -> str:
    inner = ", ".join("{}={}".format(k, v) for k, v in data.items())
    return "{" + inner + "}"
