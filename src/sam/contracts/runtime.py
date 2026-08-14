"""
Runtime State Enum — compatibility shim.

Canonical definition lives in ``sam.runtime.state``.
This module re-exports it so that ``from sam.contracts import RuntimeState``
remains a valid compatibility surface without introducing a second definition.
"""

from sam.runtime.state import RuntimeState

__all__ = ["RuntimeState"]
