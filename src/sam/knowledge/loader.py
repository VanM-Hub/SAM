"""Async Loader for knowledge documents (Markdown files)."""

import os
import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional, TYPE_CHECKING, Dict

import structlog

from sam.knowledge.models import KnowledgeDocument

if TYPE_CHECKING:
    from sam.knowledge.store import KnowledgeStore


class KnowledgeLoader:
    """Loads markdown knowledge documents from specified directories."""

    def __init__(self, root_path: str) -> None:
        self.root_path = Path(root_path)
        self.documents: List[KnowledgeDocument] = []
        self.logger = structlog.get_logger()

    async def load_all(self, store: Optional["KnowledgeStore"] = None) -> List[KnowledgeDocument]:
        """Load all markdown files from docs/ and modules/ subdirectories.

        If a KnowledgeStore is provided, also persist documents and facts
        and create auto-relationships from metadata.
        """
        self.documents.clear()
        for path in self.root_path.glob("docs/**/*.md"):
            doc = self._load_file(path)
            if doc:
                self.documents.append(doc)
                if store:
                    await self._persist_document(doc, store)
        for path in self.root_path.glob("modules/**/*.md"):
            doc = self._load_file(path)
            if doc:
                self.documents.append(doc)
                if store:
                    await self._persist_document(doc, store)
        self.logger.info("Knowledge documents loaded", count=len(self.documents))
        return self.documents

    def _load_file(self, path: Path) -> Optional[KnowledgeDocument]:
        """Load a single markdown file and extract metadata from frontmatter or headers."""
        try:
            content = path.read_text(encoding="utf-8")
            metadata = self._extract_metadata(content)
            if not metadata:
                return None
            # Extract known fields; the rest go to metadata dict
            title = metadata.pop("title", path.stem)
            version = metadata.pop("version", "0.1.0")
            status = metadata.pop("status", "Draft")
            knowledge_type = metadata.pop("knowledge_type", "Reference")
            evidence_level = metadata.pop("evidence_level", "Observed")
            confidence = metadata.pop("confidence", "Medium")
            owner = metadata.pop("owner", "SAM Framework")
            last_updated = metadata.pop("last_updated", datetime.utcnow())
            related_documents = metadata.pop("related_documents", [])
            references_from_header = metadata.pop("references", [])
            # Parse inline markdown links in body as references too
            link_pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
            inline_refs = [m.group(2) for m in link_pattern.finditer(content)]
            references = list(dict.fromkeys(references_from_header + inline_refs))
            # Ensure all remaining metadata values are strings
            cleaned_metadata: Dict[str, str] = {}
            for k, v in metadata.items():
                if isinstance(v, str):
                    cleaned_metadata[k] = v
                else:
                    cleaned_metadata[k] = str(v)
            return KnowledgeDocument(
                path=str(path.relative_to(self.root_path)),
                title=title,
                version=version,
                status=status,
                knowledge_type=knowledge_type,
                evidence_level=evidence_level,
                confidence=confidence,
                owner=owner,
                last_updated=last_updated,
                related_documents=related_documents,
                references=references,
                content=content,
                metadata=cleaned_metadata,
            )
        except Exception as e:  # pragma: no cover - defensive
            self.logger.error(
                "failed_to_load_knowledge_document",
                path=str(path),
                error=str(e),
            )
            return None

    def _extract_metadata(self, content: str) -> dict:
        """Extract simple metadata from markdown content.

        Looks for lines like:
        # Title
        Version: 1.0
        Status: Draft
        Owner: Someone
        Knowledge Type: Concept
        Evidence Level: Verified
        Confidence: High
        Related Documents: doc1.md, doc2.md
        Last Updated: 2024-01-01
        Capability Type: observation.health-checks
        Capability ID: openclaw.health-checks
        """
        patterns = {
            "title": r"^#\s*(.+?)\n",
            "version": r"Version:\s*(.+?)\n",
            "status": r"Status:\s*(.+?)\n",
            "owner": r"Owner:\s*(.+?)\n",
            "knowledge_type": r"Knowledge Type:\s*(.+?)\n",
            "evidence_level": r"Evidence Level:\s*(.+?)\n",
            "confidence": r"Confidence:\s*(.+?)\n",
            "related_documents": r"Related Documents:\s*(.+?)\n",
            "references": r"References:\s*(.+?)\n",
            "last_updated": r"Last Updated:\s*(.+?)\n",
            "capability_type": r"Capability Type:\s*(.+?)\n",
            "capability_id": r"Capability ID:\s*(.+?)\n",
        }
        result = {}
        for key, pattern in patterns.items():
            match = re.search(pattern, content, re.IGNORECASE | re.MULTILINE)
            if match:
                value = match.group(1).strip()
                if key == "related_documents" or key == "references":
                    result[key] = [doc.strip() for doc in value.split(",") if doc.strip()]
                elif key == "last_updated":
                    dt = self._parse_date(value)
                    result[key] = dt if dt is not None else datetime.utcnow()
                else:
                    result[key] = value
        return result

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Try to parse a date string using common formats."""
        date_str = date_str.strip().strip('"\'')
        formats = [
            "%Y-%m-%d",
            "%Y/%m/%d",
            "%d-%m-%Y",
            "%m/%d/%Y",
            "%Y-%m-%d %H:%M:%S",
            "%Y/%m/%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%SZ",
        ]
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        # Try ISO format with timezone
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except ValueError:
            pass
        return None

    async def _persist_document(self, doc: KnowledgeDocument, store: "KnowledgeStore") -> None:
        """Persist a document and its extracted facts to the knowledge store.

        For each section/heading in the document that looks like a fact statement,
        create a KnowledgeFact. Auto-relationships from metadata are handled
        by store.add_fact via metadata keys.
        """
        import json
        from uuid import uuid4

        # First ensure the document row exists in knowledge_documents
        conn = await store._ensure_connection()
        await conn.execute(
            """
            INSERT OR IGNORE INTO knowledge_documents (id, path, title, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                str(doc.id),
                doc.path,
                doc.title,
                doc.last_updated.isoformat(),
            ),
        )
        await conn.commit()

        # Extract fact-like statements from the document content
        # Simple heuristic: look for lines starting with "- " or "* " under headings
        facts_created = 0
        lines = doc.content.split("\n")
        current_section = ""
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("#"):
                current_section = stripped.lstrip("#").strip()
                continue
            if stripped.startswith(("- ", "* ")):
                statement = stripped[2:].strip()
                if statement:
                    # Determine category from section or default
                    category = current_section.lower().replace(" ", "_") or "general"
                    # Confidence from document metadata
                    confidence_map = {"high": 0.9, "medium": 0.7, "low": 0.4}
                    confidence = confidence_map.get(doc.confidence.lower(), 0.7)
                    # Build metadata including auto-relationship hints
                    fact_metadata = dict(doc.metadata)
                    fact_metadata["source_document"] = str(doc.id)
                    fact_metadata["source_section"] = current_section
                    # related_documents -> related_to auto-relationships
                    if doc.related_documents:
                        fact_metadata["related_to"] = doc.related_documents

                    await store.add_fact(
                        document_id=doc.id,
                        statement=statement,
                        category=category,
                        confidence=confidence,
                        metadata=fact_metadata,
                    )
                    facts_created += 1
        self.logger.info("Document persisted with facts", doc_id=str(doc.id), facts=facts_created)
