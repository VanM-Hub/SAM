"""
Guardian Event Subscriber Protocol.

Defines the interface for all event subscribers in the Guardian Live Runtime.
Synchronous only. No async, no threading, no network.
"""

from typing import List, Dict, Optional, Any

from .event import GuardianEvent, GuardianEventType


class GuardianEventSubscriber:
    """
    Base class for all event subscribers.

    Subscribers declare which event types they support and
    provide a synchronous handle() method.

    This class intentionally provides default (non-abstract)
    implementations so test code can instantiate subclasses
    that do not override methods.
    """

    def supports(self, event: GuardianEvent) -> bool:
        """
        Check if this subscriber can handle the given event.

        Default implementation returns False; override in concrete
        subscribers to accept events.
        """
        return False

    def handle(self, event: GuardianEvent) -> Optional[Dict[str, Any]]:
        """
        Handle an event synchronously.

        Default implementation does nothing and returns None.
        Override in concrete subscribers to provide handling logic.
        """
        return None

    def get_name(self) -> str:
        """Return the subscriber's name for identification."""
        return self.__class__.__name__

    def supported_types(self) -> List[GuardianEventType]:
        """Return supported event types (override for specific filtering)."""
        return list(GuardianEventType)
