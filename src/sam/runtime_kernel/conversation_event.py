"""Conversation Event Bridge — 8 queries."""
from __future__ import annotations
from typing import List
from sam.runtime_kernel.event_bus import EventBus
from sam.runtime_kernel.event_dispatcher import EventDispatcher
from sam.runtime_kernel.event_logger import EventLogger
from sam.runtime_kernel.event_filter import EventFilter


class ConversationEvent:
    def __init__(self, bus: EventBus, dispatcher: EventDispatcher,
                 logger: EventLogger, filter_: EventFilter) -> None:
        self._bus = bus
        self._dispatcher = dispatcher
        self._logger = logger
        self._filter = filter_

    def get_bus(self) -> EventBus:
        return self._bus

    def get_dispatcher(self) -> EventDispatcher:
        return self._dispatcher

    def get_logger(self) -> EventLogger:
        return self._logger

    def get_filter(self) -> EventFilter:
        return self._filter

    def describe_layers(self) -> List[str]:
        return ["bus", "dispatcher", "logger", "filter"]

    def count_layers(self) -> int:
        return 4

    def get_sub_count(self) -> int:
        return self._bus.count_subs()

    def get_event_count(self) -> int:
        return self._bus.count_events()


class DashboardEvent:
    def __init__(self, bus: EventBus, logger: EventLogger) -> None:
        self._bus = bus
        self._logger = logger

    def engine_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        return ExecutionCard(
            title="Event Bus",
            description=f"{self._bus.count_subs()} subs",
            status="ready",
            metrics={"subs": self._bus.count_subs(),
                     "events": self._bus.count_events()},
            items=["bus", "dispatcher"],
        )

    def subscription_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        return ExecutionCard(
            title="Event Subscriptions",
            description=f"{self._bus.count_subs()} subscriptions",
            status="ready",
            metrics={"subs": self._bus.count_subs()},
            items=["subscriptions"],
        )

    def logger_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        return ExecutionCard(
            title="Event Logger",
            description=f"{self._logger.count()} entries",
            status="ready",
            metrics={"entries": self._logger.count()},
            items=["logs"],
        )

    def filter_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        return ExecutionCard(
            title="Event Filter",
            description="Event filtering",
            status="ready",
            metrics={"filters": 3},
            items=["type", "source", "recent"],
        )

    def summary_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        return ExecutionCard(
            title="Event Summary",
            description="Ringkasan event runtime",
            status="ready",
            metrics={"layers": 4, "events": self._bus.count_events()},
            items=["bus", "dispatcher", "logger", "filter"],
        )
