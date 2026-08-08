# Runtime Diagnostics Compliance - IP-3.2-001 / WP-09
# Suite compliance: pastikan IP-3.2-001 murni observasi, tanpa authority.

from sam.autonomy_runtime.compliance.checker import (
    compliance_check,
    default_source_files,
)

__all__ = ["compliance_check", "default_source_files"]