"""
app.py — serves the index.html demo via Streamlit Cloud.
"""
import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path

st.set_page_config(
    page_title="AI Contract Review System",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Hide Streamlit chrome so only the HTML shows
st.markdown("""
<style>
#MainMenu, header, footer { visibility: hidden; }
.block-container { padding: 0 !important; max-width: 100% !important; }
</style>
""", unsafe_allow_html=True)

html = Path(__file__).parent.joinpath("index.html").read_text(encoding="utf-8")
components.html(html, height=920, scrolling=True)
