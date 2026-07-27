from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QStackedWidget, QFrame,
    QScrollArea, QProgressBar
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor

from ...experience.models.task import TaskModel, TaskStatus
from ...operations.engine.task import TaskEngine
from ...telemetry.service import TelemetryService


class TaskPage(QWidget):
    """Halaman Task Center untuk Desktop."""

    def __init__(self, telemetry):
        super().__init__()
        self.telemetry = telemetry
        self.task_engine = TaskEngine(telemetry)
        self.current_tasks = []
        self.selected_task = None
        self._init_ui()
        self._start_refresh()

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # Header
        header = QHBoxLayout()
        title = QLabel("\U0001f4cb Tasks")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #e0e0e0;")
        header.addWidget(title)
        header.addStretch()

        refresh_btn = QPushButton("\U0001f504 Refresh")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background: #2a4a6a;
                border: none;
                border-radius: 6px;
                padding: 6px 16px;
                color: #fff;
            }
            QPushButton:hover { background: #3a5a7a; }
        """)
        refresh_btn.clicked.connect(self.refresh)
        header.addWidget(refresh_btn)
        layout.addLayout(header)

        # Split: List + Detail
        split = QHBoxLayout()

        # Left: Task list
        self.task_list = QListWidget()
        self.task_list.setStyleSheet("""
            QListWidget {
                background: #0a0a0f;
                border: 1px solid #2a2a3a;
                border-radius: 8px;
                padding: 4px;
                min-width: 300px;
            }
            QListWidget::item {
                padding: 8px 12px;
                border-bottom: 1px solid #1a1a2a;
                border-radius: 4px;
            }
            QListWidget::item:hover {
                background: #12121a;
            }
            QListWidget::item:selected {
                background: #1a2a3a;
            }
        """)
        self.task_list.itemClicked.connect(self._on_task_selected)
        split.addWidget(self.task_list, 1)

        # Right: Task detail
        self.detail_stack = QStackedWidget()
        self.detail_stack.setStyleSheet(
            "background: #0a0a0f; border: 1px solid #2a2a3a; border-radius: 8px; padding: 12px;"
        )
        self.detail_stack.addWidget(self._create_empty_detail())
        self.detail_stack.addWidget(self._create_task_detail())
        split.addWidget(self.detail_stack, 2)

        layout.addLayout(split)
        self.setLayout(layout)

        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh)
        self.refresh_timer.start(5000)

    def _create_empty_detail(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.addStretch()
        label = QLabel("Select a task to view details")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("color: #888; font-size: 16px;")
        layout.addWidget(label)
        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def _create_task_detail(self):
        widget = QWidget()
        layout = QVBoxLayout()

        self.detail_name = QLabel("Task Name")
        self.detail_name.setStyleSheet("font-size: 18px; font-weight: bold; color: #e0e0e0;")
        layout.addWidget(self.detail_name)

        self.detail_status = QLabel("Status")
        self.detail_status.setStyleSheet("color: #a0a0b0;")
        layout.addWidget(self.detail_status)

        self.detail_progress = QProgressBar()
        self.detail_progress.setStyleSheet("""
            QProgressBar {
                background: #1a1a2a;
                border: none;
                border-radius: 4px;
                height: 12px;
            }
            QProgressBar::chunk {
                background: #2a6a4a;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.detail_progress)

        self.detail_description = QLabel("Description")
        self.detail_description.setWordWrap(True)
        self.detail_description.setStyleSheet("color: #a0a0b0; padding: 4px 0;")
        layout.addWidget(self.detail_description)

        # Steps
        steps_label = QLabel("Steps:")
        steps_label.setStyleSheet("font-weight: bold; color: #c0c0c0; margin-top: 8px;")
        layout.addWidget(steps_label)

        self.detail_steps = QListWidget()
        self.detail_steps.setStyleSheet("""
            QListWidget {
                background: #12121a;
                border: 1px solid #2a2a3a;
                border-radius: 4px;
                max-height: 150px;
            }
        """)
        layout.addWidget(self.detail_steps)

        # Approval
        self.detail_approval = QLabel("")
        self.detail_approval.setStyleSheet("padding: 4px 0;")
        layout.addWidget(self.detail_approval)

        # Actions
        actions = QHBoxLayout()
        self.approve_btn = QPushButton("\u2705 Approve")
        self.approve_btn.setStyleSheet("""
            QPushButton {
                background: #2a6a4a;
                border: none;
                border-radius: 6px;
                padding: 6px 16px;
                color: #fff;
            }
            QPushButton:hover { background: #3a7a5a; }
        """)
        self.approve_btn.clicked.connect(self._on_approve)
        self.approve_btn.setVisible(False)
        actions.addWidget(self.approve_btn)

        self.deny_btn = QPushButton("\u274c Deny")
        self.deny_btn.setStyleSheet("""
            QPushButton {
                background: #6a2a2a;
                border: none;
                border-radius: 6px;
                padding: 6px 16px;
                color: #fff;
            }
            QPushButton:hover { background: #8a3a3a; }
        """)
        self.deny_btn.clicked.connect(self._on_deny)
        self.deny_btn.setVisible(False)
        actions.addWidget(self.deny_btn)
        actions.addStretch()
        layout.addLayout(actions)

        widget.setLayout(layout)
        return widget

    def _start_refresh(self):
        """Mulai refresh pertama."""
        self.refresh()

    def refresh(self):
        """Refresh task list."""
        try:
            self.current_tasks = self.task_engine.get_tasks()
            self._render_list()
            if self.selected_task:
                self._show_task_detail(self.selected_task)
        except Exception:
            pass

    def _render_list(self):
        self.task_list.clear()
        if not self.current_tasks:
            item = QListWidgetItem("No tasks found.")
            item.setForeground(QColor("#888"))
            self.task_list.addItem(item)
            return

        for task in self.current_tasks:
            status_icons = {
                TaskStatus.PENDING: "\u23f3",
                TaskStatus.RUNNING: "\U0001f504",
                TaskStatus.APPROVING: "\U0001f4cb",
                TaskStatus.PAUSED: "\u23f8\ufe0f",
                TaskStatus.COMPLETED: "\u2705",
                TaskStatus.FAILED: "\u274c",
                TaskStatus.CANCELLED: "\U0001f6ab",
            }
            icon = status_icons.get(task.status, "\U0001f4cc")
            text = "{} {} [{}]".format(icon, task.name, task.progress_text)
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, task.id)

            # Colors
            if task.status == TaskStatus.COMPLETED:
                item.setForeground(QColor("#4ae04a"))
            elif task.status == TaskStatus.FAILED:
                item.setForeground(QColor("#e06a6a"))
            elif task.needs_approval:
                item.setForeground(QColor("#e0c06a"))

            self.task_list.addItem(item)

    def _on_task_selected(self, item):
        task_id = item.data(Qt.UserRole)
        for task in self.current_tasks:
            if task.id == task_id:
                self.selected_task = task
                self._show_task_detail(task)
                break

    def _show_task_detail(self, task):
        self.detail_stack.setCurrentIndex(1)
        self.detail_name.setText(task.name)
        self.detail_status.setText("Status: {}".format(task.status.value.upper()))
        self.detail_progress.setValue(int(task.progress))
        self.detail_description.setText(task.description or "No description")

        # Steps
        self.detail_steps.clear()
        for step in task.steps:
            icon = "\u2705" if step.status == TaskStatus.COMPLETED else "\u23f3"
            self.detail_steps.addItem("{} {}".format(icon, step.name))

        # Approval
        if task.needs_approval:
            self.detail_approval.setText("\u26a0\ufe0f Approval required!")
            self.detail_approval.setStyleSheet("color: #e0c06a; padding: 4px 0;")
            self.approve_btn.setVisible(True)
            self.deny_btn.setVisible(True)
        else:
            self.detail_approval.setText("No approval required")
            self.detail_approval.setStyleSheet("color: #4ae04a; padding: 4px 0;")
            self.approve_btn.setVisible(False)
            self.deny_btn.setVisible(False)

    def _on_approve(self):
        if self.selected_task:
            # TODO: connect to ApprovalManager
            self.refresh()

    def _on_deny(self):
        if self.selected_task:
            # TODO: connect to ApprovalManager
            self.refresh()
