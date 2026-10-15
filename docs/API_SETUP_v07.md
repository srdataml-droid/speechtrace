# Superseded setup instructions

Use [API_SETUP_v09.md](API_SETUP_v09.md) for the current **Groq Free Plan + open-weight Whisper/Llama** configuration. The Deepgram/OpenAI instructions below apply to an earlier prototype and are no longer required.

---

# SpeechTrace v0.7 — Connect two AI APIs (phone only)

## Goal
Production-direction MVP: a fast speech-recognition model and separate structured text-coaching model, with original audio retained locally for acoustic analysis. No custom model training is needed to test the concept.

## Required keys

1. **Deepgram** (`DEEPGRAM_API_KEY`): sign in at https://console.deepgram.com/, create a project key authorized for speech-to-text. We use `nova-3`, `filler_words=true`, `utterances=true`, word timestamps and punctuation. You pay Deepgram for usage; check your account pricing/limits.
2. **OpenAI** (`OPENAI_API_KEY`): create a secret API key from https://platform.openai.com/api-keys. This enables the `gpt-4.1-mini` coaching model, which is asked to output evidence-grounded structured feedback. API billing is separate from ChatGPT subscriptions.

In your Vercel dashboard open `speechtrace-mobile-lab` → Settings → Environment Variables. Add both keys to Production. Redeploy the latest source after saving them. **Never put either key in `index.html`, `app.js`, GitHub, Figma, or messages to testers.**

### Optional but recommended
Set `SPEECHTRACE_ACCESS_CODE` to a private testing passcode and share it only with approved testers. The web app has a tester-code field. It does not replace full production authentication and rate limiting. `SPEECHTRACE_COACH_MODEL=gpt-4.1-mini` can select a different compatible structured-output model.

## Mobile workflow
1. Open `https://speechtrace-mobile-lab.vercel.app/` in Chrome.
2. Pick speaking goal; tap Record and grant microphone permission; speak up to five minutes.
3. Tap Finish, replay the recording and check that the audio is audible.
4. Tick separate consent checkboxes for voice transcription and optional text-model coaching.
5. Tap Analyze. The page displays animated progress indicators during audio processing, recognition, alignment and coaching.
6. Review word-level clickable timestamps, potential filler words, low-energy pauses and fast stretches, plus Version 1 (light cleanup) and Version 2 (optional stronger pitch). Download the JSON report if desired.

## Privacy and limitations
Audio goes directly from the browser to the Vercel serverless transcription handler, which forwards it to Deepgram. The handler does not intentionally retain audio. The browser keeps audio in memory until refresh; provider policies apply. Only the transcript and measured audio features are sent to OpenAI when a second checkbox is selected. No pitch deck is sent in this release. Artificial-intelligence advice is not an objective psychological or emotional assessment. ASR can omit ums or mishear accents. Audio energy is relative to the recording system and cannot reliably prove enthusiasm.

## Troubleshooting
- `/api/status`: check whether `fast_asr_configured`, `ai_coach_configured`, and `access_code_required` are true/false (does not expose keys).
- If a key is missing, the page explicitly explains this instead of silently falling back to slow Whisper.
- A network or 429 error is surfaced with a retry option. The original recording remains playable.
- If the speech provider is slow, time how long it takes for each step; optimize measured bottlenecks, not assumptions.
- Vercel request payloads are capped to roughly 3.8 MB by this service. Audio should be compressed to roughly 48 kbps. Long sessions will eventually require direct-to-object-storage uploads and async jobs.

## Launch readiness blockers
- Keys must be configured by the project owner. API integration tests have been run with mock provider responses but not actual paid API calls.
- Validate provider output and cost on multiple real phones, accents and background-noise conditions.
- Add rate limiting, authenticated accounts and deletion policies before a large public launch.