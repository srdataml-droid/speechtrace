# SpeechTrace REST API and local MCP connector

## Quick start

```bash
python -m pip install -r requirements-api.txt
uvicorn service.api:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/docs` to explore the automatically generated API contract. The default bind is loopback only.

### Manual transcription: no external AI service used

```bash
curl -s -X POST http://127.0.0.1:8000/v1/rehearsals \
  -F 'audio=@data/reference/ideal.wav' \
  -F 'manual_transcript=Um our idea will help students learn' \
  -F 'goal=Explain a solution to hackathon judges'
```

### Save the report for a compatible assistant

Add `-F 'persist_report=true'` to the request. The response returns a random `rehearsal_id`, which can be passed to the local MCP tools or these endpoints:

- `GET /v1/rehearsals/{rehearsal_id}/report`
- `GET /v1/rehearsals/{rehearsal_id}/events`
- `DELETE /v1/rehearsals/{rehearsal_id}`

The report contains the transcript and measurements, *not the raw recording*. Retained reports expire after `SPEECHTRACE_REPORT_TTL` seconds (default 3600). Users should not send confidential transcripts to a public instance. `persist_report` is false by default.

### Provider choices and consent

- `provider=Manual transcript`: use form field `manual_transcript`; no network call.
- `provider=Local faster-whisper`: install `requirements-asr.txt` and model cache; may download model weights on first run.
- `provider=AssemblyAI` / `Deepgram` / `OpenAI Whisper`: install `requirements-api.txt`, configure one corresponding SERVER secret, and send `remote_audio_consent=true`.
- `external_text_review_consent=true`: sends transcript and deck excerpts to an external language model; requires `OPENAI_API_KEY` and optional LLM dependencies. Otherwise no LLM review occurs.

### Basic auth

```bash
export SPEECHTRACE_API_TOKEN='choose-a-long-random-secret'
# Requests must include:
# Authorization: Bearer choose-a-long-random-secret
```

**Do not expose the development API directly on the open Internet.** Bearer token alone does not implement tenant isolation, quotas or abuse prevention. Put TLS, rate limits, identity-aware authorization and monitoring in front of it before a multi-user service.

### MCP local integration

```bash
python -m pip install -r requirements-mcp.txt
python -m service.mcp_server
```

Configure a trusted STDIO MCP host to run the command in this project directory and set the *same* `SPEECHTRACE_REPORT_DB` path as the API. The connector registers:

- `read_report(rehearsal_id)`
- `read_events(rehearsal_id)`
- `make_practice_plan(rehearsal_id)`

This is a **local MCP foundation only**. It does not intercept Claude/ChatGPT built-in voice audio, and it is not a remotely hosted authenticated MCP service. Do not expose the local STDIO bridge as an unauthenticated network service.
