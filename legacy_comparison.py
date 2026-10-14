"""SpeechTrace: a testable Gradio frontend for same-text acoustic comparisons.

No speech-quality model has been trained. The measurements are descriptive and
must not be presented as universal speaking-quality scores.
"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import gradio as gr
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from src.analysis import analyze_pair, load_audio, evaluate_intervals
from src.rubric import score_relative_delivery

ROOT = Path(__file__).resolve().parent
EXAMPLES_DIR = ROOT / "data"
LABELS = json.loads((EXAMPLES_DIR / "labels.json").read_text(encoding="utf-8"))
TRANSCRIPT = (EXAMPLES_DIR / "transcript.txt").read_text(encoding="utf-8").strip()
EVENT_COLUMNS = ["Flaw type", "From (s)", "To (s)", "Measured difference", "Explanation", "Suggested review"]

CSS = """
.gradio-container { max-width: 1140px !important; margin: auto !important; }
#intro { padding: 12px 0 4px; }
#intro h1 { font-size: 2.2rem; letter-spacing: -.035em; }
#results-caption { font-size: .95rem; }
"""


def _chart(result: dict) -> go.Figure:
    """Two independent feature overlays on each clip's elapsed-time axis."""
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.13,
                        subplot_titles=("RMS energy over time", "Estimated fundamental frequency"))
    ref, test = result["ref"], result["test"]
    for row, key in ((1, "db"), (2, "pitch")):
        for data, name, color in ((ref, "Reference", "#2563eb"), (test, "Rehearsal", "#e49b37")):
            # Masking pitch invalid frames uses NaNs, which Plotly supports.
            values = np.asarray(data[key], dtype=float)
            fig.add_trace(go.Scatter(
                x=np.asarray(data["times"], dtype=float), y=values,
                mode="lines", name=name, line=dict(color=color, width=1.75),
                legendgroup=name, showlegend=(row == 1), connectgaps=False,
            ), row=row, col=1)
    for event in result["events"]:
        if event["type"] == "extra_pause":
            for row in (1, 2):
                fig.add_vrect(x0=event["start"], x1=event["end"],
                              fillcolor="#dc4654", opacity=.15, line_width=0,
                              row=row, col=1)
    fig.update_yaxes(title_text="Level (dBFS)", row=1, col=1)
    fig.update_yaxes(title_text="F0 (Hz)", row=2, col=1)
    fig.update_xaxes(title_text="Time since start of each recording (seconds)", row=2, col=1)
    fig.update_layout(height=565, margin=dict(l=35, r=18, b=52, t=53),
                      legend=dict(orientation="h", y=1.12, x=0),
                      hovermode="x unified", template="plotly_white")
    return fig


def _table(events: list[dict]) -> pd.DataFrame:
    rows = []
    for e in events:
        suffix = "s" if e["type"] == "extra_pause" else "%" if e["type"] == "duration_difference" else "dB"
        rows.append([
            e["type"].replace("_", " ").title(),
            round(float(e["start"]), 2), round(float(e["end"]), 2),
            f"{e['delta']:+}{suffix}", e["explanation"], e["suggestion"],
        ])
    return pd.DataFrame(rows, columns=EVENT_COLUMNS)


