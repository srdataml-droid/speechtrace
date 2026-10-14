# Deploy SpeechTrace Gradio on Render

## Intended deployment

Deploy the **Gradio UI only**, not the unauthenticated FastAPI development service or the local STDIO MCP server. Use a dedicated GitHub repository containing the files at this project's root.

## Manual Render route

1. Push this folder to a new dedicated GitHub repository such as `speechtrace-coach` (not a subdirectory; `app.py` and `requirements-coach.txt` must be at the repository root).
2. Open https://dashboard.render.com/web/new
3. Connect your GitHub repository and select that repository.
4. Select **Python**, **free** tier if eligible, and a region close to testers.
5. Use build command: `pip install -r requirements-coach.txt`.
6. Use start command: `GRADIO_SERVER_NAME=0.0.0.0 GRADIO_SERVER_PORT=$PORT GRADIO_SHARE=0 python app.py`.
7. Add `PYTHON_VERSION=3.11.11` environment variable if Render uses another version.
8. Deploy. Wait for the service to show **Live**; open its provided `https://...onrender.com` address on mobile. If it fails, examine build logs, memory and startup logs.

Alternatively, Render's `render.yaml` Blueprint deploy can import these settings from the repository.

## Important limitations

- With **no ASR provider API key**, choose **Manual transcript** and type the actual words you said; the app still processes your original audio waveform for pauses and energy. Auto filler detection needs accurate words. On mobile this is not the full hands-free workflow yet.
- Never place API keys inside this repository or send them to public testers. Configure one speech provider's key as a **secret environment variable** in Render. The UI asks for explicit audio-consent before calling that remote provider.
- The optional OpenAI text coach is disabled until a server-side `OPENAI_API_KEY` is configured and a visitor grants separate text-transfer consent.
- A free instance can sleep during inactivity and take time to wake; insufficient memory may prevent startup or long audio analysis. Upgrade only after checking pricing and whether there are free-tier resources.
- Uploaded speech and decks are sensitive. Avoid confidential presentations. Gradio has short-lived upload caching, but public hosting still means files pass through Render.
- The sample WAV files are synthetic test fixtures, not validated speaker-quality data. The comparison and coaching reports are experimental.
- This hosting setup intentionally **does not publicly expose** the `/v1/...` FastAPI endpoints or the local MCP server. Public APIs would require robust identity and abuse controls first.

## Basic authentication (optional)

Set both `SPEECHTRACE_USER` and `SPEECHTRACE_PASSWORD` in Render's environment settings. Share the credentials out of band with invited testers only. Remember: a basic password is not a substitute for user identity or secure personal-data handling.

## Running locally

`pip install -r requirements-coach.txt && python app.py`

## Phone testing

1. Open the Render URL in Chrome on your phone.
2. Grant microphone permission if prompted.
3. Record a 15-30 second speech or upload an audio file.
4. Leave the default **Manual transcript** option until an ASR provider is configured. Type what was actually said (include um/uh).
5. Press Analyze and inspect detected pauses, energy plot and suggestions.
6. Use synthetic sample in the default input to test without a microphone first.
