"""Compatibility façade for ``sam.runtime.registry``.

The canonical implementation of the capability registry lives in the module
``src/sam/runtime/registry.py`` (single source of truth for
``CapabilityRegistry``).

This package directory (``sam/runtime/registry/``) coexists with that module
file under the same name. Python prioritises the package directory for the
import path ``sam.runtime.registry``, so this ``__init__.py`` acts as a
compatibility façade: it loads the canonical module file and re-exports its
public API under the original module name. This keeps the identity of
``CapabilityRegistry`` as ``sam.runtime.registry.CapabilityRegistry`` (no
aliasing, no duplicate classes) while preserving the import contract.

Scope: this file touches ONLY the registry package. No Repository Skeleton,
Architecture, or Compliance changes are introduced.
"""

import importlib.util
import sys
from pathlib import Path

# Canonical module file lives one level above this package directory:
#   sam/runtime/registry/__init__.py  (this façade)
#   sam/runtime/registry.py           (canonical module)
_parent_dir = Path(__file__).resolve().parent
_canonical_file = _parent_dir.parent / "registry.py"

_module_name = __name__  # "sam.runtime.registry"

_spec = importlib.util.spec_from_file_location(_module_name, _canonical_file)
_module = importlib.util.module_from_spec(_spec)
# Resolve the canonical module file under the SAME module name so class
# identity stays `sam.runtime.registry.CapabilityRegistry` (no duplicates).
sys.modules[_module_name] = _module
_spec.loader.exec_module(_module)

CapabilityRegistry = _module.CapabilityRegistry
logger = _module.logger

__all__ = [
    "CapabilityRegistry",
    "logger",
]
