from pathlib import Path

import streamlit as st

from appkit import backup, db
from appkit.config import APP_NAME

st.set_page_config(page_title=APP_NAME, page_icon="📊", layout="wide")

pages = [
    st.Page("pages/1_Home.py", title="Home", icon=":material/home:", url_path="home", default=True),
    st.Page("pages/2_Data.py", title="Data", icon=":material/table_chart:", url_path="data"),
    st.Page("pages/3_Settings.py", title="Settings", icon=":material/settings:", url_path="settings"),
    st.Page("pages/4_Docs.py", title="Docs", icon=":material/menu_book:", url_path="docs"),
]
st.markdown(f"<style>{(Path(__file__).parent / 'assets' / 'style.css').read_text()}</style>", unsafe_allow_html=True)
db.init()
backup.run_if_due()          # one consistent database copy per day
st.navigation(pages, position="top").run()
