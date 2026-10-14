"""FastAPI v1 REST boundary for the SpeechTrace Gradio/MCP ecosystem.

Start locally: uvicorn service.api:app --host 127.0.0.1 --port 8000
Do NOT expose this service publicly without SPEECHTRACE_API_TOKEN, HTTPS and rate limiting.
Only opted-in reports are stored; audio uploads are temporary and deleted.
"""
from __future__ import annotations

import os
import secrets
import tempfile
from pathlib import Path

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .pipeline import analyze_rehearsal, compact_report
from .store import ReportStore

MAX_AUDIO_BYTES = 20 * 1024 * 1024
MAX_DECK_BYTES = 10 * 1024 * 1024
AUDIO_EXT = {".wav", ".flac", ".ogg"}
DECK_EXT = {".pdf", ".pptx", ".txt"}

app = FastAPI(title="SpeechTrace", version="0.4.0", description="Evidence-first English public-speaking rehearsal analyzer")


async def auth(authorization: str | None = Header(default=None)):
    token = os.getenv("SPEECHTRACE_API_TOKEN", "").strip()
    if token and not secrets.compare_digest(authorization or "", f"Bearer {token}"):
        raise HTTPException(status_code=401, detail="A valid API bearer token is required")


async def save_upload(upload: UploadFile, dest: Path, cap: int, allowed: set[str]) -> Path:
    ext = Path(upload.filename or "").suffix.lower()
    if ext not in allowed:
        raise HTTPException(status_code=415, detail=f"Expected file type in: {', '.join(sorted(allowed))}")
    dest = dest.with_suffix(ext)
    amount = 0
    with dest.open("wb") as target:
        while True:
            piece = await upload.read(1024 * 1024)
            if not piece:
                break
            amount += len(piece)
            if amount > cap:
                raise HTTPException(status_code=413, detail="Upload too large")
            target.write(piece)
    if amount == 0:
        raise HTTPException(status_code=422, detail="Empty upload")
    return dest


@app.get("/v1/health")
def health():
    return {"status": "ok", "service": "SpeechTrace", "version": "0.4.0",
            "capabilities": ["audio_acoustics", "transcript_fillers", "deck_keywords", "track_c_legacy"]}


@app.post("/v1/rehearsals", dependencies=[Depends(auth)])
async def create_rehearsal(
    audio: UploadFile = File(...), deck: UploadFile | None = File(default=None),
    goal: str = Form(default=""), manual_transcript: str = Form(default=""),
    provider: str = Form(default="Manual transcript"),
    remote_audio_consent: bool = Form(default=False),
    external_text_review_consent: bool = Form(default=False),
    persist_report: bool = Form(default=False),
):
    if len(goal) > 600 or len(manual_transcript) > 24000:
        raise HTTPException(status_code=422, detail="Goal/transcript length limit exceeded")
    with tempfile.TemporaryDirectory(prefix="speechtrace_upload_") as tmp:
        folder = Path(tmp)
        audio_path = await save_upload(audio, folder / "speech", MAX_AUDIO_BYTES, AUDIO_EXT)
        deck_path = (await save_upload(deck, folder / "deck", MAX_DECK_BYTES, DECK_EXT)) if deck else None
        try:
            report = analyze_rehearsal(audio_path, transcript_provider=provider,
                                       manual_transcript=manual_transcript, deck_path=deck_path,
                                       goal=goal, remote_audio_consent=remote_audio_consent,
                                       external_text_review_consent=external_text_review_consent)
        except (ValueError, RuntimeError, ImportError, OSError) as exc:
            raise HTTPException(status_code=422, detail=str(exc)[:300]) from exc
        except Exception as exc:
            # Never expose server paths or provider secrets in a public error response.
            raise HTTPException(status_code=500, detail="Analysis failed; check server logs") from exc
    response = compact_report(report)
    report_id = ReportStore().save(response) if persist_report else None
    return JSONResponse(content={"rehearsal_id": report_id, "report": response,
                                 "persisted": bool(report_id), "report_ttl_seconds": ReportStore().ttl_seconds if report_id else None})


@app.get("/v1/rehearsals/{rehearsal_id}/report", dependencies=[Depends(auth)])
def get_report(rehearsal_id: str):
    report = ReportStore().get(rehearsal_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found or expired")
    return report


@app.get("/v1/rehearsals/{rehearsal_id}/events", dependencies=[Depends(auth)])
def get_events(rehearsal_id: str):
    report = ReportStore().get(rehearsal_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found or expired")
    return {"rehearsal_id": rehearsal_id, "events": report.get("events", [])}


@app.delete("/v1/rehearsals/{rehearsal_id}", dependencies=[Depends(auth)])
def delete_report(rehearsal_id: str):
    if not ReportStore().delete(rehearsal_id):
        raise HTTPException(status_code=404, detail="Report not found or expired")
    return {"deleted": True}
