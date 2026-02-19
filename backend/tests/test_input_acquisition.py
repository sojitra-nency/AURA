"""
Comprehensive test suite for AURA Phase 1 — Input Acquisition.

Tests:
  - Correct ID assignment and uniqueness
  - Correct timestamping (simulated mode for determinism)
  - Buffer overflow / FIFO eviction
  - Modality separation
  - Replay correctness
  - Deterministic behavior
  - Immutability (no mutation of raw data)
  - Validation rejection of bad inputs
  - Integrity checks
  - 1,000+ input stress test
"""

import sys
import os
import unittest
import math

# Ensure the backend package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.input_acquisition.raw_input import (
    RawInput,
    TextInput,
    AudioInput,
    VideoInput,
    PhysiologicalInput,
    VALID_MODALITIES,
)
from app.input_acquisition.time_manager import TimeManager, TimeMode
from app.input_acquisition.buffer import InputBuffer
from app.input_acquisition.validation import InputValidator, ValidationError
from app.input_acquisition.logger import InputLogger
from app.input_acquisition.manager import InputAcquisitionManager


# ===================================================================
# 1. RawInput base class tests
# ===================================================================


class TestRawInput(unittest.TestCase):

    def test_creation_basic(self):
        inp = RawInput("text", "hello", 1.0)
        self.assertEqual(inp.modality, "text")
        self.assertEqual(inp.data, "hello")
        self.assertEqual(inp.timestamp, 1.0)
        self.assertIsInstance(inp.id, str)
        self.assertEqual(len(inp.id), 32)  # uuid4 hex

    def test_unique_ids(self):
        ids = set()
        for _ in range(500):
            inp = RawInput("text", "data", 0.0)
            self.assertNotIn(inp.id, ids)
            ids.add(inp.id)

    def test_immutability_setattr(self):
        inp = RawInput("text", "data", 0.0)
        with self.assertRaises(AttributeError):
            inp._data = "mutated"

    def test_immutability_delattr(self):
        inp = RawInput("text", "data", 0.0)
        with self.assertRaises(AttributeError):
            del inp._data

    def test_data_deep_copy(self):
        original = [1, 2, [3, 4]]
        inp = RawInput("audio", original, 0.0)
        original[2].append(5)
        self.assertEqual(inp.data, [1, 2, [3, 4]])  # unaffected

    def test_data_property_returns_copy(self):
        inp = RawInput("audio", [1, 2, 3], 0.0)
        d1 = inp.data
        d1.append(999)
        self.assertEqual(inp.data, [1, 2, 3])  # still original

    def test_checksum_deterministic(self):
        inp = RawInput("text", "same data", 0.0)
        self.assertEqual(inp.checksum, inp.checksum)

    def test_integrity_verification(self):
        inp = RawInput("text", "test", 1.0)
        self.assertTrue(inp.verify_integrity())

    def test_to_dict(self):
        inp = RawInput("text", "hello", 5.0, session_id="s1", source_id="src1")
        d = inp.to_dict()
        self.assertEqual(d["modality"], "text")
        self.assertEqual(d["timestamp"], 5.0)
        self.assertEqual(d["session_id"], "s1")
        self.assertEqual(d["source_id"], "src1")
        self.assertIn("checksum", d)

    def test_invalid_modality(self):
        with self.assertRaises(ValueError):
            RawInput("smell", "data", 0.0)

    def test_none_data(self):
        with self.assertRaises(ValueError):
            RawInput("text", None, 0.0)

    def test_invalid_timestamp_type(self):
        with self.assertRaises(TypeError):
            RawInput("text", "data", "not a number")

    def test_default_session_and_source(self):
        inp = RawInput("text", "data", 0.0)
        self.assertEqual(inp.session_id, "default")
        self.assertEqual(inp.source_id, "unknown")

    def test_metadata_isolation(self):
        meta = {"key": "value"}
        inp = RawInput("text", "data", 0.0, metadata=meta)
        meta["key"] = "changed"
        self.assertEqual(inp.metadata["key"], "value")


# ===================================================================
# 2. TextInput tests
# ===================================================================


