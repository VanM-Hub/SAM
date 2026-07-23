"""Async Knowledge Graph - manages relationships between knowledge facts using aiosqlite.

This module provides a safe, single-connection aiosqlite-backed implementation
that avoids repeatedly creating/destroying connections which on Windows can
raise "RuntimeError: threads can only be started once" when the Python
threading implementation disallows starting new internal threads rapidly.

The implementation keeps one aiosqlite.Connection per KnowledgeGraph instance
(created lazily) and reuses it for all operations. Callers should ensure the
KnowledgeGraph instance remains alive for the duration of use and call close()
when done to gracefully shut down the background thread.
"""

from __future__ import annotations

import json
import structlog
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4

import aiosqlite

from .models import KnowledgeRelationship, KnowledgeFact


logger = structlog.get_logger()


class KnowledgeGraph:
    """Async manager for relationships between knowledge facts.

    Uses aiosqlite for async DB access. Assumes table knowledge_relationships exists
    and that the 'knowledge' table exists for join queries.
    """

    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self.logger = logger.bind(component="KnowledgeGraph")
        # Hold a single aiosqlite connection for the lifetime of this object.
        # Reusing one connection avoids repeatedly starting background threads
        # which on some Windows/python combinations can hit "threads can only be
        # started once" when connections are created/destroyed rapidly.
        self._conn: Optional[aiosqlite.Connection] = None

    async def _ensure_connection(self) -> aiosqlite.Connection:
        if self._conn is None:
            self._conn = await aiosqlite.connect(self.db_path, check_same_thread=False)
            self._conn.row_factory = aiosqlite.Row
        return self._conn

    async def add_relationship(
        self,
        source_id: UUID,
        target_id: UUID,
        rel_type: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> UUID:
        rel_id = uuid4()
        now = datetime.utcnow().isoformat()

        conn = await self._ensure_connection()
        await conn.execute(
            """
            INSERT INTO knowledge_relationships (id, source_id, target_id, relationship_type, metadata, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                str(rel_id),
                str(source_id),
                str(target_id),
                rel_type,
                json.dumps(metadata or {}),
                now,
            ),
        )
        await conn.commit()

        self.logger.info(
            "Relationship added",
            relationship_id=str(rel_id),
            source_id=str(source_id),
            target_id=str(target_id),
            type=rel_type,
        )
        return rel_id

    async def get_relationships(
        self,
        source_id: Optional[UUID] = None,
        target_id: Optional[UUID] = None,
        rel_type: Optional[str] = None,
    ) -> List[KnowledgeRelationship]:
        conditions = []
        params = []

        if source_id:
            conditions.append("source_id = ?")
            params.append(str(source_id))
        if target_id:
            conditions.append("target_id = ?")
            params.append(str(target_id))
        if rel_type:
            conditions.append("relationship_type = ?")
            params.append(rel_type)

        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        query = f"SELECT * FROM knowledge_relationships {where_clause} ORDER BY created_at DESC"

        conn = await self._ensure_connection()
        cursor = await conn.execute(query, params)
        rows = await cursor.fetchall()

        relationships: List[KnowledgeRelationship] = []
        for row in rows:
            relationships.append(
                KnowledgeRelationship(
                    id=UUID(row["id"]),
                    source_id=UUID(row["source_id"]),
                    target_id=UUID(row["target_id"]),
                    relationship_type=row["relationship_type"],
                    metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                    created_at=datetime.fromisoformat(row["created_at"]),
                )
            )
        return relationships

    async def get_related(
        self,
        knowledge_id: UUID,
        rel_type: Optional[str] = None,
        direction: str = "both",
    ) -> List[KnowledgeFact]:
        conditions = []
        params = []

        if direction in ("outgoing", "both"):
            conditions.append("source_id = ?")
            params.append(str(knowledge_id))
        if direction in ("incoming", "both"):
            conditions.append("target_id = ?")
            params.append(str(knowledge_id))

        if rel_type:
            conditions.append("relationship_type = ?")
            params.append(rel_type)

        # For multiple conditions we combine with OR because we want rows where any relation
        where_clause = "WHERE " + " OR ".join(f"({c})" for c in conditions) if conditions else "WHERE 1=0"

        query = f"SELECT * FROM knowledge_relationships {where_clause}"

        conn = await self._ensure_connection()
        cursor = await conn.execute(query, params)
        rows = await cursor.fetchall()

        related_ids = set()
        for row in rows:
            sid = row["source_id"]
            tid = row["target_id"]
            if sid != str(knowledge_id):
                related_ids.add(sid)
            if tid != str(knowledge_id):
                related_ids.add(tid)

        if not related_ids:
            return []

        placeholders = ",".join("?" * len(related_ids))
        fact_query = f"SELECT * FROM knowledge WHERE id IN ({placeholders})"

        conn = await self._ensure_connection()
        try:
            cursor = await conn.execute(fact_query, [rid for rid in related_ids])
            rows = await cursor.fetchall()
        except Exception:
            # knowledge table might not exist yet
            return []

        facts: List[KnowledgeFact] = []
        for row in rows:
            facts.append(
                KnowledgeFact(
                    id=UUID(row["id"]),
                    document_id=UUID(row["document_id"]),
                    statement=row["statement"],
                    category=row["category"],
                    confidence=row["confidence"],
                    metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                    created_at=datetime.fromisoformat(row["created_at"]),
                    version=row["version"],
                )
            )
        return facts

    async def delete_relationship(self, relationship_id: UUID) -> None:
        conn = await self._ensure_connection()
        await conn.execute(
            "DELETE FROM knowledge_relationships WHERE id = ?",
            (str(relationship_id),),
        )
        await conn.commit()

        self.logger.info("Relationship deleted", relationship_id=str(relationship_id))

    async def get_relationship_by_id(self, relationship_id: UUID) -> Optional[KnowledgeRelationship]:
        conn = await self._ensure_connection()
        cursor = await conn.execute(
            "SELECT * FROM knowledge_relationships WHERE id = ?",
            (str(relationship_id),),
        )
        row = await cursor.fetchone()

        if not row:
            return None

        return KnowledgeRelationship(
            id=UUID(row["id"]),
            source_id=UUID(row["source_id"]),
            target_id=UUID(row["target_id"]),
            relationship_type=row["relationship_type"],
            metadata=json.loads(row["metadata"]) if row["metadata"] else {},
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    async def query(
        self,
        source_id: Optional[UUID] = None,
        target_id: Optional[UUID] = None,
        rel_type: Optional[str] = None,
        metadata_filter: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[KnowledgeRelationship]:
        """Query relationships with optional filters.

        Args:
            source_id: Filter by source fact UUID
            target_id: Filter by target fact UUID
            rel_type: Filter by relationship type
            metadata_filter: Filter by metadata key-value pairs (JSON containment)
            limit: Maximum number of results
            offset: Pagination offset

        Returns:
            List of matching KnowledgeRelationship objects
        """
        conditions = []
        params = []

        if source_id:
            conditions.append("source_id = ?")
            params.append(str(source_id))
        if target_id:
            conditions.append("target_id = ?")
            params.append(str(target_id))
        if rel_type:
            conditions.append("relationship_type = ?")
            params.append(rel_type)
        if metadata_filter:
            # SQLite JSON1 extension: json_extract for each key
            for key, value in metadata_filter.items():
                if isinstance(value, str):
                    conditions.append(f"json_extract(metadata, '$.{key}') = ?")
                    params.append(value)
                else:
                    conditions.append(f"json_extract(metadata, '$.{key}') = ?")
                    params.append(json.dumps(value))

        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        query = f"SELECT * FROM knowledge_relationships {where_clause} ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        conn = await self._ensure_connection()
        cursor = await conn.execute(query, params)
        rows = await cursor.fetchall()

        relationships: List[KnowledgeRelationship] = []
        for row in rows:
            relationships.append(
                KnowledgeRelationship(
                    id=UUID(row["id"]),
                    source_id=UUID(row["source_id"]),
                    target_id=UUID(row["target_id"]),
                    relationship_type=row["relationship_type"],
                    metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                    created_at=datetime.fromisoformat(row["created_at"]),
                )
            )
        return relationships

    async def search_relationships(
        self,
        query_text: str,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """Semantic-like search: find relationships where source/target fact statements
        or metadata contain the query text.

        This performs a simple text search on:
        - knowledge_relationships.metadata
        - knowledge.statement (joined via source_id and target_id)
        - knowledge.metadata (joined via source_id and target_id)

        Args:
            query_text: Text to search for
            limit: Maximum number of results

        Returns:
            List of dicts with relationship, source_fact, target_fact
        """
        search_pattern = f"%{query_text}%"
        
        conn = await self._ensure_connection()
        try:
            # Search in relationship metadata
            cursor = await conn.execute(
                """
                SELECT kr.*, k1.statement as source_statement, k1.category as source_category,
                       k2.statement as target_statement, k2.category as target_category
                FROM knowledge_relationships kr
                LEFT JOIN knowledge k1 ON kr.source_id = k1.id
                LEFT JOIN knowledge k2 ON kr.target_id = k2.id
                WHERE kr.metadata LIKE ?
                   OR k1.statement LIKE ?
                   OR k1.metadata LIKE ?
                   OR k2.statement LIKE ?
                   OR k2.metadata LIKE ?
                ORDER BY kr.created_at DESC
                LIMIT ?
                """,
                [search_pattern] * 5 + [limit],
            )
            rows = await cursor.fetchall()
        except Exception:
            # Tables might not exist
            return []

        results = []
        for row in rows:
            results.append({
                "relationship": KnowledgeRelationship(
                    id=UUID(row["id"]),
                    source_id=UUID(row["source_id"]),
                    target_id=UUID(row["target_id"]),
                    relationship_type=row["relationship_type"],
                    metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                    created_at=datetime.fromisoformat(row["created_at"]),
                ),
                "source_fact": {
                    "id": str(row["source_id"]),
                    "statement": row["source_statement"],
                    "category": row["source_category"],
                } if row["source_statement"] else None,
                "target_fact": {
                    "id": str(row["target_id"]),
                    "statement": row["target_statement"],
                    "category": row["target_category"],
                } if row["target_statement"] else None,
            })
        return results

    async def search_fts(
        self,
        query_text: str,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """Full-text search using FTS5 virtual table.

        Uses the knowledge_fts virtual table for fast, ranked text search.
        Returns matching facts with their relevance ranking.

        Args:
            query_text: Text to search for (supports FTS5 query syntax)
            limit: Maximum number of results

        Returns:
            List of dicts with knowledge fact, statement, category, metadata, and rank
        """
        conn = await self._ensure_connection()
        try:
            # FTS virtual table may not expose an 'id' column; join back to the
            # main knowledge table using rowid to retrieve the authoritative id
            # and other fields. This is robust regardless of how the FTS table
            # was created (with or without explicit id column).
            cursor = await conn.execute(
                """
                SELECT k.id as knowledge_id, k.statement, k.category, k.metadata
                FROM knowledge_fts
                JOIN knowledge k ON knowledge_fts.rowid = k.rowid
                WHERE knowledge_fts MATCH ?
                LIMIT ?
                """,
                (query_text, limit),
            )
            rows = await cursor.fetchall()
        except Exception as e:
            # FTS table might not exist or query failed
            self.logger.debug("FTS search failed", error=str(e))
            return []

        results = []
        for row in rows:
            results.append({
                "knowledge_id": str(row["knowledge_id"]),
                "statement": row["statement"],
                "category": row["category"],
                "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
                # rank not available here via simple SELECT; keep as 0.0 for now
                "rank": 0.0,
            })
        return results

    async def get_graph_stats(self) -> Dict[str, Any]:
        conn = await self._ensure_connection()
        cursor = await conn.execute("SELECT COUNT(*) as count FROM knowledge_relationships")
        rel_row = await cursor.fetchone()
        rel_count = rel_row["count"] if rel_row else 0

        cursor = await conn.execute(
            "SELECT relationship_type, COUNT(*) as count FROM knowledge_relationships GROUP BY relationship_type"
        )
        rows = await cursor.fetchall()
        type_counts = {row["relationship_type"]: row["count"] for row in rows}

        fact_count = 0
        try:
            cursor = await conn.execute("SELECT COUNT(*) as count FROM knowledge")
            fact_row = await cursor.fetchone()
            fact_count = fact_row["count"] if fact_row else 0
        except Exception:
            # knowledge table might not exist yet
            pass

        return {
            "total_facts": fact_count,
            "total_relationships": rel_count,
            "relationship_types": type_counts,
        }

    async def close(self) -> None:
        """Close the underlying aiosqlite connection and its background thread.

        Call this when the KnowledgeGraph is no longer needed to ensure
        graceful shutdown of the background worker thread.
        """
        if self._conn is not None:
            await self._conn.close()
            self._conn = None


async def create_knowledge_graph(db_path: str) -> KnowledgeGraph:
    return KnowledgeGraph(db_path)