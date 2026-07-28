"""EmbeddedTerminal — SAM command terminal widget.

Provides a SAM> prompt connected to the Console dispatcher.
Supports: history, completion, multiline, colored output.
No bypass to domain. All commands go through ConsoleSession.
"""

from __future__ import annotations

from typing import Optional, List, Callable, Dict
from collections import deque

try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QTextEdit, QLineEdit,
        QHBoxLayout, QLabel, QPushButton, QCompleter,
        QScrollArea, QFrame, QApplication,
    )
    from PySide6.QtCore import Qt, QTimer, QStringListModel
    from PySide6.QtGui import (
        QTextCursor, QColor, QTextCharFormat, QBrush,
        QFont, QKeyEvent, QPalette,
    )
    HAS_QT = True
except ImportError:
    HAS_QT = False


# ── Color scheme ─────────────────────────────────────────────────────

class _TerminalColors:
    """ANSI-like color mapping for terminal output."""
    PROMPT = QColor("#00FF00")       # Green prompt
    COMMAND = QColor("#FFFFFF")       # White command text
    OUTPUT = QColor("#CCCCCC")        # Light gray output
    ERROR = QColor("#FF4444")         # Red error
    WARNING = QColor("#FFAA00")       # Orange warning
    INFO = QColor("#8888FF")          # Blue info
    SUCCESS = QColor("#00CC00")       # Green success
    DEBUG = QColor("#666666")         # Gray debug
    BACKGROUND = QColor("#1E1E1E")    # Dark background
    INPUT_BG = QColor("#2D2D2D")      # Input field background


# ── Terminal history ─────────────────────────────────────────────────

class _TerminalHistory:
    """Navigation history for terminal commands."""

    def __init__(self, max_size: int = 100):
        self._entries: deque = deque(maxlen=max_size)
        self._index = -1
        self._saved_current = ""

    def push(self, command: str) -> None:
        if command.strip():
            self._entries.append(command)
        self._index = len(self._entries)
        self._saved_current = ""

    def prev(self) -> Optional[str]:
        if not self._entries:
            return None
        if self._index > 0:
            self._index -= 1
        return self._entries[self._index] if self._index < len(self._entries) else None

    def next(self) -> Optional[str]:
        if self._index < len(self._entries) - 1:
            self._index += 1
            return self._entries[self._index]
        self._index = len(self._entries)
        return ""

    def peek(self, offset: int = 0) -> Optional[str]:
        idx = self._index + offset
        if 0 <= idx < len(self._entries):
            return self._entries[idx]
        return None

    @property
    def count(self) -> int:
        return len(self._entries)

    def clear(self) -> None:
        self._entries.clear()
        self._index = -1


# ── Terminal Output Widget ───────────────────────────────────────────

class _TerminalOutput(QTextEdit):
    """Read-only terminal output area with colored text."""

    def __init__(self, parent=None):
        if not HAS_QT:
            return
        super().__init__(parent)
        self.setReadOnly(True)
        self.setFont(QFont("Consolas, Courier New, monospace", 10))
        self.setStyleSheet(f"""
            QTextEdit {{
                background-color: {_TerminalColors.BACKGROUND.name()};
                color: {_TerminalColors.OUTPUT.name()};
                border: none;
                padding: 4px;
            }}
        """)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self.setMinimumHeight(150)

    def write_output(self, text: str, color: Optional[QColor] = None) -> None:
        """Write colored text to terminal output."""
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)

        fmt = QTextCharFormat()
        fmt.setForeground(QBrush(color or _TerminalColors.OUTPUT))
        cursor.insertText(text, fmt)

        # Auto-scroll to bottom
        scrollbar = self.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def write_line(self, text: str, color: Optional[QColor] = None) -> None:
        self.write_output(text + "\n", color)

    def write_prompt(self) -> None:
        self.write_output("SAM> ", _TerminalColors.PROMPT)

    def clear_output(self) -> None:
        self.clear()
        self.write_prompt()

    def _color_for_level(self, level: str) -> QColor:
        colors = {
            "error": _TerminalColors.ERROR,
            "warning": _TerminalColors.WARNING,
            "info": _TerminalColors.INFO,
            "success": _TerminalColors.SUCCESS,
            "debug": _TerminalColors.DEBUG,
        }
        return colors.get(level.lower(), _TerminalColors.OUTPUT)


# ── Embedded Terminal Widget ─────────────────────────────────────────

