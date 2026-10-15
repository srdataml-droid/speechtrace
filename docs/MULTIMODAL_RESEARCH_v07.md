# SpeechTrace — Multimodal models, datasets, training and roadmap

> **Updated October 2026:** The original research below is preserved as a research plan, but current infrastructure uses free-tier Groq-hosted open-weight Whisper and Qwen models. For setup see [API_SETUP_v09.md](API_SETUP_v09.md). Tests are mocked unless explicitly stated. No training or validation study has been completed.

## Why this is genuinely multimodal
The original recording retains time-varying acoustic information; the transcript contains linguistic information; timed words bridge these modalities. The coaching model interprets both the measured events and words, not just a transcript. The initial coach is text-only on a structured fusion report and cannot hear vocal tone directly; direct audio-understanding models are future comparison targets.

## Required input/output objects
- Session: `id`, `goal`, `duration_s`, audio file bytes (browser only), optional future slide documents, permissions.
- Speech provider: `transcript`, `words[]:{word,start,end,confidence}`, `utterances[]`, `provider`, `latency_ms`.
- Acoustic pipeline: RMS envelope, pauses `{start,end,length_s}`, local pace windows `{start,end,wpm}`, recording quality warning.
- AI coach: summary, strengths, moment-by-moment suggestions, light cleanup, stronger example pitch, practice steps.
- Evaluation result: human-verified transcript, filler annotations, delivery observations, expert ratings (when consented), API response timing.

## Models/APIs (current, free-tier first)
1. **Whisper Large V3 Turbo** through the Groq Free Plan for English transcription. Choose **Fast** segment timestamps for lower latency or **Detailed** word timestamps for clickable phrase replay; Groq documents extra latency for word timestamps.
2. **Browser acoustic measurements** (RMS loudness relative to this recording and possible quiet intervals) run locally in parallel with transcription. This is **not an emotion-detection model**. High energy cannot prove enthusiasm or confidence.
3. **Qwen 3.8 27B** through the same Groq key for text-and-evidence-grounded coaching and optional Version 1 / Version 2 rewrites. The model receives transcript and measured timing/energy summaries, **not raw audio**.
4. **No OpenAI API or other paid API required.** Groq is a hosted provider of open-weight models with a free tier and quota limits, not a fully self-hosted open-source API.
5. **Future comparison candidates:** locally hosted faster-whisper, open-weight direct-audio language models, VAD, pitch contours using parselmouth/Praat, sentence-level delivery alignment, and document-grounded pitch preparation.

### Current session data and outputs
The session currently exists only in the browser during the rehearsal. A production session ID, database, account system, or long-term user history **has not been built**. The report can be exported as JSON, and raw audio remains on the device while the page is open. Timed words are approximate when requested; manual edits invalidate direct timing alignment. Do not label a heuristic as an emotion observation.

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
P0: Configure one Groq Free Plan key plus a private tester access code; prove a 30–90 second recording end-to-end on a real phone and laptop, measuring real elapsed time and transcription fidelity.
P1: Offer Fast vs Detailed transcription; support transcript correction without re-uploading audio; re-run the coach only on verified text; add consistent retry/error messages and prevent stale timing/feedback. Benchmark 30-sec, 3-min and 5-min recordings.
P2: Add voice-activity detection, measured pitch contour and locally calibrated pause patterns. Validate on actual recordings. Never infer emotional state from energy alone.
P3: Allow optional PDF/PPTX and pitch notes for grounding. Report missing/covered points with source citations to each slide.
P4: Collect consented corpus, tune thresholds, human evaluation, measure relative to common speaker-coaching tools.
P5: Stream partial words, prompt at appropriate moments without interrupting rehearsals; optional spoken coaching responses.
P6: Add a SpeechTrace API and MCP integration for third-party assistants, with authentication, user consent, metering and rate limits; decide on billing only after genuine product validation.

## Do not claim
- 'We fine-tuned a model' if we have not done so.
- 'Recognizes emotion' from raw energy alone.
- 'Transcription is instant' until p50/p95 measured.
- 'World-class accuracy' without annotated evaluation.