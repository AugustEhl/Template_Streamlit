import streamlit as st

from appkit import backup, db, usage, ui

ui.setup("Settings", "⚙️")
s = db.get_settings()

st.subheader("Profile")
name = st.text_input("Display name", s["display_name"])
if st.button("Save", type="primary"):
    db.set_setting("display_name", name)
    st.success("Saved")

st.subheader("Backups")
t = backup.last()
st.caption(f"Last backup: {t:%Y-%m-%d %H:%M}" if t else "No backup yet.")
if st.button("Back up now"):
    st.success(f"Saved {backup.make()}")

st.subheader("AI usage")
log = usage.log()
if log.empty:
    st.caption("No AI calls yet.")
else:
    st.metric("Estimated total cost (USD)", f"{log['cost_usd'].sum():.2f}")
    st.dataframe(log, hide_index=True, width="stretch")