def compare(reference_path: str | None, attempt_path: str | None, transcript: str | None):
    """Gradio inference callback; returns summary, Plotly, table, JSON and file."""
    if not reference_path or not attempt_path:
        raise gr.Error("Please provide both a reference and a rehearsal recording.")
    try:
        result = analyze_pair(load_audio(str(reference_path)), load_audio(str(attempt_path)))
    except (ValueError, RuntimeError, OSError) as error:
        raise gr.Error(f"Could not analyze these recordings: {error}") from error
    except Exception as error:
        # Do not expose server paths, stack traces or implementation details to public testers.
        raise gr.Error("Audio analysis failed. Please try another short WAV recording.") from error

    metrics = result["metrics"]
    events = result["events"]
    rubric = score_relative_delivery(result)
    transcript = (transcript or "").strip()
    status = "No differences crossed the prototype thresholds." if not events else f"Detected {len(events)} reference-relative difference(s)."
    summary = (
        "### Comparison finished\n"
        f"**{status}**\n\n"
        f"**Reference:** {metrics['reference_duration_s']} s  ·  "
        f"**Rehearsal:** {metrics['attempt_duration_s']} s  ·  "
        f"**Longer-than-reference pauses:** {metrics['extra_pause_count']}  ·  "
        f"**Active audio-level delta:** {metrics['relative_energy_db']:+.1f} dB\n\n"
        f"**Experimental similarity index:** {result['deviation_index']}/100 "
        "(hand-chosen penalty scale, **not** speech quality or confidence).\n\n"
        + (f"\n\n**Reference-relative rubric (0–100):** Pause {rubric['scores']['pause']}, "
           f"Pace {rubric['scores']['relative_pace']}, "
           f"Recording level {rubric['scores']['recording_level']}. "
           f"**Weighted similarity: {rubric['combined_reference_similarity']}/100.** "
           "Higher means closer to this one reference, **not** better public speaking.\n\n")
        + ("*Transcript supplied for documentation only; no word-level forced alignment is performed.*"
           if transcript else "*No transcript supplied. Compare recordings of the same words for meaningful results.*")
    )
    report = {
        "project": "SpeechTrace Gradio prototype",
        "transcript": transcript or None,
        "index_not_a_quality_score": result["deviation_index"],
        "metrics": metrics,
        "events": events,
        "reference_relative_rubric": rubric,
        "method": "RMS and YIN pitch features, MFCC dynamic time warping, deterministic comparison thresholds",
        "limitations": [
            "Not a trained speech-quality model or assessment of persuasion",
            "No word-level forced transcript/audio alignment",
            "Events are differences from one reference, not proven delivery flaws",
            "Audio level can change with the microphone or recording gain",
            "No verified multi-speaker or accent generalization",
        ],
    }
    # Every request gets its own path, avoiding concurrent download collisions.
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", suffix=".json",
                                     prefix="speechtrace_", delete=False) as handle:
        json.dump(report, handle, indent=2)
        output_path = handle.name
    return summary, _chart(result), _table(events), report, output_path


