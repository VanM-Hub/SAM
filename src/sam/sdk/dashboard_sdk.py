# OP-427 — Dashboard SDK
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Tuple
from .plugin_sdk import PluginSDK
from .connector_sdk import ConnectorSDK
from .provider_sdk import ProviderSDK
from .extension_validator import ExtensionValidator

@dataclass(frozen=True)
class SDKCard:
    version: str = ""; extensions: int = 0

@dataclass(frozen=True)
class CompatibilityCardP:
    compatible: bool = True; checked: int = 0

@dataclass(frozen=True)
class ExtensionCard:
    plugin_templates: int = 0; connector_templates: int = 0; provider_templates: int = 0

@dataclass(frozen=True)
class ValidationCardP:
    validated: int = 0; failed: int = 0

@dataclass(frozen=True)
class TemplateCard:
    total: int = 0; types: Tuple[str,...] = field(default_factory=tuple)

@dataclass(frozen=True)
class SummaryCardSDK:
    sdk_version: str = ""; extensions: int = 0; templates: int = 0

@dataclass(frozen=True)
class SDKDashboard:
    sdk: SDKCard = field(default_factory=SDKCard)
    compatibility: CompatibilityCardP = field(default_factory=CompatibilityCardP)
    extensions: ExtensionCard = field(default_factory=ExtensionCard)
    validation: ValidationCardP = field(default_factory=ValidationCardP)
    templates: TemplateCard = field(default_factory=TemplateCard)
    summary: SummaryCardSDK = field(default_factory=SummaryCardSDK)
    timestamp: datetime = field(default_factory=datetime.utcnow)


class SDKDashboardBuilder:
    @staticmethod
    def build(psdk: PluginSDK, csdk: ConnectorSDK, prsdk: ProviderSDK,
              validator: ExtensionValidator) -> SDKDashboard:
        sv = "1.0.0"
        pt = len(psdk.get_templates()); ct = len(csdk.get_templates()); prt = len(prsdk.get_templates())
        sdk_card = SDKCard(version=sv, extensions=pt+ct+prt)
        comp = validator.check_sdk_compatibility()
        compat_card = CompatibilityCardP(compatible=comp.compatible, checked=1)
        ext_card = ExtensionCard(plugin_templates=pt, connector_templates=ct, provider_templates=prt)
        val_card = ValidationCardP()
        tmpl_types = tuple(["plugin"]*pt + ["connector"]*ct + ["provider"]*prt)
        tmpl_card = TemplateCard(total=pt+ct+prt, types=tmpl_types)
        summ_card = SummaryCardSDK(sdk_version=sv, extensions=pt+ct+prt, templates=pt+ct+prt)
        return SDKDashboard(sdk=sdk_card, compatibility=compat_card, extensions=ext_card,
            validation=val_card, templates=tmpl_card, summary=summ_card)
