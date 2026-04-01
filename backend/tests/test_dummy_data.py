"""
Tests for the dummy data generator and its integration with
InputAcquisitionManager.

Validates:
  - Correct structure and count for each modality
  - Value ranges (audio clamped, pixel bounds, physio ranges)
  - Full determinism (two identical runs produce identical output)
  - Bulk generation at 1,000+ scale
  - End-to-end ingestion through the manager
  - Replay correctness after bulk ingestion
  - Buffer integrity after stress load
"""

import sys
import os
import unittest
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tests.dummy_data import (
    generate_text_samples,
    generate_audio_samples,
    generate_video_samples,
    generate_physiological_samples,
    generate_all,
    generate_bulk_inputs,
    feed_into_manager,
)
from app.input_acquisition.manager import InputAcquisitionManager
from app.input_acquisition.time_manager import TimeManager, TimeMode
from app.input_acquisition.buffer import InputBuffer
from app.input_acquisition.logger import InputLogger


# ===================================================================
# 1. Text samples
# ===================================================================


class TestTextGeneration(unittest.TestCase):

    def test_count(self):
        samples = generate_text_samples(20)
        self.assertEqual(len(samples), 20)

    def test_type(self):
        for s in generate_text_samples(20):
            self.assertIsInstance(s, str)
            self.assertGreater(len(s), 0)

    def test_determinism(self):
        a = generate_text_samples(20)
        b = generate_text_samples(20)
        self.assertEqual(a, b)

    def test_custom_count(self):
        self.assertEqual(len(generate_text_samples(5)), 5)
        self.assertEqual(len(generate_text_samples(100)), 100)


# ===================================================================
# 2. Audio samples
# ===================================================================


class TestAudioGeneration(unittest.TestCase):

    def test_count(self):
        samples = generate_audio_samples(5)
        self.assertEqual(len(samples), 5)

    def test_waveform_length(self):
        for s in generate_audio_samples(5, waveform_length=1000):
            self.assertEqual(len(s["waveform"]), 1000)

    def test_waveform_range(self):
        for s in generate_audio_samples(5):
            for val in s["waveform"]:
                self.assertGreaterEqual(val, -1.0)
                self.assertLessEqual(val, 1.0)

    def test_sample_rate_valid(self):
        for s in generate_audio_samples(5):
            self.assertIn(s["sample_rate"], [16000, 44100])

    def test_waveform_is_list_of_floats(self):
        for s in generate_audio_samples(3):
            self.assertIsInstance(s["waveform"], list)
            for val in s["waveform"][:50]:
                self.assertIsInstance(val, float)

    def test_determinism(self):
        a = generate_audio_samples(5)
        b = generate_audio_samples(5)
        self.assertEqual(a, b)


# ===================================================================
# 3. Video samples
# ===================================================================


class TestVideoGeneration(unittest.TestCase):

    def test_count(self):
        samples = generate_video_samples(3)
        self.assertEqual(len(samples), 3)

    def test_frame_count(self):
        for s in generate_video_samples(3, frames_per_video=10):
            self.assertEqual(len(s["frames"]), 10)

    def test_resolution(self):
        samples = generate_video_samples(2, width=8, height=8)
        for s in samples:
            self.assertEqual(s["resolution"], (8, 8))
            frame = s["frames"][0]
            self.assertEqual(len(frame), 8)       # height rows
            self.assertEqual(len(frame[0]), 8)     # width cols
            self.assertEqual(len(frame[0][0]), 3)  # RGB

    def test_pixel_range(self):
        for s in generate_video_samples(2, width=4, height=4):
            for frame in s["frames"]:
                for row in frame:
                    for pixel in row:
                        for channel in pixel:
                            self.assertIsInstance(channel, int)
                            self.assertGreaterEqual(channel, 0)
                            self.assertLessEqual(channel, 255)

    def test_determinism(self):
        a = generate_video_samples(3)
        b = generate_video_samples(3)
        self.assertEqual(a, b)


# ===================================================================
# 4. Physiological samples
# ===================================================================


