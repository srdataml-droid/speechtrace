# SpeechTrace — Acoustic Evidence for Speech Rehearsal

> **Track C / Multimodal AI Hackathon 2026 — research prototype.**
> This is an *acoustic comparison tool*, not a validated public-speaking judge, a speech-recognition engine, or a trained model.

SpeechTrace compares **two short recordings of the same passage** and reports reproducible, timestamped deviations in low-energy pause length, total duration (a coarse pacing proxy), and median active RMS level. It plots RMS energy and estimated fundamental frequency, using MFCC dynamic time warping (DTW) to relate corresponding regions of the recordings.

## One-minute overview

1. Supply a reference WAV recording and a rehearsal of the **same text** (or pick a generated demonstration pair).
2. The app decodes mono audio and resamples to 16 kHz.
3. It extracts frame-level RMS, 13 MFCCs, and estimated F0 (via YIN).
4. It aligns the two MFCC sequences with DTW and checks for unusually long low-energy intervals.
5. The results display timestamp ranges, underlying measurements, suggestions, an energy/pitch graph, and downloadable JSON.

The generated demo is **eSpeak synthetic speech**, not a real public speaker. It was created to show a measurable end-to-end processing pipeline and to enable deterministic unit tests, **not to claim compliance with the full benchmark dataset requirements**.

## Install and launch

Requires Python 3.11–3.13, an internet connection to install Python packages, and enough memory for a 40-second comparison. A GPU is not required.

```bash
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv/Scripts/activate
python -m pip install -r requirements.txt
python legacy_comparison.py
```

**Dataset is already included**, so eSpeak is *not* required to run the demo. Only if regenerating it:

```bash
# Fedora: sudo dnf install espeak
# Ubuntu: sudo apt install espeak
python generate_demo.py
```

To reproduce checks:

```bash
python -m pytest -q
python run_evaluation.py
```

**Gradio:** Select one of the three synthetic sample pairs or upload/record your own two performances in your browser. Recording inputs are converted to WAV when Gradio handles them. Click **Analyze both recordings** to view results and download JSON. The 40-second maximum applies to each decoded recording. On a public app, the host processes voice recordings and Gradio may cache uploads; do not share sensitive recordings.

### Get a public tester link now

Keep the app running on a connected computer and, on Linux/Fedora/macOS, run:

```bash
GRADIO_SHARE=1 python legacy_comparison.py
```

On Windows PowerShell:

```powershell
$env:GRADIO_SHARE = "1"
python legacy_comparison.py
```

Copy the `https://...gradio.live` URL printed in the terminal and send it to your testers. It is **temporary**, requires your computer to stay on and connected, and is publicly accessible to anyone with the URL. For a protected pilot, set `SPEECHTRACE_USER` and `SPEECHTRACE_PASSWORD` in the environment before launching. For a hosted persistent URL, follow **SHARE_WITH_TESTERS.md** for deployment choices and limitations. We have **not** created a live public link from this project package.

## Algorithm and mathematical rationale

- **Sampling**: Resample mono audio to 16,000 samples/second, frame size 640 samples (40 ms), hop 320 samples (20 ms).
- **RMS**: `sqrt(mean(frame ** 2))` measures amplitude. A possible low-energy interval comprises contiguous frames below `max(0.007, 0.09 * RMS_95th_percentile)` for at least 0.35 s. The first and last 0.12 seconds are excluded from internal pause events.
- **MFCC**: 13 coefficients summarize the spectral envelope; we standardize features with reference means and scales.
- **DTW**: Dynamic time warping on normalized MFCCs finds a monotonic *acoustic* correspondence between the recordings. This is **not transcript forced alignment**. It can fail when recordings have different words, noise or recording conditions.
- **Extra pause**: For a detected rehearsal silence, we look up the mapped interval of reference time. Report an extra pause when its duration exceeds the aligned span by >=0.7 s. Measurements are not professional judgments.
- **Duration difference**: Compare the reference duration with the attempt duration after subtracting flagged pause extensions. This is a *global timing proxy*, **not words per minute**.
- **Loudness difference**: Compare median active-speech RMS in dB: `20 * log10(test_rms / reference_rms)`. Recording gain and microphone distance can dominate this signal.
- **Pitch**: YIN estimates fundamental frequency; the plot is exploratory. No accent, confidence, charisma, or vocal-quality classification is performed.
- **Index**: `100 - 22*(extra pauses) - 15*(duration flag) - 7*(level flag)`, capped at zero. It is an explicitly heuristic *reference-deviation index*, **not a calibrated speech quality score**.

