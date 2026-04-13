"""Loop detection for tool calls, inspired by Gemini CLI LoopDetectionService."""
from __future__ import annotations

import hashlib
import json
from typing import Any


class ToolCallLoopDetector:
    """Detects repetitive tool calls using SHA256 hashing (Gemini CLI approach).

    Generates a unique key from tool_name + serialized args and tracks
    consecutive identical calls.  When the count exceeds *threshold*,
    the call is considered a loop.
    """

    def __init__(self, threshold: int = 5) -> None:
        self.threshold = threshold
        self._last_key: str | None = None
        self._consecutive_count = 0
        self._total_calls = 0
        self._history: list[tuple[str, str, dict[str, Any]]] = []

    # ── public API ──────────────────────────────────────────────

    def record(self, tool_name: str, args: dict[str, Any]) -> bool:
        """Record a tool call and return *True* if a loop is detected."""
        self._total_calls += 1
        key = self._make_key(tool_name, args)

        if key == self._last_key:
            self._consecutive_count += 1
        else:
            self._last_key = key
            self._consecutive_count = 1

        self._history.append((tool_name, key, args))

        return self._consecutive_count >= self.threshold

    @property
    def last_key(self) -> str | None:
        return self._last_key

    @property
    def consecutive_count(self) -> int:
        return self._consecutive_count

    @property
    def total_calls(self) -> int:
        return self._total_calls

    def loop_description(self, tool_name: str) -> str:
        """Human-readable description of the detected loop."""
        return (
            f"tool-call loop: '{tool_name}' called {self._consecutive_count} times "
            f"consecutively with the same arguments"
        )

    # ── internals ───────────────────────────────────────────────

    @staticmethod
    def _make_key(tool_name: str, args: dict[str, Any]) -> str:
        """SHA256 hash of *tool_name* + canonical JSON of *args*."""
        payload = json.dumps({"tool": tool_name, "args": args}, sort_keys=True)
        return hashlib.sha256(payload.encode()).hexdigest()
