"""Explicitly opt-in, external API content coaching. No hidden web research."""
import os

SYSTEM = """You are a cautious English public-speaking coach. You receive an ASR/manually supplied transcript, slide text, speaker goal and quantitative evidence. Output concise Markdown with these sections: Message strengths, Content review, Suggested rehearsal changes, Two example rewrites, and Unknowns. Distinguish observed text from suggestions. Quote exact short snippets from the provided transcript to justify feedback. Indicate potential slide mismatch only if the deck contradicts or omits a claim; never infer factual falsehood, audience engagement, actual feelings, medical conditions, or charisma from amplitude. Avoid invented facts, citations, results, statistics or cases. No access to external web or experts. Respect accents and communication styles. Provide at most 5 actionable recommendations, using plain language. If no transcript, say content cannot be assessed. Hypothesized improvements are advice, not ground truth."""


def review_with_openai(transcript: str, slides: list[dict], goal: str, events: list[dict],
                       consent: bool) -> str:
    if not consent:
        return "AI text review skipped: no permission to send speech/deck text to an external model."
    if not transcript.strip():
        return "AI text review skipped: there is no transcript."
    if not os.getenv("OPENAI_API_KEY"):
        return "AI text review skipped: OPENAI_API_KEY is not configured on this host."
    try:
        from openai import OpenAI
    except ImportError:
        return "AI text review skipped: install the optional openai package in requirements-llm.txt."
    excerpt = '\n'.join(f"Slide {s['number']}: {s['text'][:1100]}" for s in slides[:25])
    content = (f"Speaker goal: {goal[:500]}\n\nSlide excerpts:\n{excerpt[:11000]}\n\n"
               f"Spoken transcript:\n{transcript[:12000]}\n\n"
               f"Acoustic flags (not emotional interpretations): {events[:20]}")
    try:
        client = OpenAI(timeout=30)
        out = client.responses.create(model=os.getenv("SPEECHTRACE_COACH_MODEL", "gpt-4.1-mini"),
                                      instructions=SYSTEM, input=content, max_output_tokens=950)
        return out.output_text or "The model returned no suggestions."
    except Exception as exc:
        return f"AI text review unavailable ({type(exc).__name__}). Acoustic and rule-based results are still usable."
