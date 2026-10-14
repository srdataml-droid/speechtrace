# SpeechTrace — 3–4 minute demonstration outline

**Important:** A video has not been recorded or uploaded. This is a ready-to-use narration and shot list.

**0:00–0:30 — The problem.** 'Two speakers can say the same words but use different pacing, pauses and vocal energy. Generic judgments like “improve your delivery” are hard to reproduce. Our prototype reports measurable deviations and where they happen.' Show the two audio input panels.

**0:30–1:00 — Provenance.** Show `data/transcript.txt`, `data/labels.json`, and `generate_demo.py`. 'For a controlled experiment, I synthesized one reference speech and deliberately introduced a 2.4-second pause. I also created a faster version and a lower-amplitude version. These are synthetic practice examples, not licensed real speeches.'

**1:00–1:45 — Engineering.** Show feature graphs. 'We decode the audio at 16 kHz, compute 20-millisecond-hop acoustic features, summarize the spectral envelope using MFCCs, estimate pitch and RMS, then use dynamic time warping to acoustically compare recordings of the same passage.'

**1:45–2:30 — Flaw evidence.** Select `extra_pause`. Show timestamp highlighted, explanation and report JSON. 'We locate low-energy intervals and compare their length to the acoustically aligned reference region. This is a measurable difference, not proof that a pause is rhetorically wrong.' Then switch to `rushed` and `quiet`.

**2:30–3:00 — Evaluation.** Show `python -m pytest -q`, `python run_evaluation.py`, and evaluation JSON. 'Twelve automated tests passed. On a single controlled injected pause, mean temporal IoU was 0.97. This is a tiny internal engineering check, not a population-level metric.'

**3:00–3:40 — Limits and next steps.** 'This prototype doesn't use transcript forced alignment, real human reference speeches, human-scored delivery, or multi-speaker tests. The next phase is licensed public speeches, real same-text mirrors, timestamped labels, speaker-held-out evaluation, and human-scored rubrics.' Show the relevant README section.

**3:40–4:00 — Closing.** 'SpeechTrace turns some of the otherwise vague parts of speech rehearsal into transparent, testable audio measurements. Future work is about determining which acoustic differences are genuinely useful for speakers.'

**Publishing checklist:** Record your own screen; show actual successful runs; add voice narration; upload to YouTube as unlisted/public per organizer rules; include the URL on Devpost and in README. Do not claim any subjective quality model has been trained.
