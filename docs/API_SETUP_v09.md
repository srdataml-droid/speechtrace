# SpeechTrace v0.9 — Zero-paid-API setup

The deployed model pipeline uses open-weight models: **Whisper Large V3 Turbo** for speech recognition and **Qwen 3.8 27B** for grounded language coaching. The models run through Groq's hosted **Free Plan**. This avoids a paid transcription or coaching subscription, but Groq is a proprietary inference service, its free limits apply, and only the models have publicly available weights.

## Connect
1. Create a Groq Free Plan account: https://console.groq.com/keys
2. Create a key and add **GROQ_API_KEY** under Vercel project **speechtrace-mobile-lab** → Settings → Environment Variables → Production.
3. Add **SPEECHTRACE_ACCESS_CODE** with a private password for approved testers. The server refuses to spend quota without this gate.
4. Optionally set **GROQ_ASR_MODEL=whisper-large-v3-turbo** and **GROQ_COACH_MODEL=qwen/qwen3.8-27b**.
5. Redeploy to production and reload https://speechtrace-mobile-lab.vercel.app/.
6. Enter your tester code on the site; record, replay, tick the separate voice/coach consents, and analyze.

Never place API keys in frontend JavaScript, GitHub, messages, screenshots or browser localStorage. The optional access code is not an API key.

## Pipeline
Browser audio (Web Audio API metrics) and uploaded recording → Vercel serverless endpoint → Groq Whisper → timed transcription → evidence fusion → Groq Qwen JSON coaching → original/Version 1/Version 2 and replayable moments.

If the free API is rate-limited or unreachable, the recorded voice and local amplitude/pause evidence remain available. Corrected text is not submitted without a separate coaching consent.

## Limits and honest claims
- Groq Free Plan may return HTTP 429. Check your account's quota at https://console.groq.com/docs/rate-limits.
- Groq is a hosted proprietary API even though Whisper and Qwen are openly released models. Qwen 3.8 27B model weights use Apache 2.0.
- Whisper word timing may be imperfect and filler words may be dropped. There is no guaranteed emotion or enthusiasm detector.
- Voice input is sent to Groq only with user permission; text/features only with the separate coach permission. Provider retention policies apply.
- No fine-tuning or real-user accuracy and latency benchmarks have yet been demonstrated; the provided tests use mocks.
- Existing original Python Track C recording comparison is preserved in the repository.

For fully self-hosted operation, run faster-whisper and an open model through Ollama with a separate always-on backend. CPU-only laptops can be slow and an offline machine cannot serve mobile users globally.