"""
Deterministic dummy raw data generator for AURA Phase 1 testing.

Generates structured, reproducible raw signals across all four modalities.
Uses a fixed seed for full determinism. No feature extraction, no
transformation, no external libraries — pure Python only.

Usage:
    from tests.dummy_data import generate_all, generate_bulk_inputs

    data = generate_all()          # structured dict of all modalities
    bulk = generate_bulk_inputs(1000)  # list of 1000 mixed raw inputs
"""

import math
import random

# -----------------------------------------------------------------------
# Seeded RNG helper — every public function reseeds so that calling
# them in any order always produces the same output.
# -----------------------------------------------------------------------

_DEFAULT_SEED = 42


def _seeded_rng(seed: int = _DEFAULT_SEED) -> random.Random:
    """Return an independent Random instance with a fixed seed."""
    return random.Random(seed)


# -----------------------------------------------------------------------
# Text generation
# -----------------------------------------------------------------------

# 60 canned sentence fragments — picked deterministically, combined by the
# RNG. No NLP, no tokenization — just raw strings.
_SUBJECTS = [
    "I", "She", "He", "The patient", "A participant", "The user",
    "Someone", "The speaker", "They", "We",
]
_VERBS = [
    "feel", "felt", "said", "noticed", "reported", "described",
    "mentioned", "expressed", "observed", "indicated",
]
_OBJECTS = [
    "a slight tension in the room",
    "some discomfort during the session",
    "a warm feeling after the conversation",
    "nothing unusual today",
    "that the noise was distracting",
    "a brief moment of calm",
    "an unexpected sense of relief",
    "mild frustration with the interface",
    "general satisfaction with the process",
    "difficulty concentrating this morning",
    "a sudden change in mood",
    "some anxiety before the test",
    "that everything seemed normal",
    "a persistent headache since noon",
    "complete relaxation after the exercise",
    "slight irritation from the bright light",
    "a sense of accomplishment",
    "that the temperature was too cold",
    "heightened awareness of their breathing",
    "no particular emotional response",
]


def generate_text_samples(n: int = 20, seed: int = _DEFAULT_SEED) -> list[str]:
    """Generate n deterministic raw text strings."""
    rng = _seeded_rng(seed)
    samples = []
    for _ in range(n):
        subj = rng.choice(_SUBJECTS)
        verb = rng.choice(_VERBS)
        obj = rng.choice(_OBJECTS)
        samples.append(f"{subj} {verb} {obj}.")
    return samples


# -----------------------------------------------------------------------
# Audio generation
# -----------------------------------------------------------------------

_SAMPLE_RATES = [16000, 44100]


def _generate_waveform(
    length: int, rng: random.Random, freq_hz: float, amplitude: float
) -> list[float]:
    """
    Synthesize a simple sine-based waveform with additive noise.
    Values clamped to [-1.0, 1.0]. Pure math — no FFT, no MFCC.
    """
    sample_rate = rng.choice(_SAMPLE_RATES)
    wave = []
    for i in range(length):
        t = i / sample_rate
        # Base sine wave
        value = amplitude * math.sin(2.0 * math.pi * freq_hz * t)
        # Small deterministic noise
        noise = (rng.random() - 0.5) * 0.1
        sample = max(-1.0, min(1.0, value + noise))
        wave.append(round(sample, 6))
    return wave, sample_rate


def generate_audio_samples(
    n: int = 5, waveform_length: int = 1000, seed: int = _DEFAULT_SEED
) -> list[dict]:
    """Generate n deterministic raw audio waveforms."""
    rng = _seeded_rng(seed + 1)  # offset seed to decouple from text
    samples = []
    for i in range(n):
        freq = 100.0 + i * 80.0  # 100, 180, 260, 340, 420 Hz
        amplitude = 0.3 + (i * 0.15)  # 0.30 → 0.90
        amplitude = min(amplitude, 0.95)
        waveform, sr = _generate_waveform(waveform_length, rng, freq, amplitude)
        samples.append({
            "waveform": waveform,
            "sample_rate": sr,
        })
    return samples


# -----------------------------------------------------------------------
# Video generation
# -----------------------------------------------------------------------


def _generate_frame(width: int, height: int, rng: random.Random) -> list[list[list[int]]]:
    """
    Generate a single frame as a height × width grid of [R, G, B] pixels.
    Values are integers in [0, 255].
    """
    return [
        [[rng.randint(0, 255) for _ in range(3)] for _ in range(width)]
        for _ in range(height)
    ]


