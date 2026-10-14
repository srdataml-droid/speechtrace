"""SpeechTrace baseline ASR metrics. Does not call paid models or collect user data.
Usage: python evaluation/evaluate.py evaluation/illustrative_examples.jsonl
"""
import collections
import json
import re
import sys
from pathlib import Path

FILLER_TOKENS = {"um", "uh", "erm", "ah", "hmm", "er"}


def tokens(text):
    return re.findall(r"[a-z']+", str(text).lower())


def edit_distance(a, b):
    prev = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        cur = [i]
        for j, y in enumerate(b, 1):
            cur.append(min(cur[-1] + 1, prev[j] + 1, prev[j - 1] + (x != y)))
        prev = cur
    return prev[-1]


def metrics(rows):
    word_errors = 0
    reference_words = 0
    true_fillers = false_fillers = missed_fillers = 0
    durations = []
    for r in rows:
        gold = tokens(r["gold_transcript"])
        pred = tokens(r["predicted_transcript"])
        word_errors += edit_distance(gold, pred)
        reference_words += len(gold)
        g = collections.Counter(x for x in gold if x in FILLER_TOKENS)
        p = collections.Counter(x for x in pred if x in FILLER_TOKENS)
        true_fillers += sum((g & p).values())
        false_fillers += sum((p - g).values())
        missed_fillers += sum((g - p).values())
        if r.get("elapsed_ms") is not None:
            durations.append(float(r["elapsed_ms"]))
    precision = true_fillers / (true_fillers + false_fillers) if (true_fillers + false_fillers) else None
    recall = true_fillers / (true_fillers + missed_fillers) if (true_fillers + missed_fillers) else None
    f1 = 2 * precision * recall / (precision + recall) if (precision is not None and recall is not None and precision + recall) else None
    sorted_ms = sorted(durations)
    return {"examples": len(rows), "wer": round(word_errors / reference_words, 4) if reference_words else None,
            "filler_precision": round(precision, 4) if precision is not None else None,
            "filler_recall": round(recall, 4) if recall is not None else None,
            "filler_f1": round(f1, 4) if f1 is not None else None,
            "transcription_p50_ms": round(sorted_ms[len(sorted_ms) // 2], 1) if durations else None,
            "transcription_p95_ms": round(sorted_ms[min(len(sorted_ms)-1, int(.95 * len(sorted_ms)))], 1) if durations else None}


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python evaluation/evaluate.py path/to/consented_eval.jsonl")
    rows = [json.loads(s) for s in Path(sys.argv[1]).read_text(encoding="utf-8").splitlines() if s.strip()]
    print(json.dumps(metrics(rows), indent=2))