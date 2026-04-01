# Phase 1 — Input Acquisition

[Back to README](../README.md) | [Architecture](architecture.md) | [API Reference](api-reference.md) | [Testing](testing.md)

## Purpose

Input Acquisition is the sensory nervous system of AURA. It captures raw signals from multiple modalities, wraps them in structured containers, and stores them in a short-term buffer. It performs **zero interpretation** — no tokenization, no spectral analysis, no feature extraction.

## Module Overview

```
  Raw Signals                          input_acquisition/
  ─────────────                        ──────────────────
  Text (string) ────────┐
  Audio (waveform) ─────┤       ┌──────────────────────────────┐
  Video (frames) ───────┼──────>│  manager.py                  │
  Physiological ────────┘       │  InputAcquisitionManager     │
                                └──────┬───────────┬───────────┘
                                       │           │
                                       v           v
                          ┌────────────────┐  ┌──────────────────┐
                          │ validation.py  │  │ time_manager.py  │
                          │ InputValidator │  │ TimeManager      │
                          └───────┬────────┘  └────────┬─────────┘
                                  │                    │
                                  v                    v
                          ┌──────────────────────────────────────┐
                          │  raw_input.py                        │
                          │  RawInput + subclasses               │
                          └──────┬───────────────┬───────────────┘
                                 │               │
                                 v               v
                          ┌────────────┐  ┌────────────┐
                          │ buffer.py  │  │ logger.py  │
                          │ InputBuffer│  │ InputLogger│
                          └────────────┘  └────────────┘
```

## Processing Pipeline

Every incoming signal follows this exact flow:

```
  receive_*(raw_data)
       │
       v
  InputValidator            structural checks
       │
       v
  TimeManager.now()         get timestamp
       │
       v
  Create RawInput           deep copy + checksum
       │
       ├──> InputBuffer.append()    FIFO storage
       │
       └──> InputLogger.log()       metadata only
       │
       v
  Return immutable RawInput to caller
```

## Components

### RawInput (`raw_input.py`)

Immutable base container for a single raw signal.

**Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `id` | `str` | UUID4 hex (32 characters), unique per input |
| `modality` | `str` | One of: `text`, `audio`, `video`, `physiological` |
| `data` | varies | The raw signal — deep-copied on creation |
| `timestamp` | `float` | Time of acquisition (system or simulated clock) |
| `metadata` | `dict` | Modality-specific and user-provided metadata |
| `session_id` | `str` | Groups inputs belonging to the same session |
| `source_id` | `str` | Identifies the signal source |
| `checksum` | `str` | SHA-256 hash of the raw data for integrity verification |

**Immutability guarantees**:
- `__setattr__` raises `AttributeError` after construction
- `__delattr__` always raises
- The `data` property returns a deep copy — callers cannot mutate internal state
- The `metadata` property returns a copy of the dict

### Modality Subclasses

```
                         RawInput
                    ┌────────┴─────────────┐
                    │  +id: str            │
                    │  +modality: str      │
                    │  +data: any          │
                    │  +timestamp: float   │
                    │  +metadata: dict     │
                    │  +session_id: str    │
                    │  +source_id: str     │
                    │  +checksum: str      │
                    │  +verify_integrity() │
                    │  +to_dict()          │
                    └───┬────┬────┬────┬───┘
                        │    │    │    │
          ┌─────────────┘    │    │    └──────────────┐
          │            ┌─────┘    └──────┐            │
          v            v                 v            v
  ┌──────────────┐ ┌──────────────┐ ┌──────────┐ ┌──────────────────┐
  │  TextInput   │ │  AudioInput  │ │VideoInput│ │PhysiologicalInput│
  │              │ │              │ │          │ │                  │
  │ +data: str   │ │ +data: list  │ │+data:list│ │ +data: dict      │
  │ auto:        │ │ +sample_rate │ │+resolut. │ │ +signal_type     │
  │  char_count  │ │ +channels    │ │ auto:    │ │ +sampling_freq   │
  │  encoding    │ │ auto:        │ │ frame_ct │ │ auto:            │
  │              │ │  sample_count│ │ res_w/h  │ │  channel_names   │
  │              │ │  duration_s  │ │          │ │  sample_counts   │
  └──────────────┘ └──────────────┘ └──────────┘ └──────────────────┘
```

#### TextInput

```python
TextInput(data="Hello world", timestamp=1.0)
```
- `data`: must be a non-empty `str`
- Auto-metadata: `char_count`, `encoding` (always `utf-8`)

#### AudioInput

```python
AudioInput(data=[0.1, -0.2, 0.3], sample_rate=44100, channels=1, timestamp=1.0)
```
- `data`: must be a non-empty `list` of numeric samples
- `sample_rate`: positive `int` (Hz)
- `channels`: positive `int` (default 1)
- Auto-metadata: `sample_rate`, `channels`, `sample_count`, `duration_seconds`

#### VideoInput

