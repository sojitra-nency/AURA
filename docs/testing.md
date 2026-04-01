# Testing Guide

[Back to README](../README.md) | [Phase 1 Docs](phase-1-input-acquisition.md)

## Overview

All tests use Python's built-in `unittest` module — no pytest, no external test runners. This is consistent with the project's pure-Python constraint.

## Test Architecture

```
  Full Test Suite — 143 tests
  ═══════════════════════════

  test_input_acquisition.py — 101 tests
  ──────────────────────────────────────
    ├── RawInput Tests
    ├── Modality Tests (Text, Audio, Video, Physiological)
    ├── TimeManager Tests
    ├── Buffer Tests
    ├── Validation Tests
    ├── Logger Tests
    ├── Manager Tests
    ├── Immutability Tests
    ├── Determinism Tests
    ├── Stress Tests
    └── Architecture Tests

  test_dummy_data.py — 42 tests
  ──────────────────────────────
    ├── Generator Tests (Text, Audio, Video, Physiological)
    ├── Bulk Tests
    └── Integration Tests
```

## Running Tests

```bash
cd backend
source venv/Scripts/activate   # Windows (Git Bash)

# Run the full suite (all test files)
python -m unittest discover -s tests -v

# Run only Phase 1 unit tests
python -m unittest tests.test_input_acquisition -v

# Run only the dummy data generator + integration tests
python -m unittest tests.test_dummy_data -v

# Run a specific test class
python -m unittest tests.test_input_acquisition.TestRawInput -v

# Run a single test method
python -m unittest tests.test_input_acquisition.TestStress.test_1000_mixed_inputs -v
```

## Test Suite Breakdown

### test_input_acquisition.py — 101 tests

Phase 1 core unit tests organized into 14 test classes:

| Class | Tests | What it covers |
|-------|:-----:|----------------|
| `TestRawInput` | 14 | Base class creation, immutability, deep copy, checksum, validation |
| `TestTextInput` | 4 | Text validation, metadata, unicode, rejection |
| `TestAudioInput` | 6 | Waveform validation, duration calc, sample rate, stereo |
| `TestVideoInput` | 3 | Frame structure, resolution validation |
| `TestPhysiologicalInput` | 5 | Signal dict, type/frequency validation |
| `TestTimeManager` | 8 | REAL/SIMULATED modes, tick, reset, determinism |
| `TestInputBuffer` | 12 | FIFO eviction, retrieval by ID/modality/time/session, ordering |
| `TestValidation` | 15 | All validator methods, rejection of bad inputs, integrity |
| `TestInputLogger` | 7 | Log entries, modality counts, filtering, bounded deque |
| `TestInputAcquisitionManager` | 14 | All receive methods, retrieval, replay, stats, rejection |
| `TestImmutability` | 5 | Source mutation isolation for all 4 modalities + metadata |
| `TestDeterminism` | 3 | Timestamp sequences, buffer order, checksum reproducibility |
| `TestStress` | 2 | 1,000 mixed inputs; 500 inputs with buffer overflow |
| `TestArchitecturalBoundaries` | 3 | No perception imports, frozen modality set, coverage |

### test_dummy_data.py — 42 tests

Dummy data generator validation and manager integration:

| Class | Tests | What it covers |
|-------|:-----:|----------------|
| `TestTextGeneration` | 4 | Count, type, determinism, custom sizes |
| `TestAudioGeneration` | 6 | Count, waveform length, range [-1,1], rate, float type, determinism |
| `TestVideoGeneration` | 5 | Count, frame count, resolution, pixel range [0,255], determinism |
| `TestPhysiologicalGeneration` | 8 | Count, structure, HR/temp/EDA ranges, sub-samples, rate, determinism |
| `TestGenerateAll` | 3 | Combined output keys, counts, determinism |
| `TestBulkGenerator` | 9 | Count, modality coverage, entry structure, value validation, determinism at 1000 |
| `TestManagerIntegration` | 7 | End-to-end ingestion, 1000 and 2000 stress, replay, eviction, modality separation, timestamp monotonicity |

## What the Tests Verify

