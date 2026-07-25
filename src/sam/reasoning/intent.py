"""
Intent Models – Sprint 22 Fase 1

Defines the formal intent model that serves as input to the
Reasoning Engine. Intents represent natural-language or structured
requests that get translated into Execution Graphs and governed
through the full SAM pipeline.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, ClassVar, Dict, List, Optional, Pattern, Tuple
import re
import uuid

from pydantic import BaseModel, Field, ConfigDict


# ── Intent Type ──────────────────────────────────────────────────────


class IntentType(str, Enum):
    """Categories of intent that SAM can process."""

    DIAGNOSE = "DIAGNOSE"
    """Investigate and report on a target's health/state."""

    REPAIR = "REPAIR"
    """Fix a known issue or failure on a target."""

    OPTIMIZE = "OPTIMIZE"
    """Improve performance, cost, or efficiency of a target."""

    MONITOR = "MONITOR"
    """Set up or adjust monitoring on a target."""

    DEPLOY = "DEPLOY"
    """Deploy a capability, plugin, or configuration."""

    ROLLBACK = "ROLLBACK"
    """Roll back a previous deployment or change."""

    SCALE = "SCALE"
    """Scale a target up or down."""

    CUSTOM = "CUSTOM"
    """User-defined intent without a standard category."""


# ── Intent Status ────────────────────────────────────────────────────


class IntentStatus(str, Enum):
    """Lifecycle states for an Intent."""

    PENDING = "PENDING"
    """Intent received, not yet planned."""

    PLANNING = "PLANNING"
    """Planning engine is generating an execution graph."""

    APPROVED = "APPROVED"
    """Governance has approved the generated graph."""

    EXECUTING = "EXECUTING"
    """Execution graph is running."""

    COMPLETED = "COMPLETED"
    """Execution finished successfully."""

    FAILED = "FAILED"
    """Execution failed (or was rejected/blocked)."""


# ── Intent Model ─────────────────────────────────────────────────────


class Intent(BaseModel):
    """A formal intent — a structured request for SAM to act on a target.

    Intents can be created directly (via API/CLI) or parsed from
    natural language by IntentParser.
    """

    model_config = ConfigDict(extra="forbid")

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique intent identifier",
    )
    type: IntentType = Field(
        default=IntentType.CUSTOM,
        description="Intent category",
    )
    target: str = Field(
        default="",
        description="Target identifier (e.g. 'provider:nvidia', 'workspace:default')",
    )
    description: str = Field(
        default="",
        description="Natural-language description of what the user wants",
    )
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional parameters for planning/execution",
    )
    context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional context from Knowledge Graph or environment",
    )
    correlation_id: str = Field(
        default="",
        description="Business correlation identifier linking this intent to a broader workflow",
    )
    status: IntentStatus = Field(
        default=IntentStatus.PENDING,
        description="Current lifecycle state",
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the intent was created",
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        description="When the intent was last updated",
    )

    def mark_planning(self) -> None:
        """Transition intent to PLANNING state."""
        self.status = IntentStatus.PLANNING
        self.updated_at = datetime.utcnow()

    def mark_approved(self) -> None:
        """Transition intent to APPROVED state."""
        self.status = IntentStatus.APPROVED
        self.updated_at = datetime.utcnow()

    def mark_executing(self) -> None:
        """Transition intent to EXECUTING state."""
        self.status = IntentStatus.EXECUTING
        self.updated_at = datetime.utcnow()

    def mark_completed(self) -> None:
        """Transition intent to COMPLETED state."""
        self.status = IntentStatus.COMPLETED
        self.updated_at = datetime.utcnow()

    def mark_failed(self) -> None:
        """Transition intent to FAILED state."""
        self.status = IntentStatus.FAILED
        self.updated_at = datetime.utcnow()

    def is_terminal(self) -> bool:
        """Return True if the intent is in a terminal state."""
        return self.status in (IntentStatus.COMPLETED, IntentStatus.FAILED)


# ── Intent Parser ────────────────────────────────────────────────────


