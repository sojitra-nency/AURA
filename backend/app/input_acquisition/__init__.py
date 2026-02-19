"""
AURA Phase 1 — Input Acquisition Layer

Sensory interface for acquiring raw multi-modal signals.
No feature extraction. No inference. No interpretation.
"""

from app.input_acquisition.raw_input import (
    RawInput,
    TextInput,
    AudioInput,
    VideoInput,
    PhysiologicalInput,
)
from app.input_acquisition.time_manager import TimeManager
from app.input_acquisition.buffer import InputBuffer
from app.input_acquisition.validation import InputValidator
from app.input_acquisition.logger import InputLogger
from app.input_acquisition.manager import InputAcquisitionManager

__all__ = [
    "RawInput",
    "TextInput",
    "AudioInput",
    "VideoInput",
    "PhysiologicalInput",
    "TimeManager",
    "InputBuffer",
    "InputValidator",
    "InputLogger",
    "InputAcquisitionManager",
]
