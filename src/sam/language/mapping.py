"""
Internal → Human term mapping.
Semua UI harus menggunakan human terms.
"""

INTERNAL_TO_HUMAN = {
    # Runtime
    "runtime": "SAM",
    "guardian": "protection",

    # Workflow
    "workflow": "task",
    "execution_graph": "plan",
    "planner": "planning",

    # Capabilities
    "capability": "skill",

    # Knowledge & Memory
    "knowledge_search": "looking for information",
    "knowledge_loaded": "knowledge ready",
    "memory_retrieval": "looking at history",
    "memory_stored": "remembered",

    # Reasoning
    "reasoning": "thinking",
    "thinking": "thinking",

    # Governance
    "policy": "rules",
    "approval": "permission",

    # Incidents
    "incident": "problem",
    "recommendation": "suggested action",
    "evidence": "findings",
    "mission": "goal",

    # Status
    "healthy": "healthy",
    "degraded": "needs attention",
    "unhealthy": "unhealthy",
    "recovering": "recovering",
    "idle": "idle",
    "busy": "busy",
    "learning": "learning",
}


def humanize(term: str) -> str:
    """Convert internal term to human-friendly term."""
    return INTERNAL_TO_HUMAN.get(term, term)


def humanize_event_message(message: str) -> str:
    """Convert event message to human-friendly."""
    msg = message
    for internal, human in INTERNAL_TO_HUMAN.items():
        if internal in msg.lower():
            msg = msg.replace(internal, human)
    return msg
