"""Evaluate deterministic acoustic deviations on the graded stress spectrum.

Run from repository root: python scripts/evaluate_stress_spectrum.py
Outputs JSON with per-example predicted events, detection and temporal overlap.
No real-speaker validation is implied by synthetic performance.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from src.analysis import analyze_pair, load_audio, evaluate_intervals  # noqa: E402

MANIFEST = ROOT / "data/spectrum/manifest.json"

def run():
    meta = json.loads(MANIFEST.read_text(encoding="utf-8"))
    reference = load_audio(str(ROOT / meta["reference"]))
    results = []
    for entry in meta["cases"]:
        output = {"id":entry["id"], "intensity":entry["intensity"],
                  "injected_category":entry["category"]}
        try:
            observed = analyze_pair(reference, load_audio(str(ROOT / entry["path"])))
            predicted = observed["events"]
            output["predicted_events"] = predicted
            output["category_detected"] = any(
                item["type"] == entry["category"] for item in predicted)
            output["prototype_deviation_index"] = observed["deviation_index"]
            if entry["category"] == "extra_pause":
                output["temporal_evaluation"] = evaluate_intervals(
                    predicted, entry["events"])
        except (ValueError, RuntimeError, OSError) as error:
            output["error"] = str(error)
        results.append(output)
    document = {
        "method": "Synthetic controlled-case audit; no independent ground truth on natural human recordings",
        "reference":meta["reference"], "cases":results,
        "note":"Scores are arbitrary prototype heuristics; silence may be intentional and gain depends on the microphone."
    }
    DEST = ROOT / "data/spectrum/evaluation_latest.json"
    DEST.write_text(json.dumps(document, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({"examples":len(results),
        "category_detections":sum(1 for x in results if x.get("category_detected")),
        "errors":sum(1 for x in results if "error" in x),"report":str(DEST)}, indent=2))

if __name__ == "__main__":
    run()
