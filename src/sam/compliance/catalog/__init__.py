"""P1-004 Compliance Check Catalog — canonical source of truth.

Exports:
    ComplianceCheckCatalog   — Main catalog with 99 check entries
    CheckMetadata            — Frozen metadata record per check
    CheckLevel, CheckCategory, CheckSeverity, EvidenceType,
    CheckAuthority, CheckerClass — Enums
    CatalogError              — Catalog-level errors
"""

from .catalog import ComplianceCheckCatalog, CatalogError
from .models import (
    CheckMetadata, CheckLevel, CheckCategory, CheckSeverity,
    EvidenceType, CheckAuthority, CheckerClass,
)

__all__ = [
    "ComplianceCheckCatalog",
    "CatalogError",
    "CheckMetadata",
    "CheckLevel",
    "CheckCategory",
    "CheckSeverity",
    "EvidenceType",
    "CheckAuthority",
    "CheckerClass",
]
