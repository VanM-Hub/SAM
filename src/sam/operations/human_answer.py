"""
HumanAnswer — DTO semantik murni.

TIDAK tahu bagaimana dirinya dirender.
Tidak ada display_cli(), display_short().
Renderer ada di render/ folder.

Tujuan: Desktop, CLI, Voice, JSON, Markdown — semuanya dari data yang sama.
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class HumanAnswer:
    """DTO presentasi murni — tidak tahu cara render.

    Semantic UI:
      - title: baris pertama, langsung memberi orientasi
      - summary: ringkasan 1-2 kalimat
      - sections: bagian-bagian detail (list of (heading, content))
      - cards: kartu informasi terpisah (list of (icon, title, detail))
      - actions: tombol/tindakan yang bisa dilakukan
      - severity: "info" | "success" | "warning" | "error" | "critical"
      - priority: 1-5 (1=tertinggi)
      - icon: emoji/ikon untuk visual
      - badges: label kecil (list of (text, color))
      - links: referensi (list of (label, target))
    """
    question: str = ""
    title: str = ""
    summary: str = ""
    details: str = ""            # deprecated — pake sections
    sections: List[tuple] = field(default_factory=list)   # (heading, content)
    cards: List[tuple] = field(default_factory=list)       # (icon, title, detail)
    actions: List[str] = field(default_factory=list)
    severity: str = "info"       # "info" | "success" | "warning" | "error" | "critical"
    priority: int = 3            # 1-5
    icon: str = ""
    badges: List[tuple] = field(default_factory=list)     # (text, color)
    links: List[tuple] = field(default_factory=list)      # (label, target)
    intent: str = ""
