"""Transparent, reproducible acoustic comparison for same-text recordings.

Do NOT interpret deviations from a reference as proof of bad public speaking.
No speech recognition or forced word alignment is implemented here.
"""
from __future__ import annotations

import io
from math import gcd
from typing import Any

import librosa
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

SAMPLE_RATE = 16_000
HOP = 320   # 20 ms
FRAME = 640 # 40 ms
MAX_SECONDS = 40


def load_audio(source: bytes | str, sample_rate: int = SAMPLE_RATE) -> np.ndarray:
    """Load WAV/FLAC bytes or a local path; mono float, resampled to sample_rate."""
    if isinstance(source, bytes):
        audio, sr = sf.read(io.BytesIO(source), dtype="float32", always_2d=True)
    else:
        audio, sr = sf.read(source, dtype="float32", always_2d=True)
    if audio.size == 0 or sr <= 0:
        raise ValueError("Audio is empty or has an invalid sample rate.")
    if audio.shape[0] / sr > MAX_SECONDS:
        raise ValueError(f"Recordings must be at most {MAX_SECONDS} seconds.")
    mono = audio.mean(axis=1)
    if not np.isfinite(mono).all():
        raise ValueError("Audio contains non-finite sample values.")
    if sr != sample_rate:
        div = gcd(sr, sample_rate)
        mono = resample_poly(mono, sample_rate // div, sr // div)
    return np.ascontiguousarray(mono, dtype=np.float32)


def frame_features(audio: np.ndarray, sr: int = SAMPLE_RATE) -> dict[str, Any]:
    """Fixed-rate features. RMS and MFCC are computed without amplitude normalization."""
    if len(audio) < sr // 2:
        raise ValueError("Please provide at least 0.5 seconds of audio.")
    rms = librosa.feature.rms(y=audio, frame_length=FRAME, hop_length=HOP, center=True)[0]
    times = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=HOP)
    mfcc = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=13, n_fft=1024, hop_length=HOP)
    mfcc = mfcc[:, :len(rms)]
    db = 20 * np.log10(np.maximum(rms, 1e-7))
    # Pitch is an estimate (not a ground-truth or vocal-quality score).
    f0 = librosa.yin(audio, fmin=70, fmax=450, sr=sr, frame_length=1024, hop_length=HOP)
    f0 = f0[:len(rms)]
    active = rms >= max(0.007, float(np.percentile(rms, 95) * 0.09))
    pitch = np.where(active[:len(f0)], f0, np.nan)
    return {
        "times": times,
        "rms": rms,
        "db": db,
        "mfcc": mfcc,
        "pitch": pitch,
        "duration": len(audio) / sr,
        "sr": sr,
        "audio": audio,
    }


def _runs(mask: np.ndarray) -> list[tuple[int, int]]:
    padded = np.concatenate(([False], mask.astype(bool), [False]))
    starts = np.where(np.diff(padded.astype(np.int8)) == 1)[0]
    ends = np.where(np.diff(padded.astype(np.int8)) == -1)[0]
    return list(zip(starts.tolist(), ends.tolist()))


def silence_intervals(features: dict, min_length: float = 0.35) -> list[dict]:
    """Internal low-energy intervals; excludes leading and trailing silence.

    Threshold is relative to a high percentile with a noise floor. May fail in noise.
    """
    rms = features["rms"]
    threshold = max(0.007, float(np.percentile(rms, 95) * 0.09))
    # Smooth brief low-energy fragments within speech without bridging real gaps.
    low = rms < threshold
    result = []
    for start, end in _runs(low):
        a = max(0.0, start * HOP / SAMPLE_RATE)
        b = min(float(features["duration"]), end * HOP / SAMPLE_RATE)
        if a <= 0.12 or b >= features["duration"] - 0.12:
            continue
        if b - a >= min_length:
            result.append({"start":round(a,3), "end":round(b,3), "duration":round(b-a,3)})
    return result


def dtw_frame_map(reference: dict, attempt: dict) -> np.ndarray:
    """Map each attempt frame onto reference timeline by MFCC-DTW.

    This is *acoustic sequence alignment*, NOT transcript forced alignment.
    """
    x = reference["mfcc"]
    y = attempt["mfcc"]
    # Normalize each cepstral dimension using reference distribution, so c0
    # and channel gain do not dominate the cost matrix.
    mu = x.mean(axis=1, keepdims=True)
    sd = x.std(axis=1, keepdims=True) + 1e-5
    ref = (x - mu) / sd
    test = (y - mu) / sd
    _, path = librosa.sequence.dtw(X=ref, Y=test, metric="euclidean", backtrack=True)
    aligned = [[] for _ in range(y.shape[1])]
    for i, j in path:
        aligned[int(j)].append(int(i))
    out = np.zeros(y.shape[1], dtype=np.float32)
    known = []
    for j, indexes in enumerate(aligned):
        if indexes:
            out[j] = np.median(indexes)
            known.append(j)
    if len(known) < 2:
        raise ValueError("Insufficient audio structure to align recordings.")
    return np.interp(np.arange(len(out)), known, out[known]) * HOP / SAMPLE_RATE


