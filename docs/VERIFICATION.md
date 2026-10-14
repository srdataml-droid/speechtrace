# Verification record: SpeechTrace v0.4

Date: October 14, 2026.

## Observed local evidence

- 27 Python tests passed with `python -m pytest -q` (includes both old Track C and new coach/API tests).
- Gradio process launched locally and served its front page with HTTP 200.
- Uvicorn/FastAPI launched locally and served `/v1/health` with HTTP 200.
- Live HTTP upload of provided synthetic WAV returned HTTP 200 with an evidence report and one manually transcribed potential filler.
- API report GET and events GET returned HTTP 200; deletion returned 200, and post-deletion GET returned HTTP 404.
- The Gradio callback with consent to retain a report could retrieve the corresponding report through the local MCP helper method.

## Not established

- Speech analysis quality on consented real speakers across microphones and accents.
- External provider results on real audio, reliability or costs (API keys not configured).
- The MCP SDK protocol handshake with Claude or ChatGPT (optional `mcp` SDK not installed in test environment).
- Remote authenticated MCP publishing, native access to assistant audio, public API security hardening.
- Public hosting, a verified repository push, or an actual video submission.
- Compliance with every Track C judging requirement; the included older Track C PDF is historical and refers to an earlier UI.

## Transparency

The synthetic sample fixtures are not a representative public-speaking benchmark. Tests confirm the software behaves as specified in controlled cases, not that it can judge emotion, factual correctness, rhetorical quality or persuasion.
