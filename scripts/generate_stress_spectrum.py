"""Regenerate graded same-text synthetic audio perturbations.

Source: data/reference/ideal.wav (original eSpeak demo).
This is a controlled robustness dataset, not a public-speaking quality benchmark.
Run: python scripts/generate_stress_spectrum.py
Requires numpy + soundfile from the existing analysis dependencies.
"""
from __future__ import annotations

import json
from pathlib import Path
import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parent.parent
REFERENCE = ROOT / "data/reference/ideal.wav"
DEST = ROOT / "data/spectrum"
PAUSES = [("pause_045", 0.45, "subtle"), ("pause_085", 0.85, "medium"), ("pause_140", 1.40, "strong")]
LEVELS = [("gain_085", 0.85, "subtle"), ("gain_060", 0.60, "medium"), ("gain_040", 0.40, "strong")]
TRANSCRIPT = ("Our ideas become stronger when we test them carefully. "
              "Evidence matters more than confidence, and practice makes every presentation clearer.")

def regenerate():
    signal, sr = sf.read(REFERENCE, dtype="float32", always_2d=True)
    if signal.shape[1] != 1 or sr != 16000:
        raise ValueError("Expected mono 16 kHz reference")
    x = signal[:, 0]
    # Preserve the near-silence location selection from the original generator.
    target = int(len(x) * 0.48)
    half_window = int(sr * 0.25)
    left, right = max(0, target - half_window), min(len(x), target + half_window)
    idx = left + int(np.argmin(np.abs(x[left:right])))
    DEST.mkdir(parents=True, exist_ok=True)
    records = []
    for slug, seconds, intensity in PAUSES:
        samples = round(seconds * sr)
        altered = np.concatenate((x[:idx], np.zeros(samples, np.float32), x[idx:]))
        sf.write(DEST / f"{slug}.wav", altered, sr, subtype="PCM_16")
        records.append(dict(id=slug, path=f"data/spectrum/{slug}.wav",
            category="extra_pause", intensity=intensity,
            perturbation={"inserted_silence_s": seconds},
            events=[{"type":"extra_pause", "start":round(idx/sr,3),
                     "end":round((idx+samples)/sr,3)}],
            label_source="deterministic signal edit"))
    for slug, gain, intensity in LEVELS:
        altered = np.clip(x * gain, -1, 1)
        sf.write(DEST / f"{slug}.wav", altered, sr, subtype="PCM_16")
        records.append(dict(id=slug, path=f"data/spectrum/{slug}.wav",
            category="energy_difference", intensity=intensity,
            perturbation={"gain":gain, "delta_db":round(20*np.log10(gain),2)},
            events=[{"type":"energy_difference", "start":0,
                     "end":round(len(x)/sr,3)}],
            label_source="deterministic signal edit"))
    # Existing three demo files are preserved; compare with full manifest.
    path = DEST / "regenerated_labels.json"
    path.write_text(json.dumps({"reference":"data/reference/ideal.wav",
        "sample_rate":sr,"transcript":TRANSCRIPT,"cases":records},
        indent=2)+"\n", encoding="utf-8")
    print(f"Regenerated {len(records)} synthetic cases; labels in {path}")

if __name__ == "__main__":
    regenerate()
