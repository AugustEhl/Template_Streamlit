"""Thin wrapper around the Anthropic API: one call, logged to the usage table. Needs ANTHROPIC_API_KEY in .env."""
import time

from . import usage
from .config import AI_MODEL


def ask(prompt: str, system: str = "", purpose: str = "example", model: str | None = None, max_tokens: int = 2000) -> str:
    import anthropic            # imported here so the app runs without the package when AI is unused
    client = anthropic.Anthropic()
    t0 = time.time()
    # The system prompt is cached (cheap on repeat calls once it is long enough to qualify).
    msg = client.messages.create(
        model=model or AI_MODEL, max_tokens=max_tokens,
        system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}] if system else anthropic.NOT_GIVEN,
        messages=[{"role": "user", "content": prompt}])
    usage.record(msg, purpose, model or AI_MODEL, time.time() - t0)
    return "".join(b.text for b in msg.content if b.type == "text")
