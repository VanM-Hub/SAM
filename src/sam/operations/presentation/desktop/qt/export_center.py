"""ExportCenter — Export mission/timeline/approval data to file formats.

Supports: TXT, Markdown, JSON, CSV.
All data from DTO via bridge pipeline. No direct query.
No business logic. Presentation only.
"""

from __future__ import annotations

import csv
import io
import json
from datetime import datetime
from typing import Dict, List, Optional, Any

try:
    from PySide6.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QLabel,
        QComboBox, QPushButton, QFileDialog, QMessageBox,
        QTextEdit, QCheckBox, QGroupBox, QRadioButton,
        QButtonGroup, QWidget,
    )
    from PySide6.QtCore import Qt, QTimer
    HAS_QT = True
except ImportError:
    HAS_QT = False


# ── Formatters ───────────────────────────────────────────────────────

def _format_txt(name: str, data: List[Dict]) -> str:
    """Format data as plain text report."""
    lines = [
        "=" * 60,
        f"  SAM Report: {name}",
        f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "=" * 60,
        "",
    ]
    for i, row in enumerate(data, 1):
        lines.append(f"--- Record {i} ---")
        for key, val in row.items():
            lines.append(f"  {key}: {val}")
        lines.append("")
    lines.append("=" * 60)
    lines.append(f"End of report — {len(data)} records")
    return "\n".join(lines)


def _format_markdown(name: str, data: List[Dict]) -> str:
    """Format data as Markdown."""
    lines = [
        f"# SAM Report: {name}",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
        "",
    ]
    if not data:
        lines.append("*No records*")
        return "\n".join(lines)

    # Table header
    headers = list(data[0].keys())
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join("---" for _ in headers) + " |")

    for row in data:
        values = [str(row.get(h, "")) for h in headers]
        lines.append("| " + " | ".join(values) + " |")

    lines.append("")
    lines.append(f"*{len(data)} records*")
    return "\n".join(lines)


def _format_json(data: List[Dict]) -> str:
    """Format data as pretty-printed JSON."""
    return json.dumps(data, indent=2, default=str)


def _format_csv(data: List[Dict]) -> str:
    """Format data as CSV."""
    if not data:
        return ""

    output = io.StringIO()
    headers = list(data[0].keys())
    writer = csv.DictWriter(output, fieldnames=headers)
    writer.writeheader()
    for row in data:
        out_row = {k: str(v) for k, v in row.items()}
        writer.writerow(out_row)
    return output.getvalue()


FORMATTERS = {
    "txt": _format_txt,
    "md": _format_markdown,
    "json": _format_json,
    "csv": _format_csv,
}

FORMAT_EXTENSIONS = {
    "txt": ".txt",
    "md": ".md",
    "json": ".json",
    "csv": ".csv",
}


# ── Export Preview Dialog ────────────────────────────────────────────

