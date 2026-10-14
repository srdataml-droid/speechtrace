# SpeechTrace — Multimodal models, datasets, training and roadmap

## Why this is genuinely multimodal
The original recording retains time-varying acoustic information; the transcript contains linguistic information; timed words bridge these modalities. The coaching model interprets both the measured events and words, not just a transcript. The initial coach is text-only on a structured fusion report and cannot hear vocal tone directly; direct audio-understanding models are future comparison targets.

## Required input/output objects
- Session: `id`, `goal`, `duration_s`, audio file bytes (browser only), optional future slide documents, permissions.
- Speech provider: `transcript`, `words[]:{word,start,end,confidence}`, `utterances[]`, `provider`, `latency_ms`.
- Acoustic pipeline: RMS envelope, pauses `{start,end,length_s}`, local pace windows `{start,end,wpm}`, recording quality warning.
- AI coach: summary, strengths, moment-by-moment suggestions, light cleanup, stronger example pitch, practice steps.
- Evaluation result: human-verified transcript, filler annotations, delivery observations, expert ratings (when consented), API response timing.

## Models/APIs (current)
1. Nova-3 for ASR and word timestamps; no local checkpoint download required.
2. Device signal analysis for energy and low-volume pauses; these are observations, not an AI emotion model.
3. `gpt-4.1-mini` for grounded coaching using the OpenAI Responses API and JSON Schema outputs.
4. Optional comparison candidate: OpenAI GPT-4o Mini Transcribe for word-error-rate/latency benchmarking.
5. Future: stream ASR, pitch contours using parselmouth/Praat, VAD, sentence-level delivery alignment, direct audio-language model for richer acoustic interpretation, document-grounded pitch preparation.

## Data sources to investigate, not automatically combine into training
- **SpeechCraft**: expressive English/Chinese speech labels including pitch, energy, speed and emphasis, with distinct underlying corpora and licenses. Helpful for acoustic-description research; not a validated public-speaking-quality score. https://github.com/thuhcsi/SpeechCraft
- **Mozilla Common Voice**: English speech and spontaneous speech releases; good for ASR diversity tests, not rhetorical-coaching grades. Check exact release, locale and CC0 terms. https://commonvoice.mozilla.org/en/datasets
- **TED-LIUM 3**: TED-talk speech and transcripts (talk-style speech); speech-to-text benchmarking; check exact licenses and annotations before use. https://www.openslr.org/51/
- **FluencyBank**: fluency/disfluency research, mixed open and access-restricted data; much is clinical research and is NOT a ready-made filler-word or public-speaking-rubric training set. https://talkbank.org/fluency/access/index.html
- **User-consented SpeechTrace corpus**: best future task-specific data. Collect speaker-permitted pitches, exact transcript, explicitly marked um/uh, pause intervals, manually judged clarity/structure, and context on audience and speaker intent. Avoid collecting sensitive recordings without consent.

## Own-data annotation format
JSONL, one recording per row: `speaker_pseudonym`, `accent_self_described_optional`, `microphone`, `consent_scope`, `duration_s`, `gold_transcript`, `gold_fillers:[{token,start_s,end_s}]`, `gold_pauses:[{start_s,end_s,intentional: true|false|null}]`, `content_goal`, `expert_notes`, `source_dataset`, `license`, `train_val_test_split`.
Do not use speaker identity features to grade or infer intelligence or confidence. Split by SPEAKER not random clip; keep Nigerian/other English accents included in evaluation.

## Training / tuning decision gates
**Phase A, now:** baseline with API ASR, prompt engineering, ground-truth comparisons and complete UX. No fine-tuning. Optimize upload size, reduce network hop, parallel acoustic analysis, limit unnecessary requests, and time individual stages.
**Phase B:** collect 20–50 genuine recordings with explicit consent, two annotators on a subset; measure word error rate, filler precision/recall, missed spontaneous hesitations, timing tolerance, coaching relevance and transcription p50/p95 latency.
**Phase C:** with at least hundreds of lawful domain-specific examples and a proven recurrent deficiency, explore custom domain vocabulary, prompt/rubric tuning, specialized audio model fine-tuning OR small supervised classifier. Fine-tuning might improve task accuracy but doesn't guarantee lower inference latency.
**Phase D:** streaming API, word-alignment confidence, consented slide-grounded presentation analysis, repeat rehearsal comparison, assistant API/MCP tools, production observability.

## Evaluation rubric
- Performance: app time-to-interactive, processing median/p95 time, ASR upload + model time, coaching time, response failures per 100 sessions.
- ASR: English word error rate, noun/keyterm accuracy, filler-word precision/recall including false positives, timestamps compared to hand annotations.
- Delivery: precision/recall of long quiet intervals and locally rushed regions; avoid interpreting microphone gain as emotion.
- Coaching: judged specificity, accurate alignment to provided evidence, does not invent facts, preserves intended meaning in Version 1/2, user preference versus generic advice.
- Privacy: consent split by provider, no leaked secrets, clear retention and deletion documentation, API abuse safeguards.

## Prioritized roadmap
P0: Get two API keys connected, prove on a real Android recording, monitor API response and cost.
P1: Improve transcript correction + recalc word evidence, voice waveform replay markers, recording limit + errors; exact filler recall testing.
P2: Add measured pitch variation and overlong-pause classifier; calibrate individual baseline and noisy environment.
P3: Allow optional PDF/PPTX and pitch notes for grounding. Report missing/covered points with source citations to each slide.
P4: Collect consented corpus, tune thresholds, human evaluation, measure relative to common speaker-coaching tools.
P5: Stream partial words, prompt at appropriate moments without interrupting rehearsals; optional spoken coaching responses.
P6: Add SpeechTrace API and MCP to third-party assistants; authenticate, meter and bill usage.

## Do not claim
- 'We fine-tuned a model' if we have not done so.
- 'Recognizes emotion' from raw energy alone.
- 'Transcription is instant' until p50/p95 measured.
- 'World-class accuracy' without annotated evaluation.