def generate_video_samples(
    n: int = 3,
    frames_per_video: int = 10,
    width: int = 8,
    height: int = 8,
    seed: int = _DEFAULT_SEED,
) -> list[dict]:
    """Generate n deterministic raw video frame sequences."""
    rng = _seeded_rng(seed + 2)
    samples = []
    for _ in range(n):
        frames = [_generate_frame(width, height, rng) for _ in range(frames_per_video)]
        samples.append({
            "frames": frames,
            "resolution": (width, height),
        })
    return samples


# -----------------------------------------------------------------------
# Physiological generation
# -----------------------------------------------------------------------


def generate_physiological_samples(
    n: int = 10, seed: int = _DEFAULT_SEED
) -> list[dict]:
    """
    Generate n deterministic physiological signal snapshots.
    Each contains heart_rate, skin_temp, eda as raw float lists
    (list rather than scalar — allows the InputAcquisitionManager
    to store multi-sample windows).
    """
    rng = _seeded_rng(seed + 3)
    samples = []
    # Base physiological state that drifts slowly
    hr_base = 72.0
    temp_base = 36.5
    eda_base = 0.4

    for i in range(n):
        # Small deterministic drift
        hr_base += (rng.random() - 0.5) * 4.0
        hr_base = max(60.0, min(100.0, hr_base))

        temp_base += (rng.random() - 0.5) * 0.3
        temp_base = max(35.0, min(38.0, temp_base))

        eda_base += (rng.random() - 0.5) * 0.15
        eda_base = max(0.1, min(1.0, eda_base))

        # 10 sub-samples per snapshot (matching 10 Hz for 1 second)
        hr_values = [round(hr_base + (rng.random() - 0.5) * 2.0, 2) for _ in range(10)]
        temp_values = [round(temp_base + (rng.random() - 0.5) * 0.1, 3) for _ in range(10)]
        eda_values = [round(eda_base + (rng.random() - 0.5) * 0.05, 4) for _ in range(10)]

        samples.append({
            "signals": {
                "heart_rate": hr_values,
                "skin_temp": temp_values,
                "eda": eda_values,
            },
            "sampling_rate": 10,
        })
    return samples


# -----------------------------------------------------------------------
# Combined generator
# -----------------------------------------------------------------------


def generate_all(seed: int = _DEFAULT_SEED) -> dict:
    """
    Generate the full structured dummy dataset.

    Returns:
        {
            "text": [str, ...],              # 20 samples
            "audio": [{"waveform", "sample_rate"}, ...],   # 5 samples
            "video": [{"frames", "resolution"}, ...],      # 3 samples
            "physiological": [{"signals", "sampling_rate"}, ...]  # 10 samples
        }
    """
    return {
        "text": generate_text_samples(20, seed),
        "audio": generate_audio_samples(5, 1000, seed),
        "video": generate_video_samples(3, 10, 8, 8, seed),
        "physiological": generate_physiological_samples(10, seed),
    }


# -----------------------------------------------------------------------
# Bulk mixed-modality generator for stress testing
# -----------------------------------------------------------------------


