# OP-421 — SDK Protocol
# Python 3.8, frozen DTO, synchronous

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple, Protocol
from datetime import datetime
import uuid


@dataclass(frozen=True)
class SDKVersion:
    major: int = 1; minor: int = 0; patch: int = 0

    @staticmethod
    def current() -> "SDKVersion": return SDKVersion(1,0,0)
    def __str__(self): return f"{self.major}.{self.minor}.{self.patch}"
    def __gt__(self, other): return (self.major,self.minor,self.patch) > (other.major,other.minor,other.patch) if isinstance(other,SDKVersion) else False
    def __le__(self, other): return (self.major,self.minor,self.patch) <= (other.major,other.minor,other.patch) if isinstance(other,SDKVersion) else False


@dataclass(frozen=True)
class SDKMetadata:
    sdk_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""; version: SDKVersion = field(default_factory=SDKVersion.current)
    python_min_version: str = "3.8"
    sam_min_version: str = "4.0.0"
    description: str = ""


@dataclass(frozen=True)
class SDKCapability:
    name: str = ""; description: str = ""
    extension_type: str = ""  # plugin, connector, provider, adapter, integration
    read_only: bool = True; requires_approval: bool = True


@dataclass(frozen=True)
class SDKContext:
    context_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sdk_version: SDKVersion = field(default_factory=SDKVersion.current)
    extension_type: str = ""
    status: str = "initialized"


@dataclass(frozen=True)
class SDKResult:
    result_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    success: bool = False; preview: str = ""
    read_only: bool = True; requires_approval: bool = True
    extension_type: str = ""


@dataclass(frozen=True)
class SDKCompatibility:
    compatible: bool = True
    sdk_version_ok: bool = True
    python_version_ok: bool = True
    sam_version_ok: bool = True
    issues: Tuple[str, ...] = field(default_factory=tuple)


class SDKProtocol(Protocol):
    @property
    def metadata(self) -> SDKMetadata: ...
    def supported_extensions(self) -> Tuple[str, ...]: ...
    def validate_extension(self, ext_type: str, manifest: Dict[str, Any]) -> Tuple[str, ...]: ...
    def get_version(self) -> SDKVersion: ...
