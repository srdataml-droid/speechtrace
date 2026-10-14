import json
from pathlib import Path
import numpy as np
import pytest
from scipy.io import wavfile
from src.analysis import (
    SAMPLE_RATE,load_audio,frame_features,silence_intervals,
    analyze_pair,temporal_iou,evaluate_intervals
)
ROOT=Path(__file__).resolve().parents[1]


def _tone_with_gap(gap=1.0):
    sr=SAMPLE_RATE
    t=np.arange(sr,dtype=float)/sr
    wave=(0.2*np.sin(2*np.pi*185*t)).astype(np.float32)
    return np.concatenate([wave,np.zeros(int(gap*sr),np.float32),wave])


def test_timestamps_and_silence():
    a=_tone_with_gap(1.3)
    x=frame_features(a)
    pauses=silence_intervals(x)
    assert len(pauses)==1
    assert abs(pauses[0]['start']-1.0)<.09
    assert abs(pauses[0]['end']-2.3)<.09


def test_resampling_stereo(tmp_path):
    sr=8000
    t=np.arange(sr)/sr
    a=(.1*np.sin(2*np.pi*200*t)).astype(np.float32)
    p=tmp_path/'voice.wav'
    wavfile.write(p,sr,np.stack([a,a],axis=1))
    b=load_audio(str(p))
    assert len(b)==SAMPLE_RATE
    assert b.ndim==1


def test_dataset_generated():
    assert (ROOT/'data/reference/ideal.wav').is_file()
    assert (ROOT/'data/flawed/extra_pause.wav').is_file()
    labels=json.loads((ROOT/'data/labels.json').read_text())
    assert labels['source_type'].startswith('eSpeak')


def test_real_demo_detects_extra_pause():
    r=load_audio(str(ROOT/'data/reference/ideal.wav'))
    p=load_audio(str(ROOT/'data/flawed/extra_pause.wav'))
    found=analyze_pair(r,p)
    truth=json.loads((ROOT/'data/labels.json').read_text())['examples'][0]['events']
    ev=evaluate_intervals(found['events'],truth)
    assert ev['tp']>=1,found['events']
    assert ev['precision']>=0.5,found['events']
    assert ev['mean_iou']>=0.35,found['events']


def test_rushed_demo_has_duration_difference():
    r=load_audio(str(ROOT/'data/reference/ideal.wav'))
    p=load_audio(str(ROOT/'data/flawed/rushed.wav'))
    found=analyze_pair(r,p)
    assert any(e['type']=='duration_difference' for e in found['events']),found['events']


def test_energy_difference():
    r=load_audio(str(ROOT/'data/reference/ideal.wav'))
    p=load_audio(str(ROOT/'data/flawed/quiet.wav'))
    found=analyze_pair(r,p)
    assert any(e['type']=='energy_difference' for e in found['events']),found['events']


def test_iou_and_matching():
    assert temporal_iou((2,4),(3,5))==pytest.approx(1/3)
    p=[{'type':'extra_pause','start':2,'end':4}]
    t=[{'type':'extra_pause','start':2.1,'end':4.1}]
    r=evaluate_intervals(p,t)
    assert r['tp']==1 and r['fp']==0 and r['fn']==0