def analyze_pair(reference_audio: np.ndarray, attempt_audio: np.ndarray) -> dict:
    """Analyze a reference and a same-text attempt with traceable measured outputs."""
    if not np.any(np.abs(reference_audio) > 0.002) or not np.any(np.abs(attempt_audio) > 0.002):
        raise ValueError("Both recordings need audible audio, not just silence.")
    ref = frame_features(reference_audio)
    test = frame_features(attempt_audio)
    ref_pauses = silence_intervals(ref)
    test_pauses = silence_intervals(test)
    mapping = dtw_frame_map(ref, test)
    events = []
    extra_pause = 0.0
    for p in test_pauses:
        start_idx = min(len(mapping)-1, max(0,int(p["start"]*SAMPLE_RATE/HOP)))
        end_idx = min(len(mapping)-1, max(start_idx+1,int(p["end"]*SAMPLE_RATE/HOP)))
        mapped = mapping[start_idx:end_idx+1]
        mapped_start = float(np.min(mapped))
        mapped_end = float(np.max(mapped))
        # Compare the mapped reference range, including a legitimate baseline pause.
        ref_span = max(0.0, mapped_end - mapped_start)
        difference = float(p["duration"] - ref_span)
        if difference >= 0.7 and p["duration"] >= 0.70:
            extra_pause += difference
            events.append({
                "type":"extra_pause", "start":p["start"], "end":p["end"],
                "observed":p["duration"], "reference":round(ref_span,2),
                "delta":round(difference,2),
                "explanation":f"Low-energy interval lasted {p['duration']:.2f}s; its aligned reference region spans {ref_span:.2f}s (difference +{difference:.2f}s).",
                "suggestion":"Rehearse the transition and confirm whether this longer pause is intentional.",
            })
    # Long pauses affect overall duration; correct for those before inferring rate.
    adjusted_attempt = max(0.5, test["duration"]-extra_pause)
    speed_ratio = ref["duration"] / adjusted_attempt
    if abs(speed_ratio-1) >= 0.18:
        word = "shorter" if speed_ratio > 1 else "longer"
        events.append({
            "type":"duration_difference", "start":0.0, "end":round(test["duration"],2),
            "observed":round(test["duration"],2), "reference":round(ref["duration"],2),
            "delta":round((speed_ratio-1)*100,1),
            "explanation":f"After adjusting for flagged pauses, the attempt's duration is {word} relative to the reference (estimated speed ratio {speed_ratio:.2f}x). This is not a word-per-minute measurement.",
            "suggestion":"Review speaking pace while preserving natural phrasing.",
        })
    def active_rms(f: dict) -> float:
        rms = f["rms"]
        threshold = max(0.007, float(np.percentile(rms, 95)*0.09))
        v = rms[rms >= threshold]
        return float(np.median(v)) if len(v) else 1e-7
    level_delta = 20*np.log10((active_rms(test)+1e-7)/(active_rms(ref)+1e-7))
    if abs(level_delta) >= 6:
        events.append({
            "type":"energy_difference", "start":0.0, "end":round(test["duration"],2),
            "observed":round(level_delta,2), "reference":0,
            "delta":round(level_delta,2),
            "explanation":f"Median active-speech RMS level differs by {level_delta:+.1f} dB from the reference. Mic distance or recording gain can cause this.",
            "suggestion":"Verify equal recording setups before interpreting level as a vocal-delivery difference.",
        })
    deviations = 100 - sum(22 for e in events if e['type']=='extra_pause') - sum(15 for e in events if e['type']=='duration_difference') - sum(7 for e in events if e['type']=='energy_difference')
    return {
        "ref":ref, "test":test, "events":sorted(events,key=lambda e:e["start"]),
        "ref_pauses":ref_pauses,"test_pauses":test_pauses,
        "mapping":mapping, "deviation_index":int(max(0,deviations)),
        "metrics":{
            "reference_duration_s":round(ref["duration"],2),
            "attempt_duration_s":round(test["duration"],2),
            "duration_ratio":round(speed_ratio,3),
            "relative_energy_db":round(float(level_delta),2),
            "extra_pause_count":sum(e["type"]=="extra_pause" for e in events),
        },
    }


def temporal_iou(a: tuple[float,float], b: tuple[float,float]) -> float:
    intersection = max(0.0,min(a[1],b[1])-max(a[0],b[0]))
    union = max(a[1],b[1])-min(a[0],b[0])
    return intersection/union if union>0 else 0.0


def evaluate_intervals(predicted: list[dict], truth: list[dict], min_iou: float=0.35) -> dict:
    """Greedy one-to-one matching by IoU, for comparable labeled event types."""
    predictions=[e for e in predicted if e["type"] == "extra_pause"]
    labels=[t for t in truth if t["type"] == "extra_pause"]
    matches=[]
    for pi,p in enumerate(predictions):
        for ti,t in enumerate(labels):
            overlap=temporal_iou((p["start"],p["end"]),(t["start"],t["end"]))
            if overlap >= min_iou:
                matches.append((overlap,pi,ti))
    matched_p=set();matched_t=set();ious=[]
    for v,pi,ti in sorted(matches, reverse=True):
        if pi in matched_p or ti in matched_t: continue
        matched_p.add(pi);matched_t.add(ti);ious.append(v)
    tp=len(ious);fp=len(predictions)-tp;fn=len(labels)-tp
    precision=tp/(tp+fp) if tp+fp else 1.0 if not labels else 0.0
    recall=tp/(tp+fn) if tp+fn else 1.0
    f1=2*precision*recall/(precision+recall) if precision+recall else 0.0
    return {"tp":tp,"fp":fp,"fn":fn,"precision":round(precision,3),"recall":round(recall,3),"f1":round(f1,3),"mean_iou":round(float(np.mean(ious)),3) if ious else 0.0}