class TestTextInput(unittest.TestCase):

    def test_creation(self):
        inp = TextInput("hello world", 1.0)
        self.assertEqual(inp.modality, "text")
        self.assertEqual(inp.data, "hello world")
        self.assertEqual(inp.metadata["char_count"], 11)
        self.assertEqual(inp.metadata["encoding"], "utf-8")

    def test_rejects_non_string(self):
        with self.assertRaises(TypeError):
            TextInput(12345, 1.0)

    def test_rejects_empty_string(self):
        with self.assertRaises(ValueError):
            TextInput("", 1.0)

    def test_unicode(self):
        inp = TextInput("日本語テスト", 1.0)
        self.assertEqual(inp.metadata["char_count"], 6)


# ===================================================================
# 3. AudioInput tests
# ===================================================================


class TestAudioInput(unittest.TestCase):

    def test_creation(self):
        waveform = [0.1, -0.2, 0.3]
        inp = AudioInput(waveform, sample_rate=44100, timestamp=2.0)
        self.assertEqual(inp.modality, "audio")
        self.assertEqual(inp.metadata["sample_rate"], 44100)
        self.assertEqual(inp.metadata["channels"], 1)
        self.assertEqual(inp.metadata["sample_count"], 3)

    def test_duration_calculation(self):
        waveform = [0.0] * 44100
        inp = AudioInput(waveform, sample_rate=44100, timestamp=0.0)
        self.assertAlmostEqual(inp.metadata["duration_seconds"], 1.0)

    def test_rejects_non_list(self):
        with self.assertRaises(TypeError):
            AudioInput("not a list", sample_rate=44100, timestamp=0.0)

    def test_rejects_empty(self):
        with self.assertRaises(ValueError):
            AudioInput([], sample_rate=44100, timestamp=0.0)

    def test_rejects_invalid_sample_rate(self):
        with self.assertRaises(ValueError):
            AudioInput([0.1], sample_rate=-1, timestamp=0.0)

    def test_stereo(self):
        waveform = [0.0] * 88200
        inp = AudioInput(waveform, sample_rate=44100, channels=2, timestamp=0.0)
        self.assertAlmostEqual(inp.metadata["duration_seconds"], 1.0)


# ===================================================================
# 4. VideoInput tests
# ===================================================================


class TestVideoInput(unittest.TestCase):

    def test_creation(self):
        frames = [[[0, 0, 0]]] * 30
        inp = VideoInput(frames, resolution=(1920, 1080), timestamp=0.0)
        self.assertEqual(inp.modality, "video")
        self.assertEqual(inp.metadata["frame_count"], 30)
        self.assertEqual(inp.metadata["resolution_width"], 1920)
        self.assertEqual(inp.metadata["resolution_height"], 1080)

    def test_rejects_non_list(self):
        with self.assertRaises(TypeError):
            VideoInput("not frames", resolution=(640, 480), timestamp=0.0)

    def test_rejects_bad_resolution(self):
        with self.assertRaises(ValueError):
            VideoInput([[1]], resolution=(0, 480), timestamp=0.0)
        with self.assertRaises(ValueError):
            VideoInput([[1]], resolution=(640,), timestamp=0.0)


# ===================================================================
# 5. PhysiologicalInput tests
# ===================================================================


class TestPhysiologicalInput(unittest.TestCase):

    def test_creation(self):
        data = {"heart_rate": [72, 73, 71], "gsr": [0.5, 0.6, 0.55]}
        inp = PhysiologicalInput(
            data, signal_type="biometric", sampling_frequency=1.0, timestamp=0.0
        )
        self.assertEqual(inp.modality, "physiological")
        self.assertEqual(inp.metadata["signal_type"], "biometric")
        self.assertIn("heart_rate", inp.metadata["channel_names"])

    def test_rejects_non_dict(self):
        with self.assertRaises(TypeError):
            PhysiologicalInput([1, 2], signal_type="x", sampling_frequency=1.0)

    def test_rejects_empty(self):
        with self.assertRaises(ValueError):
            PhysiologicalInput({}, signal_type="x", sampling_frequency=1.0)

    def test_rejects_bad_signal_type(self):
        with self.assertRaises(ValueError):
            PhysiologicalInput({"a": [1]}, signal_type="", sampling_frequency=1.0)

    def test_rejects_bad_frequency(self):
        with self.assertRaises(ValueError):
            PhysiologicalInput({"a": [1]}, signal_type="x", sampling_frequency=-5)


