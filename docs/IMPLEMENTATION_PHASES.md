# SpeechTrace delivery roadmap

## North star
Help an English public speaker rehearse a short pitch, detect measurable acoustic or language events, link them to evidence and context, and practice a clearer delivery. Distinguish empirical observations from persuasive advice. Keep the same-text reference comparison mode for Multimodal AI Hackathon Track C.

## Build principles

1. Raw audio remains available to acoustic feature extraction; text alone is insufficient.
2. Deterministic observations first; generative coaching second. Never invent timestamps or proof of persuasion.
3. All analysis paths call `service.pipeline.analyze_rehearsal` where possible.
4. Remote audio and text requests require separate consent and configured secrets.
5. No persistent recording uploads; a report persists only after explicit opt-in, with TTL.
6. Compare performance against real-world user labels before training a new model.

## Phase 0: Scope and data contracts — done

Deliverables: product goal, user journey, processing diagram, event schema, known limits and Track C compatibility statement. Gate: every observation identifies an evidence source, and events without timestamps display `null` instead of invented timings.

## Phase 1: Shared engine — implemented, test locally

Deliverables: a reusable pipeline in `service/pipeline.py`, speech normalization, rule-based acoustics, transcription provider abstraction, document parsing. Gate: the Gradio coach and REST API run the same pipeline. Out of scope: end-to-end neural speech judgment.

## Phase 2: Robust audio evidence — partially implemented

Already: RMS energy, low-energy windows, filler words in transcript, approximate WPM, timestamped bursts when word timestamps are available. Improve next: pitch/F0 contour, speech rate per phrase, noise/clip quality checks, trustworthy word-to-sound alignment, manual review UI, accent robustness. Gate: labeled event precision/recall and timestamp errors measured on human recordings. Do not claim clarity or confidence from waveform amplitude.

## Phase 3: Deck and content grounding — baseline implemented

Already: extraction from PDF, PPTX, TXT; keyword overlap warnings. Improve: slide ordering, speaker notes, per-claim evidence, visual slide content, semantic alignment with human verification. Gate: demonstrate distinction between a genuine omission and a synonym/paraphrase. No false factual-verification claims.

## Phase 4: Coaching — baseline implemented, opt-in

Already: deterministic speaking scaffold; optional provider-based language-model review with explicit text-consent. Improve: actionable feedback cards grouped by precise audio span, audience-specific examples, speaking-intention input, annotated rehearsal replay. Gate: a human can identify the evidence and test the proposed correction.

## Phase 5: REST API — implemented locally

Deliverables: `GET /v1/health`, `POST /v1/rehearsals`, `GET /v1/rehearsals/{id}/report`, `GET /v1/rehearsals/{id}/events`, `DELETE /v1/rehearsals/{id}`. Default API reports are ephemeral. Optional retention: SQLite with one-hour TTL. Gate: API contract, upload validation, auth, consent, report deletion tests pass. Before PUBLIC hosting: always HTTPS, bearer auth, rate limits, per-user ownership and upload/compute quotas.

## Phase 6: Assistant integration — local foundation implemented

Deliverables: `python -m service.mcp_server` starts a local STDIO MCP server with `read_report`, `read_events`, `make_practice_plan`. Only explicitly saved reports are retrievable. Gate: an MCP client with access to the same local store retrieves a report. Remote Claude or ChatGPT publication is NOT yet implemented. No native voice interception is claimed.

## Phase 7: Evaluation — NOT complete

Pilot: 20–30 consented English speaker recordings from different accents/devices. Two independent annotators identify fillers and pauses; check timing error, false positives and practical usefulness. Compare with Microsoft Speaker Coach/Yoodli using the same samples. Gate: predefined thresholds met on a held-out set; report limitations and bias gaps. Only afterward consider trainable models.

## Phase 8: Deployment — NOT complete

Gradio on a managed host plus a separately secured API; a hosted SQLite file is for prototyping only. Production: object storage for recordings if consented, Postgres for user-level metadata, signed upload URLs, queue workers, monitoring and audit. Access boundaries and deletion policy required before collecting public recordings.

## Phase 9: Live voice coaching — future experiment

Own WebRTC/LiveKit capture, acoustic window streaming, partial ASR and timestamp alignment, and carefully scheduled coaching responses. MCP does not expose a third-party assistant's raw microphone stream automatically. Gate: tested latency, consent, accuracy and interruption handling.

## Competition note

Track C explicitly expects reference-vs-flawed speech using identical transcripts. Preserve `legacy_comparison.py`; one-recording coaching is a separate, optional mode and does not independently satisfy the challenge.
