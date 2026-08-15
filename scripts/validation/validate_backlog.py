"""validate_backlog.py — blokir import dari folder backlog (ATLAS.md).

Menutup gap review B4: folder backlog ("belum aktif; butuh Architecture
Decision") ada di filesystem tapi tanpa enforcement, sehingga engineer bisa
tak sengaja import-nya. Script ini scan `src/sam/**/*.py` dan melaporkan
setiap import absolut `sam.<backlog>` dari file DI LUAR folder backlog tsb.

Backlog != aktif: import internal di dalam folder backlog yang sama (self-
package) diizinkan; yang dilarang adalah kode aktif (atau folder backlog lain)
menjangkau ke dalamnya.

Sumber daftar: ATLAS.md -> "backlog (belum aktif; butuh Architecture Decision)".
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[2] / "src" / "sam"

# Sumber: ATLAS.md "backlog (belum aktif; butuh Architecture Decision)".
BACKLOG = (
    "intelligence_runtime",
    "agent",
    "model_runtime",
    "connectors",
    "orchestrator",
    "skills",
)

_ALTS = "|".join(BACKLOG)
_PATTERN = re.compile(
    rf"^\s*(?:from\s+sam\.({_ALTS})(?:\.|\s)|import\s+sam\.({_ALTS})(?:\s|$))"
)


def violations() -> list[str]:
    """Kembalikan daftar "relpath:line: pesan" import backlog ilegal."""
    found: list[str] = []
    for py in sorted(SRC.rglob("*.py")):
        rel = py.relative_to(SRC.parent)  # e.g. sam/agent/planner/x.py
        text = py.read_text(encoding="utf-8", errors="ignore")
        for lineno, line in enumerate(text.splitlines(), 1):
            m = _PATTERN.match(line)
            if not m:
                continue
            target = m.group(1) or m.group(2)
            # izinkan self-package import (file berada di folder backlog tsb)
            if rel.parts[:2] == ("sam", target):
                continue
            found.append(f"{rel}:{lineno}: import sam.{target} (backlog)")
    return found


def main() -> int:
    found = violations()
    if not found:
        print("validate_backlog PASS: tidak ada import dari folder backlog")
        return 0
    print(f"validate_backlog: {len(found)} import dari folder backlog ditemukan:")
    for line in found:
        print("  " + line)
    print("Backlog = belum aktif; butuh Architecture Decision (ATLAS.md).")
    return 1


if __name__ == "__main__":
    sys.exit(main())
