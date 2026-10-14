"""Transparent reference-relative acoustic *similarity*, not performance quality.

Weights, thresholds and ranges are illustrative and unvalidated. Do not
compare scores across microphones, speakers, rooms, or different transcripts.
"""
from __future__ import annotations
import math


def score_relative_delivery(result: dict) -> dict:
    """Return independent reference-relative signal components and a weighted index.

    Pause: 25 points per extra second + 8 points per detected extra pause.
    Pace: 180 points per absolute natural log of duration ratio.
    Level: 8 points per absolute dB difference.
    Values are clipped to 0–100. Overall is 45% pause, 35% pace, 20% level.

    Higher = closer to the chosen reference in these three aspects only.
    """
    events = result["events"]
    metrics = result["metrics"]
    extra = [e for e in events if e["type"] == "extra_pause"]
    extra_duration = sum(max(0.0, float(e.get("delta", 0.0))) for e in extra)
    rate = float(metrics["duration_ratio"])
    gain = float(metrics["relative_energy_db"])
    if not math.isfinite(rate) or rate <= 0 or not math.isfinite(gain):
        raise ValueError("Expected a valid positive duration ratio and finite level delta")
    clip = lambda p: round(max(0.0, min(100.0, 100.0 - p)), 1)
    scores = {
        "pause": clip(25 * extra_duration + 8 * len(extra)),
        "relative_pace": clip(180 * abs(math.log(rate))),
        "recording_level": clip(8 * abs(gain)),
    }
    combined = round(0.45 * scores["pause"] +
                     0.35 * scores["relative_pace"] +
                     0.20 * scores["recording_level"], 1)
    return {
        "label": "Unvalidated reference-relative acoustic similarity, NOT speaking quality",
        "scores": scores,
        "combined_reference_similarity": combined,
        "weights": {"pause":0.45, "relative_pace":0.35, "recording_level":0.20},
        "formula": "Pause=100-25*extra_s-8*count; Pace=100-180*abs(ln(duration_ratio)); Level=100-8*abs(dB); each clipped [0,100]",
        "caveats": [
            "Recording-level score confounds vocal loudness, microphone gain, and distance.",
            "Reference speech is not automatically good delivery.",
            "Different speakers and recording setups are not normalized for scoring.",
            "A deliberate rhetorical pause may be appropriate.",
            "This rubric was chosen manually, not learned or validated with human judges."
        ],
    }
