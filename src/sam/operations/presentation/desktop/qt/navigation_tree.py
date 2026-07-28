"""QtNavigationTree — Navigation tree for the SAM Desktop.

QTreeWidget that consumes NavigationState (Sprint 12) and
DesktopNavigation (Sprint 16, OP-206). No new navigation structure.
"""

from __future__ import annotations

from typing import Optional, List, Callable

try:
    from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem
    from PySide6.QtCore import Qt, Signal
    HAS_QT = True
except ImportError:
    HAS_QT = False
    QTreeWidget = object

from ..navigation import DesktopNavigation, DesktopScreen


class QtNavigationTree:
    """Navigation tree widget.

    Consumes DesktopNavigation model.
    Converts navigation screens into QTreeWidget items.
    No new navigation structure.
    """

    def __init__(self, tree_widget: Optional[QTreeWidget] = None):
        if not HAS_QT:
            raise ImportError("PySide6 is required")

        self._tree = tree_widget or QTreeWidget()
        self._navigation = DesktopNavigation()
        self._on_navigate: Optional[Callable[[str], None]] = None

        # Tree configuration
        self._tree.setHeaderLabel("Navigation")
        self._tree.setIndentation(12)
        self._tree.setAnimated(True)

        # Connect selection
        self._tree.currentItemChanged.connect(self._on_item_changed)

    # ── Build ─────────────────────────────────────────────────────────

    def build(self, navigation: Optional[DesktopNavigation] = None) -> QTreeWidget:
        """Build tree items from DesktopNavigation model."""
        if navigation:
            self._navigation = navigation

        self._tree.clear()

        # Main screens (top-level)
        main_root = QTreeWidgetItem(self._tree, ["Main"])
        for screen in self._navigation.main_screens:
            self._add_screen_item(main_root, screen)

        # System screens (top-level)
        system_root = QTreeWidgetItem(self._tree, ["System"])
        for screen in self._navigation.system_screens:
            self._add_screen_item(system_root, screen)

        self._tree.expandAll()
        return self._tree

    def _add_screen_item(self, parent: QTreeWidgetItem, screen: DesktopScreen) -> None:
        """Add a single screen as a tree item."""
        label = screen.label
        if screen.badge_count > 0:
            label = f"{label} [{screen.badge_count}]"

        item = QTreeWidgetItem(parent, [label])
        item.setData(0, Qt.UserRole, screen.screen_id)

        if screen.icon:
            try:
                from PySide6.QtGui import QIcon
                item.setIcon(0, QIcon(screen.icon))
            except Exception:
                pass

    # ── Selection ─────────────────────────────────────────────────────

    def _on_item_changed(self, current, previous) -> None:
        """Handle tree item selection."""
        if current is None:
            return
        screen_id = current.data(0, Qt.UserRole)
        if screen_id and self._on_navigate:
            self._on_navigate(screen_id)

    def select_screen(self, screen_id: str) -> bool:
        """Programmatically select a screen in the tree."""
        return self._find_and_select(self._tree.invisibleRootItem(), screen_id)

    def _find_and_select(self, parent: QTreeWidgetItem, screen_id: str) -> bool:
        """Recursively find and select a screen item."""
        for i in range(parent.childCount()):
            child = parent.child(i)
            if child.data(0, Qt.UserRole) == screen_id:
                self._tree.setCurrentItem(child)
                return True
            if self._find_and_select(child, screen_id):
                return True
        return False

    # ── Events ────────────────────────────────────────────────────────

    def on_navigate(self, handler: Callable[[str], None]) -> None:
        """Register navigation callback."""
        self._on_navigate = handler

    # ── Update ────────────────────────────────────────────────────────

    def update_badge(self, screen_id: str, count: int) -> None:
        """Update badge count on a screen item without rebuild."""
        self._update_badge_recursive(self._tree.invisibleRootItem(), screen_id, count)

    def _update_badge_recursive(self, parent: QTreeWidgetItem, screen_id: str, count: int) -> bool:
        for i in range(parent.childCount()):
            child = parent.child(i)
            if child.data(0, Qt.UserRole) == screen_id:
                label = child.text(0)
                # Remove existing badge
                if "[" in label and label.endswith("]"):
                    label = label.rsplit("[", 1)[0].strip()
                if count > 0:
                    label = f"{label} [{count}]"
                child.setText(0, label)
                return True
            if self._update_badge_recursive(child, screen_id, count):
                return True
        return False

    # ── Access ────────────────────────────────────────────────────────

    @property
    def widget(self) -> QTreeWidget:
        return self._tree

    @property
    def active_screen_id(self) -> Optional[str]:
        item = self._tree.currentItem()
        if item:
            return item.data(0, Qt.UserRole)
        return None

    def rebuild(self) -> QTreeWidget:
        """Rebuild the tree (call after navigation model changes)."""
        return self.build(self._navigation)
