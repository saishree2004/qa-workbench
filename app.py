import streamlit as st

from db import init_db
from styles import inject_css, require_login
from ui.home import home

st.set_page_config(page_title="QA Workbench", page_icon="assets/favicon.svg", layout="wide")
st.logo("assets/logo.svg", icon_image="assets/favicon.svg")
inject_css()
require_login()
init_db()

nav = st.navigation({
    "": [st.Page(home, title="Home", icon="🏠", default=True)],
    "Plan": [
        st.Page("pages/analyzer.py", title="Analyzer", icon="🔍"),
        st.Page("pages/generator.py", title="Generator", icon="✨"),
        st.Page("pages/suites.py", title="Suites", icon="🗂️"),
    ],
    "Bugs": [
        st.Page("pages/bug_builder.py", title="Bug Builder", icon="🐞"),
        st.Page("pages/bug_tracker.py", title="Bug Tracker", icon="📋"),
    ],
    "Report": [
        st.Page("pages/daily_update.py", title="Daily Update", icon="📝"),
        st.Page("pages/dashboard.py", title="Dashboard", icon="📊"),
    ],
})
nav.run()
