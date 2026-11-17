import streamlit as st

from appkit import db, ui

ui.setup("Home", "🏠")
s = db.get_settings()
st.write(f"Welcome{', ' + s['display_name'] if s['display_name'] else ''}! This is the starter page.")

df = db.df("SELECT * FROM items")
ui.kpi_row([("Items", str(len(df)), None), ("Total value", f"{df['value'].sum():.0f}" if len(df) else "–", None)])

# Themed banner with its button inside; returns True on click
if ui.banner("welcome", "Add a few rows on the **Data** page to see the chart.", "Got it", "info"):
    st.toast("Nice!")

# Tiles (HTML helpers in appkit/ui.py): ring_card, metric_card, info_card, sparkline, zone_bar, dots
ui.ring_row([ui.ring_card(min(len(df) * 10, 100), str(len(df)), "Progress", "10 items = 100 %")])
