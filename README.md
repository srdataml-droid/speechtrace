# SpeechTrace v0.4 — audio-native English public-speaking coach

SpeechTrace helps someone practice a short speech with evidence-based feedback on relative energy, pauses, speaking rate, fillers, and alignment to provided presentation materials. The original Track C **same-text comparison** is preserved as a second Gradio tab.

> **Status:** engineering prototype; tested with synthetic examples. No trained end-to-end speaking-quality classifier and no validated emotion, persuasive impact, fact checking or accent scoring. Inferences and suggestions must be checked by humans.

## Architecture

![Runtime flow](docs/architecture/runtime.png)

![Build phases](docs/architecture/phases.png)

- [Phase-by-phase engineering roadmap](docs/IMPLEMENTATION_PHASES.md)
- [REST API and local MCP instructions](docs/API_AND_MCP.md)
- [Complete technology stack](docs/TECH_STACK.md)
- [Editable Mermaid source: runtime](docs/architecture/RUNTIME_FLOW.mmd)
- [Editable Mermaid source: build phases](docs/architecture/BUILD_PHASES.mmd)

### Shared layers

`service/pipeline.py` = one analysis entry point for the Gradio UI, FastAPI and assistant integration. It retains raw audio for acoustic analysis during processing, uses a consent-selected transcription provider, merges evidence and optionally asks an LLM for text coaching.

- **Signal:** RMS, low-energy intervals, intra-recording intensity changes.
- **Language:** optional word-timed transcription, filled-pause counts and local rate bursts.
- **Context:** PPTX/PDF/TXT extraction, conservative lexical overlap warnings.
- **Coach:** practice structure plus consent-gated external text review.
- **Access:** Gradio UI, FastAPI endpoints, local MCP reports (only if explicitly saved).

## 1. Run the Gradio coach

```bash
python -m pip install -r requirements-coach.txt
python app.py
```

Open the local URL printed in the terminal. You can record/upload, attach a deck, choose a transcript provider and inspect evidence. For temporary external Gradio sharing from your own machine:

```bash
GRADIO_SHARE=1 python app.py
```

The generated public link requires your computer to remain online. Use `SPEECHTRACE_USER` and `SPEECHTRACE_PASSWORD` to protect a tester demo, and do not ask testers to upload confidential pitches.

## 2. Run the local REST API

```bash
python -m pip install -r requirements-api.txt
uvicorn service.api:app --host 127.0.0.1 --port 8000
```

Swagger: http://127.0.0.1:8000/docs. Example analysis:

```bash
curl -X POST http://127.0.0.1:8000/v1/rehearsals \
  -F 'audio=@data/reference/ideal.wav' \
  -F 'provider=Manual transcript' \
  -F 'manual_transcript=Um this is my public speaking pitch'
```

Default response contains the report without saving it. `persist_report=true` is explicit consent to retain the *report*, including transcript, for up to one hour by default; audio files are removed after analysis. **Do not make the unauthenticated development API publicly reachable.** See API documentation for security requirements.

## 3. Optional assistant integration (local MCP)

```bash
python -m pip install -r requirements-mcp.txt
python -m service.mcp_server
```

This local STDIO bridge retrieves consented reports by ID; it does not capture Claude/ChatGPT microphone streams. Configure the same `SPEECHTRACE_REPORT_DB` between the API and MCP server. External MCP deployment, per-user identity and OAuth are later work.

## 4. Speech recognition and LLM options

Manual transcription is the working default, with no API key required.

- Local faster-whisper: `pip install -r requirements-asr.txt` (model weights downloaded or cached separately).
- AssemblyAI / Deepgram / OpenAI Whisper: install `requirements-api.txt`, configure one provider key on the server, then select it and explicitly allow remote audio transfer.
- OpenAI text review: configure `OPENAI_API_KEY` and separately give permission for transcript/slide text to be sent to the language model. This does not perform factual research.

Do not commit credentials. See `.env.example`.

## 5. Track C competition mode

`python legacy_comparison.py` runs the original two-recording same-text acoustic comparison app. The Gradio app also contains a Track C tab. This is a baseline only; official challenge requirements for rights-cleared real speech, forced alignment and sufficient evaluation have not all been met. The single-recording coach does **not** replace the Track C requirement.

## 6. Test

```bash
python -m pip install -r requirements-api.txt
python -m pytest -q
```

The offline suite tests the shared pipeline, Gradio configuration and callbacks, API request validation, authorization, opt-in report lifecycle, local MCP functions, and Track C comparison. The included fixtures are synthetic and do not establish real-world accuracy.

## Privacy and limitations

- Microphone gain and noise affect energy. Energy is **not** emotion, confidence or impact.
- Word timestamps may be approximate; a manual transcript does **not** provide timestamps.
- Slide keyword overlap is **not** proof of omissions, semantic mismatch, or factual errors.
- A pause may be intentional and rhetorically effective.
- Gradio demos may cache uploads on their host; inspect the hosting policy before sharing.
- The REST API is local by default and has not yet received production security hardening, hosted OAuth or cross-user isolation.

The legacy `docs/technical_report.pdf` describes an earlier Track C build and has not yet been updated to reflect Gradio/API v0.4. Use `docs/IMPLEMENTATION_PHASES.md` and `docs/VERIFICATION.md` for current status.

This software was drafted with AI assistance and must be verified by the maintainer before a hackathon submission. See `RESEARCH_DECISIONS.md`, `SUBMISSION_CHECKLIST.md` and `docs/DATASET_CARD.md` for provenance and more limitations.