# ===================================================================
# 6. TimeManager tests
# ===================================================================


class TestTimeManager(unittest.TestCase):

    def test_simulated_deterministic(self):
        tm = TimeManager(mode=TimeMode.SIMULATED, start_time=0.0)
        self.assertEqual(tm.now(), 0.0)
        tm.tick()
        self.assertEqual(tm.now(), 1.0)
        tm.tick()
        self.assertEqual(tm.now(), 2.0)

    def test_simulated_custom_delta(self):
        tm = TimeManager(mode=TimeMode.SIMULATED, start_time=100.0)
        tm.tick_delta = 0.5
        tm.tick()
        self.assertEqual(tm.now(), 100.5)

    def test_simulated_tick_with_arg(self):
        tm = TimeManager(mode=TimeMode.SIMULATED, start_time=0.0)
        tm.tick(delta=3.5)
        self.assertEqual(tm.now(), 3.5)

    def test_simulated_reset(self):
        tm = TimeManager(mode=TimeMode.SIMULATED, start_time=0.0)
        tm.tick()
        tm.tick()
        tm.reset(10.0)
        self.assertEqual(tm.now(), 10.0)
        self.assertEqual(tm.tick_count, 0)

    def test_real_mode_returns_float(self):
        tm = TimeManager(mode=TimeMode.REAL)
        t = tm.now()
        self.assertIsInstance(t, float)
        self.assertGreater(t, 0)

    def test_tick_count(self):
        tm = TimeManager(mode=TimeMode.SIMULATED)
        for _ in range(10):
            tm.tick()
        self.assertEqual(tm.tick_count, 10)

    def test_invalid_mode(self):
        with self.assertRaises(TypeError):
            TimeManager(mode="not_a_mode")

    def test_invalid_tick_delta(self):
        tm = TimeManager(mode=TimeMode.SIMULATED)
        with self.assertRaises(ValueError):
            tm.tick_delta = -1


# ===================================================================
# 7. InputBuffer tests
# ===================================================================


class TestInputBuffer(unittest.TestCase):

    def test_append_and_retrieve(self):
        buf = InputBuffer(capacity=10)
        inp = RawInput("text", "hello", 1.0)
        buf.append(inp)
        self.assertEqual(buf.size, 1)
        self.assertIs(buf.get_by_id(inp.id), inp)

    def test_fifo_eviction(self):
        buf = InputBuffer(capacity=3)
        inputs = []
        for i in range(5):
            inp = RawInput("text", f"msg-{i}", float(i))
            buf.append(inp)
            inputs.append(inp)
        self.assertEqual(buf.size, 3)
        self.assertIsNone(buf.get_by_id(inputs[0].id))
        self.assertIsNone(buf.get_by_id(inputs[1].id))
        self.assertIsNotNone(buf.get_by_id(inputs[2].id))
        self.assertIsNotNone(buf.get_by_id(inputs[3].id))
        self.assertIsNotNone(buf.get_by_id(inputs[4].id))

    def test_eviction_returns_id(self):
        buf = InputBuffer(capacity=2)
        i1 = RawInput("text", "a", 0.0)
        i2 = RawInput("text", "b", 1.0)
        i3 = RawInput("text", "c", 2.0)
        self.assertIsNone(buf.append(i1))
        self.assertIsNone(buf.append(i2))
        evicted = buf.append(i3)
        self.assertEqual(evicted, i1.id)

    def test_get_by_modality(self):
        buf = InputBuffer()
        buf.append(RawInput("text", "t", 0.0))
        buf.append(RawInput("audio", [1], 1.0))
        buf.append(RawInput("text", "t2", 2.0))
        texts = buf.get_by_modality("text")
        self.assertEqual(len(texts), 2)
        audios = buf.get_by_modality("audio")
        self.assertEqual(len(audios), 1)

    def test_get_by_time_range(self):
        buf = InputBuffer()
        for i in range(10):
            buf.append(RawInput("text", f"m{i}", float(i)))
        results = buf.get_by_time_range(3.0, 6.0)
        self.assertEqual(len(results), 4)

    def test_get_latest(self):
        buf = InputBuffer()
        for i in range(5):
            buf.append(RawInput("text", f"m{i}", float(i)))
        latest = buf.get_latest(2)
        self.assertEqual(len(latest), 2)
        self.assertEqual(latest[1].data, "m4")

    def test_clear(self):
        buf = InputBuffer()
        buf.append(RawInput("text", "x", 0.0))
        buf.clear()
        self.assertEqual(buf.size, 0)

    def test_replay_matches_get_all(self):
        buf = InputBuffer()
        for i in range(5):
            buf.append(RawInput("text", f"r{i}", float(i)))
        self.assertEqual(len(buf.replay()), len(buf.get_all()))

    def test_iteration_order(self):
        buf = InputBuffer()
        ids = []
        for i in range(10):
            inp = RawInput("text", f"d{i}", float(i))
            buf.append(inp)
            ids.append(inp.id)
        buf_ids = [inp.id for inp in buf]
        self.assertEqual(ids, buf_ids)

    def test_invalid_capacity(self):
        with self.assertRaises(ValueError):
            InputBuffer(capacity=0)
        with self.assertRaises(ValueError):
            InputBuffer(capacity=-5)

    def test_get_by_session(self):
        buf = InputBuffer()
        buf.append(RawInput("text", "a", 0.0, session_id="s1"))
        buf.append(RawInput("text", "b", 1.0, session_id="s2"))
        buf.append(RawInput("text", "c", 2.0, session_id="s1"))
        results = buf.get_by_session("s1")
        self.assertEqual(len(results), 2)


