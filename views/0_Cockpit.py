"""Cockpit demo: a row of status tiles (ring gauge, zone bar, dots, sparklines, headline card) above an animated bars + lines chart.
Replace the sample data below with your own queries; every helper lives in appkit/ui.py."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from appkit import ui

ui.setup("Cockpit", "🧭")

# ---- sample data (replace) ----------------------------------------------------------
rng = np.random.default_rng(7)
days = pd.date_range(end=pd.Timestamp.today().normalize(), periods=84, freq="D")
weekly = pd.DataFrame({"week": pd.date_range(days[0], periods=12, freq="7D"), "load": rng.integers(250, 520, 12)})
weekly["avg"] = weekly["load"].rolling(4, min_periods=1).mean()
trend_a = (rng.normal(0, 1, 12).cumsum() + 50).tolist()
trend_b = (rng.normal(0, 3, 12).cumsum() + 250).tolist()
status_days = ["#76933c", "#76933c", "#d99a1c", "#76933c", "#c8453d", "#d99a1c", "#76933c"]

GREEN, RED, BLUE = "#4f6228", "#c8453d", "#3b82c4"
up = lambda txt: f"<span style='color:#76933c'>▲ {txt}</span>"
per = "<span style='opacity:.65'> / 6w</span>"

# ---- the cockpit row ---------------------------------------------------------------------
score = 12
bar = ui.zone_bar(score, [(-30, "#d99a1c"), (-10, "#76933c"), (5, "#c9d6a8"), (15, "#9fc27a"), (30, "#d99a1c")], -40, 30)
dts = ui.dots(status_days, [f"Day {i + 1}" for i in range(7)])
ui.ring_row([
    ui.metric_card("Balance", f"{score:+d}", "Fresh · CTL 60 · ATL 48", "#76933c", bottom=bar),         # big number + strip below
    ui.ring_card(72, "72%", "This week", "7.2 of 10 h done<br><span style='font-weight:500;opacity:.8'>Mon – Sun</span>"),   # ring gauge
    ui.metric_card("Status today", "GO", "No warning signs", "#76933c",                                               # dots on the right
                   right=f"<div style='text-align:right'>{dts}<div style='font-size:.62rem;color:#8a9570;margin-top:3px'>last 7 days</div></div>"),
    ui.metric_card("Metric A", f"{trend_a[-1]:.0f}", f"Good · {up('+2.1')}{per}", RED, right=ui.sparkline(trend_a, RED)),             # sparkline
    ui.metric_card("Metric B", f"{trend_b[-1]:.0f}", f"W · {up('+8')}{per}", GREEN, right=ui.sparkline(trend_b, GREEN, delay=0.7), tag="3.4 per kg"),
    ui.metric_card("Metric C", "310", f"Detail · {up('+5')}{per}", BLUE, right=ui.sparkline(trend_b[::-1], BLUE, delay=0.8)),
])
st.html("<div style='height:6px'></div>")
st.html(ui.info_card("Next up", "Tuesday: Intervals 4×8 min", "75 min · 80 load", "In 2 days"))      # dark-green headline card

# ---- animated chart: container key must start with "anim_" ---------------------------------
with st.container(key="anim_load"):
    f = go.Figure()
    f.add_bar(x=weekly["week"], y=weekly["load"], name="Weekly load", marker_color="rgba(118,147,60,.55)")
    f.add_scatter(x=weekly["week"], y=weekly["avg"], name="4-week average", line=dict(color=GREEN, width=3), mode="lines")
    f.add_annotation(x=weekly["week"].iloc[-1], y=weekly["load"].iloc[-1], text="<b>Latest</b>", showarrow=True, arrowcolor=GREEN, bgcolor=GREEN, font=dict(color="#fff", size=11))
    ui.tidy(f, "Example chart", height=340)          # CHART_HELP entry "example chart" gives it the "?" help
    ui.chart_box(st.container(), f, notes=["Bars rise first, annotations fade in, then the line is revealed. Re-run the page to see it again."])
