"""Opt-in English speech recognition adapters.

Only the selected provider receives audio. Keys are server environment variables,
never browser fields or report content. Manual and local modes send nothing outward.
All provider outputs become the same {text, words:[{word,start,end}], provider} shape.
"""
from __future__ import annotations

import io
import os
import time
import wave
from dataclasses import dataclass
from typing import Callable

import numpy as np

from .transcribe import recognize

REMOTE_PROVIDERS = {"AssemblyAI", "Deepgram", "OpenAI Whisper"}
PROVIDERS = ["Manual transcript", "Local faster-whisper", "AssemblyAI", "Deepgram", "OpenAI Whisper"]


@dataclass(frozen=True)
class TranscriptResult:
    text: str
    words: list[dict]
    provider: str
    note: str


def wav_bytes(audio: np.ndarray, sample_rate: int = 16000) -> bytes:
    """API-safe little-endian PCM16 mono WAV from an already normalized waveform."""
    audio = np.asarray(audio, dtype=np.float32)
    if audio.ndim != 1 or len(audio) == 0 or not np.isfinite(audio).all():
        raise ValueError("Expected a nonempty finite mono waveform")
    pcm = (np.clip(audio, -1.0, 1.0) * 32767).astype('<i2')
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(pcm.tobytes())
    return buf.getvalue()


def clean_words(rows: list[dict], scale: float = 1.0) -> list[dict]:
    out = []
    for row in rows or []:
        try:
            word = str(row.get('word') or row.get('text') or '').strip()
            start = float(row['start']) * scale
            end = float(row['end']) * scale
            if word and 0 <= start <= end:
                out.append({'word': word, 'start': round(start, 3), 'end': round(end, 3)})
        except (TypeError, ValueError, KeyError):
            continue
    return out


def transcribe_assemblyai(audio: np.ndarray, *, requester=None, sleep: Callable[[float], None] = time.sleep,
                          timeout_s: int = 100) -> TranscriptResult:
    key = os.getenv('ASSEMBLYAI_API_KEY')
    if not key:
        raise RuntimeError('ASSEMBLYAI_API_KEY not set on the server.')
    if requester is None:
        import requests
        requester = requests
    api = os.getenv('ASSEMBLYAI_BASE_URL', 'https://api.assemblyai.com/v2').rstrip('/')
    headers = {'authorization': key}
    upload = requester.post(f'{api}/upload', headers={**headers, 'content-type': 'application/octet-stream'},
                            data=wav_bytes(audio), timeout=30)
    upload.raise_for_status()
    url = upload.json().get('upload_url')
    if not url:
        raise RuntimeError('AssemblyAI upload did not return an upload URL.')
    task = requester.post(f'{api}/transcript', headers=headers,
                          json={'audio_url': url, 'speech_models': ['universal-2'],
                                'language_code': 'en', 'disfluencies': True,
                                'filter_profanity': False}, timeout=30)
    task.raise_for_status()
    job_id = task.json().get('id')
    if not job_id:
        raise RuntimeError('AssemblyAI did not return a transcript ID.')
    # Poll boundedly; prevent a hosting worker from hanging indefinitely.
    last = None
    for _ in range(max(1, int(timeout_s / 3))):
        result = requester.get(f'{api}/transcript/{job_id}', headers=headers, timeout=20)
        result.raise_for_status()
        last = result.json()
        if last.get('status') == 'completed':
            return TranscriptResult(last.get('text') or '', clean_words(last.get('words'), 0.001),
                                    'AssemblyAI', 'Filler-word retention requested. Verify ASR omissions manually.')
        if last.get('status') == 'error':
            raise RuntimeError(f"AssemblyAI job failed: {str(last.get('error') or 'unknown error')[:180]}")
        sleep(3)
    raise RuntimeError('AssemblyAI transcription timed out. Try again or use local/manual mode.')


def transcribe_deepgram(audio: np.ndarray, *, requester=None) -> TranscriptResult:
    key = os.getenv('DEEPGRAM_API_KEY')
    if not key:
        raise RuntimeError('DEEPGRAM_API_KEY not set on the server.')
    if requester is None:
        import requests
        requester = requests
    url = 'https://api.deepgram.com/v1/listen'
    params = {'model': 'nova-3', 'language': 'en', 'filler_words': 'true',
              'punctuate': 'true', 'smart_format': 'true'}
    response = requester.post(url, params=params,
                              headers={'Authorization': f'Token {key}', 'Content-Type': 'audio/wav'},
                              data=wav_bytes(audio), timeout=100)
    response.raise_for_status()
    data = response.json()
    channels = data.get('results', {}).get('channels') or []
    alternatives = channels[0].get('alternatives') if channels else []
    if not alternatives:
        raise RuntimeError('Deepgram returned no transcript alternative.')
    alt = alternatives[0]
    return TranscriptResult(alt.get('transcript') or '', clean_words(alt.get('words') or []),
                            'Deepgram', 'Filler-word retention requested. Verify ASR omissions manually.')


def transcribe_openai(audio: np.ndarray, *, client=None) -> TranscriptResult:
    if not os.getenv('OPENAI_API_KEY'):
        raise RuntimeError('OPENAI_API_KEY not set on the server.')
    if client is None:
        from openai import OpenAI
        client = OpenAI(timeout=100)
    f = io.BytesIO(wav_bytes(audio))
    f.name = 'speech.wav'
    result = client.audio.transcriptions.create(file=f, model='whisper-1',
                                                response_format='verbose_json',
                                                timestamp_granularities=['word'], language='en')
    raw = getattr(result, 'words', None) or []
    words = []
    for row in raw:
        if isinstance(row, dict):
            words.append(row)
        else:
            words.append({'word': getattr(row, 'word', ''), 'start': getattr(row, 'start', None),
                          'end': getattr(row, 'end', None)})
    return TranscriptResult(getattr(result, 'text', '') or '', clean_words(words), 'OpenAI Whisper',
                            'Word timestamps requested. Whisper can omit filler words.')


def transcribe(audio: np.ndarray, provider: str, manual_text: str = '', *, remote_consent: bool = False) -> TranscriptResult:
    if provider == 'Manual transcript':
        return TranscriptResult((manual_text or '').strip(), [], 'Manual transcript',
                                'No word timestamps; fillers appear only if manually included.')
    if provider in REMOTE_PROVIDERS and not remote_consent:
        raise ValueError('Confirm permission to send voice data to the selected provider, or choose a local mode.')
    if provider == 'Local faster-whisper':
        text, aligned = recognize(audio)
        return TranscriptResult(text, aligned or [], provider, 'Local inference; fillers may be omitted.')
    if provider == 'AssemblyAI':
        return transcribe_assemblyai(audio)
    if provider == 'Deepgram':
        return transcribe_deepgram(audio)
    if provider == 'OpenAI Whisper':
        return transcribe_openai(audio)
    raise ValueError(f'Unknown transcript provider: {provider}')
