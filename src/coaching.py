"""SpeechTrace Coach v0.2: rule-based, inspectable acoustic/text/slide feedback.

This module DOES NOT infer emotions, factual correctness, intent, persuasiveness,
or speech quality. Evidence flags require human review; no trained coach model.
"""
from __future__ import annotations

from collections import Counter
from math import gcd
import re
from pathlib import Path
from typing import Any

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

SR = 16000
MAX_SECONDS = 180
HOP = 320
FRAME = 640
FILLERS = {"um", "uh", "erm", "er", "uhh", "umm", "ahh"}
STOP = set("a an the and or for from with without to of in on at by as it is are was were be this that those these we our you your i my me they their do does did have has had can will would should could what where when why how into about there here then than now not only just using use data ai one two three some many all more most much project product solution platform system".split())


def normalize_word(s: str) -> str:
    return re.sub(r"[^a-z]", "", (s or "").lower())


def words(text: str) -> list[str]:
    return re.findall(r"[a-z]+(?:'[a-z]+)?", (text or "").lower())


def read_audio(path: str, max_seconds: int = MAX_SECONDS) -> np.ndarray:
    """Load a mono stream, bounded to protect shared demos. Use WAV/FLAC/OGG."""
    if not path:
        raise ValueError("Record or upload a WAV, FLAC or OGG rehearsal.")
    with sf.SoundFile(str(path)) as file:
        sr = file.samplerate
        n = len(file)
        if n / sr > max_seconds:
            raise ValueError(f"Audio exceeds the {max_seconds} second prototype limit.")
        if n / sr < 1.0:
            raise ValueError("Please record at least one second.")
        if n == 0:
            raise ValueError("The recording is empty.")
        channels = file.read(dtype="float32", always_2d=True)
    audio = np.mean(channels, axis=1)
    if not np.isfinite(audio).all():
        raise ValueError("Recording contains invalid audio samples.")
    if sr != SR:
        d = gcd(sr, SR)
        audio = resample_poly(audio, SR // d, sr // d)
    return np.ascontiguousarray(audio, dtype=np.float32)


def runs(mask: np.ndarray) -> list[tuple[int, int]]:
    mask = np.asarray(mask, dtype=bool)
    boundary = np.diff(np.r_[False, mask, False].astype(np.int8))
    return list(zip(np.flatnonzero(boundary == 1).tolist(), np.flatnonzero(boundary == -1).tolist()))


def acoustic_evidence(signal: np.ndarray, sr: int = SR) -> dict[str, Any]:
    """Energy envelope and silence evidence; relative measures, not psychological states."""
    if len(signal) < sr:
        raise ValueError("Recording is too short for a meaningful rehearsal analysis.")
    # Efficient, padding-free analysis. A silence contains ~0.64s or more low-energy frames.
    frame_count = 1 + max(0, (len(signal) - FRAME) // HOP)
    framed = np.lib.stride_tricks.as_strided(
        signal, shape=(frame_count, FRAME), strides=(signal.strides[0] * HOP, signal.strides[0]), writeable=False
    )
    rms = np.sqrt(np.mean(framed.astype(np.float64) ** 2, axis=1))
    timestamps = np.arange(frame_count) * HOP / sr
    loud = 20 * np.log10(np.maximum(rms, 1e-7))
    threshold = max(0.004, float(np.percentile(rms, 90) * 0.12))
    active = rms > threshold
    duration = round(len(signal) / sr, 3)
    pauses: list[dict] = []
    for left, right in runs(~active):
        start = float(timestamps[left])
        end = min(duration, float((right - 1) * HOP / sr + FRAME / sr))
        if start < 0.15 or end > duration - 0.15:
            continue  # Leading/trailing silence isn't automatically a speaking flaw.
        if end - start >= 0.6:
            pauses.append({"type": "low_energy_interval", "start": round(start, 2),
                           "end": round(end, 2), "seconds": round(end-start, 2),
                           "reason": "Relative signal amplitude was low. This may be a deliberate pause or silence."})
    windows = []
    for start in np.arange(0, duration, 4.0):
        mask = (timestamps >= start) & (timestamps < start + 4)
        if mask.sum() < 5:
            continue
        segment_active = active[mask]
        windows.append({"start": round(float(start), 1), "end": round(float(min(duration, start+4)),1),
                        "median_rms": round(float(np.median(rms[mask][segment_active])) if segment_active.any() else 0.0, 5),
                        "activity_fraction": round(float(np.mean(segment_active)), 3)})
    active_median = float(np.median(rms[active])) if active.any() else 0
    # Only relative to one recording. Gain and mic distance can strongly affect it.
    quiet_windows = [x for x in windows if active_median > 0 and x['activity_fraction'] > 0.45
                     and x['median_rms'] < active_median * 0.42]
    events = list(pauses)
    for w in quiet_windows:
        events.append({"type": "relative_low_energy", "start": w["start"], "end": w["end"],
                       "reason": "This window has comparatively low amplitude within this same recording. Check audibility; mic position can cause it."})
    return {"duration_s": duration, "active_s": round(float(active.sum() * HOP / sr), 2),
            "pause_count": len(pauses), "threshold_rms": round(threshold, 5),
            "timestamps_s": timestamps.tolist(), "rms_dbfs": loud.tolist(),
            "windows": windows, "events": sorted(events, key=lambda x: x["start"]),
            "limitations": ["Amplitude is microphone-dependent, not emotion or confidence.",
                            "Low-energy events are not necessarily mistakes.",
                            "Quiet/noisy recordings may yield false flags."]}


def transcript_evidence(text: str, duration_s: float, aligned_words: list[dict] | None = None) -> dict:
    """Filled-pause lexicon, speech rate, time-specific bursts when aligned words exist."""
    word_list = words(text)
    if not text.strip():
        return {"words":0, "wpm_total":None, "filler_count":None, "fillers":[], "bursts":[],
                "notes":["No transcript: filler/word-rate and content checks were not performed."]}
    fillers = []
    for i, token in enumerate(word_list):
        if normalize_word(token) in FILLERS:
            fillers.append({"token":token,"index":i,"start":None,"end":None,
                            "review":"Potential hesitation marker. Repeated 'um' or 'uh' may distract; not every instance is a flaw."})
    bursts=[]
    if aligned_words:
        aligned = []
        for obj in aligned_words:
            try:
                start,end=float(obj["start"]),float(obj["end"])
                token=normalize_word(str(obj["word"]))
            except (ValueError, TypeError, KeyError):
                continue
            if end>=start and token:
                aligned.append({"token":token,"start":start,"end":end})
        # Align filler tokens by POSITION only if the ASR text matches this transcript
        # (manual edited transcripts are deliberately not assigned fabricated timestamps).
        if [x["token"] for x in aligned] == [normalize_word(w) for w in word_list]:
            for item, match in zip(fillers, [x for x in aligned if x["token"] in FILLERS]):
                item["start"], item["end"] = round(match["start"],2),round(match["end"],2)
        # 5-second rolling speaking rate, only if timestamps actually provided.
        for start in np.arange(0, max(duration_s-4,0), 2.5):
            segment=[x for x in aligned if x["start"]>=start and x["start"]<start+5]
            if len(segment)>=18:  # >= 216 WPM in a five-second period, heuristic not quality judge
                bursts.append({"start":round(float(start),2),"end":round(float(start+5),2),
                               "estimated_wpm":int(round(len(segment)*12)),
                               "review":"Fast local word rate; replay to check intelligibility."})
    note="Overall words/minute includes pauses and is a rough estimate, not articulation quality."
    if aligned_words:
        note += " Word timestamps are approximate and may omit fillers."
    else:
        note += " Without aligned words, individual fillers cannot be timestamped."
    return {"words":len(word_list),"wpm_total":round(len(word_list)/(duration_s/60),1) if duration_s>0 else None,
            "filler_count":len(fillers),"fillers":fillers,"bursts":bursts,"notes":[note]}


def deck_evidence(text: str, slides: list[dict], goal: str = "") -> dict:
    """Only literal word overlap; NEVER claim semantic or factual correctness."""
    combined = set(w for w in words(text) if len(w)>3 and w not in STOP)
    coverage = []
    for slide in slides:
        content=slide.get("text", "")
        tokens = [w for w in words(content) if len(w)>3 and w not in STOP]
        key_terms = [item for item, _ in Counter(tokens).most_common(12)]
        overlaps = [w for w in key_terms if w in combined]
        coverage.append({"slide": slide.get("number"), "title": (content.splitlines() or ["Untitled"])[0][:100],
                         "matched_keywords":overlaps, "missing_keywords":[w for w in key_terms if w not in combined],
                         "keyword_coverage": round(len(overlaps)/len(key_terms),2) if key_terms else None})
    return {"slides":coverage,"goal":goal,
            "limitations":["Keyword overlap is NOT semantic alignment, proof of omission, or fact checking.",
                           "Synonyms, paraphrases and figure-only slides can produce false omissions."]}


def suggested_structure(goal: str, slides: list[dict], has_transcript: bool) -> list[str]:
    """A teaching scaffold, NOT an AI rewrite or automatic storytelling verdict."""
    titles = [x.get("text", "").splitlines()[0].strip() for x in slides if x.get("text", "").strip()]
    references = ", ".join(titles[:4]) or "your topic"
    audience = goal or "the intended audience"
    return [
        f"Opening (10–20 s): name the audience problem for {audience}; use a real, sourced example only if available.",
        f"Problem / significance: make one concrete claim and support it using the slides ({references}).",
        "Solution: show one user action, system response, and the benefit; avoid vague AI claims.",
        "Evidence: distinguish measured pilot results from projections; never invent statistics.",
        "Closing: explain the intended impact and one specific ask or next step.",
    ] if has_transcript else ["Record the rehearsal or provide its actual transcript before offering content guidance."]


def coach(signal: np.ndarray, transcript: str = "", aligned_words: list[dict] | None = None,
          slides: list[dict] | None = None, goal: str = "") -> dict:
    acoustics=acoustic_evidence(signal)
    language=transcript_evidence(transcript, acoustics["duration_s"],aligned_words)
    deck=deck_evidence(transcript,slides or [],goal)
    notices=[]
    if acoustics["pause_count"]:
        notices.append(f"Review {acoustics['pause_count']} detected low-energy interval(s), including intentional pauses.")
    if language["filler_count"] is not None:
        notices.append(f"Review {language['filler_count']} likely filled-pause token(s) in the transcript.")
    if language["bursts"]:
        notices.append(f"Replay {len(language['bursts'])} fast word-rate window(s) and check actual clarity.")
    if slides:
        notices.append("Review slide keyword coverage; no factual or semantic conclusion is implied.")
    return {"version":"SpeechTrace Coach v0.2 prototype", "goal":goal, "transcript":transcript,
            "acoustics":acoustics,"language":language,"deck":deck,
            "suggestions":notices,"pitch_structure":suggested_structure(goal,slides or [],bool(transcript.strip())),
            "not_implemented":["Reliable emotion or attention detection", "Objective persuasive-performance grading",
                               "Independent web fact checking", "Model-trained storytelling judgment"]}
