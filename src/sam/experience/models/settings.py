from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime


class SettingsCategory(str, Enum):
    RUNTIME = "runtime"
    MISSION = "mission"
    AUTONOMY = "autonomy"
    POLICY = "policy"
    PLUGIN = "plugin"
    HOSTING = "hosting"
    TELEMETRY = "telemetry"


class SettingsItem(BaseModel):
    """Satu item pengaturan."""
    key: str
    value: Any
    default: Optional[Any] = None
    description: Optional[str] = None
    category: SettingsCategory
    editable: bool = True
    sensitive: bool = False  # untuk credential, API key, dll.


class SettingsSection(BaseModel):
    """Kelompok pengaturan per kategori."""
    category: SettingsCategory
    name: str
    items: List[SettingsItem]


class SettingsModel(BaseModel):
    """ViewModel untuk halaman Settings."""
    sections: List[SettingsSection]
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        frozen = True
