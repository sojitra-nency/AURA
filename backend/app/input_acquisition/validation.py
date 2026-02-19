"""
Validation and integrity checks for raw inputs.

Performs structural validation only — no interpretation,
no feature extraction, no semantic analysis.
"""

from app.input_acquisition.raw_input import VALID_MODALITIES


class ValidationError(Exception):
    """Raised when an input fails structural validation."""

    def __init__(self, message: str, modality: str | None = None):
        self.modality = modality
        super().__init__(message)


class InputValidator:
    """
    Stateless validator for raw input signals.

    All methods are classmethods — no instance state needed.
    Each returns True on success or raises ValidationError.
    """

    # Maximum sizes to reject obviously corrupted / absurd payloads
    MAX_TEXT_LENGTH = 10_000_000        # 10M characters
    MAX_AUDIO_SAMPLES = 500_000_000     # ~2.9 hours at 48kHz
    MAX_VIDEO_FRAMES = 100_000          # ~55 min at 30fps
    MAX_PHYSIO_SAMPLES = 100_000_000    # per channel

    @classmethod
    def validate_modality(cls, modality: str) -> bool:
        if modality not in VALID_MODALITIES:
            raise ValidationError(
                f"Unknown modality '{modality}'. Valid: {sorted(VALID_MODALITIES)}",
                modality=modality,
            )
        return True

    @classmethod
    def validate_not_empty(cls, data, modality: str) -> bool:
        if data is None:
            raise ValidationError("Data is None", modality=modality)
        if isinstance(data, (str, list, dict)) and len(data) == 0:
            raise ValidationError("Data is empty", modality=modality)
        return True

    @classmethod
    def validate_type(cls, data, expected_type: type, modality: str) -> bool:
        if not isinstance(data, expected_type):
            raise ValidationError(
                f"Expected {expected_type.__name__}, got {type(data).__name__}",
                modality=modality,
            )
        return True

    @classmethod
    def validate_text(cls, data) -> bool:
        cls.validate_type(data, str, "text")
        cls.validate_not_empty(data, "text")
        if len(data) > cls.MAX_TEXT_LENGTH:
            raise ValidationError(
                f"Text exceeds max length ({len(data)} > {cls.MAX_TEXT_LENGTH})",
                modality="text",
            )
        return True

    @classmethod
    def validate_audio(cls, data, sample_rate: int, channels: int) -> bool:
        cls.validate_type(data, list, "audio")
        cls.validate_not_empty(data, "audio")
        if len(data) > cls.MAX_AUDIO_SAMPLES:
            raise ValidationError(
                f"Audio exceeds max samples ({len(data)} > {cls.MAX_AUDIO_SAMPLES})",
                modality="audio",
            )
        if not isinstance(sample_rate, int) or sample_rate <= 0:
            raise ValidationError(
                "sample_rate must be a positive integer", modality="audio"
            )
        if not isinstance(channels, int) or channels <= 0:
            raise ValidationError(
                "channels must be a positive integer", modality="audio"
            )
        # Spot-check that samples are numeric
        for i in range(0, min(len(data), 100), max(1, len(data) // 100)):
            if not isinstance(data[i], (int, float)):
                raise ValidationError(
                    f"Audio sample at index {i} is not numeric: {type(data[i]).__name__}",
                    modality="audio",
                )
        return True

    @classmethod
    def validate_video(cls, data, resolution: tuple) -> bool:
        cls.validate_type(data, list, "video")
        cls.validate_not_empty(data, "video")
        if len(data) > cls.MAX_VIDEO_FRAMES:
            raise ValidationError(
                f"Video exceeds max frames ({len(data)} > {cls.MAX_VIDEO_FRAMES})",
                modality="video",
            )
        if (
            not isinstance(resolution, (tuple, list))
            or len(resolution) != 2
            or not all(isinstance(v, int) and v > 0 for v in resolution)
        ):
            raise ValidationError(
                "resolution must be (width, height) of positive ints",
                modality="video",
            )
        return True

    @classmethod
    def validate_physiological(
        cls, data: dict, signal_type: str, sampling_frequency: float
    ) -> bool:
        cls.validate_type(data, dict, "physiological")
        cls.validate_not_empty(data, "physiological")
        if not isinstance(signal_type, str) or len(signal_type) == 0:
            raise ValidationError(
                "signal_type must be a non-empty string",
                modality="physiological",
            )
        if not isinstance(sampling_frequency, (int, float)) or sampling_frequency <= 0:
            raise ValidationError(
                "sampling_frequency must be a positive number",
                modality="physiological",
            )
        for key, values in data.items():
            if not isinstance(values, list):
                raise ValidationError(
                    f"Channel '{key}' must be a list of samples",
                    modality="physiological",
                )
            if len(values) > cls.MAX_PHYSIO_SAMPLES:
                raise ValidationError(
                    f"Channel '{key}' exceeds max samples",
                    modality="physiological",
                )
        return True

    @classmethod
    def validate_timestamp(cls, timestamp) -> bool:
        if not isinstance(timestamp, (int, float)):
            raise ValidationError("Timestamp must be numeric")
        if timestamp < 0:
            raise ValidationError("Timestamp must be non-negative")
        return True

    @classmethod
    def validate_integrity(cls, raw_input) -> bool:
        """Verify that a RawInput object has not been corrupted."""
        if not hasattr(raw_input, "verify_integrity"):
            raise ValidationError("Object does not support integrity verification")
        if not raw_input.verify_integrity():
            raise ValidationError(
                f"Integrity check failed for input {raw_input.id}",
                modality=raw_input.modality,
            )
        return True
