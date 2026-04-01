# AURA

**Artificial Unified Responsive Agent** — A research-grade artificial affective system that models continuous emotional dynamics through multi-modal signal processing, cognitive appraisal, and adaptive expression.

AURA acquires raw sensory inputs (text, audio, video, physiological), processes them through a layered cognitive architecture, maintains an internal emotional state, and generates contextually appropriate responses — all while learning and adapting over time.

## System Architecture

```
  ┌─────────────────┐    ┌──────────────────┐    ┌───────────────────────┐
  │ Input            │───>│ Perception       │───>│ Attention & Salience  │
  │ Acquisition [*]  │    │ Layer            │    │ Modulator             │
  └─────────────────┘    └──────────────────┘    └───────────┬───────────┘
                                                             │
                                                             v
  ┌─────────────────┐    ┌──────────────────┐    ┌───────────────────────┐
  │ Expression      │<───│ Decision         │<───│ Cognitive Appraisal   │
  │ Layer           │    │ Reaction Engine  │    │ Engine                │
  └─────────────────┘    └──────────────────┘    └───────────┬───────────┘
                                                             ^
                                                             │
                          ┌──────────────────┐    ┌──────────┴────────────┐
                          │ Emotional        │<───│ Inference             │
                          │ Framework        │    │ Engine                │
                          └────────┬─────────┘    └───────────────────────┘
                                   │                         ^
                                   v                         │
                          ╔══════════════════╗               │
                          ║  Memory System   ║───────────────┘
                          ╠══════════════════╣
                          ║ Learn & Adapt    ║
                          ╠══════════════════╣
                          ║ Eval & Simulation║
                          ╚══════════════════╝

  [*] = Implemented    [ ] = Planned    ║ ║ = Cross-cutting systems
```

Each layer is developed as an independent phase. See [Architecture](docs/architecture.md) for the full system design.

## Current Status

| Phase | Name | Status |
|:---:|------|:---:|
| 1 | Input Acquisition | **Complete** |
| 2 | Perception Layer | Planned |
| 3 | Attention & Salience Modulator | Planned |
| 4 | Inference Engine | Planned |
| 5 | Emotional Framework | Planned |
| 6 | Cognitive Appraisal Engine | Planned |
| 7 | Decision Reaction Engine | Planned |
| 8 | Expression Layer | Planned |
| 9 | Memory System | Planned |
| 10 | Learn & Adapt | Planned |
| 11 | Evaluation & Simulation | Planned |

## Tech Stack

```
  ┌─────────────────────────────────────────────────────┐
  │                     Backend                         │
  │  ┌──────────────┐ ┌────────────┐ ┌──────────────┐  │
  │  │ Python 3.12  │ │ FastAPI    │ │ Pydantic 2.10│  │
  │  └──────────────┘ │  0.115     │ └──────────────┘  │
  │  ┌──────────────┐ └────────────┘                    │
  │  │ Uvicorn      │                                   │
  │  └──────────────┘                                   │
  └──────────────────────────┬──────────────────────────┘
                             │ HTTP / REST
  ┌──────────────────────────┴──────────────────────────┐
  │                     Frontend                        │
  │  ┌──────────────┐ ┌────────────┐ ┌──────────────┐  │
  │  │ Next.js 16   │ │ React 19   │ │ TypeScript 5 │  │
  │  └──────────────┘ └────────────┘ └──────────────┘  │
  │  ┌──────────────┐                                   │
  │  │ Tailwind CSS │                                   │
  │  └──────────────┘                                   │
  └─────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────┐
  │                     Testing                         │
  │  ┌──────────────┐ ┌────────────────────────────┐    │
  │  │ unittest     │ │ Deterministic dummy data   │    │
  │  └──────────────┘ └────────────────────────────┘    │
  └─────────────────────────────────────────────────────┘
```

## Project Structure

```
  AURA/
  ├── backend/
  │   ├── app/
  │   │   ├── main.py                  # FastAPI entry point
  │   │   ├── core/
  │   │   │   └── config.py            # Pydantic settings
  │   │   ├── input_acquisition/       # Phase 1 module
  │   │   │   ├── raw_input.py
  │   │   │   ├── time_manager.py
  │   │   │   ├── validation.py
  │   │   │   ├── buffer.py
  │   │   │   ├── logger.py
  │   │   │   └── manager.py
  │   │   ├── routers/                 # API endpoints
  │   │   │   ├── health.py
  │   │   │   └── input_acquisition.py
  │   │   ├── models/                  # Future phases
  │   │   └── schemas/                 # Future phases
  │   ├── tests/
  │   │   ├── dummy_data.py            # Deterministic test data
  │   │   ├── test_input_acquisition.py  # 101 tests
  │   │   └── test_dummy_data.py       # 42 tests
  │   ├── requirements.txt
  │   └── .env
  ├── frontend/
  │   └── src/app/                     # Next.js pages
  └── docs/
      ├── architecture.md
      ├── setup.md
      ├── phase-1-input-acquisition.md
      ├── api-reference.md
      └── testing.md
```

## Quick Start

```bash
# Backend
cd backend
python -m venv venv
source venv/Scripts/activate    # Windows (Git Bash)
pip install -r requirements.txt
uvicorn app.main:app --reload   # http://localhost:8000

# Frontend
cd frontend
npm install
npm run dev                     # http://localhost:3000
```

See [Setup Guide](docs/setup.md) for detailed instructions.

## Documentation

| Document | Description |
|----------|-------------|
| [Architecture](docs/architecture.md) | Full system design, all 11 layers, data flow, and design principles |
| [Setup Guide](docs/setup.md) | Installation, environment setup, running the project |
| [Phase 1: Input Acquisition](docs/phase-1-input-acquisition.md) | Implemented components, data structures, module API |
| [API Reference](docs/api-reference.md) | REST endpoint documentation |
| [Testing Guide](docs/testing.md) | Test strategy, running tests, dummy data generation |

## Design Principles

```
  ┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
  │ Phase Isolation   │───│ Pure Python Core │───│ Determinism      │
  └──────────────────┘   └──────────────────┘   └──────────────────┘
           │                                              │
  ┌──────────────────┐                          ┌──────────────────┐
  │ Immutability      │──────────────────────────│ Extensibility    │
  └──────────────────┘                          └──────────────────┘
```

1. **Phase isolation** — each layer is developed independently with zero imports from downstream layers
2. **Pure Python core** — the cognitive engine uses no external ML/NLP libraries; all logic is explicit
3. **Determinism** — simulated time mode ensures fully reproducible behavior for research
4. **Immutability** — raw inputs are frozen after creation; no signal mutation
5. **Extensibility** — new modalities, appraisal rules, or expression channels are added via subclassing, not modification