def generate_bulk_inputs(n: int, seed: int = _DEFAULT_SEED) -> list[dict]:
    """
    Generate n mixed-modality raw inputs for stress testing.

    Each entry is a dict with:
        {"modality": str, "data": ..., "kwargs": {...}}

    Ready to be fed directly into InputAcquisitionManager.receive_*().

    Distribution: ~40% text, ~25% audio, ~15% video, ~20% physiological
    (weighted toward cheaper modalities for throughput).
    """
    rng = _seeded_rng(seed + 100)

    # Pre-generate pools to draw from
    text_pool = generate_text_samples(50, seed)
    # For audio/video/physio we generate inline to avoid huge memory

    results = []
    for i in range(n):
        roll = rng.random()

        if roll < 0.40:
            # --- Text ---
            text = rng.choice(text_pool)
            results.append({
                "modality": "text",
                "data": text,
                "kwargs": {},
            })

        elif roll < 0.65:
            # --- Audio ---
            length = 200  # shorter for bulk speed
            freq = 100.0 + rng.random() * 400.0
            amplitude = 0.2 + rng.random() * 0.7
            sr = rng.choice(_SAMPLE_RATES)
            waveform = []
            for j in range(length):
                t = j / sr
                val = amplitude * math.sin(2.0 * math.pi * freq * t)
                noise = (rng.random() - 0.5) * 0.08
                waveform.append(round(max(-1.0, min(1.0, val + noise)), 6))
            results.append({
                "modality": "audio",
                "data": waveform,
                "kwargs": {"sample_rate": sr},
            })

        elif roll < 0.80:
            # --- Video ---
            w, h = 4, 4
            frame_count = 3  # small for bulk speed
            frames = [
                [
                    [[rng.randint(0, 255) for _ in range(3)] for _ in range(w)]
                    for _ in range(h)
                ]
                for _ in range(frame_count)
            ]
            results.append({
                "modality": "video",
                "data": frames,
                "kwargs": {"resolution": (w, h)},
            })

        else:
            # --- Physiological ---
            hr = [round(60.0 + rng.random() * 40.0, 2) for _ in range(10)]
            temp = [round(35.0 + rng.random() * 3.0, 3) for _ in range(10)]
            eda = [round(0.1 + rng.random() * 0.9, 4) for _ in range(10)]
            results.append({
                "modality": "physiological",
                "data": {"heart_rate": hr, "skin_temp": temp, "eda": eda},
                "kwargs": {
                    "signal_type": "biometric",
                    "sampling_frequency": 10.0,
                },
            })

    return results


# -----------------------------------------------------------------------
# Helper: feed bulk inputs into an InputAcquisitionManager
# -----------------------------------------------------------------------


def feed_into_manager(manager, inputs: list[dict]):
    """
    Convenience function that takes the output of generate_bulk_inputs()
    and calls the appropriate manager.receive_*() for each entry.

    Returns a list of the created RawInput objects.
    """
    created = []
    for entry in inputs:
        mod = entry["modality"]
        data = entry["data"]
        kw = entry["kwargs"]

        if mod == "text":
            created.append(manager.receive_text(data))
        elif mod == "audio":
            created.append(manager.receive_audio(data, **kw))
        elif mod == "video":
            created.append(manager.receive_video(data, **kw))
        elif mod == "physiological":
            created.append(
                manager.receive_physiological(data, **kw)
            )
    return created


# -----------------------------------------------------------------------
# Quick self-test / example output when run directly
# -----------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("AURA Dummy Data Generator — Sample Output")
    print("=" * 60)

    data = generate_all()

    print(f"\n--- Text ({len(data['text'])} samples) ---")
    for i, t in enumerate(data["text"][:5]):
        print(f"  [{i}] {t}")
    print(f"  ... ({len(data['text']) - 5} more)")

    print(f"\n--- Audio ({len(data['audio'])} samples) ---")
    for i, a in enumerate(data["audio"]):
        w = a["waveform"]
        print(
            f"  [{i}] rate={a['sample_rate']}  samples={len(w)}  "
            f"range=[{min(w):.4f}, {max(w):.4f}]"
        )

    print(f"\n--- Video ({len(data['video'])} samples) ---")
    for i, v in enumerate(data["video"]):
        res = v["resolution"]
        print(
            f"  [{i}] frames={len(v['frames'])}  resolution={res[0]}x{res[1]}  "
            f"pixel_sample={v['frames'][0][0][0]}"
        )

    print(f"\n--- Physiological ({len(data['physiological'])} samples) ---")
    for i, p in enumerate(data["physiological"][:3]):
        s = p["signals"]
        print(
            f"  [{i}] hr={s['heart_rate'][0]:.1f}  "
            f"temp={s['skin_temp'][0]:.2f}  "
            f"eda={s['eda'][0]:.3f}  "
            f"rate={p['sampling_rate']}Hz"
        )
    print(f"  ... ({len(data['physiological']) - 3} more)")

    print(f"\n--- Bulk generator ---")
    bulk = generate_bulk_inputs(1000)
    from collections import Counter
    dist = Counter(e["modality"] for e in bulk)
    print(f"  Generated {len(bulk)} inputs: {dict(dist)}")

    print("\n--- Determinism check ---")
    bulk2 = generate_bulk_inputs(1000)
    match = all(
        a["modality"] == b["modality"] and a["data"] == b["data"]
        for a, b in zip(bulk, bulk2)
    )
    print(f"  Two runs identical: {match}")

    print("\nDone.")
