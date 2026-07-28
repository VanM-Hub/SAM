"""LogViewerWidget — Log viewer for the SAM Desktop.

Support: follow, pause, search, regex, level filter, copy, save, jump.
No file I/O — data from DTO via bridge pipeline.
"""

from __future__ import annotations

import re
from typing import Optional, List, Callable, Dict

try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel,
        QPushButton, QLineEdit, QTextEdit, QComboBox,
        QCheckBox, QFileDialog, QFrame, QScrollBar,
    )
    from PySide6.QtCore import Qt, QTimer
    from PySide6.QtGui import QTextCursor, QColor, QTextCharFormat, QFont
    HAS_QT = True
except ImportError:
    HAS_QT = False


class LogViewerWidget:
    """Log viewer with follow, pause, search (regex), level filter,
    copy, save, and jump-to-line.

    Data from DTO via bridge. No log file reading.
    """

    LEVEL_COLORS = {
        "CRITICAL": "#FF0000",
        "ERROR": "#FF4444",
        "WARNING": "#FFAA00",
        "INFO": "#00AA00",
        "DEBUG": "#888888",
        "TRACE": "#555555",
    }

    def __init__(self, parent: Optional[QWidget] = None):
        if not HAS_QT:
            raise ImportError("PySide6 is required")

        self._parent = parent
        self._container: Optional[QWidget] = None
        self._text_edit: Optional[QTextEdit] = None

        # Controls
        self._search_input: Optional[QLineEdit] = None
        self._level_filter: Optional[QComboBox] = None
        self._regex_check: Optional[QCheckBox] = None
        self._follow_btn: Optional[QPushButton] = None
        self._line_count_lbl: Optional[QLabel] = None

        # State
        self._follow = True
        self._paused = False
        self._log_lines: List[str] = []
        self._max_lines = 5000
        self._line_number = 0

        # Auto-scroll timer
        self._scroll_timer: Optional[QTimer] = None

    def build(self) -> QWidget:
        """Build the log viewer widget."""
        container = QWidget()
        layout = QVBoxLayout()
        container.setLayout(layout)

        # ── Toolbar ──────────────────────────────────────────────
        toolbar = QHBoxLayout()

        # Search
        search_label = QLabel("Search:")
        toolbar.addWidget(search_label)
        search = QLineEdit()
        search.setPlaceholderText("Search logs (regex supported)...")
        search.textChanged.connect(self._on_search)
        search.returnPressed.connect(self._on_search_next)
        toolbar.addWidget(search)
        self._search_input = search

        # Regex toggle
        regex_cb = QCheckBox("Regex")
        regex_cb.toggled.connect(self._on_search)
        toolbar.addWidget(regex_cb)
        self._regex_check = regex_cb

        # Level filter
        level_cb = QComboBox()
        level_cb.addItems(["ALL", "CRITICAL", "ERROR", "WARNING",
                           "INFO", "DEBUG"])
        level_cb.currentTextChanged.connect(self._on_level_changed)
        toolbar.addWidget(level_cb)
        self._level_filter = level_cb

        toolbar.addStretch()

        # Line count
        line_lbl = QLabel("0 lines")
        toolbar.addWidget(line_lbl)
        self._line_count_lbl = line_lbl

        layout.addLayout(toolbar)

        # ── Toolbar 2 ────────────────────────────────────────────
        toolbar2 = QHBoxLayout()

        follow_btn = QPushButton("Follow")
        follow_btn.setCheckable(True)
        follow_btn.setChecked(True)
        follow_btn.toggled.connect(lambda c: follow_btn.setText(
            "Paused" if not c else "Follow"))
        follow_btn.toggled.connect(self._on_follow_toggled)
        toolbar2.addWidget(follow_btn)
        self._follow_btn = follow_btn

        copy_btn = QPushButton("Copy All")
        copy_btn.clicked.connect(self._copy_all)
        toolbar2.addWidget(copy_btn)

        save_btn = QPushButton("Save...")
        save_btn.clicked.connect(self._save_to_file)
        toolbar2.addWidget(save_btn)

        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear)
        toolbar2.addWidget(clear_btn)

        jump_btn = QPushButton("Jump to...")
        jump_btn.clicked.connect(self._jump_to_line)
        toolbar2.addWidget(jump_btn)

        toolbar2.addStretch()
        layout.addLayout(toolbar2)

        # ── Log text area ────────────────────────────────────────
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setFont(QFont("Consolas", 9))
        text_edit.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self._text_edit = text_edit
        layout.addWidget(text_edit)

        if self._parent:
            self._parent.layout().addWidget(container)

        self._container = container
        return container

    # ── Data ─────────────────────────────────────────────────────────

    def append_log(self, level: str, message: str, source: str = "",
                   timestamp: str = "") -> None:
        """Append a single log line."""
        ts = timestamp or ""
        line = f"{ts} [{level:8}] {source} {message}".strip()

        # Apply level filter
        level_filter = self._level_filter.currentText() if self._level_filter else "ALL"
        if level_filter != "ALL" and level.upper() != level_filter:
            return

        self._log_lines.append(line)
        self._line_number += 1

        # Apply search filter
        search = self._search_input.text() if self._search_input else ""
        if search:
            use_regex = self._regex_check.isChecked() if self._regex_check else False
            if use_regex:
                try:
                    if not re.search(search, line, re.IGNORECASE):
                        return
                except re.error:
                    pass
            elif search.lower() not in line.lower():
                return

        # Add to text edit with color
        self._append_colored_line(line, level)

        # Truncate
        if len(self._log_lines) > self._max_lines:
            self._log_lines = self._log_lines[-self._max_lines:]

        # Update count
        if self._line_count_lbl:
            self._line_count_lbl.setText(f"{len(self._log_lines)} lines")

    def set_logs(self, logs: List[Dict]) -> None:
        """Set log data from DTO.

        Args:
            logs: List of dicts with keys:
                level (str), message (str), source (str), timestamp (str)
        """
        self.clear()
        for log in logs:
            self.append_log(
                level=str(log.get("level", "INFO")),
                message=str(log.get("message", "")),
                source=str(log.get("source", "")),
                timestamp=str(log.get("timestamp", ""))[:19],
            )

    def _append_colored_line(self, line: str, level: str) -> None:
        if not self._text_edit:
            return
        color = self.LEVEL_COLORS.get(level.upper(), "#FFFFFF")
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))

        cursor = self._text_edit.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(line + "\n", fmt)

        if self._follow and not self._paused:
            self._scroll_to_bottom()

    def _scroll_to_bottom(self) -> None:
        if self._text_edit:
            bar = self._text_edit.verticalScrollBar()
            if bar:
                bar.setValue(bar.maximum())

    # ── Filter / Search ──────────────────────────────────────────────

    def _on_search(self) -> None:
        if not self._text_edit:
            return
        search = self._search_input.text() if self._search_input else ""
        if not search:
            self._clear_highlight()
            return

        use_regex = self._regex_check.isChecked() if self._regex_check else False
        self._highlight_search(search, use_regex)

    def _on_search_next(self) -> None:
        """Find next match."""
        search = self._search_input.text() if self._search_input else ""
        if not search or not self._text_edit:
            return

        flags = QTextDocument.FindFlag(0)
        if self._regex_check and self._regex_check.isChecked():
            pass  # QTextEdit doesn't directly support regex find
        else:
            flags |= QTextDocument.FindFlag(0)

        found = self._text_edit.find(search)
        if not found:
            # Wrap to start
            cursor = self._text_edit.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            self._text_edit.setTextCursor(cursor)
            self._text_edit.find(search)

    def _on_level_changed(self, level: str) -> None:
        pass  # Filter applied on append

    def _on_follow_toggled(self, following: bool) -> None:
        self._follow = following
        if following:
            self._scroll_to_bottom()

    # ── Actions ─────────────────────────────────────────────────────

    def _copy_all(self) -> None:
        if not self._text_edit:
            return
        from PySide6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(self._text_edit.toPlainText())

    def _save_to_file(self) -> None:
        if not self._text_edit:
            return
        path, _ = QFileDialog.getSaveFileName(
            None, "Save Log", "sam_log.txt",
            "Text Files (*.txt);;All Files (*)")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self._text_edit.toPlainText())

    def _jump_to_line(self) -> None:
        """Jump to a specific line number."""
        if not self._text_edit:
            return

        from PySide6.QtWidgets import QInputDialog
        line_num, ok = QInputDialog.getInt(
            None, "Jump to Line", "Line number:",
            1, 1, max(1, len(self._log_lines)))
        if ok:
            cursor = self._text_edit.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Start)

            # Block-based navigation
            doc = self._text_edit.document()
            block = doc.findBlockByLineNumber(max(0, line_num - 1))
            if block.isValid():
                cursor.setPosition(block.position())
                self._text_edit.setTextCursor(cursor)
                self._text_edit.centerCursor()

    def clear(self) -> None:
        self._log_lines.clear()
        self._line_number = 0
        if self._text_edit:
            self._text_edit.clear()
        if self._line_count_lbl:
            self._line_count_lbl.setText("0 lines")

    # ── Search highlight ─────────────────────────────────────────────

    def _highlight_search(self, text: str, use_regex: bool = False) -> None:
        if not self._text_edit:
            return

        self._clear_highlight()

        cursor = self._text_edit.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)

        fmt = QTextCharFormat()
        fmt.setBackground(QColor("#FFFF00"))
        fmt.setForeground(QColor("#000000"))

        if not text:
            return

        doc = self._text_edit.document()
        if use_regex:
            try:
                pattern = re.compile(text, re.IGNORECASE)
            except re.error:
                return
            full_text = doc.toPlainText()
            for match in pattern.finditer(full_text):
                c = self._text_edit.textCursor()
                c.setPosition(match.start())
                c.setPosition(match.end(), QTextCursor.MoveMode.KeepAnchor)
                c.setCharFormat(fmt)
        else:
            find_flags = QTextDocument.FindFlag(0)
            while True:
                found = doc.find(text, cursor.position(), find_flags)
                if found.isNull():
                    break
                extra_selection = QTextEdit.ExtraSelection()
                extra_selection.format = fmt
                extra_selection.cursor = found
                self._text_edit.setExtraSelections(
                    self._text_edit.extraSelections() + [extra_selection]
                )
                cursor.setPosition(found.position())

    def _clear_highlight(self) -> None:
        if self._text_edit:
            self._text_edit.setExtraSelections([])

    # ── Access ───────────────────────────────────────────────────────

    @property
    def widget(self) -> Optional[QWidget]:
        return self._container

    @property
    def line_count(self) -> int:
        return len(self._log_lines)

    @property
    def is_following(self) -> bool:
        return self._follow

    def set_follow(self, follow: bool) -> None:
        self._follow = follow
        if self._follow_btn:
            self._follow_btn.setChecked(follow)

    def summary(self) -> str:
        return (
            f"LogViewerWidget: {len(self._log_lines)} lines, "
            f"{'following' if self._follow else 'paused'}"
        )
