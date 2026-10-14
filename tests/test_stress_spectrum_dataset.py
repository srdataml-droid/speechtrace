"""Check checked-in stress-spectrum assets without calling ML or downloading models."""
from __future__ import annotations
from array import array
import json
from pathlib import Path
import wave

ROOT=Path(__file__).resolve().parents[1]
MANIFEST=json.loads((ROOT/"data/spectrum/manifest.json").read_text(encoding="utf-8"))

def wav_samples(path):
    with wave.open(str(path),"rb") as stream:
        assert stream.getnchannels()==1
        assert stream.getframerate()==16000
        assert stream.getsampwidth()==2
        count=stream.getnframes()
        samples=array("h",stream.readframes(count))
    return samples

def test_manifest_contains_matching_reference_and_nine_cases():
    assert MANIFEST["same_text_all_examples"] is True
    assert len(MANIFEST["cases"]) == 9
    assert (ROOT/MANIFEST["reference"]).exists()
    assert all((ROOT/item["path"]).exists() for item in MANIFEST["cases"])

def test_new_pause_labels_match_actual_inserted_silence():
    original=wav_samples(ROOT/MANIFEST["reference"])
    for item in MANIFEST["cases"]:
        if not item["id"].startswith("pause_"):
            continue
        altered=wav_samples(ROOT/item["path"])
        label=item["events"][0]
        start=round(label["start"]*16000)
        count=round(item["perturbation"]["inserted_silence_s"]*16000)
        assert len(altered)==len(original)+count
        # Manifest seconds rounded to 3 decimals: at most 8-sample boundary mismatch.
        assert all(sample==0 for sample in altered[start+8:start+count-8])
        assert list(altered[:start-8])==list(original[:start-8])
        assert list(altered[start+count+8:])==list(original[start+8:])

def test_new_gain_cases_preserve_timing_and_scale_signal():
    original=wav_samples(ROOT/MANIFEST["reference"])
    for item in MANIFEST["cases"]:
        if not item["id"].startswith("gain_"):
            continue
        altered=wav_samples(ROOT/item["path"])
        gain=item["perturbation"]["gain"]
        assert len(altered)==len(original)
        # Rounding differences at half-integer samples can be one least significant bit.
        assert max(abs(int(a)-round(int(b)*gain)) for a,b in zip(altered,original))<=1
