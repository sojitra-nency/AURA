# AURA System Architecture

[Back to README](../README.md)

## Overview

AURA is an artificial affective system built as a layered cognitive pipeline. Raw sensory signals flow through perception, inference, appraisal, and decision stages before producing observable behavior. A cross-cutting memory system and offline evaluation framework support learning and adaptation.

The architecture deliberately separates **sensation** (what happened), **perception** (what was observed), **inference** (what is the emotional state), **appraisal** (what does it mean), **decision** (what to do), and **expression** (how to do it).

## Full System Diagram

```
  ┌──────────────────────────────────────────────────────────────────────┐
  │                    AURA Cognitive Pipeline                           │
  ├──────────────────────────────────────────────────────────────────────┤
  │                                                                      │
  │  ┌───────────────────┐                                               │
  │  │ Phase 1 [DONE]    │                                               │
  │  │ Input Acquisition │  Acquire raw signals:                         │
  │  │ text/audio/video/ │  text, audio, video, physiological            │
  │  │ physiological     │                                               │
  │  └────────┬──────────┘                                               │
  │           │                                                          │
  │           v                                                          │
  │  ┌───────────────────┐                                               │
  │  │ Phase 2           │  Convert raw input to normalized features:    │
  │  │ Perception Layer  │  Linguistic | Prosodic | Visual Motion        │
  │  └────────┬──────────┘                                               │
  │           │                                                          │
  │           v                         ┌─────────────────────┐          │
  │  ┌───────────────────┐         .--->│ Phase 5             │          │
  │  │ Phase 3           │<-----.'     │ Emotional Framework  │          │
  │  │ Attention &       │  modulates  │ Decay, inertia,      │          │
  │  │ Salience          │             │ trait modulation      │          │
  │  └────────┬──────────┘             └──────────┬──────────┘          │
  │           │                                   ^                      │
  │           v                                   │                      │
  │  ┌───────────────────┐                        │                      │
  │  │ Phase 4           │────────────────────────┘                      │
  │  │ Inference Engine  │  Estimate continuous, uncertainty-aware        │
  │  │ (VAD model)       │  emotional state using memory                 │
  │  └────────┬──────────┘                                               │
  │           │                                                          │
  │           v                                                          │
  │  ┌───────────────────┐                                               │
  │  │ Phase 6           │  Interpret situation: intent, norms,          │
  │  │ Cognitive         │  threats/opportunities                        │
  │  │ Appraisal         │                                               │
  │  └────────┬──────────┘                                               │
  │           │                                                          │
  │           v                                                          │
  │  ┌───────────────────┐                                               │
  │  │ Phase 7           │  Select response strategy balancing           │
  │  │ Decision Reaction │  affect, goals, ethics, risk                  │
  │  │ Engine            │                                               │
  │  └────────┬──────────┘                                               │
  │           │                                                          │
  │           v                                                          │
  │  ┌───────────────────┐                                               │
  │  │ Phase 8           │  Translate strategy to behavior:              │
  │  │ Expression Layer  │  phrasing, tone, intensity                    │
  │  └───────────────────┘                                               │
  │                                                                      │
  └──────────────────────────────────────────────────────────────────────┘
```

## Cross-Cutting Systems

```
  ╔══════════════════════════════════════════════════════════╗
  ║               Phase 9 — Memory System                   ║
  ║  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ║
  ║  │ Episodic     │  │ Emotional    │  │ User         │  ║
  ║  │ Memory       │  │ Memory       │  │ Memory       │  ║
  ║  └──────────────┘  └──────────────┘  └──────────────┘  ║
  ║  ┌──────────────┐                                       ║
  ║  │ Trait        │                                       ║
  ║  │ Memory       │                                       ║
  ║  └──────────────┘                                       ║
  ╠══════════════════════════════════════════════════════════╣
  ║              Phase 10 — Learn & Adapt                   ║
  ║  ┌─────────────┐ ┌──────────────┐ ┌──────────────────┐ ║
  ║  │ Calibration │ │ Inference    │ │ Affect Dynamics   │ ║
  ║  │             │ │ Tuning       │ │                   │ ║
  ║  └─────────────┘ └──────────────┘ └──────────────────┘ ║
  ║  ┌─────────────────┐ ┌────────────────────┐            ║
  ║  │ Personalization │ │ Policy Optimization│            ║
  ║  └─────────────────┘ └────────────────────┘            ║
  ╠══════════════════════════════════════════════════════════╣
  ║          Phase 11 — Evaluation & Simulation             ║
  ║  ┌─────────────────┐ ┌──────────────┐ ┌─────────────┐  ║
  ║  │ Scenario Replay │ │ Stress       │ │ Empathy     │  ║
  ║  │                 │ │ Testing      │ │ Alignment   │  ║
  ║  └─────────────────┘ └──────────────┘ └─────────────┘  ║
  ╚══════════════════════════════════════════════════════════╝
```

## Layer Descriptions

### Phase 1 — Input Acquisition (Implemented)

The sensory nervous system. Captures raw signals from four modalities and wraps them in immutable, timestamped, checksummed containers. No interpretation occurs.

```
  Text ──┐
  Audio ─┤
  Video ─┼──> InputAcquisitionManager ──> Validate ──> Timestamp
  Physio ┘                                                 │
                                                           v
                                                    Wrap in RawInput
                                                      │         │
                                                      v         v
                                                  [Buffer]  [Logger]
```

- **Modalities**: text (string), audio (waveform), video (frame sequence), physiological (numeric signals)
- **Key guarantees**: immutability, deep-copied data, SHA-256 integrity checksum, deterministic timestamps
- **Detailed docs**: [Phase 1: Input Acquisition](phase-1-input-acquisition.md)

