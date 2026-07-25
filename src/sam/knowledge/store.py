"""Knowledge Store - manages atomic knowledge facts and integrates with KnowledgeGraph (async, reuses connection)."""

from __future__ import annotations

import json
import structlog
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4

import aiosqlite

from .models import KnowledgeFact, KnowledgeDocument
from .graph import KnowledgeGraph


logger = structlog.get_logger()


class KnowledgeStore:
    """Stores and manages atomic knowledge facts.

    Knowledge facts are extracted from documents and can be queried,
    linked via relationships, and versioned.
    """

    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self.logger = logger.bind(component="KnowledgeStore")
        self._graph: Optional[KnowledgeGraph] = None
        self._conn: Optional[aiosqlite.Connection] = None

    @property
    def graph(self) -> KnowledgeGraph:
        """Lazy-load the KnowledgeGraph."""
        if self._graph is None:
            self._graph = KnowledgeGraph(self.db_path)
        return self._graph

    async def _ensure_connection(self) -> aiosqlite.Connection:
        """Ensure a single aiosqlite connection per KnowledgeStore instance."""
        if self._conn is None:
            self._conn = await aiosqlite.connect(self.db_path, check_same_thread=False)
            self._conn.row_factory = aiosqlite.Row
        return self._conn

    async def init_tables(self) -> None:
        """Create knowledge facts table if not exists."""
        conn = await self._ensure_connection()
        # Create knowledge_documents table first (referenced by knowledge)
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS knowledge_documents (
                id TEXT PRIMARY KEY,
                path TEXT,
                title TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            )
            """
        )
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS knowledge (
                id TEXT PRIMARY KEY,
                document_id TEXT NOT NULL,
                statement TEXT NOT NULL,
                category TEXT NOT NULL,
                confidence REAL NOT NULL DEFAULT 1.0,
                metadata TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                version INTEGER NOT NULL DEFAULT 1,
                previous_version INTEGER DEFAULT NULL,
                FOREIGN KEY (document_id) REFERENCES knowledge_documents(id) ON DELETE CASCADE
            )
            """
        )
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_knowledge_category ON knowledge(category)"
        )
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_knowledge_document ON knowledge(document_id)"
        )
        await conn.commit()

        # Create knowledge_history table for versioned snapshots
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS knowledge_history (
                id TEXT PRIMARY KEY,
                knowledge_id TEXT NOT NULL,
                version INTEGER NOT NULL,
                payload_snapshot TEXT NOT NULL,
                changed_by TEXT NOT NULL,
                changed_at TEXT NOT NULL DEFAULT (datetime('now')),
                change_type TEXT NOT NULL,
                FOREIGN KEY (knowledge_id) REFERENCES knowledge(id) ON DELETE CASCADE
            )
            """
        )
        await conn.commit()

    async def add_document(self, document: KnowledgeDocument) -> UUID:
        """Add a knowledge document to the store."""
        conn = await self._ensure_connection()
        await conn.execute(
            """
            INSERT OR IGNORE INTO knowledge_documents (id, path, title, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                str(document.id),
                document.path,
                document.title,
                document.last_updated.isoformat(),
            ),
        )
        await conn.commit()
        return document.id

    async def add_fact(
        self,
        document_id: UUID,
        statement: str,
        category: str,
        confidence: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> KnowledgeFact:
        """Add a new knowledge fact.

        Args:
            document_id: Source document UUID
            statement: The factual statement
            category: Category (e.g., "provider", "model", "capability", "constraint")
            confidence: Confidence score 0.0 - 1.0
            metadata: Additional metadata

        Returns:
            The created KnowledgeFact
        """
        fact = KnowledgeFact(
            document_id=document_id,
            statement=statement,
            category=category,
            confidence=confidence,
            metadata=metadata or {},
        )

        conn = await self._ensure_connection()
        await conn.execute(
            """
            INSERT INTO knowledge (id, document_id, statement, category, confidence, metadata, created_at, version, previous_version)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(fact.id),
                str(document_id),
                statement,
                category,
                confidence,
                json.dumps(metadata or {}),
                fact.created_at.isoformat(),
                fact.version,
                None,  # previous_version is NULL for new facts
            ),
        )
        await conn.commit()

        self.logger.info(
            "Fact added",
            fact_id=str(fact.id),
            category=category,
            statement=statement[:50],
        )

        # Record history entry
        await self._record_history(fact, "created", "system")

        # Check for auto-relationships from metadata
        if metadata:
            await self._process_auto_relationships(fact)

        return fact

    async def _process_auto_relationships(self, fact: KnowledgeFact) -> None:
        """Process metadata for automatic relationship creation.

        Looks for:
        - metadata["related_to"]: list of fact IDs or statements to link with "related_to"
        - metadata["supports"]: list of fact IDs to link with "supports"
        - metadata["depends_on"]: list of fact IDs to link with "depends_on"
        """
        rel_mappings = {
            "related_to": "related_to",
            "supports": "supports",
            "depends_on": "depends_on",
            "requires": "requires",
            "contradicts": "contradicts",
            "related_documents": "related_to",
            "references": "references",
        }

        for meta_key, rel_type in rel_mappings.items():
            if meta_key in fact.metadata:
                targets = fact.metadata[meta_key]
                if isinstance(targets, str):
                    targets = [targets]
                for target in targets:
                    # Try to find target fact by statement or ID
                    # Special handling: if target looks like a document path (endswith .md), try resolve by document
                    target_id = None
                    if isinstance(target, str) and (target.endswith('.md') or '/' in target or '\\' in target):
                        # try resolve document path -> find a fact belonging to that document
                        conn = await self._ensure_connection()
                        try:
                            cur = await conn.execute(
                                "SELECT id FROM knowledge_documents WHERE path = ? LIMIT 1",
                                (target,),
                            )
                            row = await cur.fetchone()
                            if row:
                                doc_id = row['id']
                                cur2 = await conn.execute(
                                    "SELECT id FROM knowledge WHERE document_id = ? LIMIT 1",
                                    (doc_id,)
                                )
                                r2 = await cur2.fetchone()
                                if r2:
                                    target_id = r2['id']
                        except Exception:
                            target_id = None

                    if target_id is None:
                        target_fact = await self._find_fact_by_identifier(target)
                        if target_fact:
                            target_id = str(target_fact.id)

                    if target_id:
                        try:
                            await self.graph.add_relationship(
                                source_id=fact.id,
                                target_id=UUID(target_id) if not isinstance(target_id, UUID) else target_id,
                                rel_type=rel_type,
                                metadata={"auto_created": True, "source_metadata_key": meta_key},
                            )
                        except Exception as e:
                            self.logger.warning(
                                "Failed to create auto relationship",
                                source_id=str(fact.id),
                                target_identifier=target,
                                error=str(e),
                            )

    async def _find_fact_by_identifier(self, identifier: str) -> Optional[KnowledgeFact]:
        """Find a fact by UUID or by statement text match."""
        # Try as UUID first
        try:
            fact_id = UUID(identifier)
            return await self.get_fact(fact_id)
        except ValueError:
            pass

        # Try fuzzy statement match
        conn = await self._ensure_connection()
        cursor = await conn.execute(
            "SELECT * FROM knowledge WHERE statement LIKE ? LIMIT 1",
            (f"%{identifier}%",),
        )
        row = await cursor.fetchone()

        if row:
            return KnowledgeFact(
                id=UUID(row["id"]),
                document_id=UUID(row["document_id"]),
                statement=row["statement"],
                category=row["category"],
                confidence=row["confidence"],
                metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                created_at=datetime.fromisoformat(row["created_at"]),
                version=row["version"],
            )
        return None

    async def get_fact(self, fact_id: UUID) -> Optional[KnowledgeFact]:
        """Get a knowledge fact by ID."""
        conn = await self._ensure_connection()
        cursor = await conn.execute(
            "SELECT * FROM knowledge WHERE id = ?",
            (str(fact_id),),
        )
        row = await cursor.fetchone()

        if not row:
            return None

        return KnowledgeFact(
            id=UUID(row["id"]),
            document_id=UUID(row["document_id"]),
            statement=row["statement"],
            category=row["category"],
            confidence=row["confidence"],
            metadata=json.loads(row["metadata"]) if row["metadata"] else {},
            created_at=datetime.fromisoformat(row["created_at"]),
            version=row["version"],
        )

    async def list_facts(
        self,
        category: Optional[str] = None,
        document_id: Optional[UUID] = None,
        limit: int = 100,
    ) -> List[KnowledgeFact]:
        """List knowledge facts with optional filters."""
        conditions = []
        params = []

        if category:
            conditions.append("category = ?")
            params.append(category)
        if document_id:
            conditions.append("document_id = ?")
            params.append(str(document_id))

        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        query = f"SELECT * FROM knowledge {where_clause} ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        conn = await self._ensure_connection()
        cursor = await conn.execute(query, params)
        rows = await cursor.fetchall()

        facts = []
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

    async def update_fact(self, fact_id: UUID, updates: Dict[str, Any]) -> Optional[KnowledgeFact]:
        """Update a knowledge fact (creates new version)."""
        current = await self.get_fact(fact_id)
        if not current:
            return None

        # Apply updates
        for key, value in updates.items():
            if hasattr(current, key):
                setattr(current, key, value)

        current.version += 1
        current.created_at = datetime.utcnow()

        conn = await self._ensure_connection()
        await conn.execute(
            """
            UPDATE knowledge
            SET statement = ?, category = ?, confidence = ?, metadata = ?, version = ?, created_at = ?, previous_version = ?
            WHERE id = ?
            """,
            (
                current.statement,
                current.category,
                current.confidence,
                json.dumps(current.metadata),
                current.version,
                current.created_at.isoformat(),
                current.version - 1,
                str(fact_id),
            ),
        )

        # Record history entry
        import uuid as _uuid
        history_id = _uuid.uuid4()
        await conn.execute(
            """
            INSERT INTO knowledge_history (id, knowledge_id, version, payload_snapshot, changed_by, changed_at, change_type)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(history_id),
                str(fact_id),
                current.version,
                json.dumps({
                    "id": str(current.id),
                    "document_id": str(current.document_id),
                    "statement": current.statement,
                    "category": current.category,
                    "confidence": current.confidence,
                    "metadata": current.metadata,
                    "created_at": current.created_at.isoformat(),
                    "version": current.version,
                }),
                "system",
                datetime.utcnow().isoformat(),
                "updated",
            ),
        )

        await conn.commit()

        self.logger.info("Fact updated", fact_id=str(fact_id), version=current.version)
        return current

    async def delete_fact(self, fact_id: UUID) -> bool:
        """Delete a knowledge fact and its relationships."""
        # Get fact before deleting for history
        current = await self.get_fact(fact_id)
        conn = await self._ensure_connection()
        await conn.execute("DELETE FROM knowledge WHERE id = ?", (str(fact_id),))
        await conn.commit()

        # Record history entry
        if current:
            await self._record_history(current, "deleted", "system")

        self.logger.info("Fact deleted", fact_id=str(fact_id))
        return True

    async def search_facts(self, query: str, limit: int = 20) -> List[KnowledgeFact]:
        """Search facts by statement text (simple LIKE query)."""
        conn = await self._ensure_connection()
        cursor = await conn.execute(
            "SELECT * FROM knowledge WHERE statement LIKE ? ORDER BY created_at DESC LIMIT ?",
            (f"%{query}%", limit),
        )
        rows = await cursor.fetchall()

        facts = []
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

    async def list_history(self, fact_id: UUID) -> List["KnowledgeHistory"]:
        """Get version history for a knowledge fact."""
        from sam.knowledge.models import KnowledgeHistory
        
        conn = await self._ensure_connection()
        cursor = await conn.execute(
            "SELECT * FROM knowledge_history WHERE knowledge_id = ? ORDER BY version ASC",
            (str(fact_id),),
        )
        rows = await cursor.fetchall()

        history = []
        for row in rows:
            history.append(
                KnowledgeHistory(
                    id=UUID(row["id"]),
                    knowledge_id=UUID(row["knowledge_id"]),
                    version=row["version"],
                    payload_snapshot=json.loads(row["payload_snapshot"]),
                    changed_by=row["changed_by"],
                    changed_at=datetime.fromisoformat(row["changed_at"]),
                    change_type=row["change_type"],
                )
            )
        return history

    async def get_stats(self) -> Dict[str, Any]:
        """Get store statistics."""
        conn = await self._ensure_connection()
        cursor = await conn.execute("SELECT COUNT(*) as count FROM knowledge")
        row = await cursor.fetchone()
        fact_count = row["count"] if row else 0

        cursor = await conn.execute(
            "SELECT category, COUNT(*) as count FROM knowledge GROUP BY category"
        )
        rows = await cursor.fetchall()
        category_counts = {row["category"]: row["count"] for row in rows}

        graph_stats = await self.graph.get_graph_stats()

        return {
            "facts": {
                "total": fact_count,
                "by_category": category_counts,
            },
            "graph": graph_stats,
        }

    async def _record_history(
        self,
        fact: KnowledgeFact,
        change_type: str,
        changed_by: str = "system",
    ) -> None:
        """Record a history entry for a fact change."""
        import uuid as _uuid
        from datetime import datetime

        history_id = _uuid.uuid4()
        snapshot = {
            "id": str(fact.id),
            "document_id": str(fact.document_id),
            "statement": fact.statement,
            "category": fact.category,
            "confidence": fact.confidence,
            "metadata": fact.metadata,
            "created_at": fact.created_at.isoformat(),
            "version": fact.version,
        }

        conn = await self._ensure_connection()
        await conn.execute(
            """
            INSERT INTO knowledge_history (id, knowledge_id, version, payload_snapshot, changed_by, changed_at, change_type)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(history_id),
                str(fact.id),
                fact.version,
                json.dumps(snapshot),
                changed_by,
                datetime.utcnow().isoformat(),
                change_type,
            ),
        )
        await conn.commit()

    async def close(self) -> None:
        """Close the underlying aiosqlite connection and its background thread."""
        if self._conn is not None:
            await self._conn.close()
            self._conn = None
        # Also close the graph connection if it was created
        if self._graph is not None:
            await self._graph.close()


async def create_knowledge_store(db_path: str) -> KnowledgeStore:
    """Factory function to create a KnowledgeStore instance."""
    store = KnowledgeStore(db_path)
    await store.init_tables()
    return store
