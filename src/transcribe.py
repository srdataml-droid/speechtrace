"""Optional English ASR. Downloading a model and CPU inference need network/resources.

ASR can omit fillers; human editing should not fabricate timings.
"""
from __future__ import annotations
import os
from functools import lru_cache
import numpy as np

@lru_cache(maxsize=1)
def model():
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise RuntimeError("Automatic speech recognition is not installed. Install requirements-asr.txt or supply the transcript yourself.") from exc
    name = os.getenv("SPEECHTRACE_ASR_MODEL", "base.en")
    return WhisperModel(name, device=os.getenv("SPEECHTRACE_DEVICE", "cpu"), compute_type="int8")

def recognize(audio: np.ndarray) -> tuple[str, list[dict]]:
    try:
        segments, _ = model().transcribe(audio, language="en", word_timestamps=True, vad_filter=False,
                                         beam_size=3, condition_on_previous_text=False)
        segs = list(segments)
        word_segments=[]
        for seg in segs:
            for word in seg.words or []:
                if word.start is not None and word.end is not None:
                    word_segments.append({"word":word.word.strip(),"start":round(word.start,2),"end":round(word.end,2)})
        return " ".join(s.text.strip() for s in segs),word_segments
    except Exception as exc:
        raise RuntimeError(f"Automatic transcription unavailable. Retry with a manual transcript. ({type(exc).__name__})") from exc
