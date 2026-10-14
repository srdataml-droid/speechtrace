"""SpeechTrace lightweight English transcription endpoint.

This is a minimal, deliberately separate speech-to-text service for the mobile app.
It never stores recordings or raw transcripts. Temporary audio files are deleted.
"""
from __future__ import annotations

import asyncio
import logging
import os
import tempfile
from functools import lru_cache
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

MAX_BYTES = 12 * 1024 * 1024
MAX_AUDIO_SECONDS = 100
ALLOWED_SUFFIXES = {'.wav', '.webm', '.ogg', '.mp4', '.m4a', '.mp3'}
ALLOWED_ORIGINS = [
    'https://speechtrace-mobile-lab.vercel.app',
    'https://speechtrace-mobile-lab-srdataml-droids-projects.vercel.app',
]

app = FastAPI(title='SpeechTrace Transcription Service', version='0.6', docs_url=None, redoc_url=None)
app.add_middleware(CORSMiddleware, allow_origins=ALLOWED_ORIGINS, allow_methods=['POST', 'GET'],
                   allow_headers=['Content-Type'], max_age=86400)


class Word(BaseModel):
    text: str
    start: float
    end: float
    confidence: float | None = None


class TranscriptResponse(BaseModel):
    transcript: str
    words: list[Word]
    duration_seconds: float | None = None
    model: str
    warning: str


@lru_cache(maxsize=1)
def get_model():
    from faster_whisper import WhisperModel
    return WhisperModel(
        os.getenv('SPEECHTRACE_ASR_MODEL', 'tiny.en'),
        device='cpu', compute_type='int8', cpu_threads=2, num_workers=1,
    )


def infer(path: str) -> dict:
    from faster_whisper.audio import decode_audio
    # Decode first so corrupted files and excessively long input fail before inference.
    audio = decode_audio(path, sampling_rate=16000)
    duration = round(len(audio) / 16000, 2)
    if duration < 1.0:
        raise ValueError('Recording is too short. Please speak for at least two seconds.')
    if duration > MAX_AUDIO_SECONDS:
        raise ValueError('Please record 100 seconds or less for the first mobile test.')
    segments, _ = get_model().transcribe(audio, language='en',
                                         beam_size=2, best_of=2, vad_filter=False,
                                         word_timestamps=True,
                                         condition_on_previous_text=False)
    recognized = list(segments)
    text = ' '.join(s.text.strip() for s in recognized).strip()
    words = []
    for s in recognized:
        for w in s.words or []:
            if w.start is None or w.end is None:
                continue
            words.append({'text': w.word.strip(), 'start': round(float(w.start), 2),
                          'end': round(float(w.end), 2),
                          'confidence': round(float(w.probability), 3) if w.probability is not None else None})
    return {'transcript': text, 'words': words, 'duration_seconds': duration,
            'model': 'faster-whisper-tiny.en',
            'warning': 'Automatic transcription can mishear accents or omit filler words. Edit the transcript before reviewing.'}


@app.get('/health')
def health():
    return {'ok': True, 'service': 'speechtrace-transcription', 'asr_model': os.getenv('SPEECHTRACE_ASR_MODEL', 'tiny.en')}


@app.post('/v1/transcribe', response_model=TranscriptResponse)
async def transcribe(audio: UploadFile = File(...)):
    suffix = Path(audio.filename or '').suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(status_code=415, detail='Unsupported audio format. Record again in Chrome.')
    raw = await audio.read(MAX_BYTES + 1)
    await audio.close()
    if len(raw) > MAX_BYTES:
        raise HTTPException(status_code=413, detail='Audio file is too large. Record 100 seconds or less.')
    if not raw:
        raise HTTPException(status_code=422, detail='No audio received. Please record again.')
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, prefix='st_asr_') as f:
        path = f.name
        f.write(raw)
    try:
        try:
            result = await asyncio.to_thread(infer, path)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except Exception as exc:
            # Avoid exposing service internals in public errors.
            raise HTTPException(status_code=503, detail='Speech recognition is temporarily unavailable. Please retry in a moment.') from exc
        if not result['transcript']:
            raise HTTPException(status_code=422, detail='Could not recognize clear speech. Please retry closer to the microphone.')
        return result
    finally:
        Path(path).unlink(missing_ok=True)

@app.on_event('startup')
async def _prewarm_asr():
    """Background sample transcription to warm weights and validate inference."""
    if os.getenv('SPEECHTRACE_ASR_PREWARM','1') not in {'1','true','yes'}:
        return
    async def check():
        try:
            path = str(Path(__file__).resolve().parent / 'data/reference/ideal.wav')
            result = await asyncio.to_thread(infer, path)
            logging.getLogger('uvicorn.error').info(
                'ASR_SMOKE_PASS words=%s duration_s=%s',
                len(result['transcript'].split()), result['duration_seconds'])
        except Exception as exc:
            logging.getLogger('uvicorn.error').exception('ASR_SMOKE_FAILED: %s', type(exc).__name__)
    asyncio.create_task(check())
