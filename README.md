# Streamlit app template

A themed multipage Streamlit starter with SQLite storage, daily backups, an optional Claude (Anthropic) helper with cost logging,
a debounce pattern, and a library of UI helpers (banners, KPI tiles, ring gauges, sparklines, non-scrolling chart boxes with "?" help).
Extracted from a personal cycling-coach app; nothing cycling-specific remains.

## Start a new project
```bash
cp -R streamlit-app-template my-new-app && cd my-new-app
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # add ANTHROPIC_API_KEY only if you use appkit/ai.py
streamlit run app.py
```
Then: set `APP_NAME` in `appkit/config.py`, rename the `appkit` package if you like, `git init`.

## Layout
| Path | What |
|---|---|
| `app.py` | page config, navigation, CSS injection, daily backup |
| `assets/style.css` | the theme (green). Re-theme by search/replace of `#4f6228`, `#76933c`, `#1c2a10`, `#f2f5ec`, `#e9efdb` and the rgba(79,98,40/118,147,60) values; also `.streamlit/config.toml` |
| `appkit/config.py` | app name, DB path, default settings, AI model |
| `appkit/db.py` | SQLite: `SCHEMA`, `COLUMN_MIGRATIONS`, `df()`, `execute()`, key/value settings |
| `appkit/ui.py` | UI helpers: `banner`, `kpi_row`, `chart_box`, `tidy`, `help_button`, `ring_card`, `metric_card`, `info_card`, `sparkline`, `zone_bar`, `dots`; charts are locked (no zoom/scroll), tooltips unified |
| `appkit/backup.py` | one SQLite online backup per day, keeps 14 |
| `appkit/ai.py`, `usage.py` | `ai.ask(prompt, system, purpose)` with prompt caching; every call logged with an estimated cost (Settings page) |
| `appkit/debounce.py` | act only after N minutes without edits (persisted) |
| `pages/` | Home, Data (dialog + chart example), Settings, Docs |

## Lessons baked in (from the original app)
- Streamlit dialogs are fragments: `st.rerun()` inside a dialog closes it; AppTest cannot drive them (use Playwright).
- `st.container(key="x")` gives CSS class `st-key-x`; use it for scoped styling.
- A fixed `st.container(height=)` adds inner scrollbars; `chart_box` uses min-height instead.
- Never disable a button just to block empty input (blocked cursor): validate on click.
- Don't call an AI on every event: gate by once-a-day, debounce after edits, or explicit user request.
- Avoid `sed -i` on macOS in scripts; use Python for edits.