### Phase 2 — Perception Layer

Converts raw input into normalized feature representations. This is the first stage where transformation occurs.

```
                    ┌──> Linguistic Processor ──┐
                    │                           │
  RawInput ─────────┼──> Prosodic Processor  ───┼──> Feature Vector
                    │                           │
                    └──> Visual Processor    ───┘
```

- **Linguistic features**: character-level statistics, lexical density, sentence structure markers
- **Prosodic features**: energy contour, pitch estimates, speaking rate from audio waveforms
- **Visual motion features**: frame-to-frame pixel delta, motion magnitude, spatial focus regions

> Perception does NOT classify or interpret. It converts raw signals into numeric feature vectors.

### Phase 3 — Attention & Salience Modulator

Biases which features receive processing priority based on:

- Current emotional state (from the Emotional Framework)
- Recent memory context
- Current affect intensity

Features that are salient to the system's current state receive higher weight in downstream inference.

### Phase 4 — Inference Engine

Estimates a continuous, uncertainty-aware emotional state using the VAD (Valence-Arousal-Dominance) model.

```
  Salient Features ──┐
                     ├──> Multi-Modal Fusion ──┬──> VAD Estimate
  Memory ────────────┘                         │    (Valence | Arousal | Dominance)
                                               │
                                               └──> Uncertainty Bounds
```

- Continuous values, not discrete categories
- Uncertainty quantification (confidence bounds on each dimension)
- Memory-informed: prior emotional trajectory shapes current estimates
- Multi-modal fusion: combines evidence from all available modalities

### Phase 5 — Emotional Framework

Maintains the system's dynamic internal emotional state as a time-evolving process:

```
                         ┌──> Decay toward baseline ──┐
                         │                             │
  Inference Output ──> Emotional State <───────────────┘
                         │                             ^
                         ├──> Inertia dampening ───────┤
                         ├──> Trait modulation ─────────┤
                         └──> Goal influence ──────────┘
```

### Phase 6 — Cognitive Appraisal Engine

Interprets the situation by combining emotional state with contextual reasoning:

- Infers user intent and social norms
- Classifies the situation as a threat, opportunity, or neutral event
- Evaluates relevance to active goals
- Produces appraisal dimensions: novelty, pleasantness, goal relevance, coping potential

### Phase 7 — Decision Reaction Engine

Selects a response strategy by balancing multiple factors:

- Appraisal output
- Current system affect
- Active goals and priorities
- Ethical constraints and safety rules
- Confidence and risk thresholds

Output: a response plan specifying what to communicate and at what intensity.

### Phase 8 — Expression Layer

Translates the decision into observable behavior:

- Phrasing and word choice
- Tone and formality level
- Emotional intensity mapping
- Multi-modal coordination (if multiple output channels exist)

### Phase 9 — Memory System (Cross-Cutting)

A persistent store read and written across multiple layers:

| Memory Type | Purpose |
|-------------|---------|
| Episodic | Specific interaction events and their emotional signatures |
| Emotional | History of emotional states and transitions |
| User | Accumulated knowledge about the user's preferences, patterns, traits |
| Trait | The system's own personality configuration and long-term biases |

### Phase 10 — Learn & Adapt

Offline and online learning processes:

- **Calibration**: adjusting perception thresholds based on accumulated data
- **Inference tuning**: refining VAD estimation accuracy
- **Affect dynamics**: updating decay/inertia parameters
- **Personalization**: adapting to individual user patterns
- **Policy optimization**: improving decision strategies over time

### Phase 11 — Evaluation & Simulation

Offline quality assurance through scenario replay:

- Replays recorded interaction sequences
- Stress-tests emotional transitions for consistency
- Evaluates empathy alignment
- Detects regressions in response quality

## Data Flow

```
  Raw Signal
      │
      v
  RawInput (immutable)          ── Phase 1
      │
      v
  FeatureVector (perception)    ── Phase 2
      │
      v
  SalienceWeighted (attention)  ── Phase 3
      │
      v
  VADEstimate (inference)       ── Phase 4
      │
      v
  AppraisalResult (appraisal)  ── Phase 6
      │
      v
  ResponsePlan (decision)       ── Phase 7
      │
      v
  Observable Behavior           ── Phase 8
```

Each stage produces a distinct, typed data structure. No stage reaches backward to modify upstream data.

## Design Constraints

| Constraint | Rationale |
|-----------|-----------|
| Pure Python core | Explicit, auditable logic; no opaque ML black boxes |
| No circular imports | Each phase imports only from itself or earlier phases |
| Immutable signal containers | Research reproducibility; prevents accidental data corruption |
| Deterministic time mode | Enables exact replay and regression testing |
| Subclass extensibility | New modalities or appraisal rules via inheritance, not modification |
| Phase isolation | Each layer can be developed, tested, and replaced independently |

## Module Dependency Graph

```
  Phase 1: input_acquisition
      │
      v
  Phase 2: perception
      │
      v
  Phase 3: attention  <·········· Phase 5: emotional_framework
      │                                    ^
      v                                    │
  Phase 4: inference ──────────────────────┘
      │         ^
      │         │
      │    Phase 9: memory (cross-cutting)
      │         ^         │
      v         │         v
  Phase 6: appraisal      Phase 10: learning
      │                        │
      v                        v
  Phase 7: decision       Phase 11: evaluation
      │
      v
  Phase 8: expression

  ──>  = data flow         ···>  = modulates / informs
```

## Future Considerations

- **Async processing**: later phases may require concurrent handling of long-running inference
- **Streaming input**: real-time audio/video will need buffered streaming acquisition
- **Persistent storage**: memory system will eventually need disk-backed storage
- **Multi-agent**: evaluation phase may spawn parallel simulation agents
