# SpeechTrace — Evidence-First Public Speaking Rehearsal
**Multimodal AI Hackathon 2026 | Track C | Prototype brief, October 14, 2026**

## Problem
Students, founders and speakers rehearse pitches but receive vague advice such as “speak more confidently.” Many people also practise with general AI chat systems, which primarily interpret transcribed words and can miss acoustic context such as silence, intensity variation, and pacing. Existing specialist products (including PowerPoint Speaker Coach and Yoodli) already provide filler and pace feedback. We do not claim this feature category is new.

## User and goal
Our initial user is an English-speaking student or founder preparing a 1–3 minute hackathon pitch. They want to record a rehearsal and get evidence they can act on before the next attempt: likely fillers, unusual silent intervals, duration and approximate pace, plus help structuring their intended message.

## Solution
SpeechTrace preserves two distinct streams: (1) the original voice recording for acoustic measurements, and (2) an editable transcription for language analysis. The interface connects them in a review workflow and shows two optional drafting approaches: a minimal cleanup and a structural alternative. Both versions require human judgment; the current mobile rewrite is deterministic, not generative AI.

## How it works
1. Speaker selects goal and target duration.
2. Speaker records directly from a mobile browser (HTTPS microphone permission).
3. Where supported, browser speech recognition attempts an automatic English transcript; speaker verifies/edits it. If unavailable, they type a transcript.
4. Audio is decoded locally in the browser, sampled into RMS energy frames, and inspected for relative low-energy intervals longer than 450 ms. It does not infer emotions.
5. Simple conservative transcript matching highlights possible fillers (`um`, `uh`, `erm`, `you know`, `sort of`, `kind of`, etc.). Counts are approximate and not word-aligned.
6. A review dashboard displays measurements, replayable silence events, an original transcript and two drafting examples.
7. Speaker rehearses again and compares personally; multi-attempt storage and robust evaluation are future work.

## Technical architecture
- Mobile user interface: HTML, CSS, JavaScript, MediaRecorder, Web Audio API and browser SpeechRecognition where available; deployed on Vercel.
- Core Python coach: Gradio, Librosa, NumPy, SciPy, Plotly, FastAPI; deployed separately on Render. Allows optional PDF/PPTX extraction and opt-in external speech/LLM providers when configured.
- GitHub source: https://github.com/srdataml-droid/speechtrace
- Design source: https://www.figma.com/design/v0ecRK2NpIJzD8yZX1Dmkv
- Instant mobile UI: https://speechtrace-mobile-lab.vercel.app/
- Gradio proof of concept: https://speechtrace-coach.onrender.com/

## Important design constraints
The Vercel mobile release uses speech recognition offered by the browser vendor, which may be network-backed and may omit fillers or yield different results on Android devices. No speech-recognition API key has been configured for the full server deployment. It is not correct to claim reliable automatic filler recognition, accurate word timestamp alignment, context-aware critique, sentiment/emotion inference, or AI-generated rewrites in the released mobile MVP.

The current Track C reference-matched comparator lives in `legacy_comparison.py`; the newer free-form speaker coach is a related but different workflow. If same-script contrastive audio is mandatory in the organizer's Track C statement, demonstrate the original comparator and label the newer coach as an extension. It is not a validated contrastively trained model.

## Prototype evaluation
Existing Python tests exercise core deterministic features, API paths and interface behavior; a 27-test suite passed locally for the previous v0.4 branch. The mobile v0.5 JavaScript passed `node --check` but was not verified in a physical Android device or in a live speech-recording session. There is no human speaker benchmark, accent fairness study, validated scoring rubric, or measured coaching improvement yet.

## Differentiation hypothesis
Unlike conventional transcript-only writing feedback, SpeechTrace keeps acoustic events available for replay and invites a speaker to decide whether a flagged moment deserves correction. This combination is a product hypothesis, not demonstrated novelty or superiority over Yoodli or PowerPoint Speaker Coach.

## Next phases
1. Integrate an opt-in speech provider that explicitly preserves disfluencies, with word-level timestamps and confidence; validate Nigerian English recordings.
2. Join transcript words to audio evidence and enable clickable local review and editable manual corrections.
3. Add pitch-deck alignment, audience-aware LLM review, meaning-preserving rewrite choices, and privacy-safe retention/deletion.
4. Test 20–30 consented speaker recordings and report precision/recall for fillers, pause boundary errors and usefulness ratings.
5. Build a trained classifier only if that annotated baseline shows a repeatable gap that warrants learning.

## Demo sequence
Record a 30-second English pitch; show the transcript (edit if necessary); select a highlighted possible filler; play a detected low-energy gap; inspect the duration/pace metrics and both drafting suggestions; explain why no acoustic signal alone proves emotion or confidence. Then demonstrate the separate same-script Track C comparator if the track requires it.

## Credits and disclosures
Original app and engineering assisted by OpenAI ChatGPT. Synthetic eSpeak samples are engineering fixtures, not proof of effectiveness. External hosting, speech, and design tools are disclosed in the relevant project documentation. Do not claim automatic AI speech coaching where provider integration is absent.