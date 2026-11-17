"""Debounce pattern: do an expensive thing (e.g. an AI call) only after the user has stopped editing for N minutes.

Persisted in the settings table so it survives reloads and restarts.
    queue("moved a card")   # on every user edit: remembers it and restarts the timer
    due()                   # True once the quiet period has passed
    take()                  # returns the remembered edits and clears them (call when you run the expensive thing)
    status()                # shows a note and re-checks every 30 s so the work starts without any click
"""
import json
from datetime import datetime, timedelta

import streamlit as st

from . import db

QUIET_MIN = 5
KEY = "pending_changes"


def _read() -> dict | None:
    try:
        cur = json.loads(db.get_settings().get(KEY) or "{}")
    except ValueError:
        return None
    return cur if cur.get("items") else None


def queue(what: str):
    cur = _read() or {}
    due_at = (datetime.now() + timedelta(minutes=QUIET_MIN)).isoformat(timespec="seconds")
    db.set_setting(KEY, json.dumps(dict(due=due_at, items=(cur.get("items") or []) + [what])))


def due() -> bool:
    cur = _read()
    return bool(cur) and datetime.fromisoformat(cur["due"]) <= datetime.now()


def take() -> list[str]:
    cur = _read()
    db.set_setting(KEY, "")
    return cur["items"] if cur else []


def status():
    cur = _read()
    if not cur:
        return

    def tick():
        if due():
            st.rerun()
        mins = max(1, -(-(datetime.fromisoformat(cur["due"]) - datetime.now()).total_seconds() // 60))
        st.caption(f"⏳ {len(cur['items'])} change(s) noted – processing after {int(mins)} min without further edits.")
    st.fragment(run_every=30)(tick)()
