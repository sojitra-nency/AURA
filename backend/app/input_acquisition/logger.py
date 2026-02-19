"""
Logging layer for the input acquisition system.

Records structural metadata about each acquired input.
Never stores transformed data or signal content.
"""

import sys
from collections import deque


class LogEntry:
    """A single immutable log record."""

    __slots__ = ("input_id", "modality", "timestamp", "data_size", "metadata_summary")

    def __init__(
        self,
        input_id: str,
        modality: str,
        timestamp: float,
        data_size: int,
        metadata_summary: dict,
    ):
        self.input_id = input_id
        self.modality = modality
        self.timestamp = timestamp
        self.data_size = data_size
        self.metadata_summary = metadata_summary

    def to_dict(self) -> dict:
        return {
            "input_id": self.input_id,
            "modality": self.modality,
            "timestamp": self.timestamp,
            "data_size": self.data_size,
            "metadata_summary": self.metadata_summary,
        }

    def __repr__(self) -> str:
        return (
            f"LogEntry(id={self.input_id[:8]}..., "
            f"modality={self.modality}, ts={self.timestamp:.4f})"
        )


def _compute_data_size(data) -> int:
    """Estimate the size of raw data without transforming it."""
    if isinstance(data, str):
        return len(data)
    if isinstance(data, list):
        return len(data)
    if isinstance(data, dict):
        total = 0
        for v in data.values():
            if isinstance(v, list):
                total += len(v)
            else:
                total += 1
        return total
    return sys.getsizeof(data)


class InputLogger:
    """
    Append-only log of input acquisition events.

    Stores only metadata — never raw signal content.
    Uses a bounded deque to cap memory usage.
    """

    DEFAULT_MAX_ENTRIES = 10_000

    def __init__(self, max_entries: int | None = None, echo: bool = False):
        cap = max_entries or self.DEFAULT_MAX_ENTRIES
        self._entries: deque[LogEntry] = deque(maxlen=cap)
        self._echo = echo
        self._counts: dict[str, int] = {}

    @property
    def total_logged(self) -> int:
        return sum(self._counts.values())

    @property
    def counts_by_modality(self) -> dict[str, int]:
        return dict(self._counts)

    def log(self, raw_input) -> LogEntry:
        """Record metadata about an acquired input."""
        entry = LogEntry(
            input_id=raw_input.id,
            modality=raw_input.modality,
            timestamp=raw_input.timestamp,
            data_size=_compute_data_size(raw_input.data),
            metadata_summary=raw_input.metadata,
        )
        self._entries.append(entry)
        self._counts[raw_input.modality] = self._counts.get(raw_input.modality, 0) + 1

        if self._echo:
            print(f"[INPUT] {entry}")

        return entry

    def get_entries(self, modality: str | None = None) -> list[LogEntry]:
        """Return log entries, optionally filtered by modality."""
        if modality is None:
            return list(self._entries)
        return [e for e in self._entries if e.modality == modality]

    def get_recent(self, n: int = 10) -> list[LogEntry]:
        """Return the n most recent log entries."""
        items = list(self._entries)
        return items[-n:] if n <= len(items) else items

    def clear(self):
        """Clear all log entries and counters."""
        self._entries.clear()
        self._counts.clear()

    def __len__(self) -> int:
        return len(self._entries)

    def __repr__(self) -> str:
        return f"InputLogger(entries={len(self._entries)}, counts={self._counts})"