```python
VideoInput(data=[frame1, frame2, ...], resolution=(1920, 1080), timestamp=1.0)
```
- `data`: must be a non-empty `list` of frames
- `resolution`: `(width, height)` tuple of positive ints
- Auto-metadata: `frame_count`, `resolution_width`, `resolution_height`

#### PhysiologicalInput

```python
PhysiologicalInput(
    data={"heart_rate": [72, 73], "eda": [0.4, 0.5]},
    signal_type="biometric",
    sampling_frequency=10.0,
    timestamp=1.0
)
```
- `data`: must be a non-empty `dict` mapping channel names to sample lists
- `signal_type`: non-empty `str`
- `sampling_frequency`: positive `float` (Hz)
- Auto-metadata: `signal_type`, `sampling_frequency`, `channel_names`, `sample_counts`

### TimeManager (`time_manager.py`)

Central clock with two modes:

```
  REAL Mode                          SIMULATED Mode
  ─────────                          ──────────────
  now()  --> time.time()             now()   --> internal counter
  tick() --> no-op                   tick(d) --> advance counter by d
                                     reset() --> rewind clock
```

Simulated mode is critical for deterministic testing and will later drive emotional decay dynamics.

```python
from app.input_acquisition.time_manager import TimeManager, TimeMode

tm = TimeManager(mode=TimeMode.SIMULATED, start_time=0.0)
tm.tick_delta = 0.5   # default step per tick

tm.now()   # 0.0
tm.tick()  # advances to 0.5
tm.now()   # 0.5
tm.tick(delta=2.0)  # advances to 2.5
tm.reset(0.0)       # back to 0.0, tick_count resets
```

### InputValidator (`validation.py`)

Stateless validation — all methods are classmethods. Raises `ValidationError` on failure.

| Method | Checks |
|--------|--------|
| `validate_text(data)` | Is `str`, non-empty, under 10M characters |
| `validate_audio(data, sample_rate, channels)` | Is `list`, non-empty, numeric samples, valid rate/channels |
| `validate_video(data, resolution)` | Is `list`, non-empty, valid resolution tuple |
| `validate_physiological(data, signal_type, freq)` | Is `dict`, non-empty, valid channels and frequency |
| `validate_timestamp(ts)` | Is numeric, non-negative |
| `validate_integrity(raw_input)` | Checksum matches recomputed hash |

### InputBuffer (`buffer.py`)

Ordered FIFO buffer backed by `OrderedDict`.

```
  New Input ──> buffer.append()
                    │
                    ├── capacity full? ──> Evict oldest (FIFO)
                    │
                    v
               OrderedDict
                    │
                    ├──> get_by_id(id)
                    ├──> get_by_modality(mod)
                    ├──> get_by_time_range(start, end)
                    ├──> get_by_session(session)
                    ├──> get_latest(n)
                    └──> replay()
```

When `append` is called at capacity, the oldest entry is evicted (FIFO).

### InputLogger (`logger.py`)

Records structural metadata about each input. Never stores raw signal content.

Each `LogEntry` captures: `input_id`, `modality`, `timestamp`, `data_size`, `metadata_summary`.

The logger uses a bounded `deque` (default 10,000 entries) and tracks per-modality counters.

### InputAcquisitionManager (`manager.py`)

The single entry point for all signal acquisition. Orchestrates: **validate → timestamp → wrap → buffer → log**.

```python
from app.input_acquisition import InputAcquisitionManager, TimeManager, TimeMode

mgr = InputAcquisitionManager(session_id="experiment-1")

# Receive signals
text_input   = mgr.receive_text("Hello world")
audio_input  = mgr.receive_audio([0.1, -0.2], sample_rate=16000)
video_input  = mgr.receive_video([[[0,0,0]]], resolution=(1,1))
physio_input = mgr.receive_physiological(
    {"hr": [72]}, signal_type="ecg", sampling_frequency=256.0
)

# Query
mgr.get_latest(5)
mgr.get_by_modality("audio")
mgr.get_by_id(text_input.id)
mgr.replay()
mgr.stats()
mgr.clear_buffer()
```

## Boundary: What This Phase Does NOT Do

```
  ALLOWED (Phase 1)                 FORBIDDEN (later phases)
  ─────────────────                 ───────────────────────
  [x] Capture raw signals           [ ] NLP tokenization         (Phase 2)
  [x] Timestamp inputs              [ ] Sentiment detection      (Phase 4)
  [x] Validate structure            [ ] Audio FFT / MFCC         (Phase 2)
  [x] Buffer storage                [ ] Feature extraction       (Phase 2)
  [x] Checksum integrity            [ ] Emotion inference        (Phase 4)
  [x] Replay inputs                 [ ] Learning / adaptation    (Phase 10)
                                    [ ] Long-term memory         (Phase 9)
                                    [ ] Data compression         (never)
                                    [ ] External libraries       (never)
```

## Architectural Boundaries

- `input_acquisition` imports **nothing** from `perception` or any downstream module
- All interfaces are explicit — no magic, no metaclasses
- `RawInput` objects are immutable after creation
- New modalities can be added by subclassing `RawInput` without modifying existing code
