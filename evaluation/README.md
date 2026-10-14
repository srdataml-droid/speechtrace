# SpeechTrace evaluation starter kit

Run: `python evaluation/evaluate.py evaluation/illustrative_examples.jsonl`

The two included examples are **synthetic** and are NOT measurements of Deepgram or a real speaker. They exist to test the metric calculation. For real evaluation, create an **authorized** `consented_eval.jsonl` containing the original human-corrected transcript, AI transcript, and audio-transcription latency in milliseconds. Never commit identifiable real speaker data or raw recordings to a public repository.

Measure WER, filler recall/precision, elapsed time, acoustic-event match tolerance, and coaching usefulness on speaker-disjoint samples. At least two reviewers should label a subset of pauses/fillers; differences should be documented. Record regional English accent coverage without inferring race or personal identity.

Filler precision/recall here count token occurrences, not precise timestamps. A future evaluator should compare timestamp matches with 250–500 ms tolerances and separate missed 'um' from speech-specific stutters. Add baseline p50/p95 for recordings of 30 sec, 3 min and 5 min under variable mobile networks.