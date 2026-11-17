"""SQLite helpers: schema, simple migrations, DataFrame queries and a key/value settings table.

To add a table: put it in SCHEMA (CREATE TABLE IF NOT EXISTS). To add a column to an existing table: add a line to
COLUMN_MIGRATIONS - it is applied to databases created before the column existed."""
import sqlite3
from contextlib import contextmanager

import pandas as pd

from .config import DB_PATH, DEFAULT_SETTINGS

SCHEMA = """
CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE IF NOT EXISTS api_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, purpose TEXT, model TEXT,
    input_tokens INTEGER, output_tokens INTEGER, cache_write_tokens INTEGER, cache_read_tokens INTEGER,
    cost_usd REAL, duration_s REAL);
CREATE TABLE IF NOT EXISTS items (            -- example table: replace with your own data
    id INTEGER PRIMARY KEY AUTOINCREMENT, day TEXT, name TEXT, value REAL);
"""

COLUMN_MIGRATIONS: list[tuple[str, str, str]] = [
    # ("items", "note", "TEXT"),
]


@contextmanager
def conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    try:
        yield c
        c.commit()
    finally:
        c.close()


def init():
    with conn() as c:
        c.executescript(SCHEMA)
        for table, col, typ in COLUMN_MIGRATIONS:
            if col not in {r["name"] for r in c.execute(f"PRAGMA table_info({table})")}:
                c.execute(f"ALTER TABLE {table} ADD COLUMN {col} {typ}")


def df(sql: str, params=()) -> pd.DataFrame:
    with conn() as c:
        return pd.read_sql_query(sql, c, params=params)


def execute(sql: str, params=()):
    with conn() as c:
        c.execute(sql, params)


def get_settings() -> dict:
    with conn() as c:
        rows = {r["key"]: r["value"] for r in c.execute("SELECT * FROM settings")}
    return {**DEFAULT_SETTINGS, **rows}


def set_setting(key: str, value):
    execute("INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, str(value)))
