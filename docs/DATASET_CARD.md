# Demo Dataset Card

**Title:** SpeechTrace synthetic acoustic deviation demonstration v0.1

**Purpose:** Deterministic tests of pause alignment, duration differences, and amplitude differences.

**Source:** Original English paragraph synthesized using locally installed eSpeak, then modified by an explicitly defined NumPy/Librosa transformation. No human voice data or copyrighted speeches were sourced.

**Contents:** 1 reference WAV, 3 transformed WAVs, same transcript text, JSON labels, generation code, saved evaluation output.

**Sampling rate:** 16 kHz, mono PCM16. **Reference duration:** approximately 8.99 seconds.

**Supervision:** The only precisely localized injected acoustic event is the 2.4-second silence insertion. Time-stretch and amplitude changes are labeled at whole-recording level. There are no word-level alignment labels.

**Bias:** eSpeak is not human speech and this demo uses only one English synthesized speaker and one passage. It cannot establish suitability for any real demographic, accent, age or language.

**Ethical and legal concerns:** Do not represent this synthetic reference as a well-known public speaker. Check rights before adding third-party audio or public speech recordings. Real personal speech may contain identifying voiceprints; use explicit consent and secure storage.

**Evaluation:** The paired injected-silence demo was detected with 0.97 temporal overlap in a single controlled run, but this does not imply generalization or high precision on real public speech.

**To regenerate:** `python generate_demo.py` with eSpeak available. Exact audio may differ across eSpeak versions.
