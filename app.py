import streamlit as st

from db import init_db
from styles import inject_css

st.set_page_config(page_title="QA Workbench", page_icon="🧪", layout="wide")
inject_css()
init_db()


def home():
    st.title("QA Workbench")
    st.caption("Requirements to test cases to bugs, in one place.")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="card"><h4>Plan</h4>Analyze requirements, generate test cases, '
                    'organize suites.</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="card"><h4>Track</h4>Build bug reports, track status, '
                    'share daily updates and dashboards.</div>', unsafe_allow_html=True)


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