class IntentParser:
    """Parses natural-language text into structured Intent objects.

    Supports rule-based parsing using keyword patterns. Designed as
    a foundation that can later be augmented with LLM-based parsing.

    Usage::

        parser = IntentParser()
        intent = await parser.parse("diagnose provider nvidia")
    """

    # ── Keyword-to-type mapping ──────────────────────────────────
    _TYPE_KEYWORDS: ClassVar[Dict[str, Tuple[IntentType, int]]] = {
        # (IntentType, priority — higher = matched first)
        "diagnose": (IntentType.DIAGNOSE, 5),
        "diagnostic": (IntentType.DIAGNOSE, 5),
        "check": (IntentType.DIAGNOSE, 2),
        "repair": (IntentType.REPAIR, 5),
        "fix": (IntentType.REPAIR, 4),
        "restore": (IntentType.REPAIR, 3),
        "optimize": (IntentType.OPTIMIZE, 5),
        "optimise": (IntentType.OPTIMIZE, 5),
        "tune": (IntentType.OPTIMIZE, 3),
        "monitor": (IntentType.MONITOR, 5),
        "watch": (IntentType.MONITOR, 3),
        "deploy": (IntentType.DEPLOY, 5),
        "install": (IntentType.DEPLOY, 4),
        "rollback": (IntentType.ROLLBACK, 5),
        "revert": (IntentType.ROLLBACK, 4),
        "undo": (IntentType.ROLLBACK, 2),
        "scale": (IntentType.SCALE, 5),
        "grow": (IntentType.SCALE, 2),
        "shrink": (IntentType.SCALE, 2),
    }

    # ── Target extraction patterns ───────────────────────────────
    _TARGET_PATTERNS: ClassVar[List[Tuple[Pattern[str], str]]] = []

    def __init__(self) -> None:
        if not IntentParser._TARGET_PATTERNS:
            IntentParser._TARGET_PATTERNS = [
                (re.compile(r"provider[:\s]+(\S+)", re.IGNORECASE), "provider"),
                (re.compile(r"workspace[:\s]+(\S+)", re.IGNORECASE), "workspace"),
                (re.compile(r"plugin[:\s]+(\S+)", re.IGNORECASE), "plugin"),
                (re.compile(r"cluster[:\s]+(\S+)", re.IGNORECASE), "cluster"),
                (re.compile(r"service[:\s]+(\S+)", re.IGNORECASE), "service"),
                (re.compile(r"node[:\s]+(\S+)", re.IGNORECASE), "node"),
            ]

    async def parse(self, text: str, context: Optional[Dict[str, Any]] = None) -> Intent:
        """Parse natural-language text into an Intent.

        Args:
            text: The natural-language request text.
            context: Optional additional context (e.g. from Knowledge Graph).

        Returns:
            An ``Intent`` with type, target, and description populated.

        Raises:
            ValueError: If the text is empty or cannot be parsed.
        """
        if not text or not text.strip():
            raise ValueError("Intent text cannot be empty")

        text = text.strip()
        lowered = text.lower()

        # 1. Determine intent type by keyword matching
        intent_type = self._resolve_type(lowered)

        # 2. Extract target
        target = self._extract_target(text)

        # 3. Extract parameters from remaining text
        parameters = self._extract_parameters(text)

        return Intent(
            type=intent_type,
            target=target,
            description=text,
            parameters=parameters,
            context=context or {},
        )

    def _resolve_type(self, lowered: str) -> IntentType:
        """Match keywords to intent type, using word-boundary matching for accuracy."""
        best_type = IntentType.CUSTOM
        best_priority = 0

        for keyword, (itype, priority) in self._TYPE_KEYWORDS.items():
            # Use word-boundary matching so "deploy" doesn't match inside "deployment"
            pattern = re.compile(r'\b' + re.escape(keyword) + r'\b', re.IGNORECASE)
            if pattern.search(lowered) and priority > best_priority:
                best_type = itype
                best_priority = priority

        return best_type

    def _extract_target(self, text: str) -> str:
        """Extract a target identifier from text using known patterns.

        Returns the first match or empty string if no target found.
        """
        for pattern, prefix in self._TARGET_PATTERNS:
            match = pattern.search(text)
            if match:
                return f"{prefix}:{match.group(1)}"
        return ""

    def _extract_parameters(self, text: str) -> Dict[str, Any]:
        """Extract key-value parameters from the intent text.

        Recognises ``key=value`` and ``key: value`` patterns,
        including quoted values with spaces.
        """
        params: Dict[str, Any] = {}

        # key=value style (with optional quoted value)
        for match in re.finditer(
            r"(\w[\w_-]*)\s*=\s*(?:\"([^\"]+)\"|'([^']+)'|(\S+))", text
        ):
            key = match.group(1)
            # Groups: 2 = double-quoted, 3 = single-quoted, 4 = unquoted
            if match.group(2) is not None:
                val = match.group(2)  # double-quoted value (don't coerce)
            elif match.group(3) is not None:
                val = match.group(3)  # single-quoted value (don't coerce)
            else:
                val = self._coerce_value(match.group(4))
            params[key] = val

        return params

    @staticmethod
    def _coerce_value(raw: str) -> Any:
        """Coerce a raw string value to int, bool, or string (no float coercion).

        Floats like "2.0" stay as strings because they typically represent
        versions, not numeric values.
        """
        raw = raw.strip().rstrip(",")

        # Boolean
        if raw.lower() in ("true", "yes", "on"):
            return True
        if raw.lower() in ("false", "no", "off"):
            return False

        # Integer
        try:
            return int(raw)
        except ValueError:
            pass

        return raw
