"""Desktop — Presentation host for the SAM Desktop application.

Desktop is a consumer of Conversation API + DTO + RendererProtocol.
It is NOT a domain layer. No business logic. No storage access.
Desktop is one of many hosts (Console, Desktop, Web, CLI).
All hosts share the same pipeline:

    Conversation API -> DTO -> DashboardComposer -> ConsoleSession -> RendererProtocol

Sprint 16: Desktop Host Foundation.
- Application lifecycle (OP-202)
- Session bridge (OP-204)
- Window model (OP-203)
- Layout model (OP-205)
- Navigation model (OP-206)
- Theme adapter (OP-207)
- Renderer adapter (OP-208)

All modules are models/adapters only. No Qt widget implementations.
"""

from __future__ import annotations

from .application import DesktopApplication, DesktopAppState, DesktopConfig
from .session import DesktopSession
from .main_window import DesktopWindow, MenuItem, ToolbarItem, NotificationArea
from .layout import DesktopLayout, LayoutRegion, RegionPosition
from .navigation import DesktopNavigation, DesktopScreen
from .theme import DesktopThemeAdapter
from .renderer_adapter import DesktopRendererAdapter, WidgetAction

__all__ = [
    "DesktopApplication", "DesktopAppState", "DesktopConfig",
    "DesktopSession",
    "DesktopWindow", "MenuItem", "ToolbarItem", "NotificationArea",
    "DesktopLayout", "LayoutRegion", "RegionPosition",
    "DesktopNavigation", "DesktopScreen",
    "DesktopThemeAdapter",
    "DesktopRendererAdapter", "WidgetAction",
]