# ===================================================================
# 8. Validation tests
# ===================================================================


class TestValidation(unittest.TestCase):

    def test_valid_text(self):
        self.assertTrue(InputValidator.validate_text("hello"))

    def test_text_rejects_non_string(self):
        with self.assertRaises(ValidationError):
            InputValidator.validate_text(123)

    def test_text_rejects_empty(self):
        with self.assertRaises(ValidationError):
            InputValidator.validate_text("")

    def test_valid_audio(self):
        self.assertTrue(InputValidator.validate_audio([0.1, 0.2], 44100, 1))

    def test_audio_rejects_non_list(self):
        with self.assertRaises(ValidationError):
            InputValidator.validate_audio("wave", 44100, 1)

    def test_audio_rejects_bad_rate(self):
        with self.assertRaises(ValidationError):
            InputValidator.validate_audio([0.1], 0, 1)

    def test_audio_rejects_non_numeric_samples(self):
        with self.assertRaises(ValidationError):
            InputValidator.validate_audio(["a", "b"], 44100, 1)

    def test_valid_video(self):
        self.assertTrue(InputValidator.validate_video([[1]], (640, 480)))

    def test_video_rejects_bad_resolution(self):
        with self.assertRaises(ValidationError):
            InputValidator.validate_video([[1]], (0, 0))

    def test_valid_physiological(self):
        self.assertTrue(
            InputValidator.validate_physiological({"hr": [72]}, "biometric", 1.0)
        )

    def test_physio_rejects_empty(self):
        with self.assertRaises(ValidationError):
            InputValidator.validate_physiological({}, "x", 1.0)

    def test_valid_timestamp(self):
        self.assertTrue(InputValidator.validate_timestamp(1.0))

    def test_timestamp_rejects_negative(self):
        with self.assertRaises(ValidationError):
            InputValidator.validate_timestamp(-1.0)

    def test_timestamp_rejects_string(self):
        with self.assertRaises(ValidationError):
            InputValidator.validate_timestamp("now")

    def test_integrity_check(self):
        inp = RawInput("text", "data", 0.0)
        self.assertTrue(InputValidator.validate_integrity(inp))

    def test_modality_validation(self):
        self.assertTrue(InputValidator.validate_modality("text"))
        with self.assertRaises(ValidationError):
            InputValidator.validate_modality("smell")


# ===================================================================
# 9. InputLogger tests
# ===================================================================


