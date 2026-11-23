# Project notes for Claude

Streamlit multipage app (see README.md). Conventions:
- Pages in `views/` (not `pages/`: that name makes Streamlit show its default sidebar menu for a moment on launch), registered in `app.py`. Shared code in `appkit/`.
- Database via `appkit/db.py` only; new tables go in `SCHEMA`, new columns in `COLUMN_MIGRATIONS`.
- Charts: build a Plotly figure, `ui.tidy(fig, "Title")`, show with `ui.chart_box(...)`; register help text in `ui.CHART_HELP`. Never make a chart scrollable.
- Theme lives in `assets/style.css` and `.streamlit/config.toml`.
- AI calls go through `appkit/ai.py` so they are logged; avoid calling on every rerun.
- Commit/push only when asked.
