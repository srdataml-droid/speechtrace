# Track C: reproducible reference-relative scoring rubric

The score is **NOT** a judgment of speech quality, confidence, delivery talent, effectiveness, or emotion. It only describes three signal differences relative to the selected same-text reference. A naturally deliberate pause or a different microphone can lower similarity without lowering actual speaking quality.

| Component | Formula before clipping to [0,100] | Weight |
|---|---|---:|
| Pause similarity | 100 − 25 × detected extra-pause seconds − 8 × detected pause count | 45% |
| Relative pace similarity | 100 − 180 × abs(ln(reference-duration/adjusted-attempt-duration)) | 35% |
| Level similarity | 100 − 8 × abs(active-speech level difference in dB) | 20% |

All three scores are independently rounded to 0.1. The composite is the weighted arithmetic mean. Coefficients are chosen manually for a prototype demonstration. The analysis engine derives extra-pause events using low-energy regions aligned by MFCC/DTW, compares adjusted durations and estimates RMS level difference.

**No model is trained and the coefficients are not calibrated to human judging.** The index only allows repeatable within-reference comparisons for the same words and controlled audio setup. The front-end prints the three dimension scores so users can see what affected the result rather than treating a composite number as an unexplained grade.

Run unit tests:

\`\`\`bash
python -m pytest -q tests/test_contrastive_rubric.py
\`\`\`

For controlled audio and temporal-overlap evaluation see [TRACK_C_STRESS_SPECTRUM.md](TRACK_C_STRESS_SPECTRUM.md).

AI-assisted code and documentation drafted with ChatGPT; maintainer review required.
