"""
Presentation Layer — SAM Console reference implementation.

Sprint 12: Foundation (ViewModels, Composer, Widgets, Navigation, Theme, Renderer Protocol, Refresh, Interaction)
Sprint 13: Implementation (ConsoleRenderer, RichAdapter, WidgetRenderer, NavigationRuntime, Dispatcher, LiveRefresh, ConsoleSession, ThemeRuntime, ConsoleIntegration)
"""

from __future__ import annotations

from .console_view import ConsoleView, HeaderView, SidebarView, BodyView, StatusBarView, FooterView
from .dashboard_composer import ConsoleDashboard, DashboardComposer
from .widgets import (
    MissionWidget, MissionWidgetCollection,
    ApprovalWidget, ApprovalWidgetCollection,
    NotificationWidget, NotificationWidgetCollection,
    TimelineEvent, TimelineWidgetCollection,
    TrustWidget, HealthWidget, WorkspaceWidget,
    SchedulerWidget, SummaryWidget,
    WidgetRegistry,
)
from .navigation import NavigationState, NavigationItem, NavigationSection, Breadcrumb
from .theme import Theme, DarkTheme, LightTheme, CompactTheme
from .renderer import Renderer, ConsoleRenderer as AbstractConsoleRenderer
from .refresh import RefreshController, RefreshMode, RefreshState
from .interaction import (
    ApproveMission, RejectMission, CancelMission, ResumeMission,
    ExecuteRecommendation, SimulateRecommendation,
    OpenMission, OpenTimeline, OpenEvidence,
    RefreshDashboard, UserQuery,
)

# Sprint 13 — Implementation
from .rich_adapter import has_rich, create_console, styled_text, plain_table, separator, boxed
from .console_renderer import ConsoleRenderer
from .widget_renderer import WidgetRenderer
from .navigation_runtime import NavigationRuntime, NavigationMenu
from .dispatcher import CommandDispatcher, CommandResult, CommandHistory
from .live_refresh import LiveRefresh, RefreshCallback
from .console_session import ConsoleSession
from .theme_runtime import ThemeRuntime
from .console_integration import ConsoleIntegration

__all__ = [
    # Sprint 12
    "ConsoleView", "HeaderView", "SidebarView", "BodyView", "StatusBarView", "FooterView",
    "ConsoleDashboard", "DashboardComposer",
    "MissionWidget", "MissionWidgetCollection",
    "ApprovalWidget", "ApprovalWidgetCollection",
    "NotificationWidget", "NotificationWidgetCollection",
    "TimelineEvent", "TimelineWidgetCollection",
    "TrustWidget", "HealthWidget", "WorkspaceWidget", "SchedulerWidget", "SummaryWidget",
    "WidgetRegistry",
    "NavigationState", "NavigationItem", "NavigationSection", "Breadcrumb",
    "Theme", "DarkTheme", "LightTheme", "CompactTheme",
    "Renderer", "AbstractConsoleRenderer",
    "RefreshController", "RefreshMode", "RefreshState",
    "ApproveMission", "RejectMission", "CancelMission", "ResumeMission",
    "ExecuteRecommendation", "SimulateRecommendation",
    "OpenMission", "OpenTimeline", "OpenEvidence",
    "RefreshDashboard", "UserQuery",
    # Sprint 13
    "has_rich", "create_console", "styled_text", "plain_table", "separator", "boxed",
    "ConsoleRenderer",
    "WidgetRenderer",
    "NavigationRuntime", "NavigationMenu",
    "CommandDispatcher", "CommandResult", "CommandHistory",
    "LiveRefresh", "RefreshCallback",
    "ConsoleSession",
    "ThemeRuntime",
    "ConsoleIntegration",
]
