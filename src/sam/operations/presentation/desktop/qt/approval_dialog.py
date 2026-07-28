"""ApprovalDialog — Interactive approval dialog system for SAM Desktop.

Supports: modal dialog, keyboard shortcuts, batch approval, approval reason.
All actions build InteractionCommands. No business logic. No domain access.
"""

from __future__ import annotations

from typing import Optional, List, Dict, Callable

try:
    from PySide6.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QLabel,
        QPushButton, QTextEdit, QCheckBox, QGroupBox,
        QScrollArea, QFrame, QTableWidget, QTableWidgetItem,
        QHeaderView, QMessageBox, QWidget, QSplitter,
        QListWidget, QListWidgetItem, QAbstractItemView,
    )
    from PySide6.QtCore import Qt, QTimer
    from PySide6.QtGui import QKeySequence, QShortcut, QColor, QBrush, QFont
    HAS_QT = True
except ImportError:
    HAS_QT = False


class _ApprovalItemWidget(QWidget):
    """A single approval item card in the list."""

    def __init__(self, approval: Dict, parent=None):
        if not HAS_QT:
            return
        super().__init__(parent)
        self.approval_id = str(approval.get("id", approval.get("approval_id", "?")))
        self._build(approval)

    def _build(self, data: Dict) -> None:
        layout = QHBoxLayout()
        layout.setContentsMargins(4, 4, 4, 4)

        # Checkbox for batch
        self._checkbox = QCheckBox()
        layout.addWidget(self._checkbox)

        # Info
        info_layout = QVBoxLayout()

        title = data.get("title", data.get("description", "Unknown"))
        title_lbl = QLabel(f"<b>{title}</b>")
        info_layout.addWidget(title_lbl)

        detail = data.get("detail", "")
        risk = str(data.get("risk", data.get("impact", "")))
        impact = str(data.get("impact", data.get("effect", "")))
        extra = []
        if detail:
            extra.append(detail)
        if risk:
            extra.append(f"Risk: {risk}")
        if impact:
            extra.append(f"Impact: {impact}")
        if extra:
            detail_lbl = QLabel(" | ".join(extra))
            detail_lbl.setStyleSheet("color: #888888; font-size: 11px;")
            info_layout.addWidget(detail_lbl)

        layout.addLayout(info_layout, 1)

        # Right side: priority badge + confidence
        right_layout = QVBoxLayout()
        priority = str(data.get("priority", data.get("level", "normal"))).lower()
        colors = {"critical": "#FF4444", "high": "#FF8800",
                  "normal": "#00AA00", "low": "#888888"}
        p_color = colors.get(priority, "#888888")
        p_lbl = QLabel(f"<span style='color:{p_color};'>{priority.upper()}</span>")
        right_layout.addWidget(p_lbl)

        confidence = data.get("confidence")
        if confidence is not None:
            c_lbl = QLabel(f"Confidence: {confidence}%")
            c_lbl.setStyleSheet("color: #888888; font-size: 11px;")
            right_layout.addWidget(c_lbl)

        right_layout.addStretch()
        layout.addLayout(right_layout)

        self.setLayout(layout)

    @property
    def is_checked(self) -> bool:
        return self._checkbox.isChecked()

    def set_checked(self, checked: bool) -> None:
        self._checkbox.setChecked(checked)

    def check_state(self) -> bool:
        return self._checkbox.isChecked()


class ApprovalPreviewWidget(QWidget):
    """Preview impact panel for an approval."""

    def __init__(self, parent=None):
        if not HAS_QT:
            return
        super().__init__(parent)
        layout = QVBoxLayout()
        self.setLayout(layout)

        self._evidence = QTextEdit()
        self._evidence.setReadOnly(True)
        self._evidence.setMaximumHeight(200)
        self._evidence.setPlaceholderText("Select an approval to see evidence...")
        layout.addWidget(QLabel("<b>Evidence & Impact Preview:</b>"))
        layout.addWidget(self._evidence)

    def show_approval(self, data: Optional[Dict]) -> None:
        if not data:
            self._evidence.clear()
            self._evidence.setPlaceholderText("Select an approval to see evidence...")
            return

        lines = []
        evidence = data.get("evidence", data.get("details", ""))
        impact = data.get("impact", data.get("effect", ""))
        risk = data.get("risk", data.get("severity", ""))

        if evidence:
            lines.append(f"Evidence:\n{evidence}\n")
        if impact:
            lines.append(f"Impact: {impact}\n")
        if risk:
            lines.append(f"Risk Level: {risk}\n")

        # Command preview
        command_preview = data.get("command", data.get("action_description", ""))
        if command_preview:
            lines.append(f"\nAction: {command_preview}")

        self._evidence.setText("\n".join(lines) if lines else "No preview available.")

    def clear(self) -> None:
        self._evidence.clear()


