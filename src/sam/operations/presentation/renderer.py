"""Renderer — Abstract renderer Protocol for all future renderers.

Defines the contract that ConsoleRenderer, DesktopRenderer, and
WebRenderer must implement. NO implementation. Only Protocol.
"""

from __future__ import annotations
from typing import Protocol

from ..summary_builder import OperationalSummary


class Renderer(Protocol):
    """Protocol for all renderers."""

    def render_dashboard(self, view: object) -> None:
        ...

    def render_widget(self, widget_type: str, data: object) -> None:
        ...

    def render_notification(self, notification: object) -> None:
        ...

    def render_summary(self, summary: OperationalSummary) -> None:
        ...

    def render_timeline(self, events: tuple) -> None:
        ...


class ConsoleRenderer(Renderer):
    """Abstract console renderer — no implementation."""

    def render_dashboard(self, view: object) -> None:
        ...

    def render_widget(self, widget_type: str, data: object) -> None:
        ...

    def render_notification(self, notification: object) -> None:
        ...

    def render_summary(self, summary: OperationalSummary) -> None:
        ...

    def render_timeline(self, events: tuple) -> None:
        ...


class DesktopRenderer(Renderer):
    """Abstract desktop renderer — no implementation."""

    def render_dashboard(self, view: object) -> None:
        ...

    def render_widget(self, widget_type: str, data: object) -> None:
        ...

    def render_notification(self, notification: object) -> None:
        ...

    def render_summary(self, summary: OperationalSummary) -> None:
        ...

    def render_timeline(self, events: tuple) -> None:
        ...


class WebRenderer(Renderer):
    """Abstract web renderer — no implementation."""

    def render_dashboard(self, view: object) -> None:
        ...

    def render_widget(self, widget_type: str, data: object) -> None:
        ...

    def render_notification(self, notification: object) -> None:
        ...

    def render_summary(self, summary: OperationalSummary) -> None:
        ...

    def render_timeline(self, events: tuple) -> None:
        ...