class ExportPreviewDialog(QDialog):
    """Preview and export dialog for report data."""

    def __init__(self, title: str, data: List[Dict],
                 parent: Optional[QWidget] = None):
        if not HAS_QT:
            raise ImportError("PySide6 is required")
        super().__init__(parent)

        self._title = title
        self._data = data
        self._export_format = "md"

        self.setWindowTitle(f"Export: {title}")
        self.setMinimumSize(600, 400)
        self._build()

    def _build(self) -> None:
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Header
        header = QLabel(f"<b>Export:</b> {self._title} ({len(self._data)} records)")
        layout.addWidget(header)

        # Format selector
        fmt_layout = QHBoxLayout()
        fmt_label = QLabel("Format:")
        fmt_layout.addWidget(fmt_label)

        self._format_cb = QComboBox()
        self._format_cb.addItems(["md", "txt", "json", "csv"])
        self._format_cb.currentTextChanged.connect(self._on_format_changed)
        fmt_layout.addWidget(self._format_cb)
        fmt_layout.addStretch()
        layout.addLayout(fmt_layout)

        # Preview
        preview_label = QLabel("<b>Preview:</b>")
        layout.addWidget(preview_label)

        self._preview = QTextEdit()
        self._preview.setReadOnly(True)
        self._preview.setMaximumHeight(250)
        layout.addWidget(self._preview)

        # Update preview
        self._update_preview()

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        copy_btn = QPushButton("Copy to Clipboard")
        copy_btn.clicked.connect(self._copy_to_clipboard)
        btn_layout.addWidget(copy_btn)

        save_btn = QPushButton("Save to File...")
        save_btn.clicked.connect(self._save_to_file)
        btn_layout.addWidget(save_btn)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)

    def _on_format_changed(self, fmt: str) -> None:
        self._export_format = fmt
        self._update_preview()

    def _update_preview(self) -> None:
        if not self._data:
            self._preview.setText("*No data*")
            return
        fmt = self._export_format
        formatter = FORMATTERS.get(fmt, FORMATTERS["md"])
        if fmt in ("txt", "md"):
            content = formatter(self._title, self._data)
        else:
            content = formatter(self._data)
        self._preview.setText(content)

    def _get_content(self) -> str:
        return self._preview.toPlainText()

    def _copy_to_clipboard(self) -> None:
        from PySide6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(self._get_content())
        QMessageBox.information(self, "Copied", "Report copied to clipboard.")

    def _save_to_file(self) -> None:
        ext = FORMAT_EXTENSIONS.get(self._export_format, ".txt")
        fname, _ = QFileDialog.getSaveFileName(
            self, f"Save {self._title}", f"{self._title}{ext}",
            f"*{ext}",
        )
        if not fname:
            return
        try:
            with open(fname, "w", encoding="utf-8") as f:
                f.write(self._get_content())
            QMessageBox.information(self, "Saved",
                                    f"Report saved to:\n{fname}")
        except OSError as e:
            QMessageBox.critical(self, "Error",
                                 f"Failed to save:\n{e}")


# ── ExportCenter (main API) ──────────────────────────────────────────

class ExportCenter:
    """Central export utility for SAM Desktop.

    No business logic. No domain access.
    Formats: TXT, Markdown, JSON, CSV.
    """

    def __init__(self, parent: Optional[QWidget] = None):
        if not HAS_QT:
            raise ImportError("PySide6 is required")
        self._parent = parent

    # ── Export methods ───────────────────────────────────────────────

    def export_mission_report(self, mission: Dict) -> None:
        """Export a single mission report."""
        data = [mission]
        self._export("mission-report", data)

    def export_mission_list(self, missions: List[Dict]) -> None:
        """Export list of missions."""
        self._export("missions", missions)

    def export_timeline(self, events: List[Dict]) -> None:
        """Export timeline events."""
        self._export("timeline", events)

    def export_approval(self, approvals: List[Dict]) -> None:
        """Export approval records."""
        self._export("approvals", approvals)

    def export_audit(self, audit_records: List[Dict]) -> None:
        """Export audit records."""
        self._export("audit", audit_records)

    def export_performance(self, perf_data: List[Dict]) -> None:
        """Export performance data."""
        self._export("performance", perf_data)

    # ── Internal ─────────────────────────────────────────────────────

    def _export(self, title: str, data: List[Dict]) -> None:
        """Show the export preview dialog."""
        if not data:
            QMessageBox.information(
                None, "Export", f"No data to export for '{title}'.")
            return

        dialog = ExportPreviewDialog(title, data, self._parent)
        dialog.exec()

    def export_raw(self, title: str, data: List[Dict],
                   parent: Optional[QWidget] = None) -> None:
        """Export arbitrary data w/ parent override."""
        self._parent = parent or self._parent
        self._export(title, data)

    # ── Quick helpers ────────────────────────────────────────────────

    @staticmethod
    def format_as(name: str, data: List[Dict], fmt: str = "md") -> str:
        """Static format without dialog. Returns string."""
        formatter = FORMATTERS.get(fmt, FORMATTERS["md"])
        if fmt in ("txt", "md"):
            return formatter(name, data)
        return formatter(data)

    @staticmethod
    def available_formats() -> List[str]:
        return list(FORMATTERS.keys())
