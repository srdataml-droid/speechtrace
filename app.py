"""SpeechTrace Coach v0.3. Start with python app.py. The old Track C app is legacy_comparison.py.

Default mode uses local deterministic measurements and (if installed) offline ASR.
An external LLM is called only when the user checks explicit consent.
"""
from __future__ import annotations
import json
import os
import tempfile
from pathlib import Path

import gradio as gr
import plotly.graph_objects as go
import numpy as np
import pandas as pd

from src.providers import PROVIDERS
from service.pipeline import analyze_rehearsal, compact_report
from service.store import ReportStore
from legacy_comparison import compare as compare_reference_pair, EVENT_COLUMNS as COMPARE_COLUMNS

ROOT=Path(__file__).resolve().parent
DEMO_AUDIO=ROOT/'data/reference/ideal.wav'
EXAMPLE_TRANSCRIPT=(ROOT/'data/transcript.txt').read_text(encoding='utf8').strip()
EVENT_COLUMNS=['From (s)','To (s)','Evidence','Interpretation']


def plot_recording(acoustics: dict) -> go.Figure:
    fig=go.Figure()
    fig.add_scatter(x=acoustics['timestamps_s'],y=acoustics['rms_dbfs'],
                    mode='lines',name='RMS amplitude (dBFS)',line=dict(color='#2563eb'))
    for event in acoustics['events']:
        if event['type']=='low_energy_interval':
            fig.add_vrect(x0=event['start'],x1=event['end'],fillcolor='#fb7185',
                          opacity=.18,line_width=0)
    fig.update_layout(height=325,margin=dict(l=35,r=15,b=32,t=38),template='plotly_white',
                      title='Voice amplitude over time (not an emotion chart)',
                      xaxis_title='Seconds',yaxis_title='Level, dBFS')
    return fig


def rows_from_report(report: dict) -> pd.DataFrame:
    items=[]
    for e in report['acoustics']['events']:
        items.append([e['start'],e['end'],e['type'].replace('_',' '),e['reason']])
    for x in report['language']['fillers']:
        items.append([x['start'],x['end'],f"Potential filler: {x['token']}",x['review']])
    for x in report['language']['bursts']:
        items.append([x['start'],x['end'],f"Fast local rate: ~{x['estimated_wpm']} WPM",x['review']])
    items.sort(key=lambda row: float(row[0]) if row[0] is not None else float('inf'))
    return pd.DataFrame(items,columns=EVENT_COLUMNS)


def coach_rehearsal(audio_path: str | None, deck_path: str | None,
                    goal: str, mode: str, typed_transcript: str,
                    consent: bool, remote_audio_consent: bool = False, persist_report: bool = False) -> tuple:
    if not audio_path:
        raise gr.Error('Record or upload your rehearsal first.')
    try:
        report=analyze_rehearsal(audio_path,
            deck_path=deck_path, goal=goal,
            transcript_provider=mode, manual_transcript=typed_transcript,
            remote_audio_consent=remote_audio_consent,
            external_text_review_consent=consent)
    except (ValueError, RuntimeError, ImportError, OSError) as exc:
        raise gr.Error(str(exc)) from exc
    except Exception as exc:
        raise gr.Error('Analysis failed; try a shorter, clearer recording or manual transcript.') from exc
    transcript=report['transcript']
    review=report['external_llm_review']
    slides=report['deck']['slides']
    report_id = ReportStore().save(compact_report(report)) if persist_report else None
    report['stored_report_id'] = report_id
    duration=report['acoustics']['duration_s']; terms=report['language']
    count=terms['filler_count'] if terms['filler_count'] is not None else 'not analyzed'
    wpm=str(terms['wpm_total']) if terms['wpm_total'] is not None else 'not analyzed'
    bullets='\n'.join(f'- {x}' for x in report['suggestions']) or '- No heuristic evidence thresholds were triggered.'
    pitch='\n'.join(f'{i}. {step}' for i,step in enumerate(report['pitch_structure'],1))
    coverage='\n'.join(f"- Slide {x['slide']}: keyword coverage {x['keyword_coverage'] if x['keyword_coverage'] is not None else 'N/A'} — check '{x['title']}'"
                       for x in report['deck']['slides']) or 'No deck provided.'
    summary=(f"### Rehearsal evidence\n\n**Duration:** {duration}s · **Overall transcript rate:** {wpm} WPM · "
             f"**Potential fillers:** {count} · **Low-energy intervals:** {report['acoustics']['pause_count']}\n\n"
             f"{bullets}\n\n**Slide coverage (keyword heuristic, not correctness):**\n{coverage}\n\n"
             f"**Practice structure:**\n{pitch}\n\n"
             "*Important: vocal amplitude is not emotion or confidence. A deliberate pause is not necessarily wrong. "
             "ASR can omit ums/uhs; manual transcripts have no word-level timestamps. "
             "Deck overlap is not fact-checking or semantic alignment.*")
    if report_id:
        summary += (f"\n\n**Assistant report ID (expires automatically):** `{report_id}`. "
                    "Only share this ID with an assistant you trust; it can reveal transcript and speaking notes.")
    with tempfile.NamedTemporaryFile(mode='w',encoding='utf8',suffix='.json',
                                     prefix='speechtrace_coach_',delete=False) as f:
        json.dump(report,f,indent=2)
        outfile=f.name
    # report contains detailed amplitude traces; exclude them from visible JSON preview.
    small={k:v for k,v in report.items() if k not in {'acoustics'}}
    small['acoustics']={k:v for k,v in report['acoustics'].items() if k not in {'rms_dbfs','timestamps_s'}}
    return summary, transcript, plot_recording(report['acoustics']), rows_from_report(report),review,small,outfile