# ── Main Approval Dialog ─────────────────────────────────────────────

class ApprovalDialog(QDialog):
    """Approval dialog with approve/reject, reason, batch, keyboard.

    Returns InteractionCommand-style result dicts.
    """

    def __init__(self, approvals: List[Dict],
                 parent: Optional[QWidget] = None):
        if not HAS_QT:
            raise ImportError("PySide6 is required")
        super().__init__(parent)

        self._approvals_data = approvals
        self._results: List[Dict] = []

        self.setWindowTitle(f"Approvals ({len(approvals)} pending)")
        self.setMinimumSize(700, 500)

        self._build()
        self._setup_shortcuts()

    def _build(self) -> None:
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Header
        header = QLabel(f"<h2>Pending Approvals</h2>")
        layout.addWidget(header)

        subtitle = QLabel(f"{len(self._approvals_data)} approval(s) requiring review.")
        if subtitle:
            layout.addWidget(subtitle)

        # Splitter: approval list + preview
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Approval list
        list_container = QWidget()
        list_layout = QVBoxLayout()
        list_container.setLayout(list_layout)

        # Batch controls
        batch_layout = QHBoxLayout()
        self._select_all_cb = QCheckBox("Select All")
        self._select_all_cb.toggled.connect(self._on_select_all)
        batch_layout.addWidget(self._select_all_cb)
        batch_layout.addStretch()

        self._batch_approve_btn = QPushButton("Approve Selected")
        self._batch_approve_btn.clicked.connect(
            lambda: self._batch_action("approved"))
        batch_layout.addWidget(self._batch_approve_btn)

        self._batch_reject_btn = QPushButton("Reject Selected")
        self._batch_reject_btn.clicked.connect(
            lambda: self._batch_action("rejected"))
        batch_layout.addWidget(self._batch_reject_btn)

        list_layout.addLayout(batch_layout)

        # Approval cards
        self._approval_widgets: List[_ApprovalItemWidget] = []
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()
        scroll_widget.setLayout(scroll_layout)

        for approval in self._approvals_data:
            card = _ApprovalItemWidget(approval)
            self._approval_widgets.append(card)
            scroll_layout.addWidget(card)

            # Click to show preview
            card.mousePressEvent = lambda e, a=approval: self._show_preview(a)
            card.setCursor(Qt.CursorShape.PointingHandCursor)

            # Separator
            sep = QFrame()
            sep.setFrameShape(QFrame.Shape.HLine)
            scroll_layout.addWidget(sep)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)
        list_layout.addWidget(scroll)

        splitter.addWidget(list_container)

        # Preview panel
        self._preview = ApprovalPreviewWidget()
        splitter.addWidget(self._preview)
        splitter.setSizes([350, 150])

        layout.addWidget(splitter, 1)

        # Reason input
        reason_layout = QHBoxLayout()
        reason_layout.addWidget(QLabel("<b>Reason:</b>"))
        self._reason_input = QTextEdit()
        self._reason_input.setPlaceholderText("Optional reason for approval/rejection...")
        self._reason_input.setMaximumHeight(60)
        reason_layout.addWidget(self._reason_input, 1)
        layout.addLayout(reason_layout)

        # Main action buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self._approve_all_btn = QPushButton("Approve All")
        self._approve_all_btn.clicked.connect(
            lambda: self._batch_action("approved", all_items=True))
        self._approve_all_btn.setStyleSheet(
            "background-color: #00AA00; color: white; padding: 8px 16px;")
        btn_layout.addWidget(self._approve_all_btn)

        self._reject_all_btn = QPushButton("Reject All")
        self._reject_all_btn.clicked.connect(
            lambda: self._batch_action("rejected", all_items=True))
        self._reject_all_btn.setStyleSheet(
            "background-color: #FF4444; color: white; padding: 8px 16px;")
        btn_layout.addWidget(self._reject_all_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)

        # Keyboard shortcut hint
        hint = QLabel(
            "Shortcuts:  <b>A</b>=Approve Selected  "
            "<b>R</b>=Reject Selected  "
            "<b>Ctrl+A</b>=Select All  "
            "<b>Esc</b>=Cancel")
        hint.setStyleSheet("color: #888888; font-size: 11px;")
        layout.addWidget(hint)

    def _setup_shortcuts(self) -> None:
        """Register keyboard shortcuts."""
        QShortcut(QKeySequence("A"), self, lambda: self._batch_action("approved"))
        QShortcut(QKeySequence("R"), self, lambda: self._batch_action("rejected"))
        # Ctrl+A is captured by select_all_cb; don't double-register

    def _on_select_all(self, checked: bool) -> None:
        for w in self._approval_widgets:
            w.set_checked(checked)

    def _show_preview(self, approval: Dict) -> None:
        self._preview.show_approval(approval)

    def _batch_action(self, action: str, all_items: bool = False) -> None:
        """Approve or reject selected/all approvals.

        Args:
            action: "approved" or "rejected"
            all_items: If True, process all approvals regardless of checkbox
        """
        reason = self._reason_input.toPlainText().strip()
        results = []

        for i, approval in enumerate(self._approvals_data):
            widget = self._approval_widgets[i]
            if all_items or widget.is_checked:
                result = {
                    "approval_id": widget.approval_id,
                    "mission_id": approval.get("mission_id", ""),
                    "action": action,
                    "reason": reason,
                    "confidence": approval.get("confidence", 100),
                    "source": "approval_dialog",
                }
                results.append(result)

        if not results:
            QMessageBox.information(
                self, "No Selection",
                "No approvals selected. Select items or use 'Approve All'.")
            return

        self._results = results
        self.accept()

    # ── Results ──────────────────────────────────────────────────────

    @property
    def results(self) -> List[Dict]:
        """Get the approval results.

        Each result dict:
            approval_id: str
            mission_id: str
            action: "approved" | "rejected"
            reason: str
            confidence: int
            source: "approval_dialog"
        """
        return self._results

    @property
    def approved_count(self) -> int:
        return sum(1 for r in self._results if r["action"] == "approved")

    @property
    def rejected_count(self) -> int:
        return sum(1 for r in self._results if r["action"] == "rejected")

    @property
    def has_results(self) -> bool:
        return len(self._results) > 0


