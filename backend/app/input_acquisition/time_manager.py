"""
Deterministic time management for the AURA system.

Supports two modes:
  - REAL: uses actual system clock (time.time())
  - SIMULATED: manually advanced via tick(), fully deterministic

Simulated mode is critical for reproducible testing and
later emotional dynamics modeling.
"""

import time
import enum


class TimeMode(enum.Enum):
    REAL = "real"
    SIMULATED = "simulated"


class TimeManager:
    """
    Central clock for the input acquisition layer.

    In SIMULATED mode, time only advances when tick() is called,
    ensuring fully deterministic and reproducible behavior.
    """

    def __init__(self, mode: TimeMode = TimeMode.REAL, start_time: float = 0.0):
        if not isinstance(mode, TimeMode):
            raise TypeError(f"mode must be a TimeMode enum, got {type(mode).__name__}")
        if not isinstance(start_time, (int, float)):
            raise TypeError("start_time must be numeric")

        self._mode = mode
        self._simulated_time = float(start_time)
        self._tick_count = 0
        self._tick_delta = 1.0  # default seconds per tick in simulated mode

    @property
    def mode(self) -> TimeMode:
        return self._mode

    @property
    def tick_count(self) -> int:
        return self._tick_count

    @property
    def tick_delta(self) -> float:
        return self._tick_delta

    @tick_delta.setter
    def tick_delta(self, value: float):
        if not isinstance(value, (int, float)) or value <= 0:
            raise ValueError("tick_delta must be a positive number")
        self._tick_delta = float(value)

    def now(self) -> float:
        """Return the current time according to the active mode."""
        if self._mode == TimeMode.REAL:
            return time.time()
        return self._simulated_time

    def tick(self, delta: float | None = None) -> float:
        """
        Advance simulated time by delta seconds (or tick_delta if omitted).
        Returns the new time. No-op in REAL mode (returns current real time).
        """
        if self._mode == TimeMode.REAL:
            return self.now()

        step = delta if delta is not None else self._tick_delta
        if not isinstance(step, (int, float)) or step < 0:
            raise ValueError("tick delta must be a non-negative number")

        self._simulated_time += step
        self._tick_count += 1
        return self._simulated_time

    def reset(self, start_time: float = 0.0):
        """Reset simulated clock to a given time. Only affects SIMULATED mode."""
        if self._mode == TimeMode.SIMULATED:
            self._simulated_time = float(start_time)
            self._tick_count = 0

    def __repr__(self) -> str:
        return (
            f"TimeManager(mode={self._mode.value}, "
            f"time={self.now():.4f}, ticks={self._tick_count})"
        )
