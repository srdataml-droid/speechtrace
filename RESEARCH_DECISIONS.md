# Research and engineering decision log — 14 October 2026

## Goal

A public speaker preparing a 1–3 minute English hackathon pitch can **rehearse once**, supply a slide deck, review evidence at moments that deserve attention, and receive carefully qualified suggestions for a clearer message. The tool should make a user measurably more prepared, not pretend to measure emotion or professional speaking skill from sound waves.

## Competitive baseline: do not claim novelty from filler detection

- **Microsoft PowerPoint Speaker Coach**: checks pace, pitch, fillers, repeated expressions, reading slides and more. It can already be used while rehearsing slides, so it directly competes with the revised concept. https://support.microsoft.com/en-us/powerpoint/rehearse-your-slide-show-with-speaker-coach
- **Yoodli**: speech rehearsal, transcription and quantitative filler/pacing analytics, plus roleplay features. This is a serious commercial baseline. https://yoodli.ai/use-cases/speech-coaches
- Opportunity hypothesis (NOT validated differentiation): a **pitch-deck-grounded, evidence-linked coaching report** designed for short hackathon pitches. Compare usefulness, specificity, cost and performance against the above tools with real users. A deck-grounded coach is not intrinsically new.

## Component review

| Component | Candidate | Strength | Weakness / decision |
|---|---|---|---|
| Speech-to-text | faster-whisper `base.en`/`small.en` | Practical English offline transcription with approximate word timestamps; CPU int8 mode | Downloads weights; ASR may omit 'um'/'uh', hallucinate in noise, and mishear accented speech. Optional only, test against manual transcription. |
| More accurate alignment | WhisperX | VAD + forced alignment improve word boundary estimation | Alignment cannot recover words that ASR omitted; more setup and memory. Phase two, not a prerequisite today. |
| Amplitude, pauses | frame RMS + relative threshold | Fast, transparent, train-free and timestampable | Microphone gain/noise may cause false positives; pauses may be intentional. Implemented. |
| Pitch variation, other voice features | openSMILE eGeMAPSv02 | Standardized acoustic descriptors including loudness and F0; helpful for richer vocal variation | Features are not validated judgments of confidence or speaking quality. Research candidate; not yet implemented in v0.2. |
| Filler classification | lexicon with ASR + speaker-checked transcript | Interpretable, low-cost baseline | Counts depend on correct transcript; `like`/`you know` may be meaningful language, not necessarily fillers. Implemented conservative lexicon. |
| Message/slide match | lexical token overlap, followed by opt-in LLM review | Useful low-cost coverage hint; LLM can explain and rewrite in context | Lexical match misses paraphrases, charts and images; LLM can invent claims, cannot independently verify truth. Implemented with explicit caveats. |
| Narrative/storytelling suggestions | outline rules / opt-in text model | Helpful rehearsing structure and giving examples | There is no universal objectively correct storytelling moment; speaker goal/audience matter. Suggestions require human judgment. |
| New supervised model / attention network | none for MVP | Could learn validated labels **after** a study | Training now would waste resources and risk teaching biases from tiny or wrong-domain labels. Do not train until data and baseline evaluation exist. |

Sources:
- https://github.com/SYSTRAN/faster-whisper
- https://github.com/m-bain/whisperX
- https://audeering.github.io/opensmile-python/

## Dataset shortlist, correctly qualified

1. **Switchboard / NXT**: English telephone conversations with annotated disfluencies and timing. Good for spotting natural revisions and fillers; mismatched to prepared stage delivery. Access to underlying speech may need licensing. https://catalog.ldc.upenn.edu/LDC2009T26
2. **POM**: English-speaking movie review recordings, persuasion and speaker-trait labels. Better suited to studying perceived traits, NOT hackathon speech quality. Original data distributed via registration / license. https://github.com/eusip/POM
3. **3MT_French**: 248 public presentations with time-dependent ratings for persuasiveness, engagement and perceived confidence, but **French and dataset marked restricted**, so not a ready-to-use English training set. https://zenodo.org/records/7603511
4. **SpeechCraft**: Large English/Chinese expressive speech annotation project, with pitch/energy/speed/emphasis labels; substantially auto-labeled and not ratings of public-speaking quality. Third-party corpus and EULA checks apply. https://github.com/thuhcsi/SpeechCraft
5. **TED rhetorical strategies annotations**: 392 talks, with labels for audience engagement, figures of speech, repetition and humor. Only 18 of 399 annotation files are human-annotated, most machine-labeled. TED transcripts carry BY-NC-ND restrictions; review licensing before reuse. Not direct scoring labels for effective hackathon pitches. https://github.com/brezgis/TED-talks-rhetorical-strategies-annotated-dataset
6. **metaTED**: 180 English TED talks annotated for discourse patterns. The paper reports inconsistent annotator agreement across labels, so train/evaluate carefully. https://aclanthology.org/L16-1618/

**Dataset conclusion**: No single verified source above supplies English hackathon-pitch rehearsal audio with trustworthy time-stamped labels for every feature desired. Creating a small **consented, purpose-built evaluation set** is more valuable now than large-scale training. Reuse public data only within stated licenses and never assume popularity or applause means good speaking.

## Plan and measurable validation

- **Pilot:** 20–30 short English rehearsals, from diverse speakers, including Nigerian English accents and different recording devices. Obtain consent, restrict access, allow deletion.
- **Ground truth:** at least two annotators flag audible `um`/`uh`, non-speech pauses and their timestamps; rate which generated comments are actionable/useful; adjudicate disagreements.
- **Pass/fail criteria** (proposed for the pilot; NOT already achieved): filler precision >= 0.85 and recall >= 0.75 on human transcripts; event timestamp median error <= 0.5 s; > 70% of feedback statements marked helpful by users. Review subgroup gaps instead of reporting one aggregate number.
- **Evaluation design:** compare to Microsoft/Yoodli on the same recordings; blinded users rate which report better identifies a next action. Do not claim gains from synthetic tests.
- **Only later:** train/finetune a discriminative model with speaker-level held-out split if the baseline fails in reproducible, documented ways.

## Product versus hackathon-track mismatch

The previously built **Track C app compares two recordings of the same text**, using acoustic feature alignment. The requested single-recording coach is a different product. If the competition rules explicitly require same-text reference and rehearsal with time-aligned acoustic comparison, **submitting only this revised coach would risk failing the track requirements**. Keep the original app via `python legacy_comparison.py` and incorporate coaching as an optional feature rather than replacing the required evaluation.

## What works in current artifact

- Gradio interface with microphone or upload, optional deck/PDF/TXT, goals, optional manual/automatic ASR, evidence graph, event table, JSON download.
- Offline signal events, manual filler count and word rate, slide keyword checks, basic pitch structure scaffolding.
- Optional external LLM content review **requires explicit checkbox, library, API key, and network access**; no external research or factual verification is performed.
- No trained new model and no completed real-world evaluation. Synthetic audio tests do not prove coaching quality.
