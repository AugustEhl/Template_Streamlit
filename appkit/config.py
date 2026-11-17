from pathlib import Path
import os
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

APP_NAME = "My App"
DB_PATH = Path(os.getenv("APP_DB", ROOT / "data" / "app.db"))
AI_MODEL = os.getenv("APP_MODEL", "claude-sonnet-5-5")

# Defaults for the key/value settings table (edited on the Settings page). Add your own.
DEFAULT_SETTINGS = {
    "display_name": "",
}
