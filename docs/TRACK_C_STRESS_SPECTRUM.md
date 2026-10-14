# Track C: reproducible stress-spectrum demonstration

This directory contains **nine same-transcript comparisons** against one synthetic English reference. Six are new graded perturbations, three are preserved from the original demo. They are controlled tests of instrumentation, **not** gold-standard labels for how well a human speaks.

## Run

```bash
python -m pip install -r requirements-coach.txt
python scripts/generate_stress_spectrum.py
python scripts/evaluate_stress_spectrum.py
python legacy_comparison.py
```

In the Gradio app, upload `data/reference/ideal.wav` as the reference and any `data/spectrum/*.wav` as the rehearsal recording. Use the unchanged transcript in `manifest.json`.

Try `pause_045.wav` vs `pause_140.wav` to see how temporal detection changes near and above the implementation threshold. Try `gain_085.wav` vs `gain_040.wav` to see how the level-change threshold changes behavior. The preexisting `data/flawed/rushed.wav` provides an overall-speed comparison.

## Evaluation protocol

Every altered clip has exactly the same **spoken lexical content** as the reference. Inserted silence is marked precisely on the **altered clip's** timeline. Gain changes are explicitly labeled as whole-recording changes, not made-up word-level spans. The manifest records severity as perturbation strength only.

The evaluator calls `src.analysis.analyze_pair`, records which injected category triggered the detector, and computes interval temporal overlap for inserted pauses. False negatives for slight perturbations are expected and informative. Do **not** describe these as measured human speaking scores.

## Scope and limitations

- One eSpeak synthetic voice; no rights-cleared real public-speaking baseline, accent generalization or trained model.
- MFCC dynamic time warping is **acoustic** sequence alignment, not transcript forced alignment.
- Inferred pause regions do not establish that a deliberate dramatic pause is poor speaking.
- Amplitude/gain changes may come from a microphone rather than the speaker.
- Current prototype heuristics are not a validated rubric-based human performance score.
- This spectrum is a transparent stress-test addition, not a claim that every Track C requirement is met.

## AI disclosure

Code and documentation in this extension were drafted with ChatGPT assistance and should be reviewed by the project maintainer before final submission.