## Reproduced controlled test results

This run was tested on a single generated voice and script, with an inserted 2.4 s silence, a 1.34x time-stretched sample, and a 0.25x-amplitude sample.

| Example | Intended change | Observed event |
|---|---|---|
| extra_pause.wav | 2.4 s inserted silence | extra_pause |
| rushed.wav | 1.34x time stretch | duration_difference |
| quiet.wav | amplitude x0.25 | energy_difference |

For this **one positive pause example**, the automated test matched the injected interval at temporal IoU 0.97. Positive-case precision/recall were both 1.0, but the dataset is tiny, synthetic, and not representative. The value must not be quoted as field performance. See `data/evaluation_results.json` and `tests/test_core.py`.

## Dataset provenance

- `data/reference/ideal.wav`: eSpeak-generated original narration of the original text in `data/transcript.txt`.
- `data/flawed/extra_pause.wav`: the same waveform with precisely 2.4 seconds of digitally inserted zero samples.
- `data/flawed/rushed.wav`: time-stretched from that waveform using Librosa.
- `data/flawed/quiet.wav`: same waveform scaled by a factor of 0.25.
- `data/labels.json`: transformations, ground-truth injected intervals, and caveats.
- `generate_demo.py`: regenerate the examples from scratch; generated audio can differ by eSpeak version, so evaluate against regenerated labels.

This synthetic dataset cannot establish speaker-agnostic fairness, natural delivery, public-speaking competency or training generalization.

## Known gaps versus the official Track C challenge

| Official requirement | Current status |
|---|---|
| Custom contrastive good/flawed recordings | **Partial:** reproducible synthetic pairs, no real public-speaking baseline |
| Public speeches and accurate same-transcript recordings | **Not met:** requires rights-cleared real speeches and varied human mirrors |
| Temporal ground-truth labels | **Partial:** exact injected pause; coarse full-clip labels for other transformations |
| Forced word-level transcript/audio alignment | **Not met:** MFCC acoustic DTW is not forced alignment |
| FFT/MFCC/F0/pause and delivery analysis | **Partial:** MFCC, RMS, YIN F0, silence; FFT underlies MFCC |
| Exact causal flaw intervals | **Partial:** extra pauses timestamped; duration and level at clip scale |
| Speaker-agnostic normalization | **Not established:** no real multi-speaker robustness testing |
| Upload/transcript/dashboard | **Partial:** accepts transcript for documentation, not aligned word by word |
| Reproducible scores and measurable evaluation | **Partial:** deterministic rules plus a tiny controlled test |
| GitHub + <=6 page technical document + 3–10 min YouTube demo | **Partially prepared:** docs and video script provided; publishing/uploading remain separate actions |

## Next scientifically meaningful improvements

1. Obtain **licensed** human reference speeches; transcribe, correct transcripts, and record multiple speakers reading identical text with controlled delivery changes.
2. Add genuine **forced transcript alignment** (e.g. WhisperX or Montreal Forced Aligner) to map each word's beginning and end time; evaluate the alignment on manual annotation.
3. Include multiple speakers, accents, environments and microphones. Partition train/validation/test by speaker and passage.
4. Compare detectors with precision, recall, F1, temporal IoU and calibration. Include negative examples that should **not** be called flaws.
5. Validate scoring rubrics against multiple independent human raters before claiming communication quality.

## Included files

`app.py`: Gradio dashboard; `SHARE_WITH_TESTERS.md`: tester sharing/deployment; `src/analysis.py`: algorithm; `generate_demo.py`: dataset creation; `run_evaluation.py`: reproducibility; `tests/`: unit tests; `docs/technical_report.pdf`: concise report; `docs/demo_script.md`: video guidance.

## AI-assisted development disclosure

The prototype's code, text, documentation, and deterministic test design were generated with assistance from OpenAI's ChatGPT at the developer's request. It should be reviewed, tested on the developer's own machine, improved and explicitly disclosed in the submission according to organizer rules. The generated audio uses the external open-source eSpeak synthesizer. No public speeches, private recordings or copyrighted benchmark data are redistributed here.

## License and attribution

Project-specific Python source and authored documentation can be reused under the MIT license in `LICENSE`; third-party tools are licensed separately and must be respected. Use the source model/data license for any added recording. The eSpeak engine is not bundled in this project.
