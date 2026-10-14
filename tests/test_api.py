"""Public API contract, privacy and report storage tests. Network access not required."""
import io
import wave
from pathlib import Path

import numpy as np
import pytest
from fastapi.testclient import TestClient

from service.api import app
from service.store import ReportStore
from service.mcp_server import read_report, read_events, make_practice_plan

ROOT = Path(__file__).resolve().parents[1]


def test_health():
    client = TestClient(app)
    assert client.get('/v1/health').json()['status'] == 'ok'


def test_api_manual_upload_is_ephemeral_by_default(tmp_path, monkeypatch):
    monkeypatch.setenv('SPEECHTRACE_REPORT_DB', str(tmp_path/'db.sqlite'))
    monkeypatch.delenv('SPEECHTRACE_API_TOKEN', raising=False)
    client = TestClient(app)
    with (ROOT/'data/reference/ideal.wav').open('rb') as f:
        answer = client.post('/v1/rehearsals',
            data={'goal':'Explain an educational app','manual_transcript':'Um our app supports learners',
                  'provider':'Manual transcript'},
            files={'audio':('speech.wav',f,'audio/wav')})
    assert answer.status_code == 200, answer.text
    result = answer.json()
    assert result['rehearsal_id'] is None
    assert result['report']['language']['filler_count'] == 1
    assert result['report']['data_handling']['audio_retained_in_report'] is False
    assert result['report']['events']
    assert 'timestamps_s' not in result['report']['acoustics']


def test_auth_and_consent(tmp_path, monkeypatch):
    monkeypatch.setenv('SPEECHTRACE_API_TOKEN','strong-secret')
    monkeypatch.setenv('SPEECHTRACE_REPORT_DB', str(tmp_path/'db.sqlite'))
    client = TestClient(app)
    with (ROOT/'data/reference/ideal.wav').open('rb') as f:
        response = client.post('/v1/rehearsals',files={'audio':('speech.wav',f,'audio/wav')})
    assert response.status_code == 401
    with (ROOT/'data/reference/ideal.wav').open('rb') as f:
        response = client.post('/v1/rehearsals',
            headers={'Authorization':'Bearer strong-secret'},
            data={'provider':'Deepgram','remote_audio_consent':'false'},
            files={'audio':('speech.wav',f,'audio/wav')})
    assert response.status_code == 422
    assert 'permission' in response.text.lower()


def test_persist_read_delete_and_mcp(tmp_path, monkeypatch):
    monkeypatch.delenv('SPEECHTRACE_API_TOKEN', raising=False)
    monkeypatch.setenv('SPEECHTRACE_REPORT_DB', str(tmp_path/'report.sqlite'))
    client = TestClient(app)
    with (ROOT/'data/reference/ideal.wav').open('rb') as f:
        response = client.post('/v1/rehearsals',
           data={'manual_transcript':'Um I built this','persist_report':'true'},
           files={'audio':('speech.wav', f, 'audio/wav')})
    assert response.status_code == 200, response.text
    report_id = response.json()['rehearsal_id']
    assert report_id and len(report_id) >= 24
    report = client.get(f'/v1/rehearsals/{report_id}/report')
    assert report.status_code == 200
    assert read_report(report_id)['language']['filler_count'] == 1
    assert read_events(report_id)['events']
    assert make_practice_plan(report_id)['structure']
    assert client.delete(f'/v1/rehearsals/{report_id}').json()['deleted']
    assert client.get(f'/v1/rehearsals/{report_id}/report').status_code == 404


def test_rejects_wrong_type_and_oversize(tmp_path):
    client=TestClient(app)
    response=client.post('/v1/rehearsals',files={'audio':('x.mp3',io.BytesIO(b'junk'),'audio/mpeg')})
    assert response.status_code == 415
    response=client.post('/v1/rehearsals',files={'audio':('x.wav',io.BytesIO(b'x'*(20*1024*1024+1)),'audio/wav')})
    assert response.status_code == 413


def test_expired_report(tmp_path):
    store=ReportStore(tmp_path/'reports.db',ttl_seconds=60)
    rid=store.save({'transcript':'Hi'})
    assert store.get(rid)=={'transcript':'Hi'}
    import sqlite3, time
    with sqlite3.connect(store.path) as c:
        c.execute('UPDATE reports SET expires_at=? WHERE id=?',(int(time.time())-1,rid))
    assert store.get(rid) is None