# ── Approval Center ──────────────────────────────────────────────────

class ApprovalCenter:
    """Central approval management for SAM Desktop.

    Manages pending approvals and shows the approval dialog.
    No approval logic. No domain access.
    """

    def __init__(self):
        self._pending: List[Dict] = []
        self._history: List[Dict] = []
        self._on_result: Optional[Callable[[List[Dict]], None]] = None

    @property
    def pending_count(self) -> int:
        return len(self._pending)

    @property
    def history(self) -> List[Dict]:
        return list(self._history)

    def add_approval(self, approval: Dict) -> None:
        """Add a pending approval."""
        self._pending.append(approval)

    def add_approvals(self, approvals: List[Dict]) -> None:
        """Add multiple pending approvals."""
        self._pending.extend(approvals)

    def set_pending(self, approvals: List[Dict]) -> None:
        """Replace all pending approvals."""
        self._pending = list(approvals)

    def on_result(self, handler: Callable[[List[Dict]], None]) -> None:
        """Set callback for approval results."""
        self._on_result = handler

    def show_dialog(self, parent: Optional[QWidget] = None) -> List[Dict]:
        """Show the approval dialog.

        Returns results, or empty list if cancelled.
        """
        if not self._pending:
            QMessageBox.information(
                parent, "No Approvals", "No pending approvals.")
            return []

        dialog = ApprovalDialog(self._pending, parent)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            results = dialog.results

            # Move processed to history
            processed_ids = {r["approval_id"] for r in results}
            self._pending = [
                a for a in self._pending
                if str(a.get("id", a.get("approval_id", "?"))) not in processed_ids
            ]
            self._history.extend(results)

            if self._on_result:
                self._on_result(results)

            return results
        return []

    def clear_pending(self) -> None:
        self._pending.clear()

    def clear_history(self) -> None:
        self._history.clear()

    def summary(self) -> str:
        return (
            f"ApprovalCenter: {len(self._pending)} pending, "
            f"{len(self._history)} in history"
        )
