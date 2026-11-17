from datetime import date

import plotly.graph_objects as go
import streamlit as st

from appkit import db, ui

ui.setup("Data", "🗂️")


@st.dialog("Add item")
def add_dialog():
    day = st.date_input("Day", date.today())
    name = st.text_input("Name")
    value = st.number_input("Value", value=1.0)
    if st.button("Save", type="primary"):
        db.execute("INSERT INTO items(day,name,value) VALUES(?,?,?)", (day.isoformat(), name, value))
        st.rerun()


if st.button("Add item", icon=":material/add:"):
    add_dialog()

df = db.df("SELECT * FROM items ORDER BY day")
if df.empty:
    st.info("No items yet.")
else:
    fig = go.Figure(go.Bar(x=df["day"], y=df["value"], marker_color="#76933c"))
    ui.tidy(fig, "Example chart")        # title matches a CHART_HELP entry in appkit/ui.py -> "?" help button
    # chart_box: bordered box, title, "?" help, chart (fixed, non-scrollable), optional notes in an expander
    ui.chart_box(st.container(), fig, notes=["Notes go in an expander so charts never scroll."])
    st.dataframe(df, hide_index=True, width="stretch")