class TestInputLogger(unittest.TestCase):

    def test_log_entry(self):
        logger = InputLogger()
        inp = RawInput("text", "hello", 1.0)
        entry = logger.log(inp)
        self.assertEqual(entry.input_id, inp.id)
        self.assertEqual(entry.modality, "text")
        self.assertEqual(len(logger), 1)

    def test_counts_by_modality(self):
        logger = InputLogger()
        logger.log(RawInput("text", "a", 0.0))
        logger.log(RawInput("text", "b", 1.0))
        logger.log(RawInput("audio", [1], 2.0))
        counts = logger.counts_by_modality
        self.assertEqual(counts["text"], 2)
        self.assertEqual(counts["audio"], 1)

    def test_filter_by_modality(self):
        logger = InputLogger()
        logger.log(RawInput("text", "a", 0.0))
        logger.log(RawInput("audio", [1], 1.0))
        texts = logger.get_entries(modality="text")
        self.assertEqual(len(texts), 1)

    def test_recent(self):
        logger = InputLogger()
        for i in range(20):
            logger.log(RawInput("text", f"m{i}", float(i)))
        recent = logger.get_recent(5)
        self.assertEqual(len(recent), 5)

    def test_clear(self):
        logger = InputLogger()
        logger.log(RawInput("text", "a", 0.0))
        logger.clear()
        self.assertEqual(len(logger), 0)
        self.assertEqual(logger.total_logged, 0)

    def test_max_entries_bounded(self):
        logger = InputLogger(max_entries=5)
        for i in range(10):
            logger.log(RawInput("text", f"m{i}", float(i)))
        self.assertEqual(len(logger), 5)

    def test_entry_to_dict(self):
        logger = InputLogger()
        inp = RawInput("text", "x", 3.0)
        entry = logger.log(inp)
        d = entry.to_dict()
        self.assertEqual(d["input_id"], inp.id)
        self.assertIn("data_size", d)


# ===================================================================
# 10. InputAcquisitionManager tests
# ===================================================================


class TestInputAcquisitionManager(unittest.TestCase):

    def _make_manager(self, capacity=100):
        tm = TimeManager(mode=TimeMode.SIMULATED, start_time=0.0)
        buf = InputBuffer(capacity=capacity)
        logger = InputLogger()
        return InputAcquisitionManager(
            time_manager=tm, buffer=buf, logger=logger, session_id="test"
        )

    def test_receive_text(self):
        mgr = self._make_manager()
        inp = mgr.receive_text("hello world")
        self.assertEqual(inp.modality, "text")
        self.assertEqual(inp.session_id, "test")
        self.assertEqual(mgr.total_received, 1)

    def test_receive_audio(self):
        mgr = self._make_manager()
        inp = mgr.receive_audio([0.1, 0.2, 0.3], sample_rate=16000)
        self.assertEqual(inp.modality, "audio")

    def test_receive_video(self):
        mgr = self._make_manager()
        inp = mgr.receive_video([[[0]]], resolution=(320, 240))
        self.assertEqual(inp.modality, "video")

    def test_receive_physiological(self):
        mgr = self._make_manager()
        inp = mgr.receive_physiological(
            {"hr": [72, 73]}, signal_type="ecg", sampling_frequency=256.0
        )
        self.assertEqual(inp.modality, "physiological")

    def test_timestamping_simulated(self):
        mgr = self._make_manager()
        t1 = mgr.receive_text("a")
        mgr.time_manager.tick(delta=5.0)
        t2 = mgr.receive_text("b")
        self.assertEqual(t1.timestamp, 0.0)
        self.assertEqual(t2.timestamp, 5.0)

    def test_get_latest(self):
        mgr = self._make_manager()
        mgr.receive_text("a")
        mgr.receive_text("b")
        mgr.receive_text("c")
        latest = mgr.get_latest(2)
        self.assertEqual(len(latest), 2)

    def test_get_by_modality(self):
        mgr = self._make_manager()
        mgr.receive_text("t")
        mgr.receive_audio([0.1], sample_rate=8000)
        texts = mgr.get_by_modality("text")
        self.assertEqual(len(texts), 1)

    def test_get_by_id(self):
        mgr = self._make_manager()
        inp = mgr.receive_text("find me")
        found = mgr.get_by_id(inp.id)
        self.assertEqual(found.id, inp.id)

    def test_get_by_time_range(self):
        mgr = self._make_manager()
        mgr.receive_text("a")
        mgr.time_manager.tick(5.0)
        mgr.receive_text("b")
        mgr.time_manager.tick(5.0)
        mgr.receive_text("c")
        results = mgr.get_by_time_range(4.0, 6.0)
        self.assertEqual(len(results), 1)

    def test_replay(self):
        mgr = self._make_manager()
        for i in range(5):
            mgr.receive_text(f"msg-{i}")
        replayed = mgr.replay()
        self.assertEqual(len(replayed), 5)
        self.assertEqual(replayed[0].data, "msg-0")

    def test_clear_buffer(self):
        mgr = self._make_manager()
        mgr.receive_text("a")
        mgr.clear_buffer()
        self.assertEqual(len(mgr.get_all()), 0)
        self.assertEqual(mgr.total_received, 1)  # counter preserved

    def test_stats(self):
        mgr = self._make_manager()
        mgr.receive_text("a")
        mgr.receive_audio([0.1], sample_rate=8000)
        s = mgr.stats()
        self.assertEqual(s["total_received"], 2)
        self.assertEqual(s["buffer_size"], 2)
        self.assertEqual(s["counts_by_modality"]["text"], 1)
        self.assertEqual(s["counts_by_modality"]["audio"], 1)

    def test_rejects_invalid_text(self):
        mgr = self._make_manager()
        with self.assertRaises((ValidationError, TypeError)):
            mgr.receive_text(12345)

    def test_rejects_empty_text(self):
        mgr = self._make_manager()
        with self.assertRaises((ValidationError, ValueError)):
            mgr.receive_text("")


