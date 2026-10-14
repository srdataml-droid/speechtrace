"""Common speech analysis pipeline: Gradio, REST, and future MCP share this entry point.

This pipeline observes acoustic/text signals and makes no claim to infer emotion,
truth, speaker competence or audience reaction. Remote audio/text transfers require
separate explicit consent.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from src.coaching import coach, read_audio
from src.content_review import review_with_openai
from src.deck import slides_from_file
from src.providers import REMOTE_PROVIDERS, transcribe


def normalize_events(report: dict[str, Any]) -> list[dict[str, Any]]:
    """Timestamped audio events and optional ASR word events in a stable schema.

    Transcript-only fillers retain start/end=None; never fabricate alignments.
    """
    events = []
    for source, kind, items in (
        ("waveform", "acoustic", report["acoustics"]["events"]),
        ("transcript", "filler", report["language"]["fillers"]),
        ("word_timestamps", "pacing", report["language"]["bursts"]),
    ):
        for item in items:
            item_type = item.get("type") or ("potential_filler" if kind == "filler" else "fast_word_rate")
            start = item.get("start")
            end = item.get("end")
            events.append({
                "id": f"event-{len(events)+1:04d}", "category": kind,
                "type": item_type, "start_s": start, "end_s": end,
                "evidence_source": source if start is not None else "transcript_untimed",
                "measurement": {k: v for k, v in item.items() if k not in {"reason", "review"}},
                "interpretation": item.get("reason") or item.get("review", "Review this observation."),
                "certainty": "measured_signal" if kind == "acoustic" else "asr_or_transcript_based",
            })
    return sorted(events, key=lambda x: (x["start_s"] is None, x["start_s"] or 0))


def analyze_rehearsal(
    audio_path: str | Path, *, transcript_provider: str = "Manual transcript",
    manual_transcript: str = "", deck_path: str | Path | None = None,
    goal: str = "", remote_audio_consent: bool = False,
    external_text_review_consent: bool = False,
) -> dict[str, Any]:
    """Analyze one English rehearsal and return report dict (no retained audio)."""
    audio = read_audio(str(audio_path))
    slides = slides_from_file(str(deck_path) if deck_path else None)
    speech = transcribe(audio, transcript_provider, manual_transcript,
                        remote_consent=remote_audio_consent)
    report = coach(audio, speech.text, aligned_words=speech.words,
                   slides=slides, goal=(goal or "").strip())
    report["transcript_source"] = f"{speech.provider}: {speech.note}"
    report["speech_provider"] = speech.provider
    report["remote_audio_sent"] = speech.provider in REMOTE_PROVIDERS
    report["events"] = normalize_events(report)
    raw_events = report["acoustics"]["events"] + report["language"]["fillers"] + report["language"]["bursts"]
    report["external_llm_review"] = review_with_openai(
        speech.text, slides, goal, raw_events, external_text_review_consent
    ) if external_text_review_consent else "Not requested."
    report["data_handling"] = {
        "audio_retained_in_report": False,
        "remote_audio_sent": report["remote_audio_sent"],
        "external_text_review_requested": bool(external_text_review_consent),
        "slides_included_as_extracted_text": False,
    }
    return report


def compact_report(report: dict[str, Any]) -> dict[str, Any]:
    """Exclude high-volume plotting traces from JSON APIs and MCP responses."""
    return {
        **report,
        "acoustics": {k: v for k, v in report["acoustics"].items()
                      if k not in {"rms_dbfs", "timestamps_s"}},
    }