def build_app() -> gr.Blocks:
    with gr.Blocks(title="SpeechTrace · Speech Rehearsal Evidence",
                   delete_cache=(3600, 3600)) as demo:
        gr.Markdown(
            "# SpeechTrace\n"
            "**Evidence-based speech rehearsal · Track C research prototype**\n\n"
            "Compare two recordings of **the same words**. See measurable changes in "
            "pause timing, overall duration and audio level. Not an automated speaking coach "
            "or validated quality judge.", elem_id="intro"
        )
        with gr.Accordion("How to test in 60 seconds", open=True):
            gr.Markdown(
                "1. Try a sample below (Extra pause, Faster delivery or Lower recording level).\n"
                "2. Select **Analyze both recordings**.\n"
                "3. Inspect highlighted intervals and the evidence table.\n"
                "4. For your own test, upload/record two short recordings of the **same text**. "
                "Keep each under 40 seconds. The reference is not necessarily an ideal speaker.\n\n"
                "**Privacy:** On a public deployment, uploaded voice files are processed on the host "
                "and may be temporarily cached. Upload only recordings you're willing to share with that host."
            )
        with gr.Row():
            reference = gr.Audio(
                label="1. Reference performance",
                value=str(EXAMPLES_DIR / "reference" / "ideal.wav"),
                sources=["upload", "microphone"], type="filepath", format="wav", scale=1,
            )
            attempt = gr.Audio(
                label="2. Your rehearsal",
                value=str(EXAMPLES_DIR / "flawed" / "extra_pause.wav"),
                sources=["upload", "microphone"], type="filepath", format="wav", scale=1,
            )
        transcript = gr.Textbox(
            label="Transcript (optional; the same words in both recordings)",
            value=TRANSCRIPT, lines=2,
            info="Used for display/reporting only; the prototype does not align transcript words.",
        )
        gr.Examples(
            examples=[
                [str(EXAMPLES_DIR / "reference" / "ideal.wav"), str(EXAMPLES_DIR / "flawed" / "extra_pause.wav"), TRANSCRIPT],
                [str(EXAMPLES_DIR / "reference" / "ideal.wav"), str(EXAMPLES_DIR / "flawed" / "rushed.wav"), TRANSCRIPT],
                [str(EXAMPLES_DIR / "reference" / "ideal.wav"), str(EXAMPLES_DIR / "flawed" / "quiet.wav"), TRANSCRIPT],
                *[[str(EXAMPLES_DIR / "reference" / "ideal.wav"), str(EXAMPLES_DIR / "spectrum" / f"{name}.wav"), TRANSCRIPT] for name in ("pause_045","pause_085","pause_140","gain_085","gain_060","gain_040")],
            ],
            example_labels=["Inserted long pause", "Faster delivery", "Lower audio level",
                            "Subtle pause (+0.45s)", "Medium pause (+0.85s)", "Strong pause (+1.40s)",
                            "Subtle level change", "Medium level change", "Strong level change"],
            inputs=[reference, attempt, transcript],
            label="Controlled demo recordings (synthetic eSpeak voice, not a human speech)",
        )
        analyze_button = gr.Button("Analyze both recordings", variant="primary", size="lg")
        gr.Markdown("## Analysis results", elem_id="results-caption")
        summary = gr.Markdown("Choose an example and select **Analyze both recordings**.")
        plot = gr.Plot(label="Frame-level audio evidence and detected extra-pause intervals")
        table = gr.Dataframe(label="Detected changes and suggested reviews", headers=EVENT_COLUMNS,
                             interactive=False, wrap=True)
        with gr.Accordion("Raw evidence and downloadable report", open=False):
            details = gr.JSON(label="Machine-readable report")
            download = gr.File(label="Download this analysis (.json)", interactive=False)
        gr.Markdown(
            "*Red shaded intervals show detected additional low-energy pauses on the rehearsal clock. "
            "The two curves use each recording's own elapsed-time axis; they are not word-aligned. "
            "Pitch is estimated, not used to judge competence. The index is only a demonstration heuristic.*"
        )
        analyze_button.click(fn=compare, inputs=[reference, attempt, transcript],
                             outputs=[summary, plot, table, details, download],
                             concurrency_limit=1)
        gr.Markdown(
            "---\n"
            "**For testers:** Describe the two clips, which difference you expected, what the app flagged, "
            "and whether the timestamps were correct. Avoid using personal/private recordings. "
            "Code, dataset labels and limitations are documented in the project README."
        )
    return demo


demo = build_app()


if __name__ == "__main__":
    # To expose a temporary public Gradio link, run GRADIO_SHARE=1 python app.py.
    # Keep the host running; the relay is NOT permanent deployment.
    share = os.getenv("GRADIO_SHARE", "0").strip().lower() in {"1", "true", "yes"}
    host = os.getenv("GRADIO_SERVER_NAME", "0.0.0.0" if os.getenv("SPACE_ID") else "127.0.0.1")
    port = int(os.getenv("GRADIO_SERVER_PORT", "7860"))
    user, password = os.getenv("SPEECHTRACE_USER"), os.getenv("SPEECHTRACE_PASSWORD")
    auth = (user, password) if user and password else None
    demo.queue(max_size=8, default_concurrency_limit=1).launch(
        share=share, auth=auth, server_name=host, server_port=port,
        max_file_size="15mb", show_error=False,
        theme=gr.themes.Soft(), css=CSS,
    )