def build_app() -> gr.Blocks:
    with gr.Blocks(title='SpeechTrace · English Pitch Coach', delete_cache=(3600, 3600)) as demo:
        gr.Markdown('# SpeechTrace Coach v0.4\n**Two workflows: coaching a presentation, or comparing two same-text recordings for Track C.**\n\nThe acoustic detector produces measurements, not emotion or a scientifically validated speaking-quality grade.')
        with gr.Tabs():
            with gr.Tab('Presentation Coach'):
                with gr.Accordion('How this coach works / its limitations', open=False):
                    gr.Markdown('1. Record English speech. 2. Optionally upload deck. 3. Select the transcript provider. '
                                '4. Inspect acoustic and transcript evidence. 5. Optionally request a text-model coaching review.\n\n'
                                '**Audio is never sent to an external provider unless you explicitly allow it.** '
                                'Manual transcript and local faster-whisper modes are server-side only. '
                                'Remote speech providers may retain uploaded audio under their own policies. '
                                'No external fact checking, emotion recognition, learned persuasive scoring or validated voice-quality grading is performed.')
                with gr.Row():
                    audio=gr.Audio(label='1. Rehearsal (up to 3 minutes)',sources=['upload','microphone'],
                                   type='filepath',format='wav',value=str(DEMO_AUDIO))
                    with gr.Column():
                        deck=gr.File(label='2. Optional deck (PDF / PPTX / TXT, up to 30 slides)',
                                     file_types=['.pdf','.pptx','.txt'],type='filepath')
                        goal=gr.Textbox(label='Audience and speaking goal',
                            placeholder='Example: 3-minute hackathon pitch for judges; explain problem, solution, evidence and ask.',lines=2)
                        mode=gr.Dropdown(PROVIDERS,value='Manual transcript',label='3. Speech recognition mode',
                            info='For accurate filler timestamps, choose an external provider after granting consent, or local faster-whisper.')
                        remote_consent=gr.Checkbox(label='I allow the chosen speech API to receive and process this audio (needed only for remote provider modes).',value=False)
                transcript=gr.Textbox(label='Transcript of what was actually said (only used in manual mode)',
                                      lines=4,value=EXAMPLE_TRANSCRIPT,
                                      info='Include every um/uh. Manual mode has no word-level timestamps. ASR modes ignore this text.')
                consent=gr.Checkbox(label='Separately allow sending transcript, slide text and selected flags to OpenAI for optional coaching suggestions.',value=False)
                persist=gr.Checkbox(label='Save this report for my local assistant connector for one hour (includes transcript, not raw audio).',value=False)
                analyze=gr.Button('Analyze my speech',variant='primary')
                summary=gr.Markdown('Record or select a rehearsal and click Analyze.')
                with gr.Accordion('What was spoken',open=True):
                    asr_out=gr.Textbox(label='Transcript used in this analysis',lines=4,interactive=False)
                graph=gr.Plot(label='Measured amplitude and highlighted low-energy intervals')
                table=gr.Dataframe(headers=EVENT_COLUMNS,label='Events to review (timing only where measured)',interactive=False,wrap=True)
                ai=gr.Markdown(label='Optional text-review feedback')
                with gr.Accordion('Report and evidence',open=False):
                    json_output=gr.JSON(label='Report preview')
                    download=gr.File(label='Download full analysis JSON',interactive=False)
                analyze.click(coach_rehearsal,
                    inputs=[audio,deck,goal,mode,transcript,consent,remote_consent,persist],
                    outputs=[summary,asr_out,graph,table,ai,json_output,download],concurrency_limit=1)
                gr.Markdown('**Important:** This version flags measurable phenomena, not errors proven to harm a speech. '
                            'Audio energy is microphone-dependent; rapid speech need not be unclear. '
                            'A missing deck keyword does not prove a message is off topic.')
            with gr.Tab('Track C · Two-recording comparison'):
                gr.Markdown('Compare a **reference and rehearsal speaking the same text**; this preserves the original '
                            'Track C acoustic comparison. Difference from a reference does not establish a mistake.')
                with gr.Row():
                    ref_audio=gr.Audio(label='Reference recording (under 40 seconds)',
                        value=str(ROOT/'data/reference/ideal.wav'),sources=['upload','microphone'],type='filepath',format='wav')
                    attempt_audio=gr.Audio(label='Rehearsal (under 40 seconds)',
                        value=str(ROOT/'data/flawed/extra_pause.wav'),sources=['upload','microphone'],type='filepath',format='wav')
                pair_transcript=gr.Textbox(label='Shared words (optional)',value=EXAMPLE_TRANSCRIPT,lines=2)
                gr.Examples(examples=[
                    [str(ROOT/'data/reference/ideal.wav'), str(ROOT/'data/spectrum'/f'{case}.wav'), EXAMPLE_TRANSCRIPT]
                    for case in ('pause_045','pause_085','pause_140','gain_085','gain_060','gain_040')
                ], inputs=[ref_audio,attempt_audio,pair_transcript],
                   label='Controlled stress-spectrum examples (synthetic; same words)')
                pair_button=gr.Button('Compare matched recordings',variant='primary')
                pair_summary=gr.Markdown()
                pair_plot=gr.Plot(label='Reference-relative energy and pitch curves')
                pair_table=gr.Dataframe(headers=COMPARE_COLUMNS,interactive=False,wrap=True)
                with gr.Accordion('Download evidence',open=False):
                    pair_json=gr.JSON(label='Comparison report')
                    pair_download=gr.File(label='Download comparison JSON')
                pair_button.click(compare_reference_pair,
                    inputs=[ref_audio,attempt_audio,pair_transcript],
                    outputs=[pair_summary,pair_plot,pair_table,pair_json,pair_download],concurrency_limit=1)
        gr.Markdown('**Privacy for testers:** Public demos run on a remote server. Audio and documents may be cached '
                    'temporarily by the host. Do not upload confidential pitches; use the optional access password. '
                    'Text-review APIs require separate consent. No personal user accounts or long-term history are provided.')
    return demo


demo=build_app()

if __name__=='__main__':
    share=os.getenv('GRADIO_SHARE','0').lower() in ('1','true','yes')
    host=os.getenv('GRADIO_SERVER_NAME','0.0.0.0' if os.getenv('SPACE_ID') else '127.0.0.1')
    auth=(os.environ['SPEECHTRACE_USER'],os.environ['SPEECHTRACE_PASSWORD']) if os.getenv('SPEECHTRACE_USER') and os.getenv('SPEECHTRACE_PASSWORD') else None
    demo.queue(max_size=8,default_concurrency_limit=1).launch(share=share,auth=auth,
                    server_name=host,server_port=int(os.getenv('GRADIO_SERVER_PORT','7860')),
                    max_file_size='20mb',show_error=False)
