"""L1 Specification checkers (P1-008 Batch 2).

The 40 L1 checks verify that specification-mandated artifacts (models,
enums, services, validators, methods) exist in the source tree. Each
check searches the BaselineSnapshot source inventory for one or more
required symbols/predicates, supplied per-check by the builder from the
catalog description — so no checker hardcodes a path or authority.

Reading is done through ContentIndex (source files only, memoized).
Deterministic: same snapshot -> same result.
"""

from __future__ import annotations

from typing import List, Optional, Sequence

from ..base.base_check import BaseComplianceCheck
from ..base.check_context import CheckContext
from ..base.check_result import CheckResult
from ._shared import BaselineResolver, ContentIndex


class SourceSymbolPresenceCheck(BaseComplianceCheck):
    """Verifies required symbols exist somewhere in the baseline source.

    Config fields (from builder):
        symbols: list of literal substrings to search for. The check
                 passes when each symbol appears in at least one indexed
                 source file (matching by simple substring, case-aware).
        any_of:  when True, passes when ANY symbol is found (default
                 False = ALL symbols required).
        prefixes: source path roots to search (default src/sam/).
    """

    def __init__(
        self,
        symbols: Sequence[str],
        any_of: bool = False,
        prefixes: Sequence[str] = ("src/sam/",),
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._symbols = tuple(symbols)
        self._any_of = any_of
        self._prefixes = tuple(prefixes)

    @property
    def symbols(self) -> tuple:
        return self._symbols

    def execute(self, context: CheckContext) -> CheckResult:
        index = ContentIndex(
            BaselineResolver(), context, prefixes=self._prefixes)
        found_map = {}
        missing = []
        for sym in self._symbols:
            found, hits = index.any_file_contains(sym, is_regex=False)
            found_map[sym] = hits
            if not found and not self._any_of:
                missing.append(sym)

        if self._any_of:
            if any(found_map.values()):
                return CheckResult.success(
                    details="Found required symbol(s) among: %s"
                            % ", ".join(self._symbols),
                    evidence={"symbols": list(self._symbols),
                              "found": {k: v for k, v in found_map.items()
                                         if v}},
                )
            return CheckResult.failure(
                details="None of the required symbols found: %s"
                        % ", ".join(self._symbols),
                evidence={"symbols": list(self._symbols),
                          "found": {k: v for k, v in found_map.items()
                                     if v}},
            )

        if not missing:
            return CheckResult.success(
                details="All %d required symbol(s) present: %s"
                        % (len(self._symbols), ", ".join(self._symbols)),
                evidence={"symbols": list(self._symbols),
                          "found": {k: v for k, v in found_map.items()
                                     if v}},
            )
        return CheckResult.failure(
            details="Missing symbol(s): %s" % ", ".join(missing),
            evidence={"symbols": list(self._symbols),
                      "missing": missing,
                      "found": {k: v for k, v in found_map.items() if v}},
        )


class SourceSymbolAbsentCheck(BaseComplianceCheck):
    """Verifies a symbol is NOT present in the baseline source.

    Config fields:
        symbols: literal substrings that must be absent everywhere.
        prefixes: source path roots to search. Defaults to the runtime
                  subtree (src/sam/runtime/) — ADR SOURCE_ABSENT checks
                  constrain the reference runtime, not the compliance
                  tooling or unrelated subsystems.
    """

    def __init__(
        self,
        symbols: Sequence[str],
        prefixes: Sequence[str] = ("src/sam/runtime/",),
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._symbols = tuple(symbols)
        self._prefixes = tuple(prefixes)

    def execute(self, context: CheckContext) -> CheckResult:
        index = ContentIndex(
            BaselineResolver(), context, prefixes=self._prefixes)
        found = {}
        for sym in self._symbols:
            present, hits = index.any_file_contains(sym, is_regex=False)
            if present:
                found[sym] = hits
        if not found:
            return CheckResult.success(
                details="Forbidden symbol(s) absent: %s"
                        % ", ".join(self._symbols),
                evidence={"symbols": list(self._symbols), "found": {}},
            )
        return CheckResult.failure(
            details="Forbidden symbol(s) present: %s"
                    % ", ".join(sorted(found)),
            evidence={"symbols": list(self._symbols), "found": found},
        )
