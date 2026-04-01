# API Reference

[Back to README](../README.md) | [Architecture](architecture.md) | [Setup](setup.md)

Base URL: `http://localhost:8000`

Interactive docs available at `/docs` (Swagger) and `/redoc` (ReDoc) when the server is running.

## Endpoint Map

```
  General
  ───────
    GET  /                            Root health check
    GET  /api/health                  System health check

  Ingest Endpoints
  ────────────────
    POST /api/input/text              Acquire raw text signal
    POST /api/input/audio             Acquire raw audio waveform
    POST /api/input/video             Acquire raw video frames
    POST /api/input/physiological     Acquire raw physiological signals

  Query Endpoints
  ───────────────
    GET  /api/input/latest?n=         Most recent n buffered inputs
    GET  /api/input/all               All buffered inputs
    GET  /api/input/by-modality/{mod} Inputs by modality
    GET  /api/input/by-id/{id}        Single input by ID
    GET  /api/input/replay            All inputs in insertion order
    GET  /api/input/stats             Acquisition statistics

  Management
  ──────────
    DELETE /api/input/buffer          Clear all inputs from buffer
```

---

## General

### `GET /`

Root health check.

**Response** `200`:
```json
{ "message": "AURA API is running" }
```

### `GET /api/health`

System health check.

**Response** `200`:
```json
{ "status": "healthy" }
```

---

## Input Acquisition — Ingest

All input acquisition endpoints are under `/api/input`.

### `POST /api/input/text`

Acquire a raw text signal.

**Request body**:
```json
{
  "text": "I feel a slight tension in the room.",
  "source_id": "api",
  "metadata": {}
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | `string` | Yes | Raw text, minimum 1 character |
| `source_id` | `string` | No | Source identifier (default: `"api"`) |
| `metadata` | `object` | No | Additional metadata key-value pairs |

**Response** `200`:
```json
{
  "id": "a1b2c3d4e5f6...",
  "modality": "text",
  "timestamp": 1708300000.123
}
```

**Error** `422`: validation failure (empty text, wrong type)

---

### `POST /api/input/audio`

Acquire a raw audio waveform.

**Request body**:
```json
{
  "waveform": [0.1, -0.2, 0.3, 0.0, -0.1],
  "sample_rate": 16000,
  "channels": 1,
  "source_id": "api",
  "metadata": {}
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `waveform` | `float[]` | Yes | List of audio samples in [-1.0, 1.0] |
| `sample_rate` | `int` | Yes | Sample rate in Hz (must be > 0) |
| `channels` | `int` | No | Number of channels (default: 1) |
| `source_id` | `string` | No | Source identifier |
| `metadata` | `object` | No | Additional metadata |

**Response** `200`:
```json
{
  "id": "...",
  "modality": "audio",
  "timestamp": 1708300001.456
}
```

---

### `POST /api/input/video`

Acquire raw video frames.

**Request body**:
```json
{
  "frames": [
    [[[255, 0, 0], [0, 255, 0]], [[0, 0, 255], [128, 128, 128]]]
  ],
  "resolution": [2, 2],
  "source_id": "api",
  "metadata": {}
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `frames` | `array` | Yes | List of frames (each frame is a 2D grid of RGB pixels) |
| `resolution` | `[int, int]` | Yes | `[width, height]`, both > 0 |
| `source_id` | `string` | No | Source identifier |
| `metadata` | `object` | No | Additional metadata |

**Response** `200`:
```json
{
  "id": "...",
  "modality": "video",
  "timestamp": 1708300002.789
}
```

---

### `POST /api/input/physiological`

Acquire raw physiological signals.

**Request body**:
```json
{
  "signals": {
    "heart_rate": [72.5, 73.1, 71.8],
    "skin_temp": [36.5, 36.6, 36.5],
    "eda": [0.42, 0.45, 0.41]
  },
  "signal_type": "biometric",
  "sampling_frequency": 10.0,
  "source_id": "api",
  "metadata": {}
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `signals` | `object` | Yes | Dict mapping channel names to `float[]` sample lists |
| `signal_type` | `string` | Yes | Type of physiological signal (non-empty) |
| `sampling_frequency` | `float` | Yes | Sampling rate in Hz (must be > 0) |
| `source_id` | `string` | No | Source identifier |
| `metadata` | `object` | No | Additional metadata |

**Response** `200`:
```json
{
  "id": "...",
  "modality": "physiological",
  "timestamp": 1708300003.012
}
```

---

## Input Acquisition — Query

### `GET /api/input/latest?n=5`

Return the most recent `n` buffered inputs.

**Query params**: `n` (int, default 5)

**Response** `200`:
```json
[
  {
    "id": "...",
    "modality": "text",
    "timestamp": 1708300000.123,
    "metadata": { "char_count": 36, "encoding": "utf-8" },
    "session_id": "api-session",
    "source_id": "api",
    "checksum": "sha256...",
    "data_type": "str"
  }
]
```

### `GET /api/input/all`

Return all buffered inputs in insertion order.

### `GET /api/input/by-modality/{modality}`

Return all buffered inputs matching the given modality.

**Path params**: `modality` — one of `text`, `audio`, `video`, `physiological`

### `GET /api/input/by-id/{input_id}`

Return a single input by its unique ID.

**Error** `404`: input not found in buffer

### `GET /api/input/replay`

Return all buffered inputs in insertion order (alias for replay intent).

### `GET /api/input/stats`

Return acquisition statistics.

**Response** `200`:
```json
{
  "session_id": "api-session",
  "total_received": 42,
  "buffer_size": 42,
  "buffer_capacity": 5000,
  "counts_by_modality": {
    "text": 20,
    "audio": 10,
    "video": 5,
    "physiological": 7
  },
  "time_mode": "real",
  "current_time": 1708300010.0
}
```

### `DELETE /api/input/buffer`

Clear all inputs from the buffer. The total received counter is preserved.

**Response** `200`:
```json
{ "status": "buffer cleared" }
```

---

## Request → Response Flow

```
  Client                FastAPI             Manager          Validator        Buffer
    │                     │                   │                 │               │
    │  POST /api/input/   │                   │                 │               │
    │  text               │                   │                 │               │
    │────────────────────>│                   │                 │               │
    │                     │  receive_text()   │                 │               │
    │                     │──────────────────>│                 │               │
    │                     │                   │ validate_text() │               │
    │                     │                   │────────────────>│               │
    │                     │                   │      OK         │               │
    │                     │                   │<────────────────│               │
    │                     │                   │                 │               │
    │                     │                   │ TimeManager.now()               │
    │                     │                   │ Create TextInput (immutable)    │
    │                     │                   │                                 │
    │                     │                   │ append(raw_input)               │
    │                     │                   │────────────────────────────────>│
    │                     │                   │ Logger.log(raw_input)           │
    │                     │                   │                                 │
    │                     │    TextInput      │                                 │
    │                     │<─────────────────│                                 │
    │  { id, modality,    │                   │                                 │
    │    timestamp }      │                   │                                 │
    │<────────────────────│                   │                                 │
```

## Response Format Notes

- All retrieval endpoints return input metadata via `to_dict()` — they do **not** include raw signal data in the response for safety and performance
- The `data_type` field indicates the Python type of the raw data (`str`, `list`, `dict`)
- Timestamps are Unix epoch floats
- IDs are 32-character hexadecimal strings (UUID4)
