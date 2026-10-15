# SpeechTrace — Next Founders Hackathon 2026 submission guide

**Competition:** https://next-founders.devpost.com/  
**Deadline:** 15 October 2026, 5:00pm EDT = 10:00pm WAT (Lagos).  
**Eligibility:** must be age 13–22 AND currently enrolled as an undergraduate student. Confirm ND/HND qualification with organizers if uncertain.  
**This document contains proposed pitch and business assumptions, not claims of proven traction.**

## Submission positioning

**Title:** SpeechTrace — Practice Your Pitch, Understand Your Delivery  
**Tagline:** A mobile-first speaking rehearsal studio for students preparing their next important presentation.  
**Category fit:** Consumer app / underserved student presenters; no speech-specific event track exists.

## The problem

Students preparing class presentations, job interviews and hackathon pitches may have no practice audience or communication coach. Listening back to a recording is useful, but it can be difficult to find specific moments to rehearse again. Many existing products provide speaking analytics; this alone is not novel.

## What currently works in the repository

- Browser recording or audio upload, playback, editable transcript, candidate fillers and local energy/pause visualization.
- Optional, consented server-side Whisper transcription and Qwen generated revision suggestions via Groq on the hosted mobile app, dependent on deployment settings, quota and provider availability.
- Downloadable JSON rehearsal report; no user account or persistent rehearsal history is implemented.
- A separate Gradio/Python same-text acoustic comparison research prototype with synthetic stress examples, timeline differences and heuristic scoring.
- Tests for many paths are implemented. Automated mock tests do not establish working third-party services on real user phones.

## What NOT to claim

- No verified paying customers, market adoption, unit economics or measured speaking outcomes yet.
- The acoustic similarity rubric is not a validated speaking skill score; no real-speaker benchmark or forced word alignment.
- Do not claim microphone energy proves confidence, emotion or persuasion.
- Do not claim the live Groq workflow works until a real phone end-to-end test confirms it.
- The project predates this competition; disclose earlier development and clearly identify any new work.

## Business hypothesis — explicitly unvalidated

**First user:** Students preparing 1–5 minute hackathon, classroom and interview speeches using smartphones, especially those who do not use slide-centric tools.  
**Initial distribution experiment:** Invite presentation clubs, student entrepreneurship groups and campus organizers to test one rehearsal for free. Ask whether the detailed review helps and whether they will use it a second time; document consented feedback.  
**Potential business model:** Free limited trial and a paid student plan for repeat coaching. An institutional plan for campus clubs is a *future hypothesis*, not an available product. No subscription payments are currently implemented.  
**Cost discipline:** Speech transcription and AI coaching have upstream usage limits and would require realistic per-session costing, abuse protections, authentication, billing and retention controls before commercial scale.  
**Primary business metric:** Weekly returning presenters whose second rehearsal improves a self-reported communication goal; validate with human review, not only heuristic scores.

## Five-minute demo structure

- **0:00–0:40 | Who has this problem?** Student preparing to explain a pitch. A clear target consumer, no unverified population statistics.
- **0:40–1:35 | Live user journey.** Open public mobile site, choose hackathon audience, record a 20–30 second pitch with a real stumble, replay, opt in to transcript and coaching.
- **1:35–2:35 | Evidence and improvement.** Show the editable transcript, possible filler marks, local energy/pause plot, example feedback and suggested rewrite. Acknowledge imperfect ASR. If Groq fails, do not edit in a fake output; honestly show fallback and a recorded successful session.
- **2:35–3:25 | Technical architecture.** Web MediaRecorder and WebAudio in the browser; Vercel endpoints; Groq-hosted Whisper for transcript and Qwen for transcript/evidence-grounded optional coaching; separate Python acoustic comparison engine; explain consent and limitations.
- **3:25–4:15 | Market and finance.** Why student presenters; show open competitive alternatives (Microsoft Speaker Coach and Yoodli). Distinguish portable, phone-first product focus rather than claim filler detection is novel. Proposed free trial and subscription/institutional pilot; no revenue yet.
- **4:15–5:00 | Scalability and closing.** Current live service is a prototype with limited quotas and no durable distributed rate limiter. Proposed next milestones: proper authentication, metering and logs; test with real students; verify outcomes with human feedback and repeat use.

## Last checks

1. Verify student status with an active college ID and eligibility if ND/HND is not accepted as 'college undergraduate'.
2. Open https://speechtrace-mobile-lab.vercel.app/ in a phone browser, record and replay, then check transcription, feedback, export and retry with consent.
3. Verify current GitHub Actions web and Python workflows are both green.
4. Record a truthful approximately 5-minute English video, with on-screen app behavior, architecture, competition awareness and business plan.
5. Create Devpost entry before 10:00pm Lagos time; add project description, working link, GitHub and video. Review form for any other required fields and confirm final submit action.

## Originality, prior-work and AI disclosure

SpeechTrace was initially developed for the Multimodal AI Hackathon Track C before the Next Founders deadline. More recent work expanded mobile voice processing and coaching; see repository commit history. Code and writing received AI assistance. The entry must accurately disclose reused code and current state, and not imply the product was originally started during Next Founders.
