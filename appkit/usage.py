"""Anthropic API usage log: tokens per call and an estimated cost (USD) at list prices."""
from datetime import datetime

import pandas as pd

from . import db

# USD per million tokens: (input, output). Cache writes (5-minute TTL) cost 1.25x input, cache reads 0.1x input.
PRICES = {
    "claude-sonnet-5-5": (2.00, 10.00),
    "claude-sonnet-5": (2.00, 10.00),
    "claude-opus-5-5": (4.00, 20.00),
    "claude-opus-5": (5.00, 25.00),
    "claude-haiku-5-5": (0.10, 0.50),
    "claude-fable-5-1": (10.00, 50.00),
}
DEFAULT_PRICE = PRICES["claude-sonnet-5-5"]
PURPOSES = {"example": "Example call"}     # purpose key -> label shown on the Settings page


def cost_usd(model: str, inp: int, out: int, cache_write: int = 0, cache_read: int = 0) -> float:
    pi, po = PRICES.get(model, DEFAULT_PRICE)
    return (inp * pi + out * po + cache_write * pi * 1.25 + cache_read * pi * 0.1) / 1e6


def record(msg, purpose: str, model: str | None = None, seconds: float | None = None):
    """Log one API response (never raises - usage tracking must not break the app)."""
    try:
        u = msg.usage
        model = model or getattr(msg, "model", "") or ""
        inp, out = int(u.input_tokens or 0), int(u.output_tokens or 0)
        cw, cr = int(getattr(u, "cache_creation_input_tokens", 0) or 0), int(getattr(u, "cache_read_input_tokens", 0) or 0)
        db.execute("INSERT INTO api_usage(ts,purpose,model,input_tokens,output_tokens,cache_write_tokens,cache_read_tokens,cost_usd,duration_s) "
                   "VALUES(?,?,?,?,?,?,?,?,?)", (datetime.now().isoformat(timespec="seconds"), purpose, model, inp, out, cw, cr,
                                                 cost_usd(model, inp, out, cw, cr), seconds))
    except Exception:
        pass


def log() -> pd.DataFrame:
    return db.df("SELECT * FROM api_usage ORDER BY id DESC")
