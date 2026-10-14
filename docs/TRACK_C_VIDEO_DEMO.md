# SpeechTrace: 4-minute Track C submission video

This is a recording checklist and suggested narrative. Please speak naturally.
Video must be 3–10 minutes, on YouTube (Unlisted or Public).

## 0:00–0:30 — The problem

"Speech practice feedback is often vague. SpeechTrace explores a reproducible way to compare the same words delivered differently, identify acoustic changes and show where they happened."

Show project title and GitHub repository.

## 0:30–1:05 — Mobile studio

Open the mobile-first app. Record a short sentence with an intentional hesitation. Review playback, editable transcript and tentative filler highlights. Mention explicitly: "The mobile recording studio is a companion feature. The Track C scoring demonstration is separate."

## 1:05–1:45 — Dataset

Open data/spectrum/manifest.json on GitHub. "We constructed nine controlled same-text comparison cases: four with inserted silence, four with different recording levels, and one with faster delivery. Six graded variants are new; the original three are retained. These clips use one synthetic eSpeak voice, not human-speaking excellence labels."

Display filenames and the start/end annotation for pause_140.wav.

## 1:45–2:45 — Side-by-side audio analytics

Open Gradio Track C comparison tab (python app.py or legacy_comparison.py). Choose reference ideal.wav and pause_045.wav; run comparison. Then switch to pause_140.wav and run it. Show output graphs, timestamped event table and raw JSON. Note cases below a threshold may be missed, and that the thresholds are part of a transparent prototype.

## 2:45–3:25 — Scoring and reasoning

Show the three reference-relative rubric components: pause, relative pace, recording level. Explain that the formula is fixed and repeatable, and that the total is not a validated public-speaking grade. The analyzer uses RMS energy and MFCC dynamic time warping, with an estimated F0 plot.

## 3:25–4:00 — Evidence and limits

Show scripts/evaluate_stress_spectrum.py and docs/TRACK_C_RUBRIC.md. Explain how detection and IoU may be audited. Conclude: "This is a working engineering prototype using controlled synthetic data. Real-speaker validation and transcript forced alignment remain future work." 

End on the GitHub repository, technical report and deployed demo URL.