class TestPhysiologicalGeneration(unittest.TestCase):

    def test_count(self):
        samples = generate_physiological_samples(10)
        self.assertEqual(len(samples), 10)

    def test_structure(self):
        for s in generate_physiological_samples(10):
            self.assertIn("signals", s)
            self.assertIn("sampling_rate", s)
            sig = s["signals"]
            self.assertIn("heart_rate", sig)
            self.assertIn("skin_temp", sig)
            self.assertIn("eda", sig)

    def test_heart_rate_range(self):
        for s in generate_physiological_samples(10):
            for val in s["signals"]["heart_rate"]:
                self.assertGreaterEqual(val, 55.0)   # base-drift can nudge slightly
                self.assertLessEqual(val, 105.0)

    def test_skin_temp_range(self):
        for s in generate_physiological_samples(10):
            for val in s["signals"]["skin_temp"]:
                self.assertGreaterEqual(val, 34.5)
                self.assertLessEqual(val, 38.5)

    def test_eda_range(self):
        for s in generate_physiological_samples(10):
            for val in s["signals"]["eda"]:
                self.assertGreaterEqual(val, 0.0)
                self.assertLessEqual(val, 1.5)

    def test_sub_sample_count(self):
        for s in generate_physiological_samples(10):
            self.assertEqual(len(s["signals"]["heart_rate"]), 10)
            self.assertEqual(len(s["signals"]["skin_temp"]), 10)
            self.assertEqual(len(s["signals"]["eda"]), 10)

    def test_sampling_rate(self):
        for s in generate_physiological_samples(10):
            self.assertEqual(s["sampling_rate"], 10)

    def test_determinism(self):
        a = generate_physiological_samples(10)
        b = generate_physiological_samples(10)
        self.assertEqual(a, b)


# ===================================================================
# 5. Combined generate_all()
# ===================================================================


class TestGenerateAll(unittest.TestCase):

    def test_keys(self):
        data = generate_all()
        self.assertEqual(set(data.keys()), {"text", "audio", "video", "physiological"})

    def test_counts(self):
        data = generate_all()
        self.assertEqual(len(data["text"]), 20)
        self.assertEqual(len(data["audio"]), 5)
        self.assertEqual(len(data["video"]), 3)
        self.assertEqual(len(data["physiological"]), 10)

    def test_determinism(self):
        a = generate_all()
        b = generate_all()
        self.assertEqual(a, b)


# ===================================================================
# 6. Bulk generator
# ===================================================================


class TestBulkGenerator(unittest.TestCase):

    def test_count(self):
        bulk = generate_bulk_inputs(1000)
        self.assertEqual(len(bulk), 1000)

    def test_all_modalities_present(self):
        bulk = generate_bulk_inputs(1000)
        modalities = {e["modality"] for e in bulk}
        self.assertEqual(modalities, {"text", "audio", "video", "physiological"})

    def test_structure(self):
        for entry in generate_bulk_inputs(50):
            self.assertIn("modality", entry)
            self.assertIn("data", entry)
            self.assertIn("kwargs", entry)

    def test_text_entries_are_strings(self):
        for entry in generate_bulk_inputs(200):
            if entry["modality"] == "text":
                self.assertIsInstance(entry["data"], str)
                self.assertGreater(len(entry["data"]), 0)

    def test_audio_entries_valid(self):
        for entry in generate_bulk_inputs(200):
            if entry["modality"] == "audio":
                self.assertIsInstance(entry["data"], list)
                self.assertIn("sample_rate", entry["kwargs"])
                for val in entry["data"]:
                    self.assertGreaterEqual(val, -1.0)
                    self.assertLessEqual(val, 1.0)

    def test_video_entries_valid(self):
        for entry in generate_bulk_inputs(200):
            if entry["modality"] == "video":
                self.assertIsInstance(entry["data"], list)
                self.assertIn("resolution", entry["kwargs"])

    def test_physio_entries_valid(self):
        for entry in generate_bulk_inputs(200):
            if entry["modality"] == "physiological":
                self.assertIsInstance(entry["data"], dict)
                self.assertIn("signal_type", entry["kwargs"])
                self.assertIn("sampling_frequency", entry["kwargs"])

    def test_determinism(self):
        a = generate_bulk_inputs(500)
        b = generate_bulk_inputs(500)
        for x, y in zip(a, b):
            self.assertEqual(x["modality"], y["modality"])
            self.assertEqual(x["data"], y["data"])
            self.assertEqual(x["kwargs"], y["kwargs"])

    def test_determinism_full_1000(self):
        a = generate_bulk_inputs(1000)
        b = generate_bulk_inputs(1000)
        self.assertTrue(
            all(
                x["modality"] == y["modality"] and x["data"] == y["data"]
                for x, y in zip(a, b)
            )
        )


# ===================================================================
# 7. Integration: feed_into_manager
# ===================================================================


class TestManagerIntegration(unittest.TestCase):

    def _make_manager(self, capacity=5000):
        tm = TimeManager(mode=TimeMode.SIMULATED, start_time=0.0)
        tm.tick_delta = 0.01
        buf = InputBuffer(capacity=capacity)
        logger = InputLogger(max_entries=10000)
        return InputAcquisitionManager(
            time_manager=tm, buffer=buf, logger=logger, session_id="dummy-test"
        )

    def test_feed_all_modalities(self):
        """Feed the structured generate_all() output through the manager."""
        mgr = self._make_manager()
        data = generate_all()

        for text in data["text"]:
            mgr.time_manager.tick()
            mgr.receive_text(text)

        for audio in data["audio"]:
            mgr.time_manager.tick()
            mgr.receive_audio(audio["waveform"], sample_rate=audio["sample_rate"])

        for video in data["video"]:
            mgr.time_manager.tick()
            mgr.receive_video(video["frames"], resolution=video["resolution"])

        for physio in data["physiological"]:
            mgr.time_manager.tick()
            mgr.receive_physiological(
                physio["signals"],
                signal_type="biometric",
                sampling_frequency=float(physio["sampling_rate"]),
            )

        expected = 20 + 5 + 3 + 10
        self.assertEqual(mgr.total_received, expected)

        # Modality counts
        stats = mgr.stats()
        self.assertEqual(stats["counts_by_modality"]["text"], 20)
        self.assertEqual(stats["counts_by_modality"]["audio"], 5)
        self.assertEqual(stats["counts_by_modality"]["video"], 3)
        self.assertEqual(stats["counts_by_modality"]["physiological"], 10)

    def test_bulk_feed_1000(self):
        """Stress test: 1,000 mixed inputs through the manager."""
        mgr = self._make_manager(capacity=2000)
        bulk = generate_bulk_inputs(1000)
        created = feed_into_manager(mgr, bulk)

        self.assertEqual(len(created), 1000)
        self.assertEqual(mgr.total_received, 1000)
        self.assertEqual(mgr.buffer.size, 1000)

        # Integrity check on every buffered input
        for inp in mgr.get_all():
            self.assertTrue(inp.verify_integrity())

    def test_bulk_feed_2000(self):
        """Stress test at 2× scale."""
        mgr = self._make_manager(capacity=3000)
        bulk = generate_bulk_inputs(2000, seed=99)
        created = feed_into_manager(mgr, bulk)

        self.assertEqual(len(created), 2000)
        self.assertEqual(mgr.total_received, 2000)

    def test_replay_after_bulk(self):
        """Replay returns inputs in correct insertion order."""
        mgr = self._make_manager(capacity=1500)
        bulk = generate_bulk_inputs(1000)
        created = feed_into_manager(mgr, bulk)

        replayed = mgr.replay()
        self.assertEqual(len(replayed), 1000)

        # Verify order matches
        for original, replayed_inp in zip(created, replayed):
            self.assertEqual(original.id, replayed_inp.id)
            self.assertEqual(original.modality, replayed_inp.modality)

    def test_buffer_eviction_under_bulk(self):
        """Buffer capacity < bulk count → oldest evicted, newest retained."""
        mgr = self._make_manager(capacity=200)
        bulk = generate_bulk_inputs(1000)
        created = feed_into_manager(mgr, bulk)

        self.assertEqual(mgr.buffer.size, 200)
        self.assertEqual(mgr.total_received, 1000)

        # Last 200 IDs should be in buffer
        last_200_ids = {c.id for c in created[-200:]}
        buffered_ids = {inp.id for inp in mgr.get_all()}
        self.assertEqual(last_200_ids, buffered_ids)

    def test_modality_separation_after_bulk(self):
        """After bulk ingestion, modality queries return correct subsets."""
        mgr = self._make_manager(capacity=2000)
        bulk = generate_bulk_inputs(500)
        feed_into_manager(mgr, bulk)

        expected_counts = {}
        for entry in bulk:
            expected_counts[entry["modality"]] = expected_counts.get(entry["modality"], 0) + 1

        for modality, count in expected_counts.items():
            retrieved = mgr.get_by_modality(modality)
            self.assertEqual(
                len(retrieved), count,
                f"Modality '{modality}': expected {count}, got {len(retrieved)}"
            )

    def test_timestamps_monotonic_in_simulated_mode(self):
        """With simulated time + tick, all timestamps increase."""
        mgr = self._make_manager(capacity=500)
        bulk = generate_bulk_inputs(100)

        for entry in bulk:
            mgr.time_manager.tick()
            mod = entry["modality"]
            data = entry["data"]
            kw = entry["kwargs"]
            if mod == "text":
                mgr.receive_text(data)
            elif mod == "audio":
                mgr.receive_audio(data, **kw)
            elif mod == "video":
                mgr.receive_video(data, **kw)
            elif mod == "physiological":
                mgr.receive_physiological(data, **kw)

        all_inputs = mgr.get_all()
        timestamps = [inp.timestamp for inp in all_inputs]
        for i in range(1, len(timestamps)):
            self.assertGreaterEqual(
                timestamps[i], timestamps[i - 1],
                f"Timestamp regression at index {i}: {timestamps[i]} < {timestamps[i-1]}"
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