```
  Correctness                     Immutability
  ───────────                     ────────────
  [x] Unique IDs across 500+     [x] Source mutation doesn't affect input
  [x] Correct modality tagging   [x] Properties return copies
  [x] Accurate auto-metadata     [x] setattr / delattr blocked

  Determinism                     Integrity
  ───────────                     ─────────
  [x] Simulated time identical    [x] SHA-256 checksum validates
      across runs                 [x] All 1000 stress inputs pass
  [x] Buffer order identical
  [x] Checksums match across
      instances
  [x] Dummy data identical
      per seed

  Scale                           Architecture
  ─────                           ────────────
  [x] 1000 mixed inputs OK       [x] No perception imports
  [x] 2000 inputs OK             [x] VALID_MODALITIES is frozenset
  [x] Buffer overflow eviction
      correct
```

## Dummy Data Generator

Located at `tests/dummy_data.py`. Generates deterministic raw signals for all four modalities using a fixed random seed.

### Generator Flow

```
  seed=42
    │
    v
  Seeded RNG ──┬──> generate_text_samples(20)            ──┐
               ├──> generate_audio_samples(5)             ├──> generate_all()
               ├──> generate_video_samples(3)             │
               └──> generate_physiological_samples(10)  ──┘
               │
               └──> generate_bulk_inputs(n) ──> feed_into_manager(mgr, inputs)
```

### Quick usage

```python
from tests.dummy_data import generate_all, generate_bulk_inputs, feed_into_manager
from app.input_acquisition import InputAcquisitionManager, TimeManager, TimeMode

# Structured dataset
data = generate_all()
# data["text"]           → 20 raw strings
# data["audio"]          → 5 waveforms (1000 samples each)
# data["video"]          → 3 frame sequences (10 frames, 8x8 RGB)
# data["physiological"]  → 10 signal snapshots (HR, temp, EDA)

# Bulk mixed-modality inputs for stress testing
bulk = generate_bulk_inputs(1000)

# Feed directly into the manager
tm = TimeManager(mode=TimeMode.SIMULATED, start_time=0.0)
mgr = InputAcquisitionManager(time_manager=tm, session_id="test")
results = feed_into_manager(mgr, bulk)
```

### Generator functions

| Function | Default output | Seed offset |
|----------|---------------|:-----------:|
| `generate_text_samples(n=20)` | 20 human-like sentences | +0 |
| `generate_audio_samples(n=5, waveform_length=1000)` | 5 sine+noise waveforms | +1 |
| `generate_video_samples(n=3, frames=10, w=8, h=8)` | 3 RGB frame sequences | +2 |
| `generate_physiological_samples(n=10)` | 10 multi-channel snapshots | +3 |
| `generate_all()` | Combined dict of all above | per-function |
| `generate_bulk_inputs(n)` | n mixed entries (~40% text, 25% audio, 15% video, 20% physio) | +100 |

All functions accept a `seed` parameter (default `42`). Two calls with the same seed produce byte-identical output.

### Bulk distribution

```
  generate_bulk_inputs(1000) Distribution
  ─────────────────────────────────────────
  Text (393)           ████████████████████████████████████████  39.3%
  Audio (254)          ██████████████████████████               25.4%
  Physiological (205)  █████████████████████                    20.5%
  Video (148)          ███████████████                          14.8%
```

### Self-test

Run the generator directly to see sample output:

```bash
cd backend
python -m tests.dummy_data
```

Output:
```
--- Text (20 samples) ---
  [0] She feel general satisfaction with the process.
  [1] The patient noticed that the noise was distracting.
  ...

--- Audio (5 samples) ---
  [0] rate=16000  samples=1000  range=[-0.3481, 0.3474]
  ...

--- Video (3 samples) ---
  [0] frames=10  resolution=8x8  pixel_sample=[209, 59, 90]
  ...

--- Physiological (10 samples) ---
  [0] hr=70.8  temp=36.53  eda=0.325  rate=10Hz
  ...

--- Bulk generator ---
  Generated 1000 inputs: {text: 393, audio: 254, physio: 205, video: 148}

--- Determinism check ---
  Two runs identical: True
```

## Adding Tests for Future Phases

```
  Phase 2 test file
       │
       v
  Test in isolation
       │
       v
  Verify imports only from Phase 1 + self
       │
       v
  Include determinism checks
       │
       v
  Stress test at 1000+ inputs
       │
       v
  Verify no mutation of RawInput
```

When implementing Phase 2 (Perception), create `tests/test_perception.py` following this pattern:

1. Test the component in isolation
2. Verify it only imports from itself and Phase 1
3. Include determinism checks
4. Include a stress test at 1,000+ inputs
5. Verify it does not modify upstream `RawInput` objects