# ===================================================================
# 11. Immutability stress tests
# ===================================================================


class TestImmutability(unittest.TestCase):

    def test_text_data_cannot_mutate(self):
        inp = TextInput("original", 0.0)
        d = inp.data
        self.assertEqual(d, "original")
        # Strings are inherently immutable, but verify property returns consistently
        self.assertEqual(inp.data, "original")

    def test_audio_data_cannot_mutate(self):
        original = [0.1, 0.2, 0.3]
        inp = AudioInput(original, sample_rate=8000, timestamp=0.0)
        original.append(0.4)  # mutate the source
        self.assertEqual(len(inp.data), 3)
        d = inp.data
        d.append(0.5)
        self.assertEqual(len(inp.data), 3)

    def test_video_data_cannot_mutate(self):
        frame = [[1, 2], [3, 4]]
        frames = [frame]
        inp = VideoInput(frames, resolution=(2, 2), timestamp=0.0)
        frame[0][0] = 999
        self.assertEqual(inp.data[0][0][0], 1)

    def test_physio_data_cannot_mutate(self):
        signals = {"hr": [72, 73, 74]}
        inp = PhysiologicalInput(
            signals, signal_type="ecg", sampling_frequency=1.0, timestamp=0.0
        )
        signals["hr"].append(999)
        self.assertEqual(len(inp.data["hr"]), 3)

    def test_metadata_cannot_mutate(self):
        inp = TextInput("test", 0.0, metadata={"custom": "value"})
        meta = inp.metadata
        meta["injected"] = "bad"
        self.assertNotIn("injected", inp.metadata)


# ===================================================================
# 12. Determinism tests
# ===================================================================


class TestDeterminism(unittest.TestCase):

    def test_simulated_time_fully_deterministic(self):
        """Two identical sequences produce identical timestamps."""
        results = []
        for _ in range(2):
            tm = TimeManager(mode=TimeMode.SIMULATED, start_time=0.0)
            tm.tick_delta = 0.25
            timestamps = []
            for _ in range(20):
                timestamps.append(tm.now())
                tm.tick()
            results.append(timestamps)
        self.assertEqual(results[0], results[1])

    def test_buffer_order_deterministic(self):
        """Insertion order is preserved identically across runs."""
        for _ in range(3):
            buf = InputBuffer(capacity=50)
            for i in range(50):
                buf.append(RawInput("text", f"d{i}", float(i)))
            data = [inp.data for inp in buf]
            expected = [f"d{i}" for i in range(50)]
            self.assertEqual(data, expected)

    def test_checksum_deterministic_across_instances(self):
        c1 = RawInput("text", "deterministic", 0.0).checksum
        c2 = RawInput("text", "deterministic", 0.0).checksum
        self.assertEqual(c1, c2)


