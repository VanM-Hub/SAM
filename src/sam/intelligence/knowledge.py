"""
Knowledge Lookup — Phase 1

Mencari knowledge terkait insiden dari Knowledge Store.
"""

import structlog
from typing import List, Dict, Any, Optional

logger = structlog.get_logger()

# Default knowledge base untuk fallback
DEFAULT_KNOWLEDGE = [
    {
        "id": "k001",
        "fact": "Worker timeouts are often caused by high CPU utilization or network congestion",
        "confidence": 0.85,
        "tags": ["worker", "timeout", "cpu", "network"],
    },
    {
        "id": "k002",
        "fact": "Provider authentication failures commonly occur after credential rotation without updating config",
        "confidence": 0.9,
        "tags": ["provider", "auth", "credential", "rotation"],
    },
    {
        "id": "k003",
        "fact": "Runtime can be safely restarted; session state is persisted to disk",
        "confidence": 0.75,
        "tags": ["runtime", "restart", "session"],
    },
    {
        "id": "k004",
        "fact": "Out of memory errors are typically resolved by increasing memory limit or reducing concurrent workflows",
        "confidence": 0.88,
        "tags": ["memory", "oom", "allocation"],
    },
    {
        "id": "k005",
        "fact": "Database connection pool exhaustion can be mitigated by reducing query timeout and increasing pool size",
        "confidence": 0.82,
        "tags": ["database", "connection", "pool"],
    },
    {
        "id": "k006",
        "fact": "Plugin registration failures often indicate missing dependencies or version mismatch",
        "confidence": 0.78,
        "tags": ["plugin", "register", "dependency"],
    },
]


class KnowledgeLookup:
    """Cari knowledge terkait insiden dari Knowledge Store atau fallback built-in."""

    def __init__(self, knowledge_store: Optional[Any] = None):
        self.knowledge_store = knowledge_store

    async def search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Cari knowledge terkait query.

        Args:
            query: Kata kunci atau deskripsi insiden.
            max_results: Maksimal hasil yang dikembalikan.

        Returns:
            List knowledge entries yang relevan.
        """
        if self.knowledge_store:
            try:
                results = await self.knowledge_store.search(query)
                if results:
                    return results[:max_results]
            except Exception as e:
                logger.warning("knowledge_store_search_failed", error=str(e))

        # Fallback: keyword matching di default knowledge
        return self._search_default(query, max_results)

    def _search_default(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Cari di default knowledge base dengan keyword matching."""
        query_lower = query.lower()
        results = []

        for entry in DEFAULT_KNOWLEDGE:
            # Check if any tag matches
            if any(tag in query_lower for tag in entry["tags"]):
                results.append(dict(entry))
            # Check if any keyword in fact matches
            elif any(word in entry["fact"].lower() for word in query_lower.split()):
                results.append(dict(entry))

            if len(results) >= max_results:
                break

        # If no tag match, return top entries
        if not results:
            results = [dict(entry) for entry in DEFAULT_KNOWLEDGE[:max_results]]

        logger.info(
            "knowledge_search_completed",
            query=query[:50],
            results=len(results),
            source="default" if not self.knowledge_store else "store",
        )
        return results
