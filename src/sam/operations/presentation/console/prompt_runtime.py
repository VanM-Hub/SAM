"""PromptRuntime — Interactive prompt input handler.

Support: history, completion, multiline, confirmation, yes/no, interrupt.
Does NOT execute commands. Pure input runtime.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Iterator, List, Optional, Tuple


@dataclass(frozen=True)
class PromptResult:
    """Immutable result from prompt input."""
    text: str
    confirmed: bool = True
    interrupted: bool = False
    is_empty: bool = False
    error: str = ""


DEFAULT_HISTORY_SIZE = 100


@dataclass
class PromptRuntime:
    """Interactive prompt input handler.

    Manages input history, completion, and confirmation flows.
    Does NOT execute commands — returns PromptResult for the caller.

    Usage:
        prompt = PromptRuntime()
        result = prompt.input("> ")
        if not result.interrupted:
            process(result.text)
    """

    max_history: int = DEFAULT_HISTORY_SIZE
    _history: List[str] = field(default_factory=list)
    _history_cursor: int = -1
    _tab_completions: Optional[Tuple[str, ...]] = None
    _completion_idx: int = -1

    # ── History management ────────────────────────────────────────────

    @property
    def history(self) -> Tuple[str, ...]:
        """Get full history (most recent first)."""
        return tuple(reversed(self._history))

    @property
    def history_count(self) -> int:
        return len(self._history)

    def add_to_history(self, line: str) -> None:
        """Add a command line to history."""
        line = line.strip()
        if not line:
            return
        # Don't add duplicate of last entry
        if self._history and self._history[-1] == line:
            return
        self._history.append(line)
        if len(self._history) > self.max_history:
            self._history.pop(0)
        self._history_cursor = len(self._history)

    def clear_history(self) -> None:
        """Clear all history."""
        self._history.clear()
        self._history_cursor = -1

    def reset_cursor(self) -> None:
        """Reset the history cursor to the latest entry."""
        self._history_cursor = len(self._history)

    # ── Completion ────────────────────────────────────────────────────

    def set_completions(self, completions: Tuple[str, ...]) -> None:
        """Set current completion candidates."""
        self._tab_completions = completions
        self._completion_idx = -1

    def next_completion(self) -> Optional[str]:
        """Cycle to next completion candidate. Returns None if none."""
        if not self._tab_completions:
            return None
        self._completion_idx = (self._completion_idx + 1) % len(
            self._tab_completions
        )
        return self._tab_completions[self._completion_idx]

    def clear_completions(self) -> None:
        """Clear completion state."""
        self._tab_completions = None
        self._completion_idx = -1

    # ── Input methods ─────────────────────────────────────────────────

    def input(self, prompt: str = "> ") -> PromptResult:
        """Read a single line of input.

        Handles Ctrl+C (returns interrupted=True) and empty input.
        Actual input is via a blocking read from stdin.
        The caller provides the actual read mechanism.
        Returns PromptResult — command execution happens elsewhere.
        """
        try:
            text = input(prompt)
            is_empty = not text.strip()
            if not is_empty:
                self.add_to_history(text)
            return PromptResult(
                text=text.strip(),
                confirmed=True,
                interrupted=False,
                is_empty=is_empty,
            )
        except KeyboardInterrupt:
            return PromptResult(
                text="", confirmed=False, interrupted=True,
                is_empty=True, error="Interrupted by user",
            )
        except EOFError:
            return PromptResult(
                text="exit", confirmed=True, interrupted=False,
                is_empty=False,
            )

    def input_confirm(self, prompt: str, default: bool = True) -> bool:
        """Ask a yes/no confirmation question.

        Returns True for yes, False for no.
        Handles y/n/yes/no/enter (default).
        """
        suffix = " [Y/n]:" if default else " [y/N]:"
        try:
            text = input(prompt + suffix).strip().lower()
        except (KeyboardInterrupt, EOFError):
            return False

        if not text:
            return default
        if text in ("y", "yes"):
            return True
        if text in ("n", "no"):
            return False
        # Invalid input: ask again
        return self.input_confirm(
            f"Please answer 'y' or 'n'. {prompt}",
            default,
        )

    def input_multiline(self, prompt: str = "> ",
                        end_marker: str = ".") -> PromptResult:
        """Read multi-line input until end_marker on its own line.

        Returns concatenated lines.
        """
        lines: list = []
        try:
            while True:
                line = input(prompt)
                if line.strip() == end_marker:
                    break
                lines.append(line)
        except KeyboardInterrupt:
            return PromptResult(
                text="", confirmed=False, interrupted=True,
                is_empty=True, error="Multiline interrupted",
            )
        except EOFError:
            pass

        text = "\n".join(lines).strip()
        if text:
            self.add_to_history(text)
        return PromptResult(
            text=text, confirmed=True,
            is_empty=not bool(text),
        )

    def input_password(self, prompt: str = "Password: ") -> PromptResult:
        """Read a password/sensitive input (no echo in terminal).

        Note: On standard Python, input() does echo. This is a placeholder
        for getpass integration in a real terminal.
        """
        try:
            text = input(prompt)
            return PromptResult(
                text=text, confirmed=True, interrupted=False,
                is_empty=not bool(text.strip()),
            )
        except KeyboardInterrupt:
            return PromptResult(
                text="", confirmed=False, interrupted=True,
                is_empty=True, error="Password input interrupted",
            )

    # ── Iteration ─────────────────────────────────────────────────────

    def __iter__(self) -> Iterator[PromptResult]:
        """Iterate over input lines until empty/Ctrl+C.

        Usage:
            for result in prompt:
                if result.interrupted or result.text == "exit":
                    break
                handle(result)
        """
        while True:
            result = self.input()
            if result.interrupted or result.text in ("", "exit"):
                return
            yield result

    def __len__(self) -> int:
        return len(self._history)