class EmbeddedTerminal(QWidget):
    """SAM command terminal widget.

    Connects to dispatcher via callback. No domain access.
    """

    def __init__(self, parent: Optional[QWidget] = None):
        if not HAS_QT:
            raise ImportError("PySide6 is required")
        super().__init__(parent)

        self._on_command: Optional[Callable[[str], str]] = None
        self._on_autocomplete: Optional[Callable[[str], List[str]]] = None
        self._history = _TerminalHistory()
        self._current_input = ""

        self._build()

    def _build(self) -> None:
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        # Header
        header_layout = QHBoxLayout()
        title = QLabel("<b>Terminal</b>")
        header_layout.addWidget(title)
        header_layout.addStretch()

        clear_btn = QPushButton("Clear")
        clear_btn.setFixedWidth(60)
        clear_btn.clicked.connect(self.clear_terminal)
        header_layout.addWidget(clear_btn)

        layout.addLayout(header_layout)

        # Output area
        self._output = _TerminalOutput()
        layout.addWidget(self._output)

        # Input area
        input_layout = QHBoxLayout()

        prompt_label = QLabel("SAM> ")
        prompt_label.setStyleSheet(f"color: {_TerminalColors.PROMPT.name()}; font-weight: bold;")
        input_layout.addWidget(prompt_label)

        self._input = QLineEdit()
        self._input.setPlaceholderText("Type a command...")
        self._input.setFont(QFont("Consolas, Courier New, monospace", 10))
        self._input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {_TerminalColors.INPUT_BG.name()};
                color: {_TerminalColors.COMMAND.name()};
                border: 1px solid #444444;
                border-radius: 3px;
                padding: 4px 6px;
            }}
        """)
        self._input.returnPressed.connect(self._execute_command)
        self._input.textChanged.connect(self._on_text_changed)

        # Keyboard handling for history
        self._input.installEventFilter(self)

        input_layout.addWidget(self._input)

        layout.addLayout(input_layout)

        # Welcome
        self._output.write_line("SAM Terminal v1.0", _TerminalColors.SUCCESS)
        self._output.write_line("Type 'help' for available commands.", _TerminalColors.INFO)
        self._output.write_prompt()

    # ── Event filter for up/down arrow ───────────────────────────────

    def eventFilter(self, obj, event):
        if obj is self._input and event.type() == event.Type.KeyPress:
            key = event.key()
            if key == Qt.Key.Key_Up:
                cmd = self._history.prev()
                if cmd is not None:
                    self._input.setText(cmd)
                return True
            elif key == Qt.Key.Key_Down:
                cmd = self._history.next()
                self._input.setText(cmd if cmd is not None else "")
                return True
            elif key == Qt.Key.Key_Tab:
                # Autocomplete
                self._handle_tab_complete()
                return True
            elif key == Qt.Key.Key_Escape:
                self._input.clear()
                return True
        return super().eventFilter(obj, event)

    # ── Command handling ─────────────────────────────────────────────

    def _execute_command(self) -> None:
        cmd = self._input.text().strip()
        self._input.clear()

        if not cmd:
            self._output.write_prompt()
            return

        # Echo the command
        self._output.write_line(f"  {cmd}", _TerminalColors.COMMAND)

        # Execute
        if self._on_command:
            try:
                result = self._on_command(cmd)
                if result:
                    self._output.write_line(result, _TerminalColors.OUTPUT)
            except Exception as e:
                self._output.write_line(f"Error: {e}", _TerminalColors.ERROR)
        else:
            self._output.write_line(
                "Terminal not connected to dispatcher.",
                _TerminalColors.WARNING)

        # Store in history
        self._history.push(cmd)
        self._output.write_prompt()

    def _on_text_changed(self, text: str) -> None:
        self._current_input = text

    def _handle_tab_complete(self) -> None:
        text = self._input.text()
        if not self._on_autocomplete or not text:
            return

        suggestions = self._on_autocomplete(text)
        if not suggestions:
            return

        if len(suggestions) == 1:
            self._input.setText(suggestions[0])
        else:
            # Show suggestions in output
            self._output.write_line(
                "  " + "  ".join(suggestions),
                _TerminalColors.DEBUG)
            self._output.write_prompt()
            self._output.write_output(text, _TerminalColors.COMMAND)

    # ── Connection ───────────────────────────────────────────────────

    def on_command(self, handler: Callable[[str], str]) -> None:
        """Set command handler. Returns response text or empty string."""
        self._on_command = handler

    def on_autocomplete(self, handler: Callable[[str], List[str]]) -> None:
        """Set autocomplete handler. Returns list of suggestions."""
        self._on_autocomplete = handler

    # ── Output ───────────────────────────────────────────────────────

    def write(self, text: str, level: str = "info") -> None:
        """Write output from dispatcher."""
        color = self._output._color_for_level(level)
        self._output.write_line(text, color)

    def write_output(self, text: str) -> None:
        self._output.write_line(text, _TerminalColors.OUTPUT)

    def write_error(self, text: str) -> None:
        self._output.write_line(text, _TerminalColors.ERROR)

    def write_info(self, text: str) -> None:
        self._output.write_line(text, _TerminalColors.INFO)

    def write_success(self, text: str) -> None:
        self._output.write_line(text, _TerminalColors.SUCCESS)

    def clear_terminal(self) -> None:
        self._output.clear_output()

    # ── History access ───────────────────────────────────────────────

    @property
    def command_count(self) -> int:
        return self._history.count

    @property
    def is_empty(self) -> bool:
        return self._output.toPlainText().strip() == ""

    def summary(self) -> str:
        return (
            f"EmbeddedTerminal: {self._history.count} commands in history"
        )
