"""Tests that do not download model weights or send audio externally."""
from unittest.mock import patch
from fastapi.testclient import TestClient
from transcription_service import app

client=TestClient(app)

def test_health():
    r=client.get('/health')
    assert r.status_code==200 and r.json()['ok']

def test_unsupported_format():
    r=client.post('/v1/transcribe',files={'audio':('speech.exe',b'hello','application/octet-stream')})
    assert r.status_code==415

def test_empty_recording():
    r=client.post('/v1/transcribe',files={'audio':('speech.webm',b'','audio/webm')})
    assert r.status_code==422

def test_mocked_audio_transcription():
    dummy={'transcript':'I said um today we talk about students.','words':[{'text':'I','start':0.0,'end':0.2,'confidence':0.85}],
           'duration_seconds':4.1,'model':'faster-whisper-tiny.en','warning':'Review transcription'}
    with patch('transcription_service.infer',return_value=dummy):
        r=client.post('/v1/transcribe',files={'audio':('speech.webm',b'binary demo','audio/webm')})
    assert r.status_code==200
    assert r.json()['transcript']==dummy['transcript']
    assert r.json()['words'][0]['text']=='I'

def test_cors_preflight():
    r=client.options('/v1/transcribe',headers={'Origin':'https://speechtrace-mobile-lab.vercel.app','Access-Control-Request-Method':'POST','Access-Control-Request-Headers':'content-type'})
    assert r.status_code==200
    assert r.headers['access-control-allow-origin']=='https://speechtrace-mobile-lab.vercel.app'