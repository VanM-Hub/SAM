"""Cognitive Manager — Sprint 29 Fase 1-5.

Orchestrates CognitiveStateManager, WorkingMemoryManager,
ContextWindow, and CognitiveSessionManager for unified cognitive runtime.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import structlog

from sam.cognition.state import CognitiveState, CognitiveStateManager
from sam.cognition.memory import WorkingMemoryManager
from sam.cognition.context import ContextWindow, ContextItem
from sam.cognition.session import (
    CognitiveSession,
    CognitiveSessionManager,
    SESSION_ACTIVE,
    SESSION_COMPLETED,
    SESSION_ABANDONED,
)

logger = structlog.get_logger()


class CognitiveManager:
    """Orchestrator for cognitive runtime.

    Provides a unified API over:
      - CognitiveStateManager (state snapshots)
      - WorkingMemoryManager (per-session working memory)
      - ContextWindow (TTL-based context items)
      - CognitiveSessionManager (session lifecycle)
    """

    def __init__(
        self,
        state_manager: Optional[CognitiveStateManager] = None,
        working_memory_manager: Optional[WorkingMemoryManager] = None,
        context_window: Optional[ContextWindow] = None,
        session_manager: Optional[CognitiveSessionManager] = None,
    ) -> None:
        self._state = state_manager or CognitiveStateManager()
        self._memory = working_memory_manager or WorkingMemoryManager()
        self._context = context_window or ContextWindow()
        self._sessions = session_manager or CognitiveSessionManager()
        self.logger = logger.bind(component="CognitiveManager")

    # ── State operations ──────────────────────────────────────────

    async def get_current_state(self) -> CognitiveState:
        """Delegate to CognitiveStateManager."""
        return await self._state.get_current_state()

    async def update_state(self, updates: Dict[str, Any]) -> CognitiveState:
        """Update cognitive state and record the transition."""
        return await self._state.update_state(updates)

    async def get_state_history(self, limit: int = 50) -> List[CognitiveState]:
        """Return recent state transitions."""
        return await self._state.get_state_history(limit=limit)

    async def get_state(self) -> CognitiveState:
        """Alias for get_current_state()."""
        return await self.get_current_state()

    # ── Working Memory operations ─────────────────────────────────

    async def wm_set(
        self,
        key: str,
        value: Any,
        session_id: str = "default",
        ttl: Optional[int] = None,
    ) -> None:
        """Store a value in working memory for the given session."""
        await self._memory.set(key, value, session_id=session_id, ttl=ttl)

    async def wm_get(
        self,
        key: str,
        session_id: str = "default",
    ) -> Optional[Any]:
        """Retrieve a value from working memory."""
        return await self._memory.get(key, session_id=session_id)

    async def wm_delete(self, key: str, session_id: str = "default") -> None:
        """Delete a key from working memory."""
        await self._memory.delete(key, session_id=session_id)

    async def wm_clear(self, session_id: str = "default") -> None:
        """Clear all entries from a session's working memory."""
        await self._memory.clear(session_id=session_id)

    async def wm_snapshot(self, session_id: str = "default") -> Dict[str, Any]:
        """Snapshot of a session's working memory."""
        return await self._memory.snapshot(session_id=session_id)

    async def wm_snapshot_all(self) -> Dict[str, Dict[str, Any]]:
        """Snapshots of all sessions."""
        return await self._memory.snapshot_all()

    async def wm_list_sessions(self) -> List[str]:
        """List all working memory session IDs."""
        return await self._memory.list_sessions()

    # ── Context Window operations ─────────────────────────────────

    async def ctx_set(
        self,
        key: str,
        value: Any,
        importance: float = 0.5,
        ttl: Optional[int] = None,
    ) -> None:
        """Set a context item."""
        await self._context.set(key, value, importance=importance, ttl=ttl)

    async def ctx_get(self, key: str) -> Optional[Any]:
        """Get a context item value."""
        return await self._context.get(key)

    async def ctx_delete(self, key: str) -> None:
        """Delete a context item."""
        await self._context.delete(key)

    async def ctx_list(
        self,
        min_importance: float = 0.0,
    ) -> List[ContextItem]:
        """List context items filtered by importance."""
        return await self._context.list(min_importance=min_importance)

    async def ctx_snapshot(self) -> Dict[str, Any]:
        """Snapshot of all active context items."""
        return await self._context.snapshot()

    async def ctx_prune(self) -> int:
        """Prune expired and low-importance items."""
        return await self._context.prune()

    # ── Session operations ────────────────────────────────────────

    async def start_session(
        self,
        goal_id: Optional[str] = None,
        intent_id: Optional[str] = None,
    ) -> str:
        """Start a new cognitive session with current state and WM snapshot."""
        state = await self.get_current_state()
        wm_snap = await self.wm_snapshot()
        return await self._sessions.start_session(
            goal_id=goal_id,
            intent_id=intent_id,
            state=state,
            working_memory_snapshot=wm_snap,
        )

    async def get_session(self, session_id: str) -> Optional[CognitiveSession]:
        """Get a session by ID."""
        return await self._sessions.get_session(session_id)

    async def end_session(
        self,
        session_id: str,
        status: str = SESSION_COMPLETED,
    ) -> None:
        """End a session."""
        await self._sessions.end_session(session_id, status=status)

    async def get_active_session(self) -> Optional[CognitiveSession]:
        """Get the currently active session."""
        return await self._sessions.get_active_session()

    async def add_reflection_to_session(
        self,
        session_id: str,
        reflection_id: str,
    ) -> None:
        """Link a reflection to a session."""
        await self._sessions.add_reflection(session_id, reflection_id)

    async def add_decision_to_session(
        self,
        session_id: str,
        decision: Dict[str, Any],
    ) -> None:
        """Record a decision in the current session."""
        await self._sessions.add_decision(session_id, decision)

    async def list_sessions(
        self,
        status_filter: Optional[str] = None,
        limit: int = 50,
    ) -> List[CognitiveSession]:
        """List sessions, optionally filtered by status."""
        return await self._sessions.list_sessions(
            status_filter=status_filter,
            limit=limit,
        )

    # ── Combined operations ───────────────────────────────────────

    async def refresh_state_from_working_memory(
        self,
        session_id: str = "default",
    ) -> CognitiveState:
        """Refresh the cognitive state using values stored in working memory.

        Reads known keys like 'health', 'confidence', 'focus', 'risk',
        'autonomy_level', 'learning_objective', 'current_strategy'
        from working memory and applies them as state updates.

        Also syncs relevant values into the context window.
        """
        snapshot = await self.wm_snapshot(session_id)
        updates: Dict[str, Any] = {}

        key_mapping = {
            "health": "health",
            "confidence": "confidence",
            "focus": "focus",
            "risk": "risk",
            "autonomy_level": "autonomy_level",
            "learning_objective": "learning_objective",
            "current_strategy": "current_strategy",
            "current_intent_id": "current_intent_id",
            "current_goal_id": "current_goal_id",
        }

        for wm_key, state_key in key_mapping.items():
            if wm_key in snapshot:
                updates[state_key] = snapshot[wm_key]
                # Sync to context window with moderate importance
                await self._context.set(
                    f"state.{wm_key}",
                    snapshot[wm_key],
                    importance=0.6,
                    ttl=600,
                )

        if not updates:
            return await self.get_current_state()

        return await self.update_state(updates)
