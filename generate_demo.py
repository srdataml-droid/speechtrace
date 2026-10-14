"""Generate ORIGINAL, synthetic practice examples (not human public speeches).
Requires eSpeak installed: Fedora `sudo dnf install espeak` or Debian `sudo apt install espeak`.
"""
from __future__ import annotations
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

import librosa
import numpy as np
import soundfile as sf
from src.analysis import SAMPLE_RATE, load_audio

ROOT=Path(__file__).resolve().parent
TRANSCRIPT=("Our ideas become stronger when we test them carefully. "
            "Evidence matters more than confidence, and practice makes every presentation clearer.")

def main():
    if shutil.which('espeak') is None:
        raise SystemExit('eSpeak is required only to regenerate demonstration audio. Install espeak first.')
    with tempfile.TemporaryDirectory() as d:
        raw=Path(d)/'speech.wav'
        subprocess.run(['espeak','-v','en','-s','150','-w',str(raw),TRANSCRIPT],check=True,capture_output=True)
        ref=load_audio(str(raw))
    # Trim small silent padding deterministically while preserving inside gaps.
    nonzero=np.flatnonzero(np.abs(ref)>0.004)
    if len(nonzero)==0: raise RuntimeError('Synthesizer produced no speech')
    ref=ref[max(0,int(nonzero[0]-0.1*SAMPLE_RATE)):min(len(ref),int(nonzero[-1]+0.1*SAMPLE_RATE))]
    reference=ROOT/'data'/'reference'; flawed=ROOT/'data'/'flawed'
    reference.mkdir(parents=True,exist_ok=True);flawed.mkdir(parents=True,exist_ok=True)
    sf.write(reference/'ideal.wav',ref,SAMPLE_RATE,subtype='PCM_16')

    # Insert precisely known silence after a close-to-zero boundary at ~48%.
    target=int(len(ref)*0.48)
    window=int(SAMPLE_RATE*0.25)
    local=np.abs(ref[max(0,target-window):min(len(ref),target+window)])
    idx=max(0,target-window)+int(np.argmin(local))
    inserted=np.zeros(int(SAMPLE_RATE*2.4),dtype=np.float32)
    paused=np.concatenate([ref[:idx],inserted,ref[idx:]])
    sf.write(flawed/'extra_pause.wav',paused,SAMPLE_RATE,subtype='PCM_16')

    rushed=librosa.effects.time_stretch(ref,rate=1.34)
    sf.write(flawed/'rushed.wav',rushed,SAMPLE_RATE,subtype='PCM_16')
    quiet=ref*0.25
    sf.write(flawed/'quiet.wav',quiet,SAMPLE_RATE,subtype='PCM_16')
    labels={
        'version':'0.1.0',
        'source_type':'eSpeak text-to-speech synthetic demonstration; no humans, no public speaker references',
        'transcript':TRANSCRIPT,
        'sample_rate':SAMPLE_RATE,
        'reference':'data/reference/ideal.wav',
        'examples':[
            {'id':'extra_pause','path':'data/flawed/extra_pause.wav',
             'method':'Insert 2.4 s zero-amplitude audio at a near-zero crossing',
             'events':[{'type':'extra_pause','start':round(idx/SAMPLE_RATE,3),
                        'end':round(idx/SAMPLE_RATE+2.4,3)}]},
            {'id':'rushed','path':'data/flawed/rushed.wav',
             'method':'Time-stretch at 1.34x (preserve approximate pitch)',
             'events':[{'type':'duration_difference','start':0,'end':round(len(rushed)/SAMPLE_RATE,3)}]},
            {'id':'quiet','path':'data/flawed/quiet.wav',
             'method':'Scale amplitude by 0.25 (-12.04 dB)',
             'events':[{'type':'energy_difference','start':0,'end':round(len(quiet)/SAMPLE_RATE,3)}]},
        ],
        'caveat':'This dataset does not meet Track C public-speaking reference/audio quality or speaker-agnostic validation requirements. It demonstrates synthetic controlled deviations only.'
    }
    (ROOT/'data'/'labels.json').write_text(json.dumps(labels,indent=2)+'\n')
    (ROOT/'data'/'transcript.txt').write_text(TRANSCRIPT+'\n')
    print(f'Generated {round(len(ref)/SAMPLE_RATE,2)}s reference; insertion at {idx/SAMPLE_RATE:.3f}s; 3 flawed examples.')

if __name__=='__main__': main()
