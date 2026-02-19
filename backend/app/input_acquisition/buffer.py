"""
Deterministic FIFO buffer for short-term input storage.

Maintains insertion order, enforces a maximum capacity,
and supports retrieval by time range, modality, or ID.
No long-term storage. No transformation.
"""

from collections import OrderedDict


class InputBuffer:
    """
    Fixed-capacity ordered buffer of RawInput objects.

    When capacity is exceeded, the oldest entry is evicted (FIFO).
    """

    DEFAULT_CAPACITY = 1000

    def __init__(self, capacity: int | None = None):
        if capacity is not None:
            if not isinstance(capacity, int) or capacity <= 0:
                raise ValueError("capacity must be a positive integer")
        self._capacity = capacity or self.DEFAULT_CAPACITY
        self._store: OrderedDict[str, object] = OrderedDict()

    @property
    def capacity(self) -> int:
        return self._capacity

    @property
    def size(self) -> int:
        return len(self._store)

    @property
    def is_full(self) -> bool:
        return len(self._store) >= self._capacity

    def append(self, raw_input) -> str | None:
        """
        Add a RawInput to the buffer. Returns the evicted input's ID
        if the buffer was at capacity, otherwise None.
        """
        evicted_id = None
        if len(self._store) >= self._capacity:
            evicted_id, _ = self._store.popitem(last=False)
        self._store[raw_input.id] = raw_input
        return evicted_id

    def get_by_id(self, input_id: str):
        """Retrieve a single input by its unique ID, or None."""
        return self._store.get(input_id)

    def get_by_modality(self, modality: str) -> list:
        """Return all inputs matching the given modality, in insertion order."""
        return [inp for inp in self._store.values() if inp.modality == modality]

    def get_by_time_range(self, start: float, end: float) -> list:
        """Return all inputs whose timestamp falls within [start, end]."""
        return [
            inp
            for inp in self._store.values()
            if start <= inp.timestamp <= end
        ]

    def get_by_session(self, session_id: str) -> list:
        """Return all inputs belonging to a session."""
        return [inp for inp in self._store.values() if inp.session_id == session_id]

    def get_latest(self, n: int = 1) -> list:
        """Return the most recent n inputs (by insertion order)."""
        items = list(self._store.values())
        return items[-n:] if n <= len(items) else list(items)

    def get_all(self) -> list:
        """Return all buffered inputs in insertion order."""
        return list(self._store.values())

    def replay(self) -> list:
        """
        Return all inputs in insertion order for replay.
        Identical to get_all() — explicit name for intent clarity.
        """
        return self.get_all()

    def contains(self, input_id: str) -> bool:
        return input_id in self._store

    def clear(self):
        """Remove all inputs from the buffer."""
        self._store.clear()

    def __len__(self) -> int:
        return len(self._store)

    def __iter__(self):
        return iter(self._store.values())

    def __repr__(self) -> str:
        return f"InputBuffer(size={self.size}, capacity={self._capacity})"
