"""Automatic database backups: one consistent copy per day (taken when the app starts) plus a manual "back up now".

Uses SQLite's online backup, so a copy is safe even while the app is writing. The newest KEEP copies are kept.
Folder: `data/backups/` next to the database (override with APP_BACKUP_DIR)."""
import os
import sqlite3
from datetime import datetime
from pathlib import Path

from .config import DB_PATH

KEEP = 14
DIR = Path(os.getenv("APP_BACKUP_DIR", DB_PATH.parent / "backups"))


def files() -> list[Path]:
    """Existing backups, newest first."""
    return sorted(DIR.glob("app-*.db"), reverse=True) if DIR.exists() else []


def last() -> datetime | None:
    f = files()
    return datetime.fromtimestamp(f[0].stat().st_mtime) if f else None


def make() -> Path | None:
    """Write a backup now and prune old ones. Returns the file, or None if there is no database yet."""
    if not DB_PATH.exists() or DB_PATH.stat().st_size == 0:
        return None
    DIR.mkdir(parents=True, exist_ok=True)
    dest = DIR / f"app-{datetime.now():%Y%m%d-%H%M%S}.db"
    src, dst = sqlite3.connect(DB_PATH), sqlite3.connect(dest)
    try:
        src.backup(dst)
    finally:
        dst.close()
        src.close()
    for old in files()[KEEP:]:
        old.unlink(missing_ok=True)
    return dest


def run_if_due() -> Path | None:
    """Back up if none was made today. Never raises - a backup problem must not stop the app."""
    try:
        t = last()
        if t is None or t.date() < datetime.now().date():
            return make()
    except Exception:
        pass
    return None
