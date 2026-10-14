# Recommended stack, by responsibility

| Function | Current or planned implementation | Condition |
|---|---|---|
| Primary test UI | Gradio 6 | Implemented |
| Independent analysis pipeline | Python 3, NumPy, SciPy, librosa, SoundFile | Implemented |
| Speech-to-text and word timing | Local faster-whisper, AssemblyAI, Deepgram, OpenAI Whisper | Optional adapters implemented; keys/model downloads needed |
| Acoustic features | RMS, pause windows, relative amplitudes; MFCC-DTW in Track C legacy | Implemented baseline |
| Detailed pitch/prosody | librosa / openSMILE | Research and validation next |
| Deck parsing | pypdf and python-pptx | Implemented |
| Text coaching | OpenAI Responses API, consent-gated | Optional |
| JSON API | FastAPI, python-multipart, Uvicorn | Implemented local |
| Reports | SQLite, opt-in + expiry | Implemented local |
| Assistant bridge | Python MCP SDK, stdio | Local foundation implemented |
| Public production auth | OIDC/OAuth2, tenant-level ACLs, rate limiting | Not implemented |
| Queue and job system | Redis + worker or cloud job service | Future |
| Production database/storage | Postgres + encrypted object storage | Future |
| Voice streaming | LiveKit or WebRTC, partial ASR and local acoustics | Future |
| CI | Pytest and GitHub Actions | Tests available; add GitHub Actions after repository target is confirmed |

Do not train a custom end-to-end neural network until the labeled dataset and holdout evaluation show a meaningful need.
