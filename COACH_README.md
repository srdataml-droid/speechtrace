# SpeechTrace Coach v0.2: goal, evidence, limitations

## The target
Help an **English-speaking person rehearse a public presentation**. Given one 1–3 minute rehearsal, optional PDF/PPTX slides and the audience/goal, return observed filler tokens, speaking rate, low-energy pauses, voice amplitude over time, slide keyword coverage, suggested practice structure, plus an optional LLM-written review with quotations from the actual words spoken.

This changes the product goal. The **original Track C reference-versus-rehearsal comparison** is still usable via `python legacy_comparison.py` and original tests. The Coach is a **separate product experiment**, not a guarantee of eligibility for a track that requires paired recordings.

## Start

```bash
python -m pip install -r requirements-coach.txt
python app.py
```

**How to try in 60 seconds:** The Coach app loads a short **synthetic** eSpeak sample and the sample transcript. Click Analyze. Then record your own voice and replace the sample transcript with the actual words spoken. Upload a PPTX or text-extractable PDF to inspect a crude content/slide overlap report.

**Real speech-to-text** is optional because model weights are not bundled and network download/CPU inference may be slow:

```bash
python -m pip install -r requirements-asr.txt
python app.py
```

Switch to **Automatic** transcription. This lazy-loads faster-whisper `base.en` on CPU by default (environment `SPEECHTRACE_ASR_MODEL`, `SPEECHTRACE_DEVICE`). Whisper-type ASR can normalize away fillers, so **word-level filler counts may be too low** and timestamps are approximate. If you're validating fillers, audit manual transcriptions including um and uh. Auto transcript uses word timestamp estimates; manual transcript **never fabricates word timestamps**.

**Optional grounded language model review:** `pip install -r requirements-llm.txt`, provide `OPENAI_API_KEY` on the host, then explicitly check consent. The upload's **transcript + slide text** (not the audio file) goes to an external OpenAI model. The model does **not** browse for facts or conduct independent research, and its rewrites are recommendations rather than proof of correctness. Set `SPEECHTRACE_COACH_MODEL` to an available model on your provider account. Never embed API keys in a shared ZIP or source control.

## Key engineering limitations

- A louder waveform is **not** proof of confidence, emotion, passion or effectiveness.
- Rushed local word-rate windows only work with automatic word timestamps, and can be inaccurate when ASR words are missed.
- Current microphone gain, compression and ambient noise distort vocal-energy indicators; interpret changes **within a recording**, not across speakers.
- The app does not yet measure vocal pitch range. It measures **amplitude dynamics**, not complete prosody.
- Extracted slide text ignores screenshots, figures and other non-extractable content. Low overlap is not an objective error or evidence the speaker skipped a point.
- Built-in coaching structure is a guideline, not a learned speech-quality model. AI-assisted rewrite requires separately enabled, external model access.
- The 3-minute recording limit is a demo resource safeguard.

## Validation ladder

1. Human annotate 20–30 short, consented English pitch recordings: manual filler words with timestamps, known silent regions, transcription quality, and whether feedback was useful. Include Nigerian English accents and different microphone conditions.
2. Check exact filler **precision / recall** and timestamp tolerance ±0.5s; calculate median absolute rate error and silence false positives/negatives. Segment metrics by accent, mic and speaking style.
3. Blind-test whether real people prefer and improve from the feedback over generic advice. Avoid asserting confidence and persuasion without human labels and careful evaluation.
4. A second-stage supervised model is justified **only if** it beats the transparent baseline on held-out speakers; obtain permission/licenses for any third-party audio. Do not treat TED talk popularity or applause as automatically correct speaking labels.

## Research links (independent sources)

- Microsoft Speaker Coach existing feature set: https://support.microsoft.com/en-us/powerpoint/rehearse-your-slide-show-with-speaker-coach
- Yoodli commercial speech coaching: https://yoodli.ai/use-cases/speech-coaches
- faster-whisper ASR & approximate word timestamps: https://github.com/SYSTRAN/faster-whisper
- WhisperX forced alignment: https://github.com/m-bain/whisperX
- openSMILE eGeMAPS prosody features: https://audeering.github.io/opensmile-python/
- Switchboard/NXT disfluency annotations: https://catalog.ldc.upenn.edu/LDC2009T26
- POM public trait labels (movie reviews, not pitch scoring): https://github.com/eusip/POM
- 3MT_French time-sliced speaking ratings (French, restricted): https://zenodo.org/records/7603511

## Share

```bash
GRADIO_SHARE=1 python app.py
```

Public links expose an accessible server with uploaded voices and text, so configure auth and privacy controls before sharing with people who may disclose confidential presentations. `GRADIO_SHARE=1` makes a temporary URL only while the process remains running. There is no live URL in this package.

## Test

```bash
python -m pytest -q
```

Synthetic fixtures validate signal analysis only. They do not measure coaching accuracy on real speakers.
