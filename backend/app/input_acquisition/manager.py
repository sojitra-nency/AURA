"""
InputAcquisitionManager — the central orchestrator for Phase 1.

Receives raw signals, validates them, wraps them in the correct
RawInput subclass, timestamps them, buffers them, and logs them.

This is the single entry point for all modalities.
"""

from app.input_acquisition.raw_input import (
    TextInput,
    AudioInput,
    VideoInput,
    PhysiologicalInput,
)
from app.input_acquisition.time_manager import TimeManager, TimeMode
from app.input_acquisition.buffer import InputBuffer
from app.input_acquisition.validation import InputValidator, ValidationError
from app.input_acquisition.logger import InputLogger


class InputAcquisitionManager:
    """
    Facade that coordinates validation, timestamping, wrapping,
    buffering, and logging of all incoming raw signals.
    """

    def __init__(
        self,
        time_manager: TimeManager | None = None,
        buffer: InputBuffer | None = None,
        logger: InputLogger | None = None,
        session_id: str = "default",
    ):
        self._time = time_manager if time_manager is not None else TimeManager(mode=TimeMode.REAL)
        self._buffer = buffer if buffer is not None else InputBuffer()
        self._logger = logger if logger is not None else InputLogger()
        self._session_id = session_id
        self._total_received = 0

    # --- Properties ---

    @property
    def time_manager(self) -> TimeManager:
        return self._time

    @property
    def buffer(self) -> InputBuffer:
        return self._buffer

    @property
    def logger(self) -> InputLogger:
        return self._logger

    @property
    def session_id(self) -> str:
        return self._session_id

    @property
    def total_received(self) -> int:
        return self._total_received

    # --- Receive methods ---

    def receive_text(
        self,
        text: str,
        source_id: str = "unknown",
        metadata: dict | None = None,
    ) -> TextInput:
        """Acquire a raw text signal."""
        InputValidator.validate_text(text)
        ts = self._time.now()

        inp = TextInput(
            data=text,
            timestamp=ts,
            metadata=metadata,
            session_id=self._session_id,
            source_id=source_id,
        )
        self._ingest(inp)
        return inp

    def receive_audio(
        self,
        waveform: list,
        sample_rate: int,
        channels: int = 1,
        source_id: str = "unknown",
        metadata: dict | None = None,
    ) -> AudioInput:
        """Acquire a raw audio waveform."""
        InputValidator.validate_audio(waveform, sample_rate, channels)
        ts = self._time.now()

        inp = AudioInput(
            data=waveform,
            sample_rate=sample_rate,
            channels=channels,
            timestamp=ts,
            metadata=metadata,
            session_id=self._session_id,
            source_id=source_id,
        )
        self._ingest(inp)
        return inp

    def receive_video(
        self,
        frames: list,
        resolution: tuple,
        source_id: str = "unknown",
        metadata: dict | None = None,
    ) -> VideoInput:
        """Acquire raw video frames."""
        InputValidator.validate_video(frames, resolution)
        ts = self._time.now()

        inp = VideoInput(
            data=frames,
            resolution=resolution,
            timestamp=ts,
            metadata=metadata,
            session_id=self._session_id,
            source_id=source_id,
        )
        self._ingest(inp)
        return inp

    def receive_physiological(
        self,
        signal_dict: dict,
        signal_type: str,
        sampling_frequency: float,
        source_id: str = "unknown",
        metadata: dict | None = None,
    ) -> PhysiologicalInput:
        """Acquire a raw physiological signal."""
        InputValidator.validate_physiological(signal_dict, signal_type, sampling_frequency)
        ts = self._time.now()

        inp = PhysiologicalInput(
            data=signal_dict,
            signal_type=signal_type,
            sampling_frequency=sampling_frequency,
            timestamp=ts,
            metadata=metadata,
            session_id=self._session_id,
            source_id=source_id,
        )
        self._ingest(inp)
        return inp

    # --- Retrieval methods ---

    def get_latest(self, n: int = 1) -> list:
        return self._buffer.get_latest(n)

    def get_all(self) -> list:
        return self._buffer.get_all()

    def get_by_modality(self, modality: str) -> list:
        return self._buffer.get_by_modality(modality)

    def get_by_id(self, input_id: str):
        return self._buffer.get_by_id(input_id)

    def get_by_time_range(self, start: float, end: float) -> list:
        return self._buffer.get_by_time_range(start, end)

    def replay(self) -> list:
        return self._buffer.replay()

    def clear_buffer(self):
        self._buffer.clear()

    # --- Internal ---

    def _ingest(self, raw_input):
        """Buffer, log, and count a validated input."""
        InputValidator.validate_integrity(raw_input)
        self._buffer.append(raw_input)
        self._logger.log(raw_input)
        self._total_received += 1

    def stats(self) -> dict:
        """Return a summary of acquisition statistics."""
        return {
            "session_id": self._session_id,
            "total_received": self._total_received,
            "buffer_size": self._buffer.size,
            "buffer_capacity": self._buffer.capacity,
            "counts_by_modality": self._logger.counts_by_modality,
            "time_mode": self._time.mode.value,
            "current_time": self._time.now(),
        }

    def __repr__(self) -> str:
        return (
            f"InputAcquisitionManager(session={self._session_id}, "
            f"received={self._total_received}, buffer={self._buffer.size})"
        )
