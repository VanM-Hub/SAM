# SAM Service Layer — Phase 1

from .manager import ServiceManager
from .systemd import generate_unit_file, SYSTEMD_UNIT

try:
    from .windows import SAMService
except ImportError:
    SAMService = None  # pywin32 not available on Linux

__all__ = [
    "ServiceManager",
    "generate_unit_file",
    "SYSTEMD_UNIT",
    "SAMService",
]
