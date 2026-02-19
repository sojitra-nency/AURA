"""
RawInput base class and modality-specific subclasses.

All input objects are immutable after creation. They carry raw signal data,
timestamps, and modality metadata. No transformation or interpretation occurs.
"""

import copy
import hashlib
import uuid


VALID_MODALITIES = frozenset({"text", "audio", "video", "physiological"})


class RawInput:
    """
    Base container for a single raw sensory signal.

    Immutable after __init__ completes. All fields are set once
    and any subsequent attribute assignment raises an error.
    """

    __slots__ = (
        "_id",
        "_modality",
        "_data",
        "_timestamp",
        "_metadata",
        "_session_id",
        "_source_id",
        "_checksum",
        "_frozen",
    )

    def __init__(
        self,
        modality: str,
        data,
        timestamp: float,
        metadata: dict | None = None,
        session_id: str | None = None,
        source_id: str | None = None,
    ):
        if modality not in VALID_MODALITIES:
            raise ValueError(
                f"Invalid modality '{modality}'. Must be one of {sorted(VALID_MODALITIES)}"
            )
        if data is None:
            raise ValueError("Data cannot be None")
        if not isinstance(timestamp, (int, float)):
            raise TypeError("Timestamp must be a numeric value")

        object.__setattr__(self, "_id", uuid.uuid4().hex)
        object.__setattr__(self, "_modality", modality)
        object.__setattr__(self, "_data", copy.deepcopy(data))
        object.__setattr__(self, "_timestamp", float(timestamp))
        object.__setattr__(self, "_metadata", dict(metadata) if metadata else {})
        object.__setattr__(self, "_session_id", session_id or "default")
        object.__setattr__(self, "_source_id", source_id or "unknown")
        object.__setattr__(self, "_checksum", self._compute_checksum())
        object.__setattr__(self, "_frozen", True)

    def __setattr__(self, name, value):
        if getattr(self, "_frozen", False):
            raise AttributeError(
                f"RawInput is immutable. Cannot set '{name}' after creation."
            )
        object.__setattr__(self, name, value)

    def __delattr__(self, name):
        raise AttributeError("RawInput is immutable. Cannot delete attributes.")

    def _compute_checksum(self) -> str:
        raw = repr(self._data).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    # --- Read-only properties ---

    @property
    def id(self) -> str:
        return self._id

    @property
    def modality(self) -> str:
        return self._modality

    @property
    def data(self):
        return copy.deepcopy(self._data)

    @property
    def timestamp(self) -> float:
        return self._timestamp

    @property
    def metadata(self) -> dict:
        return dict(self._metadata)

    @property
    def session_id(self) -> str:
        return self._session_id

    @property
    def source_id(self) -> str:
        return self._source_id

    @property
    def checksum(self) -> str:
        return self._checksum

    def verify_integrity(self) -> bool:
        return self._checksum == self._compute_checksum()

    def to_dict(self) -> dict:
        return {
            "id": self._id,
            "modality": self._modality,
            "timestamp": self._timestamp,
            "metadata": dict(self._metadata),
            "session_id": self._session_id,
            "source_id": self._source_id,
            "checksum": self._checksum,
            "data_type": type(self._data).__name__,
        }

    def __repr__(self) -> str:
        return (
            f"RawInput(id={self._id[:8]}..., modality={self._modality}, "
            f"timestamp={self._timestamp}, session={self._session_id})"
        )


# ---------------------------------------------------------------------------
# Modality-specific subclasses
# ---------------------------------------------------------------------------


class TextInput(RawInput):
    """Raw text signal. Preserves the original string without tokenization."""

    def __init__(
        self,
        data: str,
        timestamp: float,
        metadata: dict | None = None,
        session_id: str | None = None,
        source_id: str | None = None,
    ):
        if not isinstance(data, str):
            raise TypeError(f"TextInput data must be str, got {type(data).__name__}")
        if len(data) == 0:
            raise ValueError("TextInput data must not be empty")

        modality_meta = {
            "char_count": len(data),
            "encoding": "utf-8",
        }
        merged = {**modality_meta, **(metadata or {})}
        super().__init__("text", data, timestamp, merged, session_id, source_id)


class AudioInput(RawInput):
    """Raw audio waveform. Preserves samples without spectral analysis."""

    def __init__(
        self,
        data: list,
        sample_rate: int,
        channels: int = 1,
        timestamp: float = 0.0,
        metadata: dict | None = None,
        session_id: str | None = None,
        source_id: str | None = None,
    ):
        if not isinstance(data, list):
            raise TypeError(f"AudioInput data must be list, got {type(data).__name__}")
        if len(data) == 0:
            raise ValueError("AudioInput data must not be empty")
        if not isinstance(sample_rate, int) or sample_rate <= 0:
            raise ValueError("sample_rate must be a positive integer")
        if not isinstance(channels, int) or channels <= 0:
            raise ValueError("channels must be a positive integer")

        modality_meta = {
            "sample_rate": sample_rate,
            "channels": channels,
            "sample_count": len(data),
            "duration_seconds": len(data) / (sample_rate * channels),
        }
        merged = {**modality_meta, **(metadata or {})}
        super().__init__("audio", data, timestamp, merged, session_id, source_id)


class VideoInput(RawInput):
    """Raw video frames. Preserves pixel data without any visual analysis."""

    def __init__(
        self,
        data: list,
        resolution: tuple,
        timestamp: float = 0.0,
        metadata: dict | None = None,
        session_id: str | None = None,
        source_id: str | None = None,
    ):
        if not isinstance(data, list):
            raise TypeError(f"VideoInput data must be list, got {type(data).__name__}")
        if len(data) == 0:
            raise ValueError("VideoInput data must not be empty")
        if (
            not isinstance(resolution, (tuple, list))
            or len(resolution) != 2
            or not all(isinstance(v, int) and v > 0 for v in resolution)
        ):
            raise ValueError("resolution must be a (width, height) tuple of positive ints")

        modality_meta = {
            "frame_count": len(data),
            "resolution_width": resolution[0],
            "resolution_height": resolution[1],
        }
        merged = {**modality_meta, **(metadata or {})}
        super().__init__("video", data, timestamp, merged, session_id, source_id)


class PhysiologicalInput(RawInput):
    """Raw physiological signal. Preserves numeric samples without interpretation."""

    def __init__(
        self,
        data: dict,
        signal_type: str,
        sampling_frequency: float,
        timestamp: float = 0.0,
        metadata: dict | None = None,
        session_id: str | None = None,
        source_id: str | None = None,
    ):
        if not isinstance(data, dict):
            raise TypeError(
                f"PhysiologicalInput data must be dict, got {type(data).__name__}"
            )
        if len(data) == 0:
            raise ValueError("PhysiologicalInput data must not be empty")
        if not isinstance(signal_type, str) or len(signal_type) == 0:
            raise ValueError("signal_type must be a non-empty string")
        if not isinstance(sampling_frequency, (int, float)) or sampling_frequency <= 0:
            raise ValueError("sampling_frequency must be a positive number")

        modality_meta = {
            "signal_type": signal_type,
            "sampling_frequency": float(sampling_frequency),
            "channel_names": list(data.keys()),
            "sample_counts": {k: len(v) for k, v in data.items() if isinstance(v, list)},
        }
        merged = {**modality_meta, **(metadata or {})}
        super().__init__("physiological", data, timestamp, merged, session_id, source_id)