# ===================================================================
# 13. Stress test — 1,000 input events
# ===================================================================


class TestStress(unittest.TestCase):

    def test_1000_mixed_inputs(self):
        """Ingest 1,000 inputs across all modalities without failure."""
        tm = TimeManager(mode=TimeMode.SIMULATED, start_time=0.0)
        tm.tick_delta = 0.01
        buf = InputBuffer(capacity=2000)
        logger = InputLogger()
        mgr = InputAcquisitionManager(
            time_manager=tm, buffer=buf, logger=logger, session_id="stress"
        )

        for i in range(1000):
            mod = i % 4
            tm.tick()
            if mod == 0:
                mgr.receive_text(f"stress text {i}")
            elif mod == 1:
                mgr.receive_audio(
                    [float(x) / 100 for x in range(100)],
                    sample_rate=16000,
                )
            elif mod == 2:
                mgr.receive_video(
                    [[[i % 256]]] * 5,
                    resolution=(64, 64),
                )
            else:
                mgr.receive_physiological(
                    {"ch1": [float(i), float(i + 1)]},
                    signal_type="synthetic",
                    sampling_frequency=100.0,
                )

        self.assertEqual(mgr.total_received, 1000)
        self.assertEqual(mgr.buffer.size, 1000)

        # Verify modality counts
        stats = mgr.stats()
        self.assertEqual(stats["counts_by_modality"]["text"], 250)
        self.assertEqual(stats["counts_by_modality"]["audio"], 250)
        self.assertEqual(stats["counts_by_modality"]["video"], 250)
        self.assertEqual(stats["counts_by_modality"]["physiological"], 250)

        # Verify all inputs pass integrity
        for inp in mgr.get_all():
            self.assertTrue(inp.verify_integrity())

        # Verify replay returns all 1000
        self.assertEqual(len(mgr.replay()), 1000)

    def test_buffer_overflow_at_scale(self):
        """Buffer correctly evicts when capacity < total inputs."""
        tm = TimeManager(mode=TimeMode.SIMULATED, start_time=0.0)
        buf = InputBuffer(capacity=100)
        logger = InputLogger(max_entries=2000)
        mgr = InputAcquisitionManager(
            time_manager=tm, buffer=buf, logger=logger, session_id="overflow"
        )

        ids_in_order = []
        for i in range(500):
            tm.tick()
            inp = mgr.receive_text(f"overflow-{i}")
            ids_in_order.append(inp.id)

        self.assertEqual(mgr.total_received, 500)
        self.assertEqual(mgr.buffer.size, 100)

        # Only the last 100 should remain
        buffered_ids = {inp.id for inp in mgr.get_all()}
        for old_id in ids_in_order[:400]:
            self.assertNotIn(old_id, buffered_ids)
        for new_id in ids_in_order[400:]:
            self.assertIn(new_id, buffered_ids)

        # Logger should have all 500 logged
        self.assertEqual(logger.total_logged, 500)


# ===================================================================
# 14. Architectural boundary tests
# ===================================================================


class TestArchitecturalBoundaries(unittest.TestCase):

    def test_no_perception_import(self):
        """Input acquisition must NOT import any perception module."""
        import app.input_acquisition as ia_mod
        import sys
        for mod_name in sys.modules:
            self.assertFalse(
                mod_name.startswith("app.perception"),
                f"Input acquisition imported perception module: {mod_name}",
            )

    def test_valid_modalities_is_frozen(self):
        self.assertIsInstance(VALID_MODALITIES, frozenset)

    def test_all_modalities_covered(self):
        expected = {"text", "audio", "video", "physiological"}
        self.assertEqual(VALID_MODALITIES, expected)


if __name__ == "__main__":
    unittest.main(verbosity=2)
