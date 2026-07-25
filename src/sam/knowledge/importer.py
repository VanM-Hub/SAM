from __future__ import annotations

import json
import structlog
from pathlib import Path
from typing import List, Optional
from uuid import uuid4

try:
    import yaml
except Exception:  # pragma: no cover - optional dependency
    yaml = None

from sam.knowledge.models import KnowledgeDocument
from sam.knowledge.store import KnowledgeStore


logger = structlog.get_logger()


class KnowledgeImporter:
    """Import knowledge facts from YAML/JSON files into a KnowledgeStore.

    The supported file format (YAML or JSON) is:

    facts:
      - statement: "Provider A supports Model X"
        category: capability
        metadata:
          provider: A
          model: X
          confidence: 0.95
        relationships:
          - target: "Model X requires GPU"
            type: depends_on
    """

    def __init__(self) -> None:
        self.logger = logger.bind(component="KnowledgeImporter")

    async def import_yaml(self, path: Path, store: KnowledgeStore) -> List[str]:
        if yaml is None:
            raise RuntimeError("PyYAML not available; install pyyaml to import YAML files")
        text = Path(path).read_text(encoding="utf-8")
        data = yaml.safe_load(text)
        return await self._import_data(data, path, store)

    async def import_json(self, path: Path, store: KnowledgeStore) -> List[str]:
        text = Path(path).read_text(encoding="utf-8")
        data = json.loads(text)
        return await self._import_data(data, path, store)

    async def _import_data(self, data: dict, path: Path, store: KnowledgeStore) -> List[str]:
        if not isinstance(data, dict) or "facts" not in data:
            raise ValueError("Invalid import format: expected top-level 'facts' list")

        facts = data.get("facts")
        if not isinstance(facts, list):
            raise ValueError("Invalid import format: 'facts' must be a list")

        # Ensure tables exist
        await store.init_tables()

        # Create a synthetic document for this import file
        doc_id = uuid4()
        conn = await store._ensure_connection()
        await conn.execute(
            "INSERT OR IGNORE INTO knowledge_documents (id, path, title, created_at) VALUES (?, ?, ?, datetime('now'))",
            (str(doc_id), str(path), path.name),
        )
        await conn.commit()

        created_ids: List[str] = []
        # First pass: create facts
        statement_to_id = {}
        for item in facts:
            statement = item.get("statement")
            if not statement:
                continue
            category = item.get("category", "general")
            metadata = item.get("metadata") or {}
            confidence = float(metadata.get("confidence", item.get("confidence", 0.7)))

            fact = await store.add_fact(
                document_id=doc_id,
                statement=statement,
                category=category,
                confidence=confidence,
                metadata=metadata,
            )
            created_ids.append(str(fact.id))
            statement_to_id[statement] = fact.id

        # Second pass: create explicit relationships
        for idx, item in enumerate(facts):
            statement = item.get("statement")
            if not statement:
                continue
            source_id = statement_to_id.get(statement)
            if not source_id:
                continue
            rels = item.get("relationships", [])
            for r in rels:
                target = r.get("target")
                rtype = r.get("type") or r.get("relationship_type") or "related_to"
                if not target:
                    continue
                # If target matches a created statement, prefer that id
                target_id = statement_to_id.get(target)
                if target_id is None:
                    # Try to resolve in existing store (by id or statement)
                    try:
                        resolved = await store._find_fact_by_identifier(target)
                        target_id = resolved.id if resolved else None
                    except Exception:
                        target_id = None

                if target_id:
                    try:
                        await store.graph.add_relationship(
                            source_id=source_id,
                            target_id=target_id,
                            rel_type=rtype,
                            metadata={"imported_from": str(path.name)},
                        )
                    except Exception as e:
                        self.logger.warning("failed_to_create_relationship", error=str(e), source=source_id, target=target)

        return created_ids